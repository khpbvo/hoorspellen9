import sys
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

logging.basicConfig(filename='hoorspellen_app.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    return psycopg2.connect(
        dbname='hoorspellen',
        user='hoorspellen',
        password='1337Hoorspellen!@',
        host='192.168.88.49',
        port='5432',
    )

def initialize_db(conn):
    with conn.cursor() as cursor:
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
                taal TEXT,
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    conn.commit()

def single_line_output(term, message):
    # Alle output in één regel met de cursor erachter
    print(term.home + term.clear + "-> " + message, end='', flush=True)

def geavanceerd_submenu(conn, term):
    options = [
        ("Importeren", lambda: import_function(conn, term)),
        ("Exporteren", lambda: export_function(conn, term)),
        ("DB Legen", lambda: clear_db_function(conn, term)),
        ("Terug naar Hoofdmenu", None)
    ]
    current_option = 0

    while True:
        # Toon huidige optie in één regel
        menu_line = "Geavanceerd menu: Gebruik pijltjestoetsen om te navigeren. ENTER = selecteren, ESC = terug. Huidige optie: " + options[current_option][0]
        single_line_output(term, menu_line)

        with term.cbreak():
            key = term.inkey()

        if key.name == 'KEY_UP':
            current_option = (current_option - 1) % len(options)
        elif key.name == 'KEY_DOWN':
            current_option = (current_option + 1) % len(options)
        elif key.name == 'KEY_ENTER':
            if options[current_option][1] is None:
                break
            else:
                options[current_option][1]()
        elif key.name == 'KEY_ESCAPE':
            break

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
        menu_line = "Hoofdmenu: Gebruik pijltjestoetsen (UP/DOWN) om te navigeren, ENTER = selecteren, ESC = afsluiten. Huidige optie: " + options[current_option]
        single_line_output(term, menu_line)

        with term.cbreak():
            key = term.inkey()

        if key.name == 'KEY_UP':
            current_option = (current_option - 1) % len(options)
        elif key.name == 'KEY_DOWN':
            current_option = (current_option + 1) % len(options)
        elif key.name == 'KEY_ENTER':
            if current_option == len(options) - 1:  # "Afsluiten"
                single_line_output(term, "Backup aan het maken, moment geduld...")
                email_message = create_message_with_attachment(
                    "sjefsdatabasebackups@gmail.com",
                    "sjefsdatabasebackups@gmail.com",
                    "Hoorspelen backup",
                    "De backup van de hoorspelen",
                    csv_path=export_function(conn, term)
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
            single_line_output(term, "Backup aan het maken, moment geduld...")
            email_message = create_message_with_attachment(
                "sjefsdatabasebackups@gmail.com",
                "sjefsdatabasebackups@gmail.com",
                "Hoorspelen backup",
                "De backup van de hoorspelen",
                csv_path=export_function(conn, term)
            )
            service = gmail_service()
            send_message(service, "me", email_message)
            return

def import_function(conn, term):
    single_line_output(term, "Voer het pad naar het CSV-bestand in (ESC annuleert): ")
    filename = get_input(term)
    if filename is None:
        return
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)
            with conn:
                with conn.cursor() as cursor:
                    for row in reader:
                        data_to_insert = row[1:]
                        cursor.execute('''
                            INSERT INTO hoorspelen (auteur, titel, regie, datum, omroep, bandnr, vertaling, duur, bewerking, genre, productie, themareeks, delen, bijzverm, taal)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ''', data_to_insert)
        single_line_output(term, "Importeren gelukt. Druk op een toets om verder te gaan...")
        term.inkey()
    except Exception as e:
        single_line_output(term, f"Er is een fout opgetreden: {e}. Druk op een toets om verder te gaan...")
        term.inkey()

def export_function(conn, term):
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    filename = f"hoorspellendb_{timestamp}.csv"
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM hoorspelen")
                writer = csv.writer(csvfile)
                writer.writerow([desc[0] for desc in cursor.description])
                writer.writerows(cursor.fetchall())
        single_line_output(term, f"Exporteren gelukt. Bestand opgeslagen als: {filename}. Druk op een toets om verder te gaan...")
        term.inkey()
        return filename
    except Exception as e:
        single_line_output(term, f"Er is een fout opgetreden: {e}. Druk op een toets om verder te gaan...")
        term.inkey()
        logging.error(f"Error during export: {e}")
        return None

