from __future__ import print_function
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import math
import datetime
import time
import json
from influxdb import InfluxDBClient
from Tkconstants import CURRENT

### MACROS ###

# Enable or disable debug prints.
SFXS_LOG = False

# HTTP server port.
SFXS_HTTP_PORT = 65000

# Backend JSON headers.
SIGFOX_BACKEND_JSON_HEADER_TIME = "time"
SIGFOX_BACKEND_JSON_HEADER_DEVICE_ID = "device"
SIGFOX_BACKEND_JSON_HEADER_DATA = "data"

# Devices ID and associated informations.
MFX_SIGFOX_DEVICES_ID = ["53B5", "5436", "546C", "5477", "5497", "549D", "54B6", "54E4"]
MFX_SIGFOX_DEVICES_SITE = ["INSA Toulouse", "Proto V2", "Le Vigan", "Prat Albis", "Eaunes", "Labege", "Grust", "Concarneau"]

ATXFX_SIGFOX_DEVICES_ID = ["868E", "869E", "87A5", "87EE", "87F1", "87F6", "87F4", "87F6", "87FC", "8922"]
ATXFX_SIGFOX_DEVICES_RACK = ["1", "1", "1", "1", "1", "2", "2", "2", "2", "2"]
ATXFX_SIGFOX_DEVICES_FRONT_END = ["+3.3V", "+5.0V", "+12.0V", "Adjustable", "Battery charger", "+3.3V", "+5.0V", "+12.0V", "Adjustable", "Battery charger"]

SLFX_SIGFOX_DEVICES_ID = ["44AA", "44D2", "4505", "45A0", "45AB"]
SLFX_SIGFOX_DEVICES_SITE = ["INSA Toulouse", "Le Vigan", "Unknown", "Unknown", "Unknown"]

TKFX_SIGFOX_DEVICES_ID = ["4761", "479C", "47A7", "47EA", "4894"]
TKFX_SIGFOX_DEVICES_ASSET = ["Car", "Bike", "Hiking", "Unknown", "Unknown"]

SYNCFX_SIGFOX_DEVICES_ID = ["4016", "405B", "40A7", "4151", "41CE"]
SYNCFX_SIGFOX_DEVICES_SITE = ["Proto Labo", "Labege", "Prat Albis", "Unknown", "Unknown"]

# Sigfox frame lengths.
MFX_SIGFOX_OOB_DATA = "OOB"
MFX_SIGFOX_MONITORING_FRAME_LENGTH_BYTES = 9
MFX_SIGFOX_INTERMITTENT_WEATHER_DATA_FRAME_LENGTH_BYTES = 6
MFX_SIGFOX_CONTINUOUS_WEATHER_DATA_FRAME_LENGTH_BYTES = 10
MFX_SIGFOX_GEOLOCATION_FRAME_LENGTH_BYTES = 11
MFX_SIGFOX_GEOLOCATION_TIMEOUT_FRAME_LENGTH_BYTES = 1

ATXFX_SIGFOX_START_STOP_FRAME_LENGTH_BYTES = 1
ATXFX_SIGFOX_MONITORING_FRAME_LENGTH_BYTES = 8

SLFX_SIGFOX_MONITORING_DATA_FRAME_LENGTH_BYTES = 10

TKFX_SIGFOX_OOB_DATA = "OOB"
TKFX_SIGFOX_MONITORING_FRAME_LENGTH_BYTES = 8
TKFX_SIGFOX_GEOLOCATION_FRAME_LENGTH_BYTES = 11
TKFX_SIGFOX_GEOLOCATION_TIMEOUT_FRAME_LENGTH_BYTES = 1

SYNCFX_SIGFOX_OOB_DATA = "OOB"
SYNCFX_SIGFOX_SYNCHRO_FRAME_LENGTH_BYTES = 6
SYNCFX_SIGFOX_MONITORING_FRAME_LENGTH_BYTES = 7
SYNCFX_SIGFOX_GEOLOCATION_FRAME_LENGTH_BYTES = 11
SYNCFX_SIGFOX_GEOLOCATION_TIMEOUT_FRAME_LENGTH_BYTES = 1

# Error values.
MFX_TEMPERATURE_ERROR = 0x7F
MFX_HUMIDITY_ERROR = 0xFF
MFX_UV_INDEX_ERROR = 0xFF
MFX_PRESSURE_ERROR = 0xFFFF
MFX_WIND_ERROR = 0xFF

ATXFX_OUTPUT_CURRENT_ERROR = 0xFFFFFF

TKFX_TEMPERATURE_ERROR = 0x7F

# Influx DB parameters.
INFLUXDB_DATABASE_HTTP_PORT = 8086
INFLUXDB_MFX_DATABASE_NAME = 'mfxdb'
INFLUXDB_ATXFX_DATABASE_NAME = 'atxfxdb'
INFLUXDB_SLFX_DATABASE_NAME = 'slfxdb'
INFLUXDB_SYNCFX_DATABASE_NAME = 'syncfxdb'
INFLUXDB_TKFX_DATABASE_NAME = 'tkfxdb'
INFLUXDB_NULL_DATABASE_NAME = 'nulldb'

# Influx DB measurements name.
INFLUXDB_MEASUREMENT_GLOBAL = "global"
INFLUXDB_MEASUREMENT_MONITORING = "monitoring"
INFLUXDB_MEASUREMENT_WEATHER = "weather"
INFLUXDB_MEASUREMENT_GEOLOC = "geoloc"
INFLUXDB_MEASUREMENT_SYNCHRO = "synchro"

