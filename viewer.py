from fastapi import FastAPI
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
COOLANT_INTERVAL = int(os.environ.get('COOLANT_INTERVAL', 30))

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
    }
}

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
                f"http://{HA_HOST}:8123/api/states/sensor.sensor_coolant_temperature",
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
        asyncio.create_task(poll_coolant())
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
async def hello():
    """Health check endpoint"""
    logging.info("Hello World!")
    return "Hello World!"


@app.get("/radiation")
async def get_radiation():
    """Get radiation sensor data from cache"""
    logging.info("Get radiation data")
    return cache["radiation"]["data"] or {"error": "no data"}


@app.get("/water")
async def get_water():
    """Get water pressure sensor data from cache"""
    logging.info("Get water data")
    return cache["water"]["data"] or {"error": "no data"}


@app.get("/electricity")
async def get_electricity():
    """Get electricity/power sensor data from cache"""
    logging.info("Get electricity data")
    return cache["electricity"]["data"] or {"error": "no data"}


@app.get("/coolant")
async def get_coolant():
    """Get coolant temperature sensor data from cache"""
    logging.info("Get coolant data")
    return cache["coolant"]["data"] or {"error": "no data"}


@app.get("/debug/cache")
async def debug_cache():
    """Debug endpoint to view entire cache structure including metadata"""
    return cache


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
