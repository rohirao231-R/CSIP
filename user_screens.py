"""user_screens.py - what opens when a member clicks a pentagon button.

Every screen is one simple function:   show_something(user, go_back)
    user    = the logged-in person (a dictionary with 'id', 'username', 'role')
    go_back = the function that brings the pentagon back (the arrow button uses it)

All saving and reading of data is done by forge_db.py, so this file
only has to build the screen. The date and time of every log is added
automatically by MySQL (the date_logged column), so nobody types a date.
"""
from datetime import date

from nicegui import ui

import forge_db

# ---- Colours (the same ones used in main.py) ----
CARD = 'w-full bg-[#1f150c] border border-[#412d15] rounded-sm p-6 gap-3'
HEADING = 'text-lg font-bold text-[#b08d57] tracking-wider'
TEXT = 'text-[#e1dcc9]'
MUTED = 'text-[#e1dcc9] opacity-70'
STAT_CARD = 'bg-[#1f150c] border border-[#412d15] rounded-sm items-center gap-0'

# ---- Choices shown in the drop-down lists ----
MEALS = ['Breakfast', 'Lunch', 'Snack', 'Dinner', 'Pre-workout', 'Post-workout']
ACTIVITIES = ['Running', 'Cycling', 'Swimming', 'Skipping', 'Football', 'Cricket', 'Badminton', 'Other']
FEEDBACK_TOPICS = ['General', 'My trainer', 'Gym or equipment', 'Membership and billing', 'App problem']

# value stored in the database -> name shown on screen
TOPIC_NAMES = {'all': 'All', 'general': 'General', 'diet': 'Diet',
               'bodybuilding': 'Power lifts', 'athletics': 'Athletics'}

# colour of the payment status word
STATUS_COLORS = {'paid': 'text-green-400', 'pending': 'text-yellow-400', 'overdue': 'text-red-400'}


# =====================================================================
#  Small helper functions used by every screen
# =====================================================================

def top_bar(title, go_back):
    """The row at the top of every screen: back arrow + title."""
    with ui.row().classes('w-full items-center gap-4 border-b border-[#412d15] pb-3'):
        ui.button(icon='arrow_back', on_click=go_back).props('flat round')
        ui.label(title).classes('text-2xl font-black text-[#f5efe6] tracking-widest')


def whole(box):
    """Turn what is typed in a number box into a whole number (empty box = 0)."""
    return int(box.value or 0)


def try_save(action, *values):
    """Run a save function. If the database complains, show the problem instead of crashing.
    (*values means: pass along however many values we were given.)"""
    try:
        action(*values)
        return True
    except Exception as error:
        ui.notify(f'Could not save: {error}', type='negative')
        return False


def stat_box(number, caption):
    """A small card with a big number and a caption under it."""
    with ui.card().classes(STAT_CARD):
        ui.label(str(number)).classes('text-2xl font-bold text-[#e1dcc9]')
        ui.label(caption).classes('text-xs text-[#e1dcc9] opacity-70')


def make_table(columns, rows):
    """Show a table. columns is a list like [('date_logged', 'Date'), ('exercise', 'Exercise')]."""
    table_columns = []
    for field, label in columns:
        table_columns.append({'name': field, 'label': label, 'field': field, 'align': 'left'})

    number = 0
    for row in rows:          # every table row needs its own id number
        row['id'] = number
        number = number + 1

    ui.table(columns=table_columns, rows=rows, row_key='id', pagination=8).classes('w-full')


# =====================================================================
#  DIET
# =====================================================================

def show_diet(user, go_back):
    top_bar('DIET', go_back)
    uid = user['id']

    with ui.card().classes(CARD):
        ui.label('Log a meal').classes(HEADING)
        with ui.row().classes('w-full items-start gap-3'):
            meal_box = ui.select(MEALS, value='Breakfast', label='Meal').props('outlined dense')
            food_box = ui.input('What did you eat?').props('outlined dense').classes('grow')
            calories_box = ui.number('Calories', min=0, max=10000, format='%.0f') \
                .props('outlined dense').classes('w-36')

        def save():
            food = (food_box.value or '').strip()
            if food == '':
                ui.notify('Please write what you ate.', type='warning')
                return
            calories = whole(calories_box)         # an empty box counts as 0
            if calories > 10000:
                ui.notify('Calories can be at most 10000 for one meal.', type='warning')
                return
            # the meal name and the food are saved together in one piece of text
            if try_save(forge_db.add_diet, uid, f'{meal_box.value}: {food}', calories):
                food_box.value = ''
                calories_box.value = None
                ui.notify('Meal saved', type='positive')
                show_history()

        ui.button('SAVE MEAL', icon='add', on_click=save)

    # this box gets redrawn after every save
    history_box = ui.column().classes('w-full')

    def show_history():
        history_box.clear()
        with history_box:
            with ui.row().classes('gap-3'):
                stat_box(forge_db.meals_today(uid), 'Meals logged today')
                stat_box(forge_db.calories_today(uid), 'Calories today')
            rows = forge_db.list_diet(uid)
            if len(rows) == 0:
                ui.label('No meals logged yet.').classes(MUTED)
            else:
                for row in rows:
                    if row['calories'] == 0:       # no calories were entered for this meal
                        row['calories'] = '-'
                make_table([('date_logged', 'Date and time'), ('meal_details', 'What was eaten'),
                            ('calories', 'Calories')], rows)

    show_history()


