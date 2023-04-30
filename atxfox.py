from __future__ import print_function

from common import *
from influx_db import *
from log import *

### LOCAL MACROS ###

# ATXFOX tags.
__ATXFOX_RACK = ["1", "1", "1", "1", "1", "2", "2", "2", "2", "2"]
__ATXFOX_PSFE = ["+3.3V", "+5.0V", "+12.0V", "Adjustable", "Battery_charger", "+3.3V", "+5.0V", "+12.0V", "Adjustable", "Battery_charger"]
# Sigfox frames length.
__ATXFOX_UL_PAYLOAD_STARTUP_SHUTDOWN_SIZE = 1
__ATXFOX_UL_PAYLOAD_MONITORING_SIZE = 9
__ATXFOX_UL_PAYLOAD_ERROR_STACK_SIZE = 12

### PUBLIC MACROS ###

# ATXFOX EP-IDs.
ATXFOX_EP_ID = ["868E", "869E", "87A5", "87EE", "87F1", "87F3", "87F4", "87F6", "87FC", "8922"]

### LOCAL FUNCTIONS ###

# Function performing Sigfox ID to ATX rack conversion
def __ATXFOX_get_rack(sigfox_ep_id):
    # Default is unknown.
    rack = "unknown"
    if (sigfox_ep_id in ATXFOX_EP_ID):
        rack = __ATXFOX_RACK[ATXFOX_EP_ID.index(sigfox_ep_id)]
    return rack

# Function performing Sigfox ID to ATX power supply front-end conversion
def __ATXFOX_get_psfe(sigfox_ep_id):
    # Default is unknown.
    power_supply_type = "unknown"
    if (sigfox_ep_id in ATXFOX_EP_ID):
        power_supply_type = __ATXFOX_PSFE[ATXFOX_EP_ID.index(sigfox_ep_id)]
    return power_supply_type

# Function adding the specific MeteoFox tags.
def __ATXFOX_add_tags(json_body, sigfox_ep_id) :
    for idx in range(len(json_body)) :
        json_body[idx]["tags"] = {
            INFLUX_DB_TAG_SIGFOX_EP_ID : sigfox_ep_id,
            INFLUX_DB_TAG_RACK : __ATXFOX_get_rack(sigfox_ep_id),
            INFLUX_DB_TAG_PSFE : __ATXFOX_get_psfe(sigfox_ep_id)
        }

### PUBLIC FUNCTIONS ###

# Function for parsing ATXFox device payload and fill database.
def ATXFOX_fill_data_base(timestamp, sigfox_ep_id, ul_payload):
    # Init JSON object.
    json_body = []
    # Startup frame.
    if (len(ul_payload) == (2 * COMMON_STARTUP_DATA_LENGTH_BYTES)) :
        # Create JSON object.
        result = COMMON_create_json_startup_data(timestamp, ul_payload)
        json_body = result[0]
        log_data = result[1]
        LOG_print_timestamp("[ATXFOX] * Startup data * rack=" + __ATXFOX_get_rack(sigfox_ep_id) + " psfe=" + __ATXFOX_get_psfe(sigfox_ep_id) + " " + log_data)
    # Error stack frame.
    if (len(ul_payload) == (2 * __ATXFOX_UL_PAYLOAD_ERROR_STACK_SIZE)) :
        # Create JSON object.
        result = COMMON_create_json_error_stack_data(timestamp, ul_payload, (__ATXFOX_UL_PAYLOAD_ERROR_STACK_SIZE / 2))
        json_body = result[0]
        log_data = result[1]
        LOG_print_timestamp("[ATXFOX] * Error stack * rack=" + __ATXFOX_get_rack(sigfox_ep_id) + " psfe=" + __ATXFOX_get_psfe(sigfox_ep_id) + " " + log_data)
    # Startup-shutdown frame.
    if (len(ul_payload) == (2 * __ATXFOX_UL_PAYLOAD_STARTUP_SHUTDOWN_SIZE)) :
        # Parse fields.
        status = (int(ul_payload[0:2], 16))
        # Check status.
        if (status == 0x00) :
            # Create JSON object.
            json_body = [
            {
                "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
                "time": timestamp,
                "fields": {
                    INFLUX_DB_FIELD_TIME_LAST_SHUTDOWN : timestamp,
                    INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp,
                    INFLUX_DB_FIELD_STATE : status
                },
            }]
            LOG_print_timestamp("[ATXFOX] * Shutdown event * rack=" + __ATXFOX_get_rack(sigfox_ep_id) + " psfe=" + __ATXFOX_get_psfe(sigfox_ep_id))
        elif (status == 0x01) :
            # Create JSON object.
            json_body = [
            {
                "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
                "time": timestamp,
                "fields": {
                    INFLUX_DB_FIELD_TIME_LAST_STARTUP : timestamp,
                    INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp,
                    INFLUX_DB_FIELD_STATE : status
                },
            }]
            LOG_print_timestamp("[ATXFOX] * Startup event * rack=" + __ATXFOX_get_rack(sigfox_ep_id) + " psfe=" + __ATXFOX_get_psfe(sigfox_ep_id))
    # Monitoring frame.
    if (len(ul_payload) == (2 * __ATXFOX_UL_PAYLOAD_MONITORING_SIZE)) :
        # Parse fields.
        vout_mv = int(ul_payload[0:4], 16) if (int(ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
        i_range = int(ul_payload[4:6], 16)
        iout_ua = int(ul_payload[6:12], 16) if (int(ul_payload[6:12], 16) != COMMON_ERROR_VALUE_ANALOG_24BITS) else COMMON_ERROR_DATA
        vmcu_mv = int(ul_payload[12:16], 16) if (int(ul_payload[12:16], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
        tmcu_degrees = COMMON_one_complement_to_value(int(ul_payload[16:18], 16), 7) if (int(ul_payload[16:18], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
        # Compute output power in nW (uA * mV).
        pout_nw = COMMON_ERROR_DATA
        if (vout_mv != COMMON_ERROR_DATA) and (iout_ua != COMMON_ERROR_DATA) :
            pout_nw = (vout_mv * iout_ua)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
            "time": timestamp,
            "fields": {
                INFLUX_DB_FIELD_I_RANGE : i_range,
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
        if (vout_mv != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_VOUT] = vout_mv
        if (iout_ua != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_IOUT] = iout_ua
        if (vmcu_mv != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
        if (tmcu_degrees != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
        if (pout_nw != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_POUT] = pout_nw
        LOG_print_timestamp("[ATXFOX] * Monitoring data * rack=" + __ATXFOX_get_rack(sigfox_ep_id) + " psfe=" + __ATXFOX_get_psfe(sigfox_ep_id) +
                            " vout=" + str(vout_mv) + "mV i_range=" + str(i_range) + " iout=" + str(iout_ua) + "ua pout=" + str(pout_nw) +
                            "nW vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC")
    # Fill data base.
    if (len(json_body) > 0) :
        __ATXFOX_add_tags(json_body, sigfox_ep_id)
        INFLUX_DB_write_data(INFLUX_DB_DATABASE_ATXFOX, json_body)
    else :
        LOG_print_timestamp("[ATXFOX] * Invalid frame")
        