from __future__ import print_function

from influx_db import *
from log import *

### MACROS ###

SENSIT_SIGFOX_DEVICES_ID = ["1C8330", "20F815", "86BD75", "B437B2", "B4384E"]
SENSIT_SIGFOX_DEVICES_SITE = ["Sigfox (bureau)", "Sigfox (cagibi)", "Prat Albis", "Le Vigan (maison)", "Le Vigan (atelier)"]
SENSIT_SIGFOX_DEVICES_VERSION = ["V2", "V2", "V2", "V3", "V3"]

SENSIT_SIGFOX_DATA_FRAME_LENGTH_BYTES = 4
SENSIT_SIGFOX_CONFIGURATION_FRAME_LENGTH_BYTES = 12

### FUNCTIONS ###

# Function performing Sigfox ID to Sensit site conversion.
def SENSIT_GetSite(device_id):
    # Default is unknown.
    sensit_site = "Unknown site (" + str(device_id) + ")"
    if (device_id in SENSIT_SIGFOX_DEVICES_ID):
        sensit_site = SENSIT_SIGFOX_DEVICES_SITE[SENSIT_SIGFOX_DEVICES_ID.index(device_id)]
    return sensit_site

# Function performing Sigfox ID to Sensit version conversion.
def SENSIT_GetVersion(device_id):
    # Default is unknown.
    sensit_version = "Unknown version"
    if (device_id in SENSIT_SIGFOX_DEVICES_ID):
        sensit_version = SENSIT_SIGFOX_DEVICES_VERSION[SENSIT_SIGFOX_DEVICES_ID.index(device_id)]
    return sensit_version

# Function for parsing Sensit device payload and fill database.      
def SENSIT_FillDataBase(timestamp, device_id, data):
    # Format parameters.
    influxdb_device_id = device_id.upper()
    influxdb_timestamp = int(timestamp)
    sensit_version = SENSIT_GetVersion(device_id)
    # Monitoring frame.
    if (len(data) == (2 * SENSIT_SIGFOX_DATA_FRAME_LENGTH_BYTES)) or (len(data) == (2 * SENSIT_SIGFOX_CONFIGURATION_FRAME_LENGTH_BYTES)):
        # Parse fields.
        if (sensit_version.find("V3") >= 0):
            battery_voltage = (((int(data[0:2], 16) >> 3) & 0x1F) * 50) + 2700
            mode = ((int(data[2:4], 16) >> 3) & 0x0F)
        else:
            battery_voltage = ((((int(data[0:2], 16) >> 3) & 0x10) + (int(data[2:4], 16) & 0x0F)) * 50) + 2700
            mode = (int(data[0:2], 16) & 0x07)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_BATTERY_VOLTAGE : battery_voltage,
                INFLUX_DB_FIELD_MODE : mode
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_SENSIT_SITE : SENSIT_GetSite(influxdb_device_id)
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
                INFLUX_DB_TAG_SENSIT_SITE : SENSIT_GetSite(influxdb_device_id)
            }
        }]
        temperature = "error"
        humidity = "error"
        if (mode == 0x01):
            if (sensit_version.find("V3") >= 0):
                temperature = ((((int(data[2:4], 16) << 8) & 0x300) + (int(data[4:6], 16))) - 200.0) / (8.0)
            else:
                temperature = ((((int(data[2:4], 16) << 2) & 0x3C0) + (int(data[4:6], 16) & 0x3F)) - 200.0) / (8.0)
            humidity = (int(data[6:8], 16)) / (2.0)
            json_body[0]["fields"][INFLUX_DB_FIELD_TEMPERATURE] = temperature
            json_body[0]["fields"][INFLUX_DB_FIELD_HUMIDITY] = humidity
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "SENSIT ID=" + str(device_id) + " * Monitoring data * Vbatt=" + str(battery_voltage), "mV, Mode=" + str(mode) + ", T=" + str(temperature) + "dC, H=" + str(humidity) + "%.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_SENSIT_DATABASE_NAME, json_body)