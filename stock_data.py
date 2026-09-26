from functools import lru_cache

import pandas as pd

import yfinance as yf


# ============================================================
# HISTORY RANGES
# ============================================================

PERIOD_MAP = {

    "1D": (
        "1d",
        "5m"
    ),

    "1W": (
        "5d",
        "30m"
    ),

    "1M": (
        "1mo",
        "1d"
    ),

    "3M": (
        "3mo",
        "1d"
    ),

    "6M": (
        "6mo",
        "1d"
    ),

    "YTD": (
        "ytd",
        "1d"
    ),

    "1Y": (
        "1y",
        "1d"
    ),

    "5Y": (
        "5y",
        "1wk"
    ),

    "ALL": (
        "max",
        "1mo"
    ),
}


# ============================================================
# HELPERS
# ============================================================

def _number(value):

    try:

        if (
            value is None
            or pd.isna(value)
        ):

            return None

        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return None


def _last_close(history):

    if (
        history is None
        or history.empty
        or "Close" not in history
    ):

        return None

    series = (
        history["Close"]
        .dropna()
    )

    if series.empty:

        return None

    return _number(
        series.iloc[-1]
    )


def _previous_close(history):

    if (
        history is None
        or history.empty
        or "Close" not in history
    ):

        return None

    series = (
        history["Close"]
        .dropna()
    )

    if len(series) < 2:

        return None

    return _number(
        series.iloc[-2]
    )


# ============================================================
# QUOTE
# ============================================================

@lru_cache(
    maxsize=128
)
def get_quote(ticker):

    ticker = (
        ticker
        .upper()
        .strip()
    )

    stock = yf.Ticker(ticker)

    # Basic company / market info
    try:

        info = (
            stock.get_info()
            or {}
        )

    except Exception:

        info = {}

    # Recent price fallback
    try:

        recent = stock.history(

            period="5d",

            interval="1d",

            auto_adjust=False

        )

    except Exception:

        recent = pd.DataFrame()

    price = (

        _number(
            info.get(
                "currentPrice"
            )
        )

        or

        _number(
            info.get(
                "regularMarketPrice"
            )
        )

        or

        _last_close(recent)

    )

    previous = (

        _number(
            info.get(
                "previousClose"
            )
        )

        or

        _previous_close(recent)

    )

    gain = None

    change_percent = None

    if (
        price is not None
        and previous not in (
            None,
            0
        )
    ):

        gain = (
            price
            - previous
        )

        change_percent = (

            gain
            / previous

        ) * 100

    # 52 week values
    week_52_low = _number(
        info.get(
            "fiftyTwoWeekLow"
        )
    )

    week_52_high = _number(
        info.get(
            "fiftyTwoWeekHigh"
        )
    )

    if (
        week_52_low is None
        or week_52_high is None
    ):

        try:

            year = stock.history(

                period="1y",

                interval="1d",

                auto_adjust=False

            )

            if not year.empty:

                if week_52_low is None:

                    week_52_low = _number(
                        year["Low"].min()
                    )

                if week_52_high is None:

                    week_52_high = _number(
                        year["High"].max()
                    )

        except Exception:

            pass

    return {

        "ticker":
            ticker,

        "company":
            info.get("longName")
            or info.get("shortName")
            or ticker,

        "sector":
            info.get("sector")
            or "",

        "industry":
            info.get("industry")
            or "",

        "website":
            info.get("website")
            or "",

        "summary":
            info.get(
                "longBusinessSummary"
            )
            or "",

        "price":
            price,

        "previous_close":
            previous,

        "gain":
            gain,

        "change_percent":
            change_percent,

        "day_low":
            _number(
                info.get("dayLow")
                or info.get(
                    "regularMarketDayLow"
                )
            ),

        "day_high":
            _number(
                info.get("dayHigh")
                or info.get(
                    "regularMarketDayHigh"
                )
            ),

        "week_52_low":
            week_52_low,

        "week_52_high":
            week_52_high,

        "market_cap":
            _number(
                info.get(
                    "marketCap"
                )
            ),

        "pe_ratio":
            _number(
                info.get(
                    "trailingPE"
                )
            ),

        "forward_pe":
            _number(
                info.get(
                    "forwardPE"
                )
            ),

        "eps":
            _number(
                info.get(
                    "trailingEps"
                )
            ),

        "forward_eps":
            _number(
                info.get(
                    "forwardEps"
                )
            ),

        "beta":
            _number(
                info.get(
                    "beta"
                )
            ),

        "dividend_yield":
            _number(
                info.get(
                    "dividendYield"
                )
            ),

        "volume":
            _number(
                info.get("volume")
                or info.get(
                    "regularMarketVolume"
                )
            ),

        "avg_volume":
            _number(
                info.get(
                    "averageVolume"
                )
            ),

        "price_to_book":
            _number(
                info.get(
                    "priceToBook"
                )
            ),

        "profit_margin":
            _number(
                info.get(
                    "profitMargins"
                )
            ),

        "revenue_growth":
            _number(
                info.get(
                    "revenueGrowth"
                )
            ),

        "earnings_growth":
            _number(
                info.get(
                    "earningsGrowth"
                )
            ),

        "debt_to_equity":
            _number(
                info.get(
                    "debtToEquity"
                )
            ),

        "return_on_equity":
            _number(
                info.get(
                    "returnOnEquity"
                )
            ),

        "free_cash_flow":
            _number(
                info.get(
                    "freeCashflow"
                )
            ),

        "target_mean_price":
            _number(
                info.get(
                    "targetMeanPrice"
                )
            ),

        "analyst_count":
            _number(
                info.get(
                    "numberOfAnalystOpinions"
                )
            ),
    }


