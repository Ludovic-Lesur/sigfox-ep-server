from __future__ import print_function

from influx_db import *
from log import *

### PUBLIC MACROS ###

COMMON_OOB_DATA = "OOB"
COMMON_UL_PAYLOAD_STARTUP_SIZE = 8
COMMON_UL_PAYLOAD_GEOLOC_SIZE = 11
COMMON_UL_PAYLOAD_GEOLOC_TIMEOUT_SIZE_OLD = 1
COMMON_UL_PAYLOAD_GEOLOC_TIMEOUT_SIZE = 3
# Error values.
COMMON_ERROR_DATA = "error"
COMMON_ERROR_VALUE_ANALOG_12BITS = 0xFFF
COMMON_ERROR_VALUE_ANALOG_15BITS = 0x7FFF
COMMON_ERROR_VALUE_ANALOG_16BITS = 0xFFFF
COMMON_ERROR_VALUE_ANALOG_23BITS = 0x7FFFFF
COMMON_ERROR_VALUE_ANALOG_24BITS = 0xFFFFFF
COMMON_ERROR_VALUE_LIGHT = 0xFF
COMMON_ERROR_VALUE_TEMPERATURE = 0x7F
COMMON_ERROR_VALUE_HUMIDITY = 0xFF
COMMON_ERROR_VALUE_UV_INDEX = 0xFF
COMMON_ERROR_VALUE_PRESSURE = 0xFFFF
COMMON_ERROR_VALUE_WIND = 0xFF
COMMON_ERROR_VALUE_RAIN = 0xFF
COMMON_ERROR_VALUE_VOLTAGE = 0xFFFF
COMMON_ERROR_VALUE_CURRENT = 0xFFFF
COMMON_ERROR_VALUE_ELECTRICAL_POWER = 0x7FFF
COMMON_ERROR_VALUE_POWER_FACTOR = 0x7F
COMMON_ERROR_VALUE_FREQUENCY_16BITS = 0xFFFF

### PUBLIC FUNCTIONS ###

# Function which computes the real value of a one complement number.
def COMMON_one_complement_to_value(one_complement_data, sign_bit_position) :
    value = (one_complement_data & 0x7F);
    if ((one_complement_data & (1 << sign_bit_position)) != 0) :
        value = (-1) * value
    return value

# Function for parsing startup frame.
def COMMON_create_json_startup_data(timestamp, ul_payload) :
    # Parse fields.
    reset_flags = int(ul_payload[0:2], 16)
    version_major = int(ul_payload[2:4], 16)
    version_minor = int(ul_payload[4:6], 16)
    version_commit_index = int(ul_payload[6:8], 16)
    version_commit_id = int(ul_payload[8:15], 16)
    version_dirty_flag = int(ul_payload[15:16], 16)
    version = "SW" + str(version_major) + "." + str(version_minor) + "." + str(version_commit_index)
    if (version_dirty_flag != 0) :
        version = version + ".d"
    # Create JSON object.
    json_body = [
    {
        "time" : timestamp,
        "measurement" : INFLUX_DB_MEASUREMENT_METADATA,
        "fields" : {
            INFLUX_DB_FIELD_TIME_LAST_STARTUP : timestamp,
            INFLUX_DB_FIELD_RESET_FLAGS : reset_flags,
            INFLUX_DB_FIELD_VERSION : version,
            INFLUX_DB_FIELD_VERSION_MAJOR : version_major,
            INFLUX_DB_FIELD_VERSION_MINOR : version_minor,
            INFLUX_DB_FIELD_VERSION_COMMIT_INDEX : version_commit_index,
            INFLUX_DB_FIELD_VERSION_COMMIT_ID : version_commit_id,
            INFLUX_DB_FIELD_VERSION_DIRTY_FLAG : version_dirty_flag,
            INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
        }
    }]
    log_data = "reset_flags=" + hex(reset_flags) + " version=" + version + " version_commit_id=" + hex(version_commit_id)
    return json_body, log_data

