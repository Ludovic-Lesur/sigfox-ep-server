from __future__ import print_function

from database.influx_db import *
from log import *
from ep.common import *

### LOCAL MACROS ###

# TrackFox tags.
__TRACKFOX_ASSET = ["Car", "Bike", "Hiking", "Hiking_spare", "Proto_HW1.1"]
# Sigfox frames length.
__TRACKFOX_UL_PAYLOAD_MONITORING_SIZE = 7
__TRACKFOX_UL_PAYLOAD_ERROR_STACK_SIZE = 12

### PUBLIC MACROS ###

# TrackFox EP-IDs.
TRACKFOX_EP_ID_LIST = ["4257", "428D", "42F1", "43B9", "43CD"]

### LOCAL FUNCTIONS ###

# Function performing Sigfox ID to TrackFox asset conversion.
def __TRACKFOX_get_asset(sigfox_ep_id):
    # Default is unknown.
    asset = "unknown"
    if (sigfox_ep_id in TRACKFOX_EP_ID_LIST):
        asset = __TRACKFOX_ASSET[TRACKFOX_EP_ID_LIST.index(sigfox_ep_id)]
    return asset

### PUBLIC FUNCTIONS ###

# Function adding the specific TrackFox tags.
def TRACKFOX_add_ep_tag(json_ul_data, sigfox_ep_id):
    for idx in range(len(json_ul_data)):
        if ("tags" in json_ul_data[idx]):
            json_ul_data[idx]["tags"][INFLUX_DB_TAG_SIGFOX_EP_ID] = sigfox_ep_id
            json_ul_data[idx]["tags"][INFLUX_DB_TAG_ASSET] = __TRACKFOX_get_asset(sigfox_ep_id)
        else:
            json_ul_data[idx]["tags"] = {
                INFLUX_DB_TAG_SIGFOX_EP_ID: sigfox_ep_id,
                INFLUX_DB_TAG_ASSET: __TRACKFOX_get_asset(sigfox_ep_id)
            }

# Function for parsing TrackFox device payload and fill database.
def TRACKFOX_parse_ul_payload(timestamp, sigfox_ep_id, ul_payload):
    # Init JSON object.
    json_ul_data = []
    # Startup frame.
    if (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_STARTUP_SIZE)):
        # Create JSON object.
        result = COMMON_create_json_startup_data(timestamp, ul_payload)
        json_ul_data = result[0]
        log_data = result[1]
        LOG_print("[TRACKFOX] * Startup data * asset=" + __TRACKFOX_get_asset(sigfox_ep_id) + " " + log_data)
    # Geolocation frame.
    elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_GEOLOC_SIZE)):
        # Create JSON object.
        result = COMMON_create_json_geoloc_data(timestamp, ul_payload)
        json_ul_data = result[0]
        log_data = result[1]
        LOG_print("[TRACKFOX] * Geoloc data * asset=" + __TRACKFOX_get_asset(sigfox_ep_id) + " " + log_data)
    # Geolocation timeout frame V2.
    elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_GEOLOC_TIMEOUT_SIZE_V2)):
        # Create JSON object.
        result = COMMON_create_json_geoloc_timeout_data(timestamp, ul_payload, COMMON_UL_PAYLOAD_GEOLOC_TIMEOUT_SIZE_V2)
        json_ul_data = result[0]
        log_data = result[1]
        LOG_print("[TRACKFOX] * Geoloc timeout V2 * asset=" + __TRACKFOX_get_asset(sigfox_ep_id) + " " + log_data)
    # Geolocation timeout frame V3.
    elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_GEOLOC_TIMEOUT_SIZE_V3)):
        # Create JSON object.
        result = COMMON_create_json_geoloc_timeout_data(timestamp, ul_payload, COMMON_UL_PAYLOAD_GEOLOC_TIMEOUT_SIZE_V3)
        json_ul_data = result[0]
        log_data = result[1]
        LOG_print("[TRACKFOX] * Geoloc timeout V3 * asset=" + __TRACKFOX_get_asset(sigfox_ep_id) + " " + log_data)
    # Error stack frame.
    elif (len(ul_payload) == (2 * __TRACKFOX_UL_PAYLOAD_ERROR_STACK_SIZE)):
        # Create JSON object.
        result = COMMON_create_json_error_stack_data(timestamp, ul_payload, (__TRACKFOX_UL_PAYLOAD_ERROR_STACK_SIZE // 2))
        json_ul_data = result[0]
        log_data = result[1]
        LOG_print("[TRACKFOX] * Error stack * asset=" + __TRACKFOX_get_asset(sigfox_ep_id) + " " + log_data)
    # Monitoring frame.
    elif (len(ul_payload) == (2 * __TRACKFOX_UL_PAYLOAD_MONITORING_SIZE)):
        # Parse fields.
        tamb_degrees = COMMON_one_complement_to_value(int(ul_payload[0:2], 16), 7) if (int(ul_payload[0:2], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
        hamb_percent = int(ul_payload[2:4], 16) if (int(ul_payload[2:4], 16) != COMMON_ERROR_VALUE_HUMIDITY) else COMMON_ERROR_DATA
        vsrc_mv = int(ul_payload[4:8], 16) if (int(ul_payload[4:8], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
        vcap_mv = int(ul_payload[8:12], 16) if (int(ul_payload[8:12], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
        status = int(ul_payload[12:14], 16)
        # Create JSON object.
        json_ul_data = [
        {
            "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
            "time": timestamp,
            "fields": {
                INFLUX_DB_FIELD_STATUS: status,
                INFLUX_DB_FIELD_TIME_LAST_MONITORING_DATA: timestamp
            },
        },
        {
            "measurement": INFLUX_DB_MEASUREMENT_METADATA,
            "time": timestamp,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION: timestamp
            },
        }]
        # Add valid fields to JSON.
        if (tamb_degrees != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_TAMB] = tamb_degrees
        if (hamb_percent != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_HAMB] = hamb_percent
        if (vsrc_mv != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_VSRC] = vsrc_mv
        if (vcap_mv != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_VCAP] = vcap_mv
        LOG_print("[TRACKFOX] * Monitoring data * asset=" + __TRACKFOX_get_asset(sigfox_ep_id) +
                  " tamb=" + str(tamb_degrees) + "dC hamb=" + str(hamb_percent) + "% vsrc=" + str(vsrc_mv) + "mV vcap=" + str(vcap_mv) + "mV status=" + hex(status))
    else:
        LOG_print("[TRACKFOX] * Invalid UL payload")
    return json_ul_data

# Returns the default downlink payload to sent back to the device.
def TRACKFOX_get_default_dl_payload(sigfox_ep_id):
    # Local variables.
    dl_payload = []
    return dl_payload
