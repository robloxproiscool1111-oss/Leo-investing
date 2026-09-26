import yfinance as yf


def get_chart_data(ticker):

    stock = yf.Ticker(ticker)

    history = stock.history(
        period="1y"
    )


    # Current price
    try:
        current_price = stock.fast_info["lastPrice"]
    except:
        current_price = "Unknown"


    # Moving averages
    history["MA50"] = (
        history["Close"]
        .rolling(50)
        .mean()
    )

    history["MA200"] = (
        history["Close"]
        .rolling(200)
        .mean()
    )


    # RSI
    delta = history["Close"].diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )


    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()


    rs = avg_gain / avg_loss

    rsi = 100 - (
        100 /
        (1 + rs)
    )


    latest = history.iloc[-1]


    data = f"""
Stock: {ticker}

CURRENT PRICE:
${current_price}


TECHNICAL DATA:

Latest Close:
{latest['Close']}

50 Day Moving Average:
{latest['MA50']}

200 Day Moving Average:
{latest['MA200']}

RSI:
{rsi.iloc[-1]}


RECENT PRICE DATA:

{history.tail(10)[['Close','Volume']].to_string()}


YEAR HIGH:
{history['Close'].max()}


YEAR LOW:
{history['Close'].min()}
"""

    print(data)
    return data