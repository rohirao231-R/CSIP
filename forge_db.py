import datetime
from decimal import Decimal

import database

TOPICS = ['general', 'diet', 'bodybuilding', 'athletics']   # the chat subdivisions

# ---------------------------------------------------------------------
#  New tables.  "IF NOT EXISTS" means nothing is touched if they exist.
# ---------------------------------------------------------------------
NEW_TABLES = [
    """CREATE TABLE IF NOT EXISTS gyms (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        location VARCHAR(150) NOT NULL DEFAULT ''
    )""",
    # which trainer and which gym each member has
    """CREATE TABLE IF NOT EXISTS assignments (
        user_id INT PRIMARY KEY,
        trainer_id INT NULL,
        gym_id INT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""",
    # the workout routine written by the trainer or admin
    """CREATE TABLE IF NOT EXISTS routines (
        user_id INT PRIMARY KEY,
        routine TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""",
    # one weekly session slot per member, chosen by the trainer
    """CREATE TABLE IF NOT EXISTS slots (
        user_id INT PRIMARY KEY,
        trainer_id INT NOT NULL,
        slot_day VARCHAR(10) NOT NULL,
        start_time VARCHAR(5) NOT NULL,
        end_time VARCHAR(5) NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""",
    # one chat per member + trainer; "topic" is the subdivision
    """CREATE TABLE IF NOT EXISTS messages (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        trainer_id INT NOT NULL,
        sender_id INT NOT NULL,
        topic VARCHAR(20) NOT NULL DEFAULT 'general',
        body TEXT NOT NULL,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX (user_id, trainer_id, id)
    )""",
    """CREATE TABLE IF NOT EXISTS feedback (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        category VARCHAR(40) NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_read TINYINT(1) NOT NULL DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""",
]


# ---------------------------------------------------------------------
#  Two small helpers that talk to MySQL
# ---------------------------------------------------------------------

def _clean(row):
    """Turn dates and decimals into plain text / numbers so the screen can show them."""
    result = {}
    for key, value in row.items():
        if isinstance(value, Decimal):
            value = float(value)
        elif isinstance(value, datetime.datetime):
            value = value.strftime('%Y-%m-%d %H:%M')
        elif isinstance(value, datetime.date):
            value = value.isoformat()
        result[key] = value
    return result


def _read(sql, values=(), one=False):
    """Run a SELECT. one=True gives a single row (or None), otherwise a list of rows."""
    db = database.get_db()
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(sql, values)
        rows = []
        for row in cursor.fetchall():
            rows.append(_clean(row))
        if one:
            if len(rows) > 0:
                return rows[0]
            return None
        return rows
    finally:
        db.close()


def _write(sql, values=()):
    """Run an INSERT / UPDATE."""
    db = database.get_db()
    try:
        cursor = db.cursor()
        cursor.execute(sql, values)
        db.commit()
    finally:
        db.close()


def add_column_if_missing(cursor, table, column, definition):
    """Add a column to a table, but only if the table does not have it yet.
    (MySQL cannot do this on its own, so we look first and then add.)"""
    cursor.execute("SELECT COUNT(*) FROM information_schema.COLUMNS "
                   "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
                   (table, column))
    already_there = cursor.fetchone()[0]
    if already_there == 0:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_schema():
    """Create the new tables (call once when the app starts, AFTER database.init_db())."""
    db = database.get_db()
    try:
        cursor = db.cursor()
        for sql in NEW_TABLES:
            cursor.execute(sql)
        # diet_logs came from database.py without calories; old rows simply get 0
        add_column_if_missing(cursor, 'diet_logs', 'calories', 'INT NOT NULL DEFAULT 0')
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------
#  Diet   (table: diet_logs -> meal_details, calories, date_logged)
# ---------------------------------------------------------------------

def add_diet(user_id, meal_details, calories=0):
    _write("INSERT INTO diet_logs (user_id, meal_details, calories) VALUES (%s, %s, %s)",
           (user_id, meal_details, calories))


def list_diet(user_id, limit=60):
    return _read("SELECT date_logged, meal_details, calories FROM diet_logs "
                 "WHERE user_id = %s ORDER BY id DESC LIMIT %s", (user_id, limit))


def meals_today(user_id):
    row = _read("SELECT COUNT(*) AS total FROM diet_logs "
                "WHERE user_id = %s AND DATE(date_logged) = CURDATE()", (user_id,), one=True)
    return row['total']


def calories_today(user_id):
    row = _read("SELECT COALESCE(SUM(calories), 0) AS total FROM diet_logs "
                "WHERE user_id = %s AND DATE(date_logged) = CURDATE()", (user_id,), one=True)
    return int(row['total'])


