import io
import logging
import os
import socket

STATUS_PHRASES = {
    200: "OK",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
}

logger = logging.getLogger(__name__)


class MyHTTPRequestHandler:
    def __init__(
        self,
        request_stream: io.BufferedIOBase,
        response_stream: io.BufferedIOBase,
    ):
        self.request_stream = request_stream
        self.response_stream = response_stream
        self.command = ""
        self.path = ""
        self.headers = {
            "Content-Type": "text/html",
            "Content-Length": "0",
            "Connection": "close",
        }
        self.data = ""
        self.handle()

    def handle(self) -> None:
        self._parse_request()

        if not self._validate_path():
            self._return_404()
            return

        if self.command == "POST":
            self._return_403()
            return

        if self.command not in ("GET", "HEAD"):
            self._return_405()
            return

        command = getattr(self, f"handle_{self.command}")
        command()
        self.response_stream.flush()

    def handle_GET(self) -> None:
        self.handle_HEAD()

        with open(self.path, "rb") as f:
            body = f.read()

        self.response_stream.write(body)
        self.response_stream.flush()

    def handle_HEAD(self) -> None:
        self._write_response_line(200)
        self._write_headers(**{"Content-Length": os.path.getsize(self.path)})
        self.response_stream.flush()

    def _parse_request(self):
        logger.info("parsing request line")
        requestline = self.request_stream.readline().decode()
        requestline = requestline.rstrip("\r\n")
        logger.info(requestline)

        self.command = requestline.split(" ")[0]
        self.path = requestline.split(" ")[1]

        headers = {}
        line = self.request_stream.readline().decode()
        while line not in ("\r\n", "\n", "\r", ""):
            header = line.rstrip("\r\n").split(": ")
            headers[header[0]] = header[1]
            line = self.request_stream.readline().decode()

        logger.info(headers)

    def _validate_path(self) -> bool:
        self.path = os.path.join(os.getcwd(), self.path.lstrip("/"))
        if os.path.isdir(self.path):
            self.path = os.path.join(self.path, "index.html")

        return os.path.isfile(self.path)

    def _return_404(self) -> None:
        """NOT FOUND"""
        self._write_response_line(404)
        self._write_headers()

    def _return_405(self) -> None:
        """METHOD NOT ALLOWED"""
        self._write_response_line(405)
        self._write_headers()

    def _return_403(self) -> None:
        """FORBIDDEN"""
        self._write_response_line(403)
        self._write_headers()

    def _write_response_line(self, status_code: int) -> None:
        phrase = STATUS_PHRASES.get(status_code, "")
        response_line = f"HTTP/1.1 {status_code} {phrase}\r\n"
        logger.info(response_line.encode())
        self.response_stream.write(response_line.encode())

    def _write_headers(self, *args, **kwargs) -> None:
        headers_copy = self.headers.copy()
        headers_copy.update(**kwargs)
        header_lines = "\r\n".join(f"{k}: {v}" for k, v in headers_copy.items())
        logger.info(header_lines.encode())
        self.response_stream.write(header_lines.encode())
        # mark the end of the headers
        self.response_stream.write(b"\r\n\r\n")
        self.response_stream.flush()


class MyTCPServer:
    def __init__(self, socket_address: tuple[str, int], request_handler) -> None:
        self.request_handler = request_handler
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(socket_address)
        self.sock.listen()

    def server_forever(self) -> None:
        while True:
            conn, addr = self.sock.accept()

            with conn:
                logger.info(f"Accepted connection from {addr}")
                request_stream = conn.makefile("rb")
                response_stream = conn.makefile("wb")
                self.request_handler(
                    request_stream=request_stream, response_stream=response_stream
                )

            logger.info(f"Closed connection from {addr}")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.sock.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    HOST, PORT = "127.0.0.1", 8000
    print(f"Serving HTTP on http://{HOST}:{PORT} ...")
    with MyTCPServer((HOST, PORT), MyHTTPRequestHandler) as server:
        server.server_forever()
