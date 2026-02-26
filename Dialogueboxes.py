# imports
import tkinter
from tkinter import ttk, messagebox, filedialog
import constants as C


class DialogueBox:
    def __init__(self, root, main_app, title):
        self.root = root
        self.main_app = main_app  # access the main app instance
        self.title = title
        self.dialog = tkinter.Toplevel(self.root)

    def FilterDialog(self, selected_table):
        main_frame = ttk.Frame(self.dialog)
        main_frame.grid(row=0, column=0, sticky="nsew")
        # The main frame will expand to fill the dialog
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        self.dialog.title('Filters')

        # Scrollable area
        self.dialog.geometry("397x310")
        self.dialog.resizable(False, False)
        canvas = tkinter.Canvas(main_frame)  # for scrolling
        scrollbar = ttk.Scrollbar(
            main_frame, orient="vertical", command=canvas.yview)  # Add the vertical scrollbar
        scroll_frame = ttk.Frame(canvas)

        # actually make it scrollable
        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        # to anchor the frame to the top left of the canvas
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        # link scrollbar to canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        # Grid the canvas and scrollbar
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # For canvas scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # Enable scrolling only when mouse is over the canvas
        canvas.bind("<Enter>", lambda e: canvas.bind_all(
            "<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Sync background colour with theme
        bg_color = self.main_app.style.lookup("TFrame", "background")
        if not bg_color or bg_color in ("", "SystemButtonFace"):
            # fallback for some themes/platforms
            bg_color = self.main_app.style.lookup("TLabel", "background")
        if not bg_color or bg_color in ("", "SystemButtonFace"):
            bg_color = "#f0f0f0"  # fallback to default Tkinter background
        # Set the canvas background
        canvas.configure(background=bg_color)

        result = {}  # final result dictionary
        selected_filters = {}  # selected filters for the current table
        # to pre-fill with applied filters
        applied_filters = self.main_app.selected_filters if isinstance(
            self.main_app.selected_filters, dict) else {}
        resultvalues = {}  # to hold StringVar for each filter

        # Determine filters based on selected table but only include filters
        # whose configured column actually exists for the selected table.
        table_columns = {
            'aircraft': C.aircraft_columns,
            'airports': C.airports_columns,
            'routes': C.routes_columns,
            'flights': C.flights_columns,
            'maintenance': C.maintenance_columns,
            'accounts': C.accounts_columns
        }
        for i in C.filterslist.keys():
            if C.filterslist[i]['table'] != selected_table:
                continue
            col = C.filterslist[i]['column']
            if col not in table_columns.get(selected_table, []):
                # skip filters that reference columns not present in the table
                continue
            selected_filters[i] = [C.filterslist[i]['column'],
                                   C.filterslist[i]['type'], C.filterslist[i]['title']]

        selected_columns = []  # to group filters by column
        previous = None  # to track previous column, to avoid duplicates
        for i in selected_filters.values():
            if i[0] != previous:
                selected_columns.append(i[0])
                previous = i[0]

        # for canvas scrolling
        def bind_mousewheel(widget, canvas):
            widget.bind("<Enter>", lambda e: canvas.bind_all(
                "<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units")))
            widget.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        count = 0  # row count
        for i in selected_columns:
            for j in selected_filters:
                if selected_filters[j][0] == i:
                    var = tkinter.StringVar(scroll_frame)
                    # Fill values of applied filters (safely)
                    if applied_filters and j in applied_filters:
                        var.set(applied_filters[j])
                    resultvalues[j] = var
                    filterlabel = ttk.Label(
                        scroll_frame, text=selected_filters[j][2])
                    filterlabel.grid(row=count, column=0,
                                     sticky="ew", padx=5, pady=5)
                    # for scrolling on top of labels
                    bind_mousewheel(filterlabel, canvas)
                    if selected_filters[j][1] == 'text':
                        # entry
                        text = ttk.Entry(scroll_frame, textvariable=var)
                        text.grid(row=count, column=1,
                                  sticky="ew", padx=5, pady=5)
                        # for scrolling on top of entry
                        bind_mousewheel(text, canvas)
                    elif selected_filters[j][1] == 'num':
                        number = ttk.Entry(scroll_frame, textvariable=var)
                        number.grid(row=count, column=1,
                                    sticky="ew", padx=5, pady=5)
                        # for scrolling on top of entry
                        bind_mousewheel(number, canvas)
                    elif selected_filters[j][1] == 'spin':
                        # ranges are stored in filterslist under 'range'
                        r = C.filterslist[j].get('range') or (0, 100)
                        r1, r2 = r

                        spin = ttk.Spinbox(
                            scroll_frame, from_=r1, to=r2, textvariable=var)
                        spin.grid(row=count, column=1,
                                  sticky="ew", padx=5, pady=5)
                        # for scrolling on top of entry
                        bind_mousewheel(spin, canvas)
                    elif selected_filters[j][1] == 'dropdown':
                        # combobox
                        # list of options for dropdown
                        options = C.filterslist[j].get('options')
                        dropdown = ttk.Combobox(
                            scroll_frame, values=options, state='readonly', textvariable=var)
                        dropdown.grid(row=count, column=1,
                                      sticky="ew", padx=5, pady=5)
                        # for scrolling on top of entry
                        bind_mousewheel(dropdown, canvas)
                    elif selected_filters[j][1] == 'date':
                        # date entry (YYYY-MM-DD)
                        date = ttk.Entry(scroll_frame, textvariable=var)
                        date.grid(row=count, column=1,
                                  sticky="ew", padx=5, pady=5)
                        # for scrolling on top of entry
                        bind_mousewheel(date, canvas)
                    count += 1

        def submit():
            for i in resultvalues.keys():
                # get the value from StringVar
                result[i] = resultvalues[i].get()
            try:
                self.dialog.destroy()
            except Exception:
                pass

        def clear():
            # Return an empty dict to indicate filters cleared
            nonlocal result
            result = {}
            try:
                self.dialog.destroy()
            except Exception:
                pass

        # Submit and Clear buttons section
        Buttonframe = ttk.Frame(main_frame)
        Buttonframe.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        OKbutton = ttk.Button(
            Buttonframe, text='Apply Selected Filters', command=submit)
        OKbutton.pack(pady=1, side='left')
        Clearbutton = ttk.Button(
            Buttonframe, text='Clear filters', command=clear)
        Clearbutton.pack(pady=1, side='left')
        self.dialog.wait_window()
        if result is None or result == {}:
            # No filters or cleared filters -> return empty dict for caller to set
            return {}
        return result
        # Create tab for each column
        # in each column, for each filter, add the corresponding label and input
        # selected_filters: {'filter':[column,name,title]}
        # selected_columns: {selected_filters['filter'][0]}

    def add_record_dialog(self):
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True)
        if not self.main_app.editmode.get():
            messagebox.showinfo(parent=self.root, title="View mode",
                                message="You are in View mode.\nPlease switch to edit mode to add records.")
            self.dialog.destroy()
            return
        self.result = None
        entries = []
        self.dialog.title('Add Record')
        selected_table = self.main_app.selected_table
        if selected_table == "aircraft":
            titles = C.titles[0]
        elif selected_table == "airports":
            titles = C.titles[1]
        elif selected_table == "routes":
            titles = C.titles[2]
        elif selected_table == "flights":
            titles = C.titles[3]
        elif selected_table == "maintenance":
            titles = C.titles[4]
        else:
            messagebox.showwarning("No Table Selected",
                                   "Please view a table first.")
            return
        for row, (i, j) in enumerate(zip(titles, C.dtypes[selected_table])):
            label = ttk.Label(main_frame, text=i)
            if j[0] == 'entry':
                entry = ttk.Entry(main_frame)
            elif j[0] == 'spinbox':
                r1, r2 = j[1]
                entry = ttk.Spinbox(main_frame, from_=r1, to=r2)
            elif j[0] == 'combobox':
                options = j[1]
                entry = ttk.Combobox(
                    main_frame, values=options, state='readonly')
            else:
                return
            label.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
            entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
            entries.append(entry)

        def submit():
            self.result = [entry.get() for entry in entries]
            if all(i.strip() == "" for i in self.result):  # all fields empty
                messagebox.showwarning(
                    "Empty Input", "Please enter at least one value.")
                return
            self.dialog.destroy()

        def clear():
            for i in entries:
                if isinstance(i, ttk.Combobox):
                    i.set("")
                else:
                    i.delete(0, "end")
        Buttonframe = ttk.Frame(main_frame)
        Buttonframe.grid(row=len(entries), column=0,
                         sticky="ew", padx=5, pady=5)
        OKbutton = ttk.Button(
            Buttonframe, text='Add row to table', command=submit)
        OKbutton.pack(pady=1, side='left')
        Clearbutton = ttk.Button(
            Buttonframe, text='Clear fields', command=clear)
        Clearbutton.pack(pady=1, side='left')
        self.dialog.protocol("WM_DELETE_WINDOW", lambda: (
            setattr(self, "result", None), self.dialog.destroy()))
        self.dialog.wait_window()   # pauses until dialog is closed
        if not self.result:
            return None
        return self.result


    def SettingsDialog(self, settingslist):
        # Similar to the other input dialogs
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True)
        self.dialog.title('Settings')
        tabs = ttk.Notebook(main_frame)  # tabbed view
        tabs.pack(expand=True, fill='both')
        settingstabs = ['App', 'Database']
        settings_result = {}
        for i in settingstabs:
            frame = ttk.Frame(tabs)
            tabs.add(frame, text=i)
            # for the file picker dialog

            def file_picker(defaultsaveinput, frame):
                folder_path = filedialog.askdirectory(
                    title="Select a Folder", parent=frame, initialdir=defaultsaveinput.get())
                if folder_path:
                    defaultsaveinput.insert(0, folder_path)
            if i == 'App':
                Themelabel = ttk.Label(frame, text='Theme:')
                Themelabel.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
                app_theme_input = ttk.Combobox(
                    frame, values=C.get_supported_themes(), state='readonly')
                app_theme_input.set(settingslist['app_theme'])
                app_theme_input.grid(
                    row=0, column=1, sticky="ew", padx=5, pady=5)
                Saverlabel = ttk.Label(
                    frame, text='Save files by default to this location:')
                Saverlabel.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
                defaultsaveinput = ttk.Entry(frame)
                defaultsaveinput.insert(0, settingslist['defaultsave'])
                defaultsaveinput.grid(
                    row=1, column=1, sticky="ew", padx=5, pady=5)
                SaveButton = ttk.Button(
                    frame, text='Browse...', command=lambda: file_picker(defaultsaveinput, frame))
                SaveButton.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
            elif i == 'Database':
                Userlabel = ttk.Label(frame, text='Username:')
                Userlabel.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
                usernameinput = ttk.Entry(frame)
                usernameinput.insert(0, settingslist['user_db'])
                usernameinput.grid(
                    row=1, column=1, sticky="ew", padx=5, pady=5)
                hostlabel = ttk.Label(frame, text='Host:')
                hostlabel.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
                hostinput = ttk.Entry(frame)
                hostinput.insert(-1, settingslist['host'])
                hostinput.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
                passlabel = ttk.Label(frame, text='Password:')
                passlabel.grid(row=3, column=0, sticky="ew", padx=5, pady=5)
                passwordinput = ttk.Entry(frame, show="*")
                passwordinput.grid(
                    row=3, column=1, sticky="ew", padx=5, pady=5)
                passwordinput.insert(-1, settingslist['passwd_db'])
                charlabel = ttk.Label(frame, text='Character set:')
                charlabel.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
                charsetinput = ttk.Combobox(
                    frame, values=C.supported_character_sets, state='normal')
                charsetinput.set(settingslist['charset'])
                charsetinput.grid(row=4, column=1, sticky="ew", padx=5, pady=5)

        def submit():
            settings_result.update({'user': settingslist['user'], 'pass': settingslist['pass'], 'user_db': usernameinput.get(), 'host': hostinput.get(), 'passwd_db': passwordinput.get(
            ), 'charset': charsetinput.get(), 'defaultsave': defaultsaveinput.get(), 'app_theme': app_theme_input.get(), 'database': C.database})
            self.dialog.destroy()

        def set_default_values(usernameinput, hostinput, passwordinput, defaultsaveinput, app_theme_input, charsetinput):
            self.settings_result = C.defaultsettingslist
            usernameinput.delete(0, "end")
            usernameinput.insert(0, C.defaultsettingslist['user'])
            hostinput.delete(0, "end")
            hostinput.insert(0, C.defaultsettingslist['host'])
            passwordinput.delete(0, "end")
            passwordinput.insert(0, C.defaultsettingslist['pass'])
            defaultsaveinput.delete(0, "end")
            defaultsaveinput.insert(0, C.defaultsettingslist['defaultsave'])
            app_theme_input.set(C.defaultsettingslist['app_theme'])
            charsetinput.set(C.defaultsettingslist['charset'])

        Buttonframe = ttk.Frame(main_frame)
        Buttonframe.pack(expand=True)
        OKbutton = ttk.Button(Buttonframe, text='Apply', command=submit)
        OKbutton.pack(pady=1, side='left')
        Clearbutton = ttk.Button(Buttonframe, text='Reset to default', command=lambda: set_default_values(
            usernameinput, hostinput, passwordinput, defaultsaveinput, app_theme_input, charsetinput))
        Clearbutton.pack(pady=1, side='left')

        def cancel():
            self.dialog.destroy()

        self.dialog.protocol("WM_DELETE_WINDOW", cancel)
        self.dialog.wait_window()
        return settings_result if settings_result else None

    def create_session_dialog(self):
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True)
        self.dialog.title('Login')
        username_label = ttk.Label(main_frame, text="Username:")
        username_label.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        username_entry = ttk.Entry(main_frame)
        username_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        password_label = ttk.Label(main_frame, text="Password:")
        password_label.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        password_entry = ttk.Entry(main_frame, show="*")
        password_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        def submit():
            username = username_entry.get()
            password = password_entry.get()
            user = self.main_app.db.login_user(username, password)
            if user:
                self.main_app.signed_in = True
                self.main_app.session = user  # Assign session/user object
                messagebox.showinfo(
                    title="Login Successful", message=f"Welcome, {username}!")
                self.dialog.destroy()
                for i in range(self.main_app.menubar.menubar.index("end")+1, -1, -1):
                    self.main_app.menubar.menubar.delete(i)
                self.main_app.menubar.menu()

            else:
                messagebox.showerror(parent=self.dialog, title="Login Failed",
                                     message="Invalid username or password, or account is suspended.")

        def set_default_values(username_entry, password_entry):
            username_entry.delete(0, "end")
            username_entry.insert(0, C.defaultsettingslist['user'])
            password_entry.delete(0, "end")
            password_entry.insert(0, C.defaultsettingslist['passwd'])

        Buttonframe = ttk.Frame(main_frame)
        Buttonframe.grid(row=2, column=0, columnspan=2,
                         sticky="ew", padx=5, pady=5)
        OKbutton = ttk.Button(Buttonframe, text='Log In', command=submit)
        OKbutton.pack(pady=1, side='left')
        Clearbutton = ttk.Button(Buttonframe, text='Clear', command=lambda: set_default_values(
            username_entry, password_entry))
        Clearbutton.pack(pady=1, side='left')

    def register_dialog(self):
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True)
        self.dialog.title("Register New Account")
        self.result = None

        # Fields: Username, Password, Confirm Password, Role
        ttk.Label(main_frame, text="Username:").grid(
            row=0, column=0, padx=5, pady=5, sticky="ew")
        username_entry = ttk.Entry(main_frame)
        username_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Password:").grid(
            row=1, column=0, padx=5, pady=5, sticky="ew")
        password_entry = ttk.Entry(main_frame, show="*")
        password_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Confirm Password:").grid(
            row=2, column=0, padx=5, pady=5, sticky="ew")
        confirm_entry = ttk.Entry(main_frame, show="*")
        confirm_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Role:").grid(
            row=3, column=0, padx=5, pady=5, sticky="ew")
        role_input = ttk.Combobox(main_frame, values=(
            "ADMIN", "STAFF", "GUEST"), state="readonly")
        role_input.current(2)  # Default to Guest
        role_input.grid(row=3, column=1, padx=5, pady=5)

        def submit():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            confirm = confirm_entry.get().strip()
            role = role_input.get()

            if not username or not password:
                messagebox.showerror(
                    parent=self.dialog, title="Error", message="Username and password cannot be empty.")
                return
            if password != confirm:
                messagebox.showerror(
                    parent=self.dialog, title="Error", message="Passwords do not match.")
                return
            try:
                self.main_app.db.register_user(username, password, role)
                user = self.main_app.db.login_user(username, password)
                self.main_app.signed_in = True
                self.main_app.session = user  # Auto-login after registration
                messagebox.showinfo(parent=self.dialog, title="Success",
                                    message=f"User {username} registered successfully.\nYou are now logged in.")
                self.dialog.destroy()
                # Clear and rebuild menubar
                for i in range(self.main_app.menubar.menubar.index("end")+1, -1, -1):
                    self.main_app.menubar.menubar.delete(i)
                self.main_app.menubar.menu()
            except Exception as e:
                messagebox.showerror(
                    parent=self.dialog, title="Error", message=f"Could not register user: {e}")

        ttk.Button(main_frame, text="Register", command=submit).grid(
            row=4, column=0, pady=10)
        ttk.Button(main_frame, text="Cancel", command=self.dialog.destroy).grid(
            row=4, column=1, pady=10)

        self.dialog.wait_window()

    def admin_panel(self, users_tree):
        self.dialog.title('Admin Panel')
        users = self.main_app.db.fetch_data('accounts', [], [])
        users_tree.load_table('accounts', users)
        # Ensure the frame is packed
        users_tree.frame.pack(expand=True, fill='both')

    def profile_dialog(self):
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True)
        self.dialog.title('Profile')
        accounts_columns = C.accounts_titles
        # Display user profile information
        session = self.main_app.session
        if session:
            values = session.get_profile().values()
            for title, value in zip(accounts_columns, values):
                label = ttk.Label(main_frame, text=f"{title}: {value}")
                label.pack(anchor="w", padx=20, pady=2)

    def client_setup_dialog(self):
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True)
        self.dialog.title('Setup')
        setup_label = ttk.Label(
            main_frame, text="Initial Setup", font=("Arial", 16, "bold"))
        setup_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)

        # fields: Database info for MySQL

        ttk.Label(main_frame, text="Database Username*").grid(
            row=4, column=0, padx=5, pady=5, sticky="ew")
        db_username_entry = ttk.Entry(main_frame)
        db_username_entry.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Host*").grid(
            row=5, column=0, padx=5, pady=5, sticky="ew")
        host_entry = ttk.Entry(main_frame)
        host_entry.grid(row=5, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Database password*").grid(
            row=6, column=0, padx=5, pady=5, sticky="ew")
        db_pass_entry = ttk.Entry(main_frame, show="*")
        db_pass_entry.grid(row=6, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Character Set").grid(
            row=7, column=0, padx=5, pady=5, sticky="ew")
        charset_input = ttk.Combobox(
            main_frame, values=C.supported_character_sets, state="readonly")
        charset_input.set(C.defaultsettingslist['charset'])
        charset_input.grid(row=7, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="* Required fields", font=("Arial", 8)).grid(
            row=9, column=0, columnspan=2, padx=0, pady=5)

        def on_close():
            if messagebox.askokcancel("Quit", "Setup is not complete. Are you sure you want to quit?"):
                self.dialog.destroy()

        # Bind the close button to on_close function to prevent closing without setup
        self.dialog.protocol("WM_DELETE_WINDOW", on_close)

        def submit():
            # Get and strip whitespace
            db_username = db_username_entry.get().strip()
            db_password = db_pass_entry.get().strip()
            host = host_entry.get().strip()
            charset = charset_input.get().strip()
            if not host or not db_password or not db_username:
                messagebox.showerror(
                    parent=self.dialog, title="Error", message="All fields are required.")
                return
            self.result = {'user_db': db_username, 'host': host, 'charset': charset,
                           'passwd_db': db_password, 'database': C.database}
            self.dialog.destroy()

        ttk.Button(main_frame, text="Next", command=submit).grid(
            row=10, column=0, pady=10, sticky="ew")

        self.dialog.wait_window()
        # return None if not hasattr(self, "result") else self.result
        return getattr(self, "result", None)

    def app_setup_dialog(self):
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True)
        self.dialog.title('Setup')
        setup_label = ttk.Label(main_frame, text="Setup",
                                font=("Arial", 16, "bold"))
        setup_label.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        supported_themes = C.get_supported_themes()

        # fields: Admin Username, Admin Password, Confirm Password, theme selection
        ttk.Label(main_frame, text="Username*").grid(
            row=1, column=0, padx=5, pady=5, sticky="ew")
        username_entry = ttk.Entry(main_frame)
        username_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Password*").grid(
            row=2, column=0, padx=5, pady=5, sticky="ew")
        password_entry = ttk.Entry(main_frame, show="*")
        password_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Confirm Password*").grid(
            row=3, column=0, padx=5, pady=5, sticky="ew")
        confirm_entry = ttk.Entry(main_frame, show="*")
        confirm_entry.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Theme").grid(
            row=8, column=0, padx=5, pady=5, sticky="ew")
        theme_input = ttk.Combobox(
            main_frame, values=supported_themes, state="readonly")
        theme_input.set(C.defaultsettingslist['app_theme'])
        theme_input.grid(row=8, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="* Required fields", font=("Arial", 8)).grid(
            row=9, column=0, columnspan=2, padx=0, pady=5)

        def on_close():
            if messagebox.askokcancel("Quit", "Setup is not complete. Are you sure you want to quit?"):
                self.dialog.destroy()

        # Bind the close button to on_close function to prevent closing without setup
        self.dialog.protocol("WM_DELETE_WINDOW", on_close)

        def submit():
            # Get and strip whitespace
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            confirm = confirm_entry.get().strip()
            theme = theme_input.get().strip()
            if not username or not password:
                messagebox.showerror(
                    parent=self.dialog, title="Error", message="All fields are required.")
                return
            if password != confirm:
                messagebox.showerror(
                    parent=self.dialog, title="Error", message="Passwords do not match. Try again.")
                return
            self.result = {'user': username, 'pass': password,
                           'defaultsave': C.defaultsave, 'app_theme': theme, 'database': C.database}
            # Close the dialog so wait_window() returns and caller receives the result
            try:
                self.dialog.destroy()
            except Exception:   
                pass

        ttk.Button(main_frame, text="Finish Setup", command=submit).grid(
            row=10, column=0, pady=10, sticky="ew")

        self.dialog.wait_window()
        # return None if not hasattr(self, "result") else self.result
        return getattr(self, "result", None)

    def HelpDialog(self):
        self.dialog.title('Help')
