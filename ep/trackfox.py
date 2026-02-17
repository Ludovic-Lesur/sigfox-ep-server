"""
* trackfox.py
*
*  Created on: 17 nov. 2021
*      Author: Ludo
"""

from database.database import *
from ep.common import *
from log import *

### TRACKFOX public macros ###

TRACKFOX_SIGFOX_EP_ID_LIST = [ "4257", "428D", "42F1", "43B9", "43CD" ]

### TRACKFOX local macros ###

TRACKFOX_TAG_ASSET = [ "Proto_HW1.1", "Bike", "Hiking", "Hiking_spare", "Car" ]

TRACKFOX_UL_PAYLOAD_SIZE_MONITORING = 7
TRACKFOX_UL_PAYLOAD_SIZE_ERROR_STACK = 12

TRACKFOX_ERROR_VALUE_VSRC = 0xFFFF
TRACKFOX_ERROR_VALUE_VCAP = 0xFFFF
TRACKFOX_ERROR_VALUE_TEMPERATURE = 0x7F
TRACKFOX_ERROR_VALUE_HUMIDITY = 0xFF

### TRACKFOX classes ###

class TrackFox:

    @staticmethod
    def _get_asset(sigfox_ep_id: str) -> str:
        # Default is unknown.
        asset = COMMON_UNKNOWN
        if (sigfox_ep_id in TRACKFOX_SIGFOX_EP_ID_LIST):
            asset = TRACKFOX_TAG_ASSET[TRACKFOX_SIGFOX_EP_ID_LIST.index(sigfox_ep_id)]
        return asset
    
    @staticmethod
    def get_tags(sigfox_ep_id: str) -> Dict[str, Any]:
        # Local variables.
        tags = {
            DATABASE_TAG_SIGFOX_EP_ID: sigfox_ep_id,
            DATABASE_TAG_ASSET: TrackFox._get_asset(sigfox_ep_id)
        }
        return tags
    
    @staticmethod
    def get_record_list(database: Database, timestamp: int, sigfox_ep_id: str, ul_payload: str) -> List[Record]:
        # Local variables.
        record_list = []
        record = Record()
        # Unused parameter.
        _ = database
        # Common properties.
        record.database = DATABASE_TRACKFOX
        record.timestamp = timestamp
        record.tags = TrackFox.get_tags(sigfox_ep_id)
        # Startup frame.
        if (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_SIZE_STARTUP)):
            Common.get_record_startup(record, timestamp, ul_payload, record_list)
        # Geolocation frame.
        elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_SIZE_GEOLOC)):
            Common.get_record_geolocation(record, timestamp, ul_payload, record_list)
        # Geolocation timeout frame.
        elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_SIZE_GEOLOC_TIMEOUT)):
            Common.get_record_geolocation_timeout(record, timestamp, ul_payload, record_list)
        # Error stack frame.
        elif (len(ul_payload) == (2 * TRACKFOX_UL_PAYLOAD_SIZE_ERROR_STACK)):
            Common.get_record_error_stack(record, timestamp, ul_payload, (TRACKFOX_UL_PAYLOAD_SIZE_ERROR_STACK // 2), record_list)
        # Monitoring frame.
        elif (len(ul_payload) == (2 * TRACKFOX_UL_PAYLOAD_SIZE_MONITORING)):
            # Parse fields.
            tamb_degrees_one_complement = int(ul_payload[0:2], 16)
            hamb_percent = int(ul_payload[2:4], 16)
            vsrc_mv = int(ul_payload[4:8], 16)
            vcap_mv = int(ul_payload[8:12], 16)
            status = int(ul_payload[12:14], 16)
            # Create monitoring record.
            record.measurement = DATABASE_MEASUREMENT_MONITORING
            record.fields = {
                DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                DATABASE_FIELD_STATUS: status
            }
            record.add_field(tamb_degrees_one_complement, TRACKFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_TEMPERATURE, float(Common.one_complement_to_value(tamb_degrees_one_complement, 7)))
            record.add_field(hamb_percent, TRACKFOX_ERROR_VALUE_HUMIDITY, DATABASE_FIELD_HUMIDITY, float(hamb_percent))
            record.add_field(vsrc_mv, TRACKFOX_ERROR_VALUE_VSRC, DATABASE_FIELD_SOURCE_VOLTAGE, float(vsrc_mv / 1000.0))
            record.add_field(vcap_mv, TRACKFOX_ERROR_VALUE_VCAP, DATABASE_FIELD_STORAGE_VOLTAGE, float(vcap_mv / 1000.0))
            record_list.append(copy.copy(record))
        else:
            Log.debug_print("[TRACKFOX] * Invalid UL payload")
        return record_list
    
    @staticmethod
    def get_default_dl_payload(sigfox_ep_id: str) -> str:
        # Local variables.
        dl_payload = []
        # Unused parameter.
        _ = sigfox_ep_id
        # No downlink payload defined.
        return dl_payload
