from __future__ import print_function
from influxdb import InfluxDBClient

from log import *
from getpass import fallback_getpass

### PUBLIC MACROS ###

# Influx DB databases name.
INFLUX_DB_DATABASE_SFXS = 'sfxs_db'
INFLUX_DB_DATABASE_METEOFOX = 'meteofox_db'
INFLUX_DB_DATABASE_SENSIT = 'sensit_db'
INFLUX_DB_DATABASE_ATXFOX = 'atxfox_db'
INFLUX_DB_DATABASE_TRACKFOX = 'trackfox_db'
INFLUX_DB_DATABASE_DINFOX = "dinfox_db"

# Influx DB measurements name.
INFLUX_DB_MEASUREMENT_METADATA = "metadata"
INFLUX_DB_MEASUREMENT_MONITORING = "monitoring"
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
INFLUX_DB_FIELD_TIME_LAST_STARTUP = "time_last_startup"
INFLUX_DB_FIELD_TIME_LAST_SHUTDOWN = "time_last_shutdown"
INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION = "time_last_communication"
INFLUX_DB_FIELD_TIME_LAST_WEATHER_DATA = "time_last_weather_data"
INFLUX_DB_FIELD_TIME_LAST_MONITORING_DATA = "time_last_monitoring_data"
INFLUX_DB_FIELD_TIME_LAST_GEOLOC_DATA = "time_last_geoloc_data"
INFLUX_DB_FIELD_TIME_LAST_ELECTRICAL_DATA = "time_last_electrical_data"
INFLUX_DB_FIELD_TIME_LAST_SENSOR_DATA = "time_last_sensor_data"
# Status.
INFLUX_DB_FIELD_RESET_FLAGS = "reset_flags"
INFLUX_DB_FIELD_STATE = "state"
INFLUX_DB_FIELD_STATUS = "status"
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
INFLUX_DB_FIELD_CHARGE_ENABLE = "charge_enable"
INFLUX_DB_FIELD_BACKUP_ENABLE = "backup_enable"
INFLUX_DB_FIELD_NODES_COUNT = "nodes_count"
INFLUX_DB_FIELD_ERROR = "error"
# Temperature.
INFLUX_DB_FIELD_TAMB = "tamb"
INFLUX_DB_FIELD_TMCU = "tmcu"
INFLUX_DB_FIELD_TPCB = "tpcb"
# Humidity.
INFLUX_DB_FIELD_HAMB = "hamb"
INFLUX_DB_FIELD_HPCB = "hpcb"
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
# Current.
INFLUX_DB_FIELD_IOUT = "iout"
INFLUX_DB_FIELD_I_RANGE = "i_range"
# Power.
INFLUX_DB_FIELD_POUT = "pout"
# GPS.
INFLUX_DB_FIELD_LATITUDE = "latitude"
INFLUX_DB_FIELD_LONGITUDE = "longitude"
INFLUX_DB_FIELD_ALTITUDE = "altitude"
INFLUX_DB_FIELD_GPS_FIX_DURATION = "gps_fix_duration"
INFLUX_DB_FIELD_GPS_TIMEOUT_DURATION = "gps_timeout_duration"

# Influx DB tags.
INFLUX_DB_TAG_SIGFOX_EP_ID = "sigfox_ep_id"
INFLUX_DB_TAG_NODE_ADDRESS = "node_address"
INFLUX_DB_TAG_SITE = "site"
INFLUX_DB_TAG_RACK = "rack"
INFLUX_DB_TAG_PSFE = "psfe"
INFLUX_DB_TAG_ASSET = "asset"
INFLUX_DB_TAG_SYSTEM = "system"
INFLUX_DB_TAG_NODE = "node"
INFLUX_DB_TAG_BOARD_ID = "board_id"

## LOCAL MACROS ###

# Influx DB parameters.
__INFLUX_DB_DATABASE_HTTP_PORT = 8086
# Databases list.
__INFLUX_DB_DATABASE_LIST = [
    INFLUX_DB_DATABASE_SFXS,
    INFLUX_DB_DATABASE_METEOFOX,
    INFLUX_DB_DATABASE_SENSIT,
    INFLUX_DB_DATABASE_ATXFOX,
    INFLUX_DB_DATABASE_TRACKFOX,
    INFLUX_DB_DATABASE_DINFOX
]

### GLOBAL VARIABLES ###

influxdb_client = None

### FUNCTIONS ###

def INFLUX_DB_init():
    # Variables.
    global influxdb_client
    # Wait for InfluxDB to be available.
    influxdb_found = False
    while influxdb_found == False:
        try:
            # Create client.
            influxdb_client = InfluxDBClient(host='localhost', port=__INFLUX_DB_DATABASE_HTTP_PORT)
            influxdb_found = True
            LOG_print_timestamp("[INFLUX_DB] * Connection OK.\n")
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
                LOG_print_timestamp("[INFLUX_DB] * "+ db_name + " database found.")
                influxdb_db_found = True
                break
        # Create database if it does not exist.
        if (influxdb_db_found == False) :
            LOG_print_timestamp("[INFLUX_DB] * Creating database " + db_name)
            influxdb_client.create_database(db_name)
    LOG_print("")

# Write data in database.
def INFLUX_DB_write_data(database_name, json_body):
    # Variables.
    global influxdb_client
    # Switch database.
    LOG_print_timestamp("[INFLUX_DB] * Switching and writing database " + database_name + ".")
    influxdb_client.switch_database(database_name)
    # Write data.
    influxdb_client.write_points(json_body, time_precision='s')
    
# Read data in database.
def INFLUX_DB_read_data(database_name, query):
    # Variables.
    global influxdb_client
    # Switch database.
    LOG_print_timestamp("[INFLUX_DB] * Switching and reading database " + database_name + ".")
    influxdb_client.switch_database(database_name)
    # Read data.
    return influxdb_client.query(query)

