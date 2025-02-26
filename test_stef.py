import json
import requests
from datetime import datetime
from dsmr_parser import telegram_specifications
from dsmr_parser.parsers import TelegramParser
from dsmr_parser.clients import SerialReader, SERIAL_SETTINGS_V5
from influxdb_client import InfluxDBClient, Point, WritePrecision

# Configuration
DSMR_DEVICE = '/dev/ttyUSB0'
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "your_token"
INFLUXDB_ORG = "your_org"
INFLUXDB_BUCKET = "your_bucket"
WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/onecall"
WEATHER_API_KEY = "your_api_key"
LAT = "your_latitude"
LON = "your_longitude"
ENERGY_JSON_FILE = "path_to_your_energy_prices.json"
PRICE_THRESHOLD = 0.10  # Example threshold

# Read data from DSMR meter
serial_reader = SerialReader(
    device=DSMR_DEVICE,
    serial_settings=SERIAL_SETTINGS_V5,
    telegram_specification=telegram_specifications.V5
)

# Initialize InfluxDB client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN)
write_api = client.write_api(write_options=SYNCHRONOUS)

# Fetch weather data
weather_response = requests.get(f"{WEATHER_API_URL}?lat={LAT}&lon={LON}&appid={WEATHER_API_KEY}")
weather_data = weather_response.json()

# Load energy prices from JSON file
with open(ENERGY_JSON_FILE, 'r') as file:
    energy_data = json.load(file)

# Process and store data
for telegram in serial_reader.read_as_object():
    power_usage = telegram['1-0:1.8.1']  # Example field, adjust as needed
    point = Point("energy_data").tag("location", "home").field("power_usage", power_usage).time(datetime.utcnow(), WritePrecision.NS)
    write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

# Suggest optimal times for energy usage
def suggest_optimal_times(weather_data, energy_data):
    suggestions = []
    for hour in range(24):
        if energy_data[hour]['price'] < PRICE_THRESHOLD and weather_data['hourly'][hour]['clouds'] < 20:  # Less than 20% cloud cover
            suggestions.append(hour)
    return suggestions

optimal_times = suggest_optimal_times(weather_data, energy_data)
print("Optimal times to use electrical machines:", optimal_times)