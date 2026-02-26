# imports
import csv
import constants as C


class CSVmanager:
    def __init__(self, delimiter):
        self.delimiter = delimiter  # delimiter for CSV files

    def loadcsv(self, filename):
        # Read CSV with a tolerant mode (strip headers, case-insensitive match)
        with open(filename, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=self.delimiter)
            data = list(reader)

        if not data or not data[0]:
            raise Exception('Empty or invalid CSV file')

        header = [h.strip() for h in data[0]]
        header_l = [h.lower() for h in header]

        def cols_match(cols):
            return header_l == [c.lower() for c in cols]

        if cols_match(C.aircraft_columns):
            tablename = 'aircraft'
        elif cols_match(C.airports_columns):
            tablename = 'airports'
        elif cols_match(C.routes_columns):
            tablename = 'routes'
        elif cols_match(C.flights_columns):
            tablename = 'flights'
        elif cols_match(C.maintenance_columns):
            tablename = 'maintenance'
        else:
            raise Exception(f'Invalid table attributes: {data[0]}')

        return data, tablename

    def savecsv(self, filename, rows, columns):
        with open(filename, 'w') as file:
            writer = csv.writer(
                file, delimiter=',')  # write CSV file
            writer.writerow(columns)  # write header
            writer.writerows(rows)  # write data rows
