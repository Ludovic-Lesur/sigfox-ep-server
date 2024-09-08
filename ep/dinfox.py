from __future__ import print_function

from database.influx_db import *
from log import *
from ep.common import *
from datetime import date

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
__DINFOX_SYSTEM_3_NODE_ADDRESS = [0x00, 0x01, 0x08, 0x0C, 0x14, 0x1C]
__DINFOX_SYSTEM_3_NODE = ["DMM_0", "DIM_0", "BPSM_0", "UHFM_0", "SM_0", "MPMCM_0"]

__DINFOX_SYSTEM_4_NAME = "Linky rack"
__DINFOX_SYSTEM_4_NODE_ADDRESS = [0x00, 0x01, 0x08, 0x0C, 0x14, 0x1C]
__DINFOX_SYSTEM_4_NODE = ["DMM_0", "DIM_0", "BPSM_0", "UHFM_0", "SM_0", "MPMCM_0"]

__DINFOX_SYSTEM = [__DINFOX_SYSTEM_0_NAME, __DINFOX_SYSTEM_1_NAME, __DINFOX_SYSTEM_2_NAME, __DINFOX_SYSTEM_3_NAME, __DINFOX_SYSTEM_4_NAME]

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

__DINFOX_SM_UL_PAYLOAD_MONITORING_SIZE = 3
__DINFOX_SM_UL_PAYLOAD_ELECTRICAL_SIZE = 9
__DINFOX_SM_UL_PAYLOAD_SENSOR_SIZE = 2

__DINFOX_DMM_UL_PAYLOAD_MONITORING_SIZE = 7

__DINFOX_MPMCM_UL_PAYLOAD_SIZE_STATUS = 1
__DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_POWER_FACTOR = 4
__DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_ENERGY = 5
__DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_FREQUENCY = 6
__DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_VOLTAGE = 7
__DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_POWER = 9

__DINFOX_R4S8CR_UL_PAYLOAD_ELECTRICAL_SIZE = 2

__DINFOX_COMMON_UL_PAYLOAD_ERROR_STACK_SIZE = 10

### PUBLIC MACROS ###

# TrackFox EP-IDs.
DINFOX_EP_ID_LIST = ["4761", "479C", "47A7", "47EA", "4894"]

### LOCAL GLOBAL VARIABLES ###

dinfox_zero_energy_insertion_date = ["2000-01-01", "2000-01-01", "2000-01-01", "2000-01-01", "2000-01-01"]

### LOCAL FUNCTIONS ###

# Convert DINFox temperature representation to degrees.
def __DINFOX_get_degrees(dinfox_temperature) :
    return COMMON_one_complement_to_value(dinfox_temperature, 7)

# Convert DINFox voltage representation to mV.
def __DINFOX_get_mv(dinfox_voltage) :
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
def __DINFOX_get_ua(dinfox_current) :
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

# Convert DINFox electrical power representation to mW or mVA.
def __DINFOX_get_mw_mva(dinfox_electrical_power) :
    # Reset result.
    electrical_power_mw_mva = COMMON_ERROR_DATA
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
    return electrical_power_mw_mva

# Convert DINFox electrical energy representation to mWh or mVAh.
def __DINFOX_get_mwh_mvah(dinfox_electrical_energy) :
    # Reset result.
    electrical_energy_mwh_mvah = COMMON_ERROR_DATA
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
    return electrical_energy_mwh_mvah

# Convert DINFox power factor to floating number.
def __DINFOX_get_power_factor(dinfox_power_factor) :
    # Extract sign and value.
    sign = ((dinfox_power_factor >> 7) & 0x01)
    value = ((dinfox_power_factor >> 0) & 0x7F)
    # Convert.
    power_factor = ((-1) ** (sign)) * (value / 100.0)
    return power_factor

# Function performing Sigfox ID to DinFox system conversion.
def __DINFOX_get_system(sigfox_ep_id) :
    # Default is unknown.
    system_name = "unknown"
    if (sigfox_ep_id in DINFOX_EP_ID_LIST):
        # Get system name.
        system_name = __DINFOX_SYSTEM[DINFOX_EP_ID_LIST.index(sigfox_ep_id)]
    return system_name

# Function performing Sigfox ID and node address to node name conversion.
def __DINFOX_get_node(sigfox_ep_id, node_address) :
    # Default is unknown.
    node_name = "unknown"
    if (sigfox_ep_id in DINFOX_EP_ID_LIST):
        # Get system name.
        system_name = __DINFOX_SYSTEM[DINFOX_EP_ID_LIST.index(sigfox_ep_id)]
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
        elif (system_name == __DINFOX_SYSTEM_4_NAME):
            if (node_address in __DINFOX_SYSTEM_4_NODE_ADDRESS):
                # Get node name.
                node_name = __DINFOX_SYSTEM_4_NODE[__DINFOX_SYSTEM_4_NODE_ADDRESS.index(node_address)]
    return node_name

