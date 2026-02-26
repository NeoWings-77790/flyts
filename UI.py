# imports
import tkinter
from tkinter import ttk, messagebox, filedialog
import constants as C
import Tableviewer as TV
import Dialogueboxes as dbox


class Flyts:
    def __init__(self, root, db, user=None, passwd=None):

        self.root = root  # window root
        self.db = db  # database object
        self.root.title('Flyts')
        self.root.geometry('1300x500')
        self.root.minsize(200, 200)
        self.selected_table = None  # currently selected table
        self.selected_rows = []  # used for editing
        self.selected_filters = {}  # currently applied filters
        self.menubar = MenuBar(self.root, self)  # menu bar object
        self.tree = TV.TreeViewer(self.root, self)  # treeview object
        self.editmode = tkinter.BooleanVar(value=False)  # edit mode variable

        if user is None or passwd is None:
            self.session = None
            self.signed_in = False
        else:
            self.session = self.db.login_user(user, passwd)
            self.signed_in = self.session is not None
        self.style = ttk.Style()

        # set theme on startup
        self.styleset()

        # menu initialization
        self.menubar.menu()

    def importer(self):
        from csvlogic import CSVmanager
        file_path = filedialog.askopenfilename(title="Select a file to import", filetypes=(
            # open file dialog
            ("Comma Separated Values", "*.csv"), ("All files", "*.*")))

        if not file_path:
            return

        csvmgr = CSVmanager(',')  # usually comma delimiter
        rows = csvmgr.loadcsv(file_path)
        for i in rows[0][1:]:
            self.db.insert_row(rows[1], i)  # insert each row into database
        # if currently viewing the same table, refresh
        if self.selected_table == rows[1]:
            self.menubar.show_table(rows[1])
        messagebox.showinfo("Export Complete", f"Imported from {file_path}")

    def exporter(self):
        from csvlogic import CSVmanager
        if not self.selected_table:
            messagebox.showinfo("No Table Selected",
                                "Please select a table first.")
            return
        director = C.load_settings()['defaultsave']
        folder_path = filedialog.askdirectory(
            title="Select a Folder", initialdir=director)
        if not folder_path:
            return

        rows = self.db.fetch_data(self.selected_table, [], [])
        if self.selected_table == "aircraft":
            columns = C.aircraft_columns
        elif self.selected_table == "airports":
            columns = C.airports_columns
        elif self.selected_table == "routes":
            columns = C.routes_columns
        elif self.selected_table == "flights":
            columns = C.flights_columns
        elif self.selected_table == "maintenance":
            columns = C.maintenance_columns

        csvmgr = CSVmanager(C.defdelimiter)
        csvmgr.savecsv(folder_path+'/'+self.selected_table +
                       '.csv', rows, columns)  # save CSV file
        messagebox.showinfo("Export Complete",
                            f"Exported {self.selected_table} to {folder_path}")

    def styleset(self):  # set theme from settings
        settings = C.load_settings()
        self.style.theme_use(settings['app_theme'])


