from datetime import datetime
from typing import List
from backend.database.db_manager import OfflineDatabaseManager
from backend.database.calc_reminders import deserialize_reminder_dates
from plyer import notification
from apscheduler.schedulers.background import BackgroundScheduler

class MedicationReminderScheduler:
    def __init__(self):
        """
        Initialize a background scheduler for medication reminders
        """
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
    
    def schedule_medication_reminders(self, reminder_dates: List[str], medication_name: str = None):
        """
        Schedule medication reminders
        
        Args:
            reminder_dates (List[str]): List of ISO format dates for reminders
            medication_name (str, optional): Name of medication for the notification
        """
        for date_str in reminder_dates:
            # Convert ISO format date to datetime
            reminder_date = datetime.fromisoformat(date_str)
            
            # Only schedule future reminders
            if reminder_date > datetime.now():
                # Schedule notification
                self.scheduler.add_job(
                    self._send_notification, 
                    'date', 
                    run_date=reminder_date
                )
                print(f"Scheduled reminder for {date_str} - {medication_name if medication_name else 'medication'}")
    
    def _send_notification(self):
        """
        Send a local notification
        
        Args:
            medication_name (str, optional): Name of the medication to remind about
        """
        try:
            message = "One of your medications requires attention. A refill is needed soon!" 
            notification.notify(
                title='Medication Refill Reminder',
                message=message,
                app_icon=None,  # e.g. 'path/to/app_icon.png'
                timeout=10  # seconds
            )
            print(f"Notification sent: {message}")
        except Exception as e:
            print(f"Notification error: {e}")
    
    def cancel_all_reminders(self):
        """
        Cancel all scheduled reminders
        """
        self.scheduler.remove_all_jobs()
    
    def shutdown_scheduler(self):
        """
        Shutdown the scheduler
        """
        self.scheduler.shutdown()

# Integration with Database Manager
class NotificationEnabledDatabaseManager(OfflineDatabaseManager):
    def __init__(self, *args, **kwargs):
        """
        Initialize with notification scheduler
        """
        super().__init__(*args, **kwargs)
        self.notification_scheduler = MedicationReminderScheduler()
    
    def add_medication(self, user_id: int, **medication_data):
        """
        Override add_medication to automatically schedule reminders
        
        Args:
            user_id (int): ID of the user
            **medication_data: Medication details
        
        Returns:
            Medication: Created medication with scheduled notifications
        """
        # Add medication using parent method
        medication = super().add_medication(user_id, **medication_data)
        
        # Get the decrypted medication data
        user_medications = self.get_user_medications(user_id)
        
        # Find the newly added medication
        for med in user_medications:
            if med['id'] == medication.id:
                # Schedule notifications using the decrypted reminder dates
                self.notification_scheduler.schedule_medication_reminders(
                    med['reminder_dates'],
                    med['med_name']
                )
                break
        
        return medication
    
    def load_all_reminders(self, user_id: int):
        """
        Load and schedule all reminders for a user's medications
        
        Args:
            user_id (int): ID of the user
        """
        # Get all user medications with decrypted data
        user_medications = self.get_user_medications(user_id)
        
        # Clear any existing reminders
        self.notification_scheduler.cancel_all_reminders()
        
        # Schedule reminders for each medication
        for med in user_medications:
            if 'reminder_dates' in med and med['reminder_dates']:
                self.notification_scheduler.schedule_medication_reminders(
                    med['reminder_dates'],
                    med['med_name']
                )
