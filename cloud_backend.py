import os
import json
import re
import sqlite3
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _load_local_environment():
    env_file = Path(__file__).resolve().parent / ".env"
    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        name, separator, value = line.partition("=")
        if separator and name.strip() and not name.lstrip().startswith("#"):
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


_load_local_environment()


_ACCESS_TOKEN = None
_REFRESH_TOKEN = None
_TOKEN_EXPIRES_AT = 0


class CloudRequestError(RuntimeError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def _settings():
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    key = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
    if not url or not key:
        raise RuntimeError(
            "Cloud sync is not configured. Set SUPABASE_URL and "
            "SUPABASE_PUBLISHABLE_KEY in your environment."
        )
    return url, key


def _request(path, method="GET", payload=None, token=None, prefer=None):
    url, key = _settings()
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "apikey": key,
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    if prefer:
        headers["Prefer"] = prefer
    request = Request(f"{url}/{path.lstrip('/')}", data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read()
    except HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(detail)
            detail = parsed.get("msg") or parsed.get("message") or parsed.get("error_description") or detail
        except (json.JSONDecodeError, AttributeError):
            pass
        raise CloudRequestError(error.code, detail or "Cloud request failed.") from error
    except URLError as error:
        raise RuntimeError(f"Could not reach Supabase: {error.reason}") from error
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as error:
        raise RuntimeError("Supabase returned an unreadable response.") from error


def _store_session(response):
    global _ACCESS_TOKEN, _REFRESH_TOKEN, _TOKEN_EXPIRES_AT
    _ACCESS_TOKEN = response.get("access_token")
    _REFRESH_TOKEN = response.get("refresh_token")
    _TOKEN_EXPIRES_AT = time.time() + int(response.get("expires_in", 3600))


def _require_object(response, action):
    if not isinstance(response, dict):
        raise RuntimeError(f"Supabase returned no account data during {action}.")
    return response


def _response_user(response):
    user = response.get("user")
    if user is None and response.get("id"):
        user = response
    return user


def _access_token():
    global _ACCESS_TOKEN, _REFRESH_TOKEN, _TOKEN_EXPIRES_AT
    if not _ACCESS_TOKEN:
        raise RuntimeError("Sign in to your cloud account first.")
    if _TOKEN_EXPIRES_AT <= time.time() + 60:
        if not _REFRESH_TOKEN:
            raise RuntimeError("Cloud session expired. Sign in again.")
        response = _request(
            "auth/v1/token?grant_type=refresh_token",
            "POST",
            {"refresh_token": _REFRESH_TOKEN},
        )
        _store_session(_require_object(response, "session refresh"))
    return _ACCESS_TOKEN


def _rest(table, method="GET", params=None, payload=None, prefer=None):
    query = urlencode(params or {})
    path = f"rest/v1/{table}"
    if query:
        path = f"{path}?{query}"
    return _request(path, method, payload, _access_token(), prefer)


def is_configured():
    return bool(
        os.environ.get("SUPABASE_URL", "").strip()
        and os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
    )


def sign_up(email, password, username):
    response = _require_object(_request(
        "auth/v1/signup",
        "POST",
        {"email": email.strip(), "password": password, "data": {"username": username.strip()}},
    ), "sign-up")
    if response.get("access_token"):
        _store_session(response)
        return _account(_response_user(response))
    if _response_user(response) is None:
        raise RuntimeError("Supabase did not return an account. Check the email and try again.")
    raise RuntimeError("Check your email to confirm the account, then sign in.")


def _username_email(username):
    username = username.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,32}", username):
        raise ValueError("Username must be 3-32 characters: letters, numbers, _ or -.")
    return f"{username.casefold()}@accounts.leo-investing.invalid"


def sign_up_username(username, password):
    username = username.strip()
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")
    response = _require_object(
        _request(
            "auth/v1/signup",
            "POST",
            {
                "email": _username_email(username),
                "password": password,
                "data": {"username": username},
            },
        ),
        "sign-up",
    )
    if not response.get("access_token"):
        raise RuntimeError(
            "Username-only signup needs email confirmation disabled in Supabase Auth settings. "
            "Then create the account again."
        )
    _store_session(response)
    return _account(_response_user(response))


def sign_in(email, password):
    response = _require_object(_request(
        "auth/v1/token?grant_type=password",
        "POST",
        {"email": email.strip(), "password": password},
    ), "sign-in")
    _store_session(response)
    return _account(_response_user(response))


def sign_in_username_or_email(login, password):
    login = login.strip()
    email = login if "@" in login else _username_email(login)
    return sign_in(email, password)


def sign_out():
    if is_configured():
        global _ACCESS_TOKEN, _REFRESH_TOKEN, _TOKEN_EXPIRES_AT
        if _ACCESS_TOKEN:
            try:
                _request("auth/v1/logout", "POST", token=_ACCESS_TOKEN)
            finally:
                _ACCESS_TOKEN = None
                _REFRESH_TOKEN = None
                _TOKEN_EXPIRES_AT = 0


def change_credentials(user_id, current_password, username, new_password=None):
    current_user = _require_object(
        _request("auth/v1/user", token=_access_token()), "account lookup"
    )
    if current_user is None or str(current_user.get("id")) != user_id:
        raise ValueError("Cloud session is no longer active. Sign in again.")
    sign_in(current_user["email"], current_password)
    attributes = {"data": {"username": username.strip()}}
    if new_password:
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        attributes["password"] = new_password
    response = _require_object(
        _request("auth/v1/user", "PUT", attributes, _access_token()), "account update"
    )
    return _account(response)


def import_legacy_data(user_id, username):
    data_dir = Path(__file__).resolve().parent / "data"
    try:
        portfolio = json.loads((data_dir / "portfolio.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        portfolio = []
    try:
        watchlist = json.loads((data_dir / "watchlist.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        watchlist = []

    local_positions = {}
    local_tickers = set()
    database_path = data_dir / "accounts.sqlite3"
    if database_path.exists():
        connection = sqlite3.connect(
            f"file:{database_path.as_posix()}?mode=ro", uri=True, timeout=5
        )
        connection.row_factory = sqlite3.Row
        try:
            local_user = connection.execute(
                "SELECT id FROM users WHERE username_key = ?",
                (username.strip().casefold(),),
            ).fetchone()
            if local_user:
                local_positions = {
                    row["ticker"]: {
                        "user_id": user_id,
                        "ticker": row["ticker"],
                        "shares": row["shares"],
                        "avg_price": row["avg_price"],
                    }
                    for row in connection.execute(
                        "SELECT ticker, shares, avg_price FROM portfolio WHERE user_id = ?",
                        (local_user["id"],),
                    )
                }
                local_tickers = {
                    row["ticker"]
                    for row in connection.execute(
                        "SELECT ticker FROM watchlist WHERE user_id = ?",
                        (local_user["id"],),
                    )
                }
        except sqlite3.Error:
            pass
        finally:
            connection.close()

    positions_by_ticker = {}
    if isinstance(portfolio, list):
        for item in portfolio:
            if not isinstance(item, dict):
                continue
            ticker = str(item.get("ticker", "")).strip().upper()
            try:
                shares = float(item.get("shares", 0))
                avg_price = float(item.get("avg_price", 0))
            except (TypeError, ValueError):
                continue
            if ticker and shares > 0 and avg_price > 0:
                positions_by_ticker[ticker] = {
                    "user_id": user_id,
                    "ticker": ticker,
                    "shares": shares,
                    "avg_price": avg_price,
                }
    positions_by_ticker.update(local_positions)
    tickers = {
        str(ticker).strip().upper()
        for ticker in (watchlist if isinstance(watchlist, list) else [])
        if str(ticker).strip()
    }
    tickers.update(local_tickers)
    positions = list(positions_by_ticker.values())
    tickers = sorted(tickers)

    if positions:
        _rest(
            "portfolio", "POST", {"on_conflict": "user_id,ticker"}, positions,
            "resolution=merge-duplicates,return=minimal",
        )
    if tickers:
        _rest(
            "watchlist", "POST", {"on_conflict": "user_id,ticker"},
            [{"user_id": user_id, "ticker": ticker} for ticker in tickers],
            "resolution=merge-duplicates,return=minimal",
        )
    return {"positions": len(positions), "watchlist": len(tickers)}


def _account(user):
    if user is None:
        raise RuntimeError("Cloud authentication returned no user.")
    metadata = user.get("user_metadata") or {}
    return {
        "id": str(user.get("id")),
        "username": metadata.get("username") or user.get("email"),
        "email": user.get("email"),
        "cloud": True,
    }


def load_portfolio(user_id):
    rows = _rest(
        "portfolio", params={
            "select": "ticker,shares,avg_price",
            "user_id": f"eq.{user_id}",
            "order": "ticker.asc",
        }
    )
    if not isinstance(rows, list):
        raise RuntimeError("Supabase returned an invalid portfolio response.")
    return rows


def save_portfolio(user_id, items):
    desired = {
        str(item["ticker"]).upper(): {
            "user_id": user_id,
            "ticker": str(item["ticker"]).upper(),
            "shares": float(item["shares"]),
            "avg_price": float(item["avg_price"]),
        }
        for item in items
    }
    if desired:
        _rest(
            "portfolio", "POST", {"on_conflict": "user_id,ticker"},
            list(desired.values()), "resolution=merge-duplicates,return=minimal",
        )
    current_rows = load_portfolio(user_id)
    for current in current_rows:
        if current["ticker"] not in desired:
            _rest(
                "portfolio", "DELETE",
                {"user_id": f"eq.{user_id}", "ticker": f"eq.{current['ticker']}"},
            )


def load_watchlist(user_id):
    rows = _rest(
        "watchlist", params={
            "select": "ticker",
            "user_id": f"eq.{user_id}",
            "order": "ticker.asc",
        }
    )
    if not isinstance(rows, list):
        raise RuntimeError("Supabase returned an invalid watchlist response.")
    return [row["ticker"] for row in rows]


def save_watchlist(user_id, tickers):
    clean = sorted({
        str(ticker).strip().upper() for ticker in tickers if str(ticker).strip()
    })
    if clean:
        _rest(
            "watchlist", "POST", {"on_conflict": "user_id,ticker"},
            [{"user_id": user_id, "ticker": ticker} for ticker in clean],
            "resolution=merge-duplicates,return=minimal",
        )
    current_tickers = set(load_watchlist(user_id))
    for ticker in current_tickers - set(clean):
        _rest(
            "watchlist", "DELETE",
            {"user_id": f"eq.{user_id}", "ticker": f"eq.{ticker}"},
        )


def toggle_watchlist(user_id, ticker):
    ticker = str(ticker).upper().strip()
    existing = _rest(
        "watchlist", params={
            "select": "ticker",
            "user_id": f"eq.{user_id}",
            "ticker": f"eq.{ticker}",
        }
    )
    if existing:
        _rest(
            "watchlist", "DELETE",
            {"user_id": f"eq.{user_id}", "ticker": f"eq.{ticker}"},
        )
        return False
    _rest("watchlist", "POST", payload={"user_id": user_id, "ticker": ticker})
    return True
