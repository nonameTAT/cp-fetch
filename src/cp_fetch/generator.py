from src.cp_fetch.config import BASE_DIR, TEST_DIR, LANGUAGE, TEMPLATES, FILE_EXTENSIONS
import re
import os


def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def generate_problem_files(problem_data):
    name = problem_data.get("name", "Unknown")
    url = problem_data.get("url", "Unknown URL")
    time_limit = problem_data.get("timeLimit", "Unknown")
    memory_limit = problem_data.get("memoryLimit", "Unknown")
    tests = problem_data.get("tests", [])

    ext = FILE_EXTENSIONS[LANGUAGE]
    filename = os.path.join(BASE_DIR, f"{sanitize_filename(name)}.{ext}")

    cpp_content = TEMPLATES[LANGUAGE].format(
        name=name,
        url=url,
        time_limit=time_limit,
        memory_limit=memory_limit,
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(cpp_content)

    if tests:
        os.makedirs(TEST_DIR, exist_ok=True)
        for i, test in enumerate(tests, start=1):
            with open(os.path.join(TEST_DIR, f"{i}.in"), "w", encoding="utf-8") as f_in:
                f_in.write(test.get("input", ""))
            with open(
                os.path.join(TEST_DIR, f"{i}.out"), "w", encoding="utf-8"
            ) as f_out:
                f_out.write(test.get("output", ""))

    return filename, len(tests), problem_data.get("group", "Unknown"), name
