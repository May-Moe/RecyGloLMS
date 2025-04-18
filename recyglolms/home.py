from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def homepage():
    return render_template('shework.html')  # Just shows the homepage
