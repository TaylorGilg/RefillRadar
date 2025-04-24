from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label

class SettingsScreen(Screen):
    """ 
    A screen for managing user settings, including logging out and deleting all user data. 
 
    Methods: 
        show_confirmation_dialog(): Displays a popup to confirm data deletion. 
        delete_all_data(popup): Deletes all user data and dismisses the popup. 
        logout(): Navigates back to the login screen. 
    """ 
    def show_confirmation_dialog(self):
        """
        Show a confirmation dialog for deleting all data using Popup.
        """
        # Create the content for the popup
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Add a label with the confirmation message
        content.add_widget(Label(
            text="Are you sure?\nThis will delete all user data.\nThis cannot be undone.",
            color=(1, 1, 1, 1),  # Set text color to white
            halign="center",  # Center-align the text
            valign="middle"   # Vertically align the text
        ))

        # Add buttons for "CANCEL" and "DELETE"
        button_layout = BoxLayout(orientation="horizontal", spacing=10)
        cancel_button = Button(
            text="CANCEL",
            size_hint=(1, None),
            height=40,
            background_color=(0.2, 0.4, 1, 0.7),  # Set button color to teal
            on_release=lambda x: popup.dismiss()
        )
        delete_button = Button(
            text="DELETE",
            size_hint=(1, None),
            height=40,
            background_color=(0.2, 0.4, 1, 0.9),  # Set button color to dark blue
            on_release=lambda x: self.delete_all_data(popup)
        )
        button_layout.add_widget(cancel_button)
        button_layout.add_widget(delete_button)

        # Add the buttons to the content
        content.add_widget(button_layout)

        # Create the popup
        popup = Popup(
            title="Confirmation",
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )

        # Open the popup
        popup.open()

    #def delete_all_data(self, popup):
        """ 
        To be implemented in the future: Deletes all user and medication data and dismisses the popup. 
 
        Args: 
            popup (Popup): The popup to dismiss after deletion. 
        """ 
        #popup.dismiss()
        #print("All data deleted!")  

    def logout(self):
        """
        Navigate back to the login screen.
        """
        self.manager.current = "login"