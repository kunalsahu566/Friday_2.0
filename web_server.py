"""Local web interface for Friday 2.0.

Run `python3 web_server.py` and open http://127.0.0.1:8000.
The server deliberately listens only on this computer.
"""

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB_DIR = Path(__file__).parent / "Website"


class FridayWebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/status":
            from ai.llm import MODEL
            self._send_json({"online": True, "name": "Friday 2.0", "provider": "ollama", "model": MODEL})
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
            return
        try:
            self._extracted_from_do_POST_8()
        except (ValueError, json.JSONDecodeError) as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
        except Exception as error:
            self._send_json({"error": f"Friday could not complete that request: {error}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

    # TODO Rename this here and in `do_POST`
    def _extracted_from_do_POST_8(self):
        # Delay optional assistant dependencies until a chat command is sent,
        # so the interface can still load and report its status after setup.
        from core.router import process_command

        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length))
        message = str(payload.get("message", "")).strip()
        if not message:
            raise ValueError("Please enter a message for Friday.")

        replies = []
        process_command(message, message_callback=lambda speaker, text: replies.append(str(text)) if speaker == "Friday" else None)
        self._send_json({"reply": replies[-1] if replies else "I completed that request."})

    def _send_json(self, data, status=HTTPStatus.OK):
        encoded = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        print(f"[Friday Web] {format % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), FridayWebHandler)
    print("Friday 2.0 is available at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nFriday web server stopped.")
    finally:
        server.server_close()

