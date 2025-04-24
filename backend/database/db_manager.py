import os
import sqlite3
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models import Base, User, Medication
from backend.database.security import OfflineAuthenticator
from backend.database.calc_reminders import process_medication_reminders

class OfflineDatabaseManager:
    def __init__(self, db_path: str = None, authenticator: OfflineAuthenticator = None):
        """
        Initialize offline database with secure management
        
        Args:
            db_path (str, optional): Custom database path
            authenticator (OfflineAuthenticator, optional): Custom authenticator
        """
        # Default database path in user's documents
        if not db_path:
            home_dir = os.path.expanduser("~")
            db_path = os.path.join(home_dir, "Documents", "refillradar_db.db")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create database engine
        self.engine = create_engine(f'sqlite:///{db_path}')
        
        # Create session factory
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Initialize authenticator
        self.authenticator = authenticator or OfflineAuthenticator()
        
        # Create tables
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        Base.metadata.create_all(self.engine)
    
    def register_user(self, username: str, password: str, email: str) -> User:
        """
        Register a new user securely
        
        Args:
            username (str): User's username
            password (str): User's password
            email (str): User's email
        
        Returns:
            User: Newly created user
        """
        session = self.SessionLocal()

        # Additional validation
        if not username.strip() or not password.strip() or not email.strip():
            raise ValueError("Username, password, and email cannot be blank")
        
        try:
            # Check for existing user
            existing_user = session.query(User).filter(
                (User.username == username) | 
                (User.email == email)
            ).first()
            
            if existing_user:
                raise ValueError("Username or email already exists")
            
            # Create new user
            hashed_password = self.authenticator.hash_password(password)
            encrypted_email = self.authenticator.encrypt_sensitive_data(email)
            
            new_user = User(
                username=username, 
                password_hash=hashed_password, 
                email=encrypted_email
            )
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            return new_user
        
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def authenticate_user(self, username: str, password: str) -> User:
        """
        Authenticate a user
        
        Args:
            username (str): User's username
            password (str): User's password
        
        Returns:
            User: Authenticated user
        """
        session = self.SessionLocal()
        
        try:
            user = session.query(User).filter(
                User.username == username
            ).first()
            
            if not user:
                raise ValueError("User not found")
            
            # Verify password
            if not self.authenticator.verify_password(user.password_hash, password):
                raise ValueError("Invalid credentials")
            
            return user
        
        finally:
            session.close()
    
    def add_medication(self, user_id: int, **medication_data) -> Medication:
        """
        Add a medication for a user
        
        Args:
            user_id (int): User's ID
            **medication_data: Medication details
        
        Returns:
            Medication: Newly created medication
        """
        session = self.SessionLocal()
        
        try:
            # Verify user exists
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            # Create medication instance
            new_medication = Medication(user_id=user_id, **medication_data)

            # Process medication to calculate end date and reminders
            processed_result = process_medication_reminders(new_medication)
            processed_med = processed_result['medication']

            # Fields to be encrypted
            sensitive_fields = {
                "med_name": str,
                "details": str,
                "max_dosage": str,   # integer: convert to string
                "dosage_interval": str, #integer: convert to string
                "dosage_frequency": str,
                "total_supply": str,     # integer: convert to string
                "start_date": lambda d: d.isoformat() if isinstance(d, datetime) else str(d),
                "start_time": lambda t: t.isoformat() if isinstance(t, datetime) else str(t),
                "end_date": lambda d: d.isoformat() if isinstance(d, datetime) else str(d),
                "duration_prior": str,   # integer: convert to string
                "reminder_unit": str,
                "repeat_reminders": str,     # integer: convert to string
                "repeat_intervals": str,     # integer: convert to string
                "repeat_unit": str,
                "reminder_dates": lambda rd: json.dumps(rd) if isinstance(rd, list) else str(rd)
            }

            # Encrypt sensitive fields
            for field, serializer in sensitive_fields.items():
                value = getattr(processed_med, field, None)
                if value is not None:
                    value_str = serializer(value)
                    encrypted_value = self.authenticator.encrypt_sensitive_data(value_str)
                    setattr(processed_med, field, encrypted_value)
            
            # Store the processed (and now encrypted) medication in the database
            session.add(processed_med)
            session.commit()
            session.refresh(processed_med)
            return processed_med
        
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_user_medications(self, user_id: int) -> list:
        """
        Retrieve all medications for a user
        
        Args:
            user_id (int): User's ID
        
        Returns:
            list: User's medications
        """
        session = self.SessionLocal()
        
        try:
            # Verify user exists
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            medications = session.query(Medication).filter(
                Medication.user_id == user_id
            ).all()
            result = []

            decryption_map = {
            "med_name": str,
            "details": str,
            "max_dosage": lambda v: int(v), 
            "dosage_interval": lambda v: int(v),
            "dosage_frequency": str,
            "total_supply": lambda v: int(v),
            "start_date": lambda d: datetime.fromisoformat(d),
            "start_time": lambda t: datetime.fromisoformat(t),
            "end_date": lambda d: datetime.fromisoformat(d),
            "duration_prior": lambda v: int(v),
            "reminder_unit": str,
            "repeat_reminders": lambda v: int(v),
            "repeat_intervals": lambda v: int(v),
            "repeat_unit": str,
            "reminder_dates": lambda rd: json.loads(rd)
            }
        
            for med in medications:
                med_dict = med.to_dict()
                for field, converter in decryption_map.items():
                    if med_dict.get(field):
                        decrypted_value = self.authenticator.decrypt_sensitive_data(med_dict[field])
                        try:
                            med_dict[field] = converter(decrypted_value)
                        except Exception as e:
                            # If conversion fails, fallback to the raw decrypted string
                            med_dict[field] = decrypted_value
                result.append(med_dict)
        
            return result
    
        finally:
            session.close()

    def get_medication_by_id(self, user_id: int, medication_id: int) -> dict:
        """
        Retrieve a single medication for a given user and medication id,
        decrypt its sensitive fields, and return a dictionary of unencrypted values.
        
        Args:
            user_id (int): The ID of the user.
            medication_id (int): The ID of the medication.

        Returns:
            dict: A dictionary with the medication's data decrypted.
        
        Raises:
            ValueError: If the medication is not found for the given user.
        """
        session = self.SessionLocal()
        try:
            # Verify user exists
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            medication = session.query(Medication).filter(
                Medication.user_id == user_id,
                Medication.id == medication_id
            ).first()
            
            if not medication:
                raise ValueError("Medication not found for this user.")
            
            med_dict = medication.to_dict()
            
            # Define converters for the sensitive fields.
            decryption_map = {
                "med_name": str,
                "details": str,
                "max_dosage": lambda v: int(v),
                "dosage_interval": lambda v: int(v),
                "dosage_frequency": str,
                "total_supply": lambda v: int(v),
                "start_date": lambda d: datetime.fromisoformat(d),
                "start_time": lambda t: datetime.fromisoformat(t) if t else None,
                "end_date": lambda d: datetime.fromisoformat(d) if d else None,
                "duration_prior": lambda v: int(v),
                "reminder_unit": str,
                "repeat_reminders": lambda v: int(v),
                "repeat_intervals": lambda v: int(v),
                "repeat_unit": str,
                "reminder_dates": lambda rd: json.loads(rd)
            }
            
            # Decrypt each field and convert to the correct type.
            for field, converter in decryption_map.items():
                if med_dict.get(field):
                    decrypted_value = self.authenticator.decrypt_sensitive_data(med_dict[field])
                    try:
                        med_dict[field] = converter(decrypted_value)
                    except Exception:
                        # If conversion fails, use the raw decrypted value.
                        med_dict[field] = decrypted_value
                        
            return med_dict
        
        finally:
            session.close()

    def update_medication(self, user_id: int, medication_id: int, **updated_data) -> Medication:
        """
        Update an existing medication record with new values.
        
        Args:
            user_id (int): The user's ID.
            medication_id (int): The ID of the medication to update.
            **updated_data: The fields to update and their new values.
        
        Returns:
            Medication: The updated medication object.
        
        Raises:
            ValueError: If the medication is not found.
        """
        session = self.SessionLocal()
        try:
            med = session.query(Medication).filter(
                Medication.user_id == user_id,
                Medication.id == medication_id
            ).first()
            if not med:
                raise ValueError("Medication not found")

            # Update the medication's fields.
            for key, value in updated_data.items():
                setattr(med, key, value)

            # Re-process the medication to calculate reminders and end date if needed.
            # This reuses the same processing logic as adding a new medication.
            processed_result = process_medication_reminders(med)
            processed_med = processed_result['medication']

            # Encrypt sensitive fields using your encryption scheme.
            sensitive_fields = {
                "med_name": str,
                "details": str,
                "max_dosage": str,   # integer: convert to string
                "dosage_interval": str, # integer: convert to string
                "dosage_frequency": str,
                "total_supply": str,     # integer: convert to string
                "start_date": lambda d: d.isoformat() if isinstance(d, datetime) else str(d),
                "start_time": lambda t: t.isoformat() if isinstance(t, datetime) else str(t),
                "end_date": lambda d: d.isoformat() if isinstance(d, datetime) else str(d),
                "duration_prior": str,   # integer: convert to string
                "reminder_unit": str,
                "repeat_reminders": str,     # integer: convert to string
                "repeat_intervals": str,     # integer: convert to string
                "repeat_unit": str,
                "reminder_dates": lambda rd: json.dumps(rd) if isinstance(rd, list) else str(rd)
            }

            for field, serializer in sensitive_fields.items():
                value = getattr(processed_med, field, None)
                if value is not None:
                    value_str = serializer(value)
                    encrypted_value = self.authenticator.encrypt_sensitive_data(value_str)
                    setattr(processed_med, field, encrypted_value)

            session.commit()
            session.refresh(processed_med)
            return processed_med

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def backup_database(self, backup_path: str):
        """
        Create a backup of the database
        
        Args:
            backup_path (str): Path to backup file
        """
        source_conn = sqlite3.connect(self.engine.url.database)
        backup_conn = sqlite3.connect(backup_path)
        source_conn.backup(backup_conn)
        backup_conn.close()
        source_conn.close()

# Usage example
offline_db = OfflineDatabaseManager()