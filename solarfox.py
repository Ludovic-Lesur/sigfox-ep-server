from __future__ import print_function

from influx_db import *
from log import *

### MACROS ###

SLFX_SIGFOX_DEVICES_ID = ["44AA", "44D2", "4505", "45A0", "45AB"]
SLFX_SIGFOX_DEVICES_SITE = ["INSA Toulouse", "Le Vigan", "Unknown", "Unknown", "Unknown"]

SLFX_SIGFOX_MONITORING_DATA_FRAME_LENGTH_BYTES = 10

### FUNCTIONS ###

# Function performing Sigfox ID to SolarFox site conversion.
def SLFX_GetSite(device_id):
    # Default is unknown.
    solarfox_site = "Unknown site (" + str(device_id) + ")"
    if (device_id in SLFX_SIGFOX_DEVICES_ID):
        solarfox_site = SLFX_SIGFOX_DEVICES_SITE[SLFX_SIGFOX_DEVICES_ID.index(device_id)]
    return solarfox_site

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
            "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_SOLAR_CELL_VOLTAGE : solar_cell_voltage,
                INFLUX_DB_FIELD_OUTPUT_VOLTAGE : output_voltage,
                INFLUX_DB_FIELD_OUTPUT_CURRENT : output_current,
                INFLUX_DB_FIELD_OUTPUT_POWER : output_power,
                INFLUX_DB_FIELD_MCU_VOLTAGE : mcu_voltage,
                INFLUX_DB_FIELD_MCU_TEMPERATURE : mcu_temperature,
                INFLUX_DB_FIELD_LAST_MONITORING_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_SOLARFOX_SITE : SLFX_GetSite(influxdb_device_id)
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
                INFLUX_DB_TAG_SOLARFOX_SITE : SLFX_GetSite(influxdb_device_id)
            }
        }]
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "SLFX ID=" + str(device_id) + " * Monitoring data * Vin=" + str(solar_cell_voltage) + "mV, Vout=" + str(output_voltage) + "mV, Iout=" + str(output_current) + "uA, Vmcu=" + str(mcu_voltage) + "mV, Tmcu=" + str(mcu_temperature) + "dC.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_SLFX_DATABASE_NAME, json_body)