from __future__ import print_function

from common import *
from influx_db import *
from log import *

### LOCAL MACROS ###

# Test bench.
__DINFOX_SYSTEM_0_NAME = "Test_bench"
__DINFOX_SYSTEM_0_NODE_ADDRESS = [0x00, 0x01, 0x08, 0x0C, 0x10, 0x14, 0x1C, 0x20, 0x21, 0x30, 0x70]
__DINFOX_SYSTEM_0_NODE = ["DMM_0", "DIM_0", "BPSM_0", "UHFM_0", "GPSM_0", "SM_0", "MPMCM_0", "LVRM_0", "LVRM_1", "DDRM_0", "R4S8CR_0"]
# Prat Albis.
__DINFOX_SYSTEM_1_NAME = "Prat_Albis"
__DINFOX_SYSTEM_1_NODE_ADDRESS = [0x00, 0x01, 0x08, 0x0C, 0x14, 0x70]
__DINFOX_SYSTEM_1_NODE = ["DMM_0", "DIM_0", "BPSM_0", "UHFM_0", "SM_0", "R4S8CR_0"]
# Solar rack.
__DINFOX_SYSTEM_2_NAME = "Solar_rack"
__DINFOX_SYSTEM_2_NODE_ADDRESS = [0x00, 0x01, 0x08, 0x0C, 0x20, 0x30, 0x31]
__DINFOX_SYSTEM_2_NODE = ["DMM_0", "DIM_0", "BPSM_0", "UHFM_0", "LVRM_0", "DDRM_0", "DDRM_1"]
# Mains rack.
__DINFOX_SYSTEM_3_NAME = "Mains_rack"
__DINFOX_SYSTEM_3_NODE_ADDRESS = [0x00, 0x01, 0x08, 0x0C, 0x1C]
__DINFOX_SYSTEM_3_NODE = ["DMM_0", "DIM_0", "BPSM_0", "UHFM_0", "MPMCM_0"]

__DINFOX_SYSTEM = [__DINFOX_SYSTEM_0_NAME, __DINFOX_SYSTEM_1_NAME, __DINFOX_SYSTEM_2_NAME, __DINFOX_SYSTEM_3_NAME, "N/A", "N/A", "N/A", "N/A", "N/A","N/A"]

# Board ID definition.
__DINFOX_BOARD_ID_LVRM = 0
__DINFOX_BOARD_ID_BPSM = 1
__DINFOX_BOARD_ID_DDRM = 2
__DINFOX_BOARD_ID_UHFM = 3
__DINFOX_BOARD_ID_GPSM = 4
__DINFOX_BOARD_ID_SM = 5
__DINFOX_BOARD_ID_DIM = 6
__DINFOX_BOARD_ID_RRM = 7
__DINFOX_BOARD_ID_DMM = 8
__DINFOX_BOARD_ID_MPMCM = 9
__DINFOX_BOARD_ID_R4S8CR = 10

# UL payloads structure.
__DINFOX_UL_PAYLOAD_HEADER_SIZE = 2

__DINFOX_LVRM_UL_PAYLOAD_MONITORING_SIZE = 3
__DINFOX_LVRM_UL_PAYLOAD_ELECTRICAL_SIZE = 7

__DINFOX_BPSM_UL_PAYLOAD_MONITORING_SIZE = 3
__DINFOX_BPSM_UL_PAYLOAD_ELECTRICAL_SIZE = 7

__DINFOX_DDRM_UL_PAYLOAD_MONITORING_SIZE = 3
__DINFOX_DDRM_UL_PAYLOAD_ELECTRICAL_SIZE = 7

__DINFOX_UHFM_UL_PAYLOAD_MONITORING_SIZE = 7

__DINFOX_GPSM_UL_PAYLOAD_MONITORING_SIZE = 7

__DINFOX_SM_UL_PAYLOAD_SENSOR_1_SIZE = 9
__DINFOX_SM_UL_PAYLOAD_SENSOR_2_SIZE = 5

__DINFOX_DMM_UL_PAYLOAD_MONITORING_SIZE = 5

__DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_POWER_FACTOR = 4
__DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_FREQUENCY = 6
__DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_VOLTAGE = 7
__DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_POWER = 9

