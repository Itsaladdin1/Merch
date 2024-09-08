from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import db, Merchandise, CartItem, User, Information, Sold, Discount, init_db
from forms import MerchandiseForm, LoginForm, RegistrationForm, DiscountForm, EmployeeForm
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import stripe
import json

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

stripe.api_key = app.config['STRIPE_SECRET_KEY']

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize the database
with app.app_context():
    init_db()
    db.create_all()

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('merch-register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            session['user_id'] = user.id  # Ensure this line is present
            return redirect(url_for('admin'))
        else:
            flash('Login unsuccessful. Please check your email and password.', 'danger')
    return render_template('merch-login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    merch_form = MerchandiseForm()
    discount_form = DiscountForm()
    employee_form = EmployeeForm()

    if merch_form.validate_on_submit() and 'submit_merch' in request.form:
        if merch_form.image.data:
            image_file = secure_filename(merch_form.image.data.filename)
            merch_form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_file))
        else:
            image_file = 'default.jpg'
        merch = Merchandise(
            name=merch_form.name.data,
            information=merch_form.information.data,
            value=merch_form.value.data,
            specification=merch_form.specification.data,
            image_file=image_file,
            category=merch_form.category.data
        )
        db.session.add(merch)
        db.session.commit()
        flash('Merchandise item has been added!', 'success')
        return redirect(url_for('admin'))

    if discount_form.validate_on_submit() and 'submit_discount' in request.form:
        discount = Discount(
            code=discount_form.code.data,
            percentage=discount_form.percentage.data,
            category=discount_form.category.data
        )
        db.session.add(discount)
        db.session.commit()
        flash('Discount has been added!', 'success')
        return redirect(url_for('admin'))

    if employee_form.validate_on_submit() and 'submit_employee' in request.form:
        existing_user = User.query.filter_by(email=employee_form.email.data).first()
        if existing_user:
            flash('An account with this email already exists.', 'danger')
        else:
            user = User(
                username=employee_form.username.data,
                email=employee_form.email.data,
                role=employee_form.role.data
            )
            user.set_password(employee_form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Employee has been registered!', 'success')
            return redirect(url_for('admin'))

    return render_template('merch-admin.html', merch_form=merch_form, discount_form=discount_form, employee_form=employee_form)


@app.route('/add-item', methods=['GET', 'POST'])
@login_required
def add_item():
    merch_form = MerchandiseForm()

    if merch_form.validate_on_submit():
        # Define image_file initially as None or a default image
        image_file = None

        if merch_form.image.data:
            image_file = secure_filename(merch_form.image.data.filename)
            merch_form.image.data.save(os.path.join(app.config['UPLOAD_FOLDER'], image_file))
        else:
            image_file = 'default.jpg'  # Fallback to a default image if none is uploaded

        if merch_form.submit.data:  # If the form was submitted to add an item
            merch = Merchandise(
                name=merch_form.name.data,
                information=merch_form.information.data,
                value=merch_form.value.data,
                specification=merch_form.specification.data,
                image_file=image_file,  # Use the image file determined above
                category=json.dumps(merch_form.category.data),
                color=json.dumps(merch_form.colors.data),
                size=json.dumps(merch_form.sizes.data)
            )
            db.session.add(merch)
            db.session.commit()
            flash('Merchandise item has been added!', 'success')
            return redirect(url_for('admin'))
        elif 'preview' in request.form:  # If the form was submitted for preview
            preview_data = {
                'name': merch_form.name.data,
                'information': merch_form.information.data,
                'value': merch_form.value.data,
                'specification': merch_form.specification.data,
                'image_file': image_file,  # Use the image file determined above
                'category': merch_form.category.data,
                'color': merch_form.colors.data,
                'size': merch_form.sizes.data
            }
            session['preview_data'] = preview_data
            return redirect(url_for('preview_item'))

    return render_template('merch-add_item.html', merch_form=merch_form)


@app.route('/view-item/')
def preview_item():
    preview_data = session.get('preview_data', None)
    if preview_data is None:
        return redirect(url_for('add_item'))  # If no data, redirect to form

    categories = preview_data.get('category', [])
    colors = preview_data.get('color', [])
    sizes = preview_data.get('size', [])

    return render_template('merch-view_item.html', merch=preview_data, categories=categories, colors=colors, sizes=sizes)

@app.route('/submit-item', methods=['POST'])
def submit_item():
    preview_data = session.pop('preview_data', None)
    if preview_data:
        # Now save the item to your database
        # For example:
        new_item = Merchandise(
            name=preview_data['name'],
            information=preview_data['information'],
            value=preview_data['value'],
            specification=preview_data['specification'],
            image_file=preview_data['image'],
            category=json.dumps(preview_data['category']),
            color=json.dumps(preview_data['color']),
            size=json.dumps(preview_data['size']),
            date_added=datetime.utcnow()
        )
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('view_item', item_id=new_item.id))

    return redirect(url_for('add_item'))

@app.route('/discount', methods=['GET', 'POST'])
@login_required
def add_discount():
    discount_form = DiscountForm()
    if discount_form.validate_on_submit():
        discount = Discount(
            code=discount_form.code.data,
            percentage=discount_form.percentage.data,
            category=discount_form.category.data
        )
        db.session.add(discount)
        db.session.commit()
        flash('Discount has been added!', 'success')
        return redirect(url_for('admin'))
    return render_template('merch-add_discount.html', discount_form=discount_form)

