import os

from dotenv import load_dotenv
from nicegui import ui, app
from fastapi.responses import RedirectResponse

load_dotenv()

import database
import auth
import forge_db
import user_screens

database.init_db()
forge_db.init_schema()  # creates the new tables the first time (safe to run every time)


@ui.page('/')
def login_route():
    """The default page that loads the authentication UI."""
    # 1. Check auto-login BEFORE rendering the page
    token = app.storage.user.get('remember_token')
    if token:
        user = database.get_user_by_token(token)
        if user:
            return RedirectResponse('/dashboard')

    # 2. If no token, render the login page normally
    auth.render_auth_page()


@ui.page('/dashboard')
def dashboard_route():
    """The dashboard router."""

    # 1. Security Check: Kick user back to login if no token
    token = app.storage.user.get('remember_token')
    if not token:
        return RedirectResponse('/')

    user = database.get_user_by_token(token)
    if not user:
        app.storage.user['remember_token'] = None
        return RedirectResponse('/')

    def logout():
        database.clear_user_token(user['id'])
        app.storage.user['remember_token'] = None
        ui.navigate.to('/')  # This works here because it is triggered by a button click!

    ui.colors(primary='#b08d57')   # normal buttons become bronze instead of blue

    # APP LAYOUT - Top Bar (Black background, Bronze bottom border)
    with ui.header().classes('bg-[#000000] border-b border-[#412d15] p-4 flex justify-between items-center'):
        with ui.row().classes('items-center gap-4'):
            ui.icon('fitness_center', size='sm').classes('text-[#412d15]')
            ui.label('THE FORGE').classes('text-xl font-black tracking-widest text-[#e1dcc9]')

        with ui.row().classes('items-center gap-4'):
            ui.label(f"User: {user['username'].upper()}").classes(
                'text-[#e1dcc9] font-bold tracking-wide text-sm opacity-80')
            ui.button('LOGOUT', icon='logout', on_click=logout).classes(
                'bg-[#412d15] text-[#e1dcc9] px-4 py-1 rounded-sm text-xs hover:bg-[#1f150c]')

    # MAIN CONTENT AREA (Gradient matching the auth page)
    with ui.column().classes(
            'w-full h-full min-h-screen bg-gradient-to-br from-[#1f150c] via-[#000000] to-[#1f150c] text-[#e1dcc9] p-12'):

        # Greeting Header
        with ui.row().classes('w-full items-end justify-between border-b border-[#412d15] pb-4 mb-8'):
            ui.label('DASHBOARD').classes('text-4xl font-black text-[#e1dcc9] tracking-widest')
            ui.label(f"Clearance Level: {user['role'].upper()}").classes(
                f"text-sm font-bold px-3 py-1 rounded-sm uppercase tracking-wider bg-[#412d15] text-[#e1dcc9]"
            )

        # Role-Specific Content Area (Dark Brown cards with Bronze borders)
        with ui.card().classes('w-full max-w-4xl bg-[#1f150c] border border-[#412d15] shadow-xl p-8 rounded-sm'):

            if user['role'] == 'admin':
                ui.icon('admin_panel_settings', size='lg').classes('mb-4 text-[#e1dcc9]')
                ui.label('SYSTEM ADMINISTRATION').classes('text-2xl font-bold text-[#e1dcc9] mb-2')
                ui.label(
                    'Welcome to the command center. From here, you can manage user profiles, override employee schedules, and view gym analytics.').classes(
                    'text-[#e1dcc9] opacity-70')

            elif user['role'] == 'employee':
                ui.icon('assignment', size='lg').classes('mb-4 text-[#e1dcc9]')
                ui.label('STAFF PORTAL').classes('text-2xl font-bold text-[#e1dcc9] mb-2')
                ui.label(
                    'View your upcoming shift schedule, manage floor duties, and review member training programs.').classes(
                    'text-[#e1dcc9] opacity-70')




            else:

                # "area" is an empty box. It holds either the pentagon OR the screen that is open.
                # To change what the person sees, we clear the box and fill it again.
                area = ui.column().classes('w-full items-center')

                # The look of the five round buttons (same for all, so we write it once)
                NODE_STYLE = (
                    'w-36 h-36 rounded-full bg-[#3b2a20] text-[#f5efe6] hover:bg-[#2a1d15] '
                    'border-2 border-[#b08d57] shadow-[0_0_15px_rgba(176,141,87,0.2)] '
                    'flex flex-col items-center justify-center font-bold tracking-wider '
                    'transition-all hover:scale-105'
                )

                # Each button: (name, icon, left, top, tooltip text)
                # left / top are pixel positions inside the 500 x 470 box that holds the pentagon.
                nodes = [
                    ('DIET', 'restaurant', 178, 3,
                     'Log meals with calories, protein, carbs and fats.'),
                    ('POWER LIFTS', 'fitness_center', 344, 124,
                     'Log sets by split, exercise, reps and weight.'),
                    ('ATHLETICS', 'directions_run', 281, 320,
                     'Log cardio and sport sessions with duration, distance and notes.'),
                    ('MEMBERSHIP', 'card_membership', 75, 320,
                     'Plan, status, price, renewal date with a days-remaining count.'),
                    ('TRAINER', 'forum', 12, 124,
                     'Shows the assigned trainer, gym and agreed session time, and your chat.'),
                ]

                # Which function opens which screen:  name on the button -> function
                # (the functions live in user_screens.py)
                screens = {
                    'DIET': user_screens.show_diet,
                    'POWER LIFTS': user_screens.show_powerlifts,
                    'ATHLETICS': user_screens.show_athletics,
                    'MEMBERSHIP': user_screens.show_membership,
                    'TRAINER': user_screens.show_trainer,
                }

                # The pentagon outline and the dotted lines going to the centre.
                pentagon_drawing = '''
                <svg width="500" height="470" style="position:absolute; left:0; top:0; pointer-events:none;">
                    <polygon points="250,75 416,196 353,392 147,392 84,196"
                             fill="rgba(176,141,87,0.07)" stroke="#b08d57"
                             stroke-width="2" stroke-opacity="0.55"/>
                    <line x1="250" y1="250" x2="250" y2="75"  stroke="#b08d57" stroke-opacity="0.3" stroke-dasharray="4 6"/>
                    <line x1="250" y1="250" x2="416" y2="196" stroke="#b08d57" stroke-opacity="0.3" stroke-dasharray="4 6"/>
                    <line x1="250" y1="250" x2="353" y2="392" stroke="#b08d57" stroke-opacity="0.3" stroke-dasharray="4 6"/>
                    <line x1="250" y1="250" x2="147" y2="392" stroke="#b08d57" stroke-opacity="0.3" stroke-dasharray="4 6"/>
                    <line x1="250" y1="250" x2="84"  y2="196" stroke="#b08d57" stroke-opacity="0.3" stroke-dasharray="4 6"/>
                </svg>
                '''

                def open_screen(name):
                    """Called when a pentagon button is clicked: swap the pentagon for that screen."""
                    area.clear()
                    with area:
                        screens[name](user, show_hub)     # show_hub is passed so the back arrow works

                def show_hub():
                    """Draw the pentagon (this is also what the back arrow brings back)."""
                    area.clear()
                    with area:
                        ui.label('TRAINING HUB').classes(
                            'text-2xl font-black text-[#f5efe6] mb-8 text-center tracking-widest w-full border-b border-[#4a3528] pb-4'
                        )

                        with ui.element('div').style('position: relative; width: 500px; height: 470px;'):

                            # 1. Draw the pentagon first so it stays behind the buttons.
                            # (Newer NiceGUI versions need sanitize=False, older ones do not know it,
                            #  so we try the new way first and fall back to the old way.)
                            try:
                                ui.html(pentagon_drawing, sanitize=False)
                            except TypeError:
                                ui.html(pentagon_drawing)

                            # 2. The bronze circle in the middle (just for decoration).
                            with ui.element('div').classes(
                                    'rounded-full bg-[#b08d57] flex items-center justify-center'
                            ).style('position: absolute; left: 200px; top: 200px; width: 100px; height: 100px;'):
                                ui.icon('local_fire_department', size='lg').classes('text-[#1e140e]')

                            # 3. The five buttons. The loop makes one button for each item in "nodes".
                            #    color=None lets our own brown colour show.
                            #    'stack' puts the icon above the name.
                            #    on_click=lambda n=name: ...  means "when clicked, open the screen for THIS name".
                            #    (n=name is needed so each button remembers its own name.)
                            for name, icon, left, top, tip in nodes:
                                ui.button(name, icon=icon, color=None,
                                          on_click=lambda n=name: open_screen(n)).props('stack').classes(NODE_STYLE).style(
                                    f'position: absolute; left: {left}px; top: {top}px;'
                                ).tooltip(tip)

                        # Feedback button opens a small pop-up window
                        with ui.row().classes('w-full justify-center mt-12'):
                            ui.button('SUBMIT FEEDBACK', icon='feedback', color=None,
                                      on_click=lambda: user_screens.open_feedback(user)).classes(
                                'px-6 py-2 bg-[#2a1d15] text-[#b9a998] border border-[#4a3528] rounded-md '
                                'hover:bg-[#3b2a20] hover:text-[#f5efe6] transition-colors duration-300'
                            )

                show_hub()    # when the dashboard first opens, show the pentagon

if __name__ in {"__main__", "__mp_main__"}:
    storage_secret = os.getenv("APP_STORAGE_SECRET")
    if not storage_secret:
        raise RuntimeError("Set APP_STORAGE_SECRET in the environment or .env file.")
    ui.run(
        title="THE FORGE",
        storage_secret=storage_secret,
        native=False,
        reload=False,
        dark=True
    )