# Function adding the specific DinFox tags.
def __DINFOX_add_ul_tags(json_ul_data, sigfox_ep_id, node_address, board_id, mpmcm_channel_index) :
    # Get tags.
    node_name = __DINFOX_get_node(sigfox_ep_id, node_address)
    for idx in range(len(json_ul_data)) :
        if ("tags" in json_ul_data[idx]) :
            json_ul_data[idx]["tags"][INFLUX_DB_TAG_NODE_ADDRESS] = node_address
            json_ul_data[idx]["tags"][INFLUX_DB_TAG_NODE] = node_name
            json_ul_data[idx]["tags"][INFLUX_DB_TAG_BOARD_ID] = board_id
        else :
            json_ul_data[idx]["tags"] = {
                INFLUX_DB_TAG_NODE_ADDRESS : node_address,
                INFLUX_DB_TAG_NODE : node_name,
                INFLUX_DB_TAG_BOARD_ID : board_id
            }
        if (mpmcm_channel_index != COMMON_ERROR_DATA):
            json_ul_data[idx]["tags"][INFLUX_DB_TAG_CHANNEL] = mpmcm_channel_index

### PUBLIC FUNCTIONS ###

# Function adding the specific DinFox tags.
def DINFOX_add_ep_tag(json_ul_data, sigfox_ep_id) :
    for idx in range(len(json_ul_data)) :
        if ("tags" in json_ul_data[idx]) :
            json_ul_data[idx]["tags"][INFLUX_DB_TAG_SIGFOX_EP_ID] = sigfox_ep_id
            json_ul_data[idx]["tags"][INFLUX_DB_TAG_SYSTEM] = __DINFOX_get_system(sigfox_ep_id)
        else :
            json_ul_data[idx]["tags"] = {
                INFLUX_DB_TAG_SIGFOX_EP_ID : sigfox_ep_id,
                INFLUX_DB_TAG_SYSTEM : __DINFOX_get_system(sigfox_ep_id)
            }

