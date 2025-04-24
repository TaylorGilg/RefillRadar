from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.metrics import dp
from datetime import datetime
from calendar import monthrange
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Line
from kivy.uix.popup import Popup
from kivy.core.window import Window


class CalendarScreen(Screen):
    """ 
    A screen that displays a dynamic calendar with medication reminders. 
 
    Attributes: 
        calendar_grid (ObjectProperty): The grid layout for displaying calendar days. 
        month_label (ObjectProperty): The label displaying the current month and year. 
    """ 
    calendar_grid = ObjectProperty(None)
    month_label = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_date = datetime.today()  # Track the current displayed month

    def on_enter(self):
        """ 
        Populate the calendar when the screen is entered. 
        """ 
        Clock.schedule_once(self.populate_calendar)

    def change_month(self, direction):
        """ 
        Change the displayed month. 
 
        Args: 
            direction (int): The direction to change the month (-1 for previous, 1 for next). 
        """ 
        month = self.current_date.month + direction
        year = self.current_date.year

        if month < 1:  # Wrap around to the previous year
            month = 12
            year -= 1
        elif month > 12:  # Wrap around to the next year
            month = 1
            year += 1

        self.current_date = datetime(year, month, 1)
        self.populate_calendar()

    def populate_calendar(self, *args):
        """ 
        Populate the calendar grid with buttons for each day of the current month. 
        """ 
        # Define a constant height for each calendar cell
        cell_height = dp(62)  # Adjust this value to make buttons shorter or taller

        # Sample medication schedule for demonstration.
        meds_schedule = {3, 10, 15, 20, 25}

        # Get the current date information.
        today = datetime.today()
        year, month = self.current_date.year, self.current_date.month

        # Update the month label.
        self.ids.month_label.text = self.current_date.strftime("%B %Y")

        # Get the first day and total number of days in the month.
        first_day_of_month = datetime(year, month, 1)
        _, num_days = monthrange(year, month)

        # Clear the grid.
        self.ids.calendar_grid.clear_widgets()

        # Add empty widgets for days before the first day of the month.
        for _ in range(first_day_of_month.weekday()):
            self.ids.calendar_grid.add_widget(Label(size_hint=(1 / 7, None), height=cell_height))

        # Add buttons for each day in the month.
        for day in range(1, num_days + 1):
            btn = Button(
                text=str(day),
                size_hint=(1 / 7, None),
                height=cell_height,
                background_color=(0.2, 0.6, 1, 0.8) if day in meds_schedule else (1, 1, 1, 0.7)
            )

            # Highlight the current day with an outline.
            if day == today.day and month == today.month and year == today.year:
                with btn.canvas.before:
                    from kivy.graphics import Color, Line
                    Color(0.2, 0.6, 1, 1)  # Blue color for highlight
                    Line(rectangle=(btn.x, btn.y, btn.width, btn.height), width=2)

            # Bind the button events.
            btn.bind(on_release=lambda instance, day=day: self.show_meds(day))
            self.ids.calendar_grid.add_widget(btn)

        # Add filler widgets for the remaining cells in the grid.
        total_cells = 7 * 6  # Total number of cells (7 columns x 6 rows)
        used_cells = first_day_of_month.weekday() + num_days
        for _ in range(total_cells - used_cells):
            self.ids.calendar_grid.add_widget(Label(size_hint=(1 / 7, None), height=cell_height))

    def show_meds(self, day):
        """ 
        Display a popup with medications for the selected day. 
 
        Args: 
            day (int): The selected day. 
        """ 
        # Example medication data (replace with actual data source)
        meds = {
            "3": "Glimepiride Reminder 1",
            "10": "Probiotic End Day",
            "15": "Benazepril End Day",
            "20": "Aspirin Reminder 3",
            "25": "Glimepiride Reminder 2"
        }
        meds_for_day = meds.get(str(day), "No medications for this day")

        # Create the content label.
        content = Label(text=meds_for_day)

        # Create and display a popup
        popup = Popup(
            title=f"Medications for Day {day}",
            content=Label(text=meds_for_day),
            size_hint=(0.6, 0.4),
            auto_dismiss=True,
        )
        popup.open()

        def clear_popup_content(instance):
            instance.content = Label(text="")  # Replace with a new empty label.
        # Bind that function to the on_dismiss event.
        popup.bind(on_dismiss=clear_popup_content)
        popup.open()

