from __future__ import print_function

from influx_db import *
from log import *

### MACROS ###

SYNCFX_SIGFOX_DEVICES_ID = ["4016", "405B", "40A7", "4151", "41CE"]
SYNCFX_SIGFOX_DEVICES_SITE = ["Proto Labo", "Labege", "Prat Albis", "Unknown", "Unknown"]

SYNCFX_SIGFOX_OOB_DATA = "OOB"
SYNCFX_SIGFOX_SYNCHRO_FRAME_LENGTH_BYTES = 6
SYNCFX_SIGFOX_MONITORING_FRAME_LENGTH_BYTES = 7
SYNCFX_SIGFOX_GEOLOCATION_FRAME_LENGTH_BYTES = 11
SYNCFX_SIGFOX_GEOLOCATION_TIMEOUT_FRAME_LENGTH_BYTES = 1

### FUNCTIONS ###

# Function performing Sigfox ID to SynchroFox site conversion.
def SYNCFX_GetSite(device_id):
    # Default is unknown.
    synchrofox_site = "Unknown site (" + str(device_id) + ")"
    if (device_id in SYNCFX_SIGFOX_DEVICES_ID):
        synchrofox_site = SYNCFX_SIGFOX_DEVICES_SITE[SYNCFX_SIGFOX_DEVICES_ID.index(device_id)]
    return synchrofox_site

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
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LAST_STARTUP_TIMESTAMP : influxdb_timestamp,
                INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
            }
        }]
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "SYNCFX ID=" + str(device_id) + " * Start up.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_SYNCFX_DATABASE_NAME, json_body)
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
            "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_SOLAR_CELL_VOLTAGE : solar_cell_voltage,
                INFLUX_DB_FIELD_BATTERY_VOLTAGE : battery_voltage,
                INFLUX_DB_FIELD_MCU_VOLTAGE : mcu_voltage,
                INFLUX_DB_FIELD_GPSDO_LOCK_DURATION : gpsdo_lock_duration,
                INFLUX_DB_FIELD_MCU_TEMPERATURE : mcu_temperature,
                INFLUX_DB_FIELD_STATUS_BYTE : status_byte,
                INFLUX_DB_FIELD_LAST_MONITORING_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
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
                INFLUX_DB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
            }
        }]
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "SYNCFX ID=" + str(device_id) + " * Monitoring data * Vsrc=" + str(solar_cell_voltage) + "mV, Vbatt=" + str(battery_voltage) + "mV, Vmcu=" + str(mcu_voltage) + "mV, GpsdoLockDur=" + str(gpsdo_lock_duration) + "s, Tmcu=" + str(mcu_temperature) + "dC, Status=" + str(status_byte) + ".")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_SYNCFX_DATABASE_NAME, json_body)
    # Synchronization frame.
    if len(data) == (2 * SYNCFX_SIGFOX_SYNCHRO_FRAME_LENGTH_BYTES):
        hours = (int(data[0:2], 16) >> 3) & 0x1F
        minutes = ((int(data[0:2], 16) << 3) & 0x38) + ((int(data[2:4], 16) >> 5) & 0x07)
        seconds = ((int(data[2:4], 16) << 1) & 0x3E) + ((int(data[4:6], 16) >> 7) & 0x01)
        frequency = ((int(data[4:6], 16) << 24) & 0x7F000000) + ((int(data[6:8], 16) << 16) & 0x00FF0000) + ((int(data[8:10], 16) << 8) & 0x0000FF00) + ((int(data[10:12], 16) << 0) & 0x000000FF)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUX_DB_MEASUREMENT_SYNCHRO,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_HOURS : hours,
                INFLUX_DB_FIELD_MINUTES : minutes,
                INFLUX_DB_FIELD_SECONDS : seconds,
                INFLUX_DB_FIELD_FREQUENCY : frequency,
                INFLUX_DB_FIELD_LAST_SYNCHRO_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
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
                INFLUX_DB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
            }
        }]
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "SYNCFX ID=" + str(device_id) + " * Synchro data * H=" + str(hours) + "h, M=" + str(minutes) + "m, S=" + str(seconds) + "h, f=" + str(frequency) + "Hz.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_SYNCFX_DATABASE_NAME, json_body)
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
                INFLUX_DB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
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
                INFLUX_DB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
            }
        }]
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "SYNCFX ID=" + str(device_id) + " * Geoloc data * Lat=" + str(latitude) + ", Long=" + str(longitude) + ", Alt=" + str(altitude) + "m, GpsFixDur=" + str(gps_fix_duration) + "s.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_SYNCFX_DATABASE_NAME, json_body)
    # Geolocation timeout frame.
    if len(data) == (2 * SYNCFX_SIGFOX_GEOLOCATION_TIMEOUT_FRAME_LENGTH_BYTES):
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
                INFLUX_DB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
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
                INFLUX_DB_TAG_SYNCHROFOX_SITE : SYNCFX_GetSite(influxdb_device_id)
            }
        }]
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "SYNCFX ID=" + str(device_id) + " * Geoloc timeout * GpsFixDur=" + str(gps_fix_duration) + "s.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_SYNCFX_DATABASE_NAME, json_body)