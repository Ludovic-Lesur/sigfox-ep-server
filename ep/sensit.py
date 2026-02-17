"""
* sensit.py
*
*  Created on: 17 nov. 2021
*      Author: Ludo
"""

from database.database import *
from ep.common import *
from log import *

### SENSIT public macros ###

SENSIT_SIGFOX_EP_ID_LIST = [ "86BD75" ]

### SENSIT local macros ###

SENSIT_TAG_SITE = [ "Prat_Albis" ]

SENSIT_VERSION = [ "V2" ]

SENSIT_UL_PAYLOAD_SIZE_MONITORING = 4
SENSIT_UL_PAYLOAD_SIZE_CONFIGURATION = 12

SENSIT_ERROR_VALUE_VBAT = 0xFF
SENSIT_ERROR_VALUE_MODE = 0xFF
SENSIT_ERROR_VALUE_TEMPERATURE = 0xFF
SENSIT_ERROR_VALUE_HUMIDITY = 0xFF

### SENSIT classes ###

class Sensit:

    @staticmethod
    def _get_site(sigfox_ep_id: str) -> str:
        # Default is unknown.
        site = COMMON_UNKNOWN
        if (sigfox_ep_id in SENSIT_SIGFOX_EP_ID_LIST):
            site = SENSIT_TAG_SITE[SENSIT_SIGFOX_EP_ID_LIST.index(sigfox_ep_id)]
        return site
    
    @staticmethod
    def _get_version(sigfox_ep_id: str) -> str:
        # Default is unknown.
        version = COMMON_UNKNOWN
        if (sigfox_ep_id in SENSIT_SIGFOX_EP_ID_LIST):
            version = SENSIT_VERSION[SENSIT_SIGFOX_EP_ID_LIST.index(sigfox_ep_id)]
        return version
    
    @staticmethod
    def get_tags(sigfox_ep_id: str) -> Dict[str, Any]:
        # Local variables.
        tags = {
            DATABASE_TAG_SIGFOX_EP_ID: sigfox_ep_id,
            DATABASE_TAG_SITE: Sensit._get_site(sigfox_ep_id)
        }
        return tags
    
    @staticmethod
    def get_record_list(database: Database, timestamp: int, sigfox_ep_id: str, ul_payload: str) -> List[Record]:
        # Local variables.
        record_list = []
        record = Record()
        sensit_version = Sensit._get_version(sigfox_ep_id)
        # Unused parameter.
        _ = database
        # Common properties.
        record.database = DATABASE_SENSIT
        record.timestamp = timestamp
        record.tags = Sensit.get_tags(sigfox_ep_id)
        # Monitoring or configuration frame.
        if (len(ul_payload) == (2 * SENSIT_UL_PAYLOAD_SIZE_MONITORING)) or (len(ul_payload) == (2 * SENSIT_UL_PAYLOAD_SIZE_CONFIGURATION)):
            # Parse fields.
            vbat_mv = SENSIT_ERROR_VALUE_VBAT
            mode = SENSIT_ERROR_VALUE_MODE
            tamb_degrees = SENSIT_ERROR_VALUE_TEMPERATURE
            hamb_percent = SENSIT_ERROR_VALUE_HUMIDITY
            # Check version.
            if (sensit_version.find("V3") >= 0):
                vbat_mv = (((int(ul_payload[0:2], 16) >> 3) & 0x1F) * 50) + 2700
                mode = ((int(ul_payload[2:4], 16) >> 3) & 0x0F)
            else:
                vbat_mv = ((((int(ul_payload[0:2], 16) >> 3) & 0x10) + (int(ul_payload[2:4], 16) & 0x0F)) * 50) + 2700
                mode = (int(ul_payload[0:2], 16) & 0x07)
            # Check mode.
            if (mode == 0x01):
                if (sensit_version.find("V3") >= 0):
                    tamb_degrees = ((((int(ul_payload[2:4], 16) << 8) & 0x300) + (int(ul_payload[4:6], 16))) - 200.0) / (8.0)
                else:
                    tamb_degrees = ((((int(ul_payload[2:4], 16) << 2) & 0x3C0) + (int(ul_payload[4:6], 16) & 0x3F)) - 200.0) / (8.0)
                hamb_percent = (int(ul_payload[6:8], 16)) / (2.0)
            # Create monitoring record.
            record.measurement = DATABASE_MEASUREMENT_MONITORING
            record.fields = {
                DATABASE_FIELD_LAST_DATA_TIME: timestamp
            }
            record.add_field(vbat_mv, SENSIT_ERROR_VALUE_VBAT, DATABASE_FIELD_STORAGE_VOLTAGE, float(vbat_mv / 1000.0))
            record.add_field(mode, SENSIT_ERROR_VALUE_MODE, DATABASE_FIELD_MODE, mode)
            record.add_field(tamb_degrees, SENSIT_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_TEMPERATURE, float(tamb_degrees))
            record.add_field(hamb_percent, SENSIT_ERROR_VALUE_HUMIDITY, DATABASE_FIELD_HUMIDITY, float(hamb_percent))
            record_list.append(copy.copy(record))
        else:
            Log.debug_print("[SENSIT] * Invalid UL payload")
        return record_list
    
    @staticmethod
    def get_default_dl_payload(sigfox_ep_id: str) -> str:
        # Local variables.
        dl_payload = []
        sensit_version = Sensit._get_version(sigfox_ep_id)
        # Check ID.
        if (sigfox_ep_id in SENSIT_SIGFOX_EP_ID_LIST):
            # Check version.
            if (sensit_version.find("V3") >= 0):
                dl_payload = "7F003F0F0004323C"
            else:
                dl_payload = "00FF008F04017316"
        return dl_payload
