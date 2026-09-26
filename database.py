import json
import hashlib
import hmac
import re
import secrets
import sqlite3
from contextlib import closing

from pathlib import Path

from threading import Lock


BASE_DIR = Path(
    __file__
).resolve().parent

DATA_DIR = BASE_DIR / "data"

WATCHLIST_FILE = (
    DATA_DIR
    / "watchlist.json"
)

PORTFOLIO_FILE = (
    DATA_DIR
    / "portfolio.json"
)

DATABASE_FILE = DATA_DIR / "accounts.sqlite3"
PASSWORD_ITERATIONS = 600_000

_LOCK = Lock()


# ============================================================
# FILE SETUP
# ============================================================

def _ensure_files():

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if not WATCHLIST_FILE.exists():

        WATCHLIST_FILE.write_text(
            "[]",
            encoding="utf-8"
        )

    if not PORTFOLIO_FILE.exists():

        PORTFOLIO_FILE.write_text(
            "[]",
            encoding="utf-8"
        )


def _read_json(
    path,
    default
):

    _ensure_files()

    try:

        return json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except (
        json.JSONDecodeError,
        OSError
    ):

        return default


def _write_json(
    path,
    data
):

    _ensure_files()

    path.write_text(

        json.dumps(
            data,
            indent=2
        ),

        encoding="utf-8"
    )