# Influx DB fields name.
# Timestamps.
INFLUXDB_FIELD_LAST_STARTUP_TIMESTAMP = "last_startup_timestamp"
INFLUXDB_FIELD_LAST_SHUTDOWN_TIMESTAMP = "last_shutdown_timestamp"
INFLUXDB_FIELD_LAST_COMMUNICATION_TIMESTAMP = "last_communication_timestamp"
INFLUXDB_FIELD_LAST_WEATHER_DATA_TIMESTAMP = "last_weather_data_timestamp"
INFLUXDB_FIELD_LAST_MONITORING_DATA_TIMESTAMP = "last_monitoring_data_timestamp"
INFLUXDB_FIELD_LAST_GEOLOC_DATA_TIMESTAMP = "last_geoloc_data_timestamp"
INFLUXDB_FIELD_LAST_SYNCHRO_DATA_TIMESTAMP = "last_synchro_data_timestamp"
# Time.
INFLUXDB_FIELD_HOURS = "hours"
INFLUXDB_FIELD_MINUTES = "minutes"
INFLUXDB_FIELD_SECONDS = "seconds"
# Frequency.
INFLUXDB_FIELD_FREQUENCY = "frequency"
# Status.
INFLUXDB_FIELD_STATE = "state"
INFLUXDB_FIELD_STATUS_BYTE = "status_byte"
# Temperature.
INFLUXDB_FIELD_TEMPERATURE = "temperature"
INFLUXDB_FIELD_MCU_TEMPERATURE = "mcu_temperature"
INFLUXDB_FIELD_PCB_TEMPERATURE = "pcb_temperature"
# Humidity.
INFLUXDB_FIELD_HUMIDITY = "humidity"
INFLUXDB_FIELD_PCB_HUMIDITY = "pcb_humidity"
# Light.
INFLUXDB_FIELD_LIGHT = "light"
INFLUXDB_FIELD_UV_INDEX = "uv_index"
# Pressure.
INFLUXDB_FIELD_ABSOLUTE_PRESSURE = "absolute_pressure"
INFLUXDB_FIELD_SEA_LEVEL_PRESSURE = "sea_level_pressure"
# Wind.
INFLUXDB_FIELD_AVERAGE_WIND_SPEED = "average_wind_speed"
INFLUXDB_FIELD_PEAK_WIND_SPEED = "peak_wind_speed"
INFLUXDB_FIELD_AVERAGE_WIND_DIRECTION = "average_wind_direction"
# Rain.
INFLUXDB_FIELD_RAIN = "rain"
# Voltage.
INFLUXDB_FIELD_SOURCE_VOLTAGE = "source_voltage"
INFLUXDB_FIELD_SOLAR_CELL_VOLTAGE = "solar_cell_voltage"
INFLUXDB_FIELD_SUPERCAP_VOLTAGE = "supercap_voltage"
INFLUXDB_FIELD_BATTERY_VOLTAGE = "battery_voltage"
INFLUXDB_FIELD_MCU_VOLTAGE = "mcu_voltage"
INFLUXDB_FIELD_OUTPUT_VOLTAGE = "output_voltage"
# Current.
INFLUXDB_FIELD_OUTPUT_CURRENT = "output_current"
INFLUXDB_FIELD_CURRENT_SENSE_RANGE = "current_sense_range"
# Power.
INFLUXDB_FIELD_OUTPUT_POWER = "output_power"
# GPS.
INFLUXDB_FIELD_LATITUDE = "latitude"
INFLUXDB_FIELD_LONGITUDE = "longitude"
INFLUXDB_FIELD_ALTITUDE = "altitude"
INFLUXDB_FIELD_GPS_FIX_DURATION = "gps_fix_duration"
INFLUXDB_FIELD_GPSDO_LOCK_DURATION = "gpsdo_lock_duration"

# Influx DB tags.
INFLUXDB_TAG_SIGFOX_DEVICE_ID = "sigfox_device_id"
INFLUXDB_TAG_METEOFOX_SITE = "meteofox_site"
INFLUXDB_TAG_ATXFOX_RACK = "atxfox_rack"
INFLUXDB_TAG_ATXFOX_FRONT_END = "atxfox_front_end"
INFLUXDB_TAG_SOLARFOX_SITE = "solarfox_site"
INFLUXDB_TAG_SYNCHROFOX_SITE = "synchrofox_site"
INFLUXDB_TAG_TRACKFOX_ASSET = "trackfox_asset"

### FUNCTIONS DEFINITIONS ###

# Function to get current timestamp in pretty format.
def SFXS_GetCurrentTimestamp():
    return datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S') + " *** "

# Function to switch on the correct Influx DB database.
def SFXS_GetDataBase(device_id):
    sfxs_db = INFLUXDB_NULL_DATABASE_NAME
    if (device_id in MFX_SIGFOX_DEVICES_ID):
        sfxs_db = INFLUXDB_MFX_DATABASE_NAME
    elif (device_id in ATXFX_SIGFOX_DEVICES_ID):
        sfxs_db = INFLUXDB_ATXFX_DATABASE_NAME
    elif (device_id in SLFX_SIGFOX_DEVICES_ID):
        sfxs_db = INFLUXDB_SLFX_DATABASE_NAME
    elif (device_id in SYNCFX_SIGFOX_DEVICES_ID):
        sfxs_db = INFLUXDB_SYNCFX_DATABASE_NAME
    elif (device_id in TKFX_SIGFOX_DEVICES_ID):
        sfxs_db = INFLUXDB_TKFX_DATABASE_NAME
    return sfxs_db

# Function performing Sigfox ID to MeteoFox site conversion.
def MFX_GetSite(device_id):
    # Default is unknown.
    meteofox_site = "Unknown site (" + str(device_id) + ")"
    if (device_id in MFX_SIGFOX_DEVICES_ID):
        meteofox_site = MFX_SIGFOX_DEVICES_SITE[MFX_SIGFOX_DEVICES_ID.index(device_id)]
    return meteofox_site

# Function performing Sigfox ID to ATX rack conversion
def ATXFX_GetRack(device_id):
    # Default is unknown.
    atxfox_rack = "Unknown rack (" + str(device_id) + ")"
    if (device_id in ATXFX_SIGFOX_DEVICES_ID):
        atxfox_rack = ATXFX_SIGFOX_DEVICES_RACK[ATXFX_SIGFOX_DEVICES_ID.index(device_id)]
    return atxfox_rack

# Function performing Sigfox ID to ATX front end conversion
def ATXFX_GetFrontEnd(device_id):
    # Default is unknown.
    atxfox_front_end = "Unknown front-end (" + str(device_id) + ")"
    if (device_id in ATXFX_SIGFOX_DEVICES_ID):
        atxfox_front_end = ATXFX_SIGFOX_DEVICES_FRONT_END[ATXFX_SIGFOX_DEVICES_ID.index(device_id)]
    return atxfox_front_end

# Function performing Sigfox ID to SolarFox site conversion.
def SLFX_GetSite(device_id):
    # Default is unknown.
    solarfox_site = "Unknown site (" + str(device_id) + ")"
    if (device_id in SLFX_SIGFOX_DEVICES_ID):
        solarfox_site = SLFX_SIGFOX_DEVICES_SITE[SLFX_SIGFOX_DEVICES_ID.index(device_id)]
    return solarfox_site

