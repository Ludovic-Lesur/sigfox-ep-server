from __future__ import print_function

from common import *
from influx_db import *
from log import *

### LOCAL MACROS ###

# TrackFox tags.
__TRACKFOX_ASSET = ["Car", "Bike", "Hiking", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"]
# Sigfox frames length.
__TRACKFOX_MONITORING_DATA_LENGTH_BYTES = 9
__TRACKFOX_ERROR_STACK_DATA_LENGTH_BYTES = 12

### PUBLIC MACROS ###

# TrackFox EP-IDs.
TRACKFOX_EP_ID = ["4257", "428D", "42F1", "43B9", "43CD", "44AA", "44D2", "4505", "45A0", "45AB"]

### LOCAL FUNCTIONS ###

# Function performing Sigfox ID to TrackFox asset conversion.
def __TRACKFOX_get_asset(sigfox_ep_id):
    # Default is unknown.
    asset = "unknown"
    if (sigfox_ep_id in TRACKFOX_EP_ID):
        asset = __TRACKFOX_ASSET[TRACKFOX_EP_ID.index(sigfox_ep_id)]
    return asset

# Function adding the specific TrackFox tags.
def __TRACKFOX_add_tags(json_body, sigfox_ep_id) :
    for idx in range(len(json_body)) :
        json_body[idx]["tags"] = {
            INFLUX_DB_TAG_SIGFOX_EP_ID : sigfox_ep_id,
            INFLUX_DB_TAG_ASSET : __TRACKFOX_get_asset(sigfox_ep_id)
        }

### PUBLIC FUNCTIONS ###

# Function for parsing TrackFox device payload and fill database.
def TRACKFOX_fill_data_base(timestamp, sigfox_ep_id, data):
    # Init JSON object.
    json_body = []
    # Startup frame.
    if (len(data) == (2 * COMMON_STARTUP_DATA_LENGTH_BYTES)) :
        # Create JSON object.
        result = COMMON_create_json_startup_data(timestamp, data)
        json_body = result[0]
        log_data = result[1]
        LOG_print_timestamp("[TRACKFOX] * Startup data * asset=" + __TRACKFOX_get_asset(sigfox_ep_id) + " " + log_data)
    # Geolocation frame.
    if (len(data) == (2 * COMMON_GEOLOC_DATA_LENGTH_BYTES)) :
        # Create JSON object.
        result = COMMON_create_json_geoloc_data(timestamp, data)
        json_body = result[0]
        log_data = result[1]
        LOG_print_timestamp("[TRACKFOX] * Geoloc data * asset=" + __TRACKFOX_get_asset(sigfox_ep_id) + " " + log_data)
    # Geolocation timeout frame.
    if (len(data) == (2 * COMMON_GEOLOC_TIMEOUT_DATA_LENGTH_BYTES)) :
        # Create JSON object.
        result = COMMON_create_json_geoloc_timeout_data(timestamp, data)
        json_body = result[0]
        log_data = result[1]
        LOG_print_timestamp("[TRACKFOX] * Geoloc timeout * asset=" + __TRACKFOX_get_asset(sigfox_ep_id) + " " + log_data)
    # Error stack frame.
    if (len(data) == (2 * __TRACKFOX_ERROR_STACK_DATA_LENGTH_BYTES)) :
        # Create JSON object.
        result = COMMON_create_json_error_stack_data(timestamp, data, (__TRACKFOX_ERROR_STACK_DATA_LENGTH_BYTES / 2))
        json_body = result[0]
        log_data = result[1]
        LOG_print_timestamp("[TRACKFOX] * Error stack * asset=" + __TRACKFOX_get_asset(sigfox_ep_id) + " " + log_data)
    # Monitoring frame.
    if (len(data) == (2 * __TRACKFOX_MONITORING_DATA_LENGTH_BYTES)) :
        # Parse fields.
        tamb_degrees = COMMON_one_complement_to_value(int(data[0:2], 16), 7) if (int(data[0:2], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
        hamb_percent = int(data[2:4], 16) if (int(data[2:4], 16) != COMMON_ERROR_VALUE_HUMIDITY) else COMMON_ERROR_DATA
        tmcu_degrees = COMMON_one_complement_to_value(int(data[4:6], 16), 7) if (int(data[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
        vsrc_mv = int(data[6:10], 16) if (int(data[6:10], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
        vcap_mv = int(data[10:13], 16) if (int(data[10:13], 16) != COMMON_ERROR_VALUE_ANALOG_12BITS) else COMMON_ERROR_DATA
        vmcu_mv = int(data[13:16], 16) if (int(data[13:16], 16) != COMMON_ERROR_VALUE_ANALOG_12BITS) else COMMON_ERROR_DATA
        status = int(data[16:18], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
            "time": timestamp,
            "fields": {
                INFLUX_DB_FIELD_STATUS : status,
                INFLUX_DB_FIELD_TIME_LAST_MONITORING_DATA : timestamp
            },
        },
        {
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "time": timestamp,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
            },
        }]
        # Add valid fields to JSON.
        if (tamb_degrees != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_TAMB] = tamb_degrees
        if (hamb_percent != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_HAMB] = hamb_percent
        if (tmcu_degrees != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
        if (vsrc_mv != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_VSRC] = vsrc_mv
        if (vcap_mv != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_VCAP] = vcap_mv
        if (vmcu_mv != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
        LOG_print_timestamp("[TRACKFOX] * Monitoring data * asset=" + __TRACKFOX_get_asset(sigfox_ep_id) + " tamb=" + str(tamb_degrees) + "dC hamb=" + str(hamb_percent) + "% tmcu=" + str(tmcu_degrees) + "dC vsrc=" + str(vsrc_mv) + "mV vcap=" + str(vcap_mv) + "mV vmcu=" + str(vmcu_mv) + "mV status=" + hex(status))
    # Fill data base.
    if (len(json_body) > 0) :
        __TRACKFOX_add_tags(json_body, sigfox_ep_id)
        INFLUX_DB_write_data(INFLUX_DB_DATABASE_TRACKFOX, json_body)
    else :
        LOG_print_timestamp("[TRACKFOX] * Invalid frame")
          