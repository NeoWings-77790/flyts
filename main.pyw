'''
aircraft_fleet/
            -main.py              # Entry point (starts the tkinter app)
            -databaselogic.py        # Database connection, queries, inserts
            -csvlogic.py       # CSV import/export logic
            -UI.py           # tkinter windows, menus, and event handling
            -Dialogueboxes.py   # Custom dialog boxes for input
            -Tableviewer.py      # Treeview table display and editing
            -constants.py         # Column names, mappings, menu configs
 => Total: 7 files, ~1500 lines of code
'''
# imports
import databaselogic as dbl
import Dialogueboxes as dbox
import constants as C
import UI
import tkinter
from tkinter import messagebox
import sys
import os


def setup():
    global base
    setup_root = tkinter.Tk()  # temporary root for dialog
    setup_root.withdraw()  # Hides the root window, since we only want the dialog
    
    setup_dialog_1 = dbox.DialogueBox(
        setup_root, None, "Client Setup")  # Create dialog box
    # Run setup wizard function of the dialog box for client data
    client_data = setup_dialog_1.client_setup_dialog()

    if not client_data:  # If user cancelled
        setup_root.destroy()  # Close dialog root
        sys.exit()  # Exit program if user cancelled setup
    try:
        base = dbl.database(client_data['host'], client_data['user_db'],
                            # Create database object
                            client_data['passwd_db'], client_data['charset'])
        base.connection()  # Connect to database

    except Exception as e:
        messagebox.showerror(
            parent=setup_root,
            title="Database Connection Error",
            message=f"Could not connect to database.\n\nError: {e}")
        setup_root.destroy()  # Close dialog root
        sys.exit()

    # Check if database exists
    try:
        if not base.is_db():
            base.createtables()  # Create tables if not exists
    
    except Exception as e:
        messagebox.showerror(
            parent=setup_root,
            title="Database Setup Error",
            message=f"Could not create tables.\n\nError: {e}")
        setup_root.destroy()  # Close dialog root
        sys.exit()

    # Run setup wizard function of the dialog box for app data
    setup_dialog_2 = dbox.DialogueBox(
        setup_root, None, "Application Setup")  # Create dialog box
    app_data = setup_dialog_2.app_setup_dialog()
    if not app_data:  # If user cancelled
        setup_root.destroy()  # Close dialog root
        sys.exit()

    # Save settings to file
    settings = {**client_data, **app_data}
    try:
        # Merge dictionaries
        C.save_settings(settings)  # Save settings to file
    except Exception as e:
        messagebox.showerror(
            parent=setup_root,
            title="Settings Save Error",
            message=f"Could not save settings to file.\n\nError: {e}")
        setup_root.destroy()  # Close dialog root
        sys.exit()

    try:
        if not base.accounts_exist():
            # If no accounts exist, create admin account
            base.register_user(app_data.get("user"),
                               app_data.get("pass"), "ADMIN")
        messagebox.showinfo(
        parent=setup_root,
        title="Setup Complete",
        message="Initial configuration successful.\n\nYou can now log in to Flyts.")
    except Exception as e:
        messagebox.showerror(
            parent=setup_root,
            title="Admin Creation Failed",
            message=f"Could not create admin account.\n\nError: {e}")

    
    setup_root.destroy()  # Close dialog root


# Main program starts here
if not C.settings_exist():  # If no settings file exists, run setup
    setup()
else:
    try:
        s = C.load_settings()  # Load settings from file
        # Create database object
        base = dbl.database(s['host'], s['user_db'],
                            s['passwd_db'], s['charset'])
        base.connection()  # Connect to database
        base.cursor.execute("USE " + s['database'])  # Use specified database
    except (KeyError, FileNotFoundError, ValueError) as e:
        os.remove(os.path.join(C.BASE_DIR, "settings.json"))
        messagebox.showerror(
            title="Settings Load Error",
            message=f"Could not load settings file. It may be corrupted.\n\nError: {e}")
        setup()
        sys.exit()
    except Exception as e:
        messagebox.showerror(
            title="Database Connection Error",
            message=f"Could not connect to database.\n\nError: {e}")
        sys.exit()
root = tkinter.Tk()  # Create main app root
try:
    s= C.load_settings()  # Load settings from file
    username = s.get('user')  # Load saved username
    passwd = s.get('pass')  # Load saved password
    appinstance = UI.Flyts(root, base, user=username,
                           passwd=passwd)  # Run actual GUI
    root.mainloop()  # Start tkinter event loop
finally:
    base.signout()  # After app closes, close database connection
