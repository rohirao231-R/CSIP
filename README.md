# The Forge

The Forge is a browser-based gym and fitness management website built with
Python, NiceGUI, and MySQL. It provides role-based sign-in and dashboards for
members, employees, and administrators, with member fitness logging and
trainer communication.

## Features

### Member experience

- Create a member account, sign in, and keep a session across page visits.
- Log meals and review nutrition information, including daily calorie totals.
- Record strength-training sets and review workout history and personal bests.
- Log athletics and cardio sessions and review weekly activity time.
- View membership plan, payment status, and renewal information.
- View an assigned trainer, gym, and session time when those are configured.
- Chat with the assigned trainer and submit feedback to the administrator.

### Administrator and employee areas

- Role-specific administrator and employee dashboards.
- Administrator accounts use the `admin` role; employee accounts use the
  `employee` role.
- The current administrator and employee pages are dashboard landing pages.
  They do not yet provide full user-management, scheduling, or analytics
  controls in the UI.
- The database layer includes tables and operations for gyms, assignments,
  routines, weekly session slots, member/trainer messages, and feedback. A
  trainer-specific staff dashboard is not yet implemented.

## Requirements

- Python 3.10 or newer
- MySQL Server 8.0 or a compatible MySQL server

## Setup

1. Clone this repository and enter its directory.
2. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a MySQL database and a dedicated application account. Run the
   following in a MySQL administrative session, replacing the password with a
   strong value:

   ```sql
   CREATE DATABASE IF NOT EXISTS forge;
   CREATE USER 'forge_app'@'localhost' IDENTIFIED BY 'choose-a-strong-password';
   GRANT ALL PRIVILEGES ON forge.* TO 'forge_app'@'localhost';
   FLUSH PRIVILEGES;
   ```

5. Copy `.env.example` to `.env` and set `DB_PASSWORD` to the password assigned
   to `forge_app`. Generate a unique session key for `APP_STORAGE_SECRET`, for
   example with:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   Keep `.env` private; it is excluded from Git.

6. Start the website:

   ```bash
   python main.py
   ```

   Open <http://localhost:8080> in a browser.

The application creates its tables at startup. Register an account through the
sign-up form to create the first member or employee. To grant administrator
access, promote a registered account from a MySQL administrative session:

```sql
UPDATE forge.users SET role = 'admin' WHERE username = 'your-username';
```

## Project layout

- `main.py` — NiceGUI app, routes, and role-specific dashboard views
- `auth.py` — sign-in, registration, and password hashing
- `database.py` — MySQL connection and core user tables
- `forge_db.py` — fitness, membership, trainer assignment, chat, and feedback
  data operations
- `user_screens.py` — member fitness and trainer-facing screens

## Collaboration

Contributions are welcome. Open an issue to discuss a change, or submit a pull
request with a focused description and verification steps.
