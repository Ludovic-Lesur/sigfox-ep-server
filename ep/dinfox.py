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
                    vmcu_dinfox = int(node_ul_payload[0:4], 16)
                    tmcu_dinfox = int(node_ul_payload[4:8], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(vmcu_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, DINFox._get_voltage(vmcu_dinfox))
                    record.add_field(tmcu_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, DINFox._get_temperature(tmcu_dinfox))
                    record_list.append(copy.copy(record))
                # Electrical frame.
                elif (node_ul_payload_size == (2 * DINFOX_LVRM_UL_PAYLOAD_SIZE_ELECTRICAL)):
                    # Parse field.
                    vcom_dinfox = int(node_ul_payload[0:4], 16)
                    vout_dinfox = int(node_ul_payload[4:8], 16)
                    iout_dinfox = int(node_ul_payload[8:12], 16)
                    rlstst = ((int(node_ul_payload[12:14], 16) >> 0) & 0x03)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_RELAY_STATE: rlstst
                    }
                    record.add_field(vcom_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_INPUT_VOLTAGE, DINFox._get_voltage(vcom_dinfox))
                    record.add_field(vout_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_OUTPUT_VOLTAGE, DINFox._get_voltage(vout_dinfox))
                    record.add_field(iout_dinfox, DINFOX_ERROR_VALUE_CURRENT, DATABASE_FIELD_OUTPUT_CURRENT, DINFox._get_current(iout_dinfox))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX LVRM] * Invalid UL payload")
            # BPSM.
            elif (board_id == DINFOX_BOARD_ID_BPSM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_BPSM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    vmcu_dinfox = int(node_ul_payload[0:4], 16)
                    tmcu_dinfox = int(node_ul_payload[4:8], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(vmcu_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, DINFox._get_voltage(vmcu_dinfox))
                    record.add_field(tmcu_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, DINFox._get_temperature(tmcu_dinfox))
                    record_list.append(copy.copy(record))
                # Electrical frame.
                elif (node_ul_payload_size == (2 * DINFOX_BPSM_UL_PAYLOAD_SIZE_ELECTRICAL)):
                    # Parse fields.
                    vsrc_dinfox = int(node_ul_payload[0:4], 16)
                    vstr_dinfox = int(node_ul_payload[4:8], 16)
                    vbkp_dinfox = int(node_ul_payload[8:12], 16)
                    chrgst = ((int(node_ul_payload[12:14], 16) >> 4) & 0x03)
                    chenst = ((int(node_ul_payload[12:14], 16) >> 2) & 0x03)
                    bkenst = ((int(node_ul_payload[12:14], 16) >> 0) & 0x03)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_CHARGE_STATUS: chrgst,
                        DATABASE_FIELD_CHARGE_CONTROL_STATE: chenst,
                        DATABASE_FIELD_BACKUP_CONTROL_STATE: bkenst
                    }
                    record.add_field(vsrc_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_SOURCE_VOLTAGE, DINFox._get_voltage(vsrc_dinfox))
                    record.add_field(vstr_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_STORAGE_VOLTAGE, DINFox._get_voltage(vstr_dinfox))
                    record.add_field(vbkp_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_BACKUP_VOLTAGE, DINFox._get_voltage(vbkp_dinfox))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX BPSM] * Invalid UL payload")
            # DDRM.
            elif (board_id == DINFOX_BOARD_ID_DDRM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_DDRM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    vmcu_dinfox = int(node_ul_payload[0:4], 16)
                    tmcu_dinfox = int(node_ul_payload[4:8], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(vmcu_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, DINFox._get_voltage(vmcu_dinfox))
                    record.add_field(tmcu_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, DINFox._get_temperature(tmcu_dinfox))
                    record_list.append(copy.copy(record))
                # Electrical frame.
                elif (node_ul_payload_size == (2 * DINFOX_DDRM_UL_PAYLOAD_SIZE_ELECTRICAL)):
                    # Parse field.
                    vin_dinfox = int(node_ul_payload[0:4], 16)
                    vout_dinfox = int(node_ul_payload[4:8], 16)
                    iout_dinfox = int(node_ul_payload[8:12], 16)
                    ddenst = ((int(node_ul_payload[12:14], 16) >> 0) & 0x03)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_REGULATOR_STATE: ddenst
                    }
                    record.add_field(vin_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_INPUT_VOLTAGE, DINFox._get_voltage(vin_dinfox))
                    record.add_field(vout_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_OUTPUT_VOLTAGE, DINFox._get_voltage(vout_dinfox))
                    record.add_field(iout_dinfox, DINFOX_ERROR_VALUE_CURRENT, DATABASE_FIELD_OUTPUT_CURRENT, DINFox._get_current(iout_dinfox))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX DDRM] * Invalid UL payload")
            # UHFM.
            elif (board_id == DINFOX_BOARD_ID_UHFM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_UHFM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    vmcu_dinfox = int(node_ul_payload[0:4], 16)
                    tmcu_dinfox = int(node_ul_payload[4:8], 16)
                    vrf_tx_dinfox = int(node_ul_payload[8:12], 16)
                    vrf_rx_dinfox = int(node_ul_payload[12:16], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(vmcu_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, DINFox._get_voltage(vmcu_dinfox))
                    record.add_field(tmcu_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, DINFox._get_temperature(tmcu_dinfox))
                    record.add_field(vrf_tx_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_RADIO_TX_VOLTAGE, DINFox._get_voltage(vrf_tx_dinfox))
                    record.add_field(vrf_rx_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_RADIO_RX_VOLTAGE, DINFox._get_voltage(vrf_rx_dinfox))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX UHFM] * Invalid UL payload")
            # GPSM.
            elif (board_id == DINFOX_BOARD_ID_GPSM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_GPSM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    vmcu_dinfox = int(node_ul_payload[0:4], 16)
                    tmcu_dinfox = int(node_ul_payload[4:8], 16)
                    vgps_dinfox = int(node_ul_payload[8:12], 16)
                    vant_dinfox = int(node_ul_payload[12:16], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(vmcu_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, DINFox._get_voltage(vmcu_dinfox))
                    record.add_field(tmcu_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, DINFox._get_temperature(tmcu_dinfox))
                    record.add_field(vgps_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_GPS_VOLTAGE, DINFox._get_voltage(vgps_dinfox))
                    record.add_field(vant_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_GPS_ANTENNA_VOLTAGE, DINFox._get_voltage(vant_dinfox))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX GPSM] * Invalid UL payload")
            # SM.
            elif (board_id == DINFOX_BOARD_ID_SM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_SM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    vmcu_dinfox = int(node_ul_payload[0:4], 16)
                    tmcu_dinfox = int(node_ul_payload[4:8], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(vmcu_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, DINFox._get_voltage(vmcu_dinfox))
                    record.add_field(tmcu_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, DINFox._get_temperature(tmcu_dinfox))
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
                    tamb_dinfox = int(node_ul_payload[0:4], 16)
                    hamb_percent = int(node_ul_payload[4:6], 16)
                    # Create sensor record.
                    record.measurement = DATABASE_MEASUREMENT_SENSOR
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                    }
                    record.add_field(tamb_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_TEMPERATURE, DINFox._get_temperature(tamb_dinfox))
                    record.add_field(hamb_percent, DINFOX_ERROR_VALUE_HUMIDITY, DATABASE_FIELD_HUMIDITY, float(hamb_percent))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX SM] * Invalid UL payload")
            # DMM.
            elif (board_id == DINFOX_BOARD_ID_DMM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_DMM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    vrs_dinfox = int(node_ul_payload[0:4], 16)
                    vhmi_dinfox = int(node_ul_payload[4:8], 16)
                    vusb_dinfox = int(node_ul_payload[8:12], 16)
                    node_count = int(node_ul_payload[12:14], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_NODE_COUNT: node_count
                    }
                    record.add_field(vrs_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_RS485_BUS_VOLTAGE, DINFox._get_voltage(vrs_dinfox))
                    record.add_field(vhmi_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_HMI_VOLTAGE, DINFox._get_voltage(vhmi_dinfox))
                    record.add_field(vusb_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_USB_VOLTAGE, DINFox._get_voltage(vusb_dinfox))
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX DMM] * Invalid UL payload")
            # MPMCM.
            elif (board_id == DINFOX_BOARD_ID_MPMCM):
                # Status frame.
                if (node_ul_payload_size == (2 * DINFOX_MPMCM_UL_PAYLOAD_SIZE_STATUS)):
                    # Parse fields.
                    mvd = ((int(node_ul_payload[0:2], 16) >> 5) & 0x01)
                    ticd = ((int(node_ul_payload[0:2], 16) >> 4) & 0x01)
                    ch4d = ((int(node_ul_payload[0:2], 16) >> 3) & 0x01)
                    ch3d = ((int(node_ul_payload[0:2], 16) >> 2) & 0x01)
                    ch2d = ((int(node_ul_payload[0:2], 16) >> 1) & 0x01)
                    ch1d = ((int(node_ul_payload[0:2], 16) >> 0) & 0x01)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_MAINS_VOLTAGE_DETECT: mvd,
                        DATABASE_FIELD_MAINS_LINKY_TIC_DETECT: ticd,
                        DATABASE_FIELD_MAINS_CURRENT_DETECT_CH1: ch1d,
                        DATABASE_FIELD_MAINS_CURRENT_DETECT_CH2: ch2d,
                        DATABASE_FIELD_MAINS_CURRENT_DETECT_CH3: ch3d,
                        DATABASE_FIELD_MAINS_CURRENT_DETECT_CH4: ch4d,
                    }
                    record_list.append(copy.copy(record))
                # Mains voltage frame.
                elif (node_ul_payload_size == (2 * DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_VOLTAGE)):
                    # Parse fields.
                    mpmcm_channel_index = ((int(node_ul_payload[0:2], 16) >> 0) & 0x07)
                    vrms_min_dinfox = int(node_ul_payload[2:6], 16)
                    vrms_mean_dinfox = int(node_ul_payload[6:10], 16)
                    vrms_max_dinfox = int(node_ul_payload[10:14], 16)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                    }
                    record.add_field(vrms_min_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MAINS_VOLTAGE_RMS_MIN, DINFox._get_voltage(vrms_min_dinfox))
                    record.add_field(vrms_mean_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MAINS_VOLTAGE_RMS_MEAN, DINFox._get_voltage(vrms_mean_dinfox))
                    record.add_field(vrms_max_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MAINS_VOLTAGE_RMS_MAX, DINFox._get_voltage(vrms_max_dinfox))
                    record.tags[DATABASE_TAG_CHANNEL] = mpmcm_channel_index
                    record_list.append(copy.copy(record))
                # Mains frequency frame.
                elif (node_ul_payload_size == (2 * DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_FREQUENCY)):
                    # Parse fields.
                    f_min_chz = int(node_ul_payload[0:4], 16)
                    f_mean_chz = int(node_ul_payload[4:8], 16)
                    f_max_chz = int(node_ul_payload[8:12])
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                    }
                    record.add_field(f_min_chz, DINFOX_ERROR_VALUE_FREQUENCY, DATABASE_FIELD_MAINS_FREQUENCY_MIN, float(f_min_chz / 100.0))
                    record.add_field(f_mean_chz, DINFOX_ERROR_VALUE_FREQUENCY, DATABASE_FIELD_MAINS_FREQUENCY_MEAN, float(f_mean_chz / 100.0))
                    record.add_field(f_max_chz, DINFOX_ERROR_VALUE_FREQUENCY, DATABASE_FIELD_MAINS_FREQUENCY_MAX, float(f_max_chz / 100.0))
                    record_list.append(copy.copy(record))
                # Mains power frame.
                elif (node_ul_payload_size == (2 * DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_POWER)):
                    # Parse fields.
                    mpmcm_channel_index = ((int(node_ul_payload[0:2], 16) >> 0) & 0x07)
                    pact_mean_dinfox = int(node_ul_payload[2:6], 16)
                    pact_max_dinfox = int(node_ul_payload[6:10], 16)
                    papp_mean_dinfox = int(node_ul_payload[10:14], 16)
                    papp_max_dinfox = int(node_ul_payload[14:18], 16)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                    }
                    record.add_field(pact_mean_dinfox, DINFOX_ERROR_VALUE_ELECTRICAL_POWER, DATABASE_FIELD_MAINS_ACTIVE_POWER_MEAN, DINFox._get_electrical_power(pact_mean_dinfox))
                    record.add_field(pact_max_dinfox, DINFOX_ERROR_VALUE_ELECTRICAL_POWER, DATABASE_FIELD_MAINS_ACTIVE_POWER_MAX, DINFox._get_electrical_power(pact_max_dinfox))
                    record.add_field(papp_mean_dinfox, DINFOX_ERROR_VALUE_ELECTRICAL_POWER, DATABASE_FIELD_MAINS_APPARENT_POWER_MEAN, DINFox._get_electrical_power(papp_mean_dinfox))
                    record.add_field(papp_max_dinfox, DINFOX_ERROR_VALUE_ELECTRICAL_POWER, DATABASE_FIELD_MAINS_APPARENT_POWER_MAX, DINFox._get_electrical_power(papp_max_dinfox))
                    record.tags[DATABASE_TAG_CHANNEL] = mpmcm_channel_index
                    record_list.append(copy.copy(record))
                # Mains power factor frame.
                elif (node_ul_payload_size == (2 * DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_POWER_FACTOR)):
                    # Parse fields.
                    mpmcm_channel_index = ((int(node_ul_payload[0:2], 16) >> 0) & 0x07)
                    pf_min_dinfox = int(node_ul_payload[2:4], 16)
                    pf_mean_dinfox = int(node_ul_payload[4:6], 16)
                    pf_max_dinfox = int(node_ul_payload[6:8], 16)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                    }
                    record.add_field(pf_min_dinfox, DINFOX_ERROR_VALUE_POWER_FACTOR, DATABASE_FIELD_MAINS_POWER_FACTOR_MIN, DINFox._get_power_factor(pf_min_dinfox))
                    record.add_field(pf_mean_dinfox, DINFOX_ERROR_VALUE_POWER_FACTOR, DATABASE_FIELD_MAINS_POWER_FACTOR_MEAN, DINFox._get_power_factor(pf_mean_dinfox))
                    record.add_field(pf_max_dinfox, DINFOX_ERROR_VALUE_POWER_FACTOR, DATABASE_FIELD_MAINS_POWER_FACTOR_MAX, DINFox._get_power_factor(pf_max_dinfox))
                    record.tags[DATABASE_TAG_CHANNEL] = mpmcm_channel_index
                    record_list.append(copy.copy(record))
                # Mains energy frame.
                elif (node_ul_payload_size == (2 * DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_ENERGY)):
                    # Parse fields.
                    mpmcm_channel_index = ((int(node_ul_payload[0:2], 16) >> 0) & 0x07)
                    eact_dinfox = int(node_ul_payload[2:6], 16)
                    eapp_dinfox = int(node_ul_payload[6:10], 16)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                    }
                    record.add_field(eact_dinfox, DINFOX_ERROR_VALUE_ELECTRICAL_ENERGY, DATABASE_FIELD_MAINS_ACTIVE_ENERGY, DINFox._get_electrical_energy(eact_dinfox))
                    record.add_field(eapp_dinfox, DINFOX_ERROR_VALUE_ELECTRICAL_ENERGY, DATABASE_FIELD_MAINS_APPARENT_ENERGY, DINFox._get_electrical_energy(eapp_dinfox))
                    record.tags[DATABASE_TAG_CHANNEL] = mpmcm_channel_index
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX MPMCM] * Invalid UL payload")
            # R4S8CR.
            elif (board_id == DINFOX_BOARD_ID_R4S8CR):
                # Electrical frame.
                if (node_ul_payload_size == (2 * DINFOX_R4S8CR_UL_PAYLOAD_SIZE_ELECTRICAL)):
                    # Parse fields.
                    r8stst = ((int(node_ul_payload[0:2], 16) >> 6) & 0x03)
                    r7stst = ((int(node_ul_payload[0:2], 16) >> 4) & 0x03)
                    r6stst = ((int(node_ul_payload[0:2], 16) >> 2) & 0x03)
                    r5stst = ((int(node_ul_payload[0:2], 16) >> 0) & 0x03)
                    r4stst = ((int(node_ul_payload[2:4], 16) >> 6) & 0x03)
                    r3stst = ((int(node_ul_payload[2:4], 16) >> 4) & 0x03)
                    r2stst = ((int(node_ul_payload[2:4], 16) >> 2) & 0x03)
                    r1stst = ((int(node_ul_payload[2:4], 16) >> 0) & 0x03)
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_RELAY1_STATE: r1stst,
                        DATABASE_FIELD_RELAY2_STATE: r2stst,
                        DATABASE_FIELD_RELAY3_STATE: r3stst,
                        DATABASE_FIELD_RELAY4_STATE: r4stst,
                        DATABASE_FIELD_RELAY5_STATE: r5stst,
                        DATABASE_FIELD_RELAY6_STATE: r6stst,
                        DATABASE_FIELD_RELAY7_STATE: r7stst,
                        DATABASE_FIELD_RELAY8_STATE: r8stst
                    }
                    record_list.append(copy.copy(record))
                else:
                    Log.debug_print("[DINFOX R4S8CR] * Invalid UL payload")
            # BCM.
            elif (board_id == DINFOX_BOARD_ID_BCM):
                # Monitoring frame.
                if (node_ul_payload_size == (2 * DINFOX_BCM_UL_PAYLOAD_SIZE_MONITORING)):
                    # Parse fields.
                    vmcu_dinfox = int(node_ul_payload[0:4], 16)
                    tmcu_dinfox = int(node_ul_payload[4:8], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(vmcu_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, DINFox._get_voltage(vmcu_dinfox))
                    record.add_field(tmcu_dinfox, DINFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, DINFox._get_temperature(tmcu_dinfox))
                    record_list.append(copy.copy(record))
                # Electrical frame.
                elif (node_ul_payload_size == (2 * DINFOX_BCM_UL_PAYLOAD_SIZE_ELECTRICAL)):
                    # Parse fields.
                    vsrc_dinfox = int(node_ul_payload[0:4], 16)
                    vstr_dinfox = int(node_ul_payload[4:8], 16)
                    istr_dinfox = int(node_ul_payload[8:12], 16)
                    vbkp_dinfox = int(node_ul_payload[12:16], 16)
                    chrgst1 = ((int(node_ul_payload[16:18], 16) >> 6) & 0x03)
                    chrgst0 = ((int(node_ul_payload[16:18], 16) >> 4) & 0x03)
                    chenst = ((int(node_ul_payload[16:18], 16) >> 2) & 0x03)
                    bkenst = ((int(node_ul_payload[16:18], 16) >> 0) & 0x03)
                    # Create custom charge status field
                    chrgst = 0
                    if ((chrgst1 == DINFOX_UNA_BIT_ERROR) or (chrgst0 == DINFOX_UNA_BIT_ERROR)):
                        chrgst = DINFOX_BCM_CHRGST_ERROR
                    elif ((chrgst1 == DINFOX_UNA_BIT_HW) or (chrgst0 == DINFOX_UNA_BIT_HW)):
                        chrgst = DINFOX_BCM_CHRGST_HW
                    else:
                        if (chrgst1 == DINFOX_UNA_BIT_0):
                            if (chrgst0 == DINFOX_UNA_BIT_0):
                                chrgst = DINFOX_BCM_CHRGST_NOT_CHARGING_TERMINATED
                            else:
                                chrgst = DINFOX_BCM_CHRGST_CHARGING_CC
                        else:
                            if (chrgst0 == DINFOX_UNA_BIT_0):
                                chrgst = DINFOX_BCM_CHRGST_FAULT
                            else:
                                chrgst = DINFOX_BCM_CHRGST_CHARGING_CV
                    # Create electrical record.
                    record.measurement = DATABASE_MEASUREMENT_ELECTRICAL
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_CHARGE_STATUS: chrgst,
                        DATABASE_FIELD_CHARGE_CONTROL_STATE: chenst,
                        DATABASE_FIELD_BACKUP_CONTROL_STATE: bkenst
                    }
                    record.add_field(vsrc_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_SOURCE_VOLTAGE, DINFox._get_voltage(vsrc_dinfox))
                    record.add_field(vstr_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_STORAGE_VOLTAGE, DINFox._get_voltage(vstr_dinfox))
                    record.add_field(istr_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_CHARGE_CURRENT, DINFox._get_current(istr_dinfox))
                    record.add_field(vbkp_dinfox, DINFOX_ERROR_VALUE_VOLTAGE, DATABASE_FIELD_BACKUP_VOLTAGE, DINFox._get_voltage(vbkp_dinfox))
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
