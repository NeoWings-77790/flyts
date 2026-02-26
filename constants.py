# imports
import os
import json
import tkinter as tk
from tkinter import ttk

# databaseposition=r'C:\Users\Neo\OneDrive\Documents\School\12th grade\school\CS\Fun\aircraft_fleet\airlinedb.db'
BASE_DIR = os.path.dirname(__file__)  # Folder where the project is located
DB_PATH = os.path.join(BASE_DIR, "airlinedb.db")  # SQLite file path
CSV_TEMPLATE_PATH = os.path.join(BASE_DIR, "template.csv")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")  # Folder for exported files

# default app settings
defdelimiter = ' '
signed_in_user = None
signed_in_passwd = None
user = ''
host = ''
passwd = ''
charset = 'utf8mb4'
defaultsave = EXPORTS_DIR
app_theme = 'vista'
database = 'flyts_db'
defaultsettingslist = {'user': signed_in_user,
                       'pass': signed_in_passwd,
                       'user_db': user,
                       'host': host,
                       'charset': charset,
                       'passwd_db': passwd,
                       'defaultsave': defaultsave,
                       'app_theme': app_theme,
                       'database': database}

supported_character_sets = ['utf8mb4', 'utf8',
                            'utf16', 'utf32', 'latin1', 'ucs2']


# Gets a dictionary of settings and saves them to settings.json
def save_settings(settingsdict: dict):
    # Settings file path = BASE_DIR/settings.json
    with open(os.path.join(BASE_DIR, "settings.json"), 'w') as settings:
        json.dump(settingsdict, settings)  # Save settings dict as json to file


def load_settings():
    if os.path.exists(os.path.join(BASE_DIR, "settings.json")):  # If settings file exists
        try:
            with open(os.path.join(BASE_DIR, "settings.json"), 'r') as settings:
                settingsdict = json.load(settings)  # Load settings from file
                return settingsdict  # Return loaded settings
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in settings file: {e}")
    else:
        raise FileNotFoundError("Settings file not found.")


def settings_exist():  # Returns True if settings file exists, False otherwise
    return os.path.exists(os.path.join(BASE_DIR, "settings.json"))


def get_supported_themes():  # Returns a list of supported ttk themes on the current OS
    temp_root = tk.Tk()  # Temporary root to get themes
    style = ttk.Style(temp_root)  # style object
    themes = style.theme_names()  # Get list of supported themes
    temp_root.destroy()  # Destroy temporary root
    return themes


# Table creation queries
# MySQL-optimized table creation queries (InnoDB, utf8mb4, proper types, ENUMs and AUTO_INCREMENT)
aircrafttable = """CREATE TABLE IF NOT EXISTS aircraft (
  reg_no VARCHAR(8) NOT NULL PRIMARY KEY,
  model VARCHAR(64) NOT NULL,
  engine VARCHAR(64),
  msn INT UNIQUE,
  capacity SMALLINT UNSIGNED,
  range_nm INT UNSIGNED,
  status ENUM('ACTV','MAINT','PRKD','GRND') NOT NULL DEFAULT 'ACTV',
  loc CHAR(4),
  hours_flown INT UNSIGNED NOT NULL DEFAULT 0,
  age DECIMAL(4,2),
  last_maintenance DATETIME,
  CONSTRAINT fk_aircraft_loc FOREIGN KEY (loc) REFERENCES airports(ICAO) ON DELETE SET NULL ON UPDATE CASCADE
)"""

airportstable = """CREATE TABLE IF NOT EXISTS airports (
  ICAO CHAR(4) NOT NULL PRIMARY KEY,
  IATA CHAR(3),
  name VARCHAR(100) NOT NULL,
  city VARCHAR(100),
  fuel DECIMAL(10,2) NOT NULL DEFAULT 0.00
)"""

