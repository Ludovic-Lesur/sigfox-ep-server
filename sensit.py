from __future__ import print_function

from common import *
from influx_db import *
from log import *

### LOCAL MACROS ###

# Sensit tags.
__SENSIT_SITE = ["Sigfox_bureau", "Sigfox_cagibi", "Prat_Albis", "Le_Vigan_maison", "Le_Vigan_atelier"]
__SENSIT_VERSION = ["V2", "V2", "V2", "V3", "V3"]
# Sigfox frames length.
__SENSIT_UL_PAYLOAD_MONITORING_SIZE = 4
__SENSIT_UL_PAYLOAD_CONFIGURATION_SIZE = 12

### PUBLIC MACROS ###

SENSIT_EP_ID = ["1C8330", "20F815", "86BD75", "B437B2", "B4384E"]

### LOCAL FUNCTIONS ###

# Function performing Sigfox ID to Sensit site conversion.
def __SENSIT_get_site(sigfox_ep_id):
    # Default is unknown.
    site = "unknown"
    if (sigfox_ep_id in SENSIT_EP_ID):
        site = __SENSIT_SITE[SENSIT_EP_ID.index(sigfox_ep_id)]
    return site

# Function performing Sigfox ID to Sensit version conversion.
def __SENSIT_get_version(sigfox_ep_id):
    # Default is unknown.
    version = "unknown"
    if (sigfox_ep_id in SENSIT_EP_ID):
        version = __SENSIT_VERSION[SENSIT_EP_ID.index(sigfox_ep_id)]
    return version

# Function adding the specific Sensit tags.
def __SENSIT_add_tags(json_body, sigfox_ep_id) :
    for idx in range(len(json_body)) :
        json_body[idx]["tags"] = {
            INFLUX_DB_TAG_SIGFOX_EP_ID : sigfox_ep_id,
            INFLUX_DB_TAG_SITE : __SENSIT_get_site(sigfox_ep_id)
        }

### PUBLIC FUNCTIONS ###

# Function for parsing Sensit device payload and fill database. 
def SENSIT_fill_data_base(timestamp, sigfox_ep_id, ul_payload) :
    # Init JSON object.
    json_body = []
    # Get version.
    sensit_version = __SENSIT_get_version(sigfox_ep_id)
    # Monitoring frame.
    if (len(ul_payload) == (2 * __SENSIT_UL_PAYLOAD_MONITORING_SIZE)) or (len(ul_payload) == (2 * __SENSIT_UL_PAYLOAD_CONFIGURATION_SIZE)) :
        # Parse fields.
        vbat_mv = "error"
        mode = "error"
        tamb_degrees = "error"
        hamb_percent = "error"
        if (sensit_version.find("V3") >= 0) :
            vbat_mv = (((int(ul_payload[0:2], 16) >> 3) & 0x1F) * 50) + 2700
            mode = ((int(ul_payload[2:4], 16) >> 3) & 0x0F)
        else :
            vbat_mv = ((((int(ul_payload[0:2], 16) >> 3) & 0x10) + (int(ul_payload[2:4], 16) & 0x0F)) * 50) + 2700
            mode = (int(ul_payload[0:2], 16) & 0x07)
        # Check mode.
        if (mode == 0x01):
            if (sensit_version.find("V3") >= 0):
                tamb_degrees = ((((int(ul_payload[2:4], 16) << 8) & 0x300) + (int(ul_payload[4:6], 16))) - 200.0) / (8.0)
            else:
                tamb_degrees = ((((int(ul_payload[2:4], 16) << 2) & 0x3C0) + (int(ul_payload[4:6], 16) & 0x3F)) - 200.0) / (8.0)
            hamb_percent = (int(ul_payload[6:8], 16)) / (2.0)    
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
            "time": timestamp,
            "fields": {
                INFLUX_DB_FIELD_VBAT : vbat_mv,
                INFLUX_DB_FIELD_MODE : mode,
                INFLUX_DB_FIELD_TAMB : tamb_degrees,
                INFLUX_DB_FIELD_HAMB : hamb_percent,
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_EP_ID : sigfox_ep_id,
                INFLUX_DB_TAG_SITE : __SENSIT_get_site(sigfox_ep_id)
            }
        },
        {
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "time": timestamp,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_EP_ID : sigfox_ep_id,
                INFLUX_DB_TAG_SITE : __SENSIT_get_site(sigfox_ep_id)
            }
        }]
        LOG_print_timestamp("[SENSIT] * Monitoring data * site=" + __SENSIT_get_site(sigfox_ep_id) +
                            " vbat=" + str(vbat_mv) + "mV mode=" + str(mode) + " tamb=" + str(tamb_degrees) + "dC hamb=" + str(hamb_percent) + "%")
    # Fill data base.
    if (len(json_body) > 0) :
        __SENSIT_add_tags(json_body, sigfox_ep_id)
        INFLUX_DB_write_data(INFLUX_DB_DATABASE_SENSIT, json_body)
    else :
        LOG_print_timestamp("[SENSIT] * Invalid frame")        