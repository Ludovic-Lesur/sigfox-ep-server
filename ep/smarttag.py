"""
* smarttag.py
*
*  Created on: 30 jul. 2026
*      Author: Ludo
"""

from database.database import *
from ep.common import *
from ep.ep import *
from log import *

### SMARTTAG public macros ###

SMARTTAG_DEVICE_TYPE_NAME = "smarttag"
SMARTTAG_SIGFOX_EP_ID_LIST = ep.get_tags_list(SMARTTAG_DEVICE_TYPE_NAME, DATABASE_TAG_SIGFOX_EP_ID)

### SMARTTAG local macros ###

SMARTTAG_TAG_NAME = ep.get_tags_list(SMARTTAG_DEVICE_TYPE_NAME, DATABASE_TAG_NAME)

SMARTTAG_UL_PAYLOAD_SIZE = 4

SMARTTAG_HEADER_PERIODIC_TEMP_HUM_LUX = 0x07
SMARTTAG_HEADER_PERIODIC_TEMP_HUM_ACC = 0x06
SMARTTAG_HEADER_EVENT_ON = 0x04
SMARTTAG_HEADER_EVENT_OFF = 0x02
SMARTTAG_HEADER_EVENT_BUTTON = 0x01
SMARTTAG_HEADER_EVENT_FUSE = 0x03
SMARTTAG_HEADER_EVENT_ACC = 0x05

SMARTTAG_ERROR_VALUE_LPI = 0xFF
SMARTTAG_ERROR_VALUE_FUSE_EVENT_PERIOD_COUNTER = 0xFF
SMARTTAG_ERROR_VALUE_FUSE_FLAG = 0xFF
SMARTTAG_ERROR_VALUE_TEMPERATURE = 0xFF
SMARTTAG_ERROR_VALUE_HUMIDITY = 0xFF
SMARTTAG_ERROR_VALUE_LUX = 0xFF
SMARTTAG_ERROR_VALUE_EVENT_COUNT = 0xFF
SMARTTAG_ERROR_VALUE_AXIS_FLAG = 0xFF
SMARTTAG_ERROR_VALUE_INTERRUPT_COUNT = 0xFF

### SMARTTAG classes ###

