from __future__ import print_function

from common import *
from influx_db import *
from log import *

### LOCAL MACROS ###

# DinFox tags.
__DINFOX_SYSTEM_TEST_BENCH_NAME = "Test_bench"
__DINFOX_SYSTEM_TEST_BENCH_NODE_ADDRESS = ["00", "01", "08", "0C", "10", "14", "20", "21", "30"]
__DINFOX_SYSTEM_TEST_BENCH_NODE = ["DMM_0", "DIM_0", "BPSM_0", "UHFM_0", "GPSM_0", "SM_0", "LVRM_0", "LVRM_1", "DDRM_0"]

__DINFOX_SYSTEM_PRAT_ALBIS_NAME = "Prat_Albis"
__DINFOX_SYSTEM_PRAT_ALBIS_NODE_ADDRESS = ["00", "01", "08", "0C", "70"]
__DINFOX_SYSTEM_PRAT_ALBIS_NODE = ["DMM_0", "DIM_0", "BPSM_0", "UHFM_0", "R4S8CR_0"]

__DINFOX_SYSTEM_SOLAR_RACK_NAME = "Solar_rack"
__DINFOX_SYSTEM_SOLAR_RACK_NODE_ADDRESS = ["00", "01", "08", "0C", "20", "30", "31"]
__DINFOX_SYSTEM_SOLAR_RACK_NODE = ["DMM_0", "DIM_0", "BPSM_0", "UHFM_0", "LVRM_0", "DDRM_0", "DDRM_1"]

