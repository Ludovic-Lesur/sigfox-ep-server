"""
* homefox.py
*
*  Created on: 16 nov. 2025
*      Author: Ludo
"""

from database.database import *
from ep.common import *
from log import *

### HOMEFOX public macros ###

HOMEFOX_SIGFOX_EP_ID_LIST = [ "1230", "1331", "133F", "1389", "13ED", "147D" ]

### HOMEFOX local macros ###

HOMEFOX_TAG_SITE = [ "Proto_HW2.0", "Escalquens", "Escalquens", "Escalquens", "Escalquens", "Escalquens" ]
HOMEFOX_TAG_LOCATION = [ "Proto_HW2.0", "Living_room", "Bed_room", "Store_room", "Bath_room", "Main_door" ]

HOMEFOX_UL_PAYLOAD_SIZE_MONITORING = 6
HOMEFOX_UL_PAYLOAD_SIZE_ERROR_STACK = 12
HOMEFOX_UL_PAYLOAD_SIZE_AIR_QUALITY = 7
HOMEFOX_UL_PAYLOAD_SIZE_ACCELEROMETER = 1

HOMEFOX_ERROR_VALUE_VBAT = 0xFFFF
HOMEFOX_ERROR_VALUE_TEMPERATURE = 0x7FF
HOMEFOX_ERROR_VALUE_HUMIDITY = 0xFF
HOMEFOX_ERROR_VALUE_TVOC = 0xFFFF
HOMEFOX_ERROR_VALUE_ECO2 = 0xFFFF
HOMEFOX_ERROR_VALUE_AQI_UBA = 0x7
HOMEFOX_ERROR_VALUE_AQI_S = 0x3FF
HOMEFOX_ERROR_VALUE_ACQUISITION_MODE = 0x7

### HOMEFOX classes ###

