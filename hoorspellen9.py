import sys
import msvcrt
import sqlite3
import os
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
import pickle
import os.path
from google.auth.transport.requests import Request
import pickle
import os.path
import mimetypes
import logging
import difflib


os.environ['SSL_CERT_FILE'] = certifi.where()

db_file = 'hoorspel.db'

logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s')


def geavanceerd_submenu():
    options = [
        ("Importeren", lambda: import_function('hoorspel.db')),
        ("Exporteren", lambda: export_function('hoorspel.db')),
        ("DB Legen", lambda: clear_db_function('hoorspel.db')),
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

def main_menu():
    def return_to_menu_callback():
        main_menu()
    #global db_file
    options = [
        ("Voeg Toe", lambda: voeg_toe(db_file, return_to_menu_callback)),
        ("Bewerk Hoorspellen", lambda: bewerk_hoorspel(db_file)),
        ("Zoek Hoorspellen", lambda: zoek_hoorspellen(db_file)),
        ("Totaal", lambda: toon_totaal_hoorspellen(db_file)),
        ("Geschiedenis", lambda: geschiedenis(db_file)),
        ("Geavanceerd", geavanceerd_submenu),  # No argument passed to geavanceerd_submenu
        ("Afsluiten", lambda: sys.exit())
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

        if key == b'\x1b':  # Escape key
            clear_screen()
            print("\nBackup aan het maken, moment geduld.", end='', flush=True)
            email_message = create_message_with_attachment("sjefsdatabasebackups@gmail.com", "sjefsdatabasebackups@gmail.com", "Hoorspelen backup", "De backup van de hoorspelen", csv_path=export_function(db_file))
            send_message(service, "me", email_message)
            sys.exit()
        elif key == b'H':  # Up arrow key
            current_option = (current_option - 1) % len(options)  # Move left in the list
        elif key == b'P':  # Down arrow key
            current_option = (current_option + 1) % len(options)  # Move right in the list
        elif key == b'\r':  # Enter key
            if current_option == len(options) - 1:  # Last option is "Afsluiten"
                email_message = create_message_with_attachment("sjefsdatabasebackups@gmail.com", "sjefsdatabasebackups@gmail.com", "Hoorspelen backup", "De backup van de hoorspelen", csv_path=export_function(db_file))
                send_message(service, "me", email_message)
                sys.exit()
            else:
                options[current_option][1]() # Execute the selected option's function  # Execute the selected option's function
                os.system('cls' if os.name == 'nt' else 'clear')
                
def import_function(db_file):
    filename = input("Voer het pad naar het CSV-bestand in: ")
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            # Optionally, skip the header if your CSV file includes one
            next(reader, None)  # This skips the first line of the CSV which usually contains the header
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            for row in reader:
                # Exclude the first column (id) from the row if your CSV includes it
                data_to_insert = row[1:]  # Adjust this line if the structure is different
                cursor.execute('''
                    INSERT INTO hoorspelen (auteur, titel, regie, datum, omroep, bandnr, vertaling, duur, bewerking, genre, productie, themareeks, delen, bijzverm, taal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', data_to_insert)
            conn.commit()
            conn.close()
        print("Importeren gelukt.")
    except Exception as e:
        print(f"Er is een fout opgetreden: {e}")

    input("Druk op Enter om verder te gaan...")

def export_function(db_file):
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")  # Replacing ':' with '_'
    filename = f"hoorspellendb{timestamp}.csv"
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM hoorspelen")
            writer = csv.writer(csvfile)
            writer.writerow([i[0] for i in cursor.description])  # Write headers
            writer.writerows(cursor.fetchall())
            conn.close()
        print(f"Exporteren gelukt. Bestand opgeslagen als: {filename}")
    except Exception as e:
        print(f"Er is een fout opgetreden: {e}")
        os.system('cls' if os.name == 'nt' else 'clear')

    input("Druk op Enter om verder te gaan...")

def clear_db_function(db_file):
    confirm = input("Weet u zeker dat u alle gegevens wilt wissen? Type 'ja' om te bevestigen: ")
    if confirm.lower() == 'ja':
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hoorspelen")
            conn.commit()
            conn.close()
            print("Database geleegd.")
        except Exception as e:
            print(f"Er is een fout opgetreden: {e}")
    else:
        print("Wissen geannuleerd.")

    input("Druk op Enter om verder te gaan...")

# Define the other functions (add_entry, view_entries, search_entries) here
def initialize_db(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hoorspelen (
            id INTEGER PRIMARY KEY,
            auteur TEXT,
            titel TEXT,
            regie TEXT,
            datum TEXT,
            omroep TEXT,
            bandnr TEXT,
            vertaling TEXT,
            duur REAL,
            bewerking TEXT,
            genre TEXT,
            productie TEXT,
            themareeks TEXT,
            delen INTEGER,
            bijzverm TEXT,
            taal TEXT
        )
    ''')
    conn.commit()
    conn.close()

def validate_date(date_string):
    try:
        # Parse the date string to validate if it's in a valid format
        datetime.datetime.strptime(date_string, '%Y/%m/%d')
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

def voeg_toe(db_file, return_to_menu_callback):
    logging.debug('voeg_toe called with db_file=%s', db_file)

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute('SELECT MAX(id) FROM hoorspelen')
    max_id = cursor.fetchone()[0]
    new_id = max_id + 1 if max_id is not None else 1

    logging.debug('new_id=%s', new_id)

    fields = ['auteur', 'titel', 'regie', 'datum', 'omroep', 'bandnr', 'vertaling', 'duur', 'bewerking', 'genre', 'productie', 'themareeks', 'delen', 'bijzverm', 'taal']
    record = {field: "" for field in fields}
    cursor_positions = {field: 0 for field in fields}  # Track cursor position for each field
    index = 0

    def print_form():
        clear_screen()
        for i, field in enumerate(fields):
            prefix = "->" + field + ": " if i == index else "   " + field + ": "
            field_text = record[field]
            print(f"{prefix}{field_text}")
        # Move cursor up to the line of the current field
        print('\033[F' * (len(fields) - index), end='')  
        # Move cursor right to the end of "->field: " text and the input text
        print('\033[C' * (len('->') + len(fields[index]) + len(': ') + len(record[fields[index]])), end='', flush=True)

    while True:
        print_form()

        key = msvcrt.getch()
        if key == b'\xe0':  # Arrow keys
            key = msvcrt.getch()
            if key == b'H':  # Up arrow key
                index = max(0, index - 1)
            elif key == b'P':  # Down arrow key
                index = min(len(fields) - 1, index + 1)
        elif key == b'd':  # Save record
            record_values = [new_id] + [record[field] for field in fields]
            placeholders = ', '.join(['?'] * (len(fields) + 1))
            cursor.execute(f'INSERT INTO hoorspelen (id, {", ".join(fields)}) VALUES ({placeholders})', record_values)
            conn.commit()
            logging.debug('Record added: %s', record_values)
            print("Record added successfully. Press any key to continue.")
            msvcrt.getch()
            break
        elif key == b'\x1b':  # Escape key
            break
        elif key == b'\x08':  # Backspace
            field = fields[index]
            if cursor_positions[field] > 0:
                # Remove character at cursor position - 1 and move cursor back
                record[field] = record[field][:cursor_positions[field] - 1] + record[field][cursor_positions[field]:]
                cursor_positions[field] -= 1
        else:
            field = fields[index]
            char = key.decode() if key else ''
            if char.isprintable():
                # Insert character at cursor position and move cursor forward
                record[field] = record[field][:cursor_positions[field]] + char + record[field][cursor_positions[field]:]
                cursor_positions[field] += 1

    conn.close()
    return_to_menu_callback()

def read_input():
    """
    Reads input from the user, displaying each character as it's typed.
    If the Escape key is pressed, returns None.
    """
    input_str = []
    while True:
        key = msvcrt.getch()
        if key == b'\r':  # Enter key
            print()  # Move to the next line
            return ''.join(input_str)
        elif key == b'\x1b':  # Escape key
            return None
        elif key == b'\x08':  # Backspace
            if input_str:
                input_str.pop()
                sys.stdout.write('\b \b')  # Remove the character from the console
        elif key in [b'\x00', b'\xe0']:  # Special keys (like arrow keys, function keys)
            msvcrt.getch()  # Fetch the next byte and ignore it
        else:
            try:
                char = key.decode()
                input_str.append(char)
                sys.stdout.write(char)  # Display the character
            except UnicodeDecodeError:
                continue  # Ignore undecodable characters
        sys.stdout.flush()  # Ensure the console is updated

def handle_input(prompt):
    print(prompt, end='', flush=True)
    user_input = read_input()
    return user_input

def bewerk_hoorspel(db_file):
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear the screen
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    entry_id = handle_input("Voer de ID in van de inzending die je wilt bewerken: ")
    if entry_id is None:
        conn.close()
        return
    
    try:
        entry_id = int(entry_id)
    except ValueError:
        print("Ongeldige invoer. Probeer opnieuw")
        conn.close()
        return
    
    cursor.execute("SELECT * FROM hoorspelen WHERE id = ?", (entry_id,))
    entry = cursor.fetchone()

    if entry:
        print("Huidige inzending: ", entry)
        # Gather new data from user input
        new_auteur = handle_input("Nieuwe Auteur (laat leeg om huidige te behouden): ")
        if new_auteur is None: return
        new_titel = handle_input("Nieuwe Titel (laat leeg om huidige te behouden): ")
        if new_titel is None: return
        new_regie = handle_input("Nieuwe regie (laat leeg om huidige te behouden): ")
        if new_regie is None: return
        new_datum = handle_input("Nieuwe datum (laat leeg om huidige te behouden): ")
        if new_datum is None: return
        new_omroep = handle_input("Nieuwe omroep (laat leeg om huidige te behouden): ")
        if new_omroep is None: return
        new_bandnr = handle_input("Nieuwe bandnr (laat leeg om huidige te behouden): ")
        if new_bandnr is None: return
        new_vertaling = handle_input("Nieuwe vertaling (laat leeg om huidige te behouden): ")
        if new_vertaling is None: return
        new_duur = handle_input("Nieuwe duur (laat leeg om huidige te behouden): ")
        if new_duur is None: return
        new_bewerking = handle_input("Nieuwe bewerking (laat leeg om huidige te behouden): ")
        if new_bewerking is None: return
        new_genre = handle_input("Nieuwe genre (laat leeg om huidige te behouden): ")
        if new_genre is None: return
        new_productie = handle_input("Nieuwe productie (laat leeg om huidige te behouden): ")
        if new_productie is None: return
        new_themareeks = handle_input("Nieuwe themareeks (laat leeg om huidige te behouden): ")
        if new_themareeks is None: return
        new_delen = handle_input("Nieuwe delen (laat leeg om huidige te behouden): ")
        if new_delen is None: return
        new_bijzverm = handle_input("Nieuwe bijzverm (laat leeg om huidige te behouden): ")
        if new_bijzverm is None: return
        new_taal = handle_input("Nieuwe taal (laat leeg om huidige te behouden): ")
        if new_taal is None: return
        # ... similarly gather all other fields, leaving blank to keep current

        cursor.execute('''
            UPDATE hoorspelen 
            SET auteur = COALESCE(NULLIF(?, ''), auteur),
                titel = COALESCE(NULLIF(?, ''), titel),
                regie = COALESCE(NULLIF(?, ''), regie),
                datum = COALESCE(NULLIF(?, ''), datum),
                omroep = COALESCE(NULLIF(?, ''), omroep),
                bandnr = COALESCE(NULLIF(?, ''), bandnr),
                vertaling = COALESCE(NULLIF(?, ''), vertaling),
                duur = COALESCE(NULLIF(?, ''), duur),
                bewerking = COALESCE(NULLIF(?, ''), bewerking),
                genre = COALESCE(NULLIF(?, ''), genre),
                productie = COALESCE(NULLIF(?, ''), productie),
                themareeks = COALESCE(NULLIF(?, ''), themareeks),
                delen = COALESCE(NULLIF(?, ''), delen),
                bijzverm = COALESCE(NULLIF(?, ''), bijzverm),
                taal = COALESCE(NULLIF(?, ''), taal)
            WHERE id = ?
        ''', (new_auteur, new_titel, new_regie, new_datum, new_omroep, new_bandnr, new_vertaling, new_duur, new_bewerking, new_genre, new_productie, new_themareeks, new_delen, new_bijzverm, new_taal, entry_id))

        conn.commit()
        print("Inzending succesvol bijgewerkt.")
    else:
        print("Inzending niet gevonden.")

    
    input("Druk op Enter om verder te gaan...")
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear the screen again before returning to the menu

# Other parts of your script remain unchanged...
valid_fields = [
    "id", "auteur", "titel", "regie", "datum", "omroep", "bandnr",
    "vertaling", "duur", "bewerking", "genre", "productie",
    "themareeks", "delen", "bijzverm", "taal"
]

# Clears the terminal screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def save_changes_to_database(db_file, record_id, field_name, new_value):
    print("save changes to database")
    try:
        with sqlite3.connect(db_file) as conn:
            conn.set_trace_callback(print)  # Optionally set a trace callback to debug SQL statements
            cursor = conn.cursor()
            query = f"UPDATE hoorspelen SET {field_name} = ? WHERE id = ?"
            cursor.execute(query, (new_value, record_id))
            # De connectie commit is hier niet nodig omdat `with` automatisch commit uitvoert als er geen uitzonderingen zijn.
    except sqlite3.Error as e:
        print(f"A SQLite error occurred: {e}")

def edit_current_field(db_file, current_record, current_attribute, attribute_names, results):
    clear_screen()
    # Display the initial prompt with oud (old value) and nieuw (new value) placeholders
    old_value = results[current_record][current_attribute]
    print(f"\nEdit mode: {attribute_names[current_attribute]}. oud:{old_value}, nieuw:", end='', flush=True)
    
    new_value = []
    while True:
        key = msvcrt.getch()
        if key == b'\r':  # Enter key
            new_value_str = ''.join(new_value)  # Convert list of characters to a string
            break
        elif key == b'\x1b':  # Escape key
            clear_screen()
            print("\nEdit canceled.")
            return  # Exit the function early if edit is canceled
        elif key == b'\x08':  # Backspace
            if new_value:
                new_value.pop()
                print("\b \b", end='', flush=True)  # Move back, print space, move back again
        else:
            try:
                char = key.decode()
                if char.isprintable():  # Ensure the character is printable before appending
                    new_value.append(char)
                    print(char, end='', flush=True)  # Display the character
            except UnicodeDecodeError:
                continue  # Ignore undecodable characters

    # Proceed with saving changes and other logic after input is complete
    field_name = attribute_names[current_attribute]
    record_id = results[current_record][0]  # Assuming the ID is always at index 0 in your results

    if new_value_str:
        print(f"\nAttempting to update record ID: {record_id} with {field_name} = {new_value_str}")
        save_changes_to_database(db_file, record_id, field_name, new_value_str)
        print("Changes saved.")
    else:
        print("\nNo changes made.")

    input("\nPress any key to continue...")  # Wait for user input before proceeding
    clear_screen()

    # Clear screen and re-print the updated record for continuity
    for index, attribute in enumerate(attribute_names):
        print(f"   {attribute}: {results[current_record][index]}")

# Corrects a field name based on the list of valid fields
def correct_field_name(field):
    if field in valid_fields:
        return field
    matches = difflib.get_close_matches(field, valid_fields, n=1, cutoff=0.6)
    return matches[0] if matches else None

def execute_search(db_file, field1, searchword1, field2, searchword2, offset, limit):
    logging.debug("Starting execute_search function")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        logging.info(f"Connected to database: {db_file}")

        # Initialize the query and params
        query = "SELECT * FROM hoorspelen WHERE "
        params = []

        # Add conditions for the first field and search word
        if field1 and searchword1:
            query += f"{field1} LIKE ?"
            params.append(f"%{searchword1}%")
            logging.debug(f"Added search condition for field1: {field1}")

        # Add conditions for the second field and search word if provided
        if field2 and searchword2:
            query += f" AND {field2} LIKE ?"
            params.append(f"%{searchword2}%")
            logging.debug(f"Added search condition for field2: {field2}")

        # Add LIMIT and OFFSET to the query to handle pagination
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        logging.debug("Added LIMIT and OFFSET to the query")

        # Execute the query
        cursor.execute(query, params)
        results = cursor.fetchall()
        logging.info("Query executed successfully")

        # Close the connection to the database
        conn.close()
        logging.debug("Database connection closed")

        return results
    except Exception as e:
        logging.error(f"An error occurred in execute_search: {e}")
        raise

# Other helper functions like clear_screen, save_changes_to_database,
# edit_current_field, correct_field_name, execute_search remain unchanged...

def parse_input(input_str):
    # This is just an example function. You'll need to implement the actual parsing logic.
    try:
        parts = input_str.split(',')
        parsed_data = {}
        for part in parts:
            field, value = part.split(':')
            parsed_data[field.strip()] = value.strip()
        return parsed_data
    except Exception as e:
        logging.error(f"Failed to parse input: {e}")
        return None

# Configure logging
logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s')

# Define valid_fields with the list of fields you want to display
valid_fields = ["auteur", "titel", "regie", "datum", "omroep", "bandnr", "vertaling", "duur", "bewerking", "genre", "productie", "themareeks", "delen", "bijzverm", "taal"]

# Placeholder for the clear_screen function.
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def zoek_hoorspellen(db_file):
    clear_screen()
    try:
        while True:
            logging.debug("Prompting for search input")
            clear_screen()
            print("Voer zoekopdracht in (Veld1:Zoekwoord1,Veld2:Zoekwoord2): ", end='', flush=True)
            input_str = ''
            while True:
                char = msvcrt.getch()
                if char == b'\x1b':  # Escape key
                    clear_screen()
                    logging.debug("Escape key pressed - exiting function")
                    return  # Exit function and return to main menu
                elif char == b'\r':  # Enter key
                    logging.debug("Enter key pressed - processing input")
                    break
                elif char == b'\x08':  # Backspace key
                    if len(input_str) > 0:
                        input_str = input_str[:-1]  # Remove the last character
                        print('\b \b', end='', flush=True)  # Clear the character on the screen
                else:
                    try:
                        print(char.decode(), end='', flush=True)
                        input_str += char.decode()
                    except UnicodeDecodeError:
                        logging.warning("UnicodeDecodeError encountered - ignoring undecodable characters")
                        continue

            logging.debug(f"Input string: {input_str}")
            parsed_input = parse_input(input_str.strip())
            if not parsed_input:
                logging.debug("Input parsing failed - incorrect format")
                clear_screen()
                print("\nVerkeerd formaat. Gebruik 'veld:waarde'. Druk op ENTER om verder te gaan.", end='')
                input()
                continue

            field1, searchword1 = next(iter(parsed_input.items()))
            logging.debug(f"field1: {field1}, searchword1: {searchword1}")
            parsed_input.pop(field1)
            field2, searchword2 = next(iter(parsed_input.items()), (None, None))
            logging.debug(f"field2: {field2}, searchword2: {searchword2}")

            offset = 0
            limit = 200

            try:
                logging.debug(f"Executing search with field1={field1}, searchword1={searchword1}, field2={field2}, searchword2={searchword2}")
                results = execute_search(db_file, field1, searchword1, field2, searchword2, offset=offset, limit=limit)
            except sqlite3.OperationalError as e:
                logging.error(f"Zoekopdracht mislukt: {e}")
                clear_screen()
                print("\nVerkeerd formaat. Gebruik 'veld:waarde'. Druk op ENTER om verder te gaan.", end='')
                input()
                continue

            if not results:
                logging.debug("No results found for the search criteria")
                clear_screen()
                print("Geen resultaten gevonden. Druk op ENTER om door te gaan of ESCAPE om te stoppen.")
                action_key = msvcrt.getch()
                if action_key == b'\x1b':  # ESC key
                    continue
                else:
                    return

            current_record = 0
            current_attribute = 0  # Start enumeration from 1
            logging.debug("Starting the record viewing loop")
            while True:
                clear_screen()
                for index, attribute in enumerate(valid_fields, start=0):
                    value = results[current_record][index - 0]  # Adjusted index
                    if index == current_attribute:
                        print(f"-> {attribute}: {value}")
                    else:
                        print(f"   {attribute}: {value}")
                print("\033[{}A\033[{}C".format(len(valid_fields) - current_attribute, len(f"-> {valid_fields[current_attribute]}: {results[current_record][current_attribute]}")), end='', flush=True)
                key = msvcrt.getch()
                if key in [b'\x00', b'\xe0']:  # Arrow keys are preceded by these bytes
                    key = msvcrt.getch()
                if key == b'H':  # Up arrow key
                    current_attribute = (current_attribute - 1) % len(valid_fields)  # Wrap around using modulo
                elif key == b'P':  # Down arrow key
                    current_attribute = (current_attribute + 1) % len(valid_fields)  # Wrap around using modulo
                elif key == b'M':  # Right arrow key
                    if current_record < len(results) - 1:
                        current_record += 1
                        current_attribute = 0  # Reset attribute index when changing records
                elif key == b'K':  # Left arrow key
                    if current_record > 0:
                        current_record -= 1
                        current_attribute = 0  # Reset attribute index when changing records
                elif key == b'e':  # 'e' key for edit
                    logging.debug("Edit key pressed - editing current field")
                    if valid_fields[current_attribute] == "id":
                        print("The 'id' field is not editable.")
                    else:
                        try:
                            edit_current_field(db_file, current_record, current_attribute, valid_fields, results)
                            results = execute_search(db_file, field1, searchword1, field2, searchword2, offset=offset, limit=limit)
                        except Exception as e:
                            logging.error(f"Error in edit_current_field: {e}")
                            print(f"Error in edit_current_field: {e}")
                elif key == b'\x1b':  # Escape key
                    logging.debug("Escape key pressed - returning to search prompt")
                    break  # Break out of the inner loop to go back to the search prompt
            
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print(f"Er is een fout opgetreden: {e}")
    # print("\033[1A", end='', flush=True)  # Voorbeeld ANSI Escape code om de cursor omhoog te verplaatsen


valid_fields = [
    "id","auteur", "titel", "regie", "datum", "omroep", "bandnr", 
    "vertaling", "duur", "bewerking", "genre", "productie", 
    "themareeks", "delen", "bijzverm", "taal"
]

# DB file path
db_file = 'hoorspel.db'
clear_screen()
# Laat het totaal aantal hoorspellen zien.
def toon_totaal_hoorspellen(db_file='hoorspel.db'):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM hoorspelen")
    total = cursor.fetchone()[0]
    conn.close()
    
    clear_screen()
    input(f"Totaal aantal hoorspellen: {total}. Druk op Enter om terug te gaan naar het hoofdmenu...")
    clear_screen() #     

# De gesciedenis functie in het hoofdmenu. Laat de laatste 10 toegevoegde records zien.
def geschiedenis(db_file):
    clear_screen()
    # Database connection setup
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM hoorspelen ORDER BY id DESC LIMIT 10")
    results = cursor.fetchall()
    results = list(reversed(results))  # Reverse to start with the most recently added entry

    if not results:
        print("Geen hoorspellen gevonden.")
        input("\nDruk op ENTER om verder te gaan...")
        return

    current_record = 0
    current_attribute = 0
    attribute_names = [description[0] for description in cursor.description]

    # ...

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console

        for index, attribute in enumerate(attribute_names):
            if index == current_attribute:
                print(f"-> {attribute}: {results[current_record][index]}\n", end='', flush=True)
            else:
                print(f"   {attribute}: {results[current_record][index]}")

        # Move the cursor back to the line of the selected field
        print("\033[{}A".format(len(attribute_names) - current_attribute), end='', flush=True)

        key = msvcrt.getch()
        if key in [b'\x00', b'\xe0']:
            key = msvcrt.getch()

        if key == b'\x1b':
            break
        elif key == b'H':
            current_attribute = (current_attribute - 1) % len(attribute_names)
        elif key == b'P':
            current_attribute = (current_attribute + 1) % len(attribute_names)
        elif key == b'M':
            if current_record < len(results) - 1:
                current_record += 1
                current_attribute = 0  # Reset attribute index when changing records
        elif key == b'K':
            if current_record > 0:
                current_record -= 1
                current_attribute = 0  # Reset attribute index when changing records

        # Move the cursor back to the top of the screen before the next loop iteration
        print(f"\033[{len(attribute_names)}A", end='', flush=True)

    conn.close()
    clear_screen()

def export_function(db_file):
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")  # Replacing ':' with '_'
    filename = f"hoorspellendb_{timestamp}.csv"
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM hoorspelen")
            writer = csv.writer(csvfile)
            writer.writerow([i[0] for i in cursor.description])  # Write headers
            writer.writerows(cursor.fetchall())
            conn.close()
            clear_screen()
            print(f"Export succesvol bestand opgeslagen als: {filename}")  # Optionally move the cursor up one line])
            return filename  # Return the file path of the exported CSV file
    except Exception as e:
        print(f"Er is een fout opgetreden: {e}")
        return None  # Return None to indicate export failure

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def gmail_service():
    creds = None
    service = None  # Initialize `service` to `None`

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
# Path to your credentials JSON file
CREDENTIALS_FILE = 'C:\\Users\\kevinvanosch\\Desktop\\hoorspellen\\client_secret_909008488627-c1gda8u30p8ssck0rsrcrs46p88mimb2.apps.googleusercontent.com.json'

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

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

def export_and_email_backup(service, db_file, email_address):
    csv_path = export_function(db_file)
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
    initialize_db("hoorspel.db")
    db_file = 'hoorspel.db'
    email_address = 'sjefsdatabasebackups@gmail.com'
    service = gmail_service()
    main_menu()
    if service:
        export_and_email_backup(service, db_file, email_address)
    else:
        print("Failed to initialize Gmail service.")
