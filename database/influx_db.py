from __future__ import print_function
from influxdb import InfluxDBClient

from log import *

### PUBLIC MACROS ###

# Influx DB databases name.
INFLUX_DB_DATABASE_SIGFOX_EP_SERVER = 'sigfox_ep_server_db'
INFLUX_DB_DATABASE_METEOFOX = 'meteofox_db'
INFLUX_DB_DATABASE_SENSIT = 'sensit_db'
INFLUX_DB_DATABASE_ATXFOX = 'atxfox_db'
INFLUX_DB_DATABASE_TRACKFOX = 'trackfox_db'
INFLUX_DB_DATABASE_DINFOX = "dinfox_db"
INFLUX_DB_DATABASE_HOMEFOX = "homefox_db"

# Influx DB measurements name.
INFLUX_DB_MEASUREMENT_METADATA = "metadata"
INFLUX_DB_MEASUREMENT_DOWNLINK = "downlink"
INFLUX_DB_MEASUREMENT_MONITORING = "monitoring"
INFLUX_DB_MEASUREMENT_AIR_QUALITY = "air_quality"
INFLUX_DB_MEASUREMENT_MOTION = "motion"
INFLUX_DB_MEASUREMENT_WEATHER = "weather"
INFLUX_DB_MEASUREMENT_GEOLOC = "geoloc"
INFLUX_DB_MEASUREMENT_ELECTRICAL = "electrical"
INFLUX_DB_MEASUREMENT_SENSOR = "sensor"