routestable = """CREATE TABLE IF NOT EXISTS routes (
  flight VARCHAR(6) NOT NULL PRIMARY KEY,
  dep CHAR(4) NOT NULL,
  arr CHAR(4) NOT NULL,
  dist DECIMAL(9,2),
  greatcircledist DECIMAL(9,2),
  time INT UNSIGNED,
  dept TIME,
  arrt TIME,
  CONSTRAINT fk_routes_dep FOREIGN KEY (dep) REFERENCES airports(ICAO) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_routes_arr FOREIGN KEY (arr) REFERENCES airports(ICAO) ON DELETE CASCADE ON UPDATE CASCADE
)"""

flightstable = """CREATE TABLE IF NOT EXISTS flights (
  flightnumber INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  flight VARCHAR(6) NOT NULL,
  reg_no VARCHAR(8),
  dept DATETIME,
  arrt DATETIME,
  status ENUM('Planned','In-Flight','Completed','Cancelled') NOT NULL DEFAULT 'Planned',
  dep CHAR(4),
  arr CHAR(4),
  CONSTRAINT fk_flights_route FOREIGN KEY (flight) REFERENCES routes(flight) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT fk_flights_reg FOREIGN KEY (reg_no) REFERENCES aircraft(reg_no) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_flights_dep FOREIGN KEY (dep) REFERENCES airports(ICAO) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT fk_flights_arr FOREIGN KEY (arr) REFERENCES airports(ICAO) ON DELETE SET NULL ON UPDATE CASCADE,
  KEY idx_flights_reg_no (reg_no),
  KEY idx_flights_dept (dept)
)"""

maintenancetable = """CREATE TABLE IF NOT EXISTS maintenance (
  record_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  reg_no VARCHAR(8) NOT NULL,
  date DATETIME,
  descr TEXT,
  status ENUM('Pending','Completed') NOT NULL DEFAULT 'Pending',
  CONSTRAINT fk_maintenance_reg FOREIGN KEY (reg_no) REFERENCES aircraft(reg_no) ON DELETE CASCADE ON UPDATE CASCADE,
  KEY idx_maintenance_reg (reg_no),
  KEY idx_maintenance_date (date)
)"""
# keys for faster searches on foreign key columns on reg_no and date
accountstable = """CREATE TABLE IF NOT EXISTS accounts (
  account_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(64) NOT NULL UNIQUE,
  passwd VARCHAR(255) NOT NULL,
  role ENUM('ADMIN','STAFF','GUEST') NOT NULL DEFAULT 'GUEST',
  standing ENUM('ACTV','SUSPD') NOT NULL DEFAULT 'ACTV',
  creation_date DATE NOT NULL DEFAULT (CURRENT_DATE),
  last_login DATETIME,
  KEY idx_accounts_username (username) 
)"""
# key is index for faster searches on the username column
# AUTO_INCREMENT for unique IDs
# Create referenced tables first (airports must exist before aircraft which
# has a FK to airports). Order matters for MySQL foreign key creation.
tablecreator = [airportstable, aircrafttable, routestable,
                flightstable, maintenancetable, accountstable]

primarykeys = {"aircraft": "reg_no", "airports": "ICAO",
               "routes": "flight", "flights": "flightnumber", "maintenance": "record_id", "accounts": "account_id"}

# List of columns in each table
aircraft_columns = ['reg_no', 'model', 'engine', 'msn', 'capacity',
                    'range_nm', 'status', 'loc', 'hours_flown', 'age', 'last_maintenance']
airports_columns = ['ICAO', 'IATA', 'name', 'city', 'fuel']
routes_columns = ['flight', 'dep', 'arr', 'dist',
                  'greatcircledist', 'time', 'dept', 'arrt']
flights_columns = ['flightnumber', 'flight',
                   'reg_no', 'dept', 'arrt', 'status', 'dep', 'arr']
maintenance_columns = ["record_id", "reg_no", "date", "descr", "status"]
accounts_columns = ["account_id", "username", "passwd",
                    "role", "standing", "creation_date", "last_login"]
accounts_columns_auto = ["username", "passwd",
                         # Excludes account_id since it's autoincremented, used for inserts
                         "role", "standing", "creation_date", "last_login"]
