#   This file defines two Kivy screen classes: LoginScreen and CreateAccountScreen.
#   These classes handle user interactions for logging in and creating a new
#   account, respectively. Each screen clears its input fields on entry and
#   validates the user's input before performing authentication or registration.

from kivy.uix.screenmanager import Screen
from kivy.app import App

from backend.database.db_instance import db_manager

#   Manages the user login screen. It handles the preparation of the screen
#   upon entry and attempts to authenticate the user based on provided credentials.
class LoginScreen(Screen):

    def on_pre_enter(self):
        """
        Called automatically by the Kivy framework before the screen is shown.
        This method clears any previously entered text in the username and password
        fields as well as any error messages, ensuring a clean slate on every entry.
        """
        # Clear the login fields and reset error messages.
        self.ids.login_username.text = ""
        self.ids.login_password.text = ""
        self.ids.login_error.text = ""

    def do_login(self):
        """
        Handles the login logic when a user attempts to sign in. The method gathers
        input from the username and password fields, validates that both fields are 
        filled, and then uses the backend db_manager to authenticate the user.
        """
        username = self.ids.login_username.text
        password = self.ids.login_password.text

        # Validate that the username and password fields are not empty.
        if not username or not password:
            self.ids.login_error.text = "Please fill in all fields."
            return
        
        try:
            # Attempt to authenticate the user with the provided credentials.
            user = db_manager.authenticate_user(username, password)
            print("Login successful for user:", user.username)
            # Save the authenticated user's id in the running app for future reference.
            App.get_running_app().user_id = user.id
            # Switch the current screen to the home screen upon successful login.
            self.manager.current = "home"
        except Exception as e:
            # If authentication fails, display the error message on the screen.
            self.ids.login_error.text = str(e)


#   Manages the user account creation screen. It handles the preparation of the
#   screen upon entry and processes the account creation by validating input
#   and calling the registration function from the backend.
class CreateAccountScreen(Screen):

    def on_pre_enter(self):
        """
        Method: on_pre_enter
        Purpose:
            Called automatically by the Kivy framework before the screen is shown.
            It clears any previously entered text in the username, password, email 
            fields, and resets any error messages, ensuring that the screen starts
            fresh for a new account creation attempt.
        """
        # Clear the signup fields and reset error messages.
        self.ids.signup_username.text = ""
        self.ids.signup_password.text = ""
        self.ids.signup_email.text = ""
        self.ids.signup_error.text = ""

    def do_create_account(self):
        """
        Handles the registration process when a user tries to create a new 
        account. It validates the input fields for a username, password, and email,
        and then registers the user using the backend db_manager.
        """
        username = self.ids.signup_username.text
        password = self.ids.signup_password.text
        email = self.ids.signup_email.text

        # Validate that all required fields (username, password, email) are filled.
        if not username or not password or not email:
            self.ids.signup_error.text = "All fields are required."
            return
        
        try:
            # Attempt to register the user with the provided details.
            user = db_manager.register_user(username, password, email)
            print("Account created for user:", user.username)
            # Navigate back to the login screen after successful account creation.
            self.manager.current = "login"
        except Exception as e:
            # If registration fails, display the error message on the screen.
            self.ids.signup_error.text = str(e)