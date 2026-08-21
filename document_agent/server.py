import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .agent import DocumentAgent


WEB_ROOT = Path(__file__).parent / "web"


class DocumentHandler(BaseHTTPRequestHandler):
    agent = DocumentAgent()

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/":
            self._send_file(WEB_ROOT / "index.html", "text/html; charset=utf-8")
            return
        self.send_error(404, "Not found")

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/extract":
            self.send_error(404, "Not found")
            return
        try:
            result = self._extract_upload()
            self._send_json(200, result)
        except (ValueError, OSError) as error:
            self._send_json(400, {"error": str(error)})

    def _extract_upload(self) -> dict:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            raise ValueError("Upload must use multipart/form-data")
        boundary = content_type.split("boundary=", 1)[-1].strip().strip('"').encode()
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        sections = body.split(b"--" + boundary)
        uploads = {}
        for section in sections:
            header, separator, content = section.partition(b"\r\n\r\n")
            if not separator:
                continue
            name_match = re.search(rb'name="([^"]+)"', header)
            if not name_match:
                continue
            field_name = name_match.group(1).decode("utf-8", errors="replace")
            filename_match = re.search(rb'filename="([^"]*)"', header)
            uploads[field_name] = {
                "filename": filename_match.group(1).decode("utf-8", errors="replace")
                if filename_match
                else field_name,
                "content": content.rstrip(b"\r\n"),
            }
        document = uploads.get("document")
        if not document or not document["filename"]:
            raise ValueError("Choose a document before uploading")
        job_description = uploads.get("job_description")
        job_text = job_description["content"].decode("utf-8", errors="replace") if job_description else None
        return self.agent.extract(document["filename"], document["content"], job_text)

    def _send_file(self, path: Path, content_type: str) -> None:
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, status: int, payload: dict) -> None:
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), DocumentHandler)
    print("Document Enalyzer running at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()