# =====================================================================
#  POWER LIFTS
# =====================================================================

def show_powerlifts(user, go_back):
    top_bar('POWER LIFTS', go_back)
    uid = user['id']

    # ---- current routine (written by the trainer or admin) ----
    with ui.card().classes(CARD):
        ui.label('Your current routine').classes(HEADING)
        saved_routine = forge_db.get_routine(uid)
        if saved_routine and saved_routine['routine']:
            ui.label(saved_routine['routine']).classes(TEXT + ' whitespace-pre-wrap')
        else:
            ui.label('No routine yet. Your trainer or the admin will add one.').classes(MUTED)

    # ---- the form ----
    with ui.card().classes(CARD):
        ui.label('Log a set').classes(HEADING)
        with ui.row().classes('w-full items-center gap-3'):
            exercise_box = ui.input('Exercise').props('outlined dense').classes('grow')
            sets_box = ui.number('Sets', value=3, min=1, format='%.0f').props('outlined dense')
            reps_box = ui.number('Reps', value=10, min=1, format='%.0f').props('outlined dense')
            weight_box = ui.number('Weight (kg)', value=0, min=0, max=999).props('outlined dense').classes('w-36')

        def save():
            if not (exercise_box.value or '').strip():
                ui.notify('Please enter the exercise name.', type='warning')
                return
            if whole(sets_box) < 1 or whole(reps_box) < 1:
                ui.notify('Sets and reps must be at least 1.', type='warning')
                return
            weight = float(weight_box.value or 0)
            if weight > 999:
                ui.notify('Weight can be at most 999 kg.', type='warning')
                return
            if try_save(forge_db.add_workout, uid, exercise_box.value.strip(),
                        whole(sets_box), whole(reps_box), weight):
                exercise_box.value = ''
                ui.notify('Set saved', type='positive')
                show_history()

        ui.button('SAVE SET', icon='add', on_click=save)

    # ---- personal bests and history ----
    history_box = ui.column().classes('w-full gap-3')

    def show_history():
        history_box.clear()
        with history_box:
            ui.label('Personal bests').classes(HEADING)
            bests = forge_db.personal_bests(uid)
            if len(bests) == 0:
                ui.label('Log a few sets to see your personal bests.').classes(MUTED)
            else:
                make_table([('exercise', 'Exercise'), ('best_weight', 'Best weight (kg)'),
                            ('times_logged', 'Times logged')], bests)

            ui.label('All sets').classes(HEADING)
            rows = forge_db.list_workouts(uid)
            if len(rows) == 0:
                ui.label('No sets logged yet.').classes(MUTED)
            else:
                make_table([('date_logged', 'Date and time'), ('exercise', 'Exercise'), ('sets', 'Sets'),
                            ('reps', 'Reps'), ('weight', 'Weight (kg)')], rows)

    show_history()


# =====================================================================
#  ATHLETICS
# =====================================================================

def show_athletics(user, go_back):
    top_bar('ATHLETICS', go_back)
    uid = user['id']

    with ui.card().classes(CARD):
        ui.label('Log a session').classes(HEADING)
        with ui.row().classes('w-full items-center gap-3'):
            activity_box = ui.select(ACTIVITIES, value='Running', label='Activity').props('outlined dense')
            minutes_box = ui.number('Minutes', min=1, max=1000, format='%.0f').props('outlined dense')

        def save():
            minutes = whole(minutes_box)
            if minutes < 1:
                ui.notify('Please enter how many minutes you trained.', type='warning')
                return
            if try_save(forge_db.add_athletics, uid, activity_box.value, minutes):
                minutes_box.value = None
                ui.notify('Session saved', type='positive')
                show_history()

        ui.button('SAVE SESSION', icon='add', on_click=save)

    history_box = ui.column().classes('w-full')

    def show_history():
        history_box.clear()
        with history_box:
            with ui.row():
                stat_box(forge_db.minutes_this_week(uid), 'Minutes in the last 7 days')
            rows = forge_db.list_athletics(uid)
            if len(rows) == 0:
                ui.label('No sessions logged yet.').classes(MUTED)
            else:
                make_table([('date_logged', 'Date and time'), ('activity', 'Activity'),
                            ('minutes', 'Minutes')], rows)

    show_history()


# =====================================================================
#  MEMBERSHIP  (the member can look, the admin changes it)
# =====================================================================

