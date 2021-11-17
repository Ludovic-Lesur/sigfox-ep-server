from __future__ import print_function

from influx_db import *
from log import *

### MACROS ###

TKFX_SIGFOX_DEVICES_ID = ["4761", "479C", "47A7", "47EA", "4894"]
TKFX_SIGFOX_DEVICES_ASSET = ["Car", "Bike", "Hiking", "Unknown", "Unknown"]

TKFX_SIGFOX_OOB_DATA = "OOB"
TKFX_SIGFOX_MONITORING_FRAME_LENGTH_BYTES = 8
TKFX_SIGFOX_GEOLOCATION_FRAME_LENGTH_BYTES = 11
TKFX_SIGFOX_GEOLOCATION_TIMEOUT_FRAME_LENGTH_BYTES = 1

TKFX_TEMPERATURE_ERROR = 0x7F

### FUNCTIONS ###

# Function performing Sigfox ID to TrackFox asset conversion.
def TKFX_GetAsset(device_id):
    # Default is unknown.
    trackfox_asset = "Unknown asset (" + str(device_id) + ")"
    if (device_id in TKFX_SIGFOX_DEVICES_ID):
        trackfox_asset = TKFX_SIGFOX_DEVICES_ASSET[TKFX_SIGFOX_DEVICES_ID.index(device_id)]
    return trackfox_asset

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
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LAST_STARTUP_TIMESTAMP : influxdb_timestamp,
                INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_TRACKFOX_ASSET : TKFX_GetAsset(influxdb_device_id)
            }
        }]
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "TKFX ID=" + str(device_id) + " * Start up.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_TKFX_DATABASE_NAME, json_body)
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
            "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_MCU_TEMPERATURE : mcu_temperature,
                INFLUX_DB_FIELD_SOURCE_VOLTAGE : source_voltage,
                INFLUX_DB_FIELD_SUPERCAP_VOLTAGE : supercap_voltage,
                INFLUX_DB_FIELD_MCU_VOLTAGE : mcu_voltage,
                INFLUX_DB_FIELD_STATUS_BYTE : status_byte,
                INFLUX_DB_FIELD_LAST_MONITORING_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_TRACKFOX_ASSET : TKFX_GetAsset(influxdb_device_id)
            }
        },
        {
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_TRACKFOX_ASSET : TKFX_GetAsset(influxdb_device_id)
            }
        }]
        # Manage error values.
        temperature = "error"
        if (int(data[0:2], 16) != TKFX_TEMPERATURE_ERROR):
            temperature_raw = int(data[0:2], 16)
            temperature = temperature_raw & 0x7F
            if ((temperature_raw & 0x80) != 0):
                temperature = (-1) * temperature
            json_body[0]["fields"][INFLUX_DB_FIELD_TEMPERATURE] = temperature
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "TKFX ID=" + str(device_id) + " * Monitoring data * Vsrc=" + str(source_voltage) + "mV, Vcap=" + str(supercap_voltage) + "mV, Vmcu=" + str(mcu_voltage) + "mV, T=" + str(temperature) + "dC, Tmcu=" + str(mcu_temperature) + "dC, Status=" + str(status_byte) + ".")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_TKFX_DATABASE_NAME, json_body)
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
            "measurement": INFLUX_DB_MEASUREMENT_GEOLOC,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LATITUDE : latitude,
                INFLUX_DB_FIELD_LONGITUDE : longitude,
                INFLUX_DB_FIELD_ALTITUDE : altitude,
                INFLUX_DB_FIELD_GPS_FIX_DURATION : gps_fix_duration,
                INFLUX_DB_FIELD_LAST_GEOLOC_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_TRACKFOX_ASSET : TKFX_GetAsset(influxdb_device_id)
            }
        },
        {
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_TRACKFOX_ASSET : TKFX_GetAsset(influxdb_device_id)
            }
        }]
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "TKFX ID=" + str(device_id) + " * Geoloc data * Lat=" + str(latitude) + ", Long=" + str(longitude) + ", Alt=" + str(altitude) + "m, GpsFixDur=" + str(gps_fix_duration) + "s.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_TKFX_DATABASE_NAME, json_body)
    # Geolocation timeout frame.
    if len(data) == (2 * TKFX_SIGFOX_GEOLOCATION_TIMEOUT_FRAME_LENGTH_BYTES):
        gps_timeout_duration = int(data[0:2], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUX_DB_MEASUREMENT_GEOLOC,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_GPS_TIMEOUT_DURATION : gps_timeout_duration
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_TRACKFOX_ASSET : TKFX_GetAsset(influxdb_device_id)
            }
        },
        {
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_TRACKFOX_ASSET : TKFX_GetAsset(influxdb_device_id)
            }
        }]
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "TKFX ID=" + str(device_id) + " * Geoloc timeout * GpsFixDur=" + str(gps_fix_duration) + "s.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_TKFX_DATABASE_NAME, json_body)