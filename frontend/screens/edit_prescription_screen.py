#   This file implements the EditPrescriptionScreen class using Kivy and KivyMD.
#   It provides a user interface for editing an existing medication prescription.
#   It includes functionality to load existing prescription data into the UI,
#   allow updates to medication details (including name, dosage, timing, reminders,
#   and icons/colors), and then save the updated prescription to the database.

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.graphics import Color, Line
from kivy.metrics import dp
from datetime import datetime, timedelta

from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton
from kivymd.uix.button import MDButtonText
from kivy.properties import NumericProperty, StringProperty

from backend.database.db_instance import db_manager

# Load the Kivy layout file associated with this screen.
Builder.load_file("frontend/kv/edit_prescription_screen.kv")


class EditPrescriptionScreen(MDScreen):
    # Properties for storing selected icon, color, and default date/time values.
    selected_icon_value = NumericProperty(0)
    selected_color_value = NumericProperty(0)

    def __init__(self, **kwargs):
        """
        Constructor for EditPrescriptionScreen.
        Initializes default states for the selected icon, color, supply button, and supply value.
        """
        super().__init__(**kwargs)
        self.selected_icon = None
        self.selected_color = [0, 0, 1, 1]  # Default color is blue in RGBA.
        self.selected_supply_button = None
        self.selected_supply = None


    def on_enter(self):
        """
        Called when the screen is entered.
        Loads the medication data for the given med_id from the database if available.
        If med_data is already set, it is used to populate the screen.
        """
        # Assume self.med_id is already set before switching to EditPrescriptionScreen.
        if hasattr(self, "med_id") and self.med_id:
            user_id = App.get_running_app().user_id
            try:
                if hasattr(self, "med_data") and self.med_data: 
                    self.load_medication_data(self.med_data)
                else:
                    med_data = db_manager.get_medication_by_id(user_id, self.med_id)
                    self.load_medication_data(med_data)
            except Exception as e:
                print("Error loading medication data:", e)
        else:
            print("No medication_id provided; cannot load medication data.")


    def on_kv_post(self, base_widget):
        """
        Callback once kv language rules are applied.
        Initializes the dropdown menus for selecting day, month, year, reminders, and time.
        Also schedules creation of dosage menus with a short delay.
        """
        self.create_day_menu()
        self.create_month_menu()
        self.create_year_menu()
        self.create_reminder_menus()
        self.create_time_menus()
        
        # Delay creation of dosage menus to allow proper initialization.
        Clock.schedule_once(self._create_dosage_menus_later, 0)


    def on_pre_enter(self):
        """
        Called right before the screen is shown.
        Sets the default values for the dosage dropdowns and updates the dosage summary to avoid blank fields.
        """
        self.ids.dosage_dropdown.children[0].text = "1"
        self.ids.dosage_unit_dropdown.children[0].text = "HOUR"
        self.ids.dosage_occurrence_dropdown.children[0].text = "1"
        self.update_dosage_summary()


    def load_medication_data(self, med_data):
        """
        Populate the editable fields with the data retrieved from the database.
        
        Args:
            med_data: A dictionary containing the medication data loaded from the database.
        """
        # Set medication name and ensure the field is editable.
        self.ids.med_name_input.text = med_data.get("med_name", "")
        self.ids.med_name_input.disabled = False
        
        # Set medication details and enable editing.
        self.ids.medication_box.text = med_data.get("details", "")
        self.ids.medication_box.disabled = False

        # Populate dosage fields with the corresponding values.
        self.ids.dosage_dropdown.children[0].text = str(med_data.get("max_dosage", ""))
        self.ids.dosage_occurrence_dropdown.children[0].text = str(med_data.get("dosage_interval", ""))
        self.ids.dosage_unit_dropdown.children[0].text = med_data.get("dosage_frequency", "")

        # Process start_date to update day, month, year labels
        start_date = med_data.get("start_date")
        dt_date = None
        if isinstance(start_date, datetime):
            dt_date = start_date
        else:
            try:
                dt_date = datetime.strptime(start_date, "%m/%d/%Y")
            except Exception:
                try:
                    dt_date = datetime.fromisoformat(start_date)
                except Exception:
                    dt_date = None
        if dt_date:
            self.ids.day_label.text = str(dt_date.day)
            self.ids.month_label.text = dt_date.strftime("%B")
            self.ids.year_label.text = str(dt_date.year)

        # Process start_time similarly
        start_time = med_data.get("start_time")
        dt_time = None
        if start_time:
            if isinstance(start_time, datetime):
                dt_time = start_time
            else:
                try:
                    dt_time = datetime.strptime(start_time, "%I:%M %p")
                except Exception:
                    try:
                        dt_time = datetime.fromisoformat(start_time)
                    except Exception:
                        dt_time = None
        if dt_time:
            hour = dt_time.hour
            minute = dt_time.minute
            period = "AM" if hour < 12 else "PM"
            hour_12 = hour % 12 or 12
            self.ids.hour_label.text = str(hour_12)
            self.ids.minute_label.text = f"{minute:02d}"
            self.ids.ampm_label.text = period

        # Set reminder settings and other details.
        self.ids.reminder_prior_label.text = str(med_data.get("duration_prior", ""))
        self.ids.reminder_prior_unit_label.text = med_data.get("reminder_unit", "")
        self.ids.repeat_label.text = str(med_data.get("repeat_reminders", ""))
        self.ids.repeat2_label.text = str(med_data.get("repeat_intervals", ""))
        self.ids.repeat_every_unit_label.text = med_data.get("repeat_unit", "")

        # Store the original med_data as an attribute:
        self.med_data = med_data

    # ------ Medication Icons & Colors ------
    def select_medication(self, icon_button):
        """
        Handle selection of a medication icon.
        Clears the border of previously selected icons, assigns the new selection,
        and draws a blue border to indicate selection.
        
        Args:
            icon_button: The button widget representing the medication icon.
        """
        for btn in self.ids.medication_buttons.children:
            btn.canvas.after.clear()
        self.selected_icon = icon_button

        # Extract and store the icon value from the custom attribute.
        self.selected_icon_value = getattr(icon_button, 'icon_value', 0)

        def draw_border(dt):
            # Compute the radius based on button dimensions and draw a border.
            radius = min(icon_button.width, icon_button.height) / 2 
            with icon_button.canvas.after:
                Color(0.2, 0.4, 1, 1)  # Blue border
                Line(circle=(icon_button.center_x, icon_button.center_y, radius), width=2)

        Clock.schedule_once(draw_border, 0)

    def select_color(self, color_button):
        """
        Handle selection of a color option.
        Clears the previous color border and draws a blue border around the newly selected color.
        
        Args:
            color_button: The button widget representing the color option.
        """
        if self.selected_color and hasattr(self.selected_color, "canvas"):
            self.selected_color.canvas.after.clear()

        self.selected_color = color_button

        # Extract and store the color value from the custom attribute.
        self.selected_color_value = getattr(color_button, 'color_value', 0)

        def draw_border(dt):
            radius = min(color_button.width, color_button.height) / 2 
            with color_button.canvas.after:
                Color(0.2, 0.4, 1, 1)  # Blue border for selection
                Line(circle=(color_button.center_x, color_button.center_y, radius), width=2)

        Clock.schedule_once(draw_border, 0)


    #------ Dosage Menus ------
    def _create_dosage_menus_later(self, dt):
        """
        Delayed creation of dosage-related dropdown menus after kv initialization.
        """
        self.create_dosage_menus()

    def _create_reminder_menus_later(self, dt):
        """
        Delayed creation of reminder menus.
        """
        self.create_reminder_menus()

    def create_dosage_menus(self):
        """
        Builds the dropdown menus for dosage settings:
          - Maximum dosage (values 1 to 10)
          - Dosage occurrence frequency (values 1 to 24)
          - Dosage unit (e.g., HOURS, DAYS, WEEKS)
        """
        max_dosage_items = [
            {"text": str(i), "on_release": lambda x=str(i): self.set_dosage(x)}
            for i in range(1, 11)
        ]
        self.max_dosage_menu = MDDropdownMenu(
            caller=self.ids.dosage_dropdown,
            items=max_dosage_items,
            width_mult=3,
        )

        occurrence_values = [str(i) for i in range(1, 25)]  # Every 1–24 hours.
        menu_items = [
            {"text": val, "on_release": lambda val=val: self.set_dosage_occurrence(val)}
            for val in occurrence_values
        ]
        self.dosage_occurrence_menu = MDDropdownMenu(
            caller=self.ids.dosage_occurrence_dropdown,
            items=menu_items,
            width_mult=3,
        )

        unit_items = [
            {"text": unit, "on_release": lambda unit=unit: self.set_dosage_unit(unit)}
            for unit in ["HOUR(S)", "DAY(S)", "WEEK(S)"]
        ]
        self.dosage_unit_menu = MDDropdownMenu(
            caller=self.ids.dosage_unit_dropdown,
            items=unit_items,
            width_mult=3,
            max_height=dp(200),
        )
        
    def open_dosage_dropdown(self, button):
        """
        Opens the maximum dosage dropdown menu.
        
        Args:
            button: The UI element triggering the dropdown.
        """
        self.max_dosage_menu.caller = button
        self.max_dosage_menu.open()

    def open_dosage_occurrence_dropdown(self, button):
        """
        Opens the dropdown menu for dosage occurrence.
        
        Args:
            button: The UI element triggering the dropdown.
        """
        self.dosage_occurrence_menu.caller = button
        self.dosage_occurrence_menu.open()

    def open_dosage_unit_dropdown(self, button):
        """
        Opens the dosage unit dropdown menu.
        
        Args:
            button: The UI element triggering the dropdown.
        """
        self.dosage_unit_menu.caller = button
        self.dosage_unit_menu.open()

    def set_dosage(self, value):
        """
        Sets the maximum dosage to the provided value and updates the display.
        
        Args:
            value: A string representing the selected dosage.
        """
        self.ids.dosage_dropdown.children[0].text = value
        self.max_dosage_menu.dismiss()
        self.update_dosage_summary()

    def set_dosage_unit(self, value):
        """
        Sets the dosage unit (HOUR(S), DAY(S), WEEK(S)) and updates the UI.
        
        Args:
            value: A string representing the dosage frequency unit.
        """
        self.ids.dosage_unit_dropdown.children[0].text = value
        self.dosage_unit_menu.dismiss()
        self.update_dosage_summary()

    def set_dosage_occurrence(self, value):
        """
        Sets the dosage occurrence frequency.
        
        Args:
            value: A string representing how many hours/days/weeks between doses.
        """
        self.ids.dosage_occurrence_label.text = value
        self.dosage_occurrence_menu.dismiss()

    def update_dosage_summary(self):
        """
        Updates and logs a summary of the dosage settings.
        Handles singular versus plural dose wording.
        """
        dosage = self.ids.dosage_dropdown.children[0].text
        unit = self.ids.dosage_unit_dropdown.children[0].text

        try:
            dose_int = int(dosage)
        except ValueError:
            dose_int = 1

        unit_clean = unit.lower()

        if dose_int == 1:
            unit_display = unit_clean
            dose_word = "dose"
        else:
            if unit_clean == "day":
                unit_display = "days"
            elif unit_clean == "hour":
                unit_display = "hours"
            elif unit_clean == "week":
                unit_display = "weeks"
            else:
                unit_display = unit_clean + "s"
            dose_word = "doses"

        print(f"Take {dosage} {dose_word} every {unit_display}")  # Developer log for debugging


    # ------ Supply Menus ------
    def select_supply_button(self, btn):
        """
        Called when a supply button is selected.
        Clears previous border (if any), applies a blue border to the new selection,
        and extracts the numeric supply value from the button label.

        Args:
            btn: The button widget representing a supply option (e.g., "30-days").
        """
        def apply_border(dt):
            # Remove border from previously selected supply button.
            if self.selected_supply_button:
                self._remove_existing_border(self.selected_supply_button)

            # Draw a new blue rounded rectangle border around the button.
            with btn.canvas.after:
                Color(0.2, 0.4, 1, 1) # BLUE (color for border)
                Line(
                    rounded_rectangle=(btn.x, btn.y, btn.width, btn.height, 20),
                    width=2
                )

            self.selected_supply_button = btn  # Update selected supply button 

            # Extract the supply number from the label text (e.g., "30-days" becomes 30).
            try:
                label = btn.children[0]
                self.selected_supply = int(label.text.split("-")[0])
            except Exception as e:
                print("⚠️ Supply parse error:", e)

        # Use a small delay before applying the border.
        Clock.schedule_once(apply_border, 0.05)

    def reset_supply_buttons(self):
        """
        Clears and re-creates the supply buttons to ensure there are no duplicates or broken buttons.
        """
        self.ids.supply_button_container.clear_widgets()

        supply_days = [30, 60, 90, 100]
        for day in supply_days:
            btn = MDButton(
                style="tonal",
                theme_text_color="Custom",
                text_color=(0, 0, 0, 1),
                size_hint=(None, None),
                width=dp(80),
                height=dp(40),
                radius=[20],
            )
            # Bind the button correctly to the selection function
            btn.on_release = lambda btn=btn: self.select_supply_button(btn)

            btn.add_widget(MDButtonText(text=f"{day}-Days"))
            self.ids.supply_button_container.add_widget(btn)

    def _remove_existing_border(self, button):
        """
        Helper function to remove just the border (Line) from a button's canvas.after.
        Preserves other visual effects like shadows or ripples.
        """
        if not button:
            return

        border_lines = [instr for instr in button.canvas.after.children if isinstance(instr, Line)]
        for line in border_lines:
            button.canvas.after.remove(line)


    # ------ Date Menus ------
    def create_day_menu(self):
        """
        Creates a dropdown menu for selecting day values (1 to 31).
        """
        days = [str(i) for i in range(1, 32)]
        menu_items = [{"text": day, "on_release": lambda day=day: self.set_day(day)} for day in days]
        self.day_menu = MDDropdownMenu(caller=self.ids.start_day_dropdown, items=menu_items, width_mult=3)

    def create_month_menu(self):
        """
        Creates a dropdown menu for selecting month names.
        """
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        menu_items = [{"text": month, "on_release": lambda month=month: self.set_month(month)} for month in months]
        self.month_menu = MDDropdownMenu(caller=self.ids.start_month_dropdown, items=menu_items, width_mult=3)

    def create_year_menu(self):
        """
        Creates a dropdown menu for selecting years (2025 to 2039).
        """
        years = [str(i) for i in range(2025, 2040)]
        menu_items = [{"text": year, "on_release": lambda year=year: self.set_year(year)} for year in years]
        self.year_menu = MDDropdownMenu(caller=self.ids.start_year_dropdown, items=menu_items, width_mult=3)

    def set_day(self, day):
        """
        Sets the day value using the selected value from the dropdown.
        
        Args:
            day: A string representing the selected day.
        """
        # Update the text on the label (if used)
        self.ids.day_label.text = str(day)
        self.day_menu.dismiss()

    def set_month(self, month):
        """
        Sets the month value using the selected month.
        
        Args:
            month: A string representing the selected month.
        """
        self.ids.month_label.text = month
        self.month_menu.dismiss()
        
    def set_year(self, year):
        """
        Sets the year value using the selected year.
        
        Args:
            year: A string representing the selected year.
        """
        self.ids.year_label.text = str(year)
        self.year_menu.dismiss()

    def open_day_menu(self, button):
        """
        Opens the day dropdown menu.
        
        Args:
            button: The UI element triggering the dropdown.
        """
        self.day_menu.caller = button
        self.day_menu.open()

    def open_month_menu(self, button):
        """
        Opens the month dropdown menu.
        
        Args:
            button: The UI element triggering the dropdown.
        """
        self.month_menu.caller = button
        self.month_menu.open()

    def open_year_menu(self, button):
        """
        Opens the year dropdown menu.
        
        Args:
            button: The UI element triggering the dropdown.
        """
        self.year_menu.caller = button
        self.year_menu.open()

    def get_selected_date(self):
        """
        Constructs a date string based on the selected day, month, and year.
        Converts a full month name to its numerical value if needed.
        
        Returns:
            A string representing the date in "MM/DD/YYYY" format.
        """
        day = self.ids.day_label.text
        month_text = self.ids.month_label.text
        year = self.ids.year_label.text
        try:
            month = int(month_text)
        except ValueError:
            dt = datetime.strptime(month_text, "%B")
            month = dt.month
        return f"{month}/{day}/{year}"


    # ------ Time Menus ------
    def create_time_menus(self):
        """
        Creates dropdown menus for selecting time:
          - Hours (1-12)
          - Minutes (in 5-minute increments)
          - AM/PM selection.
        """
        hours = [str(i) for i in range(1, 13)]
        hour_items = [{"text": h, "on_release": lambda h=h: self.set_hour(h)} for h in hours]
        self.hour_menu = MDDropdownMenu(caller=self.ids.hour_dropdown, items=hour_items, width_mult=2)

        minutes = [f"{i:02}" for i in range(0, 60, 5)]
        minute_items = [{"text": m, "on_release": lambda m=m: self.set_minute(m)} for m in minutes]
        self.minute_menu = MDDropdownMenu(caller=self.ids.minute_dropdown, items=minute_items, width_mult=2)

        ampm_items = [{"text": "AM", "on_release": lambda: self.set_ampm("AM")},
                      {"text": "PM", "on_release": lambda: self.set_ampm("PM") }]
        self.ampm_menu = MDDropdownMenu(caller=self.ids.ampm_dropdown, items=ampm_items, width_mult=2)

    def open_hour_menu(self, button):
        """
        Opens the hour selection dropdown.
        
        Args:
            button: The UI element triggering the dropdown.
        """
        self.hour_menu.caller = button
        self.hour_menu.open()

    def open_minute_menu(self, button):
        """
        Opens the minute selection dropdown.
        
        Args:
            button: The UI element triggering the dropdown.
        """
        self.minute_menu.caller = button
        self.minute_menu.open()

    def open_ampm_menu(self, button):
        """
        Opens the AM/PM selection dropdown.
        
        Args:
            button: The UI element triggering the dropdown.
        """
        self.ampm_menu.caller = button
        self.ampm_menu.open()

    def set_hour(self, hour):
        """
        Sets the hour value and updates the UI.
        
        Args:
            hour: A string representing the selected hour.
        """
        self.ids.hour_label.text = str(hour)
        self.hour_menu.dismiss()

    def set_minute(self, minute):
        """
        Sets the minute value and updates the UI in two-digit format.
        
        Args:
            minute: A string representing the selected minute.
        """
        formatted = f"{int(minute):02d}"
        self.ids.minute_label.text = formatted
        self.minute_menu.dismiss()

    def set_ampm(self, period):
        """
        Sets the AM/PM value.
        
        Args:
            period: A string, either "AM" or "PM", representing the period.
        """
        self.ids.ampm_label.text = period
        self.ampm_menu.dismiss()


    # ------ Reminder Menus ------
    def create_reminder_menus(self):
        """
        Creates all dropdown menus related to reminder settings including:
          - Reminder prior (unit and numeric value)
          - Repeat every (unit)
          - Repeat reminders and intervals (numeric values)
        """
        self.reminder_prior_menu = MDDropdownMenu(
            caller=self.ids.reminder_prior_unit,  # Button for reminder unit (e.g., DAY(S), WEEK(S), HOUR(S))
            items=[
                {
                    "text": unit,
                    "height": dp(48),
                    "on_release": lambda x=unit: self.set_reminder_prior_unit(x),
                }
                for unit in ["DAY(S)", "WEEK(S)", "HOUR(S)"]
            ],
            width_mult=3,
            max_height=dp(200),
        )

        self.repeat_every_unit_menu = MDDropdownMenu(
            caller=self.ids.repeat_every_unit,  # Button for "repeat every" unit.
            items=[
                {
                    "text": repeat_unit,
                    "height": dp(48),
                    "on_release": lambda x=repeat_unit: self.set_repeat_every_unit(x),
                }
                for repeat_unit in ["DAY(S)", "WEEK(S)", "HOUR(S)"]
            ],
            width_mult=3,
            max_height=dp(200),
        )

        reminders_prior_items = [
            {"text": str(i), "on_release": lambda i=i: self.set_reminder_prior_num(str(i))}
            for i in range(1, 11)
        ]
        self.reminders_prior_dropdown = MDDropdownMenu(
            caller=self.ids.reminder_prior_num_dropdown,
            items=reminders_prior_items,
            width_mult=3,
        )

        repeat_items = [
            {"text": str(i), "on_release": lambda i=i: self.set_repeat_reminders(str(i))}
            for i in range(1, 11)
        ]
        self.repeat_dropdown = MDDropdownMenu(
            caller=self.ids.repeat_dropdown,
            items=repeat_items,
            width_mult=3,
        )

        repeat_intervals_items = [
            {"text": str(i), "on_release": lambda i=i: self.set_repeat_intervals(str(i))}
            for i in range(1, 13)
        ]
        self.repeat_intervals_menu = MDDropdownMenu(
            caller=self.ids.repeat2_dropdown,
            items=repeat_intervals_items,
            width_mult=3,
        )

    def open_reminder_prior_num_dropdown(self, *args):
        """
        Opens the dropdown menu for selecting the numeric value before a reminder.
        """
        self.reminders_prior_dropdown.caller = self.ids.reminder_prior_num_dropdown
        self.reminders_prior_dropdown.open()

    def open_repeat_dropdown(self, *args):
        """
        Opens the dropdown for selecting the number of repeat reminders.
        """
        self.repeat_dropdown.caller = self.ids.repeat_dropdown
        self.repeat_dropdown.open()

    def open_repeat2_dropdown(self, *args):
        """
        Opens the dropdown for selecting the repeat intervals.
        """
        self.repeat_intervals_menu.caller = self.ids.repeat2_dropdown
        self.repeat_intervals_menu.open()

    def open_reminder_unit_menu(self, *args):
        """
        Opens the dropdown for selecting the reminder unit.
        """
        self.reminder_prior_menu.open()

    def open_repeat_unit_menu(self):
        """
        Opens the dropdown for selecting the "repeat every" unit.
        """
        self.repeat_every_unit_menu.open()
    
    def open_repeat_until_menu(self, *args):
        """
        Opens the "repeat until" option using a date picker.
        """
        self.show_date_picker()

    def set_reminder_prior_num(self, num):
        """
        Sets the number before the reminder.
        
        Args:
            num: A string representing the selected number.
        """
        self.ids.reminder_prior_num_dropdown.children[0].text = num
        self.reminders_prior_dropdown.dismiss()

    def set_repeat_reminders(self, value):
        """
        Sets the number of repeat reminders.
        
        Args:
            value: A string representing the selected repeat reminder count.
        """
        self.ids.repeat_dropdown.children[0].text = value
        self.repeat_dropdown.dismiss()

    def set_repeat_intervals(self, value):
        """
        Sets the repeat interval value.
        
        Args:
            value: A string representing the selected repeat interval.
        """
        self.ids.repeat2_dropdown.children[0].text = value
        self.repeat_intervals_menu.dismiss()

    def set_reminder_prior_unit(self, unit):
        """
        Sets the reminder prior unit (e.g., DAY, WEEK, HOUR).
        
        Args:
            unit: A string representing the unit.
        """
        self.ids.reminder_prior_unit_label.text = unit
        self.reminder_prior_menu.dismiss()

    def set_repeat_every_unit(self, unit):
        """
        Sets the unit for repeating reminders.
        
        Args:
            unit: A string representing the unit.
        """
        self.ids.repeat_every_unit_label.text = unit
        self.repeat_every_unit_menu.dismiss()


    def reset_fields(self):
        """
        Resets all form fields to their default values, including text inputs,
        date and time labels, dosage dropdowns, reminder fields, and clears any applied borders.
        """
        self.ids.med_name_input.text = ""
        self.ids.medication_box.text = ""
        
        # Reset date selectors.
        self.ids.day_label.text = "Day"
        self.ids.month_label.text = "Month"
        self.ids.year_label.text = "Year"  
        
        # Reset time selectors.
        self.ids.hour_label.text = "HOUR"
        self.ids.minute_label.text = "MINUTE"
        self.ids.ampm_label.text = "AM/PM"
        
        # Reset dosage-related dropdowns.
        self.ids.dosage_dropdown.children[0].text = "1"
        self.ids.dosage_unit_dropdown.children[0].text = "HOUR"
        self.ids.dosage_occurrence_dropdown.children[0].text = "1"
        
        # Reset reminder fields.
        self.ids.reminder_prior_num_dropdown.children[0].text = "1"
        self.ids.reminder_prior_unit_label.text = "DAY"  
        self.ids.repeat_dropdown.children[0].text = "1"
        self.ids.repeat2_dropdown.children[0].text = "1"
        self.ids.repeat_every_unit_label.text = "DAY"
        
        # Reset selections for icons, colors, and supply buttons.
        self.selected_icon = None
        self.selected_icon_value = 0
        self.selected_color = None
        self.selected_color_value = 0
        self.selected_supply_button = None
        
        # Clear canvas instructions for icon buttons.
        if self.ids.medication_buttons:
            for btn in self.ids.medication_buttons.children:
                btn.canvas.after.clear()
        
        # Clear canvas instructions for color buttons.
        if self.ids.color_buttons:
            for btn in self.ids.color_buttons.children:
                btn.canvas.after.clear()
        
        # Clear canvas instructions for supply buttons.
        if hasattr(self.ids, 'supply_buttons'):
            for btn in self.ids.supply_buttons.children:
                btn.canvas.after.clear()
    
    def on_leave(self):
        """
        Called when leaving the screen.
        Resets all form fields to ensure a clean state on re-entry.
        """
        self.reset_fields()


    def edit_prescription(self):
        """
        Gathers all updated values from the form, processes the data,
        builds an updated data dictionary, and attempts to update the medication record in the database.
        
        It uses new selection values if available, otherwise falls back to the original values.
        On successful update, it navigates back to the prescription screen.
        If an error occurs, it displays a dialog with the error message.
        """
        new_icon = self.selected_icon_value if self.selected_icon_value != 0 else self.med_data.get("icon")
        new_color = self.selected_color_value if self.selected_color_value != 0 else self.med_data.get("color")
        new_supply = (
            self.selected_supply
            if self.selected_supply is not None
            else int(self.med_data.get("total_supply", 0))
        )

        # Collect the rest of the values from the widgets.
        med_name = self.ids.med_name_input.text.strip()
        max_dosage = int(self.ids.dosage_dropdown.children[0].text)
        dosage_interval = int(self.ids.dosage_occurrence_dropdown.children[0].text)
        dosage_frequency = self.ids.dosage_unit_dropdown.children[0].text

        # Parse start date
        start_date_str = self.get_selected_date()  # Assuming this returns "MM/DD/YYYY"
        start_date = datetime.strptime(start_date_str, "%m/%d/%Y")

        # Process start time—if default values are still showing, use None.
        hour_text = self.ids.hour_label.text
        minute_text = self.ids.minute_label.text
        ampm_text = self.ids.ampm_label.text
        if hour_text == "HOUR" or minute_text == "MINUTE" or ampm_text == "AM/PM":
            start_time = None
        else:
            hour = int(hour_text)
            minute = int(minute_text)
            if ampm_text.upper() == "PM" and hour != 12:
                hour += 12
            elif ampm_text.upper() == "AM" and hour == 12:
                hour = 0
            # Determine month from the label (similar to get_selected_date)
            month = int(self.ids.month_label.text) if self.ids.month_label.text.isdigit() else datetime.strptime(self.ids.month_label.text, "%B").month
            start_time = datetime(
                year=int(self.ids.year_label.text),
                month=month,
                day=int(self.ids.day_label.text),
                hour=hour,
                minute=minute
            )
            
        duration_prior = int(self.ids.reminder_prior_num_dropdown.children[0].text)
        reminder_unit = self.ids.reminder_prior_unit_label.text
        repeat_reminders = int(self.ids.repeat_dropdown.children[0].text)
        repeat_intervals = int(self.ids.repeat2_dropdown.children[0].text)
        repeat_unit = self.ids.repeat_every_unit_label.text
        details = self.ids.medication_box.text.strip()

        # Build an updated data dictionary.
        updated_data = {
            "med_name": med_name,
            "icon": new_icon,
            "color": new_color,
            "max_dosage": max_dosage,
            "dosage_frequency": dosage_frequency,
            "dosage_interval": dosage_interval,
            "total_supply": new_supply,
            "start_date": start_date,
            "start_time": start_time,  # May be None.
            "duration_prior": duration_prior,
            "reminder_unit": reminder_unit,
            "repeat_reminders": repeat_reminders,
            "repeat_intervals": repeat_intervals,
            "repeat_unit": repeat_unit,
            "details": details,
        }

        # Retrieve the current user's ID.
        user_id = App.get_running_app().user_id

        try:
            # Call update method in db_manager
            db_manager.update_medication(user_id, self.med_id, **updated_data)
            # Navigate back to the prescription screen on success.
            if self.manager:
                self.manager.current = "prescription" # Return to the prescription info screen
        except Exception as e:
            self.dialog = MDDialog(
                title="Error updating medication.",
                text=str(e),
                buttons=[MDButton(text="OK", on_release=lambda x: self.dialog.dismiss())],
            )
            self.dialog.open()