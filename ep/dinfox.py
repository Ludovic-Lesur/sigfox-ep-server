"""
* dinfox.py
*
*  Created on: 29 apr. 2023
*      Author: Ludo
"""

from database.database import *
from ep.common import *
from log import *

### DINFOX public macros ###

DINFOX_SIGFOX_EP_ID_LIST = [ "4761", "479C", "47A7", "47EA", "4894" ]

### DINFOX local macros ###

DINFOX_TAG_SYSTEM = [ "Test_bench", "Prat_Albis", "Solar_rack", "Mains_rack", "Linky_rack" ]

DINFOX_NODE_NAME = [ "LVRM", "BPSM", "DDRM", "UHFM", "GPSM", "SM", "DIM", "RRM", "DMM", "MPMCM", "R4S8CR", "BCM" ]

DINFOX_BOARD_ID_LVRM = 0
DINFOX_BOARD_ID_BPSM = 1
DINFOX_BOARD_ID_DDRM = 2
DINFOX_BOARD_ID_UHFM = 3
DINFOX_BOARD_ID_GPSM = 4
DINFOX_BOARD_ID_SM = 5
DINFOX_BOARD_ID_DIM = 6
DINFOX_BOARD_ID_RRM = 7
DINFOX_BOARD_ID_DMM = 8
DINFOX_BOARD_ID_MPMCM = 9
DINFOX_BOARD_ID_R4S8CR = 10
DINFOX_BOARD_ID_BCM = 11
DINFOX_BOARD_ID_LAST = 12

DINFOX_UL_PAYLOAD_HEADER_SIZE = 2

DINFOX_LVRM_UL_PAYLOAD_SIZE_MONITORING = 4
DINFOX_LVRM_UL_PAYLOAD_SIZE_ELECTRICAL = 7

DINFOX_BPSM_UL_PAYLOAD_SIZE_MONITORING = 4
DINFOX_BPSM_UL_PAYLOAD_SIZE_ELECTRICAL = 7

DINFOX_DDRM_UL_PAYLOAD_SIZE_MONITORING = 4
DINFOX_DDRM_UL_PAYLOAD_SIZE_ELECTRICAL = 7

DINFOX_UHFM_UL_PAYLOAD_SIZE_MONITORING = 9

DINFOX_GPSM_UL_PAYLOAD_SIZE_MONITORING = 9

DINFOX_SM_UL_PAYLOAD_SIZE_MONITORING = 4
DINFOX_SM_UL_PAYLOAD_SIZE_ELECTRICAL = 9
DINFOX_SM_UL_PAYLOAD_SIZE_SENSOR = 3

DINFOX_DMM_UL_PAYLOAD_SIZE_MONITORING = 7

DINFOX_MPMCM_UL_PAYLOAD_SIZE_STATUS = 1
DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_POWER_FACTOR = 4
DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_ENERGY = 5
DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_FREQUENCY = 6
DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_VOLTAGE = 7
DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_POWER = 9

DINFOX_R4S8CR_UL_PAYLOAD_SIZE_ELECTRICAL = 2

DINFOX_BCM_UL_PAYLOAD_SIZE_MONITORING = 4
DINFOX_BCM_UL_PAYLOAD_SIZE_ELECTRICAL = 9

DINFOX_UL_PAYLOAD_SIZE_ERROR_STACK = 10

DINFOX_UNA_BIT_0 = 0
DINFOX_UNA_BIT_1 = 1
DINFOX_UNA_BIT_HW = 2
DINFOX_UNA_BIT_ERROR = 3

DINFOX_BCM_CHRGST_NOT_CHARGING_TERMINATED = 0
DINFOX_BCM_CHRGST_CHARGING_CC = 1
DINFOX_BCM_CHRGST_CHARGING_CV = 2
DINFOX_BCM_CHRGST_FAULT = 3,
DINFOX_BCM_CHRGST_HW = 4,
DINFOX_BCM_CHRGST_ERROR = 5

DINFOX_ERROR_VALUE_TIME = 0xFF
DINFOX_ERROR_VALUE_TEMPERATURE = 0x7FF
DINFOX_ERROR_VALUE_HUMIDITY = 0xFF
DINFOX_ERROR_VALUE_VOLTAGE = 0xFFFF
DINFOX_ERROR_VALUE_CURRENT = 0xFFFF
DINFOX_ERROR_VALUE_ELECTRICAL_POWER = 0x7FFF
DINFOX_ERROR_VALUE_ELECTRICAL_ENERGY = 0x7FFF
DINFOX_ERROR_VALUE_POWER_FACTOR = 0x7F
DINFOX_ERROR_VALUE_FREQUENCY = 0xFFFF
DINFOX_ERROR_VALUE_RF_POWER = 0xFF
DINFOX_ERROR_VALUE_YEAR = 0xFF

