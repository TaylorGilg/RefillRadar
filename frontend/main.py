# This file is in charge of loading the front end files and 
# launching the app's interactive visuals

import sys  
import os   

# Modify sys.path so that the parent directory (the root of the project)
# is in the Python path. This ensures that module imports work consistently,
# regardless of where the script is run from.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kivy.lang import Builder         
from kivy.core.window import Window     

from kivy.uix.boxlayout import BoxLayout  
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition  

from kivy.metrics import dp             
from kivymd.app import MDApp            
from kivymd.uix.label import MDLabel      
from kivymd.uix.snackbar import MDSnackbar  

from backend.database.db_instance import db_manager  

# Importing frontend screen classes for different parts of the application.
from frontend.screens.login_screens import LoginScreen, CreateAccountScreen
from frontend.screens.home_screen import HomeScreen
from frontend.screens.prescription_screen import MedicationInformationScreen
from frontend.screens.add_prescription_screen import AddPrescriptionScreen
from frontend.screens.edit_prescription_screen import EditPrescriptionScreen
from frontend.screens.calendar_screen import CalendarScreen
from frontend.screens.settings_screen import SettingsScreen

# Set the application window size and clear color.
# This is for testing on a fixed resolution and setting a default background color.
Window.size = (360, 640)
Window.clearcolor = (1, 1, 1, 1)  # White background.
Window.title= "Refill Radar"

# Load the .kv layout files for the different screens.
# This loads the user interface definitions from separate files.
Builder.load_file("frontend/kv/prescription_screen.kv")
Builder.load_file("frontend/kv/add_prescription_screen.kv")
Builder.load_file("frontend/kv/login_screens.kv")
Builder.load_file("frontend/kv/home_screen.kv")
Builder.load_file("frontend/kv/edit_prescription_screen.kv")
Builder.load_file("frontend/kv/calendar_screen.kv")
Builder.load_file("frontend/kv/settings_screen.kv")

