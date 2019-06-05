from __future__ import print_function
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import datetime
import time
import json
from influxdb import InfluxDBClient

### MACROS ###

# HTTP server port.
MFXS_HTTP_PORT = 8080

# Sigfox frame lengths.
SIGFOX_INTERMITTENT_WEATHER_DATA_FRAME_LENGTH_BYTES = 6
SIGFOX_CONITNUOUS_WEATHER_DATA_FRAME_LENGTH_BYTES = 10
SIGFOX_MONITORING_FRAME_LENGTH_BYTES = 9
SIGFOX_GEOLOCATION_FRAME_LENGTH_BYTES = 11

# Backend JSON headers.
SIGFOX_BACKEND_JSON_HEADER_TIME = "time"
SIGFOX_BACKEND_JSON_HEADER_DEVICE_ID = "device"
SIGFOX_BACKEND_JSON_HEADER_DATA = "data"

# Influx DB parameters.
INFLUXDB_DATABASE_NAME = 'mfxdb'
INFLUXDB_HTTP_PORT = 8086

# Influx DB measurements names.
INFLUXDB_TEMPERATURE = "temperature"
INFLUXDB_HUMIDITY = "humidity"
INFLUXDB_LIGHT = "light"
INFLUXDB_UV_INDEX = "uv_index"
INFLUXDB_PRESSURE = "pressure"
INFLUXDB_AVERAGE_WIND_SPEED = "average_wind_speed"
INFLUXDB_PEAK_WIND_SPEED = "peak_wind_speed"
INFLUXDB_AVERAGE_WIND_DIRECTION = "average_wind_direction"
INFLUXDB_RAIN = "rain"
INFLUXDB_MCU_TEMPERATURE = "mcu_temperature"
INFLUXDB_PCB_TEMPERATURE = "pcb_temperature"
INFLUXDB_PCB_HUMIDITY = "pcb_humidity"
INFLUXDB_SOLAR_CELL_VOLTAGE = "solar_cell_voltage"
INFLUXDB_SUPERCAP_VOLTAGE = "supercap_voltage"
INFLUXDB_MCU_VOLTAGE = "mcu_voltage"
INFLUXDB_STATUS_BYTE = "status_byte"
INFLUXDB_LOCATION = "location"
INFLUXDB_ALTITUDE = "altitude"
INFLUXDB_GPS_FIX_DURATION = "gps_fix_duration"

### FUNCTIONS DEFINITIONS ###

# Function to get current timestamp in pretty format.
def MFXS_GetCurrentTimestamp():
    return datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S') + " *** "

# Function for parsing Sigfox payload and fill database.
def MFXS_FillDataBase(timestamp, device_id, data):
    
    # Format parameters.
    influxdb_device_id = device_id.upper()
    influxdb_timestamp = int(timestamp)
    
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
            "measurement": INFLUXDB_MCU_TEMPERATURE,
            "time": influxdb_timestamp,
            "fields": {
                influxdb_device_id : mcu_temperature
            }
        },
        {
            "measurement": INFLUXDB_PCB_TEMPERATURE,
            "time": influxdb_timestamp,
            "fields": {
                influxdb_device_id : pcb_temperature
            }
        },
        {
            "measurement": INFLUXDB_PCB_HUMIDITY,
            "time": influxdb_timestamp,
            "fields": {
                influxdb_device_id : pcb_humidity
            }
        },
        {
            "measurement": INFLUXDB_SOLAR_CELL_VOLTAGE,
            "time": influxdb_timestamp,
            "fields": {
                influxdb_device_id : solar_cell_voltage
            }
        },
        {
            "measurement": INFLUXDB_SUPERCAP_VOLTAGE,
            "time": influxdb_timestamp,
            "fields": {
                influxdb_device_id : supercap_voltage
            }
        },
        {
            "measurement": INFLUXDB_MCU_VOLTAGE,
            "time": influxdb_timestamp,
            "fields": {
                influxdb_device_id : mcu_voltage
            }
        },
        {
            "measurement": INFLUXDB_STATUS_BYTE,
            "time": influxdb_timestamp,
            "fields": {
                influxdb_device_id : status_byte
            }
        }]
        print(json_body)
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
        print("Monitoring data stored in database.")
    
    # Weather data frame.
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
            "measurement": INFLUXDB_TEMPERATURE,
            "time": influxdb_timestamp,
            "fields": {
                influxdb_device_id : temperature
            }
        },
        {
            "measurement": INFLUXDB_HUMIDITY,
            "time": influxdb_timestamp,
            "fields": {
                influxdb_device_id : humidity
            }
        },
        {
            "measurement": INFLUXDB_LIGHT,
            "time": influxdb_timestamp,
            "fields": {
                influxdb_device_id : light
            }
        },
        {
            "measurement": INFLUXDB_UV_INDEX,
            "time": influxdb_timestamp,
            "fields": {
                influxdb_device_id : uv_index
            }
        },
        {
            "measurement": INFLUXDB_PRESSURE,
            "time": influxdb_timestamp,
            "fields": {
                influxdb_device_id : pressure
            }
        }]
        print(json_body)
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
        print("Weather data stored in database.")
        
        # Weather data frame.
        if len(data) == (2 * SIGFOX_GEOLOCATION_FRAME_LENGTH_BYTES):
            # Parse fields.
            latitude_degrees = int(data[0:2], 16)
            latitude_minutes = (int(data[2:4], 16) >> 2) & 0x3F
            latitude_seconds = ((((int(data[2:8], 16) & 0x03FFFE) >> 1) & 0x01FFF) / (100000)) * 60
            latitude_north = int(data[6:8], 16) & 0x01
            latitude = latitude_degrees + (latitude_minutes / 60) + (latitude_seconds / 3600)
            if (latitude_north == 0):
                latitude = -latitude
            longitude_degrees = int(data[8:10], 16)
            longitude_minutes = (int(data[10:12], 16) >> 2) & 0x3F
            longitude_seconds = ((((int(data[10:16], 16) & 0x03FFFE) >> 1) & 0x01FFF) / (100000)) * 60
            longitude_east = int(data[14:16], 16) & 0x01
            longitude = longitude_degrees + (longitude_minutes / 60) + (longitude_seconds / 3600)
            if (longitude_east == 0):
                longitude = -longitude
            altitude = int(data[16:20], 16)
            gps_fix_duration = int(data[20:22], 16)
            # Print data.
            print(latitude)
            print(longitude)
            print(altitude)
            print(gps_fix_duration)
            # Create JSON object.
            json_body = [
            {
                "measurement": INFLUXDB_LOCATION,
                "time": influxdb_timestamp,
                "fields": {
                    influxdb_device_id : latitude,
                    influxdb_device_id : longitude
                }
            },
            {
                "measurement": INFLUXDB_ALTITUDE,
                "time": influxdb_timestamp,
                "fields": {
                    influxdb_device_id : altitude
                }
            },
            {
                "measurement": INFLUXDB_GPS_FIX_DURATION,
                "time": influxdb_timestamp,
                "fields": {
                    influxdb_device_id : gps_fix_duration
                }
            }]
            print(json_body)
            # Fill data base.
            influxdb_client.write_points(json_body, time_precision='s')
            print("Geolocation data stored in database.")

