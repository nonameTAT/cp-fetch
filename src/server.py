import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from src.config import PORT
from src.generator import generate_problem_files


class CompetitiveCompanionHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        problem_data = json.loads(post_data.decode("utf-8"))

        print(
            f"\n[{problem_data.get('group', 'Unknown')}] {problem_data.get('name', 'Unknown')}"
        )
        print(f"URL: {problem_data.get('url')}")
        print(f"Time Limit: {problem_data.get('timeLimit')} ms")
        print(f"Memory Limit: {problem_data.get('memoryLimit')} MB")

        tests = problem_data.get("tests", [])
        print(f"Test Cases: {len(tests)}")
        for i, test in enumerate(tests):
            print(
                f"  Test {i + 1}: Input len={len(test.get('input', ''))}, Output len={len(test.get('output', ''))}"
            )

        try:
            filename, test_cnt, group, name = generate_problem_files(problem_data)
            print(f"Files generated successfully: {filename}")
        except Exception as e:
            print(f"Error generating files: {e}")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, format, *args):
        pass


def run():
    server_address = ("127.0.0.1", PORT)
    httpd = HTTPServer(server_address, CompetitiveCompanionHandler)
    print(f"Listening on http://127.0.0.1:{PORT} for Competitive Companion...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()


if __name__ == "__main__":
    run()
