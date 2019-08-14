from __future__ import print_function
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import datetime
import time
import json
from influxdb import InfluxDBClient

### MACROS ###

# HTTP server port.
MFXS_HTTP_PORT = 65000

# Sigfox frame lengths.
SIGFOX_OOB_DATA = "OOB"
SIGFOX_MONITORING_FRAME_LENGTH_BYTES = 9
SIGFOX_INTERMITTENT_WEATHER_DATA_FRAME_LENGTH_BYTES = 6
SIGFOX_CONTINUOUS_WEATHER_DATA_FRAME_LENGTH_BYTES = 10
SIGFOX_GEOLOCATION_FRAME_LENGTH_BYTES = 11

# Backend JSON headers.
SIGFOX_BACKEND_JSON_HEADER_TIME = "time"
SIGFOX_BACKEND_JSON_HEADER_DEVICE_ID = "device"
SIGFOX_BACKEND_JSON_HEADER_DATA = "data"

# Influx DB parameters.
INFLUXDB_DATABASE_NAME = 'mfxdb'
INFLUXDB_DATABASE_HTTP_PORT = 8086

# Influx DB global measurements names.
INFLUXDB_MEASUREMENT_GLOBAL = "global"
INFLUXDB_FIELD_LAST_STARTUP_TIMESTAMP = "last_startup_timestamp"
INFLUXDB_FIELD_LAST_COMMUNICATION_TIMESTAMP = "last_communication_timestamp"

# Influx DB weather measurements names.
INFLUXDB_MEASUREMENT_WEATHER = "weather"
INFLUXDB_FIELD_LAST_WEATHER_DATA_TIMESTAMP = "last_weather_data_timestamp"
INFLUXDB_FIELD_TEMPERATURE = "temperature"
INFLUXDB_FIELD_HUMIDITY = "humidity"
INFLUXDB_FIELD_LIGHT = "light"
INFLUXDB_FIELD_UV_INDEX = "uv_index"
INFLUXDB_FIELD_PRESSURE = "pressure"
INFLUXDB_FIELD_AVERAGE_WIND_SPEED = "average_wind_speed"
INFLUXDB_FIELD_PEAK_WIND_SPEED = "peak_wind_speed"
INFLUXDB_FIELD_AVERAGE_WIND_DIRECTION = "average_wind_direction"
INFLUXDB_FIELD_RAIN = "rain"

# Influx DB monitoring measurements names.
INFLUXDB_MEASUREMENT_MONITORING = "monitoring"
INFLUXDB_FIELD_LAST_MONITORING_DATA_TIMESTAMP = "last_monitoring_data_timestamp"
INFLUXDB_FIELD_MCU_TEMPERATURE = "mcu_temperature"
INFLUXDB_FIELD_PCB_TEMPERATURE = "pcb_temperature"
INFLUXDB_FIELD_PCB_HUMIDITY = "pcb_humidity"
INFLUXDB_FIELD_SOLAR_CELL_VOLTAGE = "solar_cell_voltage"
INFLUXDB_FIELD_SUPERCAP_VOLTAGE = "supercap_voltage"
INFLUXDB_FIELD_MCU_VOLTAGE = "mcu_voltage"
INFLUXDB_FIELD_STATUS_BYTE = "status_byte"

# Influx DB geoloc measurements names.
INFLUXDB_MEASUREMENT_GEOLOC = "geoloc"
INFLUXDB_FIELD_LAST_GEOLOC_DATA_TIMESTAMP = "last_geoloc_data_timestamp"
INFLUXDB_FIELD_LATITUDE = "latitude"
INFLUXDB_FIELD_LONGITUDE = "longitude"
INFLUXDB_FIELD_ALTITUDE = "altitude"
INFLUXDB_FIELD_GPS_FIX_DURATION = "gps_fix_duration"

# Influx DB tags.
INFLUXDB_TAG_SIGFOX_DEVICE_ID = "sigfox_device_id"
INFLUXDB_TAG_METEOFOX_SITE = "meteofox_site"

