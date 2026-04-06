import os
import io
import base64
import requests
from PIL import Image
from dotenv import load_dotenv
from langchain_community.tools import ArxivQueryRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper, ArxivAPIWrapper
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

load_dotenv()


# --- ArXiv Tool ---
arxiv_wrapper = ArxivAPIWrapper(top_k_results=3, doc_content_chars_max=1500)
arxiv_tool = ArxivQueryRun(api_wrapper=arxiv_wrapper)


# --- Wikipedia Tool ---
wiki_wrapper = WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=1500)
wiki_tool = WikipediaQueryRun(api_wrapper=wiki_wrapper)


# --- Tavily Search Tool ---
tavily_tool = TavilySearch(max_results=5)


# --- Weather Tool ---
@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city. Returns temperature, conditions, humidity, and wind speed."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Weather tool is unavailable: OPENWEATHER_API_KEY is not set in the environment."

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            desc = data["weather"][0]["description"].capitalize()
            temp = data["main"]["temp"]
            feels = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]
            country = data["sys"]["country"]
            return (
                f"Weather in {city.title()}, {country}:\n"
                f"- Condition: {desc}\n"
                f"- Temperature: {temp}°C (feels like {feels}°C)\n"
                f"- Humidity: {humidity}%\n"
                f"- Wind Speed: {wind} m/s"
            )
        elif response.status_code == 404:
            return f"City '{city}' not found. Please check the city name and try again."
        else:
            return f"Weather API error (status {response.status_code}). Please try again later."
    except requests.exceptions.Timeout:
        return "Weather request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Failed to fetch weather: {str(e)}"


# --- Crypto Price Tool ---
_NOISE_WORDS = {"coin", "token", "crypto", "price", "network", "protocol"}

def _format_price(price) -> str:
    """Format a crypto price with appropriate decimal places and $ symbol."""
    if price == "N/A":
        return "$N/A"
    if price >= 1:
        return f"${price:,.2f}"
    elif price >= 0.01:
        return f"${price:,.4f}"
    elif price >= 0.0001:
        return f"${price:,.6f}"
    else:
        return f"${price:,.8f}"

def _resolve_crypto_id(query: str) -> str | None:
    """Search CoinGecko for the best matching coin ID for a given name/symbol.
    Tries progressively simplified versions of the query to improve matching."""
    search_url = "https://api.coingecko.com/api/v3/search"

    # Build candidate queries: stripped first (cleaner match), then original, then first word
    words = query.lower().split()
    stripped = " ".join(w for w in words if w not in _NOISE_WORDS)
    candidates = dict.fromkeys(filter(None, [stripped, query.lower(), words[0] if words else None]))

    for candidate in candidates:
        try:
            resp = requests.get(search_url, params={"query": candidate}, timeout=10)
            if resp.status_code == 200:
                coins = resp.json().get("coins", [])
                if coins:
                    return coins[0]["id"]
        except requests.exceptions.RequestException:
            pass
    return None


@tool
def get_crypto_price(crypto_id: str) -> str:
    """Get the current price and market data for a cryptocurrency.
    Pass any coin name or symbol (e.g. 'pi', 'pi coin', 'pi network', 'bitcoin', 'eth').
    The tool will automatically resolve the correct CoinGecko ID if needed.
    Returns price in USD, 24h change, market cap, and other key metrics."""

    # CoinGecko API is free for basic usage
    url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            resolved = _resolve_crypto_id(crypto_id)
            if resolved and resolved != crypto_id:
                url = f"https://api.coingecko.com/api/v3/coins/{resolved}"
                response = requests.get(url, timeout=10)
            if response.status_code == 404:
                return f"Cryptocurrency '{crypto_id}' not found on CoinGecko. It may not be listed yet."
        if response.status_code == 200:
            data = response.json()
            
            # Extract key data
            name = data.get("name", "Unknown")
            symbol = data.get("symbol", "").upper()
            current_price = data.get("market_data", {}).get("current_price", {}).get("usd", "N/A")
            price_change_24h = data.get("market_data", {}).get("price_change_percentage_24h", "N/A")
            market_cap = data.get("market_data", {}).get("market_cap", {}).get("usd", "N/A")
            market_cap_rank = data.get("market_cap_rank", "N/A")
            circulating_supply = data.get("market_data", {}).get("circulating_supply", "N/A")
            total_volume = data.get("market_data", {}).get("total_volume", {}).get("usd", "N/A")
            
            # Format the response
            result = f"📊 {name} ({symbol})\n"
            result += f"💰 Price: {_format_price(current_price)}\n"
            result += f"📈 24h Change: {price_change_24h:+.2f}%\n" if price_change_24h != "N/A" else f"📈 24h Change: {price_change_24h}\n"
            result += f"💎 Market Cap: ${market_cap:,.0f}\n" if market_cap != "N/A" else f"💎 Market Cap: {market_cap}\n"
            result += f"🏆 Market Cap Rank: #{market_cap_rank}\n" if market_cap_rank != "N/A" else f"🏆 Market Cap Rank: {market_cap_rank}\n"
            result += f"🔄 24h Volume: ${total_volume:,.0f}\n" if total_volume != "N/A" else f"🔄 24h Volume: {total_volume}\n"
            result += f"🪙 Circulating Supply: {circulating_supply:,.0f} {symbol}\n" if circulating_supply != "N/A" else f"🪙 Circulating Supply: {circulating_supply}\n"
            
            return result
        else:
            return f"Crypto API error (status {response.status_code}). Please try again later."
    except requests.exceptions.Timeout:
        return "Crypto price request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Failed to fetch crypto price: {str(e)}"


# --- Image Generation Tool ---
@tool
def generate_image(prompt: str) -> str:
    """Generate an image from a text description using AI.
    Use this when the user asks to create, draw, generate, or make an image/picture/photo."""
    import urllib.parse
    try:
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true&enhance=false"
        response = requests.get(url, timeout=120)
        if response.status_code != 200:
            return f"IMAGE_ERROR: Service returned status {response.status_code}"

        # Resize to 256×256 and compress as JPEG quality=25
        # keeps base64 under ~5 KB (~1,200 tokens) so it never blows Groq's token limit
        img = Image.open(io.BytesIO(response.content)).convert("RGB")
        img = img.resize((256, 256), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=25, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"IMAGE_BASE64:{b64}"
    except Exception as e:
        return f"IMAGE_ERROR: {str(e)}"


tools = [arxiv_tool, wiki_tool, get_weather, tavily_tool, get_crypto_price, generate_image]