def clear_db_function(conn, term):
    single_line_output(term, "Weet u zeker dat u alle gegevens wilt wissen? Type 'ja' om te bevestigen (ESC annuleert): ")
    confirm = get_input(term)
    if confirm is None:
        single_line_output(term, "Wissen geannuleerd. Druk op een toets om verder te gaan...")
        term.inkey()
        return
    if confirm.lower() == 'ja':
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM hoorspelen")
            single_line_output(term, "Database geleegd. Druk op een toets om verder te gaan...")
            term.inkey()
        except Exception as e:
            single_line_output(term, f"Er is een fout opgetreden: {e}. Druk op een toets om verder te gaan...")
            term.inkey()
    else:
        single_line_output(term, "Wissen geannuleerd. Druk op een toets om verder te gaan...")
        term.inkey()

def validate_date(date_string):
    try:
        datetime.datetime.strptime(date_string, '%Y/%m/%d')
        return True
    except ValueError:
        return False

def get_input(term):
    # Leest gebruikerinput inline. ESC annuleert
    value = ''
    while True:
        with term.cbreak():
            key = term.inkey()
        if key.name == 'KEY_ENTER':
            return value
        elif key.name == 'KEY_BACKSPACE':
            if len(value) > 0:
                value = value[:-1]
                # Herteken de regel:
                # Cursor terug en spatie printen om laatste char te overschrijven
                print('\b \b', end='', flush=True)
        elif key.name == 'KEY_ESCAPE':
            print("\nInvoer geannuleerd.")
            return None
        elif key.is_sequence:
            # Pijltjes of andere keys negeren in invoer
            continue
        else:
            value += key
            print(key, end='', flush=True)

def clear_screen(term):
    print(term.home + term.clear, end='', flush=True)

