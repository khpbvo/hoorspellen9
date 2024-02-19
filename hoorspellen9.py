import sys
import msvcrt
import sqlite3
import os
import csv
import datetime
from email.message import EmailMessage
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
import pdb
import logging
import re
import difflib
import curses


os.environ['SSL_CERT_FILE'] = certifi.where()

db_file = 'hoorspel.db'

logging.basicConfig(level=logging.DEBUG, filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s')
logging.debug('This is a debug message')

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
    logging.debug('This is a debug message')
    #global db_file
    options = [
        ("Voeg Toe", lambda: voeg_toe(db_file)),
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

def voeg_toe(db_file):
    os.system('cls' if os.name == 'nt' else 'clear')
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    auteur = handle_input("Auteur: ")
    if auteur is None: 
        conn.close()
        return

    titel = handle_input("Titel: ")
    if titel is None: 
        conn.close()
        return

    regie = handle_input("Regie: ")
    if regie is None: 
        conn.close()
        return

    while True:
        datum = handle_input("Datum (yyyy/mm/dd): ")
        if datum is None: 
            conn.close()
            return
        if validate_date(datum):
            break
        else:
            print("Ongeldige datum. Voer de datum in het formaat yyyy/mm/dd.")

    omroep = handle_input("Omroep: ")
    if omroep is None: 
        conn.close()
        return
    
    bandnr = handle_input("Bandnummer: ")
    if bandnr is None: 
        conn.close()
        return

    vertaling = handle_input("Vertaling: ")
    if vertaling is None: 
        conn.close()
        return
    
    duur = handle_input("Duur: ")
    if duur is None: 
        conn.close()
        return
    
    bewerking = handle_input("Bewerking: ")
    if bewerking is None: 
        conn.close()
        return
    
    genre = handle_input("Genre: ")
    if genre is None: 
        conn.close()
        return
    
    productie = handle_input("Productie: ")
    if productie is None: 
        conn.close()
        return
    
    themareeks = handle_input("Themareeks: ")
    if themareeks is None: 
        conn.close()
        return
    
    delen = handle_input("Delen: ")
    if delen is None: 
        conn.close()
        return
    
    bijzverm = handle_input("Bijzverm: ")
    if bijzverm is None: 
        conn.close()
        return
    
    taal = handle_input("Taal: ")
    if taal is None: 
        conn.close()
        return
    
    cursor.execute('''
        INSERT INTO hoorspelen (auteur, titel, regie, datum, omroep, bandnr, vertaling, duur, bewerking, genre, productie, themareeks, delen, bijzverm, taal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (auteur, titel, regie, datum, omroep,bandnr, vertaling, duur, bewerking, genre, productie, themareeks, delen, bijzverm, taal))

    conn.commit()
    conn.close()
    print("Inzending succesvol toegevoegd.")
    input("Druk op Enter om verder te gaan...")  # Wait for user to read the message

def handle_input(prompt):
    print(prompt, end='', flush=True)
    user_input = read_input()
    return user_input


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

# Clears the terminal screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# List of valid fields for the database
valid_fields = [
    "auteur", "titel", "regie", "datum", "omroep", "bandnr",
    "vertaling", "duur", "bewerking", "genre", "productie",
    "themareeks", "delen", "bijzverm", "taal"
]

# Corrects a field name based on the list of valid fields
def correct_field_name(field):
    if field in valid_fields:
        return field
    matches = difflib.get_close_matches(field, valid_fields, n=1, cutoff=0.6)
    return matches[0] if matches else None

# Executes a search query against the database
def execute_search(db_file, field1, searchword1, field2=None, searchword2=None, offset=0, limit=10):
    logging.debug('Starting search execution')
    conn = None
    results = []

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Assuming 'valid_fields' is a list of all valid field names
        if field1 not in valid_fields:
            logging.error(f"Invalid field: {field1}")
            return results

        # Select all fields for the record
        query = "SELECT auteur, titel, regie, datum, omroep, bandnr, vertaling, duur, bewerking, genre, productie, themareeks, delen, bijzverm, taal FROM hoorspelen WHERE "
        query += f"{field1} LIKE ?"
        params = [f'%{searchword1}%']

        if field2 and searchword2 and field2 in valid_fields and field2 != field1:
            query += f" AND {field2} LIKE ?"
            params.append(f'%{searchword2}%')

        query += " ORDER BY id ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        logging.debug(f"Executing query: {query}")
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        logging.debug(f"Query executed. Number of results fetched: {len(results)}")
    except sqlite3.Error as e:
        logging.error(f'A SQLite error occurred: {e}')
        return None
    finally:
        if conn:
            conn.close()

    return results


# Parses user input into a dictionary of field-value pairs
def parse_input(input_str):
    parsed_input = {}
    matches = re.findall(r'(\w+):([^,]+)', input_str)
    for field, value in matches:
        corrected_field = correct_field_name(field)
        if corrected_field:
            parsed_input[corrected_field] = value.strip()
        else:
            logging.error(f"Invalid field: {field}. Valid fields are: {', '.join(valid_fields)}")
            return None
    return parsed_input

# Main function to perform the interactive search
def zoek_hoorspellen(db_file):
    clear_screen()
    try:
        while True:
            print("Voer zoekopdracht in (Veld1:Zoekwoord1,Veld2:Zoekwoord2): ", end='', flush=True)
            input_str = ''
            # Read input character by character to detect Escape key
            while True:
                char = msvcrt.getch()
                if char == b'\x1b':  # Escape key
                    return  # Exit function and return to main menu
                elif char == b'\r':  # Enter key
                    break  # Exit the character reading loop to process input
                else:
                    # Echo character to console and add to input string
                    try:
                        print(char.decode(), end='', flush=True)
                        input_str += char.decode()
                    except UnicodeDecodeError:
                        continue  # Ignore undecodable characters

            parsed_input = parse_input(input_str.strip())
            if parsed_input is None or not parsed_input:
                clear_screen()
                print("\nVerkeerd formaat. Gebruik 'veld:waarde'. Druk op ENTER om verder te gaan.", end='')
                input()  # Wait for the user to press Enter
                clear_screen()
                continue

            field1, searchword1 = next(iter(parsed_input.items()))
            parsed_input.pop(field1)
            field2, searchword2 = next(iter(parsed_input.items()), (None, None))

            # Define the list of fields to display for each record
            attribute_names = ["auteur", "titel", "regie", "datum", "omroep", "bandnr", "vertaling", "duur", "bewerking", "genre", "productie", "themareeks", "delen", "bijzverm", "taal"]

            offset = 0
            limit = 10  # Limit the number of results per page
            total_records = 100  # Total limit of records for the search
            results = execute_search(db_file, field1, searchword1, field2, searchword2, offset=offset, limit=limit)
            if not results:
                print("Geen resultaten gevonden. Druk op ENTER om door te gaan of ESCAPE om te stoppen.")
                action_key = msvcrt.getch()
                if action_key == b'\x1b':  # ESC key
                    continue
                else:
                    return  # Return to the main menu

            current_record = 0
            current_attribute = 0

            while True:
                clear_screen()
                print(f"Zoekresultaten (Pagina {offset // limit + 1}):")
                # Display all fields for the current record
                for index, attribute in enumerate(attribute_names):
                    if index == current_attribute:
                        # Highlight the current attribute with the pointer and cursor on the same line
                        clear_screen()
                        print(f"-> {attribute}: {results[current_record][index]}\033[K", end='', flush=True)
                        clear_screen()
                    else:
                        print(f"   {attribute}: {results[current_record][index]}")

                key = msvcrt.getch()
                if key in [b'\x00', b'\xe0']:
                    key = msvcrt.getch()

                if key == b'\x1b':
                    break
                elif key == b'H':  # Up arrow key
                    current_attribute = (current_attribute - 1) % len(attribute_names)
                elif key == b'P':  # Down arrow key
                    current_attribute = (current_attribute + 1) % len(attribute_names)
                elif key == b'M':  # Right arrow key for next record
                    if current_record < len(results) - 1:
                        current_record += 1
                        current_attribute = 0  # Reset attribute index when changing records
                elif key == b'K':  # Left arrow key for previous record
                    if current_record > 0:
                        current_record -= 1
                        current_attribute = 0  # Reset attribute index when changing records

                # Pagination keys should be different from record navigation keys
                elif key == b'M':  # rechts voor volgende pagina
                    if offset + limit < total_records:
                        offset += limit
                        results = execute_search(db_file, field1, searchword1, field2, searchword2, offset=offset, limit=limit)
                        current_record = 0  # Reset index to the start of the next page
                elif key == b'K':  # Links voor vorige pagina
                    if offset - limit >= 0:
                        offset -= limit
                        results = execute_search(db_file, field1, searchword1, field2, searchword2, offset=offset, limit=limit)
                        current_record = 0  # Reset index to the start of the previous page

    except Exception as e:
        print(f"Er is een fout opgetreden: {e}")
        print("\033[1A", end='', flush=True)  # Optionally move the cursor up one line

curses.wrapper(zoek_hoorspellen)

valid_fields = [
    "auteur", "titel", "regie", "datum", "omroep", "bandnr", 
    "vertaling", "duur", "bewerking", "genre", "productie", 
    "themareeks", "delen", "bijzverm", "taal"
]

def edit_record_values(db_file, record_id, new_values):
    """
    Edit multiple field values for a given record ID.
    
    :param db_file: str - The path to the SQLite database file.
    :param record_id: int - The ID of the record to be updated.
    :param new_values: dict - A dictionary of field names and their new values.
    """
    
    # Filter out any key-value pairs where the field is not in valid_fields
    new_values = {field: value for field, value in new_values.items() if field in valid_fields}
    
    # Construct the SQL SET part dynamically based on the keys of 'new_values'
    set_clause = ', '.join([f"{field} = ?" for field in new_values])
    
    try:
        # Connect to the SQLite database
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()

            # Prepare the SQL UPDATE query
            sql_query = f"UPDATE hoorspelen SET {set_clause} WHERE id = ?"

            # Execute the SQL command with unpacked values from 'new_values'
            # and the 'record_id' at the end
            cursor.execute(sql_query, (*new_values.values(), record_id))

            # Commit the changes to the database
            conn.commit()
            
            logging.info(f"Record {record_id} successfully updated with new values.")
            return True
    except sqlite3.Error as e:
        logging.error(f"An error occurred while updating the record: {e}")
        return False

# Example usage
# new_record_data = {
#     "auteur": "New Author",
#     "titel": "New Title",
#     "regie": "New Director",
#     # ... other fields ...
# }

# Make sure to replace 'your_database.db' and '1' with your actual database file path and record ID respectively
# success = edit_record_values('your_database.db', 1, new_record_data)


# Placeholder for the actual database file path
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

    while True:
        clear_screen()
        print("Geschiedenis (Laatste 10 toevoegingen):")
        for index, attribute in enumerate(attribute_names):
            print(f"   {attribute}: {results[current_record][index]}")

        # Correctly position the cursor to highlight the selected attribute without duplicating it
        # The fix is to clear the screen and reprint everything each time, then move the cursor
        print(f"\033[{len(attribute_names) - current_attribute}A\r-> {attribute_names[current_attribute]}: {results[current_record][current_attribute]}\033[K", end='', flush=True)

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
            print(f"Export succesvol bestand opgeslagen als: {filename}")
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
    #email_address = 'sjefsdatabasebackups@gmail.com'
    #service = gmail_service()
    main_menu()
    #if service:
        #export_and_email_backup(service, db_file, email_address)
    #else:
        #print("Failed to initialize Gmail service.")
