import curses
import sys

# Dummy functions to replace actual functionalities for demonstration
def voeg_toe(db_file):
    pass

def bewerk_hoorspel(db_file):
    pass

# More dummy functions as needed...

def run_menu(stdscr, title, options):
    curses.curs_set(0)  # Hide cursor
    current_option = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, title, curses.A_UNDERLINE)  # Menu title
        for index, option in enumerate(options):
            if index == current_option:
                stdscr.addstr(index + 2, 0, f"-> {option[0]}", curses.A_REVERSE)  # Highlight the current option
            else:
                stdscr.addstr(index + 2, 0, f"   {option[0]}")
        stdscr.refresh()

        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_option = (current_option - 1) % len(options)
        elif key == curses.KEY_DOWN:
            current_option = (current_option + 1) % len(options)
        elif key == curses.KEY_ENTER or key in [10, 13]:  # Enter key (KEY_ENTER doesn't work on all systems)
            if options[current_option][1] is not None:
                stdscr.clear()
                options[current_option][1]()
                stdscr.getch()  # Wait for any key press to return to the menu

def main_menu(stdscr):
    db_file = 'hoorspel.db'
    options = [
        ("Voeg Toe", lambda: voeg_toe(db_file)),
        ("Bewerk Hoorspellen", lambda: bewerk_hoorspel(db_file)),
        # Add your other options...
        ("Geavanceerd", lambda: geavanceerd_submenu(stdscr)),
        ("Afsluiten", lambda: sys.exit())
    ]
    run_menu(stdscr, "Hoofdmenu", options)

def geavanceerd_submenu(stdscr):
    options = [
        ("Importeren", lambda: None),  # Replace lambda: None with actual functions
        ("Exporteren", lambda: None),
        # Add your other options...
        ("Terug naar Hoofdmenu", None)
    ]
    run_menu(stdscr, "Geavanceerd Menu", options)

if __name__ == "__main__":
    curses.wrapper(main_menu)
