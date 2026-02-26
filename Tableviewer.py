# imports
import tkinter
from tkinter import ttk, messagebox
import constants as C


class TreeViewer:
    def __init__(self, root, main_app):
        self.root = root
        self.main_app = main_app
        self.frame = ttk.Frame(root)
        self.frame.pack(fill="both", expand=True)

        # Create the Treeview
        self.tree = ttk.Treeview(self.frame, show="tree headings", height=20)

        # Create scrollbars
        self.vsb = ttk.Scrollbar(
            self.frame, orient="vertical", command=self.tree.yview)  # for Y axis

        self.hsb = ttk.Scrollbar(
            self.frame, orient="horizontal", command=self.tree.xview)  # for X axis

        self.tree.configure(yscrollcommand=self.vsb.set,
                            xscrollcommand=self.hsb.set)  # link scrollbars to treeview

        # Initially hide tree and scrollbars, show placeholder
        self.tree.grid_remove()
        self.vsb.grid_remove()
        self.hsb.grid_remove()

        self.placeholder_label = ttk.Label(
            self.frame, text="•••", font=("Arial", 21), anchor="center")
        # Placeholder in center, before tree is loaded
        self.placeholder_label.grid(row=0, column=0, sticky="nsew")

        # Configure frame grid weights
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

        # Bind events like double-click(edit) and delete key(delete row)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Delete>", self.delete_row)

        self.active_editor = None  # active cell editor selection

        # Destroy editor when scrolling
        def destroy_editor(event=None):
            if self.active_editor:
                self.active_editor.destroy()
                self.active_editor = None

        self.vsb.bind("<B1-Motion>", destroy_editor)  # scrollbar drag vertical
        # scrollbar drag horizontal
        self.hsb.bind("<B1-Motion>", destroy_editor)
        self.tree.bind("<MouseWheel>", destroy_editor)   # Windows mousewheel
        self.tree.bind("<Configure>", destroy_editor)    # Resize window
        # scrollbar release vertical
        self.vsb.bind("<ButtonRelease-1>", destroy_editor)
        # scrollbar release horizontal
        self.hsb.bind("<ButtonRelease-1>", destroy_editor)

    def delete_row(self, event=None):  # delete selected row
        selected = self.tree.selection()  # selected row
        if not selected:
            return

        row_id = selected[0]  # get first selected row
        values = self.tree.item(row_id, "values")

        # confirm deletion
        if self.main_app.selected_table == "accounts":
            messagebox.showwarning(parent=self.root, title="Confirm Deletion",
                                   message="Are you sure you want to delete this account?")
        else:
            confirm = messagebox.askyesno(parent=self.root, title="Confirm Deletion",
                                          message=f"Are you sure you want to delete this row?\n\n{values}")
        if not confirm:
            return
        else:
            pk_value = values[self.pk_index]
            self.main_app.db.delete_row(self.main_app.selected_table, pk_value)
            self.tree.delete(row_id)

    def on_double_click(self, event):

        if not self.main_app.editmode.get() and self.root == self.main_app.root:   # only in edit mode
            return

        # identify clicked region
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":  # if it is not a cell, do nothing
            return

        row_id = self.tree.identify_row(event.y)  # get row ID for primary key
        col_id = self.tree.identify_column(
            event.x)  # get column ID for column name

        # get column index
        # convert to 0-based index from #1-based index
        col_index = int(col_id.replace("#", "")) - 1
        # find column name from index
        col_name = self.tree["columns"][col_index]

        if col_id == "#0":
            return  # editing tree column not supported

        # get current cell value
        old_value = self.tree.set(row_id, col_name)

        # get cell bounding box to place entry
        bbox = self.tree.bbox(row_id, col_id)
        if not bbox:  # cell not visible
            return
        x, y, width, height = bbox

        # create entry widget
        if not row_id or not col_id:
            return

        # row identification
        selected_table = self.main_app.selected_table  # from main app
        # get all values in the row
        row_values = self.tree.item(row_id, "values")
        pk_column = C.primarykeys[selected_table]
        pk_index = self.tree["columns"].index(pk_column)
        # get primary key value corresponding to the row
        pk_value = row_values[pk_index]
        self.original_pk_value = pk_value  # store original PK value in case it is edited

        # Determine editor type based on column data type
        if C.dtypes[selected_table][col_index][0] == 'entry':  # text entry
            entry = ttk.Entry(self.tree)
            entry.insert(0, old_value)
        elif C.dtypes[selected_table][col_index][0] == 'spinbox':  # numeric spinbox
            r1, r2 = C.dtypes[selected_table][col_index][1]
            entry = ttk.Spinbox(self.tree, from_=r1, to=r2)
            entry.insert(0, old_value)
        elif C.dtypes[selected_table][col_index][0] == 'combobox':  # dropdown combobox
            options = C.dtypes[selected_table][col_index][1]
            entry = ttk.Combobox(self.tree, values=options, state='readonly')
            entry.set(old_value)
        else:
            return

        # destroy any existing editor first, only one editor at a time
        if self.active_editor:
            self.active_editor.destroy()

        # place entry over cell
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus()  # focus on entry
        self.active_editor = entry  # set active editor

        def save_edit(event=None):  # save edited value on enter key press
            new_value = entry.get()  # get new value from entry
            if new_value == old_value:  # if value didn't change, do nothing
                entry.destroy()
                self.active_editor = None
                return
            self.tree.set(row_id, col_name, new_value)  # update treeview cell

            # database update confirmation
            confirm = messagebox.askyesno(parent=self.root, title="Confirm Modification",
                                          message=f"Are you sure you want to change the value from {old_value} to {new_value}?")
            if not confirm:
                self.tree.set(row_id, col_name, old_value)
                return  # revert change if not confirmed
            else:
                # commit changes to database
                entry.destroy()
                self.active_editor = None
                old_pk_value = self.original_pk_value
                # also push change to DB
                table = self.main_app.selected_table
                row_values = self.tree.item(row_id, "values")
                pk_column = C.primarykeys[table]
                pk_index = self.tree["columns"].index(pk_column)
                pk_value = row_values[pk_index]

                if col_name == pk_column:
                    old_pk_value = self.original_pk_value   # stored when editing began
                    self.main_app.db.update_cell_pk(
                        table, col_name, new_value, old_pk_value)

                else:
                    self.main_app.db.update_cell(
                        table, col_name, new_value, pk_value)

        entry.bind("<Return>", save_edit)  # Enter key to save edit
        entry.bind("<FocusOut>", lambda e: (
            # click outside to cancel edit
            entry.destroy(), setattr(self, 'active_editor', None)))

    def load_table(self, table_name, rows):
        # Hide the placeholder and bring back scrollbars
        self.placeholder_label.grid_remove()
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.hsb.grid(row=1, column=0, sticky="ew")
        if table_name == "aircraft":
            columns = C.aircraft_columns
            titles = C.aircraft_titles
        elif table_name == "airports":
            columns = C.airports_columns
            titles = C.airports_titles
        elif table_name == "routes":
            columns = C.routes_columns
            titles = C.routes_titles
        elif table_name == "flights":
            columns = C.flights_columns
            titles = C.flights_titles
        elif table_name == "maintenance":
            columns = C.maintenance_columns
            titles = C.maintenance_titles
        elif table_name == "accounts":
            columns = C.accounts_columns
            titles = C.accounts_titles
        else:
            columns, titles = [], []

        # clear old data
        self.tree.delete(*self.tree.get_children())  # Remove all items

        # input data
        self.tree["columns"] = columns
        self.tree.heading("#0", text="No.")  # index column
        self.tree.column("#0", width=50, anchor="center", stretch=False)
        # put each column heading and set width
        for i in columns:
            self.tree.heading(i, text=titles[columns.index(i)])
            self.tree.column(i, anchor="center", minwidth=60,
                             width=C.column_widths[i], stretch=False)

        # Add rows from SQL DB after fetching data and filtering, with numbering
        # enumerate rows starting from 1, giving each row an index
        for idx, row in enumerate(rows, start=1):
            self.tree.insert("", "end", text=str(idx), values=row)

        # Store the current table and selected rows
        self.main_app.selected_table = table_name
        self.main_app.selected_rows = rows
        pk_column = C.primarykeys[table_name]
        self.pk_index = columns.index(pk_column)
