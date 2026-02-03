from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import httpx
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# Load configuration from .env file
load_dotenv('config.env')

# Home Assistant configuration
HA_TOKEN = os.environ.get('HA_TOKEN', 'token')
HA_HOST = os.environ.get('HA_HOST', 'ha.host')
PORT = int(os.environ.get('PORT', 8080))

# Polling intervals (in seconds)
RADIATION_INTERVAL = int(os.environ.get('RADIATION_INTERVAL', 30))
WATER_INTERVAL = int(os.environ.get('WATER_INTERVAL', 30))
ELECTRICITY_INTERVAL = int(os.environ.get('ELECTRICITY_INTERVAL', 30))
COOLANT_INTERVAL = int(os.environ.get('COOLANT_INTERVAL', 60))
WEATHER_INTERVAL = int(os.environ.get('WEATHER_INTERVAL', 600))

# In-memory cache
cache = {
    "radiation": {
        "data": None,
        "last_updated": None,
        "error": None
    },
    "water": {
        "data": None,
        "last_updated": None,
        "error": None
    },
    "electricity": {
        "data": None,
        "last_updated": None,
        "error": None
    },
    "coolant": {
        "data": None,
        "last_updated": None,
        "error": None
    },
    "weather": {
        "data": None,
        "last_updated": None,
        "error": None
    }
}

def get_real_ip(request: Request) -> str:
    """Extract real client IP from Cloudflare headers or fallback to direct IP"""
    # Спочатку перевіряємо CF-Connecting-IP (найнадійніший для Cloudflare)
    cf_ip = request.headers.get('CF-Connecting-IP')
    if cf_ip:
        return cf_ip

    # Потім X-Forwarded-For (беремо перший IP з ланцюжка)
    x_forwarded = request.headers.get('X-Forwarded-For')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()

    # Або X-Real-IP
    x_real = request.headers.get('X-Real-IP')
    if x_real:
        return x_real

    # Fallback на direct connection IP
    return request.client.host if request.client else "unknown"

# HTTP client for async requests
http_client = None


async def poll_radiation():
    """Background task to poll radiation sensor data from Home Assistant"""
    while True:
        try:
            response = await http_client.get(
                f"http://{HA_HOST}:8123/api/states/sensor.geiger_counter_radiation_dose_per_hour",
                headers={"Authorization": f"Bearer {HA_TOKEN}"}
            )
            response.raise_for_status()
            cache["radiation"]["data"] = response.json()
            cache["radiation"]["last_updated"] = datetime.now().isoformat()
            cache["radiation"]["error"] = None
            logging.info("Updated radiation data")
        except Exception as e:
            cache["radiation"]["error"] = str(e)
            logging.error(f"Error polling radiation: {e}")
        await asyncio.sleep(RADIATION_INTERVAL)


async def poll_water():
    """Background task to poll water pressure sensor data from Home Assistant"""
    while True:
        try:
            response = await http_client.get(
                f"http://{HA_HOST}:8123/api/states/binary_sensor.water_pressure_sensor_contact",
                headers={"Authorization": f"Bearer {HA_TOKEN}"}
            )
            response.raise_for_status()
            cache["water"]["data"] = response.json()
            cache["water"]["last_updated"] = datetime.now().isoformat()
            cache["water"]["error"] = None
            logging.info("Updated water data")
        except Exception as e:
            cache["water"]["error"] = str(e)
            logging.error(f"Error polling water: {e}")
        await asyncio.sleep(WATER_INTERVAL)


async def poll_electricity():
    """Background task to poll electricity/power sensor data from Home Assistant"""
    while True:
        try:
            response = await http_client.get(
                f"http://{HA_HOST}:8123/api/states/binary_sensor.grid_lost",
                headers={"Authorization": f"Bearer {HA_TOKEN}"}
            )
            response.raise_for_status()
            cache["electricity"]["data"] = response.json()
            cache["electricity"]["last_updated"] = datetime.now().isoformat()
            cache["electricity"]["error"] = None
            logging.info("Updated electricity data")
        except Exception as e:
            cache["electricity"]["error"] = str(e)
            logging.error(f"Error polling electricity: {e}")
        await asyncio.sleep(ELECTRICITY_INTERVAL)


