# README #

### What is RefillRadar? ###
RefillRadar is a mobile-friendly app designed to help users manage prescriptions refills and set custom medication reminders based on the calculated end of a medication's supply. 

### How do I get set up? ###

1. Set up development virtual environment: 
    1. cd ~/path/to/refillradarapp
    2. python -m venv venv
    3. source venv/bin/activate

2. Install dependencies: 
    pip install -r requirements.txt
    pip install https://github.com/kivymd/KivyMD/archive/refs/heads/master.zip

    *This is necessary to use the latest version possible of KivyMD

3. Initialize database: 
    python -m backend.main

    *Your database file "refillradar_db.db" will be stored in the Documents folder on your system.

4. Run frontend:
    python -m frontend.main

### 📘 User Manual ###
RefillRadar is a mobile-friendly app designed to help users manage prescriptions and set custom medication reminders. Below is a quick guide to navigating and using the app:

#### 👤 Login & Sign Up #### 
Running backend/main.py will generate the application’s database and generate a test user and medication. After next running frontend/main.py, you will be presented with the app’s Login Screen. 
Here, you can login to the pre-generated user (username: test_user, password: secure_password) or you can click the “Create an Account” button to be brought to the Create Account Screen. 
On the sign up screen, you can enter credentials to create your own account. After clicking “Create Account” you can click “Back to Login” to enter your credentials and login.

#### 🏠 Home & Navigation ####
After logging in, you will land on the Home Screen. Here, you will see a list of your medications. If you logged in as the test user, a medication is already loaded in to see.  
Tapping the large plus button at the bottom of the screen will bring you to the  Add Prescription screen. 

#### 💊 Adding a Prescription (* Indicates necessary selection) ####
- Select a Medication Category: Choose an icon that best represents your medication (e.g., pill, injection).
- Pick a Color Tag: Assign a color to easily identify the prescription visually.
- Enter Medication Name*: Type in the medication name in the outlined text field.
- Indicate your Dosage*: Enter the max dosage you take per regular interval (eg. taking 1 pill every 2 days).
- Indicate your Supply*: Click the button that matches your prescription’s duration (30-Day, 60-Day, 90-Day, 100-Day).
- Indicate Start of Medication*: If you take your medication on an hourly basis, enter the time of your first dosage taken, otherwise enter the date of your first dosage (one or the other is required). 
- Indicate your Reminder Preferences*: The first line of input is to schedule the first notification that will remind you of your ending supply. The second line indicates how many secondary notifications you want and the interval of time between them. 
- (Optional) Add Notes: Include any special instructions, timing, or warnings under “Medication Details.”
- The Cancel button (along with the arrow at the very top left) will return you to the home page. Press the Add button after you’ve made all necessary selections and you will be returned to the home screen where you can see your new medication. 

### Creators ###
* Taylor Gilg
* Felicity Lester
* Tyler Conwell