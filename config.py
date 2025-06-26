import os

DB_USER = "sheworks_user"  #  database user
DB_PASSWORD = "sheworkslms"  #  password
DB_NAME = "sheworks_db"  #  database name
INSTANCE_CONNECTION_NAME = "sheworkslms:asia-southeast1:sheworks-mysql"  # region & instance
SECRET_KEY = os.getenv("SECRET_KEY")  # Replace with a strong random string

# SQLALCHEMY_DATABASE_URI = (
#     f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}"
#     f"?unix_socket=/cloudsql/{INSTANCE_CONNECTION_NAME}"
# )
SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@/{DB_NAME}"
    f"?unix_socket={os.path.join(os.path.dirname(__file__), 'cloudsql', INSTANCE_CONNECTION_NAME)}"
)

SQLALCHEMY_TRACK_MODIFICATIONS = False

STORAGE_BUCKET = "sheworks-uploads"

# Email service configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")  # Set this in Cloud Run environment variables
MAIL_DEFAULT_SENDER = "contact@sanaterra.info"  # Use a verified email in SendGrid