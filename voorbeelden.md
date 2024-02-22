def zoek_hoorspellen(db_file):
    clear_screen()
    try:
        # Logica om zoekopdracht uit te voeren en `results` te verkrijgen

        # Nu `results` verkregen zijn, toon ze aan de gebruiker
        if results:
            for record in results:
                print(f"Record ID: {record[0]} (niet bewerkbaar)")
                for index, field in enumerate(valid_fields):
                    # Zorg ervoor dat je index correct afhandelt, index+1 omdat `record` begint met `id`
                    print(f"   {field}: {record[index + 1]}")
                print("\n")  # Voeg een lege regel toe na elk record voor betere leesbaarheid
                
            # Mogelijk extra logica hier om de gebruiker een record te laten kiezen en te bewerken
            # Bijvoorbeeld, vragen om een Record ID en dan overgaan tot bewerken
            
        else:
            print("Geen resultaten gevonden.")
    except Exception as e:
        print(f"Er is een fout opgetreden: {e}")

    # Mogelijk meer code hier voor andere interacties na het tonen van de resultaten
