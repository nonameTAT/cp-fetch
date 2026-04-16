import os
import json

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SETTINGS_PATH = os.path.join(_PROJECT_ROOT, "settings.json")
DEFAULTS_PATH = os.path.join(_PROJECT_ROOT, "defaults.json")

with open(DEFAULTS_PATH, "r", encoding="utf-8") as _f:
    DEFAULTS = json.load(_f)

FILE_EXTENSIONS = {
    "cpp": "cpp",
    "python": "py",
    "java": "java",
    "javascript": "js",
}


def _init_settings():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = {}

    # Fill any missing top-level keys from defaults and write back
    merged = {**DEFAULTS, **existing}
    merged["templates"] = {**DEFAULTS["templates"], **existing.get("templates", {})}
    merged["commands"] = {**DEFAULTS["commands"], **existing.get("commands", {})}
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    return merged

_s = _init_settings()

PORT = _s["port"]
LANGUAGE = _s["language"]

_output_dir = _s["output_dir"]
BASE_DIR = _output_dir if _output_dir else _PROJECT_ROOT
TEST_DIR = os.path.join(BASE_DIR, _s["test_subdir"])

TEMPLATES = _s["templates"]
COMMANDS  = _s["commands"]
