import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from stock_data import get_history, get_quote, search_stocks

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# LEO INVESTING WEB PAGE
# ============================================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Leo Investing</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #050505;
    color: white;
    font-family: Arial, Helvetica, sans-serif;
}

.app {
    display: flex;
    min-height: 100vh;
}

/* SIDEBAR */

.sidebar {
    width: 230px;
    min-height: 100vh;
    background: #090909;
    border-right: 1px solid #1c1c1c;
    padding: 25px 15px;
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
}

.logo {
    font-size: 25px;
    font-weight: 800;
    padding: 10px 15px 35px;
}

.logo span {
    color: #00ff88;
}

.nav {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.nav button {
    border: 0;
    background: transparent;
    color: #999;
    text-align: left;
    padding: 14px 16px;
    border-radius: 10px;
    font-size: 15px;
    cursor: pointer;
}

.nav button:hover,
.nav button.active {
    background: #151515;
    color: white;
}

.nav button.active {
    color: #00ff88;
}

/* MAIN */

.main {
    margin-left: 230px;
    width: calc(100% - 230px);
    padding: 35px;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
}

.header h1 {
    margin: 0;
    font-size: 30px;
}

.search {
    display: flex;
    gap: 8px;
}

.search input {
    width: 260px;
    background: #111;
    border: 1px solid #292929;
    color: white;
    border-radius: 10px;
    padding: 13px 15px;
    outline: none;
}

.search input:focus {
    border-color: #00ff88;
}

button.green {
    background: #00ff88;
    color: black;
    border: none;
    border-radius: 10px;
    padding: 12px 18px;
    font-weight: bold;
    cursor: pointer;
}

button.green:hover {
    opacity: .85;
}

/* CARDS */

.cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
    margin-bottom: 25px;
}

.card {
    background: #111;
    border: 1px solid #202020;
    border-radius: 15px;
    padding: 22px;
}

.card-title {
    color: #888;
    font-size: 13px;
    margin-bottom: 10px;
}

.card-value {
    font-size: 27px;
    font-weight: bold;
}

.green-text {
    color: #00ff88;
}

.red-text {
    color: #ff4040;
}

/* STOCK */

.stock-panel {
    background: #111;
    border: 1px solid #202020;
    border-radius: 15px;
    padding: 25px;
    margin-top: 20px;
}

.stock-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.stock-symbol {
    font-size: 28px;
    font-weight: bold;
}

.stock-price {
    font-size: 28px;
    font-weight: bold;
}

.chart {
    height: 300px;
    margin-top: 25px;
    background: #080808;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #555;
}

.results {
    margin-top: 10px;
    background: #111;
    border: 1px solid #222;
    border-radius: 10px;
    overflow: hidden;
}

.result {
    padding: 14px;
    cursor: pointer;
    border-bottom: 1px solid #222;
}

.result:hover {
    background: #191919;
}

.hidden {
    display: none;
}

.message {
    margin-top: 15px;
    color: #888;
}

@media(max-width: 800px) {

    .sidebar {
        width: 70px;
        padding: 15px 8px;
    }

    .logo {
        font-size: 0;
        text-align: center;
    }

    .logo span {
        font-size: 25px;
    }

    .nav button {
        font-size: 0;
        text-align: center;
    }

    .main {
        margin-left: 70px;
        width: calc(100% - 70px);
        padding: 20px;
    }

    .cards {
        grid-template-columns: 1fr;
    }

    .header {
        flex-direction: column;
        align-items: stretch;
        gap: 15px;
    }

    .search input {
        width: 100%;
    }
}
</style>
</head>

<body>

<div class="app">

    <aside class="sidebar">

        <div class="logo">
            LEO <span>INVESTING</span>
        </div>

        <div class="nav">

            <button class="active" onclick="showHome(this)">
                🏠 Home
            </button>

            <button onclick="focusSearch(this)">
                🔍 Search
            </button>

            <button onclick="showPortfolio(this)">
                💼 Portfolio
            </button>

            <button onclick="showWatchlist(this)">
                ⭐ Watchlist
            </button>

            <button onclick="showAdvisor(this)">
                🤖 AI Advisor
            </button>

        </div>

    </aside>


    <main class="main">

        <div class="header">

            <h1 id="pageTitle">
                Welcome to Leo Investing
            </h1>

            <div class="search">

                <input
                    id="searchInput"
                    placeholder="Search stocks..."
                    autocomplete="off"
                    oninput="searchStocks()"
                >

                <button class="green" onclick="searchStocks()">
                    Search
                </button>

            </div>

        </div>


        <div id="results" class="results hidden"></div>


        <section id="homePage">

            <div class="cards">

                <div class="card">
                    <div class="card-title">
                        Portfolio Value
                    </div>

                    <div class="card-value" id="portfolioValue">
                        $0.00
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">
                        Today's Change
                    </div>

                    <div class="card-value green-text">
                        +0.00%
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">
                        Stocks Tracked
                    </div>

                    <div class="card-value" id="tracked">
                        0
                    </div>
                </div>

            </div>


            <div class="stock-panel">

                <div class="stock-header">

                    <div>
                        <div class="card-title">
                            STOCK LOOKUP
                        </div>

                        <div class="stock-symbol" id="ticker">
                            Search for a stock
                        </div>
                    </div>

                    <div class="stock-price" id="price">
                        —
                    </div>

                </div>


                <div class="chart" id="chart">
                    Search for a stock above to see its price.
                </div>

            </div>

        </section>


        <section id="otherPage" class="hidden">

            <div class="stock-panel">

                <h2 id="otherTitle">
                    Coming Soon
                </h2>

                <p class="message" id="otherMessage">
                    This section is being connected to Leo Investing.
                </p>

            </div>

        </section>

    </main>

