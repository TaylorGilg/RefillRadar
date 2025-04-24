from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone 
from typing import Dict, Any


Base = declarative_base()

class User(Base):
    """ Stores user information securely """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)  # Store only hashed passwords
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to medications
    medications = relationship("Medication", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert user to dictionary, excluding sensitive data
        
        Returns:
            dict: User data representation
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at
        }

class Medication(Base):
    """ Stores user medication information securely """
    __tablename__ = "medications"

    # General Medication Input 

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    med_name = Column(String, nullable=False) 
    icon = Column(Integer, nullable=False) # Choice of icon representation (Option 1 through 6)
    color = Column(Integer, nullable=False) # Choice of color representation (Option 1 through 10)
    details = Column(Text, nullable=True)  # Stores background info of medication (JSON string)

    max_dosage = Column(Integer, nullable=False)  # Max dosage taken per time unit
    dosage_interval = Column(Integer, nullable=False, default=1) # Interval at which max dosage is taken
    dosage_frequency = Column(String, nullable=False) # Medication taken on hour, day, or week basis

    total_supply = Column(Integer, nullable=False) 

    start_date = Column(String, nullable=False) # When user starts using medication (string for encrypted datetime)
    start_time = Column(String, nullable=True) # Time when first dose is taken (optional) (string for encrypted datetime)

    # Calculated End Date of Medication Supply

    end_date = Column(String, nullable=False) # String for encrypted datetime value

    # Reminder Settings

    duration_prior = Column(Integer, nullable=False) # How many (weeks/days/hours) before running out to trigger first reminder
    reminder_unit = Column(String, nullable=False) # Reminders on hour, day, or weekly basis

    repeat_reminders = Column(Integer, nullable=False) # Number of repeat reminders (after first reminder)
    repeat_intervals = Column(Integer, nullable=False)  # How often secondary reminders repeat
    repeat_unit = Column(String, nullable=False) # Reminder repeats on hour, day, or week basis

    reminder_dates = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to user
    user = relationship("User", back_populates="medications")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert medication to dictionary
        
        Returns:
            dict: Medication data representation
        """
        base_dict = {
            "id": self.id,
            "user_id": self.user_id,
            "med_name": self.med_name,
            "icon": self.icon,
            "color": self.color,
            "details": self.details if self.details else None,
            "max_dosage": self.max_dosage,
            "dosage_interval": self.dosage_interval, 
            "dosage_frequency": self.dosage_frequency,
            "total_supply": self.total_supply, 
            "start_date": self.start_date, 
            "start_time": self.start_time if self.start_time else None, 
            "end_date": self.end_date, 
            "duration_prior": self.duration_prior, 
            "reminder_unit": self.reminder_unit, 
            "repeat_reminders": self.repeat_reminders, 
            "repeat_intervals": self.repeat_intervals,
            "repeat_unit": self.repeat_unit,
            "reminder_dates": self.reminder_dates
        }
        return base_dict

    