# Function performing Sigfox ID to TrackFox asset conversion.
def TKFX_GetAsset(device_id):
    # Default is unknown.
    trackfox_asset = "Unknown asset (" + str(device_id) + ")"
    if (device_id in TKFX_SIGFOX_DEVICES_ID):
        trackfox_asset = TKFX_SIGFOX_DEVICES_ASSET[TKFX_SIGFOX_DEVICES_ID.index(device_id)]
    return trackfox_asset

# Function performing Sigfox ID to SynchroFox site conversion.
def SYNCFX_GetSite(device_id):
    # Default is unknown.
    synchrofox_site = "Unknown site (" + str(device_id) + ")"
    if (device_id in SYNCFX_SIGFOX_DEVICES_ID):
        synchrofox_site = SYNCFX_SIGFOX_DEVICES_SITE[SYNCFX_SIGFOX_DEVICES_ID.index(device_id)]
    return synchrofox_site

# Function to compute sea-level pressure (barometric formula).
def MFX_GetSeaLevelPressure(absolute_pressure, altitude, temperature):
    # a^(x) = exp(x*ln(a))
    temperature_kelvin = temperature + 273.15
    return (absolute_pressure * math.exp(-5.255 * math.log((temperature_kelvin) / (temperature_kelvin + 0.0065 * altitude))))