# Function for parsing geoloc frame.
def COMMON_create_json_geoloc_data(timestamp, ul_payload) :
    # Parse fields.
    latitude_degrees = int(ul_payload[0:2], 16)
    latitude_minutes = (int(ul_payload[2:4], 16) >> 2) & 0x3F
    latitude_seconds = ((((int(ul_payload[2:8], 16) & 0x03FFFE) >> 1) & 0x01FFFF) / (100000.0)) * 60.0
    latitude_north = int(ul_payload[6:8], 16) & 0x01
    latitude = latitude_degrees + (latitude_minutes / 60.0) + (latitude_seconds / 3600.0)
    if (latitude_north == 0):
        latitude = -latitude
    longitude_degrees = int(ul_payload[8:10], 16)
    longitude_minutes = (int(ul_payload[10:12], 16) >> 2) & 0x3F
    longitude_seconds = ((((int(ul_payload[10:16], 16) & 0x03FFFE) >> 1) & 0x01FFFF) / (100000.0)) * 60.0
    longitude_east = int(ul_payload[14:16], 16) & 0x01
    longitude = longitude_degrees + (longitude_minutes / 60.0) + (longitude_seconds / 3600.0)
    if (longitude_east == 0):
        longitude = -longitude
    altitude = int(ul_payload[16:20], 16)
    gps_fix_duration = int(ul_payload[20:22], 16)
    # Create JSON object.
    json_body = [
    {
        "time" : timestamp,
        "measurement" : INFLUX_DB_MEASUREMENT_GEOLOC,
        "fields" : {
            INFLUX_DB_FIELD_TIME_LAST_GEOLOC_DATA : timestamp,
            INFLUX_DB_FIELD_LATITUDE : latitude,
            INFLUX_DB_FIELD_LONGITUDE : longitude,
            INFLUX_DB_FIELD_ALTITUDE : altitude,
            INFLUX_DB_FIELD_GPS_FIX_DURATION : gps_fix_duration
        },
    },
    {
        "time" : timestamp,
        "measurement": INFLUX_DB_MEASUREMENT_METADATA,
        "fields": {
            INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
        },
    }]
    log_data = "latitude=" + str(latitude) + ", longitude=" + str(longitude) + ", altitude=" + str(altitude) + "m, gps_fix_duration=" + str(gps_fix_duration) + "s"
    return json_body, log_data
    
# Function for parsing geoloc timeout frame.
def COMMON_create_json_geoloc_timeout_data(timestamp, ul_payload, ul_payload_size) :
    # Old format.
    if (ul_payload_size == COMMON_UL_PAYLOAD_GEOLOC_TIMEOUT_SIZE_OLD) :
        # Parse field
        gps_timeout_duration = int(ul_payload[0:2], 16)
        # Create JSON object.
        json_body = [
        {
            "time" : timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_GEOLOC,
            "fields": {
                INFLUX_DB_FIELD_GPS_TIMEOUT_DURATION : gps_timeout_duration
            },
        },
        {
            "time" : timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_METADATA,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp,
            },
        }]
        log_data = "gps_timeout_duration=" + str(gps_timeout_duration) + "s."
    # New format.
    elif (ul_payload_size == COMMON_UL_PAYLOAD_GEOLOC_TIMEOUT_SIZE) :
        # Parse fields
        gps_timeout_error_code = int(ul_payload[0:4], 16)
        gps_timeout_duration = int(ul_payload[4:6], 16)
        # Create JSON object.
        json_body = [
        {
            "time" : timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_GEOLOC,
            "fields": {
                INFLUX_DB_FIELD_GPS_TIMEOUT_DURATION : gps_timeout_duration
            },
        },
        {
            "time" : timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_METADATA,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp,
                INFLUX_DB_FIELD_ERROR : gps_timeout_error_code
            },
        }]
        log_data = "gps_timeout_error_code=" + hex(gps_timeout_error_code) + " gps_timeout_duration=" + str(gps_timeout_duration) + "s."
    return json_body, log_data
    
# Function for parsing error stack frame.
def COMMON_create_json_error_stack_data(timestamp, ul_payload, number_of_errors) :
    # Create JSON object.
    json_body = list()
    # Parse field.
    log_data = ""
    for idx in range(0, number_of_errors):
        error = int(ul_payload[(idx * 4) : ((idx * 4) + 4)], 16)
        # Store error code if not null.
        if (error != 0):
            # Create JSON object.
            json_sub_body = {
                "time": (timestamp + idx),
                "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                "fields": {
                    INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp,
                    INFLUX_DB_FIELD_ERROR : error
                }
            }
            json_body.append(json_sub_body)
            log_data = log_data + "code_" + str(idx) + "=" + hex(error) + " "
    return json_body, log_data




