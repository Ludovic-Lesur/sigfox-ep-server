from __future__ import print_function

from influx_db import *
from log import *

### MACROS ###

# Devices ID and associated informations.
ATXFX_SIGFOX_DEVICES_ID = ["868E", "869E", "87A5", "87EE", "87F1", "87F3", "87F4", "87F6", "87FC", "8922"]
ATXFX_SIGFOX_DEVICES_RACK = ["1", "1", "1", "1", "1", "2", "2", "2", "2", "2"]
ATXFX_SIGFOX_DEVICES_FRONT_END = ["+3.3V", "+5.0V", "+12.0V", "Adjustable", "Battery charger", "+3.3V", "+5.0V", "+12.0V", "Adjustable", "Battery charger"]

ATXFX_SIGFOX_START_STOP_FRAME_LENGTH_BYTES = 1
ATXFX_SIGFOX_MONITORING_FRAME_LENGTH_BYTES = 8

ATXFX_OUTPUT_CURRENT_ERROR = 0xFFFFFF

### FUNCTIONS ###

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
                "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
                "time": influxdb_timestamp,
                "fields": {
                    INFLUX_DB_FIELD_LAST_SHUTDOWN_TIMESTAMP : influxdb_timestamp,
                    INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp,
                    INFLUX_DB_FIELD_STATE : status_raw
                },
                "tags": {
                    INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                    INFLUX_DB_TAG_ATXFOX_RACK : ATXFX_GetRack(influxdb_device_id),
                    INFLUX_DB_TAG_ATXFOX_FRONT_END : ATXFX_GetFrontEnd(influxdb_device_id)
                }
            }]
            if LOG == True:
                print(LOG_GetCurrentTimestamp() + "ATXFX ID=" + str(device_id) + " * Shutdown.")
            # Fill data base.
            INFLUX_DB_WriteData(INFLUX_DB_ATXFX_DATABASE_NAME, json_body)
        if (status_raw == 0x01):
            # Create JSON object.
            json_body = [
            {
                "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
                "time": influxdb_timestamp,
                "fields": {
                    INFLUX_DB_FIELD_LAST_STARTUP_TIMESTAMP : influxdb_timestamp,
                    INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp,
                    INFLUX_DB_FIELD_STATE : status_raw
                },
                "tags": {
                    INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                    INFLUX_DB_TAG_ATXFOX_RACK : ATXFX_GetRack(influxdb_device_id),
                    INFLUX_DB_TAG_ATXFOX_FRONT_END : ATXFX_GetFrontEnd(influxdb_device_id)
                }
            }]
            if LOG == True:
                print(LOG_GetCurrentTimestamp() + "ATXFX ID=" + str(device_id) + " * Start-up.")
            # Fill data base.
            INFLUX_DB_WriteData(INFLUX_DB_ATXFX_DATABASE_NAME, json_body)
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
            "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_OUTPUT_VOLTAGE : output_voltage,
                INFLUX_DB_FIELD_CURRENT_SENSE_RANGE : current_sense_range,
                INFLUX_DB_FIELD_MCU_VOLTAGE : mcu_voltage,
                INFLUX_DB_FIELD_MCU_TEMPERATURE : mcu_temperature,
                INFLUX_DB_FIELD_LAST_MONITORING_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_ATXFOX_RACK : ATXFX_GetRack(influxdb_device_id),
                INFLUX_DB_TAG_ATXFOX_FRONT_END : ATXFX_GetFrontEnd(influxdb_device_id)
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
                INFLUX_DB_TAG_ATXFOX_RACK : ATXFX_GetRack(influxdb_device_id),
                INFLUX_DB_TAG_ATXFOX_FRONT_END : ATXFX_GetFrontEnd(influxdb_device_id)
            }
        }]
        # Manage error values.
        output_current = "unknown"
        output_power = "unknown"
        if (int(data[4:10], 16) != ATXFX_OUTPUT_CURRENT_ERROR):
            output_current = int(data[4:10], 16)
            json_body[0]["fields"][INFLUX_DB_FIELD_OUTPUT_CURRENT] = output_current
            # Compute output power in nW (uA * mV).
            output_power = (output_voltage * output_current)
            json_body[0]["fields"][INFLUX_DB_FIELD_OUTPUT_POWER] = output_power
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "ATXFX ID=" + str(device_id) + " * Monitoring data * Vatx=" + str(output_voltage) + "mV, TrcsRange=" + str(current_sense_range) + ", Iatx=" + str(output_current) + "uA, Patx=" + str(output_power) + "nW, Vmcu=" + str(mcu_voltage) + "mV, Tmcu=" + str(mcu_temperature) + "dC.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_ATXFX_DATABASE_NAME, json_body)