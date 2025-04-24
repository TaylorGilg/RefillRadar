from datetime import datetime, timedelta
from typing import Optional, List, Dict
import math

class MedicationReminderCalculator:
    @staticmethod
    def calculate_end_date(
        start_date: datetime,
        max_dosage: int,
        dosage_frequency: str, 
        total_supply: int, 
        dosage_interval: int,
        start_time: Optional[datetime] = None,
    ) -> datetime:
        """
        Calculate medication end date based on dosage and supply, taking into account a dosing interval.
        
        For example, if max_dosage is 3 pills, total_supply is 30 pills, and the dosing interval is 3 days,
        then the number of doses is ceil(30/3) = 10, and the time from the first to the last dose will be
        (10 - 1) * 3 = 27 days.
        
        Args:
            start_date (datetime): Date medication starts.
            max_dosage (int): Number of pills taken per dose.
            dosage_frequency (str): Frequency unit ("HOUR(S)", "DAY(S)", or "WEEK(S)").
            total_supply (int): Total number of pills.
            dosage_interval (int, optional): Interval between doses in the given time unit. Defaults to 1.
            start_time (Optional[datetime]): Specific start time for hourly dosage.
        
        Returns:
            datetime: Calculated end date of medication supply.
        """
        
        # Adjust start date if start_time is provided for hourly dosage
        base_date = start_time if dosage_frequency == 'HOUR(S)' and start_time else start_date

        # Compute number of doses (round up in case of non-integer division)
        doses = math.ceil(total_supply / max_dosage)
        # If only one dose is available, no additional time passes.
        additional_doses = doses - 1 if doses > 0 else 0

        if dosage_frequency == 'HOUR(S)':
            return base_date + timedelta(hours=additional_doses * dosage_interval)
        elif dosage_frequency == 'DAY(S)':
            return base_date + timedelta(days=additional_doses * dosage_interval)
        elif dosage_frequency == 'WEEK(S)':
            return base_date + timedelta(weeks=additional_doses * dosage_interval)
        else:
            raise ValueError(f"Invalid dosage frequency: {dosage_frequency}")
        
    @staticmethod
    def calculate_reminder_dates(
        end_date: datetime, 
        duration_prior: int, 
        reminder_unit: str,
        repeat_reminders: int,
        repeat_intervals: int,
        repeat_unit: str,
        default_reminder_time: Optional[Dict[str, int]] = None
    ) -> List[datetime]:
        """
        Calculate reminder dates for medication refill

        Args:
            end_date (datetime): Date medication runs out
            duration_prior (int): How many time units before end date to start reminders
            reminder_unit (str): Unit of duration prior (week/day/hour)
            repeat_reminders (int): Number of repeat reminders
            repeat_intervals (int): Interval between repeat reminders
            repeat_unit (str): Unit of repeat intervals (week/day/hour)
            default_reminder_time (dict, optional): Default time for reminders (Default is 8:00 AM if not specified)

        Returns:
            List[datetime]: List of reminder dates
        """
        # Set default reminder time if not provided
        if default_reminder_time is None:
            default_reminder_time = {'hour': 8, 'minute': 0}

        # Calculate first reminder date
        if reminder_unit == 'WEEK(S)':
            first_reminder = end_date - timedelta(weeks=duration_prior)
        elif reminder_unit == 'DAY(S)':
            first_reminder = end_date - timedelta(days=duration_prior)
        elif reminder_unit == '(HOUR(S))':
            first_reminder = end_date - timedelta(hours=duration_prior)
        else:
            raise ValueError(f"Invalid reminder unit: {reminder_unit}")
        
        # Set default time for first reminder
        first_reminder = first_reminder.replace(
            hour=default_reminder_time['hour'], 
            minute=default_reminder_time['minute'], 
            second=0, 
            microsecond=0
        )

        # Calculate additional reminder dates
        reminder_dates = [first_reminder]

        for i in range(1, repeat_reminders + 1):
            if repeat_unit == 'WEEK(S)':
                next_reminder = first_reminder + timedelta(weeks=i * repeat_intervals)
            elif repeat_unit == 'DAY(S)':
                next_reminder = first_reminder + timedelta(days=i * repeat_intervals)
            elif repeat_unit == 'HOUR(S)':
                next_reminder = first_reminder + timedelta(hours=i * repeat_intervals)
            else:
                raise ValueError(f"Invalid repeat unit: {repeat_unit}")
            
            reminder_dates.append(next_reminder)

        return reminder_dates

    @staticmethod
    def serialize_reminder_dates(reminder_dates: List[datetime]) -> List[str]:
            """
            Convert datetime reminder dates to ISO format strings for JSON storage
            
            Args:
                reminder_dates (List[datetime]): List of reminder dates
            
            Returns:
                List[str]: List of ISO format date strings
            """
            return [date.isoformat() for date in reminder_dates]

def process_medication_reminders(medication, default_reminder_time=None):
    """
    Process a medication object to calculate end date and reminders
        
    Args:
        medication (Medication): Medication model instance
        default_reminder_time (dict, optional): Default time for reminders
        
    Returns:
        dict: Processed medication with calculated end date and reminder dates
    """
    # Calculate end date
    end_date = MedicationReminderCalculator.calculate_end_date(
        start_date=medication.start_date,
        max_dosage=medication.max_dosage,
        dosage_interval=medication.dosage_interval,
        dosage_frequency=medication.dosage_frequency,
        total_supply=medication.total_supply,
        start_time=medication.start_time,
    )

    # Update medication's end date
    medication.end_date = end_date

    # Calculate reminder dates
    reminder_dates = MedicationReminderCalculator.calculate_reminder_dates(
        end_date=end_date,
        duration_prior=medication.duration_prior,
        reminder_unit=medication.reminder_unit,
        repeat_reminders=medication.repeat_reminders,
        repeat_intervals=medication.repeat_intervals,
        repeat_unit=medication.repeat_unit,
        default_reminder_time=default_reminder_time
    )

    # Serialize reminder dates
    serialized_reminder_dates = MedicationReminderCalculator.serialize_reminder_dates(reminder_dates)
        
    # Update medication with serialized reminder dates
    medication.reminder_dates = serialized_reminder_dates

    return {
        'medication': medication,
        'end_date': end_date,
        'reminder_dates': reminder_dates
    }

def deserialize_reminder_dates(serialized_dates: List[str]) -> List[datetime]:
    """
    Convert ISO format date strings back to datetime objects
        
    Args:
        serialized_dates (List[str]): List of ISO format date strings
        
    Returns:
        List[datetime]: List of datetime objects
    """
    return [datetime.fromisoformat(date_str) for date_str in serialized_dates]