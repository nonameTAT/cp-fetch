import json
import os
import select
import sys
import termios
import tty

from src.cp_fetch.config import DEFAULTS, FILE_EXTENSIONS, SETTINGS_PATH


# ---------------------------------------------------------------------------
# Terminal helpers
# ---------------------------------------------------------------------------

def _read_key():
    """Read one keypress, returning the key string (handles arrow-key sequences)."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1)
        if ch == b"\x1b":
            # Peek to distinguish bare Escape from arrow / other sequences
            if select.select([fd], [], [], 0.05)[0]:
                ch2 = os.read(fd, 1)
                if ch2 == b"[" and select.select([fd], [], [], 0.05)[0]:
                    ch3 = os.read(fd, 1)
                    return "\x1b[" + ch3.decode()
            return "\x1b"
        return ch.decode()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _arrow_select(title, options, current=0):
    """
    Display *options* with arrow-key navigation.

    Returns the chosen index, or -1 if the user pressed Esc (go back).

    Keys:
      Up / Down  – move cursor
      Enter      – confirm
      Esc        – go back to the previous screen
    """
    idx = current
    n = len(options)

    def _lines():
        rows = [
            f"  {title}",
            "  up/down: navigate   Enter: confirm   Esc: back",
            "",
        ]
        for i, opt in enumerate(options):
            marker = "> " if i == idx else "  "
            rows.append(f"  {marker}{opt}")
        return rows

    # Initial render
    print("\n".join(_lines()))
    sys.stdout.flush()

    while True:
        key = _read_key()

        if key == "\x1b[A":      # Up arrow
            idx = (idx - 1) % n
        elif key == "\x1b[B":    # Down arrow
            idx = (idx + 1) % n
        elif key in ("\r", "\n"): # Enter – confirm
            print()
            return idx
        elif key == "\x1b":      # Escape – go back
            print()
            return -1
        else:
            continue

        # Redraw in-place: go up len(rows) lines, clear to end, reprint
        rows = _lines()
        sys.stdout.write(f"\033[{len(rows)}A\033[J")
        print("\n".join(rows))
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------------

def _load():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(settings):
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    print("  Saved.")


def _get(settings, key):
    return settings.get(key, DEFAULTS[key])


def _prompt(label, current):
    val = input(f"  {label} [{current}]: ").strip()
    return val if val else None


# ---------------------------------------------------------------------------
# Sub-menus
# ---------------------------------------------------------------------------

def _language_menu(settings):
    langs = list(FILE_EXTENSIONS)
    current_lang = _get(settings, "language")
    current_idx = langs.index(current_lang) if current_lang in langs else 0

    idx = _arrow_select("Select language", langs, current=current_idx)
    if idx == -1:
        return  # Esc – back to main menu

    settings["language"] = langs[idx]
    _save(settings)


def _templates_menu(settings):
    langs = list(FILE_EXTENSIONS)
    merged = {**DEFAULTS["templates"], **settings.get("templates", {})}

    while True:
        idx = _arrow_select("Select language to edit template", langs)
        if idx == -1:
            break  # Esc – back to main menu

        lang = langs[idx]

        print(f"\n  Current template for [{lang}]:")
        print("  " + "-" * 40)
        for line in merged[lang].splitlines():
            print(f"  {line}")
        print("  " + "-" * 40)
        print("  Placeholders: {name}  {url}  {time_limit}  {memory_limit}")
        print("  Enter new template line by line. Ctrl+D to finish.")
        print("  (Ctrl+D with no input = keep current template.)\n")

        lines = []
        try:
            while True:
                lines.append(input("  "))
        except EOFError:
            pass

        if lines and any(line.strip() for line in lines):
            new_template = "\n".join(lines) + "\n"
            if "templates" not in settings:
                settings["templates"] = {}
            settings["templates"][lang] = new_template
            merged[lang] = new_template
            _save(settings)


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

def menu():
    print("\n+==============================+")
    print("|   cp-fetch  Configuration    |")
    print("+==============================+")

    while True:
        settings = _load()
        output_dir = _get(settings, "output_dir")

        print(f"\n  1. Language    :  {_get(settings, 'language')}")
        print(f"  2. Port        :  {_get(settings, 'port')}")
        print(f"  3. Output dir  :  {output_dir or '(project root)'}")
        print(f"  4. Test subdir :  {_get(settings, 'test_subdir')}")
        print(f"  5. Templates")
        print(f"  0. Exit")

        choice = input("\n  Choose option: ").strip()

        if choice == "0":
            print("  Bye.")
            break

        elif choice == "1":
            _language_menu(settings)

        elif choice == "2":
            val = _prompt("Port", _get(settings, "port"))
            if val:
                try:
                    settings["port"] = int(val)
                    _save(settings)
                except ValueError:
                    print("  Invalid port number.")

        elif choice == "3":
            current = _get(settings, "output_dir") or "(project root)"
            val = input(f"  Output dir [{current}] (blank = project root): ").strip()
            settings["output_dir"] = val
            _save(settings)

        elif choice == "4":
            val = _prompt("Test subdir", _get(settings, "test_subdir"))
            if val:
                settings["test_subdir"] = val
                _save(settings)

        elif choice == "5":
            _templates_menu(settings)

        else:
            print("  Invalid option.")