# Influx DB fields name.
# Software version.
INFLUX_DB_FIELD_VERSION = "version"
INFLUX_DB_FIELD_VERSION_MAJOR = "version_major"
INFLUX_DB_FIELD_VERSION_MINOR = "version_minor"
INFLUX_DB_FIELD_VERSION_COMMIT_INDEX = "version_commit_index"
INFLUX_DB_FIELD_VERSION_COMMIT_ID = "version_commit_id"
INFLUX_DB_FIELD_VERSION_DIRTY_FLAG = "version_dirty_flag"
# Timestamps.
INFLUX_DB_FIELD_TIME_DOWNLINK_RECORD = "time_downlink_record"
INFLUX_DB_FIELD_TIME_DOWNLINK_SERVER = "time_downlink_server"
INFLUX_DB_FIELD_TIME_DOWNLINK_NETWORK = "time_downlink_network"
INFLUX_DB_FIELD_TIME_LAST_STARTUP = "time_last_startup"
INFLUX_DB_FIELD_TIME_LAST_SHUTDOWN = "time_last_shutdown"
INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION = "time_last_communication"
INFLUX_DB_FIELD_TIME_LAST_WEATHER_DATA = "time_last_weather_data"
INFLUX_DB_FIELD_TIME_LAST_MONITORING_DATA = "time_last_monitoring_data"
INFLUX_DB_FIELD_TIME_LAST_AIR_QUALITY_DATA = "time_last_air_quality_data"
INFLUX_DB_FIELD_TIME_LAST_MOTION_DATA = "time_last_motion_data"
INFLUX_DB_FIELD_TIME_LAST_GEOLOC_DATA = "time_last_geoloc_data"
INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA = "time_last_electrical_data"
INFLUX_DB_FIELD_TIME_LAST_SENSOR_DATA = "time_last_sensor_data"
INFLUX_DB_FIELD_TIME_LAST_ACTION_LOG_DATA = "time_last_action_log_data"
# Downlink.
INFLUX_DB_FIELD_DOWNLINK_HASH = "downlink_hash"
INFLUX_DB_FIELD_DL_PAYLOAD = "dl_payload"
INFLUX_DB_FIELD_DL_SUCCESS = "dl_success"
INFLUX_DB_FIELD_DL_STATUS = "dl_status"
# Status.
INFLUX_DB_FIELD_RESET_FLAGS = "reset_flags"
INFLUX_DB_FIELD_STATE = "state"
INFLUX_DB_FIELD_STATUS = "status"
INFLUX_DB_FIELD_NODE_ACCESS_STATUS = "node_access_status"
INFLUX_DB_FIELD_MODE = "mode"
INFLUX_DB_FIELD_RELAY_STATE = "relay_state"
INFLUX_DB_FIELD_RELAY_1_STATE = "relay_1_state"
INFLUX_DB_FIELD_RELAY_2_STATE = "relay_2_state"
INFLUX_DB_FIELD_RELAY_3_STATE = "relay_3_state"
INFLUX_DB_FIELD_RELAY_4_STATE = "relay_4_state"
INFLUX_DB_FIELD_RELAY_5_STATE = "relay_5_state"
INFLUX_DB_FIELD_RELAY_6_STATE = "relay_6_state"
INFLUX_DB_FIELD_RELAY_7_STATE = "relay_7_state"
INFLUX_DB_FIELD_RELAY_8_STATE = "relay_8_state"
INFLUX_DB_FIELD_DC_DC_STATE = "dc_dc_state"
INFLUX_DB_FIELD_CHARGE_STATUS = "charge_status"
INFLUX_DB_FIELD_CHARGE_STATUS_1 = "charge_status_1"
INFLUX_DB_FIELD_CHARGE_STATUS_0 = "charge_status_0"
INFLUX_DB_FIELD_CHARGE_ENABLE = "charge_enable"
INFLUX_DB_FIELD_BACKUP_ENABLE = "backup_enable"
INFLUX_DB_FIELD_NODES_COUNT = "nodes_count"
INFLUX_DB_FIELD_LINKY_TIC_DETECT = "linky_tic_detect"
INFLUX_DB_FIELD_MAINS_VOLTAGE_DETECT = "mains_voltage_detect"
INFLUX_DB_FIELD_CH1_DETECT = "ch1_detect"
INFLUX_DB_FIELD_CH2_DETECT = "ch2_detect"
INFLUX_DB_FIELD_CH3_DETECT = "ch3_detect"
INFLUX_DB_FIELD_CH4_DETECT = "ch4_detect"
INFLUX_DB_FIELD_ERROR = "error"
# Temperature.
INFLUX_DB_FIELD_TAMB = "tamb"
INFLUX_DB_FIELD_TMCU = "tmcu"
INFLUX_DB_FIELD_TPCB = "tpcb"
# Humidity.
INFLUX_DB_FIELD_HAMB = "hamb"
INFLUX_DB_FIELD_HPCB = "hpcb"
# Air quality.
INFLUX_DB_FIELD_AIR_QUALITY_ACQUISITION_STATUS = "air_quality_acquisition_status"
INFLUX_DB_FIELD_AIR_QUALITY_ACQUISITION_DURATION = "air_quality_acquisition_duration"
INFLUX_DB_FIELD_TVOC = "tvoc"
INFLUX_DB_FIELD_ECO2 = "eco2"
INFLUX_DB_FIELD_AQI_UBA = "aqi_uba"
INFLUX_DB_FIELD_AQI_S = "aqi_s"
# Motion.
INFLUX_DB_FIELD_ACCELEROMETER_EVENT_SOURCE = "accelerometer_event_source"
# Light.
INFLUX_DB_FIELD_LIGHT = "light"
INFLUX_DB_FIELD_UV_INDEX = "uv_index"
# Pressure.
INFLUX_DB_FIELD_PATM_ABS = "patm_abs"
INFLUX_DB_FIELD_PATM_SEA = "patm_sea"
# Wind.
INFLUX_DB_FIELD_WSPD_AVRG = "wspd_avrg"
INFLUX_DB_FIELD_WSPD_PEAK = "wspd_peak"
INFLUX_DB_FIELD_WDIR_AVRG = "wdir_avrg"
# Rain.
INFLUX_DB_FIELD_RAIN = "rain"
# Voltage.
INFLUX_DB_FIELD_VSRC = "vsrc"
INFLUX_DB_FIELD_VCAP = "vcap"
INFLUX_DB_FIELD_VBAT = "vbat"
INFLUX_DB_FIELD_VMCU = "vmcu"
INFLUX_DB_FIELD_VIN = "vin"
INFLUX_DB_FIELD_VOUT = "vout"
INFLUX_DB_FIELD_VCOM = "vcom"
INFLUX_DB_FIELD_VSTR = "vstr"
INFLUX_DB_FIELD_ISTR = "istr"
INFLUX_DB_FIELD_VBKP = "vbkp"
INFLUX_DB_FIELD_VRF_TX = "vrf_tx"
INFLUX_DB_FIELD_VRF_RX = "vrf_rx"
INFLUX_DB_FIELD_VGPS = "vgps"
INFLUX_DB_FIELD_VANT = "vant"
INFLUX_DB_FIELD_VUSB = "vusb"
INFLUX_DB_FIELD_VRS = "vrs"
INFLUX_DB_FIELD_VHMI = "vhmi"
INFLUX_DB_FIELD_AIN0 = "ain0"
INFLUX_DB_FIELD_AIN1 = "ain1"
INFLUX_DB_FIELD_AIN2 = "ain2"
INFLUX_DB_FIELD_AIN3 = "ain3"
INFLUX_DB_FIELD_DIO0 = "dio0"
INFLUX_DB_FIELD_DIO1 = "dio1"
INFLUX_DB_FIELD_DIO2 = "dio2"
INFLUX_DB_FIELD_DIO3 = "dio3"
INFLUX_DB_FIELD_VRMS_MIN = "vrms_min"
INFLUX_DB_FIELD_VRMS_MEAN = "vrms_mean"
INFLUX_DB_FIELD_VRMS_MAX = "vrms_max"
# Current.
INFLUX_DB_FIELD_IOUT = "iout"
INFLUX_DB_FIELD_I_RANGE = "i_range"
INFLUX_DB_FIELD_IRMS_MIN = "irms_min"
INFLUX_DB_FIELD_IRMS_MEAN = "irms_mean"
INFLUX_DB_FIELD_IRMS_MAX = "irms_max"
# Power.
INFLUX_DB_FIELD_POUT = "pout"
INFLUX_DB_FIELD_PACT_MIN = "pact_min"
INFLUX_DB_FIELD_PACT_MEAN = "pact_mean"
INFLUX_DB_FIELD_PACT_MAX = "pact_max"
INFLUX_DB_FIELD_PAPP_MIN = "papp_min"
INFLUX_DB_FIELD_PAPP_MEAN = "papp_mean"
INFLUX_DB_FIELD_PAPP_MAX = "papp_max"
# Energy
INFLUX_DB_FIELD_EACT = "eact"
INFLUX_DB_FIELD_EAPP = "eapp"
# Power factor.
INFLUX_DB_FIELD_PF_MIN = "pf_min"
INFLUX_DB_FIELD_PF_MEAN = "pf_mean"
INFLUX_DB_FIELD_PF_MAX = "pf_max"
# Frequency.
INFLUX_DB_FIELD_FREQUENCY_MIN = "f_min"
INFLUX_DB_FIELD_FREQUENCY_MEAN = "f_mean"
INFLUX_DB_FIELD_FREQUENCY_MAX = "f_max"
# GPS.
INFLUX_DB_FIELD_LATITUDE = "latitude"
INFLUX_DB_FIELD_LONGITUDE = "longitude"
INFLUX_DB_FIELD_ALTITUDE = "altitude"
INFLUX_DB_FIELD_GPS_ACQUISITION_STATUS = "gps_acquisition_status"
INFLUX_DB_FIELD_GPS_ACQUISITION_DURATION = "gps_acquisition_duration"
INFLUX_DB_FIELD_GPS_TIMEOUT_DURATION = "gps_timeout_duration"
# Registers.
INFLUX_DB_FIELD_REGISTER_ADDRESS = "register_address"
INFLUX_DB_FIELD_REGISTER_VALUE = "register_value"

