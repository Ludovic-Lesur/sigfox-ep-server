from __future__ import print_function
import math

from database.influx_db import *
from log import *
from ep.common import *

### LOCAL MACROS ###

# HomeFox tags.
__HOMEFOX_SITE = ["Proto_HW2.0", "Escalquens", "Escalquens", "Escalquens", "Escalquens", "Escalquens"]
__HOMEFOX_LOCATION = ["Proto_HW2.0", "Living_room", "Bed_room", "Store_room", "Bath_room", "Main_door"]
# Sigfox frame lengths.
__HOMEFOX_UL_PAYLOAD_SIZE_MONITORING = 6
__HOMEFOX_UL_PAYLOAD_SIZE_ERROR_STACK = 12
__HOMEFOX_UL_PAYLOAD_SIZE_AIR_QUALITY = 7
__HOMEFOX_UL_PAYLOAD_SIZE_ACCELEROMETER = 1

### PUBLIC MACROS ###

# HomeFox EP-IDs.
HOMEFOX_EP_ID_LIST = ["1230", "1331", "133F", "1389", "13ED", "147D"]

### LOCAL FUNCTIONS ###

# Function performing Sigfox ID to HomeFox site conversion.
def __HOMEFOX_get_site(sigfox_ep_id):
    # Default is unknown.
    site = "unknown"
    if (sigfox_ep_id in HOMEFOX_EP_ID_LIST):
        site = __HOMEFOX_SITE[HOMEFOX_EP_ID_LIST.index(sigfox_ep_id)]
    return site

# Function performing Sigfox ID to HomeFox location conversion.
def __HOMEFOX_get_location(sigfox_ep_id):
    # Default is unknown.
    location = "unknown"
    if (sigfox_ep_id in HOMEFOX_EP_ID_LIST):
        location = __HOMEFOX_LOCATION[HOMEFOX_EP_ID_LIST.index(sigfox_ep_id)]
    return location

### PUBLIC FUNCTIONS ###

# Function adding the specific HomeFox tags.
def HOMEFOX_add_ep_tag(json_ul_data, sigfox_ep_id):
    for idx in range(len(json_ul_data)):
        if ("tags" in json_ul_data[idx]):
            json_ul_data[idx]["tags"][INFLUX_DB_TAG_SIGFOX_EP_ID] = sigfox_ep_id
            json_ul_data[idx]["tags"][INFLUX_DB_TAG_SITE] = __HOMEFOX_get_site(sigfox_ep_id)
            json_ul_data[idx]["tags"][INFLUX_DB_TAG_LOCATION] = __HOMEFOX_get_location(sigfox_ep_id)
        else:
            json_ul_data[idx]["tags"] = {
                INFLUX_DB_TAG_SIGFOX_EP_ID: sigfox_ep_id,
                INFLUX_DB_TAG_SITE: __HOMEFOX_get_site(sigfox_ep_id),
                INFLUX_DB_TAG_LOCATION: __HOMEFOX_get_location(sigfox_ep_id)
            }

