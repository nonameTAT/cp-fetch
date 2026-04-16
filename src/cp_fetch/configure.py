import json
import os
import select
import shutil
import sys
import termios
import tty

from src.cp_fetch.config import DEFAULTS, DEFAULTS_PATH, FILE_EXTENSIONS, SETTINGS_PATH

_GREEN = "\033[32m"
_RESET = "\033[0m"


# ---------------------------------------------------------------------------
# Terminal helpers
# ---------------------------------------------------------------------------


def _alt_screen_enter():
    sys.stdout.write("\033[?1049h")
    sys.stdout.flush()


def _alt_screen_exit():
    sys.stdout.write("\033[?1049l")
    sys.stdout.flush()

def _read_key():
    """Read one keypress, returning the key string (handles arrow-key sequences)."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1)
        if ch == b"\x1b":
            if select.select([fd], [], [], 0.05)[0]:
                ch2 = os.read(fd, 1)
                if ch2 == b"[" and select.select([fd], [], [], 0.05)[0]:
                    ch3 = os.read(fd, 1)
                    return "\x1b[" + ch3.decode()
            return "\x1b"
        return ch.decode()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _prompt_with_esc(label, current):
    """
    Inline text prompt with Esc-to-go-back support.

    Returns the entered string (may be empty), or None if Esc was pressed.
    """
    sys.stdout.write(f"  {label} [{current}] (Esc: back): ")
    sys.stdout.flush()

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    buf = []
    try:
        tty.setraw(fd)
        while True:
            ch = os.read(fd, 1)

            if ch == b"\x1b":
                # Peek for escape sequence (arrow keys etc.) — consume and ignore
                if select.select([fd], [], [], 0.05)[0]:
                    ch2 = os.read(fd, 1)
                    if ch2 == b"[" and select.select([fd], [], [], 0.05)[0]:
                        os.read(fd, 1)
                else:
                    # Bare Escape → cancel
                    print()
                    return None

            elif ch in (b"\r", b"\n"):
                print()
                return "".join(buf)

            elif ch == b"\x7f":  # Backspace
                if buf:
                    buf.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()

            elif ch == b"\x03":  # Ctrl+C
                print()
                raise KeyboardInterrupt

            elif ch[0] >= 32:  # Printable character
                char = ch.decode("utf-8", errors="ignore")
                buf.append(char)
                sys.stdout.write(char)
                sys.stdout.flush()

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _arrow_select(title, options, current=0):
    """
    Display *options* with arrow-key navigation.

    Returns the chosen index, or -1 if the user pressed Esc (go back).
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
            if i == idx:
                rows.append(f"  {_GREEN}> {opt}{_RESET}")
            else:
                rows.append(f"    {opt}")
        return rows

    print("\n".join(_lines()))
    sys.stdout.flush()

    while True:
        key = _read_key()

        if key == "\x1b[A":
            idx = (idx - 1) % n
        elif key == "\x1b[B":
            idx = (idx + 1) % n
        elif key in ("\r", "\n"):
            print()
            return idx
        elif key == "\x1b":
            print()
            return -1
        else:
            continue

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


# ---------------------------------------------------------------------------
# Sub-menus
# ---------------------------------------------------------------------------

def _language_menu(settings):
    langs = list(FILE_EXTENSIONS)
    current_lang = _get(settings, "language")
    current_idx = langs.index(current_lang) if current_lang in langs else 0

    idx = _arrow_select("Select language", langs, current=current_idx)
    if idx == -1:
        return

    settings["language"] = langs[idx]
    _save(settings)


def _templates_menu(settings):
    langs = list(FILE_EXTENSIONS)
    merged = {**DEFAULTS["templates"], **settings.get("templates", {})}

    while True:
        idx = _arrow_select("Select language to edit template", langs)
        if idx == -1:
            break

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


def _reset_to_defaults():
    confirm = input("  Reset all settings to defaults? [y/N]: ").strip().lower()
    if confirm == "y":
        shutil.copy(DEFAULTS_PATH, SETTINGS_PATH)
        print("  Reset to defaults.")


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

_HANDLERS = [
    "language",
    "port",
    "output_dir",
    "test_subdir",
    "templates",
    "reset",
    "exit",
]


def menu():
    _alt_screen_enter()
    try:
        _menu()
    finally:
        _alt_screen_exit()


def _menu():
    print("\n+==============================+")
    print("|   cp-fetch  Configuration    |")
    print("+==============================+")

    idx = 0  # remember cursor position between iterations
    while True:
        settings = _load()
        output_dir = _get(settings, "output_dir")

        options = [
            f"Language    :  {_get(settings, 'language')}",
            f"Port        :  {_get(settings, 'port')}",
            f"Output dir  :  {output_dir or '(project root)'}",
            f"Test subdir :  {_get(settings, 'test_subdir')}",
            "Templates",
            "Reset to defaults",
            "Exit",
        ]

        idx = _arrow_select("cp-fetch Configuration", options, current=idx)

        if idx == -1 or _HANDLERS[idx] == "exit":
            print("  Bye.")
            break

        elif _HANDLERS[idx] == "language":
            _language_menu(settings)

        elif _HANDLERS[idx] == "port":
            val = _prompt_with_esc("Port", _get(settings, "port"))
            if val is None:
                pass
            elif val:
                try:
                    settings["port"] = int(val)
                    _save(settings)
                except ValueError:
                    print("  Invalid port number.")

        elif _HANDLERS[idx] == "output_dir":
            current = _get(settings, "output_dir") or "(project root)"
            val = _prompt_with_esc("Output dir (blank = project root)", current)
            if val is not None:
                settings["output_dir"] = val
                _save(settings)

        elif _HANDLERS[idx] == "test_subdir":
            val = _prompt_with_esc("Test subdir", _get(settings, "test_subdir"))
            if val is None:
                pass
            elif val:
                settings["test_subdir"] = val
                _save(settings)

        elif _HANDLERS[idx] == "templates":
            _templates_menu(settings)

        elif _HANDLERS[idx] == "reset":
            _reset_to_defaults()