### FUNCTIONS DEFINITIONS ###

# Function to get current timestamp in pretty format.
def MFXS_GetCurrentTimestamp():
    return datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S') + " *** "

# Function performing Sigfox ID to MeteoFox site conversion.
def MFXS_GetSite(device_id):
    # Default is unknown.
    meteofox_site = "Unknown site"
    if device_id == "53B5":
        meteofox_site = "Proto HW1.0"
    elif device_id == "5436":
        meteofox_site = "Proto HW2.0"
    elif device_id == "546C":
        meteofox_site = "Le Vigan (Lot)"
    elif device_id == "5477":
        meteofox_site = "Prat d'Albis (Ariege)"
    return meteofox_site

# Function for parsing Sigfox payload and fill database.
def MFXS_FillDataBase(timestamp, device_id, data):
    # Format parameters.
    influxdb_device_id = device_id.upper()
    influxdb_timestamp = int(timestamp)
    # OOB frame.
    if data == SIGFOX_OOB_DATA:
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_LAST_STARTUP_TIMESTAMP : influxdb_timestamp,
                INFLUXDB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_METEOFOX_SITE : MFXS_GetSite(influxdb_device_id)
            }
        }]
        print(MFXS_GetCurrentTimestamp() + "ID=" + str(device_id) + " * OOB frame (start up).")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Monitoring frame.
    if len(data) == (2 * SIGFOX_MONITORING_FRAME_LENGTH_BYTES):
        # Parse fields.
        mcu_temperature = int(data[0:2], 16)
        pcb_temperature = int(data[2:4], 16)
        pcb_humidity = int(data[4:6], 16)
        solar_cell_voltage = int(data[6:10], 16)
        supercap_voltage = int(data[10:13], 16)
        mcu_voltage = int(data[13:16], 16)
        status_byte = int(data[16:18], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_MONITORING,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_MCU_TEMPERATURE : mcu_temperature,
                INFLUXDB_FIELD_PCB_TEMPERATURE : pcb_temperature,
                INFLUXDB_FIELD_PCB_HUMIDITY : pcb_humidity,
                INFLUXDB_FIELD_SOLAR_CELL_VOLTAGE : solar_cell_voltage,
                INFLUXDB_FIELD_SUPERCAP_VOLTAGE : supercap_voltage,
                INFLUXDB_FIELD_MCU_VOLTAGE : mcu_voltage,
                INFLUXDB_FIELD_STATUS_BYTE : status_byte,
                INFLUXDB_FIELD_LAST_MONITORING_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_METEOFOX_SITE : MFXS_GetSite(influxdb_device_id)
            }
        },
        {
            "measurement": INFLUXDB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_METEOFOX_SITE : MFXS_GetSite(influxdb_device_id)
            }
        }]
        print(MFXS_GetCurrentTimestamp() + "ID=" + str(device_id) + " * Monitoring data * McuTemp=" + str(mcu_temperature) + "C, PcbTemp=" + str(pcb_temperature) + "C, PcbHum=" + str(pcb_humidity) + "%, SolarVolt=" + str(solar_cell_voltage) + ", SupercapVolt=" + str(supercap_voltage) + "mV, McuVolt=" + str(mcu_voltage) + "mV, Status=" + str(status_byte) + ".")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Intermittent eather data frame.
    if len(data) == (2 * SIGFOX_INTERMITTENT_WEATHER_DATA_FRAME_LENGTH_BYTES):
        # Parse fields.
        temperature = int(data[0:2], 16)
        humidity = int(data[2:4], 16)
        light = int(data[4:6], 16)
        uv_index = int(data[6:8], 16)
        pressure = int(data[8:12], 16) / 10.0
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_WEATHER,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_TEMPERATURE : temperature,
                INFLUXDB_FIELD_HUMIDITY : humidity,
                INFLUXDB_FIELD_LIGHT : light,
                INFLUXDB_FIELD_UV_INDEX : uv_index,
                INFLUXDB_FIELD_PRESSURE : pressure,
                INFLUXDB_FIELD_LAST_WEATHER_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_METEOFOX_SITE : MFXS_GetSite(influxdb_device_id)
            }
        },
        {
            "measurement": INFLUXDB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_METEOFOX_SITE : MFXS_GetSite(influxdb_device_id)
            }
        }]
        print(MFXS_GetCurrentTimestamp() + "ID=" + str(device_id) + " * Weather data * Temp=" + str(temperature) + "C, Hum=" + str(humidity) + "%, Light=" + str(light) + "%, UV=" + str(uv_index) + ", Pres=" + str(pressure) + "hPa.")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Continuous eather data frame.
    if len(data) == (2 * SIGFOX_CONTINUOUS_WEATHER_DATA_FRAME_LENGTH_BYTES):
        # Parse fields.
        temperature = int(data[0:2], 16)
        humidity = int(data[2:4], 16)
        light = int(data[4:6], 16)
        uv_index = int(data[6:8], 16)
        pressure = int(data[8:12], 16) / 10.0
        average_wind_speed = int(data[12:14], 16)
        peak_wind_speed = int(data[14:16], 16)
        average_wind_direction = int(data[16:18], 16)
        rain = int(data[18:20], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_WEATHER,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_TEMPERATURE : temperature,
                INFLUXDB_FIELD_HUMIDITY : humidity,
                INFLUXDB_FIELD_LIGHT : light,
                INFLUXDB_FIELD_UV_INDEX : uv_index,
                INFLUXDB_FIELD_PRESSURE : pressure,
                INFLUXDB_FIELD_AVERAGE_WIND_SPEED : average_wind_speed,
                INFLUXDB_FIELD_PEAK_WIND_SPEED : peak_wind_speed,
                INFLUXDB_FIELD_AVERAGE_WIND_DIRECTION : average_wind_direction,
                INFLUXDB_FIELD_RAIN : rain,
                INFLUXDB_FIELD_LAST_WEATHER_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_METEOFOX_SITE : MFXS_GetSite(influxdb_device_id)
            }
        },
        {
            "measurement": INFLUXDB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_METEOFOX_SITE : MFXS_GetSite(influxdb_device_id)
            }
        }]
        print(MFXS_GetCurrentTimestamp() + "ID=" + str(device_id) + " * Weather data * Temp=" + str(temperature) + "C, Hum=" + str(humidity) + "%, Light=" + str(light) + "%, UV=" + str(uv_index) + ", Pres=" + str(pressure) + "hPa, AvWindSp=" + str(average_wind_speed) + "km/h, PeakWindSp=" + str(peak_wind_speed) + "km/h, AvWindDir=" + str(average_wind_direction) + "d, Rain=" + str(rain) + "mm.")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Geolocation frame.
    if len(data) == (2 * SIGFOX_GEOLOCATION_FRAME_LENGTH_BYTES):
        # Parse fields.
        latitude_degrees = int(data[0:2], 16)
        latitude_minutes = (int(data[2:4], 16) >> 2) & 0x3F
        latitude_seconds = ((((int(data[2:8], 16) & 0x03FFFE) >> 1) & 0x01FFF) / (100000.0)) * 60.0
        latitude_north = int(data[6:8], 16) & 0x01
        latitude = latitude_degrees + (latitude_minutes / 60.0) + (latitude_seconds / 3600.0)
        if (latitude_north == 0):
            latitude = -latitude
        longitude_degrees = int(data[8:10], 16)
        longitude_minutes = (int(data[10:12], 16) >> 2) & 0x3F
        longitude_seconds = ((((int(data[10:16], 16) & 0x03FFFE) >> 1) & 0x01FFF) / (100000.0)) * 60.0
        longitude_east = int(data[14:16], 16) & 0x01
        longitude = longitude_degrees + (longitude_minutes / 60.0) + (longitude_seconds / 3600.0)
        if (longitude_east == 0):
            longitude = -longitude
        altitude = int(data[16:20], 16)
        gps_fix_duration = int(data[20:22], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_GEOLOC,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_LATITUDE : latitude,
                INFLUXDB_FIELD_LONGITUDE : longitude,
                INFLUXDB_FIELD_ALTITUDE : altitude,
                INFLUXDB_FIELD_GPS_FIX_DURATION : gps_fix_duration,
                INFLUXDB_FIELD_LAST_GEOLOC_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_METEOFOX_SITE : MFXS_GetSite(influxdb_device_id)
            }
        },
        {
            "measurement": INFLUXDB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_METEOFOX_SITE : MFXS_GetSite(influxdb_device_id)
            }
        }]
        print(MFXS_GetCurrentTimestamp() + "ID=" + str(device_id) + " * Geoloc data * Lat=" + str(latitude) + ", Long=" + str(longitude) + ", Alt=" + str(altitude) + "m, GpsFixDur=" + str(gps_fix_duration) + "s.")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')

