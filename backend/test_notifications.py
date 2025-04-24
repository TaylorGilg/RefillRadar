import os
import sys
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import app modules
from backend.database.security import OfflineAuthenticator
from backend.notifications import NotificationEnabledDatabaseManager

def setup_test_db():
    """Set up test database with authentication"""
    load_dotenv()  # Load environment variables
    
    # Get secret key or use default for testing
    app_secret_key = os.getenv("APP_SECRET_KEY") or "test_secret_key"
    
    # Create temp database path
    test_db_path = os.path.join(os.path.expanduser("~"), "refillradar_test.db")
    
    # Initialize authenticator
    authenticator = OfflineAuthenticator(app_secret_key=app_secret_key)
    
    # Create database manager with notification support
    db_manager = NotificationEnabledDatabaseManager(
        db_path=test_db_path,
        authenticator=authenticator
    )
    
    print(f"Test database created at: {test_db_path}")
    return db_manager

def create_test_user_and_meds(db_manager):
    """Create test user and medications with imminent notifications"""
    # Create test user
    try:
        user = db_manager.register_user(
            username="test_user",
            password="test_password",
            email="test@example.com"
        )
        print(f"Created test user with ID: {user.id}")
    except ValueError as e:
        # User might already exist
        print(f"Error creating user: {e}")
        user = db_manager.authenticate_user("test_user", "test_password")
        print(f"Authenticated existing user with ID: {user.id}")
    
    # Create test medications with reminders at various intervals
    now = datetime.now()
    
    medications = [
        {
            "med_name": "Test Med 1",
            "icon": 1,
            "color": 2,
            "details": "15-second reminder test",
            "max_dosage": 1,
            "dosage_interval": 2,
            "dosage_frequency": "DAY(S)",
            "total_supply": 30,
            "start_date": now,
            "duration_prior": 7,  # 7 days prior
            "reminder_unit": "DAY(S)",
            "repeat_reminders": 2,
            "repeat_intervals": 1,
            "repeat_unit": "DAY(S)"
        },
        {
            "med_name": "Test Med 2",
            "icon": 2,
            "color": 3,
            "details": "30-second reminder test",
            "max_dosage": 2,
            "dosage_interval": 2,
            "dosage_frequency": "DAY(S)",
            "total_supply": 60,
            "start_date": now,
            "duration_prior": 14,  # 14 days prior
            "reminder_unit": "DAY(S)",
            "repeat_reminders": 1,
            "repeat_intervals": 2,
            "repeat_unit": "DAY(S)"
        }
    ]
    
    for i, med_data in enumerate(medications):
        try:
            db_manager.add_medication(user.id, **med_data)
            print(f"Added test medication {i+1}")
        except Exception as e:
            print(f"Error adding medication {i+1}: {e}")
    
    return user.id

def force_immediate_notifications(db_manager, user_id):
    """Force immediate notifications for testing"""
    # Cancel any existing reminders
    db_manager.notification_scheduler.cancel_all_reminders()
    
    # Create immediate test notifications
    now = datetime.now()
    test_reminders = [
        (now + timedelta(seconds=15)).isoformat(),
        (now + timedelta(seconds=30)).isoformat(),
        (now + timedelta(seconds=45)).isoformat()
    ]
    
    # Schedule test notifications
    for i, reminder in enumerate(test_reminders):
        db_manager.notification_scheduler.schedule_medication_reminders(
            [reminder],
            f"Test Med {i+1}"
        )
        print(f"Scheduled test notification {i+1} for {reminder}")
    
    print("\nNotifications have been scheduled to trigger in 15, 30, and 45 seconds.")
    print("Keeping application alive to receive notifications...")
    
    try:
        # Keep app running to allow notifications to fire
        for i in range(60):
            time.sleep(1)
            if i % 10 == 0:
                print(f"Waiting... {i}/60 seconds elapsed")
    except KeyboardInterrupt:
        print("Test interrupted by user")
    finally:
        print("Test complete. Shutting down scheduler...")
        db_manager.notification_scheduler.shutdown_scheduler()

def run_normal_load_test(db_manager, user_id):
    """Test loading existing reminders"""
    print("\nTesting loading of existing medication reminders...")
    
    # Load all reminders for existing medications
    db_manager.load_all_reminders(user_id)
    
    print("Existing reminders loaded and scheduled.")
    print("Future reminders will fire at their scheduled times.")
    
    # Let the app run for a while to process any immediate notifications
    try:
        for i in range(30):
            time.sleep(1)
            if i % 10 == 0:
                print(f"Waiting... {i}/30 seconds elapsed")
    except KeyboardInterrupt:
        print("Test interrupted by user")
    finally:
        print("Test complete. Shutting down scheduler...")
        db_manager.notification_scheduler.shutdown_scheduler()

if __name__ == "__main__":
    print("=== Testing RefillRadar Notifications ===")
    print("Setting up test environment...")
    
    db_manager = setup_test_db()
    user_id = create_test_user_and_meds(db_manager)
    
    # Test mode selection
    print("\nSelect test mode:")
    print("1. Force immediate test notifications (15, 30, 45 seconds)")
    print("2. Load existing medication reminders")
    
    try:
        choice = input("Enter your choice (1 or 2): ")
        if choice == "1":
            force_immediate_notifications(db_manager, user_id)
        elif choice == "2":
            run_normal_load_test(db_manager, user_id)
        else:
            print("Invalid choice. Exiting.")
    except Exception as e:
        print(f"Error during testing: {e}")