async def poll_coolant():
    """Background task to poll coolant temperature sensor data from Home Assistant"""
    while True:
        try:
            response = await http_client.get(
                f"http://{HA_HOST}:8123/api/states/sensor.sensor_coolant_2_temperature",
                headers={"Authorization": f"Bearer {HA_TOKEN}"}
            )
            response.raise_for_status()
            cache["coolant"]["data"] = response.json()
            cache["coolant"]["last_updated"] = datetime.now().isoformat()
            cache["coolant"]["error"] = None
            logging.info("Updated coolant data")
        except Exception as e:
            cache["coolant"]["error"] = str(e)
            logging.error(f"Error polling coolant: {e}")
        await asyncio.sleep(COOLANT_INTERVAL)

async def poll_weather():
    """Background task to poll weather data from Home Assistant"""
    while True:
        try:
            response = await http_client.get(
                f"http://{HA_HOST}:8123/api/states/sensor.sensor_outdoor_temperature",
                headers={"Authorization": f"Bearer {HA_TOKEN}"}
            )
            response.raise_for_status()
            cache["weather"]["data"] = response.json()
            cache["weather"]["last_updated"] = datetime.now().isoformat()
            cache["weather"]["error"] = None
            logging.info("Updated weather data")
        except Exception as e:
            cache["weather"]["error"] = str(e)
            logging.error(f"Error polling weather: {e}")
        await asyncio.sleep(WEATHER_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown events"""
    global http_client

    # Startup: Initialize HTTP client and start background tasks
    http_client = httpx.AsyncClient(timeout=10.0)
    logging.info("Starting viewer with background polling tasks")

    tasks = [
        asyncio.create_task(poll_radiation()),
        asyncio.create_task(poll_water()),
        asyncio.create_task(poll_electricity()),
        asyncio.create_task(poll_coolant()),
        asyncio.create_task(poll_weather())
    ]

    yield

    # Shutdown: Cancel all background tasks and close HTTP client
    logging.info("Shutting down viewer")
    for task in tasks:
        task.cancel()
    await http_client.aclose()


# Create FastAPI application
app = FastAPI(
    title="Home Assistant Viewer",
    description="Cached API for Home Assistant sensor data",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/")
async def hello(request: Request):
    """Health check endpoint"""
    client_ip = get_real_ip(request)
    logging.info(f"Hello World! [IP: {client_ip}]")
    return "Hello World!"


@app.get("/radiation")
async def get_radiation(request: Request):
    """Get radiation sensor data from cache"""
    client_ip = get_real_ip(request)
    logging.info(f"Get radiation data [IP: {client_ip}]")
    return cache["radiation"]["data"] or {"error": "no data"}


@app.get("/water")
async def get_water(request: Request):
    """Get water pressure sensor data from cache"""
    client_ip = get_real_ip(request)
    logging.info(f"Get water data [IP: {client_ip}]")
    return cache["water"]["data"] or {"error": "no data"}


@app.get("/electricity")
async def get_electricity(request: Request):
    """Get electricity/power sensor data from cache"""
    client_ip = get_real_ip(request)
    logging.info(f"Get electricity data [IP: {client_ip}]")
    return cache["electricity"]["data"] or {"error": "no data"}


@app.get("/coolant")
async def get_coolant(request: Request):
    """Get coolant temperature sensor data from cache"""
    client_ip = get_real_ip(request)
    logging.info(f"Get coolant data [IP: {client_ip}]")
    return cache["coolant"]["data"] or {"error": "no data"}


@app.get("/weather")
async def get_weather(request: Request):
    """Get weather sensor data from cache"""
    client_ip = get_real_ip(request)
    logging.info(f"Get weather data [IP: {client_ip}]")
    return cache["weather"]["data"] or {"error": "no data"}


@app.get("/debug/cache")
async def debug_cache(request: Request):
    """Debug endpoint to view entire cache structure including metadata"""
    client_ip = get_real_ip(request)
    logging.info(f"Debug cache access [IP: {client_ip}]")
    return cache


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
