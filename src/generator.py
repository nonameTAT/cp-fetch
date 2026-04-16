from src import BASE_DIR, TEST_DIR
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

    filename = os.path.join(BASE_DIR, f"{sanitize_filename(name)}.cpp")

    cpp_content = f"""/**
 * Problem Name: {name}
 * URL: {url}
 * Time Limit: {time_limit} ms
 * Memory Limit: {memory_limit} MB
 */

#include <iostream>

using namespace std;

int main() {{
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    // Your code here

    return 0;
}}
"""

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