### CLASS DECLARATIONS ###

class ServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("")
        print(MFXS_GetCurrentTimestamp() + "GET request received.")
        self.send_response(200)     
    def do_HEAD(self):
        print("")
        print(MFXS_GetCurrentTimestamp() + "HEAD request received.")
        self.send_response(200)   
    def do_POST(self):
        # Get JSON content.
        post_length = int(self.headers.getheader('content-length', 0))
        post_json = json.loads(self.rfile.read(post_length))
        print("")
        print(MFXS_GetCurrentTimestamp() + "POST request received.")
        # Parse data.
        callback_timestamp = post_json[SIGFOX_BACKEND_JSON_HEADER_TIME]
        callback_device_id = post_json[SIGFOX_BACKEND_JSON_HEADER_DEVICE_ID]
        callback_data = post_json[SIGFOX_BACKEND_JSON_HEADER_DATA]
        print(MFXS_GetCurrentTimestamp() + "SIGFOX backend callback * Timestamp=" + callback_timestamp + " ID=" + callback_device_id + " Data=" + callback_data)
        # Fill database.
        MFXS_FillDataBase(int(callback_timestamp), callback_device_id, callback_data)
        # Send HTTP response.
        self.send_response(200)

### MAIN PROGRAM ###

print("\n*******************************************************")
print("--------------- MeteoFox Server (MFXS) ----------------")
print("*******************************************************\n")