def show_membership(user, go_back):
    top_bar('MEMBERSHIP', go_back)
    uid = user['id']

    plan = forge_db.get_membership(uid)
    with ui.card().classes(CARD):
        ui.label('Your plan').classes(HEADING)
        if plan is None:
            ui.label('No membership on file yet. Please ask the front desk to set one up.').classes(MUTED)
        else:
            ui.label(plan['plan_details'] or 'Plan not described').classes('text-2xl font-bold text-[#e1dcc9]')

            status = plan['payment_status']
            ui.label(f'Payment: {status.upper()}').classes('font-bold ' + STATUS_COLORS.get(status, TEXT))

            if plan['renewal_date']:
                days_left = (date.fromisoformat(plan['renewal_date']) - date.today()).days
                if days_left >= 0:
                    ui.label(f"Renews on {plan['renewal_date']}  ({days_left} days left)").classes(TEXT)
                else:
                    ui.label(f"Ran out on {plan['renewal_date']}  ({-days_left} days ago)").classes('text-red-400')
            else:
                ui.label('No renewal date set.').classes(MUTED)


# =====================================================================
#  TRAINER  (details + chat)
# =====================================================================

def show_trainer(user, go_back):
    top_bar('TRAINER', go_back)
    uid = user['id']

    info = forge_db.get_assignment(uid)
    if not info.get('trainer_id'):
        with ui.card().classes(CARD):
            ui.label('No trainer has been assigned to you yet. Please ask the admin.').classes(MUTED)
        return                      # nothing more to show, so stop here

    trainer_id = info['trainer_id']

    # ---- who, where and when ----
    with ui.card().classes(CARD):
        ui.label(f"Your trainer: {info['trainer_name']}").classes('text-2xl font-bold text-[#e1dcc9]')
        if info.get('gym_name'):
            ui.label(f"Gym: {info['gym_name']}  {info.get('gym_location') or ''}").classes(TEXT)
        slot = forge_db.get_slot(uid)
        if slot:
            ui.label(f"Your session: {slot['slot_day']}, {slot['start_time']} to {slot['end_time']}").classes(TEXT)
        else:
            ui.label('Your trainer has not picked a session time yet. Ask in the chat below.').classes(MUTED)

    # ---- chat ----
    with ui.card().classes(CARD):
        ui.label('Chat with your trainer').classes(HEADING)
        topic_box = ui.select(TOPIC_NAMES, value='all', label='Show messages about') \
            .props('outlined dense').classes('w-64')
        message_area = ui.scroll_area().classes('w-full border border-[#412d15]').style('height: 320px')

        def show_messages():
            message_area.clear()
            chosen = None
            if topic_box.value != 'all':
                chosen = topic_box.value
            with message_area:
                messages = forge_db.list_messages(uid, trainer_id, chosen)
                if len(messages) == 0:
                    ui.label('No messages yet. Say hello below.').classes(MUTED)
                for m in messages:
                    from_me = (m['sender_id'] == uid)
                    who = 'You' if from_me else info['trainer_name']
                    topic_name = TOPIC_NAMES.get(m['topic'], m['topic'])
                    ui.chat_message(m['body'], name=f'{who}  ({topic_name})',
                                    stamp=m['sent_at'], sent=from_me)
            message_area.scroll_to(percent=1.0)

        topic_box.on_value_change(show_messages)

        with ui.row().classes('w-full items-center no-wrap'):
            new_message = ui.input(placeholder='Type a message').props('outlined dense').classes('grow')

            def send():
                text = (new_message.value or '').strip()
                if text == '':
                    return
                topic = 'general'              # sending from the "All" view files it under General
                if topic_box.value != 'all':
                    topic = topic_box.value
                if try_save(forge_db.send_message, uid, trainer_id, uid, topic, text):
                    new_message.value = ''
                    show_messages()

            new_message.on('keydown.enter', send)
            ui.button(icon='send', on_click=send)

        show_messages()
        ui.timer(5, show_messages)             # look for new replies every 5 seconds


# =====================================================================
#  FEEDBACK  (a small pop-up window, goes to the admin)
# =====================================================================

def open_feedback(user):
    with ui.dialog() as window, ui.card().classes(
            'bg-[#1f150c] border border-[#412d15] rounded-sm gap-3').style('width: 420px'):
        ui.label('Send feedback to the admin').classes(HEADING)
        topic_box = ui.select(FEEDBACK_TOPICS, value='General', label='About') \
            .props('outlined dense').classes('w-full')
        message_box = ui.textarea('Your feedback').props('outlined').classes('w-full')

        def send():
            if not (message_box.value or '').strip():
                ui.notify('Please write your feedback first.', type='warning')
                return
            if try_save(forge_db.add_feedback, user['id'], topic_box.value, message_box.value.strip()):
                window.close()
                ui.notify('Feedback sent. Thank you!', type='positive')

        with ui.row().classes('w-full justify-end'):
            ui.button('CANCEL', on_click=window.close).props('flat')
            ui.button('SEND', icon='send', on_click=send)
    window.open()