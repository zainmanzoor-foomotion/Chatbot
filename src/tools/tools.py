import os
import requests
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
@tool
def get_crypto_price(crypto_id: str) -> str:
    """Get the current price and market data for a cryptocurrency. 
    Use common crypto IDs like 'bitcoin', 'ethereum', 'cardano', 'solana', 'dogecoin', etc.
    Returns price in USD, 24h change, market cap, and other key metrics."""
    
    # CoinGecko API is free for basic usage
    url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"
    
    try:
        response = requests.get(url, timeout=10)
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
            result += f"💰 Price: ${current_price:,.2f}\n" if current_price != "N/A" else f"💰 Price: {current_price}\n"
            result += f"📈 24h Change: {price_change_24h:+.2f}%\n" if price_change_24h != "N/A" else f"📈 24h Change: {price_change_24h}\n"
            result += f"💎 Market Cap: ${market_cap:,.0f}\n" if market_cap != "N/A" else f"💎 Market Cap: {market_cap}\n"
            result += f"🏆 Market Cap Rank: #{market_cap_rank}\n" if market_cap_rank != "N/A" else f"🏆 Market Cap Rank: {market_cap_rank}\n"
            result += f"🔄 24h Volume: ${total_volume:,.0f}\n" if total_volume != "N/A" else f"🔄 24h Volume: {total_volume}\n"
            result += f"🪙 Circulating Supply: {circulating_supply:,.0f} {symbol}\n" if circulating_supply != "N/A" else f"🪙 Circulating Supply: {circulating_supply}\n"
            
            return result
        elif response.status_code == 404:
            return f"Cryptocurrency '{crypto_id}' not found. Try common IDs like 'bitcoin', 'ethereum', 'cardano', 'solana', 'dogecoin', etc."
        else:
            return f"Crypto API error (status {response.status_code}). Please try again later."
    except requests.exceptions.Timeout:
        return "Crypto price request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Failed to fetch crypto price: {str(e)}"


tools = [arxiv_tool, wiki_tool, get_weather, tavily_tool, get_crypto_price]
