from __future__ import print_function
from influxdb import InfluxDBClient

from log import *

### MACROS ###

# Influx DB parameters.
INFLUX_DB_DATABASE_HTTP_PORT = 8086

INFLUX_DB_MFX_DATABASE_NAME = 'mfxdb'
INFLUX_DB_ATXFX_DATABASE_NAME = 'atxfxdb'
INFLUX_DB_SLFX_DATABASE_NAME = 'slfxdb'
INFLUX_DB_SYNCFX_DATABASE_NAME = 'syncfxdb'
INFLUX_DB_TKFX_DATABASE_NAME = 'tkfxdb'
INFLUX_DB_SENSIT_DATABASE_NAME = 'sensitdb'

# Influx DB measurements name.
INFLUX_DB_MEASUREMENT_GLOBAL = "global"
INFLUX_DB_MEASUREMENT_MONITORING = "monitoring"
INFLUX_DB_MEASUREMENT_WEATHER = "weather"
INFLUX_DB_MEASUREMENT_GEOLOC = "geoloc"
INFLUX_DB_MEASUREMENT_SYNCHRO = "synchro"

# Influx DB fields name.
# Software version.
INFLUX_DB_FIELD_VERSION_MAJOR = "version_major"
INFLUX_DB_FIELD_VERSION_MINOR = "version_minor"
INFLUX_DB_FIELD_VERSION_COMMIT_INDEX = "version_commit_index"
INFLUX_DB_FIELD_VERSION_COMMIT_ID = "version_commit_id"
INFLUX_DB_FIELD_VERSION_DIRTY_FLAG = "version_dirty_flag"
# Timestamps.
INFLUX_DB_FIELD_LAST_STARTUP_TIMESTAMP = "last_startup_timestamp"
INFLUX_DB_FIELD_LAST_SHUTDOWN_TIMESTAMP = "last_shutdown_timestamp"
INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP = "last_communication_timestamp"
INFLUX_DB_FIELD_LAST_WEATHER_DATA_TIMESTAMP = "last_weather_data_timestamp"
INFLUX_DB_FIELD_LAST_MONITORING_DATA_TIMESTAMP = "last_monitoring_data_timestamp"
INFLUX_DB_FIELD_LAST_GEOLOC_DATA_TIMESTAMP = "last_geoloc_data_timestamp"
INFLUX_DB_FIELD_LAST_SYNCHRO_DATA_TIMESTAMP = "last_synchro_data_timestamp"
# Time.
INFLUX_DB_FIELD_HOURS = "hours"
INFLUX_DB_FIELD_MINUTES = "minutes"
INFLUX_DB_FIELD_SECONDS = "seconds"
# Frequency.
INFLUX_DB_FIELD_FREQUENCY = "frequency"
# Status.
INFLUX_DB_FIELD_RESET_BYTE = "reset_byte"
INFLUX_DB_FIELD_STATE = "state"
INFLUX_DB_FIELD_STATUS_BYTE = "status_byte"
INFLUX_DB_FIELD_MODE = "mode"
INFLUX_DB_FIELD_ERROR = "error"
# Temperature.
INFLUX_DB_FIELD_TEMPERATURE = "temperature"
INFLUX_DB_FIELD_MCU_TEMPERATURE = "mcu_temperature"
INFLUX_DB_FIELD_PCB_TEMPERATURE = "pcb_temperature"
# Humidity.
INFLUX_DB_FIELD_HUMIDITY = "humidity"
INFLUX_DB_FIELD_PCB_HUMIDITY = "pcb_humidity"
# Light.
INFLUX_DB_FIELD_LIGHT = "light"
INFLUX_DB_FIELD_UV_INDEX = "uv_index"
# Pressure.
INFLUX_DB_FIELD_ABSOLUTE_PRESSURE = "absolute_pressure"
INFLUX_DB_FIELD_SEA_LEVEL_PRESSURE = "sea_level_pressure"
# Wind.
INFLUX_DB_FIELD_AVERAGE_WIND_SPEED = "average_wind_speed"
INFLUX_DB_FIELD_PEAK_WIND_SPEED = "peak_wind_speed"
INFLUX_DB_FIELD_AVERAGE_WIND_DIRECTION = "average_wind_direction"
# Rain.
INFLUX_DB_FIELD_RAIN = "rain"
# Voltage.
INFLUX_DB_FIELD_SOURCE_VOLTAGE = "source_voltage"
INFLUX_DB_FIELD_SOLAR_CELL_VOLTAGE = "solar_cell_voltage"
INFLUX_DB_FIELD_SUPERCAP_VOLTAGE = "supercap_voltage"
INFLUX_DB_FIELD_BATTERY_VOLTAGE = "battery_voltage"
INFLUX_DB_FIELD_MCU_VOLTAGE = "mcu_voltage"
INFLUX_DB_FIELD_OUTPUT_VOLTAGE = "output_voltage"
# Current.
INFLUX_DB_FIELD_OUTPUT_CURRENT = "output_current"
INFLUX_DB_FIELD_CURRENT_SENSE_RANGE = "current_sense_range"
# Power.
INFLUX_DB_FIELD_OUTPUT_POWER = "output_power"
# GPS.
INFLUX_DB_FIELD_LATITUDE = "latitude"
INFLUX_DB_FIELD_LONGITUDE = "longitude"
INFLUX_DB_FIELD_ALTITUDE = "altitude"
INFLUX_DB_FIELD_GPS_FIX_DURATION = "gps_fix_duration"
INFLUX_DB_FIELD_GPS_TIMEOUT_DURATION = "gps_timeout_duration"
INFLUX_DB_FIELD_GPSDO_LOCK_DURATION = "gpsdo_lock_duration"