# ---------------------------------------------------------------------
#  Power lifts   (table: power_lifts_logs -> exercise_name, sets, reps, weight)
# ---------------------------------------------------------------------

def add_workout(user_id, exercise, sets, reps, weight):
    _write("INSERT INTO power_lifts_logs (user_id, exercise_name, sets, reps, weight) "
           "VALUES (%s, %s, %s, %s, %s)", (user_id, exercise, sets, reps, weight))


def list_workouts(user_id, limit=60):
    return _read("SELECT date_logged, exercise_name AS exercise, sets, reps, weight "
                 "FROM power_lifts_logs WHERE user_id = %s ORDER BY id DESC LIMIT %s", (user_id, limit))


def personal_bests(user_id, limit=10):
    return _read("SELECT exercise_name AS exercise, MAX(weight) AS best_weight, COUNT(*) AS times_logged "
                 "FROM power_lifts_logs WHERE user_id = %s "
                 "GROUP BY exercise_name ORDER BY best_weight DESC LIMIT %s", (user_id, limit))


def get_routine(user_id):
    return _read("SELECT routine FROM routines WHERE user_id = %s", (user_id,), one=True)


# ---------------------------------------------------------------------
#  Athletics   (table: athletics_logs -> activity_type, duration_minutes)
# ---------------------------------------------------------------------

def add_athletics(user_id, activity, minutes):
    _write("INSERT INTO athletics_logs (user_id, activity_type, duration_minutes) "
           "VALUES (%s, %s, %s)", (user_id, activity, minutes))


def list_athletics(user_id, limit=60):
    return _read("SELECT date_logged, activity_type AS activity, duration_minutes AS minutes "
                 "FROM athletics_logs WHERE user_id = %s ORDER BY id DESC LIMIT %s", (user_id, limit))


def minutes_this_week(user_id):
    row = _read("SELECT COALESCE(SUM(duration_minutes), 0) AS total FROM athletics_logs "
                "WHERE user_id = %s AND date_logged >= DATE_SUB(NOW(), INTERVAL 7 DAY)",
                (user_id,), one=True)
    return int(row['total'])


# ---------------------------------------------------------------------
#  Membership   (table: memberships -> plan_details, payment_status, renewal_date)
# ---------------------------------------------------------------------

def get_membership(user_id):
    return _read("SELECT plan_details, payment_status, renewal_date "
                 "FROM memberships WHERE user_id = %s", (user_id,), one=True)


# ---------------------------------------------------------------------
#  Trainer, gym, session slot
# ---------------------------------------------------------------------

def get_assignment(user_id):
    """Returns {} when the member has no trainer yet."""
    row = _read("SELECT a.trainer_id, a.gym_id, t.username AS trainer_name, "
                "g.name AS gym_name, g.location AS gym_location "
                "FROM assignments a "
                "LEFT JOIN users t ON t.id = a.trainer_id "
                "LEFT JOIN gyms g ON g.id = a.gym_id "
                "WHERE a.user_id = %s", (user_id,), one=True)
    if row is None:
        return {}
    return row


def get_slot(user_id):
    return _read("SELECT slot_day, start_time, end_time FROM slots WHERE user_id = %s", (user_id,), one=True)


# ---------------------------------------------------------------------
#  Chat
# ---------------------------------------------------------------------

def list_messages(user_id, trainer_id, topic=None, limit=200):
    """topic=None gives every message. The newest 'limit' messages, oldest first."""
    sql = "SELECT sender_id, topic, body, sent_at FROM messages WHERE user_id = %s AND trainer_id = %s"
    values = [user_id, trainer_id]
    if topic is not None:
        sql = sql + " AND topic = %s"
        values.append(topic)
    sql = sql + " ORDER BY id DESC LIMIT %s"
    values.append(limit)
    rows = _read(sql, tuple(values))
    rows.reverse()            # we asked for newest first, the screen wants oldest first
    return rows


def send_message(user_id, trainer_id, sender_id, topic, body):
    if topic not in TOPICS:
        topic = 'general'
    _write("INSERT INTO messages (user_id, trainer_id, sender_id, topic, body) "
           "VALUES (%s, %s, %s, %s, %s)", (user_id, trainer_id, sender_id, topic, body))


# ---------------------------------------------------------------------
#  Feedback
# ---------------------------------------------------------------------

def add_feedback(user_id, category, message):
    _write("INSERT INTO feedback (user_id, category, message) VALUES (%s, %s, %s)",
           (user_id, category, message))