# Create Influx DB client.
influxdb_client = InfluxDBClient(host='localhost', port=INFLUXDB_DATABASE_HTTP_PORT)

# Get list of existing databases.
influxdb_database_list = influxdb_client.get_list_database()
influxdb_mfxdb_found = False
for influxdb_database in influxdb_database_list:
    if (influxdb_database['name'].find(INFLUXDB_DATABASE_NAME) >= 0):
        print(MFXS_GetCurrentTimestamp() + "MeteoFox database found.")
        influxdb_mfxdb_found = True

# Create MeteoFox database if it does not exist.   
if (influxdb_mfxdb_found == False):
    print(MFXS_GetCurrentTimestamp() + "Creating database " + INFLUXDB_DATABASE_NAME + ".")
    influxdb_client.create_database(INFLUXDB_DATABASE_NAME)

# Switch to MeteoFox database.
print(MFXS_GetCurrentTimestamp() + "Switching to database " + INFLUXDB_DATABASE_NAME + ".")
influxdb_client.switch_database(INFLUXDB_DATABASE_NAME)
        
# Start server.
SocketServer.TCPServer.allow_reuse_address = True
mfxs_handler = ServerHandler
mfxs = SocketServer.TCPServer(("", MFXS_HTTP_PORT), mfxs_handler)
print (MFXS_GetCurrentTimestamp() + "Starting server at port " + str(MFXS_HTTP_PORT) + ".")
mfxs.serve_forever()