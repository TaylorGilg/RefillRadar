
#   This file implements the app's Add Prescription Screen.
#   It provides a user interface for adding a new medication prescription, including:
#   - selecting an icon and color to help customize and identify a prescription and 
#   - indicating dosage, supply, start date/start time and background medicine information 
#   - specifying reminder notification preferences 
#   The screen gathers input values from various dropdowns and buttons,
#   extracts those inputs, and on submission, stores the prescription data using the database manager.

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
from kivy.properties import NumericProperty

from backend.database.db_instance import db_manager

# Load the associated Kivy layout file for this screen.
Builder.load_file("frontend/kv/add_prescription_screen.kv")

class AddPrescriptionScreen(MDScreen):
    # Define properties to store the selected icon and color values.
    selected_icon_value = NumericProperty(0)
    selected_color_value = NumericProperty(0)


    def __init__(self, **kwargs):
        """
        Constructor for AddPrescriptionScreen.
        Initializes default states for selected icon, color, 
        and the selected supply button.
        """
        super().__init__(**kwargs)
        self.selected_icon = None
        self.selected_color = [0, 0, 1, 1]
        self.selected_supply_button = None


    def on_kv_post(self, base_widget):
        """
        Callback after the kv language rules are applied.
        Sets up the initial menus for day, month, year, reminder, and time selections.
        A dosage menu creation is scheduled with a short delay 
        (to allow all other elements to load in)
        """
        self.create_day_menu()
        self.create_month_menu()
        self.create_year_menu()
        self.create_reminder_menus()
        self.create_time_menus()

        # Use Clock to schedule the dosage menu creation after the kv rules are applied
        Clock.schedule_once(self._create_dosage_menus_later, 0)


    def on_pre_enter(self):
        """
        Called right before the screen is shown.
        Sets default values for dosage selections and updates the dosage summary.
        This prevents the fields from being empty when the user first enters the screen.
        """
        self.ids.dosage_dropdown.children[0].text = "1"
        self.ids.dosage_unit_dropdown.children[0].text = "HOUR"
        self.ids.dosage_occurrence_dropdown.children[0].text = "1"


    # ------Medication Icon & Color Selectors------
    def select_medication(self, icon_button):
        """
        Called when a medication icon button is selected.
        Clears any previous selection borders, assigns the new icon, and draws a border around it.
        
        Args:
            icon_button: The button widget that represents a medication icon.
        """
        # Clear borders for all medication icon buttons.
        for btn in self.ids.medication_buttons.children:
            btn.canvas.after.clear()
        self.selected_icon = icon_button

        # Save the selected icon value from its custom property.
        self.selected_icon_value = getattr(icon_button, 'icon_value', 0)

        def draw_border(dt):
            # Compute the radius from the button's dimensions
            radius = min(icon_button.width, icon_button.height) / 2 
            with icon_button.canvas.after:
                Color(0.2, 0.4, 1, 1) # BLUE (color for border)
                Line(circle=(icon_button.center_x, icon_button.center_y, radius), width=2)

        # Schedule drawing the border after the current frame.
        Clock.schedule_once(draw_border, 0)


    def select_color(self, color_button):
        """
        Called when a color button is selected.
        Clears the previous color selection border, assigns the new color,
        and draws a border around the selected color button.
        
        Args:
            color_button: The button widget that represents a color option.
        """
        # Remove border from the previously selected color if available.
        if self.selected_color and hasattr(self.selected_color, "canvas"):
            self.selected_color.canvas.after.clear()

        self.selected_color = color_button

        # Save the selected color value from its custom property.
        self.selected_color_value = getattr(color_button, 'color_value', 0)

        def draw_border(dt):
            # Calculate a circular border based on the button size.
            radius = min(color_button.width, color_button.height) / 2 
            with color_button.canvas.after:
                Color(0.2, 0.4, 1, 1) # BLUE (color for border)
                Line(circle=(color_button.center_x, color_button.center_y, radius), width=2)

        Clock.schedule_once(draw_border, 0)

    # ------Dosage Menus------
    def _create_dosage_menus_later(self, dt):
        """
        Delayed creation of dosage-related dropdown menus.
        This method is scheduled after the view is rendered to ensure proper layout.
        """
        self.create_dosage_menus()

    def create_dosage_menus(self):
        """
        Builds the dropdown menus used for dosage selection.
        
        Creates three menus:
          - max_dosage_menu: Lets the user choose the maximum dosage (1 to 10).
          - dosage_occurrence_menu: Sets how frequently the dosage is taken (1 to 24).
          - dosage_unit_menu: Chooses the unit for the dosage frequency (hours, days, or weeks).
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

        occurrence_values = [str(i) for i in range(1, 25)]  # accounts for up to 24 hours
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
            button: The button widget that triggers the dropdown.
        """
        self.max_dosage_menu.caller = button
        self.max_dosage_menu.open()

    def open_dosage_occurrence_dropdown(self, button):
        """
        Opens the dosage occurrence (frequency) dropdown menu.
        
        Args:
            button: The button widget that triggers the dropdown.
        """
        self.dosage_occurrence_menu.caller = button
        self.dosage_occurrence_menu.open()

    def open_dosage_unit_dropdown(self, button):
        """
        Opens the dosage unit dropdown menu.
        
        Args:
            button: The button widget that triggers the dropdown.
        """
        self.dosage_unit_menu.caller = button
        self.dosage_unit_menu.open()

    def set_dosage(self, value):
        """
        Sets the maximum dosage to the provided value,
        updates the UI text, dismisses the dropdown, and updates the dosage summary.
        
        Args:
            value: A string representing the selected dosage.
        """
        self.ids.dosage_dropdown.children[0].text = value
        self.max_dosage_menu.dismiss()

    def set_dosage_occurrence(self, value):
        """
        Sets the frequency at which dosage is taken,
        updating the associated label and dismissing the dropdown.
        
        Args:
            value: A string representing the dosage occurrence.
        """
        self.ids.dosage_occurrence_label.text = value
        self.dosage_occurrence_menu.dismiss()

    def set_dosage_unit(self, value):
        """
        Sets the dosage frequency unit (e.g., HOUR(S), DAY(S), WEEK(S)) to the provided value,
        updates the UI, dismisses the dropdown, and updates the dosage summary.
        
        Args:
            value: A string representing the selected dosage unit.
        """
        self.ids.dosage_unit_dropdown.children[0].text = value
        self.dosage_unit_menu.dismiss()


    # ------Supply Menus------
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
        Creates a dropdown menu for selecting the day (1-31).
        """
        days = [str(i) for i in range(1, 32)]
        menu_items = [{"text": day, "on_release": lambda day=day: self.set_day(day)} for day in days]
        self.day_menu = MDDropdownMenu(caller=self.ids.start_day_dropdown, items=menu_items, width_mult=3)

    def create_month_menu(self):
        """
        Creates a dropdown menu for selecting the month by name.
        """
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        menu_items = [{"text": month, "on_release": lambda month=month: self.set_month(month)} for month in months]
        self.month_menu = MDDropdownMenu(caller=self.ids.start_month_dropdown, items=menu_items, width_mult=3)

    def create_year_menu(self):
        """
        Creates a dropdown menu for selecting the year (2025-2039).
        """
        years = [str(i) for i in range(2025, 2040)]
        menu_items = [{"text": year, "on_release": lambda year=year: self.set_year(year)} for year in years]
        self.year_menu = MDDropdownMenu(caller=self.ids.start_year_dropdown, items=menu_items, width_mult=3)

    def set_day(self, day):
        """
        Sets the day label to the selected day and dismisses the day menu.
        
        Args:
            day: A string representing the selected day.
        """
        self.ids.start_day_label.text = str(day)
        self.day_menu.dismiss()

    def set_month(self, month):
        """
        Sets the month label to the selected month and dismisses the month menu.
        
        Args:
            month: A string representing the selected month.
        """
        self.ids.start_month_label.text = month
        self.month_menu.dismiss()

    def set_year(self, year):
        """
        Sets the year label to the selected year and dismisses the year menu.
        
        Args:
            year: A string representing the selected year.
        """
        self.ids.start_year_label.text = str(year)
        self.year_menu.dismiss()

    def open_day_menu(self, button):
        """
        Opens the day selection dropdown.
        
        Args:
            button: The button that triggers the day menu.
        """
        self.day_menu.caller = button
        self.day_menu.open()

    def open_month_menu(self, button):
        """
        Opens the month selection dropdown.
        
        Args:
            button: The button that triggers the month menu.
        """
        self.month_menu.caller = button
        self.month_menu.open()

    def open_year_menu(self, button):
        """
        Opens the year selection dropdown.
        
        Args:
            button: The button that triggers the year menu.
        """
        self.year_menu.caller = button
        self.year_menu.open()

    
    # ------ Time Menus ------
    def create_time_menus(self):
        """
        Creates dropdown menus for selecting time:
          - Hour menu: Options 1-12.
          - Minute menu: Options in 5-minute increments.
          - AM/PM menu: AM or PM selection.
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
            button: The button that triggers the hour menu.
        """
        self.hour_menu.caller = button
        self.hour_menu.open()

    def open_minute_menu(self, button):
        """
        Opens the minute selection dropdown.
        
        Args:
            button: The button that triggers the minute menu.
        """
        self.minute_menu.caller = button
        self.minute_menu.open()

    def open_ampm_menu(self, button):
        """
        Opens the AM/PM selection dropdown.
        
        Args:
            button: The button that triggers the AM/PM menu.
        """
        self.ampm_menu.caller = button
        self.ampm_menu.open()

    def set_hour(self, hour):
        """
        Sets the hour label to the selected hour and dismisses the hour menu.
        
        Args:
            hour: A string representing the selected hour.
        """
        self.ids.hour_label.text = hour
        self.hour_menu.dismiss()

    def set_minute(self, minute):
        """
        Sets the minute label to the selected minute and dismisses the minute menu.
        
        Args:
            minute: A string representing the selected minute.
        """
        self.ids.minute_label.text = minute
        self.minute_menu.dismiss()

    def set_ampm(self, period):
        """
        Sets the AM/PM label based on selection and dismisses the AM/PM menu.
        
        Args:
            period: A string "AM" or "PM" indicating the period.
        """
        self.ids.ampm_label.text = period
        self.ampm_menu.dismiss()


    # ------ Reminder Menus -------
    def create_reminder_menus(self):
        """
        Creates dropdown menus related to reminders:
          - Reminder prior: The time before the event for the reminder.
          - Repeat every: The frequency unit for reminder repetition.
          - Numeric selections for reminder prior, repeat reminders, and repeat intervals.
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

        # Menu for selecting the number for reminder prior (1-10).
        reminders_prior_items = [
            {"text": str(i), "on_release": lambda i=i: self.set_reminder_prior_num(str(i))}
            for i in range(1, 11)
        ]
        self.reminders_prior_dropdown = MDDropdownMenu(
            caller=self.ids.reminder_prior_num_dropdown,  # Button that shows the selected number.
            items=reminders_prior_items,
            width_mult=3,
        )

        # Create the menu for repeat reminders numeric selection (e.g., 1 through 10)
        repeat_items = [
            {"text": str(i), "on_release": lambda i=i: self.set_repeat_reminders(str(i))}
            for i in range(1, 5)
        ]
        self.repeat_dropdown = MDDropdownMenu(
            caller=self.ids.repeat_dropdown,  # button that shows the selected repeat reminders value
            items=repeat_items,
            width_mult=3,
        )

        # Create the menu for repeat intervals numeric selection (e.g., 1 through 12)
        repeat_intervals_items = [
            {"text": str(i), "on_release": lambda i=i: self.set_repeat_intervals(str(i))}
            for i in range(1, 13)
        ]
        self.repeat_intervals_menu = MDDropdownMenu(
            caller=self.ids.repeat2_dropdown,  # Button that shows the selected repeat interval.
            items=repeat_intervals_items,
            width_mult=3,
        )

    def open_reminder_prior_num_dropdown(self, *args):
        """
        Opens the numeric dropdown for selecting the reminder prior number.
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
        Opens the dropdown for selecting repeat intervals.
        """
        self.repeat_intervals_menu.caller = self.ids.repeat2_dropdown
        self.repeat_intervals_menu.open()

    def open_reminder_unit_menu(self, *args):
        """
        Opens the dropdown menu for reminder prior unit.
        """
        self.reminder_prior_menu.open()

    def open_repeat_unit_menu(self):
        """
        Opens the dropdown menu for the "repeat every" unit.
        """
        self.repeat_every_unit_menu.open()
    
    def open_repeat_until_menu(self, *args):
        """
        Opens the "repeat until" option using a date picker.
        This method calls the date picker instead of a dropdown menu.
        """
        self.show_date_picker()

    # Setter functions for reminder related dropdowns.
    def set_reminder_prior_num(self, num):
        """
        Sets the reminder prior number to the provided value.
        
        Args:
            num: A string representing the numeric value before the event for the reminder.
        """
        self.ids.reminder_prior_num_dropdown.children[0].text = num
        self.reminders_prior_dropdown.dismiss()

    def set_repeat_reminders(self, value):
        """
        Sets the number of repeat reminders.
        
        Args:
            value: A string representing the selected number of repeats.
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
            unit: A string representing the reminder unit.
        """
        self.ids.reminder_prior_unit_label.text = unit
        self.reminder_prior_menu.dismiss()

    def set_repeat_every_unit(self, unit):
        """
        Sets the unit for the repeat every frequency (e.g., DAY, WEEK, HOUR).
        
        Args:
            unit: A string representing the repeat unit.
        """
        self.ids.repeat_every_unit_label.text = unit
        self.repeat_every_unit_menu.dismiss()

    def _create_reminder_menus_later(self, dt):
        """
        Delayed creation of reminder menus.
        Scheduled using Clock to allow the interface to set up properly.
        """
        self.create_reminder_menus()


    def get_selected_date(self):
        """
        Determines and returns the selected date.
        Checks if a text field exists for the date; if not, constructs the date from the day,
        month, and year labels. Converts a full month name to a month number if needed.
        
        Returns:
            A string representing the date in "MM/DD/YYYY" format.
        """
        if hasattr(self.ids, "start_date_field"):
            return self.ids.start_date_field.text
        else:
            day = self.ids.start_day_label.text
            month_text = self.ids.start_month_label.text
            year = self.ids.start_year_label.text
            try:
                # If month is already a number.
                month = int(month_text)
            except ValueError:
                # Convert month name (e.g., "April") to month number.
                dt = datetime.strptime(month_text, "%B")
                month = dt.month
            return f"{month}/{day}/{year}"


    def reset_fields(self):
        """
        Resets the form fields back to default values.
        Clears text inputs, resets dropdown texts and date/time selectors,
        and clears any drawn borders on icon, color, or supply buttons.
        """
        # Clear text fields
        self.ids.med_name_input.text = ""
        self.ids.medication_box.text = ""
        
        # Reset date selectors
        self.ids.start_day_label.text = "Day"
        self.ids.start_month_label.text = "Month"
        self.ids.start_year_label.text = "Year"  
        
        # Reset time selectors
        self.ids.hour_label.text = "HOUR"
        self.ids.minute_label.text = "MINUTE"
        self.ids.ampm_label.text = "AM/PM"
        
        # Reset dosage dropdowns and related labels to defaults
        self.ids.dosage_dropdown.children[0].text = "1"
        self.ids.dosage_unit_dropdown.children[0].text = "HOUR"
        self.ids.dosage_occurrence_dropdown.children[0].text = "1"
        
        # Reset reminder fields
        self.ids.reminder_prior_num_dropdown.children[0].text = "1"
        self.ids.reminder_prior_unit_label.text = "DAY"  
        self.ids.repeat_dropdown.children[0].text = "1"
        self.ids.repeat2_dropdown.children[0].text = "1"
        self.ids.repeat_every_unit_label.text = "DAY"
        
        # Reset any selected icons, colors, or supply buttons
        self.selected_icon = None
        self.selected_icon_value = 0
        self.selected_color = None
        self.selected_color_value = 0
        self.selected_supply_button = None
        
        # Clear canvas instructions for icon buttons
        if self.ids.medication_buttons:
            for btn in self.ids.medication_buttons.children:
                btn.canvas.after.clear()
        
        # Clear canvas instructions for color buttons
        if self.ids.color_buttons:
            for btn in self.ids.color_buttons.children:
                btn.canvas.after.clear()
        
        # Clear canvas instructions for supply buttons
        if hasattr(self.ids, 'supply_buttons'):
            for btn in self.ids.supply_buttons.children:
                btn.canvas.after.clear()
    
    # Override on_leave to clear the form when leaving the screen.
    def on_leave(self):
        """
        Called when the user navigates away from this screen.
        Clears the form by calling reset_fields to ensure a fresh start on re-entry.
        """
        self.reset_fields()


    def add_prescription(self):
        """
        Gathers all input values from the form, processes the data (including
        date and time conversions), builds a medication data dictionary, and
        attempts to add the medication using the db_manager.
        
        If the prescription is added successfully, the screen navigates back to home.
        If there is an error, an MDDialog is displayed showing the error.
        """
        # Retrieve basic values
        icon = self.selected_icon_value
        color = self.selected_color_value
        med_name = self.ids.med_name_input.text.strip()
        max_dosage = int(self.ids.dosage_dropdown.children[0].text)
        dosage_frequency = self.ids.dosage_unit_dropdown.children[0].text
        total_supply = self.selected_supply

        # Parse the start date
        start_date_str = self.get_selected_date()  # Format expected: "MM/DD/YYYY"
        start_date = datetime.strptime(start_date_str, "%m/%d/%Y")

        # Check if time selection is complete or still using the default placeholders.
        hour_text = self.ids.hour_label.text
        minute_text = self.ids.minute_label.text
        ampm_text = self.ids.ampm_label.text
        if hour_text == "HOUR" or minute_text == "MINUTE" or ampm_text == "AM/PM":
            start_time = None
        else:
            # Convert and adjust time if valid input exists.
            hour = int(hour_text)
            minute = int(minute_text)
            if ampm_text.upper() == "PM" and hour != 12:
                hour += 12
            elif ampm_text.upper() == "AM" and hour == 12:
                hour = 0

            # Determine month value from the month label (handling full month names if needed)
            try:
                month = int(self.ids.start_month_label.text)
            except ValueError:
                month = datetime.strptime(self.ids.start_month_label.text, "%B").month

            # Construct the start_time
            start_time = datetime(
                year=int(self.ids.start_year_label.text),
                month=month,
                day=int(self.ids.start_day_label.text),
                hour=hour,
                minute=minute
            )

        # Convert reminder settings to integers
        duration_prior = int(self.ids.reminder_prior_num_dropdown.children[0].text)
        reminder_unit = self.ids.reminder_prior_unit_label.text
        repeat_reminders = int(self.ids.repeat_dropdown.children[0].text)
        repeat_intervals = int(self.ids.repeat2_dropdown.children[0].text)
        repeat_unit = self.ids.repeat_every_unit_label.text

        details = self.ids.medication_box.text.strip()

        dosage_interval = int(self.ids.dosage_occurrence_dropdown.children[0].text)

        # Build the medication data dictionary
        med_data = {
            "med_name": med_name,
            "icon": icon,
            "color": color,
            "max_dosage": max_dosage,
            "dosage_frequency": dosage_frequency,
            "dosage_interval": dosage_interval,
            "total_supply": total_supply,
            "start_date": start_date,
            "start_time": start_time,  # May be None if not provided by the user.
            "duration_prior": duration_prior,
            "reminder_unit": reminder_unit,
            "repeat_reminders": repeat_reminders,
            "repeat_intervals": repeat_intervals,
            "repeat_unit": repeat_unit,
            "details": details,
        }

        # Retrieve the current user's id (from the running app instance)
        user_id = App.get_running_app().user_id

        try:
            # Add the medication using the db_manager.
            db_manager.add_medication(user_id, **med_data)
            # Navigate back to the home screen on success
            if self.manager:
                self.manager.current = "home"
        except Exception as e:
            # If an error occurs, display a dialog with the error message.
            self.dialog = MDDialog(
                title="Error adding medication.",
                text=str(e),
                buttons=[MDButton(text="OK", on_release=lambda x: self.dialog.dismiss())],
            )
            self.dialog.open()