class MenuBar:
    def __init__(self, root, main_app):
        self.menubar = tkinter.Menu(root)
        root.config(menu=self.menubar)
        self.main_app = main_app
        self.menubar.focus_set()

    def open_settings_dialog(self):  # open settings dialog menu action
        dialog = dbox.DialogueBox(
            self.main_app.root, self.main_app, "Settings")
        settings = dialog.SettingsDialog(C.load_settings())
        if settings:
            C.save_settings(settings)
            self.main_app.styleset()

    def filemenu(self):  # define file menu buttons and actions
        FileMenu = tkinter.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=FileMenu)
        FileMenu.add_command(
            label='Settings', command=self.open_settings_dialog)
        if self.main_app.session is None or not (self.main_app.session.is_admin() or self.main_app.session.is_staff()):
            return
        FileMenu.add_separator()  # separator
        FileMenu.add_command(label="Import data",
                             command=self.main_app.importer)
        FileMenu.add_command(label="Export data",
                             command=self.main_app.exporter)

    def editmenu(self):  # define edit menu buttons and actions
        EditMenu = tkinter.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Edit", menu=EditMenu)
        if self.main_app.session is None or not (self.main_app.session.is_admin() or self.main_app.session.is_staff()):
            self.menubar.entryconfig("Edit", state="disabled")
            return
        EditMenu.add_checkbutton(
            label="Edit Mode", variable=self.main_app.editmode, onvalue=True, offvalue=False)
        EditMenu.add_separator()
        EditMenu.add_command(label="Add Row", command=self.add_row)
        EditMenu.add_command(label="Delete Row",
                             command=self.main_app.tree.delete_row)

    def add_row(self):  # open add row dialog and insert into database
        dialogue = dbox.DialogueBox(
            self.main_app.root, self.main_app, "Add Record")
        result = dialogue.add_record_dialog()
        if result is None:  # User closed the dialog without action
            return
        else:  # Insert into SQL (or apply filters)
            self.main_app.db.insert_row(self.main_app.selected_table, result)
            self.show_table(self.main_app.selected_table)

    def viewmenu(self):  # define view menu buttons and actions
        ViewMenu = tkinter.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=ViewMenu)
        if self.main_app.session is not None:
            ViewMenu.add_command(
                label="Aircraft", command=lambda: self.show_table("aircraft"))
            ViewMenu.add_command(
                label="Airports", command=lambda: self.show_table("airports"))
            ViewMenu.add_command(
                label="Routes", command=lambda: self.show_table("routes"))
            ViewMenu.add_command(
                label="Flights", command=lambda: self.show_table("flights"))
            ViewMenu.add_command(label="Maintenance",
                                 command=lambda: self.show_table("maintenance"))
            ViewMenu.add_separator()
            ViewMenu.add_command(
                label='Filters', command=self.open_filter_dialog)
        else:
            # if not signed in, disable view menu
            self.menubar.entryconfig("View", state="disabled")

    def show_table(self, table_name):  # load and display table in treeview
        rows = self.main_app.db.fetch_data(table_name, [], [])
        self.main_app.tree.load_table(table_name, rows)
        self.main_app.selected_table = table_name
        self.main_app.selected_filters = {}

    def planningmenu(self):  # define planning menu buttons and actions
        PlanningMenu = tkinter.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Plan", menu=PlanningMenu)
        if self.main_app.session is None or not (self.main_app.session.is_admin() or self.main_app.session.is_staff()):
            self.menubar.entryconfig("Plan", state="disabled")
            return  # only admin/staff can plan flights
        PlanningMenu.add_command(label='Plan Flights',
                                 command=self.plan_flights)
        PlanningMenu.add_command(
            label='Clear All Flights', command=self.clear_flights)

    def plan_flights(self):  # plan flights menu action
        self.main_app.db.plan_flights()  # database function to plan flights
        # refresh flights table if currently viewing, else send to flights table
        self.show_table("flights")

    def clear_flights(self):  # clear all flights menu action
        self.main_app.db.clear_all_flights()  # database function to clear all flights
        # refresh flights table if currently viewing, else send to flights table
        self.show_table("flights")

    def open_filter_dialog(self):  # open filter dialog menu action
        # Use the currently selected table
        filter_values = {}
        table = self.main_app.selected_table
        if not table:  # if no table selected, show warning
            messagebox.showwarning("No Table Selected",
                                   "Please view a table first.")
            return
        dialog = dbox.DialogueBox(self.main_app.root, self.main_app, "Filters")
        filter_values = dialog.FilterDialog(
            table)  # get filter values from dialog
        self.main_app.selected_filters = filter_values
        # Fetch filtered data from the database
        if filter_values != None:  # if user didn't cancel
            if filter_values == 'clear':  # reset filters
                rows = self.main_app.db.fetch_data(table, [], [])
                self.main_app.tree.load_table(table, rows)
            else:  # apply filters
                filterkeys = [i for i in filter_values.keys()
                              # only include non-empty filters for SQL
                              if filter_values[i]]
                filtervalues = [filter_values[i]
                                for i in filterkeys]  # corresponding values
                rows = self.main_app.db.fetch_data(
                    table, filterkeys, filtervalues)  # fetch new data from database
                # load new data into treeview
                self.main_app.tree.load_table(table, rows)

    def usermenu(self):  # define user menu buttons and actions
        UserMenu = tkinter.Menu(self.menubar, tearoff=0)
        if self.main_app.signed_in == False:  # login/register if not signed in
            UserMenu.add_command(label='Login', command=self.login)
        if self.main_app.signed_in:  # if signed in, show user options based on account
            if self.main_app.session.is_admin():  # control panel options for admin
                UserMenu.add_command(label='Register', command=self.register)
                UserMenu.add_command(label='Admin Panel',
                                     command=self.admin_panel)
            # general user options
            UserMenu.add_command(label='Profile', command=self.view_profile)
            UserMenu.add_command(label='Logout', command=self.logout)
        self.menubar.add_cascade(label="User", menu=UserMenu)

    def login(self):  # login menu action
        login_dialog = dbox.DialogueBox(
            self.main_app.root, self.main_app, "Login")
        login_dialog.create_session_dialog()

    def logout(self):  # logout menu action
        confirmation = messagebox.askyesno(
            "Confirm Logout", "Are you sure you want to logout?")
        if confirmation:
            self.main_app.signed_in = False  # set signed in to false
            self.main_app.session = None  # set session to none
            self.main_app.tree.tree.delete(
                *self.main_app.tree.tree.get_children())  # set treeview to empty
            for i in range(self.main_app.menubar.menubar.index("end")+1, -1, -1):  # remove all menus
                self.main_app.menubar.menubar.delete(i)
            self.main_app.menubar.menu()  # reinitialize menus (because user state changed)
            messagebox.showinfo("Logged Out", "You have been logged out.")

    def view_profile(self):  # view profile menu action
        profile_dialog = dbox.DialogueBox(
            self.main_app.root, self.main_app, "Profile")
        profile_dialog.profile_dialog()

    def register(self):  # register menu action
        register_dialog = dbox.DialogueBox(
            self.main_app.root, self.main_app, "Register")
        register_dialog.register_dialog()

    def admin_panel(self):  # admin panel menu action
        admin_dialog = dbox.DialogueBox(
            self.main_app.root, self.main_app, "Admin Panel")
        users_tree = TV.TreeViewer(admin_dialog.dialog, self.main_app)
        admin_dialog.admin_panel(users_tree)

    def menu(self):  # initialize all menus
        self.filemenu()
        self.editmenu()
        self.viewmenu()
        self.planningmenu()
        self.usermenu()
