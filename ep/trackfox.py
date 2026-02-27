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

TRACKFOX_ERROR_VALUE_SOURCE_VOLTAGE = 0xFFFF
TRACKFOX_ERROR_VALUE_STORAGE_VOLTAGE = 0xFFFF
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
        record.limited_retention = True
        # Startup frame.
        if (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_SIZE_STARTUP)):
            Common.get_record_startup(record, timestamp, ul_payload, record_list)
        # Geolocation frame.
        elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_SIZE_GPS)):
            Common.get_record_gps(record, timestamp, ul_payload, record_list)
        # Geolocation timeout frame.
        elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_SIZE_GPS_TIMEOUT)):
            Common.get_record_gps_timeout(record, timestamp, ul_payload, record_list)
        # Error stack frame.
        elif (len(ul_payload) == (2 * TRACKFOX_UL_PAYLOAD_SIZE_ERROR_STACK)):
            Common.get_record_error_stack(record, timestamp, ul_payload, (TRACKFOX_UL_PAYLOAD_SIZE_ERROR_STACK // 2), record_list)
        # Monitoring frame.
        elif (len(ul_payload) == (2 * TRACKFOX_UL_PAYLOAD_SIZE_MONITORING)):
            # Parse fields.
            temperature_degrees_one_complement = int(ul_payload[0:2], 16)
            humidity_percent = int(ul_payload[2:4], 16)
            source_voltage_mv = int(ul_payload[4:8], 16)
            storage_voltage_mv = int(ul_payload[8:12], 16)
            status = int(ul_payload[12:14], 16)
            # Create monitoring record.
            record.measurement = DATABASE_MEASUREMENT_MONITORING
            record.fields = {
                DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                DATABASE_FIELD_STATUS: status
            }
            record.add_field(temperature_degrees_one_complement, TRACKFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_TEMPERATURE, float(Common.one_complement_to_value(temperature_degrees_one_complement, 7)))
            record.add_field(humidity_percent, TRACKFOX_ERROR_VALUE_HUMIDITY, DATABASE_FIELD_HUMIDITY, float(humidity_percent))
            record.add_field(source_voltage_mv, TRACKFOX_ERROR_VALUE_SOURCE_VOLTAGE, DATABASE_FIELD_SOURCE_VOLTAGE, float(source_voltage_mv / 1000.0))
            record.add_field(storage_voltage_mv, TRACKFOX_ERROR_VALUE_STORAGE_VOLTAGE, DATABASE_FIELD_STORAGE_VOLTAGE, float(storage_voltage_mv / 1000.0))
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