def _connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_FILE, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    with _LOCK, closing(_connect()) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                username_key TEXT NOT NULL UNIQUE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS watchlist (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                ticker TEXT NOT NULL,
                PRIMARY KEY (user_id, ticker)
            );
            CREATE TABLE IF NOT EXISTS portfolio (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                ticker TEXT NOT NULL,
                shares REAL NOT NULL,
                avg_price REAL NOT NULL,
                PRIMARY KEY (user_id, ticker)
            );
            """
        )
        user_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(users)")
        }
        if {"recovery_salt", "recovery_hash"}.issubset(user_columns):
            connection.execute(
                "UPDATE users SET recovery_salt = NULL, recovery_hash = NULL"
            )


def _password_hash(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PASSWORD_ITERATIONS
    ).hex()


def create_account(username, password):
    username = str(username).strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,32}", username):
        raise ValueError("Username must be 3-32 characters: letters, numbers, _ or -.")
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    salt = secrets.token_bytes(16).hex()
    password_hash = _password_hash(password, salt)
    with _LOCK, closing(_connect()) as connection, connection:
        first_account = connection.execute("SELECT 1 FROM users LIMIT 1").fetchone() is None
        try:
            cursor = connection.execute(
                "INSERT INTO users (username, username_key, password_salt, password_hash) "
                "VALUES (?, ?, ?, ?)",
                (username, username.casefold(), salt, password_hash),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("That username is already taken.") from error

        user_id = cursor.lastrowid
        if first_account:
            legacy_watchlist = _read_json(WATCHLIST_FILE, [])
            legacy_portfolio = _read_json(PORTFOLIO_FILE, [])
            connection.executemany(
                "INSERT OR IGNORE INTO watchlist (user_id, ticker) VALUES (?, ?)",
                [(user_id, str(ticker).strip().upper()) for ticker in legacy_watchlist if str(ticker).strip()],
            )
            connection.executemany(
                "INSERT OR REPLACE INTO portfolio (user_id, ticker, shares, avg_price) "
                "VALUES (?, ?, ?, ?)",
                [
                    (user_id, str(item.get("ticker", "")).strip().upper(),
                     float(item.get("shares", 0)), float(item.get("avg_price", 0)))
                    for item in legacy_portfolio
                    if isinstance(item, dict) and str(item.get("ticker", "")).strip()
                ],
            )
    return {"id": user_id, "username": username}


def authenticate_account(username, password):
    with _LOCK, closing(_connect()) as connection, connection:
        row = connection.execute(
            "SELECT id, username, password_salt, password_hash FROM users WHERE username_key = ?",
            (str(username).strip().casefold(),),
        ).fetchone()
    if row is None:
        _password_hash(password, "00000000000000000000000000000000")
        return None
    candidate = _password_hash(password, row["password_salt"])
    if hmac.compare_digest(candidate, row["password_hash"]):
        return {"id": row["id"], "username": row["username"]}
    return None


def change_account_credentials(user_id, current_password, username, new_password=None):
    if isinstance(user_id, str):
        from cloud_backend import change_credentials

        return change_credentials(user_id, current_password, username, new_password)

    username = str(username).strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,32}", username):
        raise ValueError("Username must be 3-32 characters: letters, numbers, _ or -.")
    if new_password and len(new_password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    with _LOCK, closing(_connect()) as connection, connection:
        row = connection.execute(
            "SELECT password_salt, password_hash FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None or not hmac.compare_digest(
            _password_hash(current_password, row["password_salt"]), row["password_hash"]
        ):
            raise ValueError("Current password is incorrect.")

        if new_password:
            password_salt = secrets.token_bytes(16).hex()
            password_hash = _password_hash(new_password, password_salt)
        else:
            password_salt = row["password_salt"]
            password_hash = row["password_hash"]

        try:
            connection.execute(
                "UPDATE users SET username = ?, username_key = ?, password_salt = ?, "
                "password_hash = ? WHERE id = ?",
                (username, username.casefold(), password_salt, password_hash, user_id),
            )
        except sqlite3.IntegrityError as error:
            raise ValueError("That username is already taken.") from error
    return {"id": user_id, "username": username}


# ============================================================
# WATCHLIST
# ============================================================

def load_watchlist(user_id):
    if isinstance(user_id, str):
        from cloud_backend import load_watchlist as cloud_load_watchlist

        return cloud_load_watchlist(user_id)

    with _LOCK, closing(_connect()) as connection, connection:
        rows = connection.execute(
            "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY ticker", (user_id,)
        ).fetchall()
    return [row["ticker"] for row in rows]


def save_watchlist(user_id, tickers):
    if isinstance(user_id, str):
        from cloud_backend import save_watchlist as cloud_save_watchlist

        return cloud_save_watchlist(user_id, tickers)
    clean = sorted({str(ticker).strip().upper() for ticker in tickers if str(ticker).strip()})
    with _LOCK, closing(_connect()) as connection, connection:
        connection.execute("DELETE FROM watchlist WHERE user_id = ?", (user_id,))
        connection.executemany(
            "INSERT INTO watchlist (user_id, ticker) VALUES (?, ?)",
            [(user_id, ticker) for ticker in clean],
        )


def toggle_watchlist(user_id, ticker):
    if isinstance(user_id, str):
        from cloud_backend import toggle_watchlist as cloud_toggle_watchlist

        return cloud_toggle_watchlist(user_id, ticker)
    ticker = str(ticker).upper().strip()
    with _LOCK, closing(_connect()) as connection, connection:
        existing = connection.execute(
            "SELECT 1 FROM watchlist WHERE user_id = ? AND ticker = ?", (user_id, ticker)
        ).fetchone()
        if existing:
            connection.execute(
                "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?", (user_id, ticker)
            )
            return False
        connection.execute(
            "INSERT INTO watchlist (user_id, ticker) VALUES (?, ?)", (user_id, ticker)
        )
        return True


# ============================================================
# PORTFOLIO
# ============================================================

def load_portfolio(user_id):
    if isinstance(user_id, str):
        from cloud_backend import load_portfolio as cloud_load_portfolio

        return cloud_load_portfolio(user_id)
    with _LOCK, closing(_connect()) as connection, connection:
        rows = connection.execute(
            "SELECT ticker, shares, avg_price FROM portfolio WHERE user_id = ? ORDER BY ticker",
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def save_portfolio(user_id, items):
    if isinstance(user_id, str):
        from cloud_backend import save_portfolio as cloud_save_portfolio

        return cloud_save_portfolio(user_id, items)
    with _LOCK, closing(_connect()) as connection, connection:
        connection.execute("DELETE FROM portfolio WHERE user_id = ?", (user_id,))
        connection.executemany(
            "INSERT INTO portfolio (user_id, ticker, shares, avg_price) VALUES (?, ?, ?, ?)",
            [
                (user_id, item["ticker"].upper(), float(item["shares"]), float(item["avg_price"]))
                for item in items
            ],
        )


def add_position(
    user_id,
    ticker,
    shares,
    price
):

    ticker = (
        ticker
        .upper()
        .strip()
    )

    shares = float(shares)

    price = float(price)

    if (
        shares <= 0
        or price <= 0
    ):

        raise ValueError(
            "Shares and price must both be greater than zero."
        )

    items = load_portfolio(user_id)

    for item in items:

        if (
            item
            .get(
                "ticker",
                ""
            )
            .upper()
            == ticker
        ):

            old_shares = float(
                item.get(
                    "shares",
                    0
                )
            )

            old_avg = float(
                item.get(
                    "avg_price",
                    0
                )
            )

            total_shares = (
                old_shares
                + shares
            )

            weighted_avg = (

                (
                    old_shares
                    * old_avg
                )

                +

                (
                    shares
                    * price
                )

            ) / total_shares

            item["shares"] = (
                total_shares
            )

            item["avg_price"] = (
                weighted_avg
            )

            save_portfolio(user_id, items)

            return

    items.append({

        "ticker": ticker,

        "shares": shares,

        "avg_price": price

    })

    save_portfolio(user_id, items)


def remove_position(user_id, ticker):
    ticker = str(ticker).upper().strip()
    items = [
        item for item in load_portfolio(user_id)
        if item.get("ticker", "").upper() != ticker
    ]
    save_portfolio(user_id, items)