columns = [aircraft_columns, airports_columns,
           routes_columns, flights_columns, maintenance_columns, accounts_columns]


# Titles for each column in each table
aircraft_titles = ["Registration", "Aircraft Model", "Engine", "MSN", "Capacity",
                   "Range(NM)", "Status", "Location", "Hours Flown", "Age(Years)", "Last Maintenance"]
airports_titles = ["ICAO code", "IATA code", "Name", "City", "Fuel Cost"]
routes_titles = ["Flight", "From", "To",
                 "Distance (NM)", "Great Circle Distance (NM)", "Time (min)", "Departure Time", "Arrival Time"]
flights_titles = ["Flight No.", "Flight", "Registration",
                  "Departure Time", "Arrival Time", "Status", "From", "To"]
maintenance_titles = ["Record ID", "Registration",
                      "Date", "Description", "Status"]
accounts_titles = ["Account ID", "Username", "Password",
                   "Role", "Standing", "Creation Date", "Last Login"]
titles = [aircraft_titles, airports_titles,
          routes_titles, flights_titles, maintenance_titles, accounts_titles]

# Column widths for each column in each table
column_widths = {  # some columns are wider than others so they need different widths
    # some columns are the same across multiple tables so they can share widths
    # aircraft table
    'reg_no': 75,  # registration
    'model': 100,  # aircraft model
    'engine': 120,  # engine
    'msn': 100,  # MSN
                 'capacity': 60,  # capacity
                 'range_nm': 80,  # range
                 'status': 300,  # status
                 'loc': 70,  # location
                 'hours_flown': 100,  # hours flown
                 'age': 70,  # age
                 'last_maintenance': 150,  # last maintenance

    # airports table
                 'ICAO': 70,  # ICAO code (airport)
                 'IATA': 70,  # IATA code (airport)
                 'name': 120,  # Name
                 'city': 200,  # City
                 'fuel': 120,  # Fuel Cost

    # routes table
                 'flight': 120,  # flight
                 'dep': 70,  # departure airport ICAO
                 'arr': 70,  # arrival airport ICAO
                 'dist': 90,  # distance (NM)
                 'greatcircledist': 90,  # great circle distance (NM)
                 'time': 70,  # time (min)
                 'dept': 120,  # departure time
                 'arrt': 120,  # arrival time

    # flights table
                 # flight number (unique ID for each flight)
                 'flightnumber': 120,

    # maintenance table
                 # record ID (unique ID for each maintenance record)
                 "record_id": 70,
                 "date": 170,  # date of maintenance
                 "descr": 300,  # description of maintenance

                    # accounts table
                 'account_id': 70,  # account ID (unique ID for each account)
                 'username': 120,  # username
                 'passwd': 120,  # password
                 'role': 120,  # role
                 'standing': 120,  # standing
                 'creation_date': 170,  # creation date
                 'last_login': 170,  # last login

}

