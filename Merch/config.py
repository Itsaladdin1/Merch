import os

class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///merch.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    STRIPE_PUBLIC_KEY = 'pk_test_51PUzFcP5lJfzmHx5zJFstT6C4W2uw7S7yO61UaZdcoxH1mq6V53OOWQpDr38G14Z3whsWGhxNrx85fksWAQj62D6002fgMb5Yb'
    STRIPE_SECRET_KEY = 'sk_test_51PUzFcP5lJfzmHx5DPkdO8IP3TSai3UGxU7olJTx2QLvlJxbTcu2dFAMbsT2d8X3H3v4JRtVtFvYjrJlSXZiRwut00D0420zYw'
