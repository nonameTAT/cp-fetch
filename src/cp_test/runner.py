import os
import shlex
import subprocess
import tempfile

from src.cp_fetch.config import BASE_DIR, TEST_DIR, LANGUAGE, FILE_EXTENSIONS, COMMANDS

_GREEN  = "\033[32m"
_RED    = "\033[31m"
_YELLOW = "\033[33m"
_BOLD   = "\033[1m"
_RESET  = "\033[0m"

_TIMEOUT = 5  # seconds per test case


# ---------------------------------------------------------------------------
# Compile / run using commands from config
# ---------------------------------------------------------------------------

def _resolve(template, **kwargs):
    """Substitute placeholders in a command template and split into a list."""
    quoted = {k: shlex.quote(str(v)) for k, v in kwargs.items()}
    return shlex.split(template.format(**quoted))


def _compile(language, source):
    """
    Run the compile command for *language* if one is defined.
    Returns (artifact, error_string).
    artifact is passed to _run_cmd as needed (binary path or classpath dir).
    """
    cmd_cfg = COMMANDS[language]
    compile_tpl = cmd_cfg.get("compile")

    if not compile_tpl:
        return source, None  # no compilation needed; artifact = source path

    if language == "cpp":
        artifact = os.path.join(
            tempfile.gettempdir(), os.path.basename(source) + ".bin"
        )
        cmd = _resolve(compile_tpl, source=source, binary=artifact)
    elif language == "java":
        artifact = os.path.dirname(source)  # classpath = dir of .class files
        cmd = _resolve(compile_tpl, source=source)
    else:
        artifact = source
        cmd = _resolve(compile_tpl, source=source)

    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return None, r.stderr
    return artifact, None


def _run_cmd(language, artifact, source):
    """Build the run command list for *language*."""
    run_tpl = COMMANDS[language]["run"]
    return _resolve(run_tpl, source=source, binary=artifact, classpath=artifact)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_tests(problem_name):
    ext      = FILE_EXTENSIONS[LANGUAGE]
    source   = os.path.join(BASE_DIR, f"{problem_name}.{ext}")
    test_dir = os.path.join(TEST_DIR, problem_name)

    if not os.path.exists(source):
        print(f"{_RED}Source file not found:{_RESET} {source}")
        return

    if not os.path.exists(test_dir):
        print(f"{_RED}Test directory not found:{_RESET} {test_dir}")
        return

    test_indices = sorted(
        int(f[:-3]) for f in os.listdir(test_dir) if f.endswith(".in")
    )
    if not test_indices:
        print(f"{_RED}No test cases found in{_RESET} {test_dir}")
        return

    # ── compile ────────────────────────────────────────────────────────────
    artifact, err = _compile(LANGUAGE, source)
    if err:
        print(f"{_BOLD}Compiling {problem_name}.{ext}...{_RESET}")
        print(f"{_RED}Compilation error:{_RESET}\n{err}")
        return

    cmd = _run_cmd(LANGUAGE, artifact, source)

    # ── run test cases ─────────────────────────────────────────────────────
    sep = "─" * 40
    print(f"\n{_BOLD}Testing: {problem_name}  ({LANGUAGE}){_RESET}")
    print(sep)

    passed = 0
    for i in test_indices:
        in_path  = os.path.join(test_dir, f"{i}.in")
        out_path = os.path.join(test_dir, f"{i}.out")

        input_data = open(in_path,  encoding="utf-8").read()
        expected   = open(out_path, encoding="utf-8").read().strip()

        try:
            result = subprocess.run(
                cmd,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=_TIMEOUT,
            )
            actual = result.stdout.strip()

            if actual == expected:
                print(f"  {_GREEN}[PASS]{_RESET} Test {i}")
                passed += 1
            else:
                print(f"  {_RED}[FAIL]{_RESET} Test {i}")
                preview = input_data.strip()
                if len(preview) > 120:
                    preview = preview[:120] + "..."
                print(f"    {_BOLD}Input   :{_RESET} {preview}")
                print(f"    {_BOLD}Expected:{_RESET} {expected}")
                print(f"    {_BOLD}Got     :{_RESET} {actual}")
                if result.stderr.strip():
                    print(f"    {_YELLOW}Stderr  :{_RESET} {result.stderr.strip()}")

        except subprocess.TimeoutExpired:
            print(f"  {_YELLOW}[TLE] {_RESET} Test {i}  (>{_TIMEOUT}s)")

    print(sep)
    color = _GREEN if passed == len(test_indices) else _RED
    print(f"  {color}{_BOLD}{passed}/{len(test_indices)} passed{_RESET}\n")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.cp_test.runner <problem_name>")
        sys.exit(1)
    run_tests(sys.argv[1])