# Function for parsing MeteoFox device payload and fill database.
def MFX_FillDataBase(timestamp, device_id, data):
    # Format parameters.
    influxdb_device_id = device_id.upper()
    influxdb_timestamp = int(timestamp)
    # OOB frame.
    if data == MFX_SIGFOX_OOB_DATA:
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
                INFLUXDB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        }]
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "MFX ID=" + str(device_id) + " * OOB frame (start up).")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Monitoring frame.
    if len(data) == (2 * MFX_SIGFOX_MONITORING_FRAME_LENGTH_BYTES):
        # Parse fields.
        mcu_temperature_raw = int(data[0:2], 16)
        mcu_temperature = mcu_temperature_raw & 0x7F
        if ((mcu_temperature_raw & 0x80) != 0):
            mcu_temperature = (-1) * mcu_temperature
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
                INFLUXDB_FIELD_SOLAR_CELL_VOLTAGE : solar_cell_voltage,
                INFLUXDB_FIELD_SUPERCAP_VOLTAGE : supercap_voltage,
                INFLUXDB_FIELD_MCU_VOLTAGE : mcu_voltage,
                INFLUXDB_FIELD_STATUS_BYTE : status_byte,
                INFLUXDB_FIELD_LAST_MONITORING_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
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
                INFLUXDB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        }]
        # Manage error values.
        pcb_temperature = "error"
        if (int(data[2:4], 16) != MFX_TEMPERATURE_ERROR):
            pcb_temperature_raw = int(data[2:4], 16)
            pcb_temperature = pcb_temperature_raw & 0x7F
            if ((pcb_temperature_raw & 0x80) != 0):
                pcb_temperature = (-1) * pcb_temperature
            json_body[0]["fields"][INFLUXDB_FIELD_PCB_TEMPERATURE] = pcb_temperature
        pcb_humidity = "error"
        if (int(data[4:6], 16) != MFX_HUMIDITY_ERROR):
            pcb_humidity = int(data[4:6], 16)
            json_body[0]["fields"][INFLUXDB_FIELD_PCB_HUMIDITY] = pcb_humidity
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "MFX ID=" + str(device_id) + " * Monitoring data * McuTemp=" + str(mcu_temperature) + "dC, PcbTemp=" + str(pcb_temperature) + "dC, PcbHum=" + str(pcb_humidity) + "%, SolarVolt=" + str(solar_cell_voltage) + "mV, SupercapVolt=" + str(supercap_voltage) + "mV, McuVolt=" + str(mcu_voltage) + "mV, Status=" + str(status_byte) + ".")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Intermittent eather data frame.
    if len(data) == (2 * MFX_SIGFOX_INTERMITTENT_WEATHER_DATA_FRAME_LENGTH_BYTES):
        # Parse fields.
        light = int(data[4:6], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_WEATHER,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_LIGHT : light,
                INFLUXDB_FIELD_LAST_WEATHER_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
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
                INFLUXDB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        }]
        # Manage error values.
        temperature = "error"
        if (int(data[0:2], 16) != MFX_TEMPERATURE_ERROR):
            temperature_raw = int(data[0:2], 16)
            temperature = temperature_raw & 0x7F
            if ((temperature_raw & 0x80) != 0):
                temperature = (-1) * temperature
            json_body[0]["fields"][INFLUXDB_FIELD_TEMPERATURE] = temperature
        humidity = "error"
        if (int(data[2:4], 16) != MFX_HUMIDITY_ERROR):
            humidity = int(data[2:4], 16)
            json_body[0]["fields"][INFLUXDB_FIELD_HUMIDITY] = humidity
        uv_index = "error"
        if (int(data[6:8], 16) != MFX_UV_INDEX_ERROR):
            uv_index = int(data[6:8], 16)
            json_body[0]["fields"][INFLUXDB_FIELD_UV_INDEX] = uv_index
        absolute_pressure = "error"
        sea_level_pressure = "error"
        if (int(data[8:12], 16) != MFX_PRESSURE_ERROR):
            absolute_pressure = (int(data[8:12], 16) / 10.0)
            json_body[0]["fields"][INFLUXDB_FIELD_ABSOLUTE_PRESSURE] = absolute_pressure
            if (int(data[0:2], 16) != MFX_TEMPERATURE_ERROR):
                try:
                    altitude_query = "SELECT last(altitude) FROM geoloc WHERE sigfox_device_id='" + influxdb_device_id + "'"
                    altitude_query_result = influxdb_client.query(altitude_query)
                    altitude_points = altitude_query_result.get_points()
                    for point in altitude_points:
                        altitude = int(point["last"])
                    sea_level_pressure = MFX_GetSeaLevelPressure(absolute_pressure, altitude, temperature)
                    json_body[0]["fields"][INFLUXDB_FIELD_SEA_LEVEL_PRESSURE] = sea_level_pressure
                except:
                    # Altitude is not available yet for this device.
                    sea_level_pressure = "error"
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "MFX ID=" + str(device_id) + " * Weather data * Temp=" + str(temperature) + "dC, Hum=" + str(humidity) + "%, Light=" + str(light) + "%, UV=" + str(uv_index) + ", AbsPres=" + str(absolute_pressure) + "hPa, SeaPres=" + str(sea_level_pressure) + "hpa.")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Continuous weather data frame.
    if len(data) == (2 * MFX_SIGFOX_CONTINUOUS_WEATHER_DATA_FRAME_LENGTH_BYTES):
        # Parse fields.
        light = int(data[4:6], 16)
        average_wind_speed = int(data[12:14], 16)
        peak_wind_speed = int(data[14:16], 16)
        rain = int(data[18:20], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_WEATHER,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_LIGHT : light,
                INFLUXDB_FIELD_AVERAGE_WIND_SPEED : average_wind_speed,
                INFLUXDB_FIELD_PEAK_WIND_SPEED : peak_wind_speed,
                INFLUXDB_FIELD_RAIN : rain,
                INFLUXDB_FIELD_LAST_WEATHER_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
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
                INFLUXDB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        }]
        # Manage error values.
        temperature = "error"
        if (int(data[0:2], 16) != MFX_TEMPERATURE_ERROR):
            temperature_raw = int(data[0:2], 16)
            temperature = temperature_raw & 0x7F
            if ((temperature_raw & 0x80) != 0):
                temperature = (-1) * temperature
            json_body[0]["fields"][INFLUXDB_FIELD_TEMPERATURE] = temperature
        humidity = "error"
        if (int(data[2:4], 16) != MFX_HUMIDITY_ERROR):
            humidity = int(data[2:4], 16)
            json_body[0]["fields"][INFLUXDB_FIELD_HUMIDITY] = humidity
        uv_index = "error"
        if (int(data[6:8], 16) != MFX_UV_INDEX_ERROR):
            uv_index = int(data[6:8], 16)
            json_body[0]["fields"][INFLUXDB_FIELD_UV_INDEX] = uv_index
        absolute_pressure = "error"
        sea_level_pressure = "error"
        if (int(data[8:12], 16) != MFX_PRESSURE_ERROR):
            absolute_pressure = (int(data[8:12], 16) / 10.0)
            json_body[0]["fields"][INFLUXDB_FIELD_ABSOLUTE_PRESSURE] = absolute_pressure
            if (int(data[0:2], 16) != MFX_TEMPERATURE_ERROR):
                try:
                    altitude_query = "SELECT last(altitude) FROM geoloc WHERE sigfox_device_id='" + influxdb_device_id + "'"
                    altitude_query_result = influxdb_client.query(altitude_query)
                    altitude_points = altitude_query_result.get_points()
                    for point in altitude_points:
                        altitude = int(point["last"])
                    sea_level_pressure = MFX_GetSeaLevelPressure(absolute_pressure, altitude, temperature)
                    json_body[0]["fields"][INFLUXDB_FIELD_SEA_LEVEL_PRESSURE] = sea_level_pressure
                except:
                    # Altitude is not available yet for this device.
                    sea_level_pressure = "error"
        average_wind_direction = "error"
        if (int(data[16:18], 16) != MFX_WIND_ERROR):
            average_wind_direction = 2 * int(data[16:18], 16)
            json_body[0]["fields"][INFLUXDB_FIELD_AVERAGE_WIND_DIRECTION] = average_wind_direction
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "MFX ID=" + str(device_id) + " * Weather data * Temp=" + str(temperature) + "C, Hum=" + str(humidity) + "%, Light=" + str(light) + "%, UV=" + str(uv_index) + ", Pres=" + str(absolute_pressure) + "hPa, SeaPres=" + str(sea_level_pressure) + "hPa, AvWindSp=" + str(average_wind_speed) + "km/h, PeakWindSp=" + str(peak_wind_speed) + "km/h, AvWindDir=" + str(average_wind_direction) + "d, Rain=" + str(rain) + "mm.")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Geolocation frame.
    if len(data) == (2 * MFX_SIGFOX_GEOLOCATION_FRAME_LENGTH_BYTES):
        # Parse fields.
        latitude_degrees = int(data[0:2], 16)
        latitude_minutes = (int(data[2:4], 16) >> 2) & 0x3F
        latitude_seconds = ((((int(data[2:8], 16) & 0x03FFFE) >> 1) & 0x01FFFF) / (100000.0)) * 60.0
        latitude_north = int(data[6:8], 16) & 0x01
        latitude = latitude_degrees + (latitude_minutes / 60.0) + (latitude_seconds / 3600.0)
        if (latitude_north == 0):
            latitude = -latitude
        longitude_degrees = int(data[8:10], 16)
        longitude_minutes = (int(data[10:12], 16) >> 2) & 0x3F
        longitude_seconds = ((((int(data[10:16], 16) & 0x03FFFE) >> 1) & 0x01FFFF) / (100000.0)) * 60.0
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
                INFLUXDB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
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
                INFLUXDB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        }]
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "MFX ID=" + str(device_id) + " * Geoloc data * Lat=" + str(latitude) + ", Long=" + str(longitude) + ", Alt=" + str(altitude) + "m, GpsFixDur=" + str(gps_fix_duration) + "s.")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Geolocation timeout frame.
    if len(data) == (2 * MFX_SIGFOX_GEOLOCATION_TIMEOUT_FRAME_LENGTH_BYTES):
        gps_fix_duration = int(data[0:2], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_GEOLOC,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_GPS_FIX_DURATION : gps_fix_duration,
                INFLUXDB_FIELD_LAST_GEOLOC_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
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
                INFLUXDB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        }]
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "MFX ID=" + str(device_id) + " * Geoloc timeout * GpsFixDur=" + str(gps_fix_duration) + "s.")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')

