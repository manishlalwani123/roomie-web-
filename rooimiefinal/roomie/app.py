import os
import mysql.connector
from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

# -------------------------
# Upload Configuration
# -------------------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# -------------------------
# Environment Variables
# -------------------------
MYSQL_HOST = os.environ.get("MYSQL_HOST")
MYSQL_USER = os.environ.get("MYSQL_USER")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_DB = os.environ.get("MYSQL_DB")
SECRET_KEY = os.environ.get("SECRET_KEY", "your_secret_key")

# -------------------------
# Flask App
# -------------------------
app = Flask(__name__)

app.config["SECRET_KEY"] = SECRET_KEY
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def create_connection():
    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def create_tables():
    try:
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                fullname VARCHAR(100) NOT NULL,
                cuchd_id VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_information (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_cuchd_id VARCHAR(50) NOT NULL,
                department VARCHAR(100),
                year_of_study INT,
                phone_no VARCHAR(20),
                gender VARCHAR(10),
                dob DATE,
                district VARCHAR(100),
                state VARCHAR(100),
                FOREIGN KEY (user_cuchd_id) REFERENCES users (cuchd_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS room_preferences (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_cuchd_id VARCHAR(50),
                accommodation_type VARCHAR(50),
                preferred_location VARCHAR(100),
                rent_budget INT,
                num_roommates INT,
                bhk INT,
                amenity1 BOOLEAN,
                amenity2 BOOLEAN,
                amenity3 BOOLEAN,
                FOREIGN KEY (user_cuchd_id) REFERENCES users(cuchd_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS roommate_preferences (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_cuchd_id VARCHAR(50),
                department VARCHAR(100),
                year_of_study INT,
                sleep_schedule VARCHAR(100),
                gender VARCHAR(10),
                state VARCHAR(100),
                FOREIGN KEY (user_cuchd_id) REFERENCES users(cuchd_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_cuchd_id VARCHAR(50),
                introduction TEXT,
                profile_picture VARCHAR(255),
                FOREIGN KEY (user_cuchd_id) REFERENCES users(cuchd_id)
            )
            """
        )
        connection.commit()
        cursor.close()
        connection.close()
    except mysql.connector.Error as e:
        print(f"Error creating tables: {e}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_picture(file):
    if file.filename == "":
        return None

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        file.save(filepath)

        return filename

    return None  # File extension not allowed

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form['fullname']
        cuchd_id = request.form['cuchd_id']
        password = request.form['password']
        
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    SELECT * FROM users WHERE cuchd_id = %s
                    """,
                    (cuchd_id,)
                )
                existing_user = cursor.fetchone()
                if existing_user:
                    error_message = 'The provided CUCHD ID already exists. Please choose a different one.'
                    return render_template('signup.html', error=error_message)
                else:
                    cursor.execute(
                        """
                        INSERT INTO users (fullname, cuchd_id, password)
                        VALUES (%s, %s, %s)
                        """,
                        (fullname, cuchd_id, password)
                    )
                    connection.commit()
                    cursor.close()
                    connection.close()
                    session['cuchd_id'] = cuchd_id
                    return redirect(url_for('addinfo'))
            except mysql.connector.Error as e:
                print(f"Error executing SQL query: {e}")
                return 'An error occurred while signing up'
        else:
            return 'Error connecting to database'
    return render_template('signup.html')

@app.route('/addinfo', methods=['GET', 'POST'])
def addinfo():
    if request.method == 'POST':
        user_cuchd_id = session.get('cuchd_id')
        if not user_cuchd_id:
            return 'User session not found. Please log in again.'
        
        department = request.form.get('department')
        year_of_study = request.form.get('year_of_study')
        phone_no = request.form.get('phone_no')
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        district = request.form.get('district')
        state = request.form.get('state')

        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                # Insert the user's personal information into the database
                cursor.execute(
                    """
                    INSERT INTO user_information (user_cuchd_id, department, year_of_study, phone_no, gender, dob, district, state)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (user_cuchd_id, department, year_of_study, phone_no, gender, dob, district, state)
                )
                connection.commit()
                cursor.close()
                connection.close()
                return redirect(url_for('room_preferences'))
            except mysql.connector.Error as e:
                print(f"Error executing SQL query: {e}")
                return 'An error occurred while saving personal information.'
        else:
            return 'Error connecting to database'
    return render_template('addinfo.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cuchd_id = request.form['cuchd_id']
        password = request.form['password']
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT * FROM users WHERE cuchd_id = %s AND password = %s
                    """,
                    (cuchd_id, password)
                )
                user = cursor.fetchone()
                cursor.close()
                connection.close()
                if user:
                    session['cuchd_id'] = cuchd_id
                    return redirect(url_for('user_records'))  # Redirect to the home route
                else:
                    error_message = 'Invalid CUCHD ID or password. Please try again.'
                    return render_template('login.html', error=error_message)
            except mysql.connector.Error as e:
                print(f"Error executing SQL query: {e}")
                return 'An error occurred while logging in'
        else:
            return 'Error connecting to database'
    return render_template('login.html')

@app.route('/room_preferences', methods=['GET', 'POST'])
def room_preferences():
    if request.method == 'POST':
        # Get the logged-in user's CUCHD ID from the session
        user_cuchd_id = session.get('cuchd_id')
        if not user_cuchd_id:
            return 'User session not found. Please log in again.'
        
        # Retrieve form data
        accommodation_type = request.form.get('accommodation_type')
        preferred_location = request.form.get('preferred_location')
        rent_budget = request.form.get('rent_budget')
        num_roommates = request.form.get('num_roommates')
        bhk = request.form.get('bhk')
        amenity1 = 'amenity1' in request.form
        amenity2 = 'amenity2' in request.form
        amenity3 = 'amenity3' in request.form
        
        # Store the room preference data in the database
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO room_preferences (user_cuchd_id, accommodation_type, preferred_location, rent_budget, num_roommates, bhk, amenity1, amenity2, amenity3)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (user_cuchd_id, accommodation_type, preferred_location, rent_budget, num_roommates, bhk, amenity1, amenity2, amenity3)
                )
                connection.commit()
                cursor.close()
                connection.close()
                return redirect(url_for('roommate_preferences'))  # Redirect to the home page after submitting room preferences
            except mysql.connector.Error as e:
                print(f"Error executing SQL query: {e}")
                return 'An error occurred while saving room preferences'
        else:
            return 'Error connecting to database'
    return render_template('room_preferences.html')

@app.route('/roommate_preferences', methods=['GET', 'POST'])
def roommate_preferences():
    if request.method == 'POST':
        # Get the logged-in user's CUCHD ID from the session
        user_cuchd_id = session.get('cuchd_id')
        if not user_cuchd_id:
            return 'User session not found. Please log in again.'
        
        # Retrieve logged-in user's room preferences
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    SELECT * FROM room_preferences WHERE user_cuchd_id = %s
                    """,
                    (user_cuchd_id,)
                )
                room_preferences_data = cursor.fetchone()
                if not room_preferences_data:
                    return 'Room preferences not found. Please fill out room preferences first.'
                
                # Retrieve form data for roommate preferences
                department = request.form.get('department')
                year_of_study = request.form.get('year_of_study')
                sleep_schedule = request.form.get('sleep_schedule')
                gender = request.form.get('gender')
                state = request.form.get('state')
                
                # Insert roommate preference data
                cursor.execute(
                    """
                    INSERT INTO roommate_preferences (user_cuchd_id, department, year_of_study, sleep_schedule, gender, state)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (user_cuchd_id, department, year_of_study, sleep_schedule, gender, state)
                )
                connection.commit()
                cursor.close()
                connection.close()
                return redirect(url_for('profile'))  # Redirect to the profile page after submitting roommate preferences
            except mysql.connector.Error as e:
                print(f"Error executing SQL query: {e}")
                return 'An error occurred while saving roommate preferences'
        else:
            return 'Error connecting to database'
    return render_template('roommate_preferences.html')

# Define a route for the profile page
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        # Get the logged-in user's CUCHD ID from the session
        user_cuchd_id = session.get('cuchd_id')
        if not user_cuchd_id:
            return 'User session not found. Please log in again.'
        
        # Retrieve form data
        introduction = request.form.get('introduction')

        # Handle file upload for profile picture
        profile_picture = ''
        if 'profile_picture' in request.files:
            profile_picture = save_profile_picture(request.files['profile_picture'])
        
        # Store the profile data in the database
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO profiles (user_cuchd_id, introduction, profile_picture)
                    VALUES (%s, %s, %s)
                    """,
                    (user_cuchd_id, introduction, profile_picture)
                )
                connection.commit()
                cursor.close()
                connection.close()
                
                # Redirect to the final page with a success message
                
                return redirect(url_for('final'))
            except mysql.connector.Error as e:
                # Log the error
                app.logger.error(f"Error executing SQL query: {e}")
                # Return an error message to the user
                return 'An error occurred while saving profile'
        else:
            return 'Error connecting to database'
    
    return render_template('profile.html')

@app.route('/final')
def final():
    return render_template('final.html')

# Function to retrieve user data from the 'users' table
def get_user_data(cuchd_id):
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT * FROM users WHERE cuchd_id = %s
                """,
                (cuchd_id,)
            )
            user_data = cursor.fetchone()
            cursor.close()
            connection.close()
            return user_data
        else:
            print("Error connecting to database")
            return None
    except mysql.connector.Error as e:
        print(f"Error executing SQL query: {e}")
        return None

# Function to retrieve personal information from the 'user_information' table
def get_personal_info(cuchd_id):
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT * FROM user_information WHERE user_cuchd_id = %s
                """,
                (cuchd_id,)
            )
            personal_info = cursor.fetchone()
            cursor.close()
            connection.close()
            return personal_info
        else:
            print("Error connecting to database")
            return None
    except mysql.connector.Error as e:
        print(f"Error executing SQL query: {e}")
        return None

# Function to retrieve room preferences from the 'room_preferences' table
def get_room_preferences(cuchd_id):
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT * FROM room_preferences WHERE user_cuchd_id = %s
                """,
                (cuchd_id,)
            )
            room_preferences = cursor.fetchone()
            cursor.close()
            connection.close()
            return room_preferences
        else:
            print("Error connecting to database")
            return None
    except mysql.connector.Error as e:
        print(f"Error executing SQL query: {e}")
        return None

