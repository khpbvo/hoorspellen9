import curses

def main(stdscr):
    curses.curs_set(0)  # Hide cursor
    stdscr.addstr("Hello, world!")
    stdscr.refresh()
    stdscr.getch()

if __name__ == "__main__":
    curses.wrapper(main)
    try:
        curses.wrapper(main_menu)
    except Exception as e:
        print(f"Error: {e}")