# Influx DB tags.
INFLUX_DB_TAG_SIGFOX_EP_ID = "sigfox_ep_id"
INFLUX_DB_TAG_NODE_ADDRESS = "node_address"
INFLUX_DB_TAG_SITE = "site"
INFLUX_DB_TAG_LOCATION = "location"
INFLUX_DB_TAG_RACK = "rack"
INFLUX_DB_TAG_PSFE = "psfe"
INFLUX_DB_TAG_ASSET = "asset"
INFLUX_DB_TAG_SYSTEM = "system"
INFLUX_DB_TAG_NODE = "node"
INFLUX_DB_TAG_BOARD_ID = "board_id"
INFLUX_DB_TAG_CHANNEL = "channel"

## LOCAL MACROS ###

# Influx DB parameters.
__INFLUX_DB_DATABASE_HTTP_PORT = 8086

# Databases list.
__INFLUX_DB_DATABASE_LIST = [
    INFLUX_DB_DATABASE_SIGFOX_EP_SERVER,
    INFLUX_DB_DATABASE_METEOFOX,
    INFLUX_DB_DATABASE_SENSIT,
    INFLUX_DB_DATABASE_ATXFOX,
    INFLUX_DB_DATABASE_TRACKFOX,
    INFLUX_DB_DATABASE_DINFOX,
    INFLUX_DB_DATABASE_HOMEFOX
]

### GLOBAL VARIABLES ###

influxdb_client = None

### FUNCTIONS ###

def INFLUX_DB_init() :
    # Variables.
    global influxdb_client
    influxdb_version = 0
    influxdb_found = False
    # Wait for InfluxDB to be available.
    LOG_print("[INFLUX_DB] * Creating client...")
    while influxdb_found == False:
        try:
            # Create client.
            influxdb_client = InfluxDBClient(host='localhost', port=__INFLUX_DB_DATABASE_HTTP_PORT)
            # Ping database.
            influxdb_version = influxdb_client.ping()
            influxdb_found = True
            LOG_print("[INFLUX_DB] * Connection OK (" + str(influxdb_version) + ")")
            LOG_print("")
        except:
            influxdb_found = False
    # Get list of existing databases.
    influxdb_database_list = influxdb_client.get_list_database()
    # Check databases.
    for idx in range(len(__INFLUX_DB_DATABASE_LIST)) :
        db_name = __INFLUX_DB_DATABASE_LIST[idx]
        influxdb_db_found = False
        for influxdb_database in influxdb_database_list :
            if (influxdb_database['name'].find(db_name) >= 0) :
                LOG_print("[INFLUX_DB] * "+ db_name + " database found")
                influxdb_db_found = True
                break
        # Create database if it does not exist.
        if (influxdb_db_found == False) :
            LOG_print("[INFLUX_DB] * Creating database " + db_name)
            influxdb_client.create_database(db_name)

# Write data in database.
def INFLUX_DB_write_data(database_name, json_body) :
    # Variables.
    global influxdb_client
    # Switch database.
    LOG_print("[INFLUX_DB] * Switching and writing database " + database_name)
    influxdb_client.switch_database(database_name)
    # Write data.
    influxdb_client.write_points(json_body, time_precision='s')
    
# Read data in database.
def INFLUX_DB_read_data(database_name, query) :
    # Variables.
    global influxdb_client
    # Switch database.
    LOG_print("[INFLUX_DB] * Switching and reading database " + database_name)
    influxdb_client.switch_database(database_name)
    # Read data.
    return influxdb_client.query(query)