__DINFOX_R4S8CR_UL_PAYLOAD_ELECTRICAL_SIZE = 1

__DINFOX_UL_PAYLOAD_ERROR_STACK_SIZE = 10

### PUBLIC MACROS ###

# TrackFox EP-IDs.
DINFOX_EP_ID = ["4761", "479C", "47A7", "47EA", "4894", "48AA", "48CB", "48E1", "4928", "492F"]

### LOCAL FUNCTIONS ###

# Convert DINFox temperature representation to degrees.
def __DINFOX_get_degrees(dinfox_temperature):
    return COMMON_one_complement_to_value(dinfox_temperature, 7)

# Convert DINFox voltage representation to mV.
def __DINFOX_get_mv(dinfox_voltage):
    # Reset result.
    voltage_mv = COMMON_ERROR_DATA
    # Extract unit and value.
    unit = ((dinfox_voltage >> 15) & 0x0001)
    value = ((dinfox_voltage >> 0) & 0x7FFF)
    # Convert.
    if (unit == 0):
        voltage_mv = (value * 1)
    else:
        voltage_mv = (value * 100)
    return voltage_mv

# Convert DINFox current representation to uA.
def __DINFOX_get_ua(dinfox_current):
    # Reset result.
    current_ua = COMMON_ERROR_DATA
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
    return current_ua

def __DINFOX_get_mW(dinfox_electrical_power):
    # Reset result.
    electrical_power_mw = COMMON_ERROR_DATA
    # Extract sign, unit and value.
    sign = ((dinfox_electrical_power >> 15) & 0x0001)
    unit = ((dinfox_electrical_power >> 13) & 0x0003)
    value = ((dinfox_electrical_power >> 0) & 0x1FFF)
    # Convert.
    if (unit == 0):
        electrical_power_mw = ((-1) ** (sign)) * (value * 1)
    elif (unit == 1):
        electrical_power_mw = ((-1) ** (sign)) * (value * 100)
    elif (unit == 2):
        electrical_power_mw = ((-1) ** (sign)) * (value * 1000)
    else:
        electrical_power_mw = ((-1) ** (sign)) * (value * 100000)
    return electrical_power_mw

# Function performing Sigfox ID to DinFox system and node conversion.
def __DINFOX_get_system_and_node(sigfox_ep_id, node_address):
    # Default is unknown.
    system_name = "unknown"
    node_name = "unknown"
    if (sigfox_ep_id in DINFOX_EP_ID):
        # Get system name.
        system_name = __DINFOX_SYSTEM[DINFOX_EP_ID.index(sigfox_ep_id)]
        # Search node list.
        if (system_name == __DINFOX_SYSTEM_0_NAME):
            if (node_address in __DINFOX_SYSTEM_0_NODE_ADDRESS):
                # Get node name.
                node_name = __DINFOX_SYSTEM_0_NODE[__DINFOX_SYSTEM_0_NODE_ADDRESS.index(node_address)]
        elif (system_name == __DINFOX_SYSTEM_1_NAME):
            if (node_address in __DINFOX_SYSTEM_1_NODE_ADDRESS):
                # Get node name.
                node_name = __DINFOX_SYSTEM_1_NODE[__DINFOX_SYSTEM_1_NODE_ADDRESS.index(node_address)]
        elif (system_name == __DINFOX_SYSTEM_2_NAME):
            if (node_address in __DINFOX_SYSTEM_2_NODE_ADDRESS):
                # Get node name.
                node_name = __DINFOX_SYSTEM_2_NODE[__DINFOX_SYSTEM_2_NODE_ADDRESS.index(node_address)]
        elif (system_name == __DINFOX_SYSTEM_3_NAME):
            if (node_address in __DINFOX_SYSTEM_3_NODE_ADDRESS):
                # Get node name.
                node_name = __DINFOX_SYSTEM_3_NODE[__DINFOX_SYSTEM_3_NODE_ADDRESS.index(node_address)]    
    return system_name, node_name