# Data types and input methods for each column in each table
# Format: 'table_name': [('data_type', additional_info)]
dtypes = {
    'aircraft': [
        ('entry',),                            # reg_no
        ('entry',),                            # model
        ('entry',),                            # engine
        ('entry',),                            # MSN
        ('spinbox', (1, 600)),                 # capacity (passenger capacity)
        ('spinbox', (100, 20000)),             # range (in km/nm, adjustable)
        ('combobox', ('ACTV', 'MAINT', 'PRKD', 'GRND')),             # status
        ('entry',),                            # loc (base airport ICAO)
        ('spinbox', (0, 100000)),              # hours_flown
        ('spinbox', (0, 50)),                 # age (years)
        ('entry',)                            # last_maintenance
    ],

    'airports': [
        ('entry',),                            # icao
        ('entry',),                            # iata
        ('entry',),                            # name
        ('entry',),                            # city
        ('spinbox', (0, 1000000))              # fuel (stored units)
    ],

    'routes': [
        ('entry',),                            # flight
        ('entry',),                            # dep (ICAO)
        ('entry',),                            # arr (ICAO)
        ('spinbox', (0, 20000)),               # dist
        ('spinbox', (0, 20000)),               # greatcircledist
        ('spinbox', (0, 1000))                 # time (minutes/hours depending)
    ],

    'flights': [
        ('entry',),                            # flightnumber
        ('entry',),                            # flight
        ('entry',),                            # reg_no
        ('entry',),                            # dept(departure time)
        ('entry',),                            # arrt (arrival time)
        ('combobox', ('Planned', 'In-Flight', 'Completed', 'Cancelled')),  # status
        ('entry',),                            # dep (departure airport ICAO)
        ('entry',),                            # arr (arrival airport ICAO)
    ],

    'maintenance': [
        ('entry',),                            # record_id
        ('entry',),                            # reg_no
        ('entry',),                            # date
        ('entry',),                            # descr
        ('combobox', ('Pending', 'Completed'))  # status
    ],

    'accounts': [
        ('entry',),                            # account_id
        ('entry',),                            # username
        ('entry',),                            # password
        ('combobox', ('USER', 'ADMIN')),        # role
        ('combobox', ('ACTV', 'SUSPD')),       # standing
        ('entry',),                            # creation_date
        ('entry',)                             # last_login
    ]
}