# Function for parsing ATXFox device payload and fill database.      
def ATXFX_FillDataBase(timestamp, device_id, data):
    # Format parameters.
    influxdb_device_id = device_id.upper()
    influxdb_timestamp = int(timestamp)
    # Start-stop frame.
    if len(data) == (2 * ATXFX_SIGFOX_START_STOP_FRAME_LENGTH_BYTES):
        status_raw = (int(data[0:2], 16)) & 0xFF
        # Check status.
        if (status_raw == 0x00):  
            # Create JSON object.
            json_body = [
            {
                "measurement": INFLUXDB_MEASUREMENT_GLOBAL,
                "time": influxdb_timestamp,
                "fields": {
                    INFLUXDB_FIELD_LAST_SHUTDOWN_TIMESTAMP : influxdb_timestamp,
                    INFLUXDB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp,
                    INFLUXDB_FIELD_STATE : status_raw
                },
                "tags": {
                    INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                    INFLUXDB_TAG_ATXFOX_RACK : ATXFX_GetRack(influxdb_device_id),
                    INFLUXDB_TAG_ATXFOX_FRONT_END : ATXFX_GetFrontEnd(influxdb_device_id)
                }
            }]
            if SFXS_LOG == True:
                print(SFXS_GetCurrentTimestamp() + "ATXFX ID=" + str(device_id) + " * Shutdown.")
            # Fill data base.
            influxdb_client.write_points(json_body, time_precision='s')
        if (status_raw == 0x01):
            # Create JSON object.
            json_body = [
            {
                "measurement": INFLUXDB_MEASUREMENT_GLOBAL,
                "time": influxdb_timestamp,
                "fields": {
                    INFLUXDB_FIELD_LAST_STARTUP_TIMESTAMP : influxdb_timestamp,
                    INFLUXDB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp,
                    INFLUXDB_FIELD_STATE : status_raw
                },
                "tags": {
                    INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                    INFLUXDB_TAG_ATXFOX_RACK : ATXFX_GetRack(influxdb_device_id),
                    INFLUXDB_TAG_ATXFOX_FRONT_END : ATXFX_GetFrontEnd(influxdb_device_id)
                }
            }]
            if SFXS_LOG == True:
                print(SFXS_GetCurrentTimestamp() + "ATXFX ID=" + str(device_id) + " * Start-up.")
            # Fill data base.
            influxdb_client.write_points(json_body, time_precision='s')
    # Monitoring frame.
    if len(data) == (2 * ATXFX_SIGFOX_MONITORING_FRAME_LENGTH_BYTES):
        # Parse fields.
        output_voltage = ((int(data[0:4], 16)) >> 2) & 0x3FFF
        current_sense_range = ((int(data[0:4], 16)) >> 0) & 0x0003
        mcu_voltage = int(data[10:14], 16)
        mcu_temperature_raw = int(data[14:16], 16)
        mcu_temperature = mcu_temperature_raw & 0x7F
        if ((mcu_temperature_raw & 0x80) != 0):
            mcu_temperature = (-1) * mcu_temperature
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_MONITORING,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_OUTPUT_VOLTAGE : output_voltage,
                INFLUXDB_FIELD_CURRENT_SENSE_RANGE : current_sense_range,
                INFLUXDB_FIELD_MCU_VOLTAGE : mcu_voltage,
                INFLUXDB_FIELD_MCU_TEMPERATURE : mcu_temperature,
                INFLUXDB_FIELD_LAST_MONITORING_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_ATXFOX_RACK : ATXFX_GetRack(influxdb_device_id),
                INFLUXDB_TAG_ATXFOX_FRONT_END : ATXFX_GetFrontEnd(influxdb_device_id)
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
                INFLUXDB_TAG_ATXFOX_RACK : ATXFX_GetRack(influxdb_device_id),
                INFLUXDB_TAG_ATXFOX_FRONT_END : ATXFX_GetFrontEnd(influxdb_device_id)
            }
        }]
        # Manage error values.
        output_current = "unknown"
        output_power = "unknown"
        if (int(data[4:10], 16) != ATXFX_OUTPUT_CURRENT_ERROR):
            output_current = int(data[4:10], 16)
            json_body[0]["fields"][INFLUXDB_FIELD_OUTPUT_CURRENT] = output_current
            # Compute output power in nW (uA * mV).
            output_power = (output_voltage * output_current)
            json_body[0]["fields"][INFLUXDB_FIELD_OUTPUT_POWER] = output_power
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "ATXFX ID=" + str(device_id) + " * Monitoring data * U=" + str(output_voltage) + "mV, Range=" + str(current_sense_range) + ", I=" + str(output_current) + "uA, P=" + str(output_power) + "nW, McuVoltage=" + str(mcu_voltage) + "mV, McuTemp=" + str(mcu_temperature) + "dC.")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')

# Function for parsing SolarFox device payload and fill database.      
def SLFX_FillDataBase(timestamp, device_id, data):
    # Format parameters.
    influxdb_device_id = device_id.upper()
    influxdb_timestamp = int(timestamp)
    # Monitoring frame.
    if len(data) == (2 * SLFX_SIGFOX_MONITORING_DATA_FRAME_LENGTH_BYTES):
        # Parse fields.
        solar_cell_voltage = int(data[0:4], 16)
        output_voltage = int(data[4:8], 16)
        output_current = int(data[8:14], 16)
        mcu_voltage = int(data[14:18], 16)
        mcu_temperature_raw = int(data[18:20], 16)
        mcu_temperature = mcu_temperature_raw & 0x7F
        if ((mcu_temperature_raw & 0x80) != 0):
            mcu_temperature = (-1) * mcu_temperature
        # Compute power in nW (mV * uA)
        output_power = (output_voltage * output_current)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_MONITORING,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_SOLAR_CELL_VOLTAGE : solar_cell_voltage,
                INFLUXDB_FIELD_OUTPUT_VOLTAGE : output_voltage,
                INFLUXDB_FIELD_OUTPUT_CURRENT : output_current,
                INFLUXDB_FIELD_OUTPUT_POWER : output_power,
                INFLUXDB_FIELD_MCU_VOLTAGE : mcu_voltage,
                INFLUXDB_FIELD_MCU_TEMPERATURE : mcu_temperature,
                INFLUXDB_FIELD_LAST_MONITORING_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_SOLARFOX_SITE : SLFX_GetSite(influxdb_device_id)
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
                INFLUXDB_TAG_SOLARFOX_SITE : SLFX_GetSite(influxdb_device_id)
            }
        }]
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "SLFX ID=" + str(device_id) + " * Monitoring data * Vpv=" + str(solar_cell_voltage) + "mV, Vout=" + str(output_voltage) + "mV, Iout=" + str(output_current) + "uA, McuVoltage=" + str(mcu_voltage) + "mV, McuTemp=" + str(mcu_temperature) + "dC.")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')

