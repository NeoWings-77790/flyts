# imports
import mysql.connector
import constants as C
import hashlib
from datetime import datetime, timedelta
from random import choice


class database:
    def __init__(self, host=C.host, user=C.user, passwd=C.passwd, charset=C.charset):
        # self.mydb = sqlite3.connect(self.db_path) for SQlite only
        self.cursor = None
        self.mydb = mysql.connector.connect(
            host=host,
            user=user,
            password=passwd,
            charset=charset
        )

    def connection(self):
        if self.mydb:
            # self.mydb.execute("PRAGMA foreign_keys = ON") for SQLite only
            self.cursor = self.mydb.cursor()

    def is_db(self):
        self.cursor.execute("SHOW DATABASES LIKE %s",
                            (C.database,))
        result = self.cursor.fetchone()
        if result:
            result2 = self.cursor.fetchone()
        return result is not None and result2 is not None

    def accounts_exist(self):
        self.cursor.execute("SELECT COUNT(*) FROM accounts")
        result = self.cursor.fetchone()
        return result[0] > 0

    def createtables(self):
        self.cursor.execute("CREATE DATABASE IF NOT EXISTS " +
                            C.database)
        self.cursor.execute("USE " + C.database)
        for i in C.tablecreator:
            self.cursor.execute(i)

    def insert_row(self, table, values):
        # Map table names to their column definitions
        table_columns = {
            "aircraft": C.aircraft_columns,
            "airports": C.airports_columns,
            "routes": C.routes_columns,
            "flights": C.flights_columns,
            "maintenance": C.maintenance_columns,
            "accounts": C.accounts_columns_auto
        }
        if table not in table_columns:
            raise ValueError(f"Unknown table: {table}")

        columns = table_columns[table]
        placeholders = ",".join("%s" for x in columns)
        query = f"INSERT IGNORE INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
        # INSERT IGNORE for MySQL

        self.cursor.execute(query, values)
        self.mydb.commit()

    def update_cell(self, table, column, newvalue, keyvalue):
        # 'UPDATE TABLE SET COLUMN = NEWVALUE WHERE PRIMARYKEY = KEYVALUE'
        query = f'UPDATE {table} SET {column} = %s where {C.primarykeys[table]} = %s'
        self.cursor.execute(query, (newvalue, keyvalue))
        self.mydb.commit()

    def update_cell_pk(self, table, pk_column, newvalue, old_pk_value):  # For primary keys ONLY
        query = f'UPDATE {table} SET {pk_column} = %s WHERE {pk_column} = %s'
        self.cursor.execute(query, (newvalue, old_pk_value))
        self.mydb.commit()

    def delete_row(self, table, keyvalue):  # delete row based on primary key value
        query = f"DELETE FROM {table} WHERE {C.primarykeys[table]} = %s"
        self.cursor.execute(query, (keyvalue,))
        self.mydb.commit()

    def filter_table(self, filters, valuelist):
        # Creates a list of filters that contain pieces of the SQL queries
        # Returns [AND (TABLE.COLUMN) OPERATOR (USERSPECIFIEDVALUE)] for each constraint
        constraints = ""
        values = []
        for i in range(len(filters)):
            column = C.filterslist[filters[i]]["column"]
            operator = C.filterslist[filters[i]]["op"]
            constraints += f" AND {column} {operator} %s"
            values.append(valuelist[i])
        return constraints, values

    def fetch_data(self, table, filters, valuelist):
        constraints, values = self.filter_table(filters, valuelist)
        query = f"SELECT * FROM {table} WHERE 1=1{constraints}"
        self.cursor.execute(query, values)
        rows = self.cursor.fetchall()
        return rows

    def plan_flights(self, days_ahead=14):
        # Get the location of each aircraft
        self.cursor.execute(
            "SELECT reg_no, loc FROM aircraft WHERE status='ACTV'")
        aircraft_locations = dict(self.cursor.fetchall())

        # Get the range of each aircraft
        self.cursor.execute(
            "SELECT reg_no, range_nm FROM aircraft WHERE status='ACTV'")
        aircraft_ranges = dict(self.cursor.fetchall())

        next_positions = aircraft_locations.copy()
        used_routes = set()
        for day in range(days_ahead):
            base_date = datetime.now().date() + timedelta(days=day)
            # For each aircraft, find potential routes it can take based on its current location and range
            for reg_no, current_loc in next_positions.items():
                potential_aircraft_assignments_query = (
                    """
                    SELECT flight, dep, arr, dept, arrt 
                    FROM routes 
                    WHERE dep=%s AND dist<%s 
                    ORDER BY greatcircledist ASC
                    """
                )
                self.cursor.execute(
                    potential_aircraft_assignments_query, (current_loc, aircraft_ranges.get(reg_no, 0)))
                routes = self.cursor.fetchall()

                if not routes:
                    continue  # No assignments possible for this aircraft
                # Filter out used routes
                potential_assignments = [assignment for assignment in routes if (
                    assignment[0], base_date) not in used_routes]
                if not potential_assignments:
                    continue  # No assignments possible for this aircraft

                flight, dep, arr, dept, arrt = choice(
                    potential_assignments)  # Unpacking results

                # Safely parse times — skip route if any time is missing
                if not dept or not arrt:
                    continue

                # Try to parse dept/arrt into datetimes if they are strings
                try:
                    dept_time = datetime.combine(
                        base_date, datetime.strptime(str(dept), "%H:%M:%S").time())
                    arr_time = datetime.combine(
                        base_date, datetime.strptime(str(arrt), "%H:%M:%S").time())
                    # If flight is overnight, adjust arrival time
                except ValueError:
                    continue
                if arr_time <= dept_time:
                    arr_time += timedelta(days=1)

                # Insert the new flight into the flights table
                insert_flight_query = (
                    '''
                    INSERT INTO flights (flight, reg_no, dept, arrt, status, dep, arr) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    '''
                )
                # Use a status value that matches the flights.status ENUM in constants
                # flights.status ENUM: ('Planned','In-Flight','Completed','Cancelled')
                self.cursor.execute(
                    insert_flight_query, (flight, reg_no,
                                          dept_time, arr_time, "Planned", dep, arr)
                )
                # Update the aircraft's next location
                next_positions[reg_no] = arr
                # Mark this route as used
                used_routes.add((flight, base_date))
        self.mydb.commit()

    def clear_all_flights(self):
        # Use TRUNCATE on MySQL to remove rows and reset AUTO_INCREMENT
        self.cursor.execute("TRUNCATE TABLE flights")
        # DELETE FROM sqlite_sequence WHERE name='flights'; for SQlite
        self.mydb.commit()

    # account management functions

    # takes username, password, role; creates new user in accounts table
    def register_user(self, username, password, role):
        hashed_password = hash_password(password)
        self.insert_row('accounts', (username, hashed_password,
                        role, 'ACTV', datetime.now(), datetime.now()))
        self.mydb.commit()

    # takes username and password, returns UserAccount object if successful, else None
    def login_user(self, username, password):
        hashed_password = hash_password(password)
        self.cursor.execute(
            "SELECT * FROM accounts WHERE username = %s AND passwd = %s", (username, hashed_password))
        result = self.cursor.fetchone()
        if result:
            user = UserAccount(self, *result)
            if user.is_active():
                self.update_cell('accounts', 'last_login',
                                 datetime.now(), user.account_id)
                return user
        return None

    def suspend_user(self, id):  # bans user
        self.update_cell('accounts', 'standing', 'SUSPD', id)

    def reactivate_user(self, id):  # unbans user
        self.update_cell('accounts', 'standing', 'ACTV', id)

    def change_passwd(self, id, new_password):
        hashed_password = hash_password(new_password)
        self.update_cell('accounts', 'passwd', hashed_password, id)

    def signout(self):  # From database connection
        if self.mydb:
            self.mydb.close()

# Helper function to hash passwords


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


class UserAccount:
    def __init__(self, db, account_id, username, passwd, role, standing, creation_date, last_login):
        self.db = db
        self.account_id = account_id
        self.username = username
        self.passwd = passwd
        self.role = role
        self.standing = standing
        self.creation_date = creation_date
        self.last_login = last_login

    def get_profile(self):
        return {
            "Account ID": self.account_id,
            "Username": self.username,
            "Role": self.role,
            "Standing": self.standing,
            "Creation Date": self.creation_date,
            "Last Login": self.last_login
        }

    def is_admin(self):
        return self.role == 'ADMIN'

    def is_staff(self):
        return self.role == 'STAFF'

    def is_guest(self):
        return self.role == 'GUEST'

    def is_active(self):
        return self.standing == 'ACTV'