</div>


<script>

let searchTimer = null;


async function searchStocks() {

    const input = document.getElementById("searchInput");
    const results = document.getElementById("results");

    const query = input.value.trim();

    if (!query) {
        results.classList.add("hidden");
        return;
    }

    clearTimeout(searchTimer);

    searchTimer = setTimeout(async () => {

        try {

            const response =
                await fetch("/api/search?q=" + encodeURIComponent(query));

            const data = await response.json();

            results.innerHTML = "";

            if (!Array.isArray(data) || data.length === 0) {

                results.innerHTML =
                    '<div class="result">No stocks found.</div>';

                results.classList.remove("hidden");

                return;
            }


            data.forEach(stock => {

                const ticker =
                    stock.ticker ||
                    stock.symbol ||
                    stock.code ||
                    "";

                const name =
                    stock.name ||
                    stock.company ||
                    ticker;

                const item =
                    document.createElement("div");

                item.className = "result";

                item.innerHTML =
                    "<strong>" +
                    ticker +
                    "</strong> — " +
                    name;

                item.onclick = () => {

                    input.value = ticker;

                    results.classList.add("hidden");

                    loadStock(ticker);

                };

                results.appendChild(item);

            });

            results.classList.remove("hidden");

        } catch (error) {

            results.innerHTML =
                '<div class="result">Unable to search right now.</div>';

            results.classList.remove("hidden");

        }

    }, 250);

}


async function loadStock(ticker) {

    document.getElementById("ticker").textContent = ticker;

    document.getElementById("price").textContent = "...";

    document.getElementById("chart").textContent =
        "Loading stock data...";


    try {

        const quoteResponse =
            await fetch(
                "/api/quote?ticker=" +
                encodeURIComponent(ticker)
            );

        const quote = await quoteResponse.json();


        if (quote.error) {

            document.getElementById("price").textContent = "N/A";

            document.getElementById("chart").textContent =
                quote.error;

            return;
        }


        const price =
            quote.price ??
            quote.lastPrice ??
            quote.currentPrice;


        if (price !== undefined && price !== null) {

            document.getElementById("price").textContent =
                "$" + Number(price).toFixed(2);

        }


        loadHistory(ticker);


    } catch (error) {

        document.getElementById("price").textContent = "N/A";

        document.getElementById("chart").textContent =
            "Unable to load stock data.";

    }

}


async function loadHistory(ticker) {

    try {

        const response =
            await fetch(
                "/api/history?ticker=" +
                encodeURIComponent(ticker) +
                "&period=1Y"
            );

        const data = await response.json();

        if (!data.points || data.points.length === 0) {

            document.getElementById("chart").textContent =
                "No chart data available.";

            return;

        }


        const points = data.points;

        const values =
            points.map(point => point.close);

        const min =
            Math.min(...values);

        const max =
            Math.max(...values);


        let svg =
            '<svg width="100%" height="100%" viewBox="0 0 1000 300" preserveAspectRatio="none">';

        let path = "";

        points.forEach((point, index) => {

            const x =
                (index / (points.length - 1)) * 1000;

            const normalized =
                (point.close - min) /
                ((max - min) || 1);

            const y =
                270 - normalized * 240;

            path +=
                (index === 0 ? "M " : " L ") +
                x +
                " " +
                y;

        });


        svg +=
            '<path d="' +
            path +
            '" fill="none" stroke="#00ff88" stroke-width="4"/>';

        svg += "</svg>";


        document.getElementById("chart").innerHTML = svg;


    } catch (error) {

        document.getElementById("chart").textContent =
            "Chart unavailable.";

    }

}


function setActive(button) {

    document
        .querySelectorAll(".nav button")
        .forEach(btn => btn.classList.remove("active"));

    button.classList.add("active");

}


function showHome(button) {

    setActive(button);

    document.getElementById("pageTitle").textContent =
        "Welcome to Leo Investing";

    document.getElementById("homePage")
        .classList.remove("hidden");

    document.getElementById("otherPage")
        .classList.add("hidden");

}


function focusSearch(button) {

    setActive(button);

    document.getElementById("searchInput").focus();

}


function showPortfolio(button) {

    setActive(button);

    document.getElementById("homePage")
        .classList.add("hidden");

    document.getElementById("otherPage")
        .classList.remove("hidden");

    document.getElementById("pageTitle").textContent =
        "Portfolio";

    document.getElementById("otherTitle").textContent =
        "💼 Portfolio";

    document.getElementById("otherMessage").textContent =
        "Your portfolio section is ready to be connected.";

}