# ============================================================
# HISTORICAL DATA
# ============================================================

def get_history(
    ticker,
    range_name="1Y"
):

    ticker = (
        ticker
        .upper()
        .strip()
    )

    period, interval = PERIOD_MAP.get(

        range_name,

        PERIOD_MAP["1Y"]

    )

    stock = yf.Ticker(ticker)

    try:

        history = stock.history(

            period=period,

            interval=interval,

            auto_adjust=False,

            prepost=False,

        )

    except Exception:

        return pd.DataFrame()

    if history is None:

        return pd.DataFrame()

    if "Close" in history:

        return history.dropna(
            subset=["Close"]
        )

    return history


def history_performance(history):

    if (
        history is None
        or history.empty
        or "Close" not in history
    ):

        return (
            None,
            None
        )

    closes = (
        history["Close"]
        .dropna()
    )

    if len(closes) < 2:

        return (
            None,
            None
        )

    start = _number(
        closes.iloc[0]
    )

    end = _number(
        closes.iloc[-1]
    )

    if (
        start in (
            None,
            0
        )
        or end is None
    ):

        return (
            None,
            None
        )

    gain = (
        end
        - start
    )

    pct = (

        gain
        / start

    ) * 100

    return (
        gain,
        pct
    )


# ============================================================
# SEARCH
# ============================================================

def search_stocks(
    query,
    max_results=6
):

    query = query.strip()

    if not query:

        return []

    try:

        results = yf.Search(

            query,

            max_results=max_results,

            news_count=0

        ).quotes

    except Exception:

        results = []

    clean = []

    seen = set()

    for result in (
        results
        or []
    ):

        symbol = str(
            result.get(
                "symbol",
                ""
            )
        ).upper().strip()

        quote_type = str(
            result.get(
                "quoteType",
                ""
            )
        ).upper()

        if (
            not symbol
            or symbol in seen
        ):

            continue

        if (
            quote_type
            and quote_type
            not in {
                "EQUITY",
                "ETF"
            }
        ):

            continue

        seen.add(symbol)

        clean.append({

            "ticker":
                symbol,

            "company":
                result.get("longname")
                or result.get("shortname")
                or symbol,

            "exchange":
                result.get("exchange")
                or "",

            "quote_type":
                quote_type
                or "EQUITY",

        })

        if (
            len(clean)
            >= max_results
        ):

            break

    # Direct ticker fallback
    if not clean:

        symbol = query.upper()

        try:

            quote = get_quote(
                symbol
            )

            if (
                quote.get(
                    "price"
                )
                is not None
            ):

                clean.append({

                    "ticker":
                        symbol,

                    "company":
                        quote.get(
                            "company",
                            symbol
                        )

                })

        except Exception:

            pass

    return clean