def voeg_toe(conn, term):
    logging.info("Starting voeg_toe function")
    fields = ['auteur', 'titel', 'regie', 'datum', 'omroep', 'bandnr', 'vertaling', 'duur', 'bewerking', 'genre', 'productie', 'themareeks', 'delen', 'bijzverm', 'taal']
    record = {field: "" for field in fields}
    current_field = 0
    error_message = ""

    def validate_record():
        if not is_valid_datum_format(record['datum']):
            return "Verkeerde datum. Gebruik YYYY/MM/DD."
        for field in fields:
            if not record[field].strip():
                return f"'{field}' mag niet leeg zijn."
        return None

    while True:
        # Toon huidige veld en waarde in één regel, incl. error
        line = f"Voeg toe: Gebruik UP/DOWN om veld te kiezen, ENTER om waarde in te voeren, CTRL+S om op te slaan, ESC om te annuleren. Huidig veld: {fields[current_field]}: {record[fields[current_field]]}"
        if error_message:
            line += f" FOUT: {error_message}"
        single_line_output(term, line)

        with term.cbreak():
            key = term.inkey()

        if key.name == 'KEY_ESCAPE':
            return
        elif key.name == 'KEY_UP':
            current_field = (current_field - 1) % len(fields)
            error_message = ""
        elif key.name == 'KEY_DOWN':
            current_field = (current_field + 1) % len(fields)
            error_message = ""
        elif key.name == 'KEY_ENTER':
            single_line_output(term, f"Voer waarde in voor {fields[current_field]} (ESC annuleert): ")
            value = get_input(term)
            if value is not None:
                record[fields[current_field]] = value
            error_message = ""
        elif key == '\x13':  # Ctrl+S
            error = validate_record()
            if error:
                error_message = error
            else:
                try:
                    record_values = [record[field] for field in fields]
                    placeholders = ', '.join(['%s'] * len(fields))
                    query = f'INSERT INTO hoorspelen ({", ".join(fields)}) VALUES ({placeholders}) RETURNING id'
                    with conn:
                        with conn.cursor() as cursor:
                            cursor.execute(query, record_values)
                            new_id = cursor.fetchone()[0]
                    single_line_output(term, "Record toegevoegd. Druk op een toets om verder te gaan...")
                    term.inkey()
                    return
                except Exception as e:
                    error_message = f"Fout bij toevoegen: {e}"

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
    clear_screen(term)
    single_line_output(term, "Voer de ID in van de inzending die je wilt bewerken (ESC annuleert): ")
    entry_id = get_input(term)
    if entry_id is None:
        return

    try:
        entry_id = int(entry_id)
    except ValueError:
        single_line_output(term, "Ongeldige invoer. Druk op een toets om verder te gaan...")
        term.inkey()
        return

    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM hoorspelen WHERE id = %s FOR UPDATE", (entry_id,))
                entry = cursor.fetchone()

                if entry:
                    fields = ['auteur', 'titel', 'regie', 'datum', 'omroep', 'bandnr', 'vertaling', 'duur',
                              'bewerking', 'genre', 'productie', 'themareeks', 'delen', 'bijzverm', 'taal']
                    current_field = 0
                    record = {field: entry[i+1] if entry[i+1] is not None else '' for i, field in enumerate(fields)}
                    error_message = ""

                    def validate_record():
                        if not is_valid_datum_format(record['datum']):
                            return "Verkeerde datum. Gebruik YYYY/MM/DD."
                        for field in fields:
                            if not record[field].strip():
                                return f"'{field}' mag niet leeg zijn."
                        return None

                    while True:
                        line = f"Bewerk record {entry_id}: UP/DOWN veld wisselen, ENTER waarde invoeren, CTRL+S opslaan, ESC annuleren. Huidig veld: {fields[current_field]}: {record[fields[current_field]]}"
                        if error_message:
                            line += f" FOUT: {error_message}"
                        single_line_output(term, line)

                        with term.cbreak():
                            key = term.inkey()

                        if key.name == 'KEY_ESCAPE':
                            return
                        elif key.name == 'KEY_UP':
                            current_field = (current_field - 1) % len(fields)
                        elif key.name == 'KEY_DOWN':
                            current_field = (current_field + 1) % len(fields)
                        elif key.name == 'KEY_ENTER':
                            single_line_output(term, f"Nieuwe waarde voor {fields[current_field]} (ESC annuleert): ")
                            new_value = get_input(term)
                            if new_value is not None:
                                record[fields[current_field]] = new_value
                            error_message = ""
                        elif key == '\x13':  # Ctrl+S
                            error = validate_record()
                            if error:
                                error_message = error
                            else:
                                try:
                                    placeholders = ', '.join([f"{field} = %s" for field in fields])
                                    query = f"UPDATE hoorspelen SET {placeholders}, last_modified = CURRENT_TIMESTAMP WHERE id = %s"
                                    cursor.execute(query, [record[field] for field in fields] + [entry_id])
                                    single_line_output(term, "Record succesvol bijgewerkt. Druk op een toets om verder te gaan...")
                                    term.inkey()
                                    return
                                except Exception as e:
                                    error_message = f"Fout bij bijwerken: {e}"
                else:
                    single_line_output(term, "Inzending niet gevonden. Druk op een toets om verder te gaan...")
                    term.inkey()
    except Exception as e:
        single_line_output(term, f"Er is een fout opgetreden: {e}. Druk op een toets om verder te gaan...")
        term.inkey()

valid_fields = [
    "id", "auteur", "titel", "regie", "datum", "omroep", "bandnr",
    "vertaling", "duur", "bewerking", "genre", "productie",
    "themareeks", "delen", "bijzverm", "taal"
]

def execute_search(conn, search_term, offset, limit, specific_field=None):
    try:
        with conn.cursor() as cursor:
            if specific_field and specific_field in valid_fields:
                if specific_field == 'id':
                    if not search_term.isdigit():
                        raise ValueError("ID moet een numerieke waarde zijn.")
                    query = sql.SQL("SELECT * FROM hoorspelen WHERE {} = %s LIMIT %s OFFSET %s").format(sql.Identifier(specific_field))
                    cursor.execute(query, (search_term, limit, offset))
                else:
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
            return results

    except Exception as e:
        conn.rollback()
        logging.error(f"An error occurred in execute_search: {e}")
        raise