function showWatchlist(button) {

    setActive(button);

    document.getElementById("homePage")
        .classList.add("hidden");

    document.getElementById("otherPage")
        .classList.remove("hidden");

    document.getElementById("pageTitle").textContent =
        "Watchlist";

    document.getElementById("otherTitle").textContent =
        "⭐ Watchlist";

    document.getElementById("otherMessage").textContent =
        "Your watchlist section is ready to be connected.";

}


function showAdvisor(button) {

    setActive(button);

    document.getElementById("homePage")
        .classList.add("hidden");

    document.getElementById("otherPage")
        .classList.remove("hidden");

    document.getElementById("pageTitle").textContent =
        "Leo AI Advisor";

    document.getElementById("otherTitle").textContent =
        "🤖 Leo AI Advisor";

    document.getElementById("otherMessage").textContent =
        "AI Advisor connection will be added here.";

}

</script>

</body>
</html>
"""


# ============================================================
# SERVER
# ============================================================

class WebHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def end_headers(self):

        self.send_header(
            "X-Content-Type-Options",
            "nosniff"
        )

        self.send_header(
            "Referrer-Policy",
            "strict-origin-when-cross-origin"
        )

        self.send_header(
            "X-Frame-Options",
            "DENY"
        )

        super().end_headers()


    def send_json(self, payload, status=200):

        body = json.dumps(
            payload,
            allow_nan=False
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.send_header(
            "Cache-Control",
            "no-store"
        )

        self.end_headers()

        self.wfile.write(body)


    def do_GET(self):

        parsed = urlparse(self.path)

        params = parse_qs(parsed.query)


        # HOME PAGE
        if parsed.path == "/":

            body = HTML.encode("utf-8")

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )

            self.send_header(
                "Content-Length",
                str(len(body))
            )

            self.end_headers()

            self.wfile.write(body)

            return


        # CONFIG
        if parsed.path == "/api/config":

            self.send_json({
                "supabaseUrl":
                    os.environ.get(
                        "SUPABASE_URL",
                        ""
                    ).strip(),

                "supabaseKey":
                    os.environ.get(
                        "SUPABASE_PUBLISHABLE_KEY",
                        ""
                    ).strip(),
            })

            return


        # SEARCH
        if parsed.path == "/api/search":

            query = params.get(
                "q",
                [""]
            )[0][:80]

            try:

                self.send_json(
                    search_stocks(
                        query,
                        max_results=10
                    )
                )

            except Exception as error:

                self.send_json(
                    {"error": str(error)},
                    502
                )

            return


        # QUOTE
        if parsed.path == "/api/quote":

            ticker = params.get(
                "ticker",
                [""]
            )[0].strip().upper()


            if not ticker or len(ticker) > 16:

                self.send_json(
                    {
                        "error":
                        "Enter a valid stock ticker."
                    },
                    400
                )

                return


            try:

                quote = get_quote(ticker)

                if quote.get("price") is None:

                    self.send_json(
                        {
                            "error":
                            f"No quote found for {ticker}."
                        },
                        404
                    )

                else:

                    self.send_json(quote)

            except Exception as error:

                self.send_json(
                    {"error": str(error)},
                    502
                )

            return


        # HISTORY
        if parsed.path == "/api/history":

            ticker = params.get(
                "ticker",
                [""]
            )[0].strip().upper()

            period = params.get(
                "period",
                ["1Y"]
            )[0].upper()


            if not ticker or len(ticker) > 16:

                self.send_json(
                    {
                        "error":
                        "Enter a valid stock ticker."
                    },
                    400
                )

                return


            try:

                history = get_history(
                    ticker,
                    period
                )


                if (
                    history.empty
                    or "Close" not in history
                ):

                    self.send_json(
                        {"points": []}
                    )

                    return


                points = [

                    {
                        "date":
                            stamp.isoformat(),

                        "close":
                            float(close)
                    }

                    for stamp, close
                    in history["Close"]
                    .dropna()
                    .items()

                ]


                self.send_json({
                    "points": points
                })


            except Exception as error:

                self.send_json(
                    {"error": str(error)},
                    502
                )

            return


        # FALLBACK
        self.send_error(404, "File not found.")


    def log_message(self, fmt, *args):

        print(
            f"[web] "
            f"{self.address_string()} - "
            f"{fmt % args}"
        )


# ============================================================
# START SERVER
# ============================================================

def main():

    host = os.environ.get(
        "WEB_HOST",
        "0.0.0.0"
    )

    port = int(
        os.environ.get(
            "PORT",
            os.environ.get(
                "WEB_PORT",
                "8000"
            )
        )
    )


    server = ThreadingHTTPServer(
        (host, port),
        WebHandler
    )


    print(
        f"Leo Investing web app running "
        f"at http://{host}:{port}"
    )


    try:

        server.serve_forever()

    except KeyboardInterrupt:

        print(
            "\nStopping Leo Investing web app."
        )

    finally:

        server.server_close()


if __name__ == "__main__":
    main()