class SmartTag:

    @staticmethod
    def _get_name(sigfox_ep_id: str) -> str:
        # Default is unknown.
        name = COMMON_UNKNOWN
        if (sigfox_ep_id in SMARTTAG_SIGFOX_EP_ID_LIST):
            name = SMARTTAG_TAG_NAME[SMARTTAG_SIGFOX_EP_ID_LIST.index(sigfox_ep_id)]
        return name
    
    @staticmethod
    def get_tags(sigfox_ep_id: str) -> Dict[str, Any]:
        # Local variables.
        tags = {
            DATABASE_TAG_SIGFOX_EP_ID: sigfox_ep_id,
            DATABASE_TAG_NAME: SmartTag._get_name(sigfox_ep_id)
        }
        return tags
    
    @staticmethod
    def get_record_list(database: Database, timestamp: int, sigfox_ep_id: str, ul_payload: str) -> List[Record]:
        # Local variables.
        data_type = DATABASE_FIELD_DATA_TYPE_UNKNOWN
        record_list = []
        record = Record()
        # Unused parameter.
        _ = database
        # Common properties.
        record.database = DATABASE_SMARTTAG
        record.timestamp = timestamp
        record.tags = SmartTag.get_tags(sigfox_ep_id)
        record.limited_retention = True
        # All frames have the same length.
        if (len(ul_payload) == (2 * SMARTTAG_UL_PAYLOAD_SIZE)):
            # Init data.
            lpi = SMARTTAG_ERROR_VALUE_LPI
            fuse_event_period_counter = SMARTTAG_ERROR_VALUE_FUSE_EVENT_PERIOD_COUNTER
            temperature = SMARTTAG_ERROR_VALUE_TEMPERATURE
            humidity = SMARTTAG_ERROR_VALUE_HUMIDITY
            lux = SMARTTAG_ERROR_VALUE_LUX
            fuse_flag = SMARTTAG_ERROR_VALUE_FUSE_FLAG
            high_threshold_event_count = SMARTTAG_ERROR_VALUE_EVENT_COUNT
            high_threshold_interrupt_count = SMARTTAG_ERROR_VALUE_INTERRUPT_COUNT
            high_threshold_x_flag = SMARTTAG_ERROR_VALUE_AXIS_FLAG
            high_threshold_y_flag = SMARTTAG_ERROR_VALUE_AXIS_FLAG
            high_threshold_z_flag = SMARTTAG_ERROR_VALUE_AXIS_FLAG
            low_threshold_event_count = SMARTTAG_ERROR_VALUE_EVENT_COUNT
            low_threshold_interrupt_count = SMARTTAG_ERROR_VALUE_INTERRUPT_COUNT
            low_threshold_x_flag = SMARTTAG_ERROR_VALUE_AXIS_FLAG
            low_threshold_y_flag = SMARTTAG_ERROR_VALUE_AXIS_FLAG
            low_threshold_z_flag = SMARTTAG_ERROR_VALUE_AXIS_FLAG
            # Parse header.
            header = ((int(ul_payload[0:2], 16) >> 4) & 0x0F)
            # Periodic temperature / humidity / light.
            if (header == SMARTTAG_HEADER_PERIODIC_TEMP_HUM_LUX):
                # Set message type.
                data_type = DatabaseFieldDataType.PERIODIC_MONITORING.value
                # Parse fields.
                lpi = ((int(ul_payload[0:2], 16) >> 3) & 0x01)
                fuse_event_period_counter = ((int(ul_payload[0:2], 16) >> 0) & 0x07)
                temperature = int(ul_payload[2:4], 16)
                humidity = int(ul_payload[4:6], 16)
                lux = int(ul_payload[6:8], 16)
            # Periodic temperature / humidity / accelerometer data.
            elif (header == SMARTTAG_HEADER_PERIODIC_TEMP_HUM_ACC):
                # Set message type.
                data_type = DatabaseFieldDataType.PERIODIC_MONITORING.value
                # Parse fields.
                lpi = ((int(ul_payload[0:2], 16) >> 3) & 0x01)
                fuse_event_period_counter = ((int(ul_payload[0:2], 16) >> 0) & 0x07)
                temperature = int(ul_payload[2:4], 16)
                humidity = int(ul_payload[4:6], 16)
                motion_history = int(ul_payload[6:8], 16)
                high_threshold_event_count = ((motion_history >> 4) & 0x0F)
                low_threshold_event_count = ((motion_history >> 0) & 0x0F)
            # Start, stop; button and light events.
            elif ((header == SMARTTAG_HEADER_EVENT_ON) or (header == SMARTTAG_HEADER_EVENT_OFF) or (header == SMARTTAG_HEADER_EVENT_BUTTON) or (header == SMARTTAG_HEADER_EVENT_FUSE)):
                # Set message type.
                if (header == SMARTTAG_HEADER_EVENT_ON):
                    data_type = DatabaseFieldDataType.EVENT_STARTUP.value
                elif (header == SMARTTAG_HEADER_EVENT_OFF):
                    data_type = DatabaseFieldDataType.EVENT_SHUTDOWN.value
                elif (header == SMARTTAG_HEADER_EVENT_BUTTON):
                    data_type = DatabaseFieldDataType.EVENT_BUTTON.value
                else:
                    data_type = DatabaseFieldDataType.EVENT_FUSE.value
                # Parse fields.
                lpi = ((int(ul_payload[0:2], 16) >> 3) & 0x01)
                fuse_event_period_counter = ((int(ul_payload[0:2], 16) >> 0) & 0x07)
                temperature = int(ul_payload[2:4], 16)
                humidity = int(ul_payload[4:6], 16)
                lux = int(ul_payload[6:8], 16)
            # Accelerometer event.
            elif (header == SMARTTAG_HEADER_EVENT_ACC):
                # Parse fields.
                lpi = ((int(ul_payload[0:2], 16) >> 3) & 0x01)
                fuse_flag = ((int(ul_payload[0:2], 16) >> 2) & 0x01)
                temperature = int(ul_payload[2:4], 16)
                high_threshold_event = int(ul_payload[4:6], 16)
                high_threshold_interrupt_count = ((high_threshold_event >> 0) & 0x1F)
                high_threshold_x_flag = ((high_threshold_event >> 5) & 0x01)
                high_threshold_y_flag = ((high_threshold_event >> 6) & 0x01)
                high_threshold_z_flag = ((high_threshold_event >> 7) & 0x01)
                low_threshold_event = int(ul_payload[6:8], 16)
                low_threshold_interrupt_count = ((low_threshold_event >> 0) & 0x1F)
                low_threshold_x_flag = ((low_threshold_event >> 5) & 0x01)
                low_threshold_y_flag = ((low_threshold_event >> 6) & 0x01)
                low_threshold_z_flag = ((low_threshold_event >> 7) & 0x01)
                # Set message type.
                if ((high_threshold_event == 0) and (low_threshold_event == 0)):
                    data_type = DatabaseFieldDataType.EVENT_ACCELEROMETER_STOP.value
                else:
                    data_type = DatabaseFieldDataType.EVENT_ACCELEROMETER_START.value
            else:
                Log.debug_print("[SMARTTAG] * Invalid UL payload header")
                return record_list
            # Create monitoring record.
            record.measurement = DATABASE_MEASUREMENT_MONITORING
            record.fields = {
                DATABASE_FIELD_LAST_DATA_TIME: timestamp
            }
            record.add_field(lpi, SMARTTAG_ERROR_VALUE_LPI, DATABASE_FIELD_STORAGE_VOLTAGE_LOW_FLAG, lpi)
            record.add_field(fuse_event_period_counter, SMARTTAG_ERROR_VALUE_FUSE_EVENT_PERIOD_COUNTER, DATABASE_FIELD_FUSE_EVENT_PERIOD_COUNTER, fuse_event_period_counter)
            record_list.append(copy.copy(record))
            # Create sensor record.
            record.measurement = DATABASE_MEASUREMENT_SENSOR
            record.fields = {
                DATABASE_FIELD_LAST_DATA_TIME: timestamp
            }
            record.add_field(temperature, SMARTTAG_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_TEMPERATURE, float((temperature / 2.0) - 20.0))
            record.add_field(humidity, SMARTTAG_ERROR_VALUE_HUMIDITY, DATABASE_FIELD_HUMIDITY, float(humidity / 2.0))
            record.add_field(lux, SMARTTAG_ERROR_VALUE_LUX, DATABASE_FIELD_LIGHT, float(lux))
            record.add_field(fuse_flag, SMARTTAG_ERROR_VALUE_FUSE_FLAG, DATABASE_FIELD_FUSE_FLAG, fuse_flag)
            record.add_field(high_threshold_event_count, SMARTTAG_ERROR_VALUE_EVENT_COUNT, DATABASE_FIELD_ACCELEROMETER_HIGH_THRESHOLD_EVENT_COUNT, high_threshold_event_count)
            record.add_field(high_threshold_interrupt_count, SMARTTAG_ERROR_VALUE_INTERRUPT_COUNT, DATABASE_FIELD_ACCELEROMETER_HIGH_THRESHOLD_INTERRUPT_COUNT, high_threshold_interrupt_count)
            record.add_field(high_threshold_x_flag, SMARTTAG_ERROR_VALUE_AXIS_FLAG, DATABASE_FIELD_ACCELEROMETER_HIGH_THRESHOLD_X_FLAG, high_threshold_x_flag)
            record.add_field(high_threshold_y_flag, SMARTTAG_ERROR_VALUE_AXIS_FLAG, DATABASE_FIELD_ACCELEROMETER_HIGH_THRESHOLD_Y_FLAG, high_threshold_y_flag)
            record.add_field(high_threshold_z_flag, SMARTTAG_ERROR_VALUE_AXIS_FLAG, DATABASE_FIELD_ACCELEROMETER_HIGH_THRESHOLD_Z_FLAG, high_threshold_z_flag)
            record.add_field(low_threshold_event_count, SMARTTAG_ERROR_VALUE_EVENT_COUNT, DATABASE_FIELD_ACCELEROMETER_LOW_THRESHOLD_EVENT_COUNT, low_threshold_event_count)
            record.add_field(low_threshold_interrupt_count, SMARTTAG_ERROR_VALUE_INTERRUPT_COUNT, DATABASE_FIELD_ACCELEROMETER_LOW_THRESHOLD_INTERRUPT_COUNT, low_threshold_interrupt_count)
            record.add_field(low_threshold_x_flag, SMARTTAG_ERROR_VALUE_AXIS_FLAG, DATABASE_FIELD_ACCELEROMETER_LOW_THRESHOLD_X_FLAG, low_threshold_x_flag)
            record.add_field(low_threshold_y_flag, SMARTTAG_ERROR_VALUE_AXIS_FLAG, DATABASE_FIELD_ACCELEROMETER_LOW_THRESHOLD_Y_FLAG, low_threshold_y_flag)
            record.add_field(low_threshold_z_flag, SMARTTAG_ERROR_VALUE_AXIS_FLAG, DATABASE_FIELD_ACCELEROMETER_LOW_THRESHOLD_Z_FLAG, low_threshold_z_flag)
            record_list.append(copy.copy(record))
        else:
            Log.debug_print("[SMARTTAG] * Invalid UL payload")
        return [data_type, record_list]
    
    @staticmethod
    def get_default_dl_payload(sigfox_ep_id: str) -> str:
        # Local variables.
        dl_payload = []
        # Unused parameter.
        _ = sigfox_ep_id
        # No downlink payload defined.
        return dl_payload

    @staticmethod
    def update_dl_payload(sigfox_ep_id: str, dl_payload: str) -> str:
        # Unused parameter.
        _ = sigfox_ep_id
        # No dynamic payload used.
        return dl_payload
