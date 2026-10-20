from nicegui import ui, app
import hashlib
import uuid
import database


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def render_auth_page():
    # MAIN GRADIENT BACKGROUND
    with ui.column().classes(
            'w-full h-screen items-center justify-center bg-gradient-to-br from-[#000000] via-[#1f150c] to-[#412d15] text-[#e1dcc9]'):

        # Title with custom cream/bronze glow shadow
        title_label = ui.label('').classes(
            'text-7xl font-black tracking-[0.2em] drop-shadow-[0_0_20px_rgba(225,220,201,0.4)] text-[#e1dcc9]'
        )
        tagline_label = ui.label('chisel your body like a sword.').classes(
            'text-xl mt-6 text-[#e1dcc9] font-serif italic tracking-widest opacity-0 transition-opacity duration-1000'
        )

        # Restored BOTH Sign In and Sign Up buttons
        with ui.row().classes('mt-16 opacity-0 transition-opacity duration-1000 gap-8') as buttons_container:
            ui.button('SIGN IN', icon='login', on_click=lambda: signin_dialog.open()).classes(
                'px-8 py-4 bg-[#412d15] text-[#e1dcc9] font-bold rounded-sm hover:bg-[#1f150c] hover:-translate-y-1 border border-[#412d15] hover:shadow-[0_0_15px_rgba(225,220,201,0.3)] transition-all duration-300'
            )
            ui.button('SIGN UP', icon='person_add', on_click=lambda: signup_dialog.open()).classes(
                'px-8 py-4 bg-[#000000] text-[#e1dcc9] font-bold rounded-sm hover:bg-[#1f150c] hover:-translate-y-1 border border-[#412d15] hover:shadow-[0_0_15px_rgba(225,220,201,0.1)] transition-all duration-300'
            )

        # Typewriter Animation
        text_to_type = "THE FORGE"
        state = {'index': 0}

        def type_text():
            if state['index'] < len(text_to_type):
                title_label.text += text_to_type[state['index']]
                state['index'] += 1
            else:
                type_timer.cancel()
                tagline_label.classes(remove='opacity-0', add='opacity-100')
                buttons_container.classes(remove='opacity-0', add='opacity-100')

        type_timer = ui.timer(0.15, type_text)

    # ==========================================
    # DIALOGS
    # ==========================================

    # SIGN IN DIALOG
    with ui.dialog() as signin_dialog, ui.card().classes(
            'w-96 bg-[#1f150c] border border-[#412d15] shadow-[0_20px_50px_rgba(0,0,0,0.8)] p-8'):
        ui.label('ACCESS TERMINAL').classes(
            'text-xl font-black text-[#e1dcc9] tracking-wider mb-6 border-b border-[#412d15] pb-2 w-full text-center')

        login_user = ui.input('Username').classes('w-full mb-4').props('dark outlined rounded color="brown-4"')
        login_pass = ui.input('Password', password=True, password_toggle_button=True).classes('w-full mb-8').props(
            'dark outlined rounded color="brown-4"')

        def handle_login():
            user = database.get_user_by_username(login_user.value)

            if not user:
                ui.notify('User account not found.', type='negative', position='top')
                return
            if user['password'] != hash_password(login_pass.value):
                ui.notify('Incorrect password.', type='negative', position='top')
                return

            new_token = str(uuid.uuid4())
            database.update_user_token(user['id'], new_token)
            app.storage.user['remember_token'] = new_token

            ui.notify('Access Granted', type='positive', position='top', icon='gavel')
            ui.navigate.to('/dashboard')

        ui.button('ENTER THE FORGE', on_click=handle_login).classes(
            'w-full py-3 bg-[#412d15] text-[#e1dcc9] font-bold rounded-sm hover:bg-[#000000]')

    # SIGN UP DIALOG (Restored!)
    with ui.dialog() as signup_dialog, ui.card().classes(
            'w-96 bg-[#1f150c] border border-[#412d15] shadow-[0_20px_50px_rgba(0,0,0,0.8)] p-8'):
        ui.label('NEW RECRUIT').classes(
            'text-xl font-black text-[#e1dcc9] tracking-wider mb-6 border-b border-[#412d15] pb-2 w-full text-center')

        reg_user = ui.input('Username').classes('w-full mb-4').props('dark outlined rounded color="brown-4"')
        reg_pass = ui.input('Password', password=True).classes('w-full mb-4').props(
            'dark outlined rounded color="brown-4"')
        reg_role = ui.select(['user', 'employee'], value='user', label='Role').classes('w-full mb-8').props(
            'dark outlined rounded color="brown-4"')

        def handle_signup():
            if not reg_user.value or not reg_pass.value:
                ui.notify('Please fill all fields', type='warning')
                return

            success = database.create_user(reg_user.value, hash_password(reg_pass.value), reg_role.value)

            if success:
                ui.notify('Account created! Proceed to sign in.', type='positive', position='top')
                signup_dialog.close()
            else:
                ui.notify('Username already exists.', type='negative', position='top')

        ui.button('REGISTER', on_click=handle_signup).classes(
            'w-full py-3 bg-[#000000] text-[#e1dcc9] font-bold rounded-sm border border-[#412d15] hover:bg-[#412d15]')