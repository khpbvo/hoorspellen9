# Hoorspelen Database Beheertool

Dit programma is ontwikkeld voor een blinde gebruiker die een braillemachine hanteert. Vanwege deze reden maakt het gebruik van ANSI escape-sequenties en commando's om het scherm te wissen, om zo optimale compatibiliteit met braille-apparatuur te garanderen.

Het programma is een databasebeheertool voor hoorspelen, waarmee je hoorspelen kunt toevoegen, bewerken, zoeken en beheren.

## Inhoudsopgave

- [Functies](#functies)
- [Installatie](#installatie)
- [Gebruik](#gebruik)
- [Configuratie](#configuratie)
- [Opmerkingen](#opmerkingen)
- [Licentie](#licentie)

## Functies

- **Hoofdmenu**: Biedt toegang tot alle hoofdfunctionaliteiten zoals toevoegen, bewerken, zoeken, totaaloverzicht, geschiedenis en geavanceerde opties.
- **Toevoegen van Hoorspelen**: Voeg nieuwe hoorspelen toe aan de database met details zoals auteur, titel, regie, datum, enzovoort.
- **Bewerken van Hoorspelen**: Bewerk bestaande hoorspelen in de database.
- **Zoeken naar Hoorspelen**: Zoek hoorspelen op basis van specifieke velden en zoekwoorden.
- **Totaaloverzicht**: Toon het totale aantal hoorspelen in de database.
- **Geschiedenis**: Bekijk de laatste 10 toegevoegde hoorspelen.
- **Geavanceerde Opties**:
  - **Importeren**: Importeer hoorspelen vanuit een CSV-bestand.
  - **Exporteren**: Exporteer de database naar een CSV-bestand.
  - **Database Legen**: Verwijder alle gegevens uit de database.
- **Backup Functionaliteit**: Bij het afsluiten wordt automatisch een backup van de database gemaakt en via Gmail verstuurd.

## Installatie

1. **Vereisten**:

   - Python 3.x geïnstalleerd op uw systeem.
   - Een internetverbinding voor de backup-functionaliteit.
   - Toegang tot de Gmail API (zie Configuratie).

2. **Benodigde Python-pakketten installeren**:

   Voer het volgende commando uit om de benodigde pakketten te installeren:

   ```bash
   pip install -r requirements.txt
   ```

   *Als er geen `requirements.txt` is, installeer dan de volgende pakketten afzonderlijk:*

   ```bash
   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client certifi
   ```

3. **Code downloaden**:

   Download of kloon deze repository naar uw lokale machine.

4. **Database Initialiseren**:

   Bij de eerste uitvoering zal het programma automatisch het `hoorspel.db` bestand aanmaken als dit nog niet bestaat.

## Gebruik

Start het programma door het volgende commando uit te voeren:

```bash
python main.py
```

*Let op: vervang `main.py` door de daadwerkelijke bestandsnaam als deze anders is.*

Gebruik de pijltoetsen om door het menu te navigeren en druk op **Enter** om een selectie te maken.

## Configuratie

### Gmail API Instellen voor Backup Functionaliteit

1. **Google Cloud Console**:

   - Ga naar de [Google Cloud Console](https://console.cloud.google.com/).
   - Maak een nieuw project aan of gebruik een bestaand project.
   - Schakel de **Gmail API** in voor dit project.

2. **OAuth Inloggegevens Aanmaken**:

   - Ga naar **APIs & Services** > **Credentials**.
   - Klik op **Create Credentials** en kies voor **OAuth client ID**.
   - Selecteer **Desktop app** als toepassingssoort.
   - Download het gegenereerde `credentials.json` bestand en plaats dit in de hoofdmap van het programma.

3. **Authenticatie**:

   Bij de eerste uitvoering die de backup-functionaliteit gebruikt, zal er een browservenster openen om in te loggen met uw Google-account en de nodige permissies toe te staan.

## Opmerkingen

- **Braille Compatibiliteit**: Het programma maakt gebruik van ANSI escape-sequenties en schermwissingscommando's om compatibiliteit met braille-apparaten te optimaliseren.
- **Besturingssysteem**: Ontwikkeld voor Windows-omgevingen (maakt gebruik van het `msvcrt`-module).
- **Backup E-mail**: Zorg ervoor dat minder veilige apps zijn ingeschakeld in uw Gmail-account of gebruik een app-wachtwoord als tweestapsverificatie is ingeschakeld.

## Licentie

Dit project is gelicentieerd onder de MIT-licentie - zie het [LICENSE](LICENSE) bestand voor details.

---

*Dit programma is ontwikkeld met speciale aandacht voor toegankelijkheid en gebruiksgemak voor gebruikers met een visuele beperking.*
