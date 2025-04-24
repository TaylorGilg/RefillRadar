
#   This file defines the prescription screen which displays detailed medication
#   information. It loads the corresponding .kv file layout and uses the database
#   manager to fetch and decrypt the data of the respective medication selected via the home page.

from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivy.app import App
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton
from datetime import datetime

from backend.database.db_instance import db_manager 

# Load the KV layout file that defines the visual interface for this screen.
Builder.load_file("frontend/kv/prescription_screen.kv")

#   Define mapping dictionaries to translate numeric codes into icon names and
#   RGBA color values. These mappings are used to display the appropriate icon and
#   color styling on the medication information screen.

ICON_MAP = {
    1: "pill",
    2: "minus-circle",
    3: "bottle-tonic",
    4: "medication",
    5: "bottle-tonic-plus-outline",
    6: "needle"
}
COLOR_MAP = {
    1: (1, 0, 0, 1), # RED
    2: (0, 0.5, 0.5, 1), # TEAL
    3: (0, 0, 1, 1), # DARK BLUE
    4: (1, 1, 0, 1), # YELLOW
    5: (1, 0.5, 0, 1), # ORANGE
    6: (1, 0.08, 0.58, 1), # PINK
    7: (0.73, 0.33, 0.83, 1), # PURPLE
    8: (0.13, 0.55, 0.13, 1), # FOREST GREEN
    9: (0.53, 0.81, 0.98, 1), # LIGHT BLUE
}

#   Represents the screen where detailed information about a specific medication is
#   displayed. Handles loading, formatting, and displaying medication data from
#   the backend, as well as navigating to the edit screen.
class MedicationInformationScreen(MDScreen):

    def load_medication_data(self, med_data):
        """
            Populate the screen widgets with the medication data passed as a dictionary.
            This includes basic fields like medication name, details, dosage, start date,
            start time, reminder settings, and visual elements like icons and colors.
        """
        # Populate basic fields with the decrypted values from med_data.
        self.ids.med_name_input.text = med_data.get("med_name", "")
        self.ids.medication_box.text = med_data.get("details", "")
        self.ids.dosage_label.text = str(med_data.get("max_dosage", ""))
        dosage_interval = med_data.get("dosage_interval", "")
        self.ids.dosage_occurrence_label.text = str(dosage_interval) if dosage_interval else ""
        self.ids.dosage_unit_label.text = str(med_data.get("dosage_frequency", ""))
        self.ids.supply_label.text = str(med_data.get("total_supply", ""))

        # Process start_date to update the Day/Month/Year labels on the screen.
        start_date = med_data.get("start_date")
        dt_date = None
        # Check if start_date is already a datetime object.
        if isinstance(start_date, datetime):
            dt_date = start_date
        else:
            try:
                # Attempt to parse the start_date string in the format "MM/DD/YYYY".
                dt_date = datetime.strptime(start_date, "%m/%d/%Y")
            except Exception:
                try:
                    # Fallback: attempt to parse start_date using ISO format.
                    dt_date = datetime.fromisoformat(start_date)
                except Exception:
                    dt_date = None
        if dt_date:
            self.ids.start_day_label.text = str(dt_date.day)
            self.ids.start_month_label.text = dt_date.strftime("%B")
            self.ids.start_year_label.text = str(dt_date.year)

        # Process start_time to extract and format hour, minute, and period (AM/PM).
        start_time = med_data.get("start_time")
        dt_time = None
        if start_time:
            if isinstance(start_time, datetime):
                dt_time = start_time
            else:
                try:
                    # Attempt to parse time in "%I:%M %p" format (12-hour format).
                    dt_time = datetime.strptime(start_time, "%I:%M %p")
                except Exception:
                    try:
                        # Fallback: attempt to parse time using ISO format.
                        dt_time = datetime.fromisoformat(start_time)
                    except Exception:
                        dt_time = None
        if dt_time:
            hour = dt_time.hour
            minute = dt_time.minute
            period = "AM" if hour < 12 else "PM"
            hour_12 = hour % 12 or 12  # Convert hour to 12-hour format.
            self.ids.hour_label.text = str(hour_12)
            self.ids.minute_label.text = f"{minute:02d}"  # Formats minute as two digits.
            self.ids.ampm_label.text = period

        # Set reminder details from med_data.
        self.ids.reminder_prior_label.text = str(med_data.get("duration_prior", ""))
        self.ids.reminder_prior_unit_label.text = med_data.get("reminder_unit", "")
        self.ids.repeat_label.text = str(med_data.get("repeat_reminders", ""))
        self.ids.repeat2_label.text = str(med_data.get("repeat_intervals", ""))
        self.ids.repeat_every_unit_label.text = med_data.get("repeat_unit", "")

        # Map the numeric icon value to the corresponding icon string and update the widget.
        icon_value = med_data.get("icon", 1)
        # Convert icon_value to int if it comes as a digit string.
        if isinstance(icon_value, str) and icon_value.isdigit():
            icon_value = int(icon_value)
        icon_str = ICON_MAP.get(icon_value, "pill")
        self.ids.icon_button.icon = icon_str
        
        # Map the numeric color value to the corresponding RGBA value for visual styling.
        color_value = med_data.get("color", 1)
        # Convert color_value to int if necessary.
        if isinstance(color_value, str) and color_value.isdigit():
            color_value = int(color_value)
        color_val = COLOR_MAP.get(color_value, (0, 0, 0, 1))
        # Apply the color to both the icon and the background of the color button.
        self.ids.color_button.icon_color = color_val  # Set the icon color.
        self.ids.color_button.md_bg_color = color_val  # Set the background color.

    def on_enter(self):
        """
            Automatically called by the Kivy framework when the screen becomes visible.
            It checks whether a medication identifier (med_id) is set, retrieves the
            decrypted medication data for the logged-in user from the database, and
            loads the data into the screen.
        """
        # Check if the medication identifier was provided (typically set by another screen).
        if hasattr(self, "med_id") and self.med_id:
            user_id = App.get_running_app().user_id
            try:
                # Retrieve decrypted medication data using the database manager.
                med_data = db_manager.get_medication_by_id(user_id, self.med_id)
                self.load_medication_data(med_data)
                self.med_data = med_data  # Store the data for later use.
            except Exception as e:
                print("Error loading medication data:", e)
        else:
            print("No medication_id provided; cannot load medication data.")

    def goto_edit(self):
        """
            Transitions the user to the prescription editing screen. It transfers the
            current medication data (med_data) and identifier (med_id) to the edit screen,
            so that the user can modify the details.
        """
        # Obtain the edit screen instance from the screen manager.
        edit_screen = self.manager.get_screen("edit_prescription")
        # Pass the current medication data and id to the edit screen.
        edit_screen.med_data = self.med_data
        edit_screen.med_id = self.med_id
        # Change the current screen to the edit screen.
        self.manager.current = "edit_prescription"
