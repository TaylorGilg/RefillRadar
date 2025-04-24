import os
from backend.database.db_manager import OfflineDatabaseManager
from backend.database.security import OfflineAuthenticator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load the secret key from environment variables
app_secret_key = os.getenv("APP_SECRET_KEY")
if not app_secret_key:
    raise Exception("APP_SECRET_KEY is not set in the environment!")

# Create the authenticator using the secret key
authenticator = OfflineAuthenticator(app_secret_key=app_secret_key)

# Define the database path (adjust as needed)
home_dir = os.path.expanduser("~")
db_path = os.path.join(home_dir, "Documents", "refillradar_db.db")

print(f"Creating database at: {db_path}")

# Initialize the shared database manager instance
db_manager = OfflineDatabaseManager(db_path, authenticator=authenticator)