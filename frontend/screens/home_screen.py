#   This file implements the home screen of the application.
#   It defines a MedicationCard widget which visually represents a medication prescription,
#   and a HomeScreen class which manages the display of these prescriptions.
#   The HomeScreen class retrieves user medications from the database, creates MedicationCard
#   instances (using ICON_MAP and COLOR_MAP to map stored values to icons and colors), 
#   and handles user interactions such as selecting a medication card.

from datetime import datetime
from kivy.uix.screenmanager import Screen
from kivy.app import App
from kivy.metrics import dp
from kivymd.uix.card import MDCard
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivymd.uix.card import MDCard
from kivy.properties import ListProperty

from backend.database.db_instance import db_manager  

# Map integer icon choice to icon names
ICON_MAP = {
    1: "pill",
    2: "minus-circle",
    3: "bottle-tonic",
    4: "medication",
    5: "bottle-tonic-plus-outline",
    6: "needle"
}

# Map integer color choices to RGBA values
COLOR_MAP = {
    1: (1, 0, 0, 1),          # RED
    2: (0, 0.5, 0.5, 1),      # TEAL
    3: (0, 0, 1, 1),          # DARK BLUE
    4: (1, 1, 0, 1),          # YELLOW
    5: (1, 0.5, 0, 1),        # ORANGE
    6: (1, 0.08, 0.58, 1),    # PINK
    7: (0.73, 0.33, 0.83, 1), # PURPLE
    8: (0.13, 0.55, 0.13, 1), # FOREST GREEN
    9: (0.53, 0.81, 0.98, 1), # LIGHT BLUE
}

class MedicationCard(MDCard):
    # Properties that define medication information and display settings.
    med_id = NumericProperty(0)
    med_name = StringProperty("")
    total_supply = NumericProperty(0)
    first_reminder_date = StringProperty("")
    icon_color = ListProperty([0, 0, 0, 1])
    icon_name = StringProperty("")
    refill_status = BooleanProperty(False)

    def toggle_refill_status(self):
        """
        Toggle the refill status of the medication.
        Updates the refill_status property and changes the appearance of the refill button accordingly.
        """
        self.refill_status = not self.refill_status
        btn = self.ids.refill_button
        if self.refill_status:
            btn.text = "Refilled"
            btn.background_color = 0.2, 0.6, 1, 1  # Lighter blue for "refilled"
        else:
            btn.text = "Refill"
            btn.background_color = (242, 244, 246, 1)


class HomeScreen(Screen):
    def on_enter(self):
        """
        Called when the HomeScreen is entered.
        Clears any existing widgets from the prescription list, retrieves the current user's medications
        from the database, and creates a MedicationCard for each medication.
        """
        self.ids.prescription_list.clear_widgets()
        user_id = App.get_running_app().user_id
        medications = db_manager.get_user_medications(user_id)

        for med in medications:
            med_name = med.get('med_name', '')
            total_supply = med.get('total_supply', 0)
            reminder_dates = med.get('reminder_dates', '')

            # Process reminder_dates to extract the first reminder date as a string.
            if isinstance(reminder_dates, list) and len(reminder_dates) > 0:
                try:
                    # Convert the first reminder date from ISO format to "MM/DD/YYYY"
                    dt = datetime.fromisoformat(reminder_dates[0])
                    first_reminder_date = dt.strftime("%m/%d/%Y")
                except Exception as e:
                    # If conversion fails, fallback to the raw first element as a string.
                    first_reminder_date = str(reminder_dates[0])
            elif isinstance(reminder_dates, str):
                first_reminder_date = reminder_dates
            else:
                first_reminder_date = ""

            # Retrieve and map the icon value.
            try:
                icon_choice = int(med.get('icon', 1))
            except Exception:
                icon_choice = 1
            icon_name = ICON_MAP.get(icon_choice, "pill")
            # Retrieve and map the color value.
            try:
                color_choice = int(med.get('color', 1))
            except Exception:
                color_choice = 1
            icon_color = COLOR_MAP.get(color_choice, (0, 0, 0, 1))
            
            # Create a MedicationCard with all the necessary properties set.
            card = MedicationCard(
                med_id=med.get('id', 0),
                med_name=med_name,
                total_supply=total_supply,
                first_reminder_date=first_reminder_date,
                icon_color=icon_color,
                icon_name=icon_name,
                size_hint=(1, None),
                height=dp(120),
                padding=dp(8),
                radius=[dp(12)]
            )
            # Bind the on_release event of the card to trigger navigation.
            card.bind(on_release=self.on_card_release)
            self.ids.prescription_list.add_widget(card)

    def on_card_release(self, instance):
        """
        Event handler called when a MedicationCard is clicked.
        Navigates to the prescription screen, passing the medication ID so that details can be loaded.
        
        Args:
            instance: The MedicationCard instance that was clicked.
        """
        app = App.get_running_app()
        # Get the target screen from ScreenManager.
        target_screen = app.root.get_screen("prescription")
        # Pass the medication id to the prescription screen.
        target_screen.med_id = instance.med_id
        # Switch to the prescription screen.
        app.root.current = "prescription"

    # Logout to be utilized in the future in settings menu
    #def logout(self):
        """
        Logs the user out by navigating to the login screen.
        """
    #    self.manager.current = "login"



