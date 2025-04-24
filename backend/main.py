from backend.database.db_manager import OfflineDatabaseManager
from backend.database.db_instance import db_manager
from backend.database.security import OfflineAuthenticator
from datetime import datetime
import os

def main():
    
    # Database tables will be automatically created during initialization
    print("Database and tables created successfully!")
    
    # Optional: Create a test user
    try:
        test_user = db_manager.register_user(
            username="test_user",
            password="secure_password",
            email="test@example.com"
        )
        print(f"Test user created with ID: {test_user.id}")
    except ValueError as e:
        print(f"Couldn't create test user: {e}")
    
    # Optional: Add a test medication
    try:
        med = db_manager.add_medication(
            user_id=1,  # Assuming first user has ID 1
            med_name="Test Medication",
            icon=1,
            color=2,
            details="Test medication details",
            max_dosage=2,
            dosage_interval=2,
            dosage_frequency="DAY(S)",
            total_supply=60,
            start_date=datetime.now(),
            duration_prior=7,
            reminder_unit="DAY(S)",
            repeat_reminders=3,
            repeat_intervals=1,
            repeat_unit="DAY(S)"
        )
        print(f"Test medication added with ID: {med.id}")
    except Exception as e:
        print(f"Couldn't add test medication: {e}")

if __name__ == "__main__":
    main()