# Function adding the specific DinFox tags.
def __DINFOX_add_tags(json_body, sigfox_ep_id, node_address, board_id, mpmcm_channel_index):
    # Get tags.
    result = __DINFOX_get_system_and_node(sigfox_ep_id, node_address)
    system_name = result[0]
    node_name = result[1]
    for idx in range(len(json_body)) :
        json_body[idx]["tags"] = {
            INFLUX_DB_TAG_SIGFOX_EP_ID : sigfox_ep_id,
            INFLUX_DB_TAG_SYSTEM : system_name,
            INFLUX_DB_TAG_NODE_ADDRESS : node_address,
            INFLUX_DB_TAG_NODE : node_name,
            INFLUX_DB_TAG_BOARD_ID : board_id
        }
        if (mpmcm_channel_index != COMMON_ERROR_DATA):
            json_body[idx]["tags"][INFLUX_DB_TAG_CHANNEL] = mpmcm_channel_index

### PUBLIC FUNCTIONS ###

# Function for parsing TrackFox device payload and fill database.
def DINFOX_fill_data_base(timestamp, sigfox_ep_id, ul_payload):
    # Init JSON object.
    json_body = []
    # MPMCM specific tag.
    mpmcm_channel_index = COMMON_ERROR_DATA
    # Check payload size.
    if (len(ul_payload) <= (2 * __DINFOX_UL_PAYLOAD_HEADER_SIZE)) :
        LOG_print_timestamp("[DINFOX] * Invalid payload")
        return
    # Read node address and board ID.
    node_address = int(ul_payload[0:2], 16)
    board_id = int(ul_payload[2:4], 16)
    # Get system and node names for log print.
    result = __DINFOX_get_system_and_node(sigfox_ep_id, node_address)
    system_name = result[0]
    node_name = result[1]
    # Extract node payload.
    node_ul_payload = ul_payload[(2 * __DINFOX_UL_PAYLOAD_HEADER_SIZE):]
    node_ul_payload_size = len(ul_payload) - (2 * __DINFOX_UL_PAYLOAD_HEADER_SIZE)
    # Common startup frame for all nodes.
    if (node_ul_payload_size == (2 * COMMON_UL_PAYLOAD_STARTUP_SIZE)):
        # Create JSON object.
        result = COMMON_create_json_startup_data(timestamp, node_ul_payload)
        json_body = result[0]
        log_data = result[1]
        LOG_print_timestamp("[DINFOX] * Startup data * system=" + system_name + " node=" + node_name + " " + log_data)
    # Common error stack frame for all nodes.
    elif (node_ul_payload_size == (2 * __DINFOX_UL_PAYLOAD_ERROR_STACK_SIZE)):
        result = COMMON_create_json_error_stack_data(timestamp, node_ul_payload, (__DINFOX_UL_PAYLOAD_ERROR_STACK_SIZE / 2))
        json_body = result[0]
        log_data = result[1]
        LOG_print_timestamp("[DINFOX] * Error stack data * system=" + system_name + " node=" + node_name + " " + log_data)
    # Node-specific frames.
    else:
        # LVRM.
        if (board_id == __DINFOX_BOARD_ID_LVRM):
            # Monitoring frame.
            if (node_ul_payload_size == (2 * __DINFOX_LVRM_UL_PAYLOAD_MONITORING_SIZE)):
                vmcu_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                tmcu_degrees = __DINFOX_get_degrees(int(node_ul_payload[4:6], 16)) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_MONITORING_DATA : timestamp
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (vmcu_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
                if (tmcu_degrees != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
                LOG_print_timestamp("[DINFOX LVRM] * Monitoring payload * system=" + system_name + " node=" + node_name +
                                    " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC ")
            # Electrical frame.
            elif (node_ul_payload_size == (2 * __DINFOX_LVRM_UL_PAYLOAD_ELECTRICAL_SIZE)):
                vcom_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                vout_mv = __DINFOX_get_mv(int(node_ul_payload[4:8], 16)) if (int(node_ul_payload[4:8], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                iout_ua = __DINFOX_get_ua(int(node_ul_payload[8:12], 16)) if (int(node_ul_payload[8:12], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                rlst = (int(node_ul_payload[12:14], 16) >> 0) & 0x01
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                        INFLUX_DB_FIELD_RELAY_STATE : rlst
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (vcom_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VCOM] = vcom_mv
                if (vout_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VOUT] = vout_mv
                if (iout_ua != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_IOUT] = iout_ua 
                LOG_print_timestamp("[DINFOX LVRM] * Electrical payload * system=" + system_name + " node=" + node_name +
                                    " vcom=" + str(vcom_mv) + "mV vout=" + str(vout_mv) + "mV iout=" + str(iout_ua) + "uA relay=" + str(rlst))
            else:
                LOG_print_timestamp("[DINFOX LVRM] * system=" + system_name + " node=" + node_name + " * Invalid payload")
        # BPSM.
        elif (board_id == __DINFOX_BOARD_ID_BPSM):
            # Monitoring frame.
            if (node_ul_payload_size == (2 * __DINFOX_BPSM_UL_PAYLOAD_MONITORING_SIZE)):
                vmcu_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                tmcu_degrees = __DINFOX_get_degrees(int(node_ul_payload[4:6], 16)) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_MONITORING_DATA : timestamp
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (vmcu_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
                if (tmcu_degrees != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
                LOG_print_timestamp("[DINFOX BPSM] * Monitoring payload * system=" + system_name + " node=" + node_name +
                                    " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC ")
            # Electrical frame.
            elif (node_ul_payload_size == (2 * __DINFOX_BPSM_UL_PAYLOAD_ELECTRICAL_SIZE)):
                vsrc_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                vstr_mv = __DINFOX_get_mv(int(node_ul_payload[4:8], 16)) if (int(node_ul_payload[4:8], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                vbkp_mv = __DINFOX_get_mv(int(node_ul_payload[8:12], 16)) if (int(node_ul_payload[8:12], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                chst = (int(node_ul_payload[12:14], 16) >> 0) & 0x01
                chen = (int(node_ul_payload[12:14], 16) >> 1) & 0x01
                bken = (int(node_ul_payload[12:14], 16) >> 2) & 0x01
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                        INFLUX_DB_FIELD_CHARGE_STATUS : chst,
                        INFLUX_DB_FIELD_CHARGE_ENABLE : chen,
                        INFLUX_DB_FIELD_BACKUP_ENABLE : bken
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (vsrc_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VSRC] = vsrc_mv
                if (vstr_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VSTR] = vstr_mv
                if (vbkp_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VBKP] = vbkp_mv
                LOG_print_timestamp("[DINFOX BPSM] * Electrical payload * system=" + system_name + " node=" + node_name +
                                    " vsrc=" + str(vsrc_mv) + "mV vstr=" + str(vstr_mv) + "mV vbkp=" + str(vbkp_mv) +
                                    "mV charge_status=" + str(chst) + " charge_enable=" + str(chen) + " backup_enable=" + str(bken))
            else:
                LOG_print_timestamp("[DINFOX BPSM] * system=" + system_name + " node=" + node_name + " * Invalid payload")
        # DDRM.
        elif (board_id == __DINFOX_BOARD_ID_DDRM):
            # Monitoring frame.
            if (node_ul_payload_size == (2 * __DINFOX_DDRM_UL_PAYLOAD_MONITORING_SIZE)):
                vmcu_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                tmcu_degrees = __DINFOX_get_degrees(int(node_ul_payload[4:6], 16)) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_MONITORING_DATA : timestamp
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (vmcu_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
                if (tmcu_degrees != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
                LOG_print_timestamp("[DINFOX DDRM] * Monitoring payload * system=" + system_name + " node=" + node_name +
                                    " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC ")
            # Electrical frame.
            elif (node_ul_payload_size == (2 * __DINFOX_DDRM_UL_PAYLOAD_ELECTRICAL_SIZE)):
                vin_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                vout_mv = __DINFOX_get_mv(int(node_ul_payload[4:8], 16)) if (int(node_ul_payload[4:8], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                iout_ua = __DINFOX_get_ua(int(node_ul_payload[8:12], 16)) if (int(node_ul_payload[8:12], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                dden = (int(node_ul_payload[12:14], 16) >> 0) & 0x01
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                        INFLUX_DB_FIELD_DC_DC_STATE : dden
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (vin_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VIN] = vin_mv
                if (vout_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VOUT] = vout_mv
                if (iout_ua != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_IOUT] = iout_ua 
                LOG_print_timestamp("[DINFOX DDRM] * Electrical payload * system=" + system_name + " node=" + node_name +
                                    " vin=" + str(vin_mv) + "mV vout=" + str(vout_mv) + "mV iout=" + str(iout_ua) + "uA dc_dc=" + str(dden))
            else:
                LOG_print_timestamp("[DINFOX DDRM] * system=" + system_name + " node=" + node_name + " * Invalid payload")
        # UHFM.
        elif (board_id == __DINFOX_BOARD_ID_UHFM):
            # Monitoring frame.
            if (node_ul_payload_size == (2 * __DINFOX_UHFM_UL_PAYLOAD_MONITORING_SIZE)):
                vmcu_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                tmcu_degrees = __DINFOX_get_degrees(int(node_ul_payload[4:6], 16)) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                vrf_mv_tx = __DINFOX_get_mv(int(node_ul_payload[6:10], 16)) if (int(node_ul_payload[6:10], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                vrf_mv_rx = __DINFOX_get_mv(int(node_ul_payload[10:14], 16)) if (int(node_ul_payload[10:14], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_MONITORING_DATA : timestamp
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (vmcu_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
                if (tmcu_degrees != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
                if (vrf_mv_tx != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VRF_TX] = vrf_mv_tx
                if (vrf_mv_rx != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VRF_RX] = vrf_mv_rx
                LOG_print_timestamp("[DINFOX UHFM] * Monitoring payload * system=" + system_name + " node=" + node_name +
                                    " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC vrf_tx=" + str(vrf_mv_tx) + "mV vrf_rx=" + str(vrf_mv_rx) + "mV")
            else:
                LOG_print_timestamp("[DINFOX UHFM] * system=" + system_name + " node=" + node_name + " * Invalid payload")
        # GPSM.
        elif (board_id == __DINFOX_BOARD_ID_GPSM):
            # Monitoring frame.
            if (node_ul_payload_size == (2 * __DINFOX_GPSM_UL_PAYLOAD_MONITORING_SIZE)):
                vmcu_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                tmcu_degrees = __DINFOX_get_degrees(int(node_ul_payload[4:6], 16)) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                vgps_mv = __DINFOX_get_mv(int(node_ul_payload[6:10], 16)) if (int(node_ul_payload[6:10], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                vant_mv = __DINFOX_get_mv(int(node_ul_payload[10:14], 16)) if (int(node_ul_payload[10:14], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_MONITORING_DATA : timestamp
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (vmcu_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
                if (tmcu_degrees != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
                if (vgps_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VGPS] = vgps_mv
                if (vant_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VANT] = vant_mv
                LOG_print_timestamp("[DINFOX GPSM] * Monitoring payload * system=" + system_name + " node=" + node_name +
                                    " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC vgps=" + str(vgps_mv) + "mV vant=" + str(vant_mv) + "mV")
            else:
                LOG_print_timestamp("[DINFOX GPSM] * system=" + system_name + " node=" + node_name + " * Invalid payload")
        # SM.
        elif (board_id == __DINFOX_BOARD_ID_SM):
            # Sensor 1 frame.
            if (node_ul_payload_size == (2 * __DINFOX_SM_UL_PAYLOAD_SENSOR_1_SIZE)):
                ain0_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS else COMMON_ERROR_DATA
                ain1_mv = __DINFOX_get_mv(int(node_ul_payload[4:8], 16)) if int(node_ul_payload[4:8], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS else COMMON_ERROR_DATA
                ain2_mv = __DINFOX_get_mv(int(node_ul_payload[8:12], 16)) if int(node_ul_payload[8:12], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS else COMMON_ERROR_DATA
                ain3_mv = __DINFOX_get_mv(int(node_ul_payload[12:16], 16)) if int(node_ul_payload[12:16], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS else COMMON_ERROR_DATA
                dio0 = (int(node_ul_payload[16:18], 16) >> 0) & 0x01
                dio1 = (int(node_ul_payload[16:18], 16) >> 1) & 0x01
                dio2 = (int(node_ul_payload[16:18], 16) >> 2) & 0x01
                dio3 = (int(node_ul_payload[16:18], 16) >> 3) & 0x01
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_SENSOR,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_SENSOR_DATA : timestamp,
                        INFLUX_DB_FIELD_DIO0 : dio0,
                        INFLUX_DB_FIELD_DIO1 : dio1,
                        INFLUX_DB_FIELD_DIO2 : dio2,
                        INFLUX_DB_FIELD_DIO3 : dio3
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (ain0_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_AIN0] = ain0_mv
                if (ain1_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_AIN1] = ain1_mv
                if (ain2_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_AIN2] = ain2_mv
                if (ain3_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_AIN3] = ain3_mv
                LOG_print_timestamp("[DINFOX SM] * Sensor 1 payload * system=" + system_name + " node=" + node_name +
                                    " ain0=" + str(ain0_mv) + "mV ain1=" + str(ain1_mv) + "mV ain2=" + str(ain2_mv) + "mV ain3=" + str(ain3_mv) +
                                    " dio0=" + str(dio0) + " dio1=" + str(dio1) + " dio2=" + str(dio2) + " dio3=" + str(dio3))
            # Sensor 2 frame.
            elif (node_ul_payload_size == (2 * __DINFOX_SM_UL_PAYLOAD_SENSOR_2_SIZE)):
                vmcu_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                tmcu_degrees = __DINFOX_get_degrees(int(node_ul_payload[4:6], 16)) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                tamb_degrees = __DINFOX_get_degrees(int(node_ul_payload[6:8], 16)) if (int(node_ul_payload[6:8], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                hamb_degrees = int(node_ul_payload[8:10], 16) if (int(node_ul_payload[8:10], 16) != COMMON_ERROR_VALUE_HUMIDITY) else COMMON_ERROR_DATA
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_MONITORING_DATA : timestamp
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (vmcu_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
                if (tmcu_degrees != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
                if (tamb_degrees != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_TAMB] = tamb_degrees
                if (hamb_degrees != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_HAMB] = hamb_degrees
                LOG_print_timestamp("[DINFOX SM] * Sensor 2 payload * system=" + system_name + " node=" + node_name +
                                    " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC tamb=" + str(tamb_degrees) + "dC hamb=" + str(hamb_degrees) + "%")
            else:
                LOG_print_timestamp("[DINFOX SM] * system=" + system_name + " node=" + node_name + " * Invalid payload")
        # DMM.
        elif (board_id == __DINFOX_BOARD_ID_DMM):
            # Monitoring frame.
            if (node_ul_payload_size == (2 * __DINFOX_DMM_UL_PAYLOAD_MONITORING_SIZE)):
                vrs_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                vhmi_mv = __DINFOX_get_mv(int(node_ul_payload[4:8], 16)) if (int(node_ul_payload[4:8], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                nodes_count = int(node_ul_payload[8:10], 16)
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_MONITORING_DATA : timestamp,
                        INFLUX_DB_FIELD_NODES_COUNT : nodes_count
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (vrs_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VRS] = vrs_mv
                if (vhmi_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VHMI] = vhmi_mv
                LOG_print_timestamp("[DINFOX DMM] * Monitoring payload * system=" + system_name + " node=" + node_name +
                                    " vrs=" + str(vrs_mv) + "mV vhmi=" + str(vhmi_mv) + "mV nodes_count=" + str(nodes_count))
            else:
                LOG_print_timestamp("[DINFOX DMM] * system=" + system_name + " node=" + node_name + " * Invalid payload")
        # MPMCM.
        elif (board_id == __DINFOX_BOARD_ID_MPMCM):
            # Mains voltage frame.
            if (node_ul_payload_size == (2 * __DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_VOLTAGE)):
                mvd =  (int(node_ul_payload[0:2], 16) >> 4) & 0x01
                ch4d = (int(node_ul_payload[0:2], 16) >> 3) & 0x01
                ch3d = (int(node_ul_payload[0:2], 16) >> 2) & 0x01
                ch2d = (int(node_ul_payload[0:2], 16) >> 1) & 0x01
                ch1d = (int(node_ul_payload[0:2], 16) >> 0) & 0x01
                vrms_min =  __DINFOX_get_mv(int(node_ul_payload[2:6], 16))   if (int(node_ul_payload[2:6], 16)   != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                vrms_mean = __DINFOX_get_mv(int(node_ul_payload[6:10], 16))  if (int(node_ul_payload[6:10], 16)  != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                vrms_max =  __DINFOX_get_mv(int(node_ul_payload[10:14], 16)) if (int(node_ul_payload[10:14], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                        INFLUX_DB_FIELD_MAINS_VOLTAGE_DETECT : mvd,
                        INFLUX_DB_FIELD_CH1_DETECT : ch1d,
                        INFLUX_DB_FIELD_CH2_DETECT : ch2d,
                        INFLUX_DB_FIELD_CH3_DETECT : ch3d,
                        INFLUX_DB_FIELD_CH4_DETECT : ch4d,
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (vrms_min != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VRMS_MIN] = vrms_min
                if (vrms_mean != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VRMS_MEAN] = vrms_mean
                if (vrms_max != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VRMS_MAX] = vrms_max
                LOG_print_timestamp("[DINFOX MPMCM] * Electrical mains voltage payload * system=" + system_name + " node=" + node_name +
                                    " mvd=" + str(mvd) + " ch1d=" + str(ch1d) + " ch2d=" + str(ch2d) + " ch3d=" + str(ch3d) + " ch4d=" + str(ch4d) +
                                    " vrms_min=" + str(vrms_min) + "mV vrms_mean=" + str(vrms_mean) + "mV vrms_max=" + str(vrms_max) + "mV")
            # Mains frequency frame.
            elif (node_ul_payload_size == (2 * __DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_FREQUENCY)):
                f_min =  (int(node_ul_payload[0:4], 16) / 100.0)  if (int(node_ul_payload[2:6], 16)   != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                f_mean = (int(node_ul_payload[4:8], 16) / 100.0)  if (int(node_ul_payload[6:10], 16)  != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                f_max =  (int(node_ul_payload[8:12], 16) / 100.0) if (int(node_ul_payload[10:14], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (f_min != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_FREQUENCY_MIN] = f_min
                if (f_mean != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_FREQUENCY_MEAN] = f_mean
                if (f_max != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_FREQUENCY_MAX] = f_max
                LOG_print_timestamp("[DINFOX MPMCM] * Electrical mains frequency payload * system=" + system_name + " node=" + node_name +
                                    " f_min=" + str(f_min) + "Hz f_mean=" + str(f_mean) + "Hz f_max=" + str(f_max) + "Hz")
            # Mains power frame.
            elif (node_ul_payload_size == (2 * __DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_POWER)):
                mpmcm_channel_index = (int(node_ul_payload[0:2], 16) >> 0) & 0x03
                pact_mean = __DINFOX_get_mW(int(node_ul_payload[2:6], 16))   if (int(node_ul_payload[2:6], 16)   != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                pact_max =  __DINFOX_get_mW(int(node_ul_payload[6:10], 16))  if (int(node_ul_payload[6:10], 16)  != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                papp_mean = __DINFOX_get_mW(int(node_ul_payload[10:14], 16)) if (int(node_ul_payload[10:14], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                papp_max =  __DINFOX_get_mW(int(node_ul_payload[14:18], 16)) if (int(node_ul_payload[14:18], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (pact_mean != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_PACT_MEAN] = pact_mean
                if (pact_max != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_PACT_MAX] = pact_max
                if (papp_mean != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_PAPP_MEAN] = papp_mean
                if (papp_max != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_PAPP_MAX] = papp_max
                LOG_print_timestamp("[DINFOX MPMCM] * Electrical mains power payload * system=" + system_name + " node=" + node_name + " channel=" + str(mpmcm_channel_index) +
                                    " pact_mean=" + str(pact_mean) + "mW pact_max=" + str(pact_max) + "mW papp_mean=" + str(papp_mean) + "mW papp_max=" + str(papp_max) + "mW")
            # Mains power factor frame.
            elif (node_ul_payload_size == (2 * __DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_POWER_FACTOR)):
                mpmcm_channel_index = (int(node_ul_payload[0:2], 16) >> 0) & 0x03
                pf_min =  (int(node_ul_payload[2:4], 16) / 100.0) if (int(node_ul_payload[2:4], 16) != COMMON_ERROR_POWER_FACTOR) else COMMON_ERROR_DATA
                pf_mean = (int(node_ul_payload[4:6], 16) / 100.0) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_POWER_FACTOR) else COMMON_ERROR_DATA
                pf_max =  (int(node_ul_payload[6:8], 16) / 100.0) if (int(node_ul_payload[6:8], 16) != COMMON_ERROR_POWER_FACTOR) else COMMON_ERROR_DATA
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                # Add valid fields to JSON.
                if (pf_min != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_PF_MIN] = pf_min
                if (pf_mean != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_PF_MEAN] = pf_mean
                if (pf_max != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_PF_MAX] = pf_max
                LOG_print_timestamp("[DINFOX MPMCM] * Electrical mains frequency payload * system=" + system_name + " node=" + node_name + " channel=" + str(mpmcm_channel_index) +
                                    " pf_min=" + str(pf_min) + " pf_mean=" + str(pf_mean) + " pf_max=" + str(pf_max))
            else:
                LOG_print_timestamp("[DINFOX MPMCM] * system=" + system_name + " node=" + node_name + " * Invalid payload")
        # R4S8CR.
        elif (board_id == __DINFOX_BOARD_ID_R4S8CR):
            # Electrical frame.
            if (node_ul_payload_size == (2 * __DINFOX_R4S8CR_UL_PAYLOAD_ELECTRICAL_SIZE)):
                r1st = (int(node_ul_payload[0:2], 16) >> 0) & 0x01
                r2st = (int(node_ul_payload[0:2], 16) >> 1) & 0x01
                r3st = (int(node_ul_payload[0:2], 16) >> 2) & 0x01
                r4st = (int(node_ul_payload[0:2], 16) >> 3) & 0x01
                r5st = (int(node_ul_payload[0:2], 16) >> 4) & 0x01
                r6st = (int(node_ul_payload[0:2], 16) >> 5) & 0x01
                r7st = (int(node_ul_payload[0:2], 16) >> 6) & 0x01
                r8st = (int(node_ul_payload[0:2], 16) >> 7) & 0x01
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                        INFLUX_DB_FIELD_RELAY_1_STATE : r1st,
                        INFLUX_DB_FIELD_RELAY_2_STATE : r2st,
                        INFLUX_DB_FIELD_RELAY_3_STATE : r3st,
                        INFLUX_DB_FIELD_RELAY_4_STATE : r4st,
                        INFLUX_DB_FIELD_RELAY_5_STATE : r5st,
                        INFLUX_DB_FIELD_RELAY_6_STATE : r6st,
                        INFLUX_DB_FIELD_RELAY_7_STATE : r7st,
                        INFLUX_DB_FIELD_RELAY_8_STATE : r8st
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                LOG_print_timestamp("[DINFOX R4S8CR] * Electrical payload * system=" + system_name + " node=" + node_name +
                                    " relay_1=" + str(r1st) + " relay_2=" + str(r2st) + " relay_3=" + str(r3st) + " relay_4=" + str(r4st) +
                                    " relay_5=" + str(r5st) + " relay_6=" + str(r6st) + " relay_7=" + str(r7st) + " relay_8=" + str(r8st))
            else:
                LOG_print_timestamp("[DINFOX R4S8CR] * system=" + system_name + " node=" + node_name + " * Invalid payload")
        # Unknown board ID.
        else:
            LOG_print_timestamp("[DINFOX] * system=" + system_name + " node=" + node_name + " * Unknown board ID")
    # Fill data base.
    if (len(json_body) > 0) :
        __DINFOX_add_tags(json_body, sigfox_ep_id, node_address, board_id, mpmcm_channel_index)
        INFLUX_DB_write_data(INFLUX_DB_DATABASE_DINFOX, json_body)
    else :
        LOG_print_timestamp("[DINFOX] * Invalid frame")