@app.route('/information')
@login_required
def information():
    info = Information.query.all()
    return render_template('merch-information.html', info=info)

@app.route('/merch')
def merch():
    items = Merchandise.query.all()
    return render_template('merch.html', items=items, key=app.config['STRIPE_PUBLIC_KEY'])

@app.route('/add-to-cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    item = Merchandise.query.get_or_404(item_id)
    cart_item = CartItem.query.filter_by(merchandise_id=item_id).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        cart_item = CartItem(merchandise_id=item_id, quantity=1)
        db.session.add(cart_item)
    db.session.commit()
    flash('Item added to cart', 'success')
    return redirect(url_for('merch'))

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    cart_items = CartItem.query.all()
    total = sum(item.merchandise.value * item.quantity for item in cart_items)
    discount_value = 0

    if request.method == 'POST':
        discount_code = request.form.get('discount_code')
        if discount_code:
            discount = Discount.query.filter_by(code=discount_code).first()
            if discount:
                discount_value = (discount.percentage / 100) * total
                total -= discount_value
            else:
                flash('Invalid discount code', 'danger')

    return render_template('merch-cart.html', cart_items=cart_items, total=total, discount_value=discount_value, key=app.config['STRIPE_PUBLIC_KEY'])


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        data = request.get_json()
        discount_code = data.get('discount_code')
        cart_items = CartItem.query.all()

        # Calculate the total and apply discount
        total = sum(item.merchandise.value * item.quantity for item in cart_items)
        discount = Discount.query.filter_by(code=discount_code).first() if discount_code else None
        discount_percentage = discount.percentage if discount else 0
        discount_amount = total * (discount_percentage / 100) if discount_percentage else 0
        discounted_total = total - discount_amount

        # Create Stripe line items with the discounted total
        line_items = []
        for item in cart_items:
            unit_amount = int(item.merchandise.value * 100)  # Convert SEK to cents
            discounted_unit_amount = int(unit_amount * (1 - discount_percentage / 100)) if discount and item.merchandise.category == discount.category else unit_amount

            line_items.append({
                'price_data': {
                    'currency': 'sek',
                    'product_data': {
                        'name': item.merchandise.name,
                    },
                    'unit_amount': discounted_unit_amount,
                },
                'quantity': item.quantity,
            })

        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=url_for('success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('canceled', _external=True),
            payment_intent_data={
                'metadata': {
                    'discount_code': discount_code if discount else '',
                    'original_total': int(total * 100),
                    'discount_amount': int(discount_amount * 100),
                }
            }
        )

        return jsonify({'id': session.id})

    except Exception as e:
        print(f"Error creating checkout session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/success')
def success():
    user_id = session.get('user_id')
    print(f"User ID: {user_id}")  # Debug statement
    if not user_id:
        flash('User not logged in or session expired.', 'danger')
        return redirect(url_for('login'))

    cart_items = CartItem.query.all()
    for item in cart_items:
        sold_item = Sold(
            merchandise_id=item.merchandise_id,
            user_id=user_id,
            quantity=item.quantity
        )
        db.session.add(sold_item)

    CartItem.query.delete()  # Clear the cart after successful payment
    db.session.commit()
    return render_template('merch-success.html')

@app.route('/canceled')
def canceled():
    return render_template('merch-cancel.html')

@app.route('/manage-users')
@login_required
def manage_users():
    users = User.query.all()
    return render_template('merch-users.html', users=users)


@app.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        if 'email' in request.form:
            user.email = request.form['email']
        if 'password' in request.form:
            user.set_password(request.form['password'])
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('manage_users'))
    return render_template('merch-edit-user.html', user=user)


@app.route('/delete-user/<int:user_id>')
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('manage_users'))

@app.route('/view-merchandise', methods=['GET'])
@login_required
def view_merchandise():
    period = request.args.get('period', 'all')
    end_date = datetime.utcnow()

    if period == 'this_month':
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'last_month':
        start_date = (end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)).replace(day=1)
        end_date = start_date + timedelta(days=31)
    elif period == 'last_3_months':
        start_date = (end_date - timedelta(days=90)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'last_6_months':
        start_date = (end_date - timedelta(days=180)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        # If "all" is selected, we don't filter by date
        merchandise = Merchandise.query.all()
        return render_template('merch-view_merch.html', merch=merchandise)

    merchandise = Merchandise.query.filter(Merchandise.date_added >= start_date, Merchandise.date_added < end_date).all()
    return render_template('merch-view_merch.html', merch=merchandise)

@app.route('/view-discounts', methods=['GET'])
def view_discounts():
    discounts = Discount.query.all()
    return render_template('merch-view-discounts.html', discounts=discounts)

@app.route('/delete-discount/<int:discount_id>', methods=['POST'])
def delete_discount(discount_id):
    discount = Discount.query.get_or_404(discount_id)
    db.session.delete(discount)
    db.session.commit()
    return redirect(url_for('view_discounts'))

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    item = Merchandise.query.get_or_404(item_id)
    return render_template('merch-item.html', item=item)

@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    db.session.delete(cart_item)
    db.session.commit()
    return redirect(url_for('cart'))

if __name__ == '__main__':
    app.run(debug=True)