# Function for parsing HomeFox device payload and fill database.
def HOMEFOX_parse_ul_payload(timestamp, sigfox_ep_id, ul_payload):
    # Init JSON object.
    json_ul_data = []
    # Startup frame.
    if (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_STARTUP_SIZE)):
        # Create JSON object.
        result = COMMON_create_json_startup_data(timestamp, ul_payload)
        json_ul_data = result[0]
        log_data = result[1]
        LOG_print("[HOMEFOX] * Startup data * site=" + __HOMEFOX_get_site(sigfox_ep_id) + " " + log_data)
    # Error stack frame.
    elif (len(ul_payload) == (2 * __HOMEFOX_UL_PAYLOAD_SIZE_ERROR_STACK)):
        # Create JSON object.
        result = COMMON_create_json_error_stack_data(timestamp, ul_payload, (__HOMEFOX_UL_PAYLOAD_SIZE_ERROR_STACK // 2))
        json_ul_data = result[0]
        log_data = result[1]
        LOG_print("[HOMEFOX] * Error stack * site=" + __HOMEFOX_get_site(sigfox_ep_id) + " " + log_data)
    # Monitoring frame.
    elif (len(ul_payload) == (2 * __HOMEFOX_UL_PAYLOAD_SIZE_MONITORING)):
        # Parse fields.
        vbat_mv = int(ul_payload[0:4], 16) if (int(ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
        tamb_degrees = (COMMON_one_complement_to_value(int(ul_payload[5:8], 16), 11) / 10.0) if (int(ul_payload[5:8], 16) != COMMON_ERROR_VALUE_TEMPERATURE_TENTH) else COMMON_ERROR_DATA
        hamb_percent = int(ul_payload[8:10], 16) if (int(ul_payload[8:10], 16) != COMMON_ERROR_VALUE_HUMIDITY) else COMMON_ERROR_DATA
        status = int(ul_payload[10:12], 16)
        # Create JSON object.
        json_ul_data = [
        {
            "time": timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
            "fields": {
                INFLUX_DB_FIELD_STATUS: status,
                INFLUX_DB_FIELD_TIME_LAST_MONITORING_DATA: timestamp
            },
        },
        {
            "time": timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_METADATA,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION: timestamp
            },
        }]
        # Add valid fields to JSON.
        if (vbat_mv != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_VBAT] = vbat_mv
        if (tamb_degrees != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_TAMB] = tamb_degrees
        if (hamb_percent != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_HAMB] = hamb_percent
        LOG_print("[HOMEFOX] * Monitoring data * site=" + __HOMEFOX_get_site(sigfox_ep_id) +
                  " vbatt=" + str(vbat_mv) + "mV tamb=" + str(tamb_degrees) + "dC hamb=" + str(hamb_percent) + "% status=" + hex(status))
    # Air quality data frame.
    elif (len(ul_payload) == (2 * __HOMEFOX_UL_PAYLOAD_SIZE_AIR_QUALITY)):
        # Parse fields.
        tvoc_ppb = int(ul_payload[0:4], 16) if (int(ul_payload[0:4], 16) != COMMON_ERROR_VALUE_TVOC) else COMMON_ERROR_DATA
        eco2_ppm = int(ul_payload[4:8], 16) if (int(ul_payload[4:8], 16) != COMMON_ERROR_VALUE_ECO2) else COMMON_ERROR_DATA
        aqi_uba_raw = ((int(ul_payload[8:10], 16) >> 5) & 0x07)
        aqi_uba = aqi_uba_raw if (aqi_uba_raw != COMMON_ERROR_VALUE_AQI_UBA) else COMMON_ERROR_DATA
        aqi_s_raw = ((int(ul_payload[8:10], 16) & 0x1F) << 5) + ((int(ul_payload[10:12], 16) >> 3) & 0x1F)
        aqi_s = aqi_s_raw if (aqi_s_raw != COMMON_ERROR_VALUE_AQI_S) else COMMON_ERROR_DATA
        acquisition_mode_raw = (int(ul_payload[10:12], 16) & 0x07)
        acquisition_mode = acquisition_mode_raw if (acquisition_mode_raw != COMMON_ERROR_VALUE_ACQUISITION_MODE) else COMMON_ERROR_DATA
        acquisition_status = ((int(ul_payload[12:14], 16) >> 6) & 0x03)
        acquisition_duration_seconds = ((int(ul_payload[12:14], 16) & 0x3F) * 10)
        # Create JSON object.
        json_ul_data = [
        {
            "time": timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_AIR_QUALITY,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_AIR_QUALITY_DATA: timestamp,
                INFLUX_DB_FIELD_AIR_QUALITY_ACQUISITION_DURATION : acquisition_duration_seconds,
                INFLUX_DB_FIELD_AIR_QUALITY_ACQUISITION_STATUS : acquisition_status
            },
        },
        {
            "time": timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_METADATA,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION: timestamp
            },
        }]
        # Add valid fields to JSON.
        if (tvoc_ppb != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_TVOC] = tvoc_ppb
        if (eco2_ppm != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_ECO2] = eco2_ppm
        if (aqi_uba != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_AQI_UBA] = aqi_uba
        if (aqi_s != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_AQI_S] = aqi_s
        if (acquisition_mode != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_ACQUISITION_MODE] = acquisition_mode
        LOG_print("[HOMEFOX] * Air quality data * site=" + __HOMEFOX_get_site(sigfox_ep_id) +
                  " tvoc=" + str(tvoc_ppb) + "ppb eco2=" + str(eco2_ppm) + "ppm aqi_uba=" + str(aqi_uba) + " aqi_s=" + str(aqi_s) +
                  " acquisition_mode=" + str(acquisition_mode) + " acquisition_duration=" + str(acquisition_duration_seconds) +
                  "s acquisition_status=" + str(acquisition_status))
    # Accelerometer event frame.
    elif (len(ul_payload) == (2 * __HOMEFOX_UL_PAYLOAD_SIZE_ACCELEROMETER)):
        accelerometer_event_source = int(ul_payload[0:2], 16)
        # Create JSON object.
        json_ul_data = [
        {
            "time": timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_MOTION,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_MOTION_DATA: timestamp,
                INFLUX_DB_FIELD_ACCELEROMETER_EVENT_SOURCE : accelerometer_event_source,
            },
        },
        {
            "time": timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_METADATA,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION: timestamp
            },
        }]
        
        LOG_print("[HOMEFOX] * Motion data * site=" + __HOMEFOX_get_site(sigfox_ep_id) + " accelerometer_event_source=" + hex(accelerometer_event_source))
    else:
        LOG_print("[HOMEFOX] * Invalid UL payload")
    return json_ul_data

# Returns the default downlink payload to sent back to the device.
def HOMEFOX_get_default_dl_payload(sigfox_ep_id):
    # Local variables.
    dl_payload = []
    if (sigfox_ep_id in HOMEFOX_EP_ID_LIST):
        dl_payload = "0000000000000000"
    return dl_payload
