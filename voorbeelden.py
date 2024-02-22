def zoek_hoorspellen(db_file):
    clear_screen()
    try:
        # Behoud de initiële logica voor het invoeren en verwerken van de zoekopdracht.

        # Na het verkrijgen van de resultaten:
        if not results:
            print("Geen resultaten gevonden. Druk op ENTER om door te gaan of ESCAPE om te stoppen.")
            action_key = msvcrt.getch()
            if action_key == b'\x1b':  # ESCAPE om de zoekfunctie te verlaten
                clear_screen()
                return
        else:
            # De correcte weergave van resultaten met aangepaste interactie hieronder.
            current_record = 0  # Start bij het eerste record
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen voor elke update
                # Toon het huidige record. Pas aan om alle velden correct weer te geven.
                for index, attribute in enumerate(attribute_names):
                    # Zorg dat 'id' correct wordt weergegeven
                    value = results[current_record][index]
                    print(f"   {attribute}: {value}")

                print("\nGebruik 'e' om te bewerken, ESCAPE om terug te gaan.")
                key = msvcrt.getch()

                # Hier komt de afhandeling van de gebruikersinput.
                if key == b'\x1b':  # ESCAPE toets
                    break  # Verlaat de loop en ga terug naar het hoofdmenu.
                elif key == b'e':  # 'e' toets voor bewerken
                    # Bewerk de huidige record
                    edit_current_field(db_file, current_record, 0, attribute_names, results)
                    # Na bewerking, forceer een refresh of ga terug naar hoofdmenu afhankelijk van je voorkeur.

                # Voeg indien nodig meer toetsafhandeling toe, zoals navigatie door records.

    except Exception as e:
        print(f"Er is een fout opgetreden: {e}")