def zoek_hoorspellen(conn, term):
    while True:
        single_line_output(term, "Voer zoekterm in of veld:zoekwoord (ESC om terug te gaan): ")
        search_term_line = get_input(term)
        if search_term_line is None:
            return
        search_term = search_term_line
        specific_field = None
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
            single_line_output(term, f"Zoekopdracht mislukt: {e}. Druk op een toets om verder te gaan...")
            term.inkey()
            continue

        if not results:
            single_line_output(term, "Geen resultaten gevonden. Druk op een toets om verder te gaan...")
            term.inkey()
            continue

        display_search_results(conn, term, results, search_term, offset, limit)

def display_search_results(conn, term, results, search_term, offset, limit):
    current_record = 0
    current_attribute = 0
    while True:
        # Toon huidige resultaat op één regel
        record_info = []
        for i, attribute_name in enumerate(valid_fields):
            prefix = "-> " if i == current_attribute else ""
            record_info.append(f"{prefix}{attribute_name}: {results[current_record][i]}")

        line = (f"Resultaat {current_record+1}/{len(results)} | Gebruik UP/DOWN voor attribuut, LEFT/RIGHT voor record wisselen, ESC terug, 'e' om attribuut te bewerken: " 
                + " | ".join(record_info))
        single_line_output(term, line)

        with term.cbreak():
            key = term.inkey()

        if not key:
            continue

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
                current_record = 0
        elif key.name == 'KEY_LEFT':
            if current_record > 0:
                current_record -= 1
            else:
                current_record = len(results) - 1
        elif key.lower() == 'e':
            if valid_fields[current_attribute] != "id":
                edit_field(conn, term, results, current_record, current_attribute, search_term, offset, limit)
                results = execute_search(conn, search_term, offset, limit)

def edit_field(conn, term, results, current_record, current_attribute, search_term, offset, limit):
    field_name = valid_fields[current_attribute]
    current_value = results[current_record][current_attribute]
    single_line_output(term, f"Bewerk {field_name}, huidige waarde: {current_value}. Nieuwe waarde (ESC annuleert): ")
    new_value = get_input(term)
    if new_value is None:
        return
    if new_value == '':
        new_value = current_value
    if new_value != current_value:
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM hoorspelen WHERE id = %s FOR UPDATE", (results[current_record][0],))
                    entry = cursor.fetchone()
                    if not entry:
                        single_line_output(term, "Record niet gevonden of gewijzigd door een andere gebruiker. Druk op een toets om verder te gaan...")
                        term.inkey()
                        return
                    update_query = sql.SQL("UPDATE hoorspelen SET {} = %s, last_modified = CURRENT_TIMESTAMP WHERE id = %s").format(sql.Identifier(field_name))
                    cursor.execute(update_query, (new_value, results[current_record][0]))
            single_line_output(term, "Record succesvol bijgewerkt. Druk op een toets om verder te gaan...")
            term.inkey()
            results[current_record] = list(results[current_record])
            results[current_record][current_attribute] = new_value
        except Exception as e:
            single_line_output(term, f"Fout bij het bijwerken: {e}. Druk op een toets om verder te gaan...")
            term.inkey()

def toon_totaal_hoorspellen(conn, term):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM hoorspelen")
            total = cursor.fetchone()[0]
        single_line_output(term, f"Totaal aantal hoorspellen: {total}. Druk op een toets om verder te gaan...")
        term.inkey()
    except Exception as e:
        single_line_output(term, f"Er is een fout opgetreden: {e}. Druk op een toets om verder te gaan...")
        term.inkey()