class HomeFox:

    @staticmethod
    def _get_site(sigfox_ep_id: str) -> str:
        # Default is unknown.
        site = COMMON_UNKNOWN
        if (sigfox_ep_id in HOMEFOX_SIGFOX_EP_ID_LIST):
            site = HOMEFOX_TAG_SITE[HOMEFOX_SIGFOX_EP_ID_LIST.index(sigfox_ep_id)]
        return site
    
    @staticmethod
    def _get_location(sigfox_ep_id: str) -> str:
        # Default is unknown.
        location = COMMON_UNKNOWN
        if (sigfox_ep_id in HOMEFOX_SIGFOX_EP_ID_LIST):
            location = HOMEFOX_TAG_LOCATION[HOMEFOX_SIGFOX_EP_ID_LIST.index(sigfox_ep_id)]
        return location
    
    @staticmethod
    def get_tags(sigfox_ep_id: str) -> Dict[str, Any]:
        # Local variables.
        tags = {
            DATABASE_TAG_SIGFOX_EP_ID: sigfox_ep_id,
            DATABASE_TAG_SITE: HomeFox._get_site(sigfox_ep_id),
            DATABASE_TAG_LOCATION: HomeFox._get_location(sigfox_ep_id)
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
        record.database = DATABASE_HOMEFOX
        record.timestamp = timestamp
        record.tags = HomeFox.get_tags(sigfox_ep_id)
        record.limited_retention = True
        # Startup frame.
        if (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_SIZE_STARTUP)):
            Common.get_record_startup(record, timestamp, ul_payload, record_list)
        # Error stack frame.
        elif (len(ul_payload) == (2 * HOMEFOX_UL_PAYLOAD_SIZE_ERROR_STACK)):
            Common.get_record_error_stack(record, timestamp, ul_payload, (HOMEFOX_UL_PAYLOAD_SIZE_ERROR_STACK // 2), record_list)
        # Monitoring frame.
        elif (len(ul_payload) == (2 * HOMEFOX_UL_PAYLOAD_SIZE_MONITORING)):
            # Parse fields.
            vbat_mv = int(ul_payload[0:4], 16)
            tamb_tenth_degrees_one_complement = int(ul_payload[5:8], 16)
            hamb_percent = int(ul_payload[8:10], 16)
            status = int(ul_payload[10:12], 16)
            # Create sensor record.
            record.measurement = DATABASE_MEASUREMENT_HOME
            record.fields = {
                DATABASE_FIELD_LAST_DATA_TIME: timestamp,
            }
            record.add_field(tamb_tenth_degrees_one_complement, HOMEFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_TEMPERATURE, float(Common.one_complement_to_value(tamb_tenth_degrees_one_complement, 11) / 10.0))
            record.add_field(hamb_percent, HOMEFOX_ERROR_VALUE_HUMIDITY, DATABASE_FIELD_HUMIDITY, float(hamb_percent))
            record_list.append(copy.copy(record))
            # Create monitoring record.
            record.measurement = DATABASE_MEASUREMENT_MONITORING
            record.fields = {
                DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                DATABASE_FIELD_STATUS: status
            }
            record.add_field(vbat_mv, HOMEFOX_ERROR_VALUE_VBAT, DATABASE_FIELD_STORAGE_VOLTAGE, float(vbat_mv / 1000.0))
            record_list.append(copy.copy(record))
        # Air quality data frame.
        elif (len(ul_payload) == (2 * HOMEFOX_UL_PAYLOAD_SIZE_AIR_QUALITY)):
            # Parse fields.
            tvoc_ppb = int(ul_payload[0:4], 16)
            eco2_ppm = int(ul_payload[4:8], 16)
            aqi_uba = ((int(ul_payload[8:10], 16) >> 5) & 0x07)
            aqi_s = ((int(ul_payload[8:10], 16) & 0x1F) << 5) + ((int(ul_payload[10:12], 16) >> 3) & 0x1F)
            acquisition_mode = (int(ul_payload[10:12], 16) & 0x07)
            acquisition_status = ((int(ul_payload[12:14], 16) >> 6) & 0x03)
            acquisition_duration_seconds = ((int(ul_payload[12:14], 16) & 0x3F) * 10)
            # Create air quality record.
            record.measurement = DATABASE_MEASUREMENT_HOME
            record.fields = {
                DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                DATABASE_FIELD_AIR_QUALITY_ACQUISITION_STATUS : acquisition_status,
                DATABASE_FIELD_AIR_QUALITY_ACQUISITION_TIME: float(acquisition_duration_seconds)
            }
            record.add_field(tvoc_ppb, HOMEFOX_ERROR_VALUE_TVOC, DATABASE_FIELD_AIR_QUALITY_TVOC, float(tvoc_ppb))
            record.add_field(eco2_ppm, HOMEFOX_ERROR_VALUE_ECO2, DATABASE_FIELD_AIR_QUALITY_ECO2, float(eco2_ppm))
            record.add_field(aqi_uba, HOMEFOX_ERROR_VALUE_AQI_UBA, DATABASE_FIELD_AIR_QUALITY_INDEX_UBA, float(aqi_uba))
            record.add_field(aqi_s, HOMEFOX_ERROR_VALUE_AQI_S, DATABASE_FIELD_AIR_QUALITY_INDEX_S, float(aqi_s))
            record.add_field(acquisition_mode, HOMEFOX_ERROR_VALUE_ACQUISITION_MODE, DATABASE_FIELD_AIR_QUALITY_ACQUISITION_MODE, acquisition_mode)
            record_list.append(copy.copy(record))
        # Accelerometer event frame.
        elif (len(ul_payload) == (2 * HOMEFOX_UL_PAYLOAD_SIZE_ACCELEROMETER)):
            # Parse fields.
            accelerometer_event_source = int(ul_payload[0:2], 16)
            # Create motion record.
            record.measurement = DATABASE_MEASUREMENT_HOME
            record.fields = {
                DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                DATABASE_FIELD_ACCELEROMETER_EVENT_SOURCE: accelerometer_event_source
            }
            record_list.append(copy.copy(record))
        else:
            Log.debug_print("[HOMEFOX] * Invalid UL payload")
        return record_list
    
    @staticmethod
    def get_default_dl_payload(sigfox_ep_id: str) -> str:
        # Local variables.
        dl_payload = []
        # Check ID.
        if (sigfox_ep_id in HOMEFOX_SIGFOX_EP_ID_LIST):
            dl_payload = "0000000000000000"
        return dl_payload
