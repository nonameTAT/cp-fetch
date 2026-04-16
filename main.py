import sys

if __name__ == "__main__":
    if "--config" in sys.argv:
        from src.cp_fetch.configure import menu
        menu()
    else:
        from src.cp_fetch.server import run
        run()
