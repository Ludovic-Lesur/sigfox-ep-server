"""
* atxfox.py
*
*  Created on: 17 nov. 2021
*      Author: Ludo
"""

from database.database import *
from ep.common import *
from log import *

### ATXFOX public macros ###

ATXFOX_SIGFOX_EP_ID_LIST = [ "868E", "869E", "87A5", "87EE", "87F1", "87F3", "87F4", "87F6", "87FC", "8922" ]

### ATXFOX local macros ###

ATXFOX_TAG_RACK = [ 1, 1, 1, 1, 1, 2, 2, 2, 2, 2 ]
ATXFOX_TAG_PSFE = [ "+3.3V", "+5.0V", "+12.0V", "Adjustable", "Battery_charger", "+3.3V", "+5.0V", "+12.0V", "Adjustable", "Battery_charger" ]

ATXFOX_UL_PAYLOAD_SIZE_MONITORING = 9
ATXFOX_UL_PAYLOAD_SIZE_ERROR_STACK = 12

ATXFOX_ERROR_VALUE_VOUT = 0xFFFF
ATXFOX_ERROR_VALUE_IOUT = 0xFFFFFF
ATXFOX_ERROR_VALUE_VMCU = 0xFFFF
ATXFOX_ERROR_VALUE_TMCU = 0X7F

### ATXFOX classes ###

class ATXFox:

    @staticmethod
    def _get_rack(sigfox_ep_id: str) -> str:
        # Default is unknown.
        rack = COMMON_UNKNOWN
        if (sigfox_ep_id in ATXFOX_SIGFOX_EP_ID_LIST):
            rack = ATXFOX_TAG_RACK[ATXFOX_SIGFOX_EP_ID_LIST.index(sigfox_ep_id)]
        return rack
    
    @staticmethod
    def _get_psfe(sigfox_ep_id: str) -> str:
        # Default is unknown.
        psfe = COMMON_UNKNOWN
        if (sigfox_ep_id in ATXFOX_SIGFOX_EP_ID_LIST):
            psfe = ATXFOX_TAG_PSFE[ATXFOX_SIGFOX_EP_ID_LIST.index(sigfox_ep_id)]
        return psfe
    
    @staticmethod
    def get_tags(sigfox_ep_id: str) -> Dict[str, Any]:
        # Local variables.
        tags = {
            DATABASE_TAG_SIGFOX_EP_ID: sigfox_ep_id,
            DATABASE_TAG_RACK: ATXFox._get_rack(sigfox_ep_id),
            DATABASE_TAG_PSFE: ATXFox._get_psfe(sigfox_ep_id)
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
        record.database = DATABASE_ATXFOX
        record.timestamp = timestamp
        record.tags = ATXFox.get_tags(sigfox_ep_id)
        record.limited_retention = True
        # Startup frame.
        if (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_SIZE_STARTUP)):
            Common.get_record_startup(record, timestamp, ul_payload, record_list)
        # Error stack frame.
        elif (len(ul_payload) == (2 * ATXFOX_UL_PAYLOAD_SIZE_ERROR_STACK)):
            Common.get_record_error_stack(record, timestamp, ul_payload, (ATXFOX_UL_PAYLOAD_SIZE_ERROR_STACK // 2), record_list)
        # Monitoring frame.
        elif (len(ul_payload) == (2 * ATXFOX_UL_PAYLOAD_SIZE_MONITORING)):
            # Parse fields.
            vout_mv = int(ul_payload[0:4], 16)
            iout_range = int(ul_payload[4:6], 16)
            iout_ua = int(ul_payload[6:12], 16)
            vmcu_mv = int(ul_payload[12:16], 16)
            tmcu_one_complement = int(ul_payload[16:18], 16)
            # Create electrical record.
            record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
            record.fields = {
                DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                DATABASE_FIELD_OUTPUT_CURRENT_RANGE: iout_range
            }
            record.add_field(vout_mv, ATXFOX_ERROR_VALUE_VOUT, DATABASE_FIELD_OUTPUT_VOLTAGE, float(vout_mv / 1000.0))
            record.add_field(iout_ua, ATXFOX_ERROR_VALUE_IOUT, DATABASE_FIELD_OUTPUT_CURRENT, float(iout_ua / 1000000.0))
            record_list.append(copy.copy(record))
            # Create monitoring record.
            record.measurement = DATABASE_MEASUREMENT_MONITORING
            record.fields = {
                DATABASE_FIELD_LAST_DATA_TIME: timestamp
            }
            record.add_field(vmcu_mv, ATXFOX_ERROR_VALUE_VMCU, DATABASE_FIELD_MCU_VOLTAGE, float(vmcu_mv / 1000.0))
            record.add_field(tmcu_one_complement, ATXFOX_ERROR_VALUE_TMCU, DATABASE_FIELD_MCU_TEMPERATURE, float(Common.one_complement_to_value(tmcu_one_complement, 7)))
            record_list.append(copy.copy(record))
        else:
            Log.debug_print("[ATXFOX] * Invalid UL payload")
        return record_list
    
    @staticmethod
    def get_default_dl_payload(sigfox_ep_id: str) -> str:
        # Local variables.
        dl_payload = []
        # Unused parameter.
        _ = sigfox_ep_id
        # No downlink payload defined.
        return dl_payload
