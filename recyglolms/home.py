from flask import Blueprint, render_template

home_bp = Blueprint('main', __name__)

@home_bp.route('/')
def homepage():
    return render_template('shework.html')  # Just shows the homepage