def geschiedenis(conn, term):
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM hoorspelen ORDER BY id DESC LIMIT 10")
            results = cursor.fetchall()
            results = list(reversed(results))

        if not results:
            single_line_output(term, "Geen hoorspelen gevonden. Druk op een toets om verder te gaan...")
            term.inkey()
            return

        current_record = 0
        current_attribute = 0
        attribute_names = valid_fields
        message = None

        while True:
            record_info = []
            for i, attribute_name in enumerate(attribute_names):
                prefix = "-> " if i == current_attribute else ""
                record_info.append(f"{prefix}{attribute_name}: {results[current_record][i]}")

            line = f"Geschiedenis {current_record+1}/{len(results)} | UP/DOWN attribuut, LEFT/RIGHT record, ESC terug, 'e' bewerken: " + " | ".join(record_info)
            if message:
                line += f" | {message}"
            single_line_output(term, line)

            with term.cbreak():
                key = term.inkey()

            if key.name == 'KEY_ESCAPE':
                break
            elif message:
                if key.name == 'KEY_LEFT':
                    if current_record > 0:
                        current_record -= 1
                        message = None
                    else:
                        message = "Begin resultaten, gebruik RIGHT om vooruit te gaan."
                elif key.name == 'KEY_RIGHT':
                    if current_record < len(results) - 1:
                        current_record += 1
                        message = None
                    else:
                        message = "Einde resultaten, gebruik LEFT om terug te gaan."
            else:
                if key.name == 'KEY_UP':
                    current_attribute = (current_attribute - 1) % len(attribute_names)
                elif key.name == 'KEY_DOWN':
                    current_attribute = (current_attribute + 1) % len(attribute_names)
                elif key.name == 'KEY_RIGHT':
                    if current_record < len(results) - 1:
                        current_record += 1
                    else:
                        message = "Einde resultaten, gebruik LEFT om terug te gaan."
                elif key.name == 'KEY_LEFT':
                    if current_record > 0:
                        current_record -= 1
                    else:
                        message = "Begin resultaten, gebruik RIGHT om verder te gaan."
                elif key == 'e':
                    if attribute_names[current_attribute] != 'id':
                        single_line_output(term, f"Huidige waarde: {results[current_record][current_attribute]}. Nieuwe waarde (ESC annuleert): ")
                        new_value = get_input(term)
                        if new_value is None:
                            continue
                        if new_value == "":
                            continue
                        if attribute_names[current_attribute] == 'datum' and not validate_date(new_value):
                            single_line_output(term, "Verkeerde datumformaat. Gebruik YYYY/MM/DD. Druk op een toets om verder te gaan...")
                            term.inkey()
                            continue
                        try:
                            with conn:
                                with conn.cursor() as cursor:
                                    cursor.execute("SELECT * FROM hoorspelen WHERE id = %s FOR UPDATE", (results[current_record][0],))
                                    entry = cursor.fetchone()
                                    if not entry:
                                        single_line_output(term, "Record niet gevonden of gewijzigd. Druk op een toets om verder te gaan...")
                                        term.inkey()
                                        continue
                                    update_query = sql.SQL("UPDATE hoorspelen SET {} = %s, last_modified = CURRENT_TIMESTAMP WHERE id = %s").format(sql.Identifier(attribute_names[current_attribute]))
                                    cursor.execute(update_query, (new_value, results[current_record][0]))
                            results[current_record] = list(results[current_record])
                            results[current_record][current_attribute] = new_value
                            single_line_output(term, "Record succesvol bijgewerkt. Druk op een toets om verder te gaan...")
                            term.inkey()
                        except Exception as e:
                            single_line_output(term, f"Fout bij bijwerken: {e}. Druk op een toets om verder te gaan...")
                            term.inkey()

    except Exception as e:
        single_line_output(term, f"Er is een fout opgetreden: {e}. Druk op een toets om verder te gaan...")
        term.inkey()

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def gmail_service():
    creds = None
    service = None
    token_path = 'token.pickle'
    credentials_path = "client_secret_909008488627-c1gda8u30p8ssck0rsrcrs46p88mimb2.apps.googleusercontent.com.json"

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

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
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    if creds:
        service = build('gmail', 'v1', credentials=creds)
    else:
        print("Geen valide login.")

    return service

def create_message_with_attachment(sender, to, subject, message_text, csv_path):
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
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print('Message Id: %s' % message['id'])
    except HttpError as error:
        print(f'An error occurred: {error}')

def export_and_email_backup(service, conn, email_address):
    csv_path = export_function(conn, term)
    if csv_path:
        sender = "me"
        to = email_address
        subject = "Database Backup"
        message_text = "Attached is the database backup."
        message = create_message_with_attachment(sender, to, subject, message_text, csv_path)
        send_message(service, "me", message)
    else:
        single_line_output(term, "Export mislukt. Email niet verzonden. Druk op een toets om verder te gaan...")
        term.inkey()

if __name__ == "__main__":
    term = blessed.Terminal()
    conn = get_db_connection()
    initialize_db(conn)
    main_menu(conn, term)
    conn.close()