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

ATXFOX_ERROR_VALUE_OUTPUT_VOLTAGE = 0xFFFF
ATXFOX_ERROR_VALUE_OUTPUT_CURRENT = 0xFFFFFF
ATXFOX_ERROR_VALUE_MCU_VOLTAGE = 0xFFFF
ATXFOX_ERROR_VALUE_MCU_TEMPERATURE = 0X7F

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
            output_voltage_mv = int(ul_payload[0:4], 16)
            output_current_range = int(ul_payload[4:6], 16)
            output_current_ua = int(ul_payload[6:12], 16)
            mcu_voltage_mv = int(ul_payload[12:16], 16)
            mcu_temperature_one_complement = int(ul_payload[16:18], 16)
            # Create electrical record.
            record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
            record.fields = {
                DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                DATABASE_FIELD_OUTPUT_CURRENT_RANGE: output_current_range
            }
            record.add_field(output_voltage_mv, ATXFOX_ERROR_VALUE_OUTPUT_VOLTAGE, DATABASE_FIELD_OUTPUT_VOLTAGE, float(output_voltage_mv / 1000.0))
            record.add_field(output_current_ua, ATXFOX_ERROR_VALUE_OUTPUT_CURRENT, DATABASE_FIELD_OUTPUT_CURRENT, float(output_current_ua / 1000000.0))
            record_list.append(copy.copy(record))
            # Create monitoring record.
            record.measurement = DATABASE_MEASUREMENT_MONITORING
            record.fields = {
                DATABASE_FIELD_LAST_DATA_TIME: timestamp
            }
            record.add_field(mcu_voltage_mv, ATXFOX_ERROR_VALUE_MCU_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, float(mcu_voltage_mv / 1000.0))
            record.add_field(mcu_temperature_one_complement, ATXFOX_ERROR_VALUE_MCU_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, float(Common.one_complement_to_value(mcu_temperature_one_complement, 7)))
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