# Function for parsing TrackFox device payload and fill database.
def TKFX_FillDataBase(timestamp, device_id, data):
    # Format parameters.
    influxdb_device_id = device_id.upper()
    influxdb_timestamp = int(timestamp)
    # OOB frame.
    if data == TKFX_SIGFOX_OOB_DATA:
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
                INFLUXDB_TAG_TRACKFOX_ASSET : TKFX_GetAsset(influxdb_device_id)
            }
        }]
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "TKFX ID=" + str(device_id) + " * OOB frame (start up).")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Monitoring frame.
    if len(data) == (2 * TKFX_SIGFOX_MONITORING_FRAME_LENGTH_BYTES):
        # Parse fields.
        mcu_temperature_raw = int(data[2:4], 16)
        mcu_temperature = mcu_temperature_raw & 0x7F
        if ((mcu_temperature_raw & 0x80) != 0):
            mcu_temperature = (-1) * mcu_temperature
        source_voltage = int(data[4:8], 16)
        supercap_voltage = ((int(data[8:10], 16) << 4) & 0x0FF0) + ((int(data[10:12], 16) >> 4) & 0x000F)
        mcu_voltage = ((int(data[10:12], 16) << 8) & 0x0F00) + ((int(data[12:14], 16) >> 0) & 0x00FF)
        status_byte = int(data[14:16], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_MONITORING,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_MCU_TEMPERATURE : mcu_temperature,
                INFLUXDB_FIELD_SOURCE_VOLTAGE : source_voltage,
                INFLUXDB_FIELD_SUPERCAP_VOLTAGE : supercap_voltage,
                INFLUXDB_FIELD_MCU_VOLTAGE : mcu_voltage,
                INFLUXDB_FIELD_STATUS_BYTE : status_byte,
                INFLUXDB_FIELD_LAST_MONITORING_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_TRACKFOX_ASSET : TKFX_GetAsset(influxdb_device_id)
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
                INFLUXDB_TAG_TRACKFOX_ASSET : TKFX_GetAsset(influxdb_device_id)
            }
        }]
        # Manage error values.
        temperature = "error"
        if (int(data[0:2], 16) != TKFX_TEMPERATURE_ERROR):
            temperature_raw = int(data[0:2], 16)
            temperature = temperature_raw & 0x7F
            if ((temperature_raw & 0x80) != 0):
                temperature = (-1) * temperature
            json_body[0]["fields"][INFLUXDB_FIELD_TEMPERATURE] = temperature
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "TKFX ID=" + str(device_id) + " * Monitoring data * SourceVolt=" + str(source_voltage) + "mV, SupercapVolt=" + str(supercap_voltage) + "mV, McuVolt=" + str(mcu_voltage) + "mV, Temp=" + str(temperature) + "dC, McuTemp=" + str(mcu_temperature) + "dC, Status=" + str(status_byte) + ".")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Geolocation frame.
    if len(data) == (2 * TKFX_SIGFOX_GEOLOCATION_FRAME_LENGTH_BYTES):
        # Parse fields.
        latitude_degrees = int(data[0:2], 16)
        latitude_minutes = (int(data[2:4], 16) >> 2) & 0x3F
        latitude_seconds = ((((int(data[2:8], 16) & 0x03FFFE) >> 1) & 0x01FFFF) / (100000.0)) * 60.0
        latitude_north = int(data[6:8], 16) & 0x01
        latitude = latitude_degrees + (latitude_minutes / 60.0) + (latitude_seconds / 3600.0)
        if (latitude_north == 0):
            latitude = -latitude
        longitude_degrees = int(data[8:10], 16)
        longitude_minutes = (int(data[10:12], 16) >> 2) & 0x3F
        longitude_seconds = ((((int(data[10:16], 16) & 0x03FFFE) >> 1) & 0x01FFFF) / (100000.0)) * 60.0
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
                INFLUXDB_TAG_TRACKFOX_ASSET : TKFX_GetAsset(influxdb_device_id)
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
                INFLUXDB_TAG_TRACKFOX_ASSET : TKFX_GetAsset(influxdb_device_id)
            }
        }]
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "TKFX ID=" + str(device_id) + " * Geoloc data * Lat=" + str(latitude) + ", Long=" + str(longitude) + ", Alt=" + str(altitude) + "m, GpsFixDur=" + str(gps_fix_duration) + "s.")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Geolocation timeout frame.
    if len(data) == (2 * TKFX_SIGFOX_GEOLOCATION_TIMEOUT_FRAME_LENGTH_BYTES):
        gps_fix_duration = int(data[0:2], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_GEOLOC,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_GPS_FIX_DURATION : gps_fix_duration,
                INFLUXDB_FIELD_LAST_GEOLOC_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_TRACKFOX_ASSET : TKFX_GetAsset(influxdb_device_id)
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
                INFLUXDB_TAG_TRACKFOX_ASSET : TKFX_GetAsset(influxdb_device_id)
            }
        }]
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "TKFX ID=" + str(device_id) + " * Geoloc timeout * GpsFixDur=" + str(gps_fix_duration) + "s.")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
        
