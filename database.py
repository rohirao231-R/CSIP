import mysql.connector
import os
import sys
from dotenv import load_dotenv

load_dotenv()

DB_HOST = "localhost"
DB_USER = os.getenv("DB_USER", "forge_app")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = "forge"


def init_db():

    try:
        db = get_db()
        cursor = db.cursor()

        # Create Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role ENUM('admin', 'employee', 'user') DEFAULT 'user',
                remember_token VARCHAR(255)
            )
        """)

        # Add this inside the init_db() function in database.py, directly under the users table creation

        # Diet Logs
        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS diet_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        meal_details TEXT,
                        date_logged TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)

        # Power Lifts Logs (Replaces placeholder bodybuilding table)
        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS power_lifts_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        exercise_name VARCHAR(100),
                        sets INT,
                        reps INT,
                        weight DECIMAL(5,2),
                        date_logged TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)

        # Athletics Logs
        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS athletics_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        activity_type VARCHAR(100),
                        duration_minutes INT,
                        date_logged TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)

        # Memberships
        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS memberships (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL UNIQUE,
                        plan_details VARCHAR(255),
                        payment_status ENUM('paid', 'pending', 'overdue') DEFAULT 'pending',
                        renewal_date DATE,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)

        # Note: As you build the employee and member sections, you can add
        # CREATE TABLE statements here for things like 'workouts' or 'schedules'.

        db.commit()
        db.close()
        print("Database initialized successfully.")

    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        print("Please check that your DB_PASSWORD is correct and MySQL is running locally.")
        sys.exit(1)


def get_db():
    if not DB_PASSWORD:
        raise RuntimeError("Set DB_PASSWORD in the environment or .env file.")
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


def get_user_by_username(username):
    """Fetches a user dictionary by their username."""
    db = get_db()
    cursor = db.cursor(dictionary=True)  # Returns a dict instead of a tuple
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    db.close()
    return user


def get_user_by_token(token):
    """Fetches a user dictionary using their remember-me token."""
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE remember_token = %s", (token,))
    user = cursor.fetchone()
    db.close()
    return user


def create_user(username, hashed_password, role):
    """Inserts a new user into the database."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            (username, hashed_password, role)
        )
        db.commit()
        success = True
    except mysql.connector.IntegrityError:
        # Happens if the username already exists (UNIQUE constraint)
        success = False
    finally:
        db.close()
    return success


def update_user_token(user_id, token):
    """Updates the remember-me token for a specific user."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET remember_token = %s WHERE id = %s", (token, user_id))
    db.commit()
    db.close()


def clear_user_token(user_id):
    """Clears the remember-me token (used for logging out)."""
    update_user_token(user_id, None)