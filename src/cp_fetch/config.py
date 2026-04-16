import os

PORT = 10043
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEST_DIR = os.path.join(BASE_DIR, "test")

# Language to generate: "cpp", "python", "java", or "javascript"
LANGUAGE = "cpp"

TEMPLATES = {
    "cpp": """\
/**
 * Problem Name: {name}
 * URL: {url}
 * Time Limit: {time_limit} ms
 * Memory Limit: {memory_limit} MB
 */
""",
    "python": """\
# Problem Name: {name}
# URL: {url}
# Time Limit: {time_limit} ms
# Memory Limit: {memory_limit} MB
""",
    "java": """\
/**
 * Problem Name: {name}
 * URL: {url}
 * Time Limit: {time_limit} ms
 * Memory Limit: {memory_limit} MB
 */
""",
    "javascript": """\
/**
 * Problem Name: {name}
 * URL: {url}
 * Time Limit: {time_limit} ms
 * Memory Limit: {memory_limit} MB
 */
""",
}

FILE_EXTENSIONS = {
    "cpp": "cpp",
    "python": "py",
    "java": "java",
    "javascript": "js",
}