# Influx DB tags.
INFLUX_DB_TAG_SIGFOX_DEVICE_ID = "sigfox_device_id"
INFLUX_DB_TAG_METEOFOX_SITE = "meteofox_site"
INFLUX_DB_TAG_ATXFOX_RACK = "atxfox_rack"
INFLUX_DB_TAG_ATXFOX_FRONT_END = "atxfox_front_end"
INFLUX_DB_TAG_SOLARFOX_SITE = "solarfox_site"
INFLUX_DB_TAG_SYNCHROFOX_SITE = "synchrofox_site"
INFLUX_DB_TAG_TRACKFOX_ASSET = "trackfox_asset"
INFLUX_DB_TAG_SENSIT_SITE = "sensit_site"

### GLOBAL VARIABLES ###

influxdb_client = None

### FUNCTIONS ###

def INFLUX_DB_Init():
    # Variables.
    global influxdb_client
    # Wait for InfluxDB to be availabmle and create client.
    influxdb_found = False
    while influxdb_found == False:
        try:
            influxdb_client = InfluxDBClient(host='localhost', port=INFLUX_DB_DATABASE_HTTP_PORT)
            influxdb_found = True
            if LOG == True:
                print(LOG_GetCurrentTimestamp() + "INFLUX_DB Connection OK.\n")
        except:
            influxdb_found = False
    # Get list of existing databases.
    influxdb_database_list = influxdb_client.get_list_database()
    influxdb_mfxdb_found = False
    influxdb_atxfxdb_found = False
    influxdb_slfxdb_found = False
    influxdb_syncfxdb_found = False
    influxdb_tkfxdb_found = False
    influxdb_sensitdb_found = False
    for influxdb_database in influxdb_database_list:
        if (influxdb_database['name'].find(INFLUX_DB_MFX_DATABASE_NAME) >= 0):
            if LOG == True:
                print(LOG_GetCurrentTimestamp() + "INFLUX_DB MeteoFox database found.")
            influxdb_mfxdb_found = True
        if (influxdb_database['name'].find(INFLUX_DB_ATXFX_DATABASE_NAME) >= 0):
            if LOG == True:
                print(LOG_GetCurrentTimestamp() + "INFLUX_DB ATXFox database found.")
            influxdb_atxfxdb_found = True
        if (influxdb_database['name'].find(INFLUX_DB_SLFX_DATABASE_NAME) >= 0):
            if LOG == True:
                print(LOG_GetCurrentTimestamp() + "INFLUX_DB SolarFox database found.")
            influxdb_slfxdb_found = True
        if (influxdb_database['name'].find(INFLUX_DB_SYNCFX_DATABASE_NAME) >= 0):
            if LOG == True:
                print(LOG_GetCurrentTimestamp() + "INFLUX_DB SynchroFox database found.")
            influxdb_syncfxdb_found = True
        if (influxdb_database['name'].find(INFLUX_DB_TKFX_DATABASE_NAME) >= 0):
            if LOG == True:
                print(LOG_GetCurrentTimestamp() + "INFLUX_DB TrackFox database found.")
            influxdb_tkfxdb_found = True
        if (influxdb_database['name'].find(INFLUX_DB_SENSIT_DATABASE_NAME) >= 0):
            if LOG == True:
                print(LOG_GetCurrentTimestamp() + "INFLUX_DB Sensit database found.")
            influxdb_sensitdb_found = True
    # Create MeteoFox database if it does not exist.   
    if (influxdb_mfxdb_found == False):
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "INFLUX_DB Creating database " + INFLUX_DB_MFX_DATABASE_NAME + ".")
        influxdb_client.create_database(INFLUX_DB_MFX_DATABASE_NAME)
    # Create ATXFox database if it does not exist.   
    if (influxdb_atxfxdb_found == False):
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "INFLUX_DB Creating database " + INFLUX_DB_ATXFX_DATABASE_NAME + ".")
        influxdb_client.create_database(INFLUX_DB_ATXFX_DATABASE_NAME)
    # Create SolarFox database if it does not exist.   
    if (influxdb_slfxdb_found == False):
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "INFLUX_DB Creating database " + INFLUX_DB_SLFX_DATABASE_NAME + ".")
        influxdb_client.create_database(INFLUX_DB_SLFX_DATABASE_NAME)
    # Create SynchroFox database if it does not exist.  
    if (influxdb_syncfxdb_found == False):
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "INFLUX_DB Creating database " + INFLUX_DB_SYNCFX_DATABASE_NAME + ".")
        influxdb_client.create_database(INFLUX_DB_SYNCFX_DATABASE_NAME)
    # Create TrackFox database if it does not exist.  
    if (influxdb_tkfxdb_found == False):
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "INFLUX_DB Creating database " + INFLUX_DB_TKFX_DATABASE_NAME + ".")
        influxdb_client.create_database(INFLUX_DB_TKFX_DATABASE_NAME)
    # Create Sensit database if it does not exist.
    if (influxdb_sensitdb_found == False):
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "INFLUX_DB Creating database " + INFLUX_DB_SENSIT_DATABASE_NAME + ".")
        influxdb_client.create_database(INFLUX_DB_SENSIT_DATABASE_NAME)
    if LOG == True:
        print("")

# Write data in database.
def INFLUX_DB_WriteData(database_name, json_body):
    # Variables.
    global influxdb_client
    # Switch database.
    if LOG == True:
        print(LOG_GetCurrentTimestamp() + "INFLUX_DB Switching and writing database " + database_name + ".")
    influxdb_client.switch_database(database_name)
    # Write data.
    influxdb_client.write_points(json_body, time_precision='s')
    
# Read data in database.
def INFLUX_DB_ReadData(database_name, query):
    # Variables.
    global influxdb_client
    # Switch database.
    if LOG == True:
        print(LOG_GetCurrentTimestamp() + "INFLUX_DB Switching and reading database " + database_name + ".")
    influxdb_client.switch_database(database_name)
    # Read data.
    return influxdb_client.query(query)