### DINFOX classes ###

class DINFox:

    @staticmethod
    def _get_temperature(dinfox_temperature: int) -> float:
        # Reset result.
        temperature_tenth_degrees = DINFOX_ERROR_VALUE_TEMPERATURE
        # Check error value.
        if (dinfox_temperature != DINFOX_ERROR_VALUE_TEMPERATURE):
            temperature_tenth_degrees = Common.one_complement_to_value(dinfox_temperature, 11)
        return float(temperature_tenth_degrees / 10.0)
    
    @staticmethod
    def _get_voltage(dinfox_voltage: int) -> float:
        # Reset result.
        voltage_mv = DINFOX_ERROR_VALUE_VOLTAGE
        # Check error value.
        if (dinfox_voltage != DINFOX_ERROR_VALUE_VOLTAGE):
            # Extract unit and value.
            unit = ((dinfox_voltage >> 15) & 0x0001)
            value = ((dinfox_voltage >> 0) & 0x7FFF)
            # Convert.
            if (unit == 0):
                voltage_mv = (value * 1)
            else:
                voltage_mv = (value * 100)
        return float(voltage_mv / 1000.0)
    
    @staticmethod
    def _get_current(dinfox_current: int) -> float:
        # Reset result.
        current_ua = DINFOX_ERROR_VALUE_CURRENT
        # Check error value.
        if (dinfox_current != DINFOX_ERROR_VALUE_CURRENT):
            # Extract unit and value.
            unit = ((dinfox_current >> 14) & 0x0003)
            value = ((dinfox_current >> 0) & 0x3FFF)
            # Convert.
            if (unit == 0):
                current_ua = (value * 1)
            elif (unit == 1):
                current_ua = (value * 100)
            elif (unit == 2):
                current_ua = (value * 1000)
            else:
                current_ua = (value * 100000)
        return float(current_ua / 1000000.0)
    
    @staticmethod
    def _get_electrical_power(dinfox_electrical_power: int) -> float:
        # Reset result.
        electrical_power_mw_mva = DINFOX_ERROR_VALUE_ELECTRICAL_POWER
        # Check error value.
        if (dinfox_electrical_power != DINFOX_ERROR_VALUE_ELECTRICAL_POWER):
            # Extract sign, unit and value.
            sign = ((dinfox_electrical_power >> 15) & 0x0001)
            unit = ((dinfox_electrical_power >> 13) & 0x0003)
            value = ((dinfox_electrical_power >> 0) & 0x1FFF)
            # Convert.
            if (unit == 0):
                electrical_power_mw_mva = ((-1) ** (sign)) * (value * 1)
            elif (unit == 1):
                electrical_power_mw_mva = ((-1) ** (sign)) * (value * 100)
            elif (unit == 2):
                electrical_power_mw_mva = ((-1) ** (sign)) * (value * 1000)
            else:
                electrical_power_mw_mva = ((-1) ** (sign)) * (value * 100000)
        return float(electrical_power_mw_mva / 1000.0)
    
    @staticmethod
    def _get_electrical_energy(dinfox_electrical_energy: int) -> float:
        # Reset result.
        electrical_energy_mwh_mvah = DINFOX_ERROR_VALUE_ELECTRICAL_ENERGY
        # Check error value.
        if (dinfox_electrical_energy != DINFOX_ERROR_VALUE_ELECTRICAL_ENERGY):
            # Extract sign, unit and value.
            sign = ((dinfox_electrical_energy >> 15) & 0x0001)
            unit = ((dinfox_electrical_energy >> 13) & 0x0003)
            value = ((dinfox_electrical_energy >> 0) & 0x1FFF)
            # Convert.
            if (unit == 0):
                electrical_energy_mwh_mvah = ((-1) ** (sign)) * (value * 1)
            elif (unit == 1):
                electrical_energy_mwh_mvah = ((-1) ** (sign)) * (value * 100)
            elif (unit == 2):
                electrical_energy_mwh_mvah = ((-1) ** (sign)) * (value * 1000)
            else:
                electrical_energy_mwh_mvah = ((-1) ** (sign)) * (value * 100000)
        return float(electrical_energy_mwh_mvah / 1000.0)
    
    @staticmethod
    def _get_power_factor(dinfox_power_factor: int) -> float:
        # Reset result.
        power_factor = DINFOX_ERROR_VALUE_POWER_FACTOR
        # Check error value.
        if (dinfox_power_factor != DINFOX_ERROR_VALUE_POWER_FACTOR):
            # Extract sign and value.
            sign = ((dinfox_power_factor >> 7) & 0x01)
            value = ((dinfox_power_factor >> 0) & 0x7F)
            # Convert.
            power_factor = ((-1) ** (sign)) * (value / 100.0)
        return float(power_factor)
    
    @staticmethod
    def _get_system(sigfox_ep_id: str) -> str:
        # Default is unknown.
        system_name = COMMON_UNKNOWN
        if (sigfox_ep_id in DINFOX_SIGFOX_EP_ID_LIST):
            # Get system name.
            system_name = DINFOX_TAG_SYSTEM[DINFOX_SIGFOX_EP_ID_LIST.index(sigfox_ep_id)]
        return system_name
    
    @staticmethod
    def _get_node_name(board_id: int) -> str:
        # Default is unknown.
        node_name = COMMON_UNKNOWN
        # Check board ID.
        if (board_id < DINFOX_BOARD_ID_LAST):
            node_name = DINFOX_NODE_NAME[board_id]
        return node_name
    
    @staticmethod
    def _get_tags(sigfox_ep_id: str, node_address: int, board_id: int) -> Dict[str, Any]:
        # Local variables.
        tags = DINFox.get_tags(sigfox_ep_id)
        # Add specific tags.
        tags[DATABASE_TAG_NODE_ADDRESS] = node_address
        tags[DATABASE_TAG_NODE] = DINFox._get_node_name(board_id)
        tags[DATABASE_TAG_BOARD_ID] = board_id
        return tags
    
    @staticmethod
    def get_tags(sigfox_ep_id: str) -> Dict[str, Any]:
        # Local variables.
        tags = {
            DATABASE_TAG_SIGFOX_EP_ID: sigfox_ep_id,
            DATABASE_TAG_SYSTEM: DINFox._get_system(sigfox_ep_id)
        }
        return tags
    
    @staticmethod
    def get_record_list(database: Database, timestamp: int, sigfox_ep_id: str, ul_payload: str) -> List[Record]:
        # Local variables.
        record_list = []
        record = Record()
        mpmcm_channel_index = 0
        # Unused parameter.
        _ = database
        # Read node address and board ID.
        node_address = int(ul_payload[0:2], 16)
        board_id = int(ul_payload[2:4], 16)
        # Common properties.
        record.database = DATABASE_DINFOX
        record.timestamp = timestamp
        record.tags = DINFox._get_tags(sigfox_ep_id, node_address, board_id)
        record.limited_retention = True
        # Extract node payload.
        node_ul_payload = ul_payload[(2 * DINFOX_UL_PAYLOAD_HEADER_SIZE):]
        node_ul_payload_size = len(ul_payload) - (2 * DINFOX_UL_PAYLOAD_HEADER_SIZE)
        # Startup or action log frame.
        if (node_ul_payload_size == (2 * COMMON_UL_PAYLOAD_SIZE_STARTUP)):
            # Check marker to select between startup or action log.
            marker = ((int(node_ul_payload[0:2], 16) >> 4) & 0x0F);
            if (marker == 0x0F):
                # Action log frame.
                downlink_hash = (int(node_ul_payload[0:4], 16) & 0x0FFF);
                register_address = int(node_ul_payload[4:6], 16)
                register_value = int(node_ul_payload[6:14], 16)
                node_access_status = int(node_ul_payload[14:16], 16)
                # Create record.
                record.measurement = DATABASE_MEASUREMENT_SIGFOX_DOWNLINK
                record.fields = {
                    DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                    DATABASE_FIELD_SIGFOX_DOWNLINK_HASH: downlink_hash,
                    DATABASE_FIELD_NODE_REGISTER_ADDRESS: register_address,
                    DATABASE_FIELD_NODE_REGISTER_VALUE: register_value,
                    DATABASE_FIELD_NODE_ACCESS_STATUS: node_access_status
                }
                record_list.append(copy.copy(record))
            else:
                Common.get_record_startup(record, timestamp, node_ul_payload, record_list)
        # Error stack frame.
        elif (node_ul_payload_size == (2 * DINFOX_UL_PAYLOAD_SIZE_ERROR_STACK)):
            Common.get_record_error_stack(record, timestamp, node_ul_payload, (DINFOX_UL_PAYLOAD_SIZE_ERROR_STACK // 2), record_list)
        # Node-specific frames.
        else:
            # LVRM.
            if (board_id == DINFOX_BOARD_ID_LVRM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_LVRM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    mcu_voltage_dinfox = int(node_ul_payload[0:4], 16)
                    mcu_temperature_dinfox = int(node_ul_payload[4:8], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(mcu_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, DINFox._get_voltage(mcu_voltage_dinfox))
                    record.add_field(mcu_temperature_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, DINFox._get_temperature(mcu_temperature_dinfox))
                    record_list.append(copy.copy(record))
                # Electrical frame.
                elif (node_ul_payload_size == (2 * DINFOX_LVRM_UL_PAYLOAD_SIZE_ELECTRICAL)):
                    # Parse field.
                    input_voltage_dinfox = int(node_ul_payload[0:4], 16)
                    output_voltage_dinfox = int(node_ul_payload[4:8], 16)
                    output_current_dinfox = int(node_ul_payload[8:12], 16)
                    relay_control_state = ((int(node_ul_payload[12:14], 16) >> 0) & 0x03)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_RELAY_CONTROL_STATE: relay_control_state
                    }
                    record.add_field(input_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_INPUT_VOLTAGE, DINFox._get_voltage(input_voltage_dinfox))
                    record.add_field(output_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_OUTPUT_VOLTAGE, DINFox._get_voltage(output_voltage_dinfox))
                    record.add_field(output_current_dinfox, DINFOX_ERROR_VALUE_CURRENT, DATABASE_FIELD_OUTPUT_CURRENT, DINFox._get_current(output_current_dinfox))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX LVRM] * Invalid UL payload")
            # BPSM.
            elif (board_id == DINFOX_BOARD_ID_BPSM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_BPSM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    mcu_voltage_dinfox = int(node_ul_payload[0:4], 16)
                    mcu_temperature_dinfox = int(node_ul_payload[4:8], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(mcu_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, DINFox._get_voltage(mcu_voltage_dinfox))
                    record.add_field(mcu_temperature_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, DINFox._get_temperature(mcu_temperature_dinfox))
                    record_list.append(copy.copy(record))
                # Electrical frame.
                elif (node_ul_payload_size == (2 * DINFOX_BPSM_UL_PAYLOAD_SIZE_ELECTRICAL)):
                    # Parse fields.
                    source_voltage_dinfox = int(node_ul_payload[0:4], 16)
                    storage_voltage_dinfox = int(node_ul_payload[4:8], 16)
                    backup_voltage_dinfox = int(node_ul_payload[8:12], 16)
                    charge_status = ((int(node_ul_payload[12:14], 16) >> 4) & 0x03)
                    charge_control_state = ((int(node_ul_payload[12:14], 16) >> 2) & 0x03)
                    backup_control_state = ((int(node_ul_payload[12:14], 16) >> 0) & 0x03)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_CHARGE_STATUS: charge_status,
                        DATABASE_FIELD_CHARGE_CONTROL_STATE: charge_control_state,
                        DATABASE_FIELD_BACKUP_CONTROL_STATE: backup_control_state
                    }
                    record.add_field(source_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_SOURCE_VOLTAGE, DINFox._get_voltage(source_voltage_dinfox))
                    record.add_field(storage_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_STORAGE_VOLTAGE, DINFox._get_voltage(storage_voltage_dinfox))
                    record.add_field(backup_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_BACKUP_VOLTAGE, DINFox._get_voltage(backup_voltage_dinfox))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX BPSM] * Invalid UL payload")
            # DDRM.
            elif (board_id == DINFOX_BOARD_ID_DDRM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_DDRM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    mcu_voltage_dinfox = int(node_ul_payload[0:4], 16)
                    mcu_temperature_dinfox = int(node_ul_payload[4:8], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(mcu_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, DINFox._get_voltage(mcu_voltage_dinfox))
                    record.add_field(mcu_temperature_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, DINFox._get_temperature(mcu_temperature_dinfox))
                    record_list.append(copy.copy(record))
                # Electrical frame.
                elif (node_ul_payload_size == (2 * DINFOX_DDRM_UL_PAYLOAD_SIZE_ELECTRICAL)):
                    # Parse field.
                    input_voltage_dinfox = int(node_ul_payload[0:4], 16)
                    output_voltage_dinfox = int(node_ul_payload[4:8], 16)
                    output_current_dinfox = int(node_ul_payload[8:12], 16)
                    regulator_control_state = ((int(node_ul_payload[12:14], 16) >> 0) & 0x03)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_REGULATOR_CONTROL_STATE: regulator_control_state
                    }
                    record.add_field(input_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_INPUT_VOLTAGE, DINFox._get_voltage(input_voltage_dinfox))
                    record.add_field(output_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_OUTPUT_VOLTAGE, DINFox._get_voltage(output_voltage_dinfox))
                    record.add_field(output_current_dinfox, DINFOX_ERROR_VALUE_CURRENT, DATABASE_FIELD_OUTPUT_CURRENT, DINFox._get_current(output_current_dinfox))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX DDRM] * Invalid UL payload")
            # UHFM.
            elif (board_id == DINFOX_BOARD_ID_UHFM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_UHFM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    mcu_voltage_dinfox = int(node_ul_payload[0:4], 16)
                    mcu_temperature_dinfox = int(node_ul_payload[4:8], 16)
                    radio_tx_voltage_dinfox = int(node_ul_payload[8:12], 16)
                    radio_rx_voltage_dinfox = int(node_ul_payload[12:16], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(mcu_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, DINFox._get_voltage(mcu_voltage_dinfox))
                    record.add_field(mcu_temperature_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, DINFox._get_temperature(mcu_temperature_dinfox))
                    record.add_field(radio_tx_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_RADIO_TX_VOLTAGE, DINFox._get_voltage(radio_tx_voltage_dinfox))
                    record.add_field(radio_rx_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_RADIO_RX_VOLTAGE, DINFox._get_voltage(radio_rx_voltage_dinfox))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX UHFM] * Invalid UL payload")
            # GPSM.
            elif (board_id == DINFOX_BOARD_ID_GPSM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_GPSM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    mcu_voltage_dinfox = int(node_ul_payload[0:4], 16)
                    mcu_temperature_dinfox = int(node_ul_payload[4:8], 16)
                    gps_voltage_dinfox = int(node_ul_payload[8:12], 16)
                    antenna_voltage_dinfox = int(node_ul_payload[12:16], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(mcu_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, DINFox._get_voltage(mcu_voltage_dinfox))
                    record.add_field(mcu_temperature_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, DINFox._get_temperature(mcu_temperature_dinfox))
                    record.add_field(gps_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_GPS_VOLTAGE, DINFox._get_voltage(gps_voltage_dinfox))
                    record.add_field(antenna_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_GPS_ANTENNA_VOLTAGE, DINFox._get_voltage(antenna_voltage_dinfox))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX GPSM] * Invalid UL payload")
            # SM.
            elif (board_id == DINFOX_BOARD_ID_SM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_SM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    mcu_voltage_dinfox = int(node_ul_payload[0:4], 16)
                    mcu_temperature_dinfox = int(node_ul_payload[4:8], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(mcu_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, DINFox._get_voltage(mcu_voltage_dinfox))
                    record.add_field(mcu_temperature_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, DINFox._get_temperature(mcu_temperature_dinfox))
                    record_list.append(copy.copy(record))
                # Electrical frame.
                if (node_ul_payload_size == (2 * DINFOX_SM_UL_PAYLOAD_SIZE_ELECTRICAL)):
                    # Parse fields.
                    ain0_dinfox = int(node_ul_payload[0:4], 16)
                    ain1_dinfox = int(node_ul_payload[4:8], 16)
                    ain2_dinfox = int(node_ul_payload[8:12], 16)
                    ain3_dinfox = int(node_ul_payload[12:16], 16)
                    dio0 = ((int(node_ul_payload[16:18], 16) >> 0) & 0x03)
                    dio1 = ((int(node_ul_payload[16:18], 16) >> 2) & 0x03)
                    dio2 = ((int(node_ul_payload[16:18], 16) >> 4) & 0x03)
                    dio3 = ((int(node_ul_payload[16:18], 16) >> 6) & 0x03)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_DIO0_STATE: dio0,
                        DATABASE_FIELD_DIO1_STATE: dio1,
                        DATABASE_FIELD_DIO2_STATE: dio2,
                        DATABASE_FIELD_DIO3_STATE: dio3
                    }
                    record.add_field(ain0_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_AIN0_VOLTAGE, DINFox._get_voltage(ain0_dinfox))
                    record.add_field(ain1_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_AIN1_VOLTAGE, DINFox._get_voltage(ain1_dinfox))
                    record.add_field(ain2_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_AIN2_VOLTAGE, DINFox._get_voltage(ain2_dinfox))
                    record.add_field(ain3_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_AIN3_VOLTAGE, DINFox._get_voltage(ain3_dinfox))
                    record_list.append(copy.copy(record))
                # Digital sensors frame.
                elif (node_ul_payload_size == (2 * DINFOX_SM_UL_PAYLOAD_SIZE_SENSOR)):
                    # Parse fields.
                    temperature_dinfox = int(node_ul_payload[0:4], 16)
                    humidity_percent = int(node_ul_payload[4:6], 16)
                    # Create sensor record.
                    record.measurement = DATABASE_MEASUREMENT_SENSOR
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                    }
                    record.add_field(temperature_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_TEMPERATURE, DINFox._get_temperature(temperature_dinfox))
                    record.add_field(humidity_percent, DINFOX_ERROR_VALUE_HUMIDITY, DATABASE_FIELD_HUMIDITY, float(humidity_percent))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX SM] * Invalid UL payload")
            # DMM.
            elif (board_id == DINFOX_BOARD_ID_DMM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_DMM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    rs485_bus_voltage_dinfox = int(node_ul_payload[0:4], 16)
                    hmi_voltage_dinfox = int(node_ul_payload[4:8], 16)
                    usb_voltage_dinfox = int(node_ul_payload[8:12], 16)
                    node_count = int(node_ul_payload[12:14], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_NODE_COUNT: node_count
                    }
                    record.add_field(rs485_bus_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_RS485_BUS_VOLTAGE, DINFox._get_voltage(rs485_bus_voltage_dinfox))
                    record.add_field(hmi_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_HMI_VOLTAGE, DINFox._get_voltage(hmi_voltage_dinfox))
                    record.add_field(usb_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_USB_VOLTAGE, DINFox._get_voltage(usb_voltage_dinfox))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX DMM] * Invalid UL payload")
            # MPMCM.
            elif (board_id == DINFOX_BOARD_ID_MPMCM):
                # Status frame.
                if (node_ul_payload_size == (2 * DINFOX_MPMCM_UL_PAYLOAD_SIZE_STATUS)):
                    # Parse fields.
                    mains_voltage_detect = ((int(node_ul_payload[0:2], 16) >> 5) & 0x01)
                    mains_linky_tic_detect = ((int(node_ul_payload[0:2], 16) >> 4) & 0x01)
                    mains_current_detect_ch4 = ((int(node_ul_payload[0:2], 16) >> 3) & 0x01)
                    mains_current_detect_ch3 = ((int(node_ul_payload[0:2], 16) >> 2) & 0x01)
                    mains_current_detect_ch2 = ((int(node_ul_payload[0:2], 16) >> 1) & 0x01)
                    mains_current_detect_ch1 = ((int(node_ul_payload[0:2], 16) >> 0) & 0x01)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_MAINS_VOLTAGE_DETECT: mains_voltage_detect,
                        DATABASE_FIELD_MAINS_LINKY_TIC_DETECT: mains_linky_tic_detect,
                        DATABASE_FIELD_MAINS_CURRENT_DETECT_CH1: mains_current_detect_ch1,
                        DATABASE_FIELD_MAINS_CURRENT_DETECT_CH2: mains_current_detect_ch2,
                        DATABASE_FIELD_MAINS_CURRENT_DETECT_CH3: mains_current_detect_ch3,
                        DATABASE_FIELD_MAINS_CURRENT_DETECT_CH4: mains_current_detect_ch4,
                    }
                    record_list.append(copy.copy(record))
                # Mains voltage frame.
                elif (node_ul_payload_size == (2 * DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_VOLTAGE)):
                    # Parse fields.
                    mains_voltage_rms_min_dinfox = int(node_ul_payload[2:6], 16)
                    mains_voltage_rms_mean_dinfox = int(node_ul_payload[6:10], 16)
                    mains_voltage_rms_max_dinfox = int(node_ul_payload[10:14], 16)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                    }
                    record.add_field(mains_voltage_rms_min_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MAINS_VOLTAGE_RMS_MIN, DINFox._get_voltage(mains_voltage_rms_min_dinfox))
                    record.add_field(mains_voltage_rms_mean_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MAINS_VOLTAGE_RMS_MEAN, DINFox._get_voltage(mains_voltage_rms_mean_dinfox))
                    record.add_field(mains_voltage_rms_max_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MAINS_VOLTAGE_RMS_MAX, DINFox._get_voltage(mains_voltage_rms_max_dinfox))
                    record_list.append(copy.copy(record))
                # Mains frequency frame.
                elif (node_ul_payload_size == (2 * DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_FREQUENCY)):
                    # Parse fields.
                    mains_frequency_min_chz = int(node_ul_payload[0:4], 16)
                    mains_frequency_mean_chz = int(node_ul_payload[4:8], 16)
                    mains_frequency_max_chz = int(node_ul_payload[8:12], 16)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                    }
                    record.add_field(mains_frequency_min_chz, DINFOX_ERROR_VALUE_FREQUENCY, DATABASE_FIELD_MAINS_FREQUENCY_MIN, float(mains_frequency_min_chz / 100.0))
                    record.add_field(mains_frequency_mean_chz, DINFOX_ERROR_VALUE_FREQUENCY, DATABASE_FIELD_MAINS_FREQUENCY_MEAN, float(mains_frequency_mean_chz / 100.0))
                    record.add_field(mains_frequency_max_chz, DINFOX_ERROR_VALUE_FREQUENCY, DATABASE_FIELD_MAINS_FREQUENCY_MAX, float(mains_frequency_max_chz / 100.0))
                    record_list.append(copy.copy(record))
                # Mains power frame.
                elif (node_ul_payload_size == (2 * DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_POWER)):
                    # Parse fields.
                    mpmcm_channel_index = ((int(node_ul_payload[0:2], 16) >> 0) & 0x07)
                    mains_active_power_mean_dinfox = int(node_ul_payload[2:6], 16)
                    mains_active_power_max_dinfox = int(node_ul_payload[6:10], 16)
                    mains_apparent_power_mean_dinfox = int(node_ul_payload[10:14], 16)
                    mains_apparent_power_max_dinfox = int(node_ul_payload[14:18], 16)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                    }
                    record.add_field(mains_active_power_mean_dinfox, DINFOX_ERROR_VALUE_ELECTRICAL_POWER, DATABASE_FIELD_MAINS_ACTIVE_POWER_MEAN, DINFox._get_electrical_power(mains_active_power_mean_dinfox))
                    record.add_field(mains_active_power_max_dinfox, DINFOX_ERROR_VALUE_ELECTRICAL_POWER, DATABASE_FIELD_MAINS_ACTIVE_POWER_MAX, DINFox._get_electrical_power(mains_active_power_max_dinfox))
                    record.add_field(mains_apparent_power_mean_dinfox, DINFOX_ERROR_VALUE_ELECTRICAL_POWER, DATABASE_FIELD_MAINS_APPARENT_POWER_MEAN, DINFox._get_electrical_power(mains_apparent_power_mean_dinfox))
                    record.add_field(mains_apparent_power_max_dinfox, DINFOX_ERROR_VALUE_ELECTRICAL_POWER, DATABASE_FIELD_MAINS_APPARENT_POWER_MAX, DINFox._get_electrical_power(mains_apparent_power_max_dinfox))
                    record.tags[DATABASE_TAG_CHANNEL] = mpmcm_channel_index
                    record_list.append(copy.copy(record))
                # Mains power factor frame.
                elif (node_ul_payload_size == (2 * DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_POWER_FACTOR)):
                    # Parse fields.
                    mpmcm_channel_index = ((int(node_ul_payload[0:2], 16) >> 0) & 0x07)
                    mains_power_factor_min_dinfox = int(node_ul_payload[2:4], 16)
                    mains_power_factor_mean_dinfox = int(node_ul_payload[4:6], 16)
                    mains_power_factor_max_dinfox = int(node_ul_payload[6:8], 16)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                    }
                    record.add_field(mains_power_factor_min_dinfox, DINFOX_ERROR_VALUE_POWER_FACTOR, DATABASE_FIELD_MAINS_POWER_FACTOR_MIN, DINFox._get_power_factor(mains_power_factor_min_dinfox))
                    record.add_field(mains_power_factor_mean_dinfox, DINFOX_ERROR_VALUE_POWER_FACTOR, DATABASE_FIELD_MAINS_POWER_FACTOR_MEAN, DINFox._get_power_factor(mains_power_factor_mean_dinfox))
                    record.add_field(mains_power_factor_max_dinfox, DINFOX_ERROR_VALUE_POWER_FACTOR, DATABASE_FIELD_MAINS_POWER_FACTOR_MAX, DINFox._get_power_factor(mains_power_factor_max_dinfox))
                    record.tags[DATABASE_TAG_CHANNEL] = mpmcm_channel_index
                    record_list.append(copy.copy(record))
                # Mains energy frame.
                elif (node_ul_payload_size == (2 * DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_ENERGY)):
                    # Parse fields.
                    mpmcm_channel_index = ((int(node_ul_payload[0:2], 16) >> 0) & 0x07)
                    mains_active_energy_dinfox = int(node_ul_payload[2:6], 16)
                    mains_apparent_energy_dinfox = int(node_ul_payload[6:10], 16)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                    }
                    record.add_field(mains_active_energy_dinfox, DINFOX_ERROR_VALUE_ELECTRICAL_ENERGY, DATABASE_FIELD_MAINS_ACTIVE_ENERGY, DINFox._get_electrical_energy(mains_active_energy_dinfox))
                    record.add_field(mains_apparent_energy_dinfox, DINFOX_ERROR_VALUE_ELECTRICAL_ENERGY, DATABASE_FIELD_MAINS_APPARENT_ENERGY, DINFox._get_electrical_energy(mains_apparent_energy_dinfox))
                    record.tags[DATABASE_TAG_CHANNEL] = mpmcm_channel_index
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX MPMCM] * Invalid UL payload")
            # R4S8CR.
            elif (board_id == DINFOX_BOARD_ID_R4S8CR):
                # Electrical frame.
                if (node_ul_payload_size == (2 * DINFOX_R4S8CR_UL_PAYLOAD_SIZE_ELECTRICAL)):
                    # Parse fields.
                    relay8_status = ((int(node_ul_payload[0:2], 16) >> 6) & 0x03)
                    relay7_status = ((int(node_ul_payload[0:2], 16) >> 4) & 0x03)
                    relay6_status = ((int(node_ul_payload[0:2], 16) >> 2) & 0x03)
                    relay5_status = ((int(node_ul_payload[0:2], 16) >> 0) & 0x03)
                    relay4_status = ((int(node_ul_payload[2:4], 16) >> 6) & 0x03)
                    relay3_status = ((int(node_ul_payload[2:4], 16) >> 4) & 0x03)
                    relay2_status = ((int(node_ul_payload[2:4], 16) >> 2) & 0x03)
                    relay1_status = ((int(node_ul_payload[2:4], 16) >> 0) & 0x03)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_RELAY1_STATUS: relay1_status,
                        DATABASE_FIELD_RELAY2_STATUS: relay2_status,
                        DATABASE_FIELD_RELAY3_STATUS: relay3_status,
                        DATABASE_FIELD_RELAY4_STATUS: relay4_status,
                        DATABASE_FIELD_RELAY5_STATUS: relay5_status,
                        DATABASE_FIELD_RELAY6_STATUS: relay6_status,
                        DATABASE_FIELD_RELAY7_STATUS: relay7_status,
                        DATABASE_FIELD_RELAY8_STATUS: relay8_status
                    }
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX R4S8CR] * Invalid UL payload")
            # BCM.
            elif (board_id == DINFOX_BOARD_ID_BCM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_BCM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    mcu_voltage_dinfox = int(node_ul_payload[0:4], 16)
                    mcu_temperature_dinfox = int(node_ul_payload[4:8], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(mcu_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, DINFox._get_voltage(mcu_voltage_dinfox))
                    record.add_field(mcu_temperature_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, DINFox._get_temperature(mcu_temperature_dinfox))
                    record_list.append(copy.copy(record))
                # Electrical frame.
                elif (node_ul_payload_size == (2 * DINFOX_BCM_UL_PAYLOAD_SIZE_ELECTRICAL)):
                    # Parse fields.
                    source_voltage_dinfox = int(node_ul_payload[0:4], 16)
                    storage_voltage_dinfox = int(node_ul_payload[4:8], 16)
                    charge_current_dinfox = int(node_ul_payload[8:12], 16)
                    backup_voltage_dinfox = int(node_ul_payload[12:16], 16)
                    charge_status1 = ((int(node_ul_payload[16:18], 16) >> 6) & 0x03)
                    charge_status0 = ((int(node_ul_payload[16:18], 16) >> 4) & 0x03)
                    charge_control_state = ((int(node_ul_payload[16:18], 16) >> 2) & 0x03)
                    backup_control_state = ((int(node_ul_payload[16:18], 16) >> 0) & 0x03)
                    # Create custom charge status field
                    charge_status = 0
                    if ((charge_status1 == DINFOX_UNA_BIT_ERROR) or (charge_status0 == DINFOX_UNA_BIT_ERROR)):
                        charge_status = DINFOX_BCM_CHRGST_ERROR
                    elif ((charge_status1 == DINFOX_UNA_BIT_HW) or (charge_status0 == DINFOX_UNA_BIT_HW)):
                        charge_status = DINFOX_BCM_CHRGST_HW
                    else:
                        if (charge_status1 == DINFOX_UNA_BIT_0):
                            if (charge_status0 == DINFOX_UNA_BIT_0):
                                charge_status = DINFOX_BCM_CHRGST_NOT_CHARGING_TERMINATED
                            else:
                                charge_status = DINFOX_BCM_CHRGST_CHARGING_CC
                        else:
                            if (charge_status0 == DINFOX_UNA_BIT_0):
                                charge_status = DINFOX_BCM_CHRGST_FAULT
                            else:
                                charge_status = DINFOX_BCM_CHRGST_CHARGING_CV
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_CHARGE_STATUS: charge_status,
                        DATABASE_FIELD_CHARGE_CONTROL_STATE: charge_control_state,
                        DATABASE_FIELD_BACKUP_CONTROL_STATE: backup_control_state
                    }
                    record.add_field(source_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_SOURCE_VOLTAGE, DINFox._get_voltage(source_voltage_dinfox))
                    record.add_field(storage_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_STORAGE_VOLTAGE, DINFox._get_voltage(storage_voltage_dinfox))
                    record.add_field(charge_current_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_CHARGE_CURRENT, DINFox._get_current(charge_current_dinfox))
                    record.add_field(backup_voltage_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_BACKUP_VOLTAGE, DINFox._get_voltage(backup_voltage_dinfox))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX BCM] * Invalid UL payload")
            # Unknown board ID.
            else:
                Log.debug_print("[DINFOX] * Unknown board ID")
        return record_list
    
    @staticmethod
    def get_default_dl_payload(sigfox_ep_id: str) -> str:
        # Local variables.
        dl_payload = []
        # Check ID.
        if (sigfox_ep_id in DINFOX_SIGFOX_EP_ID_LIST):
            dl_payload = "0000000000000000"
        return dl_payload