# This is the main application class that sets up and runs the KivyMD app.
# It creates a ScreenManager, adds all the screens to it, and binds additional
# methods for UI interactivity (such as tooltips and character count updates).
class PrescriptionApp(MDApp):
    def build(self):
        """
        Build method:
            Initializes the ScreenManager with a fade transition between screens,
            instantiates each screen, binds screen change events to clear tooltips,
            and assigns helper methods for dynamic UI behavior from within the .kv file.
        
        Returns:
            The root widget (ScreenManager) of the application.
        """
        # Create a ScreenManager with a short fade transition for screen changes.
        sm = ScreenManager(transition=FadeTransition(duration=0.2))

        # Instantiate each screen with a unique name.
        # These names are used for screen navigation.
        login_screen = LoginScreen(name="login")
        create_account_screen = CreateAccountScreen(name="create_account")
        home_screen = HomeScreen(name="home")
        add_prescription_screen = AddPrescriptionScreen(name="add_prescription")
        prescription_screen = MedicationInformationScreen(name="prescription")
        edit_prescription_screen = EditPrescriptionScreen(name="edit_prescription")
        calendar_screen = CalendarScreen(name="calendar")
        settings_screen = SettingsScreen(name="settings")

        # Add all the screens to the ScreenManager.
        sm.add_widget(login_screen)
        sm.add_widget(create_account_screen)
        sm.add_widget(home_screen)
        sm.add_widget(add_prescription_screen)
        sm.add_widget(prescription_screen)
        sm.add_widget(edit_prescription_screen)
        sm.add_widget(calendar_screen)
        sm.add_widget(settings_screen)

        # Bind a lambda function to the ScreenManager's current property.
        # This ensures that any displayed tooltip (used in add_prescription_screen 
        # and edit_prescription_screen) is cleared when the user switches screens.
        sm.bind(current=lambda instance, value: self.clear_tooltip())

        # Set the initial screen to the login screen.
        sm.current = "login"

        #-------Add Prescription Widget Functionality Accessability------
        # Make certain methods accessible from the add_prescription_screen.kv file using the "app" variable.
        # These methods help with UI interactions, such as opening dropdown menus.
        self.select_color = add_prescription_screen.select_color
        self.select_medication = add_prescription_screen.select_medication
        self.open_day_menu = add_prescription_screen.open_day_menu
        self.open_month_menu = add_prescription_screen.open_month_menu
        self.open_year_menu = add_prescription_screen.open_year_menu
        self.open_dosage_unit_menu = add_prescription_screen.open_dosage_unit_dropdown

        # New dropdown openers so that the .kv file won't break.
        self.open_reminder_unit_menu = add_prescription_screen.open_reminder_unit_menu
        self.open_repeat_unit_menu = add_prescription_screen.open_repeat_unit_menu
        self.open_repeat_until_menu = add_prescription_screen.open_repeat_until_menu

        # Time dropdowns for selecting hour, minute, and AM/PM.
        self.open_hour_menu = add_prescription_screen.open_hour_menu
        self.open_minute_menu = add_prescription_screen.open_minute_menu
        self.open_ampm_menu = add_prescription_screen.open_ampm_menu

        return sm

    def go_back(self):
        """
            Sets the current screen to the home screen.
            This can be used when a user wants to navigate back from 
            the add_prescription_screen and prescription_screen.
        """
        self.root.current = "home"

    def update_char_count(self, text, screen_name=None):
        """
            Updates the character count label for a text input field.
            If the text exceeds a specified maximum character limit (200),
            it trims the text and updates the label with the current count.
            It is used in add_prescription and edit_prescription.

        Arguments:
            text (str): The text to count characters from.
            screen_name (str, optional): Name of the screen to update.
            If not provided, the current screen is used.
        """
        # Determine which screen's character count label to update.
        if screen_name is None:
            screen = self.root.get_screen(self.root.current)
        else:
            screen = self.root.get_screen(screen_name)
        
        # Calculate the number of characters and enforce a maximum limit.
        char_count = len(text)
        max_chars = 200

        if char_count > max_chars:
            trimmed_text = text[:max_chars]
            screen.ids.medication_box.text = trimmed_text
            char_count = max_chars

        # Update the character count label with a custom message.
        screen.ids.char_count_label.text = f"Character Count : {char_count}/200"
        screen.ids.char_count_label.theme_text_color = "Custom"
        # Change text color to red if near the limit, else use a default grey tone.
        screen.ids.char_count_label.text_color = (
            (1, 0, 0, 1) if char_count >= 190 else (0.5, 0.5, 0.5, 1)
        )

    def show_tooltip(self, title, description):
        """
            Displays a tooltip (using an MDSnackbar) with a title and description.
            The tooltip is styled as a label and wrapped inside a BoxLayout for dynamic sizing.
            It is used in add_prescription and edit_prescription.
        
        Arguments:
            title (str): The title text for the tooltip (will be displayed in bold).
            description (str): Additional details or instructions for the tooltip.
        """
        # Combine title and description with markup for styling.
        full_text = f"[b]{title}[/b]: {description}"

        # Create a label with wrapped text. The size is dynamically adjusted based on the text.
        label = MDLabel(
            text=full_text,
            markup=True,
            halign="left",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            font_size="16sp",
            size_hint_y=None,
            text_size=(dp(240), None),  # Wrap text within a specific width.
        )
        label.bind(
            texture_size=lambda *x: setattr(label, "height", label.texture_size[1])
        )

        # Create a container layout that adapts its height to fit the label content.
        content = BoxLayout(
            orientation="vertical",
            padding=[12, 0, 12, 24],
            size_hint_y=None
        )
        content.bind(
            minimum_height=lambda layout, h: setattr(content, "height", h)
        )
        content.add_widget(label)

        # Create and configure the snackbar that will display the tooltip.
        snackbar = MDSnackbar(
            content,
            size_hint_x=None,
            width=dp(340),  # Customize the width as necessary.
            pos_hint={"center_x": 0.5, "bottom": 0.9},
        )
        snackbar.open()

        # Save a reference to the current snackbar so it can be cleared later.
        self._current_snackbar = snackbar

    def clear_tooltip(self):
        """
            Dismisses the currently displayed tooltip (if any).
            This is called when the user navigates to a different screen.
        """
        if hasattr(self, "_current_snackbar") and self._current_snackbar:
            self._current_snackbar.dismiss()
            self._current_snackbar = None


if __name__ == "__main__":
    PrescriptionApp().run()