__DINFOX_SYSTEM = [__DINFOX_SYSTEM_TEST_BENCH_NAME, __DINFOX_SYSTEM_PRAT_ALBIS_NAME, __DINFOX_SYSTEM_SOLAR_RACK_NAME, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A","N/A"]

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
__DINFOX_LVRM_UL_PAYLOAD_DATA_SIZE = 7

__DINFOX_BPSM_UL_PAYLOAD_MONITORING_SIZE = 3
__DINFOX_BPSM_UL_PAYLOAD_DATA_SIZE = 7

__DINFOX_DDRM_UL_PAYLOAD_MONITORING_SIZE = 3
__DINFOX_DDRM_UL_PAYLOAD_DATA_SIZE = 7

__DINFOX_UHFM_UL_PAYLOAD_MONITORING_SIZE = 5

__DINFOX_GPSM_UL_PAYLOAD_MONITORING_SIZE = 7

### PUBLIC MACROS ###

# TrackFox EP-IDs.
DINFOX_EP_ID = ["4761", "479C", "47A7", "47EA", "4894", "48AA", "48CB", "48E1", "4928", "492F"]

### LOCAL FUNCTIONS ###

# Function performing Sigfox ID to DinFox system and node conversion.
def __DINFOX_get_system_and_node(sigfox_ep_id, node_address):
    # Default is unknown.
    system_name = "unknown"
    node_name = "unknown"
    if (sigfox_ep_id in DINFOX_EP_ID):
        # Get system name.
        system_name = __DINFOX_SYSTEM[DINFOX_EP_ID.index(sigfox_ep_id)]
        # Search node list.
        if (system_name == __DINFOX_SYSTEM_TEST_BENCH_NAME):
            if (node_address in __DINFOX_SYSTEM_TEST_BENCH_NODE_ADDRESS):
                # Get node name.
                node_name = __DINFOX_SYSTEM_TEST_BENCH_NODE[__DINFOX_SYSTEM_TEST_BENCH_NODE_ADDRESS.index(node_address)]
        elif (system_name == __DINFOX_SYSTEM_PRAT_ALBIS_NAME):
            if (node_address in __DINFOX_SYSTEM_PRAT_ALBIS_NODE_ADDRESS):
                # Get node name.
                node_name = __DINFOX_SYSTEM_PRAT_ALBIS_NODE[__DINFOX_SYSTEM_PRAT_ALBIS_NODE_ADDRESS.index(node_address)]
        elif (system_name == __DINFOX_SYSTEM_SOLAR_RACK_NAME):
            if (node_address in __DINFOX_SYSTEM_SOLAR_RACK_NODE_ADDRESS):
                # Get node name.
                node_name = __DINFOX_SYSTEM_SOLAR_RACK_NODE[__DINFOX_SYSTEM_SOLAR_RACK_NODE_ADDRESS.index(node_address)]    
    return system_name, node_name

# Function adding the specific DinFox tags.
def __DINFOX_add_tags(json_body, sigfox_ep_id, node_address, board_id):
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

### PUBLIC FUNCTIONS ###

# Function for parsing TrackFox device payload and fill database.
def DINFOX_fill_data_base(timestamp, sigfox_ep_id, ul_payload):
    # Init JSON object.
    json_body = []
    # Read node address and board ID.
    node_address = ul_payload[0:2]
    board_id = ul_payload[2:4]
    board_id_int = int(board_id, 16)
    # Get system and node names for log print.
    result = __DINFOX_get_system_and_node(sigfox_ep_id, node_address)
    system_name = result[0]
    node_name = result[1]
    # Extract node payload.
    node_ul_payload = ul_payload[(2 * __DINFOX_UL_PAYLOAD_HEADER_SIZE):]
    print(node_ul_payload)
    node_ul_payload_size = len(ul_payload) - (2 * __DINFOX_UL_PAYLOAD_HEADER_SIZE)
    # Common startup frame for all nodes.
    if (node_ul_payload_size == (2 * COMMON_STARTUP_DATA_LENGTH_BYTES)):
        # Create JSON object.
        result = COMMON_create_json_startup_data(timestamp, node_ul_payload)
        json_body = result[0]
        log_data = result[1]
        LOG_print_timestamp("[DINFOX] * Startup data * system=" + system_name + " node=" + node_name + " " + log_data)
    else:
        # LVRM.
        if (board_id_int == __DINFOX_BOARD_ID_LVRM):
            # Monitoring payload.
            if (node_ul_payload_size == (2 * __DINFOX_LVRM_UL_PAYLOAD_MONITORING_SIZE)):
                vmcu_mv = int(node_ul_payload[0:4], 16) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                tmcu_degrees = COMMON_one_complement_to_value(int(node_ul_payload[4:6], 16), 7) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
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
                    "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
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
                LOG_print_timestamp("[DINFOX LVRM] * Monitoring payload * system=" + system_name + " node=" + node_name + " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC ")
            # Data payload.
            elif (node_ul_payload_size == (2 * __DINFOX_LVRM_UL_PAYLOAD_DATA_SIZE)):
                vcom_mv = int(node_ul_payload[0:4], 16) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                vout_mv = int(node_ul_payload[4:8], 16) if (int(node_ul_payload[4:8], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                tmp = ((int(node_ul_payload[8:14], 16)) >> 1) & 0x7FFFFF
                iout_ua = tmp if (tmp != COMMON_ERROR_VALUE_ANALOG_23BITS) else COMMON_ERROR_DATA
                relay_state = (int(node_ul_payload[12:14], 16) >> 0) & 0x01
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                        INFLUX_DB_FIELD_RELAY_STATE : relay_state
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
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
                LOG_print_timestamp("[DINFOX LVRM] * Electrical payload * system=" + system_name + " node=" + node_name + " vcom=" + str(vcom_mv) + "mV vout=" + str(vout_mv) + "mV iout=" + str(iout_ua) + "uA relay=" + str(relay_state))
            else:
                LOG_print_timestamp("[DINFOX LVRM] * system=" + system_name + " node=" + node_name + " * Invalid payload")
        # BPSM.
        elif (board_id_int == __DINFOX_BOARD_ID_BPSM):
            # Monitoring payload.
            if (node_ul_payload_size == (2 * __DINFOX_BPSM_UL_PAYLOAD_MONITORING_SIZE)):
                vmcu_mv = int(node_ul_payload[0:4], 16) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                tmcu_degrees = COMMON_one_complement_to_value(int(node_ul_payload[4:6], 16), 7) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
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
                    "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
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
                LOG_print_timestamp("[DINFOX BPSM] * Monitoring payload * system=" + system_name + " node=" + node_name + " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC ")
            # Data payload.
            elif (node_ul_payload_size == (2 * __DINFOX_BPSM_UL_PAYLOAD_DATA_SIZE)):
                vsrc_mv = int(node_ul_payload[0:4], 16) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                vstr_mv = int(node_ul_payload[4:8], 16) if (int(node_ul_payload[4:8], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                vbkp_mv = int(node_ul_payload[8:12], 16) if (int(node_ul_payload[8:12], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                charge_status = (int(node_ul_payload[12:14], 16) >> 0) & 0x01
                charge_enable = (int(node_ul_payload[12:14], 16) >> 1) & 0x01
                backup_enable = (int(node_ul_payload[12:14], 16) >> 2) & 0x01
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                        INFLUX_DB_FIELD_CHARGE_STATUS : charge_status,
                        INFLUX_DB_FIELD_CHARGE_ENABLE : charge_enable,
                        INFLUX_DB_FIELD_BACKUP_ENABLE : backup_enable
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
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
                LOG_print_timestamp("[DINFOX BPSM] * Electrical payload * system=" + system_name + " node=" + node_name + " vsrc=" + str(vsrc_mv) + "mV vstr=" + str(vstr_mv) + "mV vbkp=" + str(vbkp_mv) + "mV charge_status=" + str(charge_status) + " charge_enable=" + str(charge_enable) + " backup_enable=" + str(backup_enable))
            else:
                LOG_print_timestamp("[DINFOX BPSM] * system=" + system_name + " node=" + node_name + " * Invalid payload")
        # DDRM.
        elif (board_id_int == __DINFOX_BOARD_ID_DDRM):
            # Monitoring payload.
            if (node_ul_payload_size == (2 * __DINFOX_DDRM_UL_PAYLOAD_MONITORING_SIZE)):
                vmcu_mv = int(node_ul_payload[0:4], 16) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                tmcu_degrees = COMMON_one_complement_to_value(int(node_ul_payload[4:6], 16), 7) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
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
                    "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
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
                LOG_print_timestamp("[DINFOX DDRM] * Monitoring payload * system=" + system_name + " node=" + node_name + " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC ")
            # Data payload.
            elif (node_ul_payload_size == (2 * __DINFOX_DDRM_UL_PAYLOAD_DATA_SIZE)):
                vin_mv = int(node_ul_payload[0:4], 16) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                vout_mv = int(node_ul_payload[4:8], 16) if (int(node_ul_payload[4:8], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                tmp = ((int(node_ul_payload[8:14], 16)) >> 1) & 0x7FFFFF
                iout_ua = tmp if (tmp != COMMON_ERROR_VALUE_ANALOG_23BITS) else COMMON_ERROR_DATA
                dc_dc_state = (int(node_ul_payload[12:14], 16) >> 0) & 0x01
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_ELECTRICAL,
                    "time": timestamp,
                    "fields": {
                        INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA : timestamp,
                        INFLUX_DB_FIELD_DC_DC_STATE : dc_dc_state
                    },
                },
                {
                    "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
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
                LOG_print_timestamp("[DINFOX DDRM] * Electrical payload * system=" + system_name + " node=" + node_name + " vin=" + str(vin_mv) + "mV vout=" + str(vout_mv) + "mV iout=" + str(iout_ua) + "uA dc_dc=" + str(dc_dc_state))
            else:
                LOG_print_timestamp("[DINFOX DDRM] * system=" + system_name + " node=" + node_name + " * Invalid payload")
        # UHFM.
        if (board_id_int == __DINFOX_BOARD_ID_UHFM):
            # Monitoring payload.
            if (node_ul_payload_size == (2 * __DINFOX_UHFM_UL_PAYLOAD_MONITORING_SIZE)):
                vmcu_mv = int(node_ul_payload[0:4], 16) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                tmcu_degrees = COMMON_one_complement_to_value(int(node_ul_payload[4:6], 16), 7) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                vrf_mv = int(node_ul_payload[6:10], 16) if (int(node_ul_payload[6:10], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
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
                    "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
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
                if (vrf_mv != COMMON_ERROR_DATA) :
                    json_body[0]["fields"][INFLUX_DB_FIELD_VRF] = vrf_mv
                LOG_print_timestamp("[DINFOX UHFM] * Monitoring payload * system=" + system_name + " node=" + node_name + " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC vrf=" + str(vrf_mv) + "mV")
            else:
                LOG_print_timestamp("[DINFOX UHFM] * system=" + system_name + " node=" + node_name + " * Invalid payload")
        # GPSM.
        if (board_id_int == __DINFOX_BOARD_ID_GPSM):
            # Monitoring payload.
            if (node_ul_payload_size == (2 * __DINFOX_GPSM_UL_PAYLOAD_MONITORING_SIZE)):
                vmcu_mv = int(node_ul_payload[0:4], 16) if (int(node_ul_payload[0:4], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                tmcu_degrees = COMMON_one_complement_to_value(int(node_ul_payload[4:6], 16), 7) if (int(node_ul_payload[4:6], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
                vgps_mv = int(node_ul_payload[6:10], 16) if (int(node_ul_payload[6:10], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
                vant_mv = int(node_ul_payload[10:14], 16) if (int(node_ul_payload[10:14], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
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
                    "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
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
                LOG_print_timestamp("[DINFOX GPSM] * Monitoring payload * system=" + system_name + " node=" + node_name + " vmcu=" + str(vmcu_mv) + "mV tmcu=" + str(tmcu_degrees) + "dC vgps=" + str(vgps_mv) + "mV vant=" + str(vant_mv) + "mV")
            else:
                LOG_print_timestamp("[DINFOX GPSM] * system=" + system_name + " node=" + node_name + " * Invalid payload")
        # Unknwon board ID.
        else:
            LOG_print_timestamp("[DINFOX] * system=" + system_name + " node=" + node_name + " * Unknwon board ID")
    # Fill data base.
    if (len(json_body) > 0) :
        __DINFOX_add_tags(json_body, sigfox_ep_id, node_address, board_id)
        INFLUX_DB_write_data(INFLUX_DB_DATABASE_DINFOX, json_body)
    else :
        LOG_print_timestamp("[DINFOX] * Invalid frame")