### CLASS DECLARATIONS ###

class ServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        print(MFXS_GetCurrentTimestamp() + "GET request received")
        self.send_response(200)
        
    def do_HEAD(self):
        print(MFXS_GetCurrentTimestamp() + "HEAD request received")
        self.send_response(200)
        
    def do_POST(self):
        # Get JSON content.
        post_length = int(self.headers.getheader('content-length', 0))
        post_json = json.loads(self.rfile.read(post_length))
        print(MFXS_GetCurrentTimestamp() + "POST request received: " + str(post_json))
        # Parse data.
        callback_timestamp = post_json[SIGFOX_BACKEND_JSON_HEADER_TIME]
        #timestamp = timestamp + "000000000" # Convert Unix timestamp to nanoseconds for InfluxDB.
        callback_device_id = post_json[SIGFOX_BACKEND_JSON_HEADER_DEVICE_ID]
        callback_data = post_json[SIGFOX_BACKEND_JSON_HEADER_DATA]
        print("Uplink message: timestamp=" + callback_timestamp + " device_id=" + callback_device_id + " data=" + callback_data)
        # Fill database.
        MFXS_FillDataBase(int(callback_timestamp), callback_device_id, callback_data)
        # Send HTTP response.
        self.send_response(200)

### MAIN PROGRAM ###

print("\n*******************************************************")
print("--------------- MeteoFox Server (MFXS) ----------------")
print("*******************************************************\n")

# Create Influx DB client.
influxdb_client = InfluxDBClient(host='localhost', port=INFLUXDB_HTTP_PORT)

# Get list of existing databases.
influxdb_database_list = influxdb_client.get_list_database()
influxdb_mfxdb_found = False
for influxdb_database in influxdb_database_list:
    if (influxdb_database['name'].find(INFLUXDB_DATABASE_NAME) >= 0):
        print(MFXS_GetCurrentTimestamp() + "MeteoFox database found")
        influxdb_mfxdb_found = True

# Create MeteoFox database if it does not exist.   
if (influxdb_mfxdb_found == False):
    print(MFXS_GetCurrentTimestamp() + "Creating database " + INFLUXDB_DATABASE_NAME)
    influxdb_client.create_database(INFLUXDB_DATABASE_NAME)

# Swtich to MeteoFox database.
print(MFXS_GetCurrentTimestamp() + "Switching to database " + INFLUXDB_DATABASE_NAME)
influxdb_client.switch_database(INFLUXDB_DATABASE_NAME)
        
# Start server.
SocketServer.TCPServer.allow_reuse_address = True
mfxs_handler = ServerHandler
mfxs = SocketServer.TCPServer(("", MFXS_HTTP_PORT), mfxs_handler)
print (MFXS_GetCurrentTimestamp() + "Starting server at port", MFXS_HTTP_PORT)
mfxs.serve_forever()