# Function to retrieve roommate preferences from the 'roommate_preferences' table
def get_roommate_preferences(cuchd_id):
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT * FROM roommate_preferences WHERE user_cuchd_id = %s
                """,
                (cuchd_id,)
            )
            roommate_preferences = cursor.fetchone()
            cursor.close()
            connection.close()
            return roommate_preferences
        else:
            print("Error connecting to database")
            return None
    except mysql.connector.Error as e:
        print(f"Error executing SQL query: {e}")
        return None

# Function to retrieve profile information from the 'profiles' table
def get_profile_info(cuchd_id):
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT * FROM profiles WHERE user_cuchd_id = %s
                """,
                (cuchd_id,)
            )
            profile_info = cursor.fetchone()
            cursor.close()
            connection.close()
            return profile_info
        else:
            print("Error connecting to database")
            return None
    except mysql.connector.Error as e:
        print(f"Error executing SQL query: {e}")
        return None

@app.route('/user_account/<cuchd_id>')
def user_account(cuchd_id):
    user_data = get_user_data(cuchd_id)
    personal_info = get_personal_info(cuchd_id)
    room_preferences = get_room_preferences(cuchd_id)
    roommate_preferences = get_roommate_preferences(cuchd_id)
    profile_info = get_profile_info(cuchd_id)

    if user_data and personal_info and room_preferences and roommate_preferences and profile_info:
        return render_template('user_account.html', 
                               user=user_data, 
                               personal_info=personal_info, 
                               room_preferences=room_preferences, 
                               roommate_preferences=roommate_preferences, 
                               profile=profile_info)
    else:
        return "Error: Unable to fetch user data"
# Route for logging out
# Modify the route to fetch user records with required fields
@app.route('/user_records')
def user_records():
    # Check if user is logged in
    if 'cuchd_id' in session:
        try:
            connection = create_connection()
            if connection:
                cursor = connection.cursor(dictionary=True)
                # Modify the query to join users and user_information tables
                cursor.execute("""
                    SELECT users.fullname, users.cuchd_id, user_information.department,
                           user_information.year_of_study, user_information.phone_no,
                           user_information.gender
                    FROM users
                    INNER JOIN user_information ON users.cuchd_id = user_information.user_cuchd_id
                """)
                user_records = cursor.fetchall()
                cursor.close()
                connection.close()
                return render_template('user_records.html', user_records=user_records)
            else:
                return 'Error connecting to database'
        except mysql.connector.Error as e:
            print(f"Error executing SQL query: {e}")
            return 'An error occurred while fetching user records'
    else:
        # If user is not logged in, redirect to the login page
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    # Redirect the user to the login page
    return redirect(url_for('login'))



if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
