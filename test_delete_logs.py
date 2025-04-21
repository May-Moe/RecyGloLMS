from recyglolms.__inti__ import app  # Import the app from __init__.py
from recyglolms.admin import delete_old_logs

with app.app_context():
    delete_old_logs()