# Function for parsing SynchroFox device payload and fill database.
def SYNCFX_FillDataBase(timestamp, device_id, data):
    # Format parameters.
    influxdb_device_id = device_id.upper()
    influxdb_timestamp = int(timestamp)
    # OOB frame.
    if data == SYNCFX_SIGFOX_OOB_DATA:
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
                INFLUXDB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
            }
        }]
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "SYNCFX ID=" + str(device_id) + " * OOB frame (start up).")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Monitoring frame.
    if len(data) == (2 * SYNCFX_SIGFOX_MONITORING_FRAME_LENGTH_BYTES):
        # Parse fields.
        solar_cell_voltage = 10 * (((int(data[0:2], 16) << 2) & 0x03FC) + ((int(data[2:4], 16) >> 6) & 0x0003))
        battery_voltage = 10 * (((int(data[2:4], 16) << 4) & 0x03F0) + ((int(data[4:6], 16) >> 4) & 0x000F))
        mcu_voltage = 10 * (((int(data[4:6], 16) << 6) & 0x03C0) + ((int(data[6:8], 16) >> 2) & 0x003F))
        gpsdo_lock_duration = ((int(data[6:8], 16) << 8) & 0x0300) + ((int(data[8:10], 16) >> 0) & 0x00FF)
        mcu_temperature_raw = int(data[10:12], 16)
        mcu_temperature_abs = mcu_temperature_raw & 0x7F
        mcu_temperature = mcu_temperature_abs
        if ((mcu_temperature_raw & 0x80) != 0):
            mcu_temperature = (-1) * ((~mcu_temperature_abs & 0x7F) + 1)
        status_byte = int(data[12:14], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_MONITORING,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_SOLAR_CELL_VOLTAGE : solar_cell_voltage,
                INFLUXDB_FIELD_BATTERY_VOLTAGE : battery_voltage,
                INFLUXDB_FIELD_MCU_VOLTAGE : mcu_voltage,
                INFLUXDB_FIELD_GPSDO_LOCK_DURATION : gpsdo_lock_duration,
                INFLUXDB_FIELD_MCU_TEMPERATURE : mcu_temperature,
                INFLUXDB_FIELD_STATUS_BYTE : status_byte,
                INFLUXDB_FIELD_LAST_MONITORING_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
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
                INFLUXDB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
            }
        }]
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "SYNCFX ID=" + str(device_id) + " * Monitoring data * SolarVolt=" + str(solar_cell_voltage) + "mV, BattVolt=" + str(battery_voltage) + "mV, McuVolt=" + str(mcu_voltage) + "mV, GpsdoLockDur=" + str(gpsdo_lock_duration) + "s, McuTemp=" + str(mcu_temperature) + "dC, Status=" + str(status_byte) + ".")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Synchronization frame.
    if len(data) == (2 * SYNCFX_SIGFOX_SYNCHRO_FRAME_LENGTH_BYTES):
        hours = (int(data[0:2], 16) >> 3) & 0x1F
        minutes = ((int(data[0:2], 16) << 3) & 0x38) + ((int(data[2:4], 16) >> 5) & 0x07)
        seconds = ((int(data[2:4], 16) << 1) & 0x3E) + ((int(data[4:6], 16) >> 7) & 0x01)
        frequency = ((int(data[4:6], 16) << 24) & 0x7F000000) + ((int(data[6:8], 16) << 16) & 0x00FF0000) + ((int(data[8:10], 16) << 8) & 0x0000FF00) + ((int(data[10:12], 16) << 0) & 0x000000FF)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_SYNCHRO,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_HOURS : hours,
                INFLUXDB_FIELD_MINUTES : minutes,
                INFLUXDB_FIELD_SECONDS : seconds,
                INFLUXDB_FIELD_FREQUENCY : frequency,
                INFLUXDB_FIELD_LAST_SYNCHRO_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
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
                INFLUXDB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
            }
        }]
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "SYNCFX ID=" + str(device_id) + " * Synchro data * Hours=" + str(hours) + "h, Minutes=" + str(minutes) + "m, Seconds=" + str(seconds) + "h, Freq=" + str(frequency) + "Hz.")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Geolocation frame.
    if len(data) == (2 * SYNCFX_SIGFOX_GEOLOCATION_FRAME_LENGTH_BYTES):
        # Parse fields.
        latitude_degrees = int(data[0:2], 16)
        latitude_minutes = (int(data[2:4], 16) >> 2) & 0x3F
        latitude_seconds = ((((int(data[2:8], 16) & 0x03FFFE) >> 1) & 0x01FFFF) / (100000.0)) * 60.0
        latitude_north = int(data[6:8], 16) & 0x01
        latitude = latitude_degrees + (latitude_minutes / 60.0) + (latitude_seconds / 3600.0)
        if (latitude_north == 0):
            latitude = -latitude
        longitude_degrees = int(data[8:10], 16)
        longitude_minutes = (int(data[10:12], 16) >> 2) & 0x3F
        longitude_seconds = ((((int(data[10:16], 16) & 0x03FFFE) >> 1) & 0x01FFFF) / (100000.0)) * 60.0
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
                INFLUXDB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
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
                INFLUXDB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
            }
        }]
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "SYNCFX ID=" + str(device_id) + " * Geoloc data * Lat=" + str(latitude) + ", Long=" + str(longitude) + ", Alt=" + str(altitude) + "m, GpsFixDur=" + str(gps_fix_duration) + "s.")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
    # Geolocation timeout frame.
    if len(data) == (2 * SYNCFX_SIGFOX_GEOLOCATION_TIMEOUT_FRAME_LENGTH_BYTES):
        gps_fix_duration = int(data[0:2], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUXDB_MEASUREMENT_GEOLOC,
            "time": influxdb_timestamp,
            "fields": {
                INFLUXDB_FIELD_GPS_FIX_DURATION : gps_fix_duration,
                INFLUXDB_FIELD_LAST_GEOLOC_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUXDB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUXDB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
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
                INFLUXDB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
            }
        }]
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "SYNCFX ID=" + str(device_id) + " * Geoloc timeout * GpsFixDur=" + str(gps_fix_duration) + "s.")
        # Fill data base.
        influxdb_client.write_points(json_body, time_precision='s')
        
### CLASS DECLARATIONS ###

class ServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if SFXS_LOG == True:
            print("")
            print(SFXS_GetCurrentTimestamp() + "GET request received.")
        self.send_response(200)     
    def do_HEAD(self):
        if SFXS_LOG == True:
            print("")
            print(SFXS_GetCurrentTimestamp() + "HEAD request received.")
        self.send_response(200)   
    def do_POST(self):
        # Get JSON content.
        post_length = int(self.headers.getheader('content-length', 0))
        post_json = json.loads(self.rfile.read(post_length))
        if SFXS_LOG == True:
            print("")
            print(SFXS_GetCurrentTimestamp() + "POST request received.")
        # Parse data.
        callback_timestamp = post_json[SIGFOX_BACKEND_JSON_HEADER_TIME]
        callback_device_id = post_json[SIGFOX_BACKEND_JSON_HEADER_DEVICE_ID]
        callback_data = post_json[SIGFOX_BACKEND_JSON_HEADER_DATA]
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "SIGFOX backend callback * Timestamp=" + callback_timestamp + " ID=" + callback_device_id + " Data=" + callback_data)
        # Update database.
        sfxs_database = SFXS_GetDataBase(callback_device_id)
        if (sfxs_database == INFLUXDB_MFX_DATABASE_NAME):
            if SFXS_LOG == True:
                print(SFXS_GetCurrentTimestamp() + "Switching to database " + INFLUXDB_MFX_DATABASE_NAME + ".")
            influxdb_client.switch_database(INFLUXDB_MFX_DATABASE_NAME)
            MFX_FillDataBase(int(callback_timestamp), callback_device_id, callback_data)
        elif (sfxs_database == INFLUXDB_ATXFX_DATABASE_NAME):
            influxdb_client.switch_database(INFLUXDB_ATXFX_DATABASE_NAME)
            if SFXS_LOG == True:
                print(SFXS_GetCurrentTimestamp() + "Switching to database " + INFLUXDB_ATXFX_DATABASE_NAME + ".")
            ATXFX_FillDataBase(int(callback_timestamp), callback_device_id, callback_data)
        elif (sfxs_database == INFLUXDB_SLFX_DATABASE_NAME):
            influxdb_client.switch_database(INFLUXDB_SLFX_DATABASE_NAME)
            if SFXS_LOG == True:
                print(SFXS_GetCurrentTimestamp() + "Switching to database " + INFLUXDB_SLFX_DATABASE_NAME + ".")
            SLFX_FillDataBase(int(callback_timestamp), callback_device_id, callback_data)
        elif (sfxs_database == INFLUXDB_SYNCFX_DATABASE_NAME):
            influxdb_client.switch_database(INFLUXDB_SYNCFX_DATABASE_NAME)
            if SFXS_LOG == True:
                print(SFXS_GetCurrentTimestamp() + "Switching to database " + INFLUXDB_SYNCFX_DATABASE_NAME + ".")
            SYNCFX_FillDataBase(int(callback_timestamp), callback_device_id, callback_data)
        elif (sfxs_database == INFLUXDB_TKFX_DATABASE_NAME):
            influxdb_client.switch_database(INFLUXDB_TKFX_DATABASE_NAME)
            if SFXS_LOG == True:
                print(SFXS_GetCurrentTimestamp() + "Switching to database " + INFLUXDB_TKFX_DATABASE_NAME + ".")
            TKFX_FillDataBase(int(callback_timestamp), callback_device_id, callback_data)
        else:
            if SFXS_LOG == True:
                print(SFXS_GetCurrentTimestamp() + "Unknown Sigfox device ID.")
        # Send HTTP response.
        self.send_response(200)

### MAIN PROGRAM ###

if SFXS_LOG == True:
    print("\n*******************************************************")
    print("------------ Sigfox Devices Server (SFXS) -------------")
    print("*******************************************************\n")

# Wait for InfluxDB to be availabmle and create client.
influxdb_found = False
while influxdb_found == False:
    try:
        influxdb_client = InfluxDBClient(host='localhost', port=INFLUXDB_DATABASE_HTTP_PORT)
        influxdb_found = True
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "InfluxDB connection OK.")
    except:
        influxdb_found = False

# Get list of existing databases.
influxdb_database_list = influxdb_client.get_list_database()
influxdb_mfxdb_found = False
influxdb_atxfxdb_found = False
influxdb_slfxdb_found = False
influxdb_syncfxdb_found = False
influxdb_tkfxdb_found = False
for influxdb_database in influxdb_database_list:
    if (influxdb_database['name'].find(INFLUXDB_MFX_DATABASE_NAME) >= 0):
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "MeteoFox database found.")
        influxdb_mfxdb_found = True
    if (influxdb_database['name'].find(INFLUXDB_ATXFX_DATABASE_NAME) >= 0):
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "ATXFox database found.")
        influxdb_atxfxdb_found = True
    if (influxdb_database['name'].find(INFLUXDB_SLFX_DATABASE_NAME) >= 0):
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "SolarFox database found.")
        influxdb_slfxdb_found = True
    if (influxdb_database['name'].find(INFLUXDB_SYNCFX_DATABASE_NAME) >= 0):
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "SynchroFox database found.")
        influxdb_syncfxdb_found = True
    if (influxdb_database['name'].find(INFLUXDB_TKFX_DATABASE_NAME) >= 0):
        if SFXS_LOG == True:
            print(SFXS_GetCurrentTimestamp() + "TrackFox database found.")
        influxdb_tkfxdb_found = True

# Create MeteoFox database if it does not exist.   
if (influxdb_mfxdb_found == False):
    if SFXS_LOG == True:
        print(SFXS_GetCurrentTimestamp() + "Creating database " + INFLUXDB_MFX_DATABASE_NAME + ".")
    influxdb_client.create_database(INFLUXDB_MFX_DATABASE_NAME)
# Create ATXFox database if it does not exist.   
if (influxdb_atxfxdb_found == False):
    if SFXS_LOG == True:
        print(SFXS_GetCurrentTimestamp() + "Creating database " + INFLUXDB_ATXFX_DATABASE_NAME + ".")
    influxdb_client.create_database(INFLUXDB_ATXFX_DATABASE_NAME)
# Create SolarFox database if it does not exist.   
if (influxdb_slfxdb_found == False):
    if SFXS_LOG == True:
        print(SFXS_GetCurrentTimestamp() + "Creating database " + INFLUXDB_SLFX_DATABASE_NAME + ".")
    influxdb_client.create_database(INFLUXDB_SLFX_DATABASE_NAME)
if (influxdb_syncfxdb_found == False):
    if SFXS_LOG == True:
        print(SFXS_GetCurrentTimestamp() + "Creating database " + INFLUXDB_SYNCFX_DATABASE_NAME + ".")
    influxdb_client.create_database(INFLUXDB_SYNCFX_DATABASE_NAME)
if (influxdb_tkfxdb_found == False):
    if SFXS_LOG == True:
        print(SFXS_GetCurrentTimestamp() + "Creating database " + INFLUXDB_TKFX_DATABASE_NAME + ".")
    influxdb_client.create_database(INFLUXDB_TKFX_DATABASE_NAME)
        
# Start server.
SocketServer.TCPServer.allow_reuse_address = True
mfxs_handler = ServerHandler
mfxs = SocketServer.TCPServer(("", SFXS_HTTP_PORT), mfxs_handler)
if SFXS_LOG == True:
    print (SFXS_GetCurrentTimestamp() + "Starting server at port " + str(SFXS_HTTP_PORT) + ".")
mfxs.serve_forever()