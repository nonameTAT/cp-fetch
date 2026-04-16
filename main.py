import sys

if __name__ == "__main__":
    if "--config" in sys.argv:
        from src.cp_fetch.configure import menu
        menu()

    elif "--test" in sys.argv:
        idx = sys.argv.index("--test")
        if idx + 1 >= len(sys.argv):
            print("Usage: python main.py --test <problem_name>")
            sys.exit(1)
        problem_name = sys.argv[idx + 1]
        from src.cp_test.runner import run_tests
        run_tests(problem_name)

    else:
        from src.cp_fetch.server import run
        run()
