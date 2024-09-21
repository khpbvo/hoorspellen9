import sys
import msvcrt
import psycopg2
from psycopg2 import sql
import blessed
import csv
import datetime
import certifi
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
import base64
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from google.auth.transport.requests import Request
import pickle
import os.path
import mimetypes
import logging
import difflib
import re
import time

os.environ['SSL_CERT_FILE'] = certifi.where()

# Make sure to set up logging at the beginning of your script
logging.basicConfig(filename='hoorspellen_app.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Database connection details
def get_db_connection():
    return psycopg2.connect(
        dbname='hoorspellen',
        user='hoorspellen',
        password='1337Hoorspellen!@',
        host='172.20.20.172',
        port='5432'
    )

def initialize_db(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hoorspelen (
            id SERIAL PRIMARY KEY,
            auteur TEXT,
            titel TEXT,
            regie TEXT,
            datum TEXT,
            omroep TEXT,
            bandnr TEXT,
            vertaling TEXT,
            duur TEXT,
            bewerking TEXT,
            genre TEXT,
            productie TEXT,
            themareeks TEXT,
            delen TEXT,
            bijzverm TEXT,
            taal TEXT
        )
    ''')
    conn.commit()

def geavanceerd_submenu(conn, term):
    options = [
        ("Importeren", lambda: import_function(conn)),
        ("Exporteren", lambda: export_function(conn)),
        ("DB Legen", lambda: clear_db_function(conn)),
        ("Terug naar Hoofdmenu", None)
    ]
    current_option = 0

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        for index, option in enumerate(options):
            print(f"   {option[0]}")
        # Move cursor back to the start of the line where the selected option is and clear to end of line.
        print(f"\033[{len(options) - current_option}A\r-> {options[current_option][0]}\033[K", end='', flush=True)

        key = msvcrt.getch()
        if key in [b'\x00', b'\xe0']:  # Special keys (including arrows) are preceded by these bytes
            key = msvcrt.getch()  # Fetch the actual key code

        if key == b'\r':  # Enter key
            if options[current_option][1] is None:  # "Terug naar Hoofdmenu" option
                break
            else:
                options[current_option][1]()  # Execute the selected function
        elif key == b'H':  # Up arrow key
            current_option = (current_option - 1) % len(options)  # Move up in the list
        elif key == b'P':  # Down arrow key
            current_option = (current_option + 1) % len(options)  # Move down in the list

def main_menu(conn, term):
    options = [
        "Voeg Toe",
        "Bewerk Hoorspellen",
        "Zoek Hoorspellen",
        "Totaal",
        "Geschiedenis",
        "Geavanceerd",
        "Afsluiten"
    ]
    current_option = 0

    while True:
        print(term.home + term.clear, end='')
        for index, option in enumerate(options):
            if index == current_option:
                print(f"-> {option}")
            else:
                print(f"   {option}")
        
        # Move cursor to the end of the selected option
        selected_text = f"-> {options[current_option]}"
        print(term.move_yx(current_option, len(selected_text)), end='', flush=True)

        with term.cbreak():
            key = term.inkey()

        if key.name == 'KEY_UP':
            current_option = (current_option - 1) % len(options)
        elif key.name == 'KEY_DOWN':
            current_option = (current_option + 1) % len(options)
        elif key.name == 'KEY_ENTER':
            if current_option == len(options) - 1:  # "Afsluiten" option
                print(term.home + term.clear)
                print("Backup aan het maken, moment geduld.")
                email_message = create_message_with_attachment(
                    "sjefsdatabasebackups@gmail.com",
                    "sjefsdatabasebackups@gmail.com",
                    "Hoorspelen backup",
                    "De backup van de hoorspelen",
                    csv_path=export_function(conn)
                )
                service = gmail_service()
                send_message(service, "me", email_message)
                return
            else:
                function_map = {
                    "Voeg Toe": lambda: voeg_toe(conn, term),
                    "Bewerk Hoorspellen": lambda: bewerk_hoorspel(conn, term),
                    "Zoek Hoorspellen": lambda: zoek_hoorspellen(conn, term),
                    "Totaal": lambda: toon_totaal_hoorspellen(conn, term),
                    "Geschiedenis": lambda: geschiedenis(conn, term),
                    "Geavanceerd": lambda: geavanceerd_submenu(conn, term),
                }
                selected_function = function_map.get(options[current_option])
                if selected_function:
                    selected_function()
        elif key.name == 'KEY_ESCAPE':
            print(term.home + term.clear)
            print("Backup aan het maken, moment geduld.")
            email_message = create_message_with_attachment(
                "sjefsdatabasebackups@gmail.com",
                "sjefsdatabasebackups@gmail.com",
                "Hoorspelen backup",
                "De backup van de hoorspelen",
                csv_path=export_function(conn)
            )
            service = gmail_service()
            send_message(service, "me", email_message)
            return

def import_function(conn):
    filename = input("Voer het pad naar het CSV-bestand in: ")
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            # Optionally, skip the header if your CSV file includes one
            next(reader, None)  # This skips the first line of the CSV which usually contains the header
            cursor = conn.cursor()
            for row in reader:
                print(f"Importing row: {row}")  # Debugging statement
                # Adjust this line if the structure is different
                data_to_insert = row[1:]  # Exclude the first column (id) if your CSV includes it
                print(f"Data to insert: {data_to_insert}")  # Debugging statement
                cursor.execute('''
                    INSERT INTO hoorspelen (auteur, titel, regie, datum, omroep, bandnr, vertaling, duur, bewerking, genre, productie, themareeks, delen, bijzverm, taal)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', data_to_insert)
            conn.commit()
        print("Importeren gelukt.")
    except Exception as e:
        print(f"Er is een fout opgetreden: {e}")

    input("Druk op Enter om verder te gaan...")

def export_function(conn):
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")  # Replacing ':' with '_'
    filename = f"hoorspellendb_{timestamp}.csv"
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM hoorspelen")
            writer = csv.writer(csvfile)
            writer.writerow([desc[0] for desc in cursor.description])  # Write headers
            writer.writerows(cursor.fetchall())
        print(f"Exporteren gelukt. Bestand opgeslagen als: {filename}")
        return filename  # Return the filename for use in email attachment
    except Exception as e:
        print(f"Er is een fout opgetreden: {e}")
        os.system('cls' if os.name == 'nt' else 'clear')
        return None  # Return None to indicate failure

    input("Druk op Enter om verder te gaan...")

def clear_db_function(conn):
    confirm = input("Weet u zeker dat u alle gegevens wilt wissen? Type 'ja' om te bevestigen: ")
    if confirm.lower() == 'ja':
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hoorspelen")
            conn.commit()
            print("Database geleegd.")
        except Exception as e:
            print(f"Er is een fout opgetreden: {e}")
    else:
        print("Wissen geannuleerd.")

    input("Druk op Enter om verder te gaan...")

def validate_date(date_string):
    try:
        datetime.datetime.strptime(date_string, '%Y/%m/%d')  # Validate date format
        return True
    except ValueError:
        return False

def get_input(prompt):
    print(prompt, end='', flush=True)
    value = ''
    while True:
        char = msvcrt.getch()
        if char in (b'\r', b'\n'):  # Enter key
            break
        elif char == b'\x08':  # Backspace key
            value = value[:-1]
            # Reprint the prompt and current value
            print('\r' + ' ' * (len(prompt) + len(value) + 1) + '\r', end='', flush=True)
            print(prompt + value, end='', flush=True)
        elif char == b'\x1b':  # Escape key
            print("\nExiting input...")
            return None
        else:
            value += char.decode()
            print(char.decode(), end='', flush=True)
    print()  # Print a newline
    return value

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def voeg_toe(conn, term):
    logging.info("Starting voeg_toe function")
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT MAX(id) FROM hoorspelen')
        max_id = cursor.fetchone()[0]
        new_id = max_id + 1 if max_id is not None else 1
        logging.info(f"New record ID will be: {new_id}")
    except Exception as e:
        logging.error(f"Error getting new ID: {e}")
        print(term.clear + f"Error: {e}. Press any key to continue.")
        term.inkey()
        return

    fields = ['auteur', 'titel', 'regie', 'datum', 'omroep', 'bandnr', 'vertaling', 'duur', 'bewerking', 'genre', 'productie', 'themareeks', 'delen', 'bijzverm', 'taal']
    record = {field: "" for field in fields}
    current_field = 0
    error_message = ""

    def display_form():
        print(term.home + term.clear, end='')
        for i, field in enumerate(fields):
            if i == current_field:
                print(f"-> {field}: {record[field]}", end='')
                if error_message:
                    print(f" {term.red(error_message)}", end='')
                print()
            else:
                print(f"   {field}: {record[field]}")
        
        # Move cursor to the end of the selected option
        print(term.move_yx(current_field, len(f"-> {fields[current_field]}: {record[fields[current_field]]}")), end='', flush=True)

    def validate_record():
        logging.info("Validating record")
        if not is_valid_datum_format(record['datum']):
            logging.warning(f"Invalid date format: {record['datum']}")
            return "Verkeerde datum. Gebruik YYYY/MM/DD."
        for field in fields:
            if not record[field].strip():
                logging.warning(f"Empty field: {field}")
                return f"'{field}' mag niet leeg zijn."
        logging.info("Record validation passed")
        return None

    while True:
        display_form()

        with term.cbreak():
            key = term.inkey()

        if key.name == 'KEY_ESCAPE':
            logging.info("User pressed ESC, exiting voeg_toe")
            return
        elif key == '\x13':  # Ctrl+S
            logging.info("User pressed Ctrl+S, attempting to save record")
            error = validate_record()
            if error:
                error_message = error
                logging.warning(f"Validation error: {error}")
            else:
                try:
                    record_values = [new_id] + [record[field] for field in fields]
                    placeholders = ', '.join(['%s'] * (len(fields) + 1))
                    query = f'INSERT INTO hoorspelen (id, {", ".join(fields)}) VALUES ({placeholders})'
                    logging.info(f"Executing SQL query: {query}")
                    logging.info(f"Query parameters: {record_values}")
                    cursor.execute(query, record_values)
                    conn.commit()
                    logging.info("Record successfully added to database")
                    print(term.clear + "Record toegevoegd. Druk op een toets.")
                    term.inkey()
                    return
                except Exception as e:
                    error_message = f"Fout bij toevoegen: {e}"
                    logging.error(f"Error adding record to database: {e}")
        elif key.name == 'KEY_UP':
            current_field = (current_field - 1) % len(fields)
            error_message = ""
        elif key.name == 'KEY_DOWN':
            current_field = (current_field + 1) % len(fields)
            error_message = ""
        elif key.name == 'KEY_ENTER':
            current_field = (current_field + 1) % len(fields)
            error_message = ""
        elif key.name == 'KEY_BACKSPACE':
            record[fields[current_field]] = record[fields[current_field]][:-1]
            error_message = ""
        else:
            record[fields[current_field]] += key
            error_message = ""

    cursor.close()
    logging.info("Exiting voeg_toe function")

def is_valid_datum_format(datum):
    if not re.match(r'^\d{4}/\d{2}/\d{2}$', datum):
        return False
    try:
        year, month, day = map(int, datum.split('/'))
        datetime.date(year, month, day)
        return True
    except ValueError:
        return False

def bewerk_hoorspel(conn, term):
    clear_screen = lambda: print(term.home + term.clear, end='', flush=True)

    # Prompt voor invoeren van ID
    clear_screen()
    entry_id = handle_input("Voer de ID in van de inzending die je wilt bewerken: ")
    if entry_id is None:
        return

    try:
        entry_id = int(entry_id)
    except ValueError:
        print("Ongeldige invoer. Probeer opnieuw")
        return

    # Query om de inzending met dit ID op te halen
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hoorspelen WHERE id = %s", (entry_id,))
    entry = cursor.fetchone()

    if entry:
        fields = ['auteur', 'titel', 'regie', 'datum', 'omroep', 'bandnr', 'vertaling', 'duur', 'bewerking', 'genre', 'productie', 'themareeks', 'delen', 'bijzverm', 'taal']
        current_field = 0
        record = {field: entry[i+1] for i, field in enumerate(fields)}  # Op basis van SQL-resultaten
        error_message = ""

        def display_form():
            print(term.home + term.clear, end='')
            for i, field in enumerate(fields):
                value = record[field] if record[field] is not None else ''
                if i == current_field:
                    print(f"-> {field}: {value}", end='')
                    if error_message:
                        print(f" {term.red(error_message)}", end='')
                    print()
                else:
                    print(f"   {field}: {value}")
            
            # Cursor positioneren
            print(term.move_yx(current_field, len(f"-> {fields[current_field]}: {record[fields[current_field]]}")), end='', flush=True)

        def validate_record():
            # Controleer of datum-formaat correct is
            if not is_valid_datum_format(record['datum']):
                return "Verkeerde datum. Gebruik YYYY/MM/DD."
            for field in fields:
                if not record[field].strip():  # Verifieer lege velden
                    return f"'{field}' mag niet leeg zijn."
            return None

        while True:
            display_form()

            with term.cbreak():
                key = term.inkey()

            if key.name == 'KEY_ESCAPE':
                return
            elif key.name == 'KEY_UP':
                current_field = (current_field - 1) % len(fields)
            elif key.name == 'KEY_DOWN':
                current_field = (current_field + 1) % len(fields)
            elif key.name == 'KEY_ENTER':
                clear_screen()
                new_value = handle_input(f"Nieuwe waarde voor {fields[current_field]}: ")
                if new_value:
                    record[fields[current_field]] = new_value
            elif key == '\x13':  # Ctrl+S om op te slaan
                error = validate_record()
                if error:
                    error_message = error
                else:
                    try:
                        placeholders = ', '.join([f"{field} = %s" for field in fields])
                        query = f"UPDATE hoorspelen SET {placeholders} WHERE id = %s"
                        cursor.execute(query, [record[field] for field in fields] + [entry_id])
                        conn.commit()
                        # Verplaats cursor direct achter de zin
                        print(term.clear + "Record succesvol bijgewerkt. Druk op een toets.", end='')
                        # Verplaats de cursor naar het einde van de tekst
                        print(term.move_x(len("Record succesvol bijgewerkt. Druk op een toets.")), end='', flush=True)
                        term.inkey()
                        return
                    except Exception as e:
                        error_message = f"Fout bij bijwerken: {e}"
                
    else:
        print("Inzending niet gevonden.")
    
    input("Druk op Enter om verder te gaan...")

valid_fields = [
    "id", "auteur", "titel", "regie", "datum", "omroep", "bandnr",
    "vertaling", "duur", "bewerking", "genre", "productie",
    "themareeks", "delen", "bijzverm", "taal"
]

def execute_search(conn, search_term, offset, limit, specific_field=None):
    cursor = conn.cursor()

    try:
        # If a specific field is provided
        if specific_field and specific_field in valid_fields:
            if specific_field == 'id':
                # Ensure the search term is a digit for 'id'
                if not search_term.isdigit():
                    raise ValueError("ID moet een numerieke waarde zijn.")
                query = sql.SQL("SELECT * FROM hoorspelen WHERE {} = %s LIMIT %s OFFSET %s").format(sql.Identifier(specific_field))
                cursor.execute(query, (search_term, limit, offset))
            else:
                # Use ILIKE for text fields
                query = sql.SQL("SELECT * FROM hoorspelen WHERE {} ILIKE %s LIMIT %s OFFSET %s").format(sql.Identifier(specific_field))
                cursor.execute(query, (f"%{search_term}%", limit, offset))
        else:
            conditions = []
            params = []

            for field in valid_fields:
                if field != 'id':
                    conditions.append(sql.SQL("{} ILIKE %s").format(sql.Identifier(field)))
                    params.append(f"%{search_term}%")

            if search_term.isdigit():
                conditions.append(sql.SQL("{} = %s").format(sql.Identifier('id')))
                params.append(search_term)

            query = sql.SQL("SELECT * FROM hoorspelen WHERE {} LIMIT %s OFFSET %s").format(sql.SQL(" OR ").join(conditions))
            cursor.execute(query, params + [limit, offset])

        results = cursor.fetchall()
        cursor.close()
        return results

    except Exception as e:
        conn.rollback()
        logging.error(f"An error occurred in execute_search: {e}")
        raise
def zoek_hoorspellen(conn, term):
    def clear_screen():
        print(term.home + term.clear, end='', flush=True)

    try:
        while True:
            clear_screen()
            print("Voer zoekterm in of veld:zoekwoord (ESC om terug te gaan) ", end='', flush=True)
            search_term = ''
            specific_field = None

            while True:
                with term.cbreak():
                    key = term.inkey(timeout=1)

                if not key:
                    continue

                if key.name == 'KEY_ESCAPE':
                    return
                elif key.name == 'KEY_ENTER':
                    break
                elif key.name == 'KEY_BACKSPACE':
                    if search_term:
                        search_term = search_term[:-1]
                        # Move the cursor back, overwrite the character with space, move back again
                        print('\b \b', end='', flush=True)
                elif key.is_sequence:
                    continue
                else:
                    search_term += key
                    print(key, end='', flush=True)

            if ':' in search_term:
                parts = search_term.split(':', 1)
                if parts[0] in valid_fields:
                    specific_field = parts[0]
                    search_term = parts[1]

            offset = 0
            limit = 200

            try:
                results = execute_search(conn, search_term, offset, limit, specific_field)
            except psycopg2.OperationalError as e:
                clear_screen()
                print(f"Zoekopdracht mislukt: {e}")
                print("Druk op een toets om verder te gaan...")
                term.inkey()
                continue

            if not results:
                clear_screen()
                print("Geen resultaten gevonden.")
                print("Druk op een toets om verder te gaan...")
                term.inkey()
                continue

            display_search_results(conn, term, results, search_term, offset, limit)

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print(f"Er is een fout opgetreden: {e}")
        print("Druk op een toets om terug te gaan...")
        term.inkey()

def display_search_results(conn, term, results, search_term, offset, limit):
    current_record = 0
    current_attribute = 0

    while True:
        # Clear the screen and print the header
        print(term.home + term.clear, end='', flush=True)
        print(f"Resultaat {current_record + 1} van {len(results)}")

        # Initialize variables to store cursor position
        selected_line_number = None
        selected_line_length = None

        # Print each attribute
        for i, attribute_name in enumerate(valid_fields):
            value = str(results[current_record][i])

            if i == current_attribute:
                # Selected attribute
                line_content = f"-> {attribute_name}: {value}"
                print(term.bold(line_content))
                # Record the line number and length
                selected_line_number = i + 1  # +1 because of the header line
                selected_line_length = len(line_content)
            else:
                # Other attributes
                line_content = f"   {attribute_name}: {value}"
                print(line_content)

        # After printing all lines, move the cursor to the end of the selected line
        if selected_line_number is not None and selected_line_length is not None:
            # Calculate cursor position
            # Rows and columns start from 0 in term.move()
            cursor_row = selected_line_number
            cursor_col = selected_line_length

            # Move the cursor to the position
            print(term.move(cursor_row, cursor_col), end='', flush=True)

        # Wait for user input
        with term.cbreak():
            key = term.inkey()

        if not key:
            continue

        # Handle key presses
        if key.name == 'KEY_ESCAPE':
            break
        elif key.name == 'KEY_UP':
            current_attribute = (current_attribute - 1) % len(valid_fields)
        elif key.name == 'KEY_DOWN':
            current_attribute = (current_attribute + 1) % len(valid_fields)
        elif key.name == 'KEY_RIGHT':
            if current_record < len(results) - 1:
                current_record += 1
            else:
                current_record = 0  # Loop to the first result
            # current_attribute remains the same
        elif key.name == 'KEY_LEFT':
            if current_record > 0:
                current_record -= 1
            else:
                current_record = len(results) - 1  # Loop to the last result
            # current_attribute remains the same
        elif key.lower() == 'e':
            if valid_fields[current_attribute] != "id":
                edit_field(conn, term, results, current_record, current_attribute)
                # Refresh results after editing
                results = execute_search(conn, search_term, offset, limit)
        elif key.name == 'KEY_ENTER':
            # Optional: Handle Enter key if needed
            pass

def edit_field(conn, term, results, current_record, current_attribute):
    def clear_screen():
        print(term.home + term.clear, end='', flush=True)

    clear_screen()
    field_name = valid_fields[current_attribute]
    current_value = results[current_record][current_attribute]

    print(f"Bewerk {field_name}")
    print(f"Huidige waarde: {current_value}")
    print("Voer nieuwe waarde in (Enter om te bewaren, ESC om te annuleren):")

    new_value = ''
    while True:
        with term.cbreak():
            key = term.inkey()

        if not key:
            continue

        if key.name == 'KEY_ESCAPE':
            return
        elif key.name == 'KEY_ENTER':
            break
        elif key.name == 'KEY_BACKSPACE':
            if new_value:
                new_value = new_value[:-1]
                print('\b \b', end='', flush=True)
        elif key.is_sequence:
            continue
        else:
            new_value += key
            print(key, end='', flush=True)

    if new_value == '':
        new_value = current_value

    if new_value != current_value:
        try:
            cursor = conn.cursor()
            update_query = sql.SQL("UPDATE hoorspelen SET {} = %s WHERE id = %s").format(sql.Identifier(field_name))
            cursor.execute(update_query, (new_value, results[current_record][0]))
            conn.commit()
            print("\nRecord succesvol bijgewerkt.")
            # Update the value in the results
            results[current_record] = list(results[current_record])
            results[current_record][current_attribute] = new_value
        except Exception as e:
            conn.rollback()
            print(f"\nFout bij het bijwerken van het record: {e}")
        finally:
            cursor.close()

    print("Druk op een toets om verder te gaan...")
    term.inkey()

def toon_totaal_hoorspellen(conn, term):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM hoorspelen")
        total = cursor.fetchone()[0]

        # Clear the screen and display the information
        print(term.home + term.clear, end='')
        info_line = f"Totaal aantal hoorspellen: {total}. Druk op Toets."
        print(info_line, end='')

        # Move the cursor to the end of the information line
        print(term.move_x(len(info_line)), end='', flush=True)

        # Wait for a keypress
        with term.cbreak():
            term.inkey()

    except Exception as e:
        print(term.home + term.clear, end='')
        error_message = f"Er is een fout opgetreden: {e}. Druk op een toets."
        print(error_message, end='')
        print(term.move_x(len(error_message)), end='', flush=True)
        with term.cbreak():
            term.inkey()

    finally:
        if cursor:
            cursor.close()

def geschiedenis(conn, term):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hoorspelen ORDER BY id DESC LIMIT 10")
        results = cursor.fetchall()
        results = list(reversed(results))

        if not results:
            print(term.clear())
            print("Geen hoorspelen gevonden.")
            input("Druk op Enter om verder te gaan...")
            return

        current_record = 0
        current_attribute = 0
        attribute_names = [desc[0] for desc in cursor.description]

        def display_record():
            print(term.home + term.clear, end='')
            for i, attribute_name in enumerate(attribute_names):
                value = str(results[current_record][i])
                if i == current_attribute:
                    print(f"-> {attribute_name}: {value}")
                else:
                    print(f"   {attribute_name}: {value}")
            
            selected_text = f"-> {attribute_names[current_attribute]}: {results[current_record][current_attribute]}"
            print(term.move_yx(current_attribute, len(selected_text)), end='', flush=True)

        def get_input_with_escape(prompt):
            print(prompt, end='', flush=True)
            buffer = []
            while True:
                with term.cbreak():
                    key = term.inkey()
                if key.name == 'KEY_ESCAPE':
                    return None
                elif key.name == 'KEY_ENTER':
                    return ''.join(buffer)
                elif key.name == 'KEY_BACKSPACE':
                    if buffer:
                        buffer.pop()
                        print('\b \b', end='', flush=True)
                elif key.is_sequence:
                    continue
                else:
                    buffer.append(key)
                    print(key, end='', flush=True)

        while True:
            display_record()

            with term.cbreak():
                key = term.inkey()

            if key.name == 'KEY_ESCAPE':
                break
            elif key.name == 'KEY_UP':
                current_attribute = (current_attribute - 1) % len(attribute_names)
            elif key.name == 'KEY_DOWN':
                current_attribute = (current_attribute + 1) % len(attribute_names)
            elif key.name == 'KEY_RIGHT':
                if current_record < len(results) - 1:
                    current_record += 1
            elif key.name == 'KEY_LEFT':
                if current_record > 0:
                    current_record -= 1
            elif key == 'e':
                if attribute_names[current_attribute] != 'id':
                    print(term.clear())
                    current_value = str(results[current_record][current_attribute])
                    print(f"Current value: {current_value}")
                    new_value = get_input_with_escape(f"New value for {attribute_names[current_attribute]} (press Enter to keep current, ESC to cancel): ")

                    if new_value is None:  # User pressed ESC
                        continue
                    elif new_value == "":  # User pressed Enter without input
                        continue

                    if attribute_names[current_attribute] == 'datum' and not validate_date(new_value):
                        print("Verkeerd formaat datum. Gebruik YYYY/MM/DD.")
                        input("Druk op Enter om verder te gaan...")
                        continue

                    try:
                        update_query = sql.SQL("UPDATE hoorspelen SET {} = %s WHERE id = %s").format(sql.Identifier(attribute_names[current_attribute]))
                        cursor.execute(update_query, (new_value, results[current_record][0]))
                        conn.commit()
                        results[current_record] = list(results[current_record])
                        results[current_record][current_attribute] = new_value
                        print("Record updated successfully.")
                    except Exception as e:
                        conn.rollback()
                        print(f"Error updating record: {e}")
                    
                    input("Druk op Enter om verder te gaan...")

    except Exception as e:
        print(term.clear())
        print(f"Er is een fout opgetreden: {e}")
        input("Druk op Enter om verder te gaan...")
    finally:
        if cursor:
            cursor.close()

# Gmail-related functions
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def gmail_service():
    creds = None
    service = None

    # Ensure that the token.pickle and credentials file paths are correct
    token_path = 'token.pickle'
    credentials_path = "client_secret_909008488627-c1gda8u30p8ssck0rsrcrs46p88mimb2.apps.googleusercontent.com.json"

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # Check if the credentials are expired or missing
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if os.path.exists(credentials_path):
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                print(f"Error: Kan de login gegevens niet vinden '{credentials_path}'.")
                return None

        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    if creds:
        # Build the service after ensuring credentials are valid
        service = build('gmail', 'v1', credentials=creds)
    else:
        print("Geen valide login.")

    return service

def create_message_with_attachment(sender, to, subject, message_text, csv_path):
    """
    Create a message for an email with an attachment.
    """
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    msg = MIMEText(message_text)
    message.attach(msg)

    content_type, encoding = mimetypes.guess_type(csv_path)
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    with open(csv_path, 'rb') as fp:
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        encoders.encode_base64(msg)
    
    msg.add_header('Content-Disposition', 'attachment', filename=os.path.basename(csv_path))
    message.attach(msg)
    
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def send_message(service, user_id, message):
    """
    Send an email message.
    """
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print('Message Id: %s' % message['id'])
    except HttpError as error:
        print(f'An error occurred: {error}')

def export_and_email_backup(service, conn, email_address):
    csv_path = export_function(conn)
    if csv_path:
        sender = "me"
        to = email_address  # Ensure this is the recipient's email address
        subject = "Database Backup"
        message_text = "Attached is the database backup."
        message = create_message_with_attachment(sender, to, subject, message_text, csv_path)
        send_message(service, "me", message)
    else:
        print("Export mislukt. Email niet verzonden.")

if __name__ == "__main__":
    term = blessed.Terminal()
    conn = get_db_connection()
    initialize_db(conn)
    main_menu(conn, term)
    conn.close()