# Function for parsing TrackFox device payload and fill database.
def DINFOX_parse_ul_payload(timestamp, sigfox_ep_id, ul_payload) :
    # Global variables.
    global dinfox_zero_energy_insertion_date
    # Init JSON object.
    json_ul_data = []
    # MPMCM specific tag.
    mpmcm_channel_index = COMMON_ERROR_DATA
    # Read node address and board ID.
    node_address = int(ul_payload[0:2], 16)
    board_id = int(ul_payload[2:4], 16)
    # Get system and node names for log print.
    system_name = __DINFOX_get_system(sigfox_ep_id)
    node_name = __DINFOX_get_node(sigfox_ep_id, node_address)
    # Extract node payload.
    node_ul_payload = ul_payload[(2 * __DINFOX_UL_PAYLOAD_HEADER_SIZE):]
    node_ul_payload_size = len(ul_payload) - (2 * __DINFOX_UL_PAYLOAD_HEADER_SIZE)
    # Common startup frame for all nodes.
    if (node_ul_payload_size == (2 * COMMON_UL_PAYLOAD_STARTUP_SIZE)):
        # Check marker to select between startup or action log.
        marker = ((int(node_ul_payload[0:2], 16) >> 4) & 0x0F);
        if (marker == 0x0F) :
            # Action log frame.
            downlink_hash = (int(node_ul_payload[0:4], 16) & 0x0FFF);
            register_address = int(node_ul_payload[4:6], 16)
            register_value = int(node_ul_payload[6:14], 16)
            node_access_status = int(node_ul_payload[14:16], 16)
            # Create JSON object.
            json_ul_data = [
            {
                "measurement": INFLUX_DB_MEASUREMENT_DOWNLINK,
                "time": timestamp,
                "fields": {
                   INFLUX_DB_FIELD_TIME_LAST_ACTION_LOG_DATA : timestamp,
                   INFLUX_DB_FIELD_DOWNLINK_HASH : downlink_hash,
                   INFLUX_DB_FIELD_REGISTER_ADDRESS : register_address,
                   INFLUX_DB_FIELD_REGISTER_VALUE : register_value,
                   INFLUX_DB_FIELD_NODE_ACCESS_STATUS : node_access_status
                },
            },
            {
                "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                "time": timestamp,
                "fields": {
                    INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                },
            }]
            LOG_print("[DINFOX] * Action log data * system=" + system_name + " node=" + node_name +
                      " downlink_hash=" + str(downlink_hash) + " register_address=" + str(register_address) + " register_value=" + str(register_value) + " node_access_status=" + str(node_access_status))
        else :
            # Create JSON object.
            result = COMMON_create_json_startup_data(timestamp, node_ul_payload)
            json_ul_data = result[0]
            log_data = result[1]
            LOG_print("[DINFOX] * Startup data * system=" + system_name + " node=" + node_name + " " + log_data)
    # Common error stack frame for all nodes.
    elif (node_ul_payload_size == (2 * __DINFOX_COMMON_UL_PAYLOAD_ERROR_STACK_SIZE)):
        result = COMMON_create_json_error_stack_data(timestamp, node_ul_payload, (__DINFOX_COMMON_UL_PAYLOAD_ERROR_STACK_SIZE / 2))
        json_ul_data = result[0]
        log_data = result[1]
        LOG_print("[DINFOX] * Error stack data * system=" + system_name + " node=" + node_name + " " + log_data)
    # Node-specific frames.
    else:
        # LVRM.
        if (board_id == __DINFOX_BOARD_ID_LVRM):
            # Monitoring frame.
            if (node_ul_payload_size == (2 * __DINFOX_LVRM_UL_PAYLOAD_MONITORING_SIZE)) :
                vmcu_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                tmcu_degrees = __DINFOX_get_degrees(int(node_ul_payload[4:6], 16)) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                # Create JSON object.
                json_ul_data = [
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
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
                if (tmcu_degrees != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
                LOG_print("[DINFOX LVRM] * Monitoring payload * system=" + system_name + " node=" + node_name +
                          " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC ")
            # Electrical frame.
            elif (node_ul_payload_size == (2 * __DINFOX_LVRM_UL_PAYLOAD_ELECTRICAL_SIZE)) :
                vcom_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16))  if (int(node_ul_payload[0:4], 16)  != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                vout_mv = __DINFOX_get_mv(int(node_ul_payload[4:8], 16))  if (int(node_ul_payload[4:8], 16)  != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                iout_ua = __DINFOX_get_ua(int(node_ul_payload[8:12], 16)) if (int(node_ul_payload[8:12], 16) != COMMON_ERROR_VALUE_CURRENT) else COMMON_ERROR_DATA
                rlstst = (int(node_ul_payload[12:14], 16) >> 0) & 0x03
                # Create JSON object.
                json_ul_data = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                        INFLUX_DB_FIELD_RELAY_STATE : rlstst
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
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VCOM] = vcom_mv
                if (vout_mv != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VOUT] = vout_mv
                if (iout_ua != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_IOUT] = iout_ua
                LOG_print("[DINFOX LVRM] * Electrical payload * system=" + system_name + " node=" + node_name +
                          " vcom=" + str(vcom_mv) + "mV vout=" + str(vout_mv) + "mV iout=" + str(iout_ua) + "uA relay=" + str(rlstst))
            else:
                LOG_print("[DINFOX LVRM] * system=" + system_name + " node=" + node_name + " * Invalid UL payload")
        # BPSM.
        elif (board_id == __DINFOX_BOARD_ID_BPSM):
            # Monitoring frame.
            if (node_ul_payload_size == (2 * __DINFOX_BPSM_UL_PAYLOAD_MONITORING_SIZE)) :
                vmcu_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                tmcu_degrees = __DINFOX_get_degrees(int(node_ul_payload[4:6], 16)) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                # Create JSON object.
                json_ul_data = [
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
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
                if (tmcu_degrees != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
                LOG_print("[DINFOX BPSM] * Monitoring payload * system=" + system_name + " node=" + node_name +
                          " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC ")
            # Electrical frame.
            elif (node_ul_payload_size == (2 * __DINFOX_BPSM_UL_PAYLOAD_ELECTRICAL_SIZE)) :
                vsrc_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16))  if (int(node_ul_payload[0:4], 16)  != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                vstr_mv = __DINFOX_get_mv(int(node_ul_payload[4:8], 16))  if (int(node_ul_payload[4:8], 16)  != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                vbkp_mv = __DINFOX_get_mv(int(node_ul_payload[8:12], 16)) if (int(node_ul_payload[8:12], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                chrgst = (int(node_ul_payload[12:14], 16) >> 4) & 0x03
                chenst = (int(node_ul_payload[12:14], 16) >> 2) & 0x03
                bkenst = (int(node_ul_payload[12:14], 16) >> 0) & 0x03
                # Create JSON object.
                json_ul_data = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                        INFLUX_DB_FIELD_CHARGE_STATUS : chrgst,
                        INFLUX_DB_FIELD_CHARGE_ENABLE : chenst,
                        INFLUX_DB_FIELD_BACKUP_ENABLE : bkenst
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
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VSRC] = vsrc_mv
                if (vstr_mv != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VSTR] = vstr_mv
                if (vbkp_mv != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VBKP] = vbkp_mv
                LOG_print("[DINFOX BPSM] * Electrical payload * system=" + system_name + " node=" + node_name +
                          " vsrc=" + str(vsrc_mv) + "mV vstr=" + str(vstr_mv) + "mV vbkp=" + str(vbkp_mv) +
                          "mV charge_status=" + str(chrgst) + " charge_enable=" + str(chenst) + " backup_enable=" + str(bkenst))
            else:
                LOG_print("[DINFOX BPSM] * system=" + system_name + " node=" + node_name + " * Invalid UL payload")
        # DDRM.
        elif (board_id == __DINFOX_BOARD_ID_DDRM):
            # Monitoring frame.
            if (node_ul_payload_size == (2 * __DINFOX_DDRM_UL_PAYLOAD_MONITORING_SIZE)) :
                vmcu_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                tmcu_degrees = __DINFOX_get_degrees(int(node_ul_payload[4:6], 16)) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                # Create JSON object.
                json_ul_data = [
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
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
                if (tmcu_degrees != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
                LOG_print("[DINFOX DDRM] * Monitoring payload * system=" + system_name + " node=" + node_name +
                          " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC ")
            # Electrical frame.
            elif (node_ul_payload_size == (2 * __DINFOX_DDRM_UL_PAYLOAD_ELECTRICAL_SIZE)) :
                vin_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                vout_mv = __DINFOX_get_mv(int(node_ul_payload[4:8], 16)) if (int(node_ul_payload[4:8], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                iout_ua = __DINFOX_get_ua(int(node_ul_payload[8:12], 16)) if (int(node_ul_payload[8:12], 16) != COMMON_ERROR_VALUE_CURRENT) else COMMON_ERROR_DATA
                ddenst = (int(node_ul_payload[12:14], 16) >> 0) & 0x03
                # Create JSON object.
                json_ul_data = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                        INFLUX_DB_FIELD_DC_DC_STATE : ddenst
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
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VIN] = vin_mv
                if (vout_mv != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VOUT] = vout_mv
                if (iout_ua != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_IOUT] = iout_ua
                LOG_print("[DINFOX DDRM] * Electrical payload * system=" + system_name + " node=" + node_name +
                          " vin=" + str(vin_mv) + "mV vout=" + str(vout_mv) + "mV iout=" + str(iout_ua) + "uA dc_dc=" + str(ddenst))
            else:
                LOG_print("[DINFOX DDRM] * system=" + system_name + " node=" + node_name + " * Invalid UL payload")
        # UHFM.
        elif (board_id == __DINFOX_BOARD_ID_UHFM):
            # Monitoring frame.
            if (node_ul_payload_size == (2 * __DINFOX_UHFM_UL_PAYLOAD_MONITORING_SIZE)) :
                vmcu_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                tmcu_degrees = __DINFOX_get_degrees(int(node_ul_payload[4:6], 16)) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                vrf_mv_tx = __DINFOX_get_mv(int(node_ul_payload[6:10], 16)) if (int(node_ul_payload[6:10], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                vrf_mv_rx = __DINFOX_get_mv(int(node_ul_payload[10:14], 16)) if (int(node_ul_payload[10:14], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                # Create JSON object.
                json_ul_data = [
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
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
                if (tmcu_degrees != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
                if (vrf_mv_tx != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VRF_TX] = vrf_mv_tx
                if (vrf_mv_rx != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VRF_RX] = vrf_mv_rx
                LOG_print("[DINFOX UHFM] * Monitoring payload * system=" + system_name + " node=" + node_name +
                          " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC vrf_tx=" + str(vrf_mv_tx) + "mV vrf_rx=" + str(vrf_mv_rx) + "mV")
            else:
                LOG_print("[DINFOX UHFM] * system=" + system_name + " node=" + node_name + " * Invalid UL payload")
        # GPSM.
        elif (board_id == __DINFOX_BOARD_ID_GPSM):
            # Monitoring frame.
            if (node_ul_payload_size == (2 * __DINFOX_GPSM_UL_PAYLOAD_MONITORING_SIZE)) :
                vmcu_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                tmcu_degrees = __DINFOX_get_degrees(int(node_ul_payload[4:6], 16)) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                vgps_mv = __DINFOX_get_mv(int(node_ul_payload[6:10], 16)) if (int(node_ul_payload[6:10], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                vant_mv = __DINFOX_get_mv(int(node_ul_payload[10:14], 16)) if (int(node_ul_payload[10:14], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                # Create JSON object.
                json_ul_data = [
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
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
                if (tmcu_degrees != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
                if (vgps_mv != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VGPS] = vgps_mv
                if (vant_mv != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VANT] = vant_mv
                LOG_print("[DINFOX GPSM] * Monitoring payload * system=" + system_name + " node=" + node_name +
                          " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC vgps=" + str(vgps_mv) + "mV vant=" + str(vant_mv) + "mV")
            else:
                LOG_print("[DINFOX GPSM] * system=" + system_name + " node=" + node_name + " * Invalid UL payload")
        # SM.
        elif (board_id == __DINFOX_BOARD_ID_SM):
            # Monitoring frame.
            if (node_ul_payload_size == (2 * __DINFOX_SM_UL_PAYLOAD_MONITORING_SIZE)) :
                vmcu_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16)) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                tmcu_degrees = __DINFOX_get_degrees(int(node_ul_payload[4:6], 16)) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                # Create JSON object.
                json_ul_data = [
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
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
                if (tmcu_degrees != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
                LOG_print("[DINFOX SM] * Monitoring payload * system=" + system_name + " node=" + node_name + " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC")
            # External inputs frame.
            if (node_ul_payload_size == (2 * __DINFOX_SM_UL_PAYLOAD_ELECTRICAL_SIZE)) :
                ain0_mv = __DINFOX_get_mv(int(node_ul_payload[0:4], 16))   if int(node_ul_payload[0:4], 16)   != COMMON_ERROR_VALUE_VOLTAGE else COMMON_ERROR_DATA
                ain1_mv = __DINFOX_get_mv(int(node_ul_payload[4:8], 16))   if int(node_ul_payload[4:8], 16)   != COMMON_ERROR_VALUE_VOLTAGE else COMMON_ERROR_DATA
                ain2_mv = __DINFOX_get_mv(int(node_ul_payload[8:12], 16))  if int(node_ul_payload[8:12], 16)  != COMMON_ERROR_VALUE_VOLTAGE else COMMON_ERROR_DATA
                ain3_mv = __DINFOX_get_mv(int(node_ul_payload[12:16], 16)) if int(node_ul_payload[12:16], 16) != COMMON_ERROR_VALUE_VOLTAGE else COMMON_ERROR_DATA
                dio0 = (int(node_ul_payload[16:18], 16) >> 0) & 0x03
                dio1 = (int(node_ul_payload[16:18], 16) >> 2) & 0x03
                dio2 = (int(node_ul_payload[16:18], 16) >> 4) & 0x03
                dio3 = (int(node_ul_payload[16:18], 16) >> 6) & 0x03
                # Create JSON object.
                json_ul_data = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
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
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_AIN0] = ain0_mv
                if (ain1_mv != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_AIN1] = ain1_mv
                if (ain2_mv != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_AIN2] = ain2_mv
                if (ain3_mv != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_AIN3] = ain3_mv
                LOG_print("[DINFOX SM] * Electrical payload * system=" + system_name + " node=" + node_name +
                          " ain0=" + str(ain0_mv) + "mV ain1=" + str(ain1_mv) + "mV ain2=" + str(ain2_mv) + "mV ain3=" + str(ain3_mv) +
                          " dio0=" + str(dio0) + " dio1=" + str(dio1) + " dio2=" + str(dio2) + " dio3=" + str(dio3))
            # Digital sensors frame.
            elif (node_ul_payload_size == (2 * __DINFOX_SM_UL_PAYLOAD_SENSOR_SIZE)) :
                tamb_degrees = __DINFOX_get_degrees(int(node_ul_payload[0:2], 16)) if (int(node_ul_payload[0:2], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                hamb_degrees = int(node_ul_payload[2:4], 16) if (int(node_ul_payload[2:4], 16) != COMMON_ERROR_VALUE_HUMIDITY) else COMMON_ERROR_DATA
                # Create JSON object.
                json_ul_data = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_SENSOR,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_SENSOR_DATA : timestamp
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
                if (tamb_degrees != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_TAMB] = tamb_degrees
                if (hamb_degrees != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_HAMB] = hamb_degrees
                LOG_print("[DINFOX SM] * Sensor payload * system=" + system_name + " node=" + node_name + " tamb=" + str(tamb_degrees) + "dC hamb=" + str(hamb_degrees) + "%")
            else:
                LOG_print("[DINFOX SM] * system=" + system_name + " node=" + node_name + " * Invalid UL payload")
        # DMM.
        elif (board_id == __DINFOX_BOARD_ID_DMM):
            # Monitoring frame.
            if (node_ul_payload_size == (2 * __DINFOX_DMM_UL_PAYLOAD_MONITORING_SIZE)) :
                vrs_mv =  __DINFOX_get_mv(int(node_ul_payload[0:4], 16))  if (int(node_ul_payload[0:4], 16)  != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                vhmi_mv = __DINFOX_get_mv(int(node_ul_payload[4:8], 16))  if (int(node_ul_payload[4:8], 16)  != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                vusb_mv = __DINFOX_get_mv(int(node_ul_payload[8:12], 16)) if (int(node_ul_payload[8:12], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                nodes_count = int(node_ul_payload[12:14], 16)
                # Create JSON object.
                json_ul_data = [
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
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VRS] = vrs_mv
                if (vhmi_mv != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VHMI] = vhmi_mv
                if (vusb_mv != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VUSB] = vusb_mv
                LOG_print("[DINFOX DMM] * Monitoring payload * system=" + system_name + " node=" + node_name +
                          " vrs=" + str(vrs_mv) + "mV vhmi=" + str(vhmi_mv) + "mV vusb=" + str(vusb_mv) + "mV nodes_count=" + str(nodes_count))
            else:
                LOG_print("[DINFOX DMM] * system=" + system_name + " node=" + node_name + " * Invalid UL payload")
        # MPMCM.
        elif (board_id == __DINFOX_BOARD_ID_MPMCM):
            # Status frame.
            if (node_ul_payload_size == (2 * __DINFOX_MPMCM_UL_PAYLOAD_SIZE_STATUS)) :
                mvd =  (int(node_ul_payload[0:2], 16) >> 5) & 0x01
                ticd = (int(node_ul_payload[0:2], 16) >> 4) & 0x01
                ch4d = (int(node_ul_payload[0:2], 16) >> 3) & 0x01
                ch3d = (int(node_ul_payload[0:2], 16) >> 2) & 0x01
                ch2d = (int(node_ul_payload[0:2], 16) >> 1) & 0x01
                ch1d = (int(node_ul_payload[0:2], 16) >> 0) & 0x01
                # Create JSON object.
                json_ul_data = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                        INFLUX_DB_FIELD_MAINS_VOLTAGE_DETECT : mvd,
                        INFLUX_DB_FIELD_LINKY_TIC_DETECT : ticd,
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
                LOG_print("[DINFOX MPMCM] * Electrical mains voltage payload * system=" + system_name + " node=" + node_name +
                          " mvd=" + str(mvd) + " ticd=" + str(ticd) + " ch1d=" + str(ch1d) + " ch2d=" + str(ch2d) + " ch3d=" + str(ch3d) + " ch4d=" + str(ch4d))
            # Mains voltage frame.
            elif (node_ul_payload_size == (2 * __DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_VOLTAGE)) :
                mpmcm_channel_index = (int(node_ul_payload[0:2], 16) >> 0) & 0x07
                vrms_min =  __DINFOX_get_mv(int(node_ul_payload[2:6], 16))   if (int(node_ul_payload[2:6], 16)   != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                vrms_mean = __DINFOX_get_mv(int(node_ul_payload[6:10], 16))  if (int(node_ul_payload[6:10], 16)  != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                vrms_max =  __DINFOX_get_mv(int(node_ul_payload[10:14], 16)) if (int(node_ul_payload[10:14], 16) != COMMON_ERROR_VALUE_VOLTAGE) else COMMON_ERROR_DATA
                # Create JSON object.
                json_ul_data = [
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
                if (vrms_min != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VRMS_MIN] = vrms_min
                if (vrms_mean != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VRMS_MEAN] = vrms_mean
                if (vrms_max != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_VRMS_MAX] = vrms_max
                LOG_print("[DINFOX MPMCM] * Electrical mains voltage payload * system=" + system_name + " node=" + node_name + " channel=" + str(mpmcm_channel_index) +
                          " vrms_min=" + str(vrms_min) + "mV vrms_mean=" + str(vrms_mean) + "mV vrms_max=" + str(vrms_max) + "mV")
            # Mains frequency frame.
            elif (node_ul_payload_size == (2 * __DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_FREQUENCY)) :
                f_min =  (int(node_ul_payload[0:4], 16) / 100.0)  if (int(node_ul_payload[0:4], 16)  != COMMON_ERROR_VALUE_FREQUENCY_16BITS) else COMMON_ERROR_DATA
                f_mean = (int(node_ul_payload[4:8], 16) / 100.0)  if (int(node_ul_payload[4:8], 16)  != COMMON_ERROR_VALUE_FREQUENCY_16BITS) else COMMON_ERROR_DATA
                f_max =  (int(node_ul_payload[8:12], 16) / 100.0) if (int(node_ul_payload[8:12], 16) != COMMON_ERROR_VALUE_FREQUENCY_16BITS) else COMMON_ERROR_DATA
                # Create JSON object.
                json_ul_data = [
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
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_FREQUENCY_MIN] = f_min
                if (f_mean != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_FREQUENCY_MEAN] = f_mean
                if (f_max != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_FREQUENCY_MAX] = f_max
                LOG_print("[DINFOX MPMCM] * Electrical mains frequency payload * system=" + system_name + " node=" + node_name +
                          " f_min=" + str(f_min) + "Hz f_mean=" + str(f_mean) + "Hz f_max=" + str(f_max) + "Hz")
            # Mains power frame.
            elif (node_ul_payload_size == (2 * __DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_POWER)) :
                mpmcm_channel_index = (int(node_ul_payload[0:2], 16) >> 0) & 0x07
                pact_mean = __DINFOX_get_mw_mva(int(node_ul_payload[2:6], 16))   if (int(node_ul_payload[2:6], 16)   != COMMON_ERROR_VALUE_ELECTRICAL_POWER) else COMMON_ERROR_DATA
                pact_max =  __DINFOX_get_mw_mva(int(node_ul_payload[6:10], 16))  if (int(node_ul_payload[6:10], 16)  != COMMON_ERROR_VALUE_ELECTRICAL_POWER) else COMMON_ERROR_DATA
                papp_mean = __DINFOX_get_mw_mva(int(node_ul_payload[10:14], 16)) if (int(node_ul_payload[10:14], 16) != COMMON_ERROR_VALUE_ELECTRICAL_POWER) else COMMON_ERROR_DATA
                papp_max =  __DINFOX_get_mw_mva(int(node_ul_payload[14:18], 16)) if (int(node_ul_payload[14:18], 16) != COMMON_ERROR_VALUE_ELECTRICAL_POWER) else COMMON_ERROR_DATA
                # Create JSON object.
                json_ul_data = [
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
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_PACT_MEAN] = pact_mean
                if (pact_max != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_PACT_MAX] = pact_max
                if (papp_mean != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_PAPP_MEAN] = papp_mean
                if (papp_max != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_PAPP_MAX] = papp_max
                LOG_print("[DINFOX MPMCM] * Electrical mains power payload * system=" + system_name + " node=" + node_name + " channel=" + str(mpmcm_channel_index) +
                          " pact_mean=" + str(pact_mean) + "mW pact_max=" + str(pact_max) + "mW papp_mean=" + str(papp_mean) + "mW papp_max=" + str(papp_max) + "mW")
            # Mains power factor frame.
            elif (node_ul_payload_size == (2 * __DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_POWER_FACTOR)) :
                mpmcm_channel_index = (int(node_ul_payload[0:2], 16) >> 0) & 0x07
                pf_min =  __DINFOX_get_power_factor(int(node_ul_payload[2:4], 16)) if (int(node_ul_payload[2:4], 16) != COMMON_ERROR_VALUE_POWER_FACTOR) else COMMON_ERROR_DATA
                pf_mean = __DINFOX_get_power_factor(int(node_ul_payload[4:6], 16)) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_POWER_FACTOR) else COMMON_ERROR_DATA
                pf_max =  __DINFOX_get_power_factor(int(node_ul_payload[6:8], 16)) if (int(node_ul_payload[6:8], 16) != COMMON_ERROR_VALUE_POWER_FACTOR) else COMMON_ERROR_DATA
                # Create JSON object.
                json_ul_data = [
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
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_PF_MIN] = pf_min
                if (pf_mean != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_PF_MEAN] = pf_mean
                if (pf_max != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_PF_MAX] = pf_max
                LOG_print("[DINFOX MPMCM] * Electrical mains frequency payload * system=" + system_name + " node=" + node_name + " channel=" + str(mpmcm_channel_index) +
                          " pf_min=" + str(pf_min) + " pf_mean=" + str(pf_mean) + " pf_max=" + str(pf_max))
            # Mains energy frame.
            elif (node_ul_payload_size == (2 * __DINFOX_MPMCM_UL_PAYLOAD_SIZE_MAINS_ENERGY)) :
                mpmcm_channel_index = (int(node_ul_payload[0:2], 16) >> 0) & 0x07
                eact = __DINFOX_get_mwh_mvah(int(node_ul_payload[2:6], 16)) if (int(node_ul_payload[2:6], 16) != COMMON_ERROR_VALUE_ELECTRICAL_ENERGY) else COMMON_ERROR_DATA
                eapp = __DINFOX_get_mwh_mvah(int(node_ul_payload[6:10], 16)) if (int(node_ul_payload[6:10], 16) != COMMON_ERROR_VALUE_ELECTRICAL_ENERGY) else COMMON_ERROR_DATA
                # Create JSON object.
                json_ul_data = [
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
                # Check if day changed.
                if (str(date.today()) != dinfox_zero_energy_insertion_date[mpmcm_channel_index]) :
                    # Update local variable.
                    dinfox_zero_energy_insertion_date[mpmcm_channel_index] = str(date.today())
                    # Create additional point.
                    json_zero_energy = {
                        "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                        "time": (timestamp + 1),
                        "fields": {
                            INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                            INFLUX_DB_FIELD_EACT : 0,
                            INFLUX_DB_FIELD_EAPP : 0
                        }
                    }
                    # Insert additional point.
                    json_ul_data.append(json_zero_energy)
                    LOG_print("[DINFOX MPMCM] Daily zero energy insertion on channel " + str(mpmcm_channel_index))
                # Add valid fields to JSON.
                if (eact != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_EACT] = eact
                if (eapp != COMMON_ERROR_DATA) :
                    json_ul_data[0]["fields"][INFLUX_DB_FIELD_EAPP] = eapp
                LOG_print("[DINFOX MPMCM] * Electrical mains energy payload * system=" + system_name + " node=" + node_name + " channel=" + str(mpmcm_channel_index) +
                          " eact=" + str(eact) + "mWh eapp=" + str(eapp) + "mVAh")
            else:
                LOG_print("[DINFOX MPMCM] * system=" + system_name + " node=" + node_name + " * Invalid UL payload")
        # R4S8CR.
        elif (board_id == __DINFOX_BOARD_ID_R4S8CR):
            # Electrical frame.
            if (node_ul_payload_size == (2 * __DINFOX_R4S8CR_UL_PAYLOAD_ELECTRICAL_SIZE)) :
                r8stst = (int(node_ul_payload[0:2], 16) >> 6) & 0x03
                r7stst = (int(node_ul_payload[0:2], 16) >> 4) & 0x03
                r6stst = (int(node_ul_payload[0:2], 16) >> 2) & 0x03
                r5stst = (int(node_ul_payload[0:2], 16) >> 0) & 0x03
                r4stst = (int(node_ul_payload[2:4], 16) >> 6) & 0x03
                r3stst = (int(node_ul_payload[2:4], 16) >> 4) & 0x03
                r2stst = (int(node_ul_payload[2:4], 16) >> 2) & 0x03
                r1stst = (int(node_ul_payload[2:4], 16) >> 0) & 0x03
                # Create JSON object.
                json_ul_data = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                        INFLUX_DB_FIELD_RELAY_1_STATE : r1stst,
                        INFLUX_DB_FIELD_RELAY_2_STATE : r2stst,
                        INFLUX_DB_FIELD_RELAY_3_STATE : r3stst,
                        INFLUX_DB_FIELD_RELAY_4_STATE : r4stst,
                        INFLUX_DB_FIELD_RELAY_5_STATE : r5stst,
                        INFLUX_DB_FIELD_RELAY_6_STATE : r6stst,
                        INFLUX_DB_FIELD_RELAY_7_STATE : r7stst,
                        INFLUX_DB_FIELD_RELAY_8_STATE : r8stst
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_METADATA,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
                    },
                }]
                LOG_print("[DINFOX R4S8CR] * Electrical payload * system=" + system_name + " node=" + node_name +
                          " relay_1=" + str(r1stst) + " relay_2=" + str(r2stst) + " relay_3=" + str(r3stst) + " relay_4=" + str(r4stst) +
                          " relay_5=" + str(r5stst) + " relay_6=" + str(r6stst) + " relay_7=" + str(r7stst) + " relay_8=" + str(r8stst))
            else:
                LOG_print("[DINFOX R4S8CR] * system=" + system_name + " node=" + node_name + " * Invalid UL payload")
        # Unknown board ID.
        else:
            LOG_print("[DINFOX] * system=" + system_name + " node=" + node_name + " * Unknown board ID")
    # Add specific uplink tags.
    __DINFOX_add_ul_tags(json_ul_data, sigfox_ep_id, node_address, board_id, mpmcm_channel_index)
    return json_ul_data
               
# Returns the default downlink payload to sent back to the device.
def DINFOX_get_default_dl_payload(sigfox_ep_id) :
    # Local variables.
    dl_payload = []
    if (sigfox_ep_id in DINFOX_EP_ID_LIST) :
        dl_payload = "0000000000000000"
    return dl_payload
