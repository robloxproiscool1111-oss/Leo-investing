import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from stock_data import get_history, get_quote, search_stocks

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "dist"
WEB_DIR = DIST_DIR if (DIST_DIR / "index.html").exists() else BASE_DIR / "web"


def load_env():
    try:
        lines = (BASE_DIR / ".env").read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        name, separator, value = line.partition("=")
        if separator and name.strip() and not name.lstrip().startswith("#"):
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


load_env()


class WebHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("X-Frame-Options", "DENY")
        super().end_headers()

    def send_json(self, payload, status=200):
        body = json.dumps(payload, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if parsed.path == "/api/config":
            self.send_json({
                "supabaseUrl": os.environ.get("SUPABASE_URL", "").strip(),
                "supabaseKey": os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip(),
            })
            return
        if parsed.path == "/api/search":
            query = params.get("q", [""])[0][:80]
            try:
                self.send_json(search_stocks(query, max_results=10))
            except Exception as error:
                self.send_json({"error": str(error)}, 502)
            return
        if parsed.path == "/api/quote":
            ticker = params.get("ticker", [""])[0].strip().upper()
            if not ticker or len(ticker) > 16:
                self.send_json({"error": "Enter a valid stock ticker."}, 400)
                return
            try:
                quote = get_quote(ticker)
                if quote.get("price") is None:
                    self.send_json({"error": f"No quote found for {ticker}."}, 404)
                else:
                    self.send_json(quote)
            except Exception as error:
                self.send_json({"error": str(error)}, 502)
            return
        if parsed.path == "/api/history":
            ticker = params.get("ticker", [""])[0].strip().upper()
            period = params.get("period", ["1Y"])[0].upper()
            if not ticker or len(ticker) > 16:
                self.send_json({"error": "Enter a valid stock ticker."}, 400)
                return
            try:
                history = get_history(ticker, period)
                if history.empty or "Close" not in history:
                    self.send_json({"points": []})
                    return
                points = [
                    {"date": stamp.isoformat(), "close": float(close)}
                    for stamp, close in history["Close"].dropna().items()
                ]
                self.send_json({"points": points})
            except Exception as error:
                self.send_json({"error": str(error)}, 502)
            return
        if parsed.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def log_message(self, fmt, *args):
        print(f"[web] {self.address_string()} - {fmt % args}")


def main():
    host = os.environ.get(
        "WEB_HOST", "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"
    )
    port = int(os.environ.get("PORT", os.environ.get("WEB_PORT", "8000")))
    server = ThreadingHTTPServer((host, port), WebHandler)
    print(f"Leo Investing web app running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Leo Investing web app.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