# The filterslist dictionary contains filter configurations for each filterable field across different tables.
# Each filter configuration includes the table name, column name, operation, input type, title, and additional options if applicable.
# Format: 'filter_name': {'table': 'table_name', 'column': 'column_name', 'op': 'operator', 'type': 'input_type', 'title': 'Display Title', 'options': (optional, for dropdowns)}
filterslist = {
    # Aircraft Filters
    "aircraft": {"table": "aircraft", "column": "reg_no", "op": "=", 'type': 'text', 'title': 'Aircraft'},
    "aircraft_model": {"table": "aircraft", "column": "model", "op": "=", 'type': 'text', 'title': 'Aircraft Model'},
    "aircraft_engine": {"table": "aircraft", "column": "engine", "op": "=", 'type': 'text', 'title': 'Aircraft Engine'},
    "aircraft_msn": {"table": "aircraft", "column": "msn", "op": "=", 'type': 'text', 'title': 'Aircraft MSN'},
    "capacity_min": {"table": "aircraft", "column": "capacity", "op": ">=", 'type': 'num', 'title': 'Minimum Capacity'},
    "capacity_max": {"table": "aircraft", "column": "capacity", "op": "<=", 'type': 'num', 'title': 'Maximum Capacity'},
    "aircraft_status": {"table": "aircraft", "column": "status", "op": "=", 'type': 'dropdown', 'title': 'Aircraft Status', 'options': ('ACTV', 'MAINT', 'PRKD', 'GRND')},
    "current_location": {"table": "aircraft", "column": "loc", "op": "=", 'type': 'text', 'title': 'Current Location'},
    "hours_flown_min": {"table": "aircraft", "column": "hours_flown", "op": ">=", 'type': 'num', 'title': 'Minimum Hours Flown'},
    "hours_flown_max": {"table": "aircraft", "column": "hours_flown", "op": "<=", 'type': 'num', 'title': 'Maximum Hours Flown'},
    "range_min": {"table": "aircraft", "column": "range_nm", "op": ">=", 'type': 'num', 'title': 'Minimum Range'},
    "range_max": {"table": "aircraft", "column": "range_nm", "op": "<=", 'type': 'num', 'title': 'Maximum Range'},
    "aircraft_age_max": {"table": "aircraft", "column": "age", "op": "<=", 'type': 'spin', 'title': aircraft_titles[9], 'range': (0, 50)},
    "last_maint_before": {"table": "aircraft", "column": "last_maintenance", "op": "<", 'type': 'date', 'title': 'Maintained before (YYYY-MM-DD)'},

    # Airport Filters
    "airport_name": {"table": "airports", "column": "name", "op": "=", 'type': 'text', 'title': 'Airport Name'},
    "airport_code": {"table": "airports", "column": "ICAO", "op": "=", 'type': 'text', 'title': 'Airport ICAO Code'},
    "airport_code_IATA": {"table": "airports", "column": "IATA", "op": "=", 'type': 'text', 'title': 'Airport IATA Code'},
    "fuel_cost_min": {"table": "airports", "column": "fuel", "op": ">=", 'type': 'num', 'title': 'Minimum Fuel Cost'},
    "fuel_cost_max": {"table": "airports", "column": "fuel", "op": "<=", 'type': 'num', 'title': 'Maximum Fuel Cost'},

    # Flight Filters
    "flight_id": {"table": "flights", "column": "flightnumber", "op": "=", 'type': 'text', 'title': 'Flight ID'},
    "flight_no": {"table": "flights", "column": "flight", "op": "=", 'type': 'text', 'title': 'Flight No.'},
    "assigned_aircraft": {"table": "flights", "column": "reg_no", "op": "=", 'type': 'text', 'title': 'Assigned Aircraft'},
    "dept_after": {"table": "flights", "column": "dept", "op": ">=", 'type': 'num', 'title': 'Departure After'},
    "dept_before": {"table": "flights", "column": "dept", "op": "<=", 'type': 'num', 'title': 'Departure Before'},
    "flight_status": {"table": "flights", "column": "status", "op": "=", 'type': 'dropdown', 'title': 'Flight Status', 'options': ('On-Time', 'Delayed', 'Cancelled')},
    "dep_airport": {"table": "routes", "column": "dep", "op": "=", 'type': 'text', 'title': 'Departure Airport'},
    "arr_airport": {"table": "routes", "column": "arr", "op": "=", 'type': 'text', 'title': 'Arrival Airport'},


    # Route Filters
    "route_flight": {"table": "routes", "column": "flight", "op": "=", 'type': 'text', 'title': 'Flight'},
    "route_dep": {"table": "routes", "column": "dep", "op": "=", 'type': 'text', 'title': 'Departure Airport'},
    "route_arr": {"table": "routes", "column": "arr", "op": "=", 'type': 'text', 'title': 'Arrival Airport'},
    "route_dist_min": {"table": "routes", "column": "dist", "op": ">=", 'type': 'num', 'title': 'Minimium Distance'},
    "route_dist_max": {"table": "routes", "column": "dist", "op": "<=", 'type': 'num', 'title': 'Maximum Distance'},
    "route_great_circle_dist_min": {"table": "routes", "column": "greatcircledist", "op": "=", 'type': 'num', 'title': 'Great Circle Distance'},
    "route_great_circle_dist_max": {"table": "routes", "column": "greatcircledist", "op": "<=", 'type': 'num', 'title': 'Maximum Great Circle Distance'},
    "route_time_max": {"table": "routes", "column": "time", "op": "<=", 'type': 'num', 'title': 'Maximum Time'},

    # Maintenance Filters
    "maint_record_id": {"table": "maintenance", "column": "record_id", "op": "=", 'type': 'text', 'title': 'Record ID'},
    "maint_registration": {"table": "maintenance", "column": "reg_no", "op": "=", 'type': 'text', 'title': 'Registration'},
    "maint_date": {"table": "maintenance", "column": "date", "op": "=", 'type': 'text', 'title': 'Date'},
    "maint_description": {"table": "maintenance", "column": "descr", "op": "=", 'type': 'text', 'title': 'Description'},
    "maint_status": {"table": "maintenance", "column": "status", "op": "=", 'type': 'dropdown', 'title': 'Aircraft Status', 'options': ('Pending', 'Completed')},
    "maint_after": {"table": "maintenance", "column": "date", "op": ">=", 'type': 'text', 'title': 'Maintenance After'},
    "maint_before": {"table": "maintenance", "column": "date", "op": "<=", 'type': 'text', 'title': 'Maintenance Before'},
    "maint_aircraft": {"table": "maintenance", "column": "reg_no", "op": "=", 'type': 'text', 'title': 'Aircraft'}
}
