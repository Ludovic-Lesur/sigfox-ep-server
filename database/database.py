"""
* database.py
*
*  Created on: 17 nov. 2021
*      Author: Ludo
"""

import json

from influxdb import InfluxDBClient
from log import *
from typing import List, Dict, Any

### DATABASE public macros ###

# Databases name.
DATABASE_SIGFOX_EP_SERVER = "sigfox_ep_server_db"
DATABASE_METEOFOX = "meteofox_db"
DATABASE_SENSIT = "sensit_db"
DATABASE_ATXFOX = "atxfox_db"
DATABASE_TRACKFOX = "trackfox_db"
DATABASE_DINFOX = "dinfox_db"
DATABASE_HOMEFOX = "homefox_db"

# Measurements name.
DATABASE_MEASUREMENT_METADATA = "metadata"
DATABASE_MEASUREMENT_SIGFOX_DOWNLINK = "sigfox_downlink"
DATABASE_MEASUREMENT_MONITORING = "monitoring"
DATABASE_MEASUREMENT_WEATHER = "weather"
DATABASE_MEASUREMENT_GEOLOCATION = "geolocation"
DATABASE_MEASUREMENT_ELECTRICAL = "electrical"
DATABASE_MEASUREMENT_SENSOR = "sensor"
DATABASE_MEASUREMENT_HOME = "home"

# Fields name.
# Generic.
DATABASE_FIELD_STATUS = "status"
DATABASE_FIELD_MODE = "mode"
DATABASE_FIELD_RESET_FLAGS = "reset_flags"
DATABASE_FIELD_ERROR = "error"
DATABASE_FIELD_LAST_STARTUP_TIME = "last_startup_time"
DATABASE_FIELD_LAST_SHUTDOWN_TIME = "last_shutdown_time"
DATABASE_FIELD_LAST_DATA_TIME = "last_data_time"
# Software.
DATABASE_FIELD_SW_VERSION = "sw_version"
DATABASE_FIELD_SW_VERSION_MAJOR = "sw_version_major"
DATABASE_FIELD_SW_VERSION_MINOR = "sw_version_minor"
DATABASE_FIELD_SW_VERSION_COMMIT_INDEX = "sw_version_commit_index"
DATABASE_FIELD_SW_VERSION_COMMIT_ID = "sw_version_commit_id"
DATABASE_FIELD_SW_VERSION_DIRTY_FLAG = "sw_version_dirty_flag"
# Nodes.
DATABASE_FIELD_NODE_COUNT = "node_count"
DATABASE_FIELD_NODE_ACCESS_STATUS = "node_access_status"
DATABASE_FIELD_NODE_REGISTER_ADDRESS = "node_register_address"
DATABASE_FIELD_NODE_REGISTER_VALUE = "node_register_value"
# Sigfox downlink.
DATABASE_FIELD_SIGFOX_DOWNLINK_RECORD_TIME = "sigfox_downlink_record_time"
DATABASE_FIELD_SIGFOX_DOWNLINK_SERVER_TIME = "sigfox_downlink_server_time"
DATABASE_FIELD_SIGFOX_DOWNLINK_NETWORK_TIME = "sigfox_downlink_network_time"
DATABASE_FIELD_SIGFOX_DOWNLINK_HASH = "sigfox_downlink_hash"
DATABASE_FIELD_SIGFOX_DOWNLINK_PAYLOAD = "sigfox_downlink_payload"
DATABASE_FIELD_SIGFOX_DOWNLINK_SUCCESS = "sigfox_downlink_success"
DATABASE_FIELD_SIGFOX_DOWNLINK_STATUS = "sigfox_downlink_status"
# Input.
DATABASE_FIELD_INPUT_VOLTAGE = "input_voltage"
# Source.
DATABASE_FIELD_SOURCE_VOLTAGE = "source_voltage"
# Output.
DATABASE_FIELD_OUTPUT_VOLTAGE = "output_voltage"
DATABASE_FIELD_OUTPUT_CURRENT = "output_current"
DATABASE_FIELD_OUTPUT_CURRENT_RANGE = "output_current_range"
# Storage.
DATABASE_FIELD_STORAGE_VOLTAGE = "storage_voltage"
# Backup.
DATABASE_FIELD_BACKUP_VOLTAGE = "backup_voltage"
DATABASE_FIELD_BACKUP_CONTROL_STATE = "backup_control_state"
# Charge.
DATABASE_FIELD_CHARGE_STATUS = "charge_status"
DATABASE_FIELD_CHARGE_CONTROL_STATE = "charge_control_state"
DATABASE_FIELD_CHARGE_CURRENT = "charge_current"
# MCU
DATABASE_FIELD_MCU_VOLTAGE = "mcu_voltage"
DATABASE_FIELD_MCU_TEMPERATURE = "mcu_temperature"
# Radio.
DATABASE_FIELD_RADIO_TX_VOLTAGE = "radio_tx_voltage"
DATABASE_FIELD_RADIO_RX_VOLTAGE = "radio_rx_voltage"
# USB.
DATABASE_FIELD_USB_VOLTAGE = "usb_voltage"
# RS485 bus.
DATABASE_FIELD_RS485_BUS_VOLTAGE = "rs485_bus_voltage"
# HMI
DATABASE_FIELD_HMI_VOLTAGE = "hmi_voltage"
# Analog.
DATABASE_FIELD_AIN0_VOLTAGE = "ain0_voltage"
DATABASE_FIELD_AIN1_VOLTAGE = "ain1_voltage"
DATABASE_FIELD_AIN2_VOLTAGE = "ain2_voltage"
DATABASE_FIELD_AIN3_VOLTAGE = "ain3_voltage"
# Digital.
DATABASE_FIELD_DIO0_STATE = "dio0_state"
DATABASE_FIELD_DIO1_STATE = "dio1_state"
DATABASE_FIELD_DIO2_STATE = "dio2_state"
DATABASE_FIELD_DIO3_STATE = "dio3_state"
# Relay.
DATABASE_FIELD_RELAY_STATE = "relay_state"
DATABASE_FIELD_RELAY1_STATE = "relay1_state"
DATABASE_FIELD_RELAY2_STATE = "relay2_state"
DATABASE_FIELD_RELAY3_STATE = "relay3_state"
DATABASE_FIELD_RELAY4_STATE = "relay4_state"
DATABASE_FIELD_RELAY5_STATE = "relay5_state"
DATABASE_FIELD_RELAY6_STATE = "relay6_state"
DATABASE_FIELD_RELAY7_STATE = "relay7_state"
DATABASE_FIELD_RELAY8_STATE = "relay8_state"
# Regulator.
DATABASE_FIELD_REGULATOR_STATE = "regulator_state"
# Mains.
DATABASE_FIELD_MAINS_VOLTAGE_DETECT = "mains_voltage_detect"
DATABASE_FIELD_MAINS_VOLTAGE_RMS_MIN = "mains_voltage_rms_min"
DATABASE_FIELD_MAINS_VOLTAGE_RMS_MEAN = "mains_voltage_rms_mean"
DATABASE_FIELD_MAINS_VOLTAGE_RMS_MAX = "mains_voltage_rms_max"
DATABASE_FIELD_MAINS_CURRENT_DETECT_CH1 = "mains_current_detect_ch1"
DATABASE_FIELD_MAINS_CURRENT_DETECT_CH2 = "mains_current_detect_ch2"
DATABASE_FIELD_MAINS_CURRENT_DETECT_CH3 = "mains_current_detect_ch3"
DATABASE_FIELD_MAINS_CURRENT_DETECT_CH4 = "mains_current_detect_ch4"
DATABASE_FIELD_MAINS_CURRENT_RMS_MIN = "mains_current_rms_min"
DATABASE_FIELD_MAINS_CURRENT_RMS_MEAN = "mains_current_rms_mean"
DATABASE_FIELD_MAINS_CURRENT_RMS_MAX = "mains_current_rms_max"
DATABASE_FIELD_MAINS_LINKY_TIC_DETECT = "mains_linky_tic_detect"
DATABASE_FIELD_MAINS_ACTIVE_POWER_MIN = "mains_active_power_min"
DATABASE_FIELD_MAINS_ACTIVE_POWER_MEAN = "mains_active_power_mean"
DATABASE_FIELD_MAINS_ACTIVE_POWER_MAX = "mains_active_power_max"
DATABASE_FIELD_MAINS_APPARENT_POWER_MIN = "mains_apparent_power_min"
DATABASE_FIELD_MAINS_APPARENT_POWER_MEAN = "mains_apparent_power_mean"
DATABASE_FIELD_MAINS_APPARENT_POWER_MAX = "mains_apparent_power_max"
DATABASE_FIELD_MAINS_ACTIVE_ENERGY = "mains_active_energy"
DATABASE_FIELD_MAINS_APPARENT_ENERGY = "mains_apparent_energy"
DATABASE_FIELD_MAINS_POWER_FACTOR_MIN = "mains_power_factor_min"
DATABASE_FIELD_MAINS_POWER_FACTOR_MEAN = "mains_power_factor_mean"
DATABASE_FIELD_MAINS_POWER_FACTOR_MAX = "mains_power_factor_max"
DATABASE_FIELD_MAINS_FREQUENCY_MIN = "mains_frequency_min"
DATABASE_FIELD_MAINS_FREQUENCY_MEAN = "mains_frequency_mean"
DATABASE_FIELD_MAINS_FREQUENCY_MAX = "mains_frequency_max"
# Temperature.
DATABASE_FIELD_TEMPERATURE = "temperature"
# Humidity.
DATABASE_FIELD_HUMIDITY = "humidity"
# Air quality.
DATABASE_FIELD_AIR_QUALITY_TVOC = "air_quality_tvoc"
DATABASE_FIELD_AIR_QUALITY_ECO2 = "air_quality_eco2"
DATABASE_FIELD_AIR_QUALITY_INDEX_UBA = "air_quality_index_uba"
DATABASE_FIELD_AIR_QUALITY_INDEX_S = "air_quality_index_s"
DATABASE_FIELD_AIR_QUALITY_ACQUISITION_MODE = "air_quality_acquisition_mode"
DATABASE_FIELD_AIR_QUALITY_ACQUISITION_STATUS = "air_quality_acquisition_status"
DATABASE_FIELD_AIR_QUALITY_ACQUISITION_TIME = "air_quality_acquisition_time"
# Sunshine.
DATABASE_FIELD_SUNSHINE_LIGHT = "sunshine_light"
DATABASE_FIELD_SUNSHINE_UV_INDEX = "sunshine_uv_index"
# Pressure.
DATABASE_FIELD_PRESSURE_ATMOSPHERIC_ABSOLUTE = "pressure_atmospheric_absolute"
DATABASE_FIELD_PRESSURE_ATMOSPHERIC_SEA_LEVEL = "pressure_atmospheric_sea_level"
# Wind.
DATABASE_FIELD_WIND_SPEED_AVERAGE = "wind_speed_average"
DATABASE_FIELD_WIND_SPEED_PEAK = "wind_speed_peak"
DATABASE_FIELD_WIND_DIRECTION_AVERAGE = "wind_direction_average"
# Rainfall.
DATABASE_FIELD_RAINFALL = "rainfall"
# Accelerometer.
DATABASE_FIELD_ACCELEROMETER_EVENT_SOURCE = "accelerometer_event_source"
# Geolocation.
DATABASE_FIELD_GEOLOCATION_LATITUDE = "geolocation_latitude"
DATABASE_FIELD_GEOLOCATION_LONGITUDE = "geolocation_longitude"
DATABASE_FIELD_GEOLOCATION_ALTITUDE = "geolocation_altitude"
DATABASE_FIELD_GEOLOCATION_SOURCE = "geolocation_source"
# GPS.
DATABASE_FIELD_GPS_ACQUISITION_STATUS = "gps_acquisition_status"
DATABASE_FIELD_GPS_ACQUISITION_TIME = "gps_acquisition_time"
DATABASE_FIELD_GPS_ACQUISITION_TIMEOUT_TIME = "gps_acquisition_timeout_time"
DATABASE_FIELD_GPS_VOLTAGE = "gps_voltage"
DATABASE_FIELD_GPS_ANTENNA_VOLTAGE = "gps_antenna_voltage"

# Tags name.
DATABASE_TAG_SIGFOX_EP_ID = "sigfox_ep_id"
DATABASE_TAG_NODE_ADDRESS = "node_address"
DATABASE_TAG_SITE = "site"
DATABASE_TAG_LOCATION = "location"
DATABASE_TAG_RACK = "rack"
DATABASE_TAG_PSFE = "psfe"
DATABASE_TAG_ASSET = "asset"
DATABASE_TAG_SYSTEM = "system"
DATABASE_TAG_NODE = "node"
DATABASE_TAG_BOARD_ID = "board_id"
DATABASE_TAG_CHANNEL = "channel"

### DATABASE local macros ###

DATABASE_LIST = {
    DATABASE_SIGFOX_EP_SERVER: "365d",
    DATABASE_METEOFOX: "365d",
    DATABASE_SENSIT: "365d",
    DATABASE_ATXFOX: "30d",
    DATABASE_TRACKFOX: "365d",
    DATABASE_DINFOX: "60d",
    DATABASE_HOMEFOX: "60d"
}

DATABASE_RETENTION_POLICY_10_YEARS_NAME = "rp_10y"

DATABASE_JSON_KEY_TIME = "time"
DATABASE_JSON_KEY_MEASUREMENT = "measurement"
DATABASE_JSON_KEY_FIELDS = "fields"
DATABASE_JSON_KEY_TAGS = "tags"

DATABASE_FIELD_NAME = "name"
DATABASE_FIELD_LAST = "last"

### DATABASE classes ###

class Record:
    
    def __init__(self) -> None :
        self.database = None
        self.measurement = None
        self.timestamp = None
        self.fields = None
        self.tags = None
        self.limited_retention = True
        
    def add_field(self, field_raw: Any, field_raw_error: Any, field_name: str, field_value: Any):
        # Check error value.
        if (field_raw != field_raw_error):
            self.fields[field_name] = field_value
    
    def log_print(self) -> None:
        # Local variables.
        log_string = "[RECORD] * "
        if (self.database):
            log_string += ("database=" + str(self.database) + " ")
        if (self.measurement):
            log_string += ("measurement=" + str(self.measurement) + " ")
        if (self.timestamp):
            log_string += ("timestamp=" + str(self.timestamp) + " ")
        if (self.fields):
            log_string += "fields={"
            for field_name, field_value in self.fields.items():
                log_string += (" " + str(field_name) + "=" + str(field_value))
            log_string += " } "
        if (self.tags):
            log_string += "tags={"
            for tag_name, tag_value in self.tags.items():
                log_string += (" " + str(tag_name) + "=" + str(tag_value))
            log_string += " } "
        log_string += ("(limited_retention=" + str(self.limited_retention) + ")")
        Log.debug_print(log_string)

class Database:
    
    def __init__(self, database_host: str = "localhost", database_port: int = 8086) -> None:
        # Local variables.
        influxdb_version = 0
        influxdb_found = False
        database_found = False
        retention_policy_found = False
        retention_policy_infinite_found = False
        # Init context.
        self._influxdb_client = None
        # Wait for InfluxDB to be available.
        Log.debug_print("[DATABASE] * Creating client...")
        while influxdb_found == False:
            try:
                # Create client.
                self._influxdb_client = InfluxDBClient(host=database_host, port=database_port)
                # Ping database.
                influxdb_version = self._influxdb_client.ping()
                influxdb_found = True
                Log.debug_print("[DATABASE] * Influx DB connection OK (" + str(influxdb_version) + ")")
                Log.debug_print("")
            except:
                influxdb_found = False
        # Get list of existing databases.
        influxdb_database_list = self._influxdb_client.get_list_database()
        # Check databases.
        for database, retention_policy_duration in DATABASE_LIST.items():
            # Reset flags.
            database_found = False
            retention_policy_found = False
            retention_policy_infinite_found = False
            # Check if database exists.
            for influxdb_database in influxdb_database_list :
                if (influxdb_database[DATABASE_FIELD_NAME].find(database) >= 0) :
                    Log.debug_print("[DATABASE] * " + database + " database found")
                    database_found = True
                    break
            # Create database if not found.
            if (database_found == False) :
                Log.debug_print("[DATABASE] * Creating database " + database)
                self._influxdb_client.create_database(database)
            # Check retention policy.
            retention_policy_name = ("rp_" + database)
            retention_policy_list = list(self._influxdb_client.query(f'SHOW RETENTION POLICIES ON "{database}"').get_points())
            # Check if retention policy exists.
            for rp in retention_policy_list:
                if (rp.get(DATABASE_FIELD_NAME) == retention_policy_name):
                    Log.debug_print("[DATABASE] * " + retention_policy_name + " retention policy found")
                    retention_policy_found = True
                if (rp.get(DATABASE_FIELD_NAME) == DATABASE_RETENTION_POLICY_10_YEARS_NAME):
                    Log.debug_print("[DATABASE] * " + DATABASE_RETENTION_POLICY_10_YEARS_NAME + " retention policy found")
                    retention_policy_infinite_found = True
            # Create or modify database retention policy.
            query_action = "CREATE" if (retention_policy_found == False) else "ALTER"
            Log.debug_print("[DATABASE] * " + query_action + " retention policy " + retention_policy_name)
            self._influxdb_client.query(f'{query_action} RETENTION POLICY "{retention_policy_name}" ON "{database}" DURATION {retention_policy_duration} REPLICATION 1 DEFAULT')
            # Create or modify infinite retention policy.
            query_action = "CREATE" if (retention_policy_infinite_found == False) else "ALTER"
            Log.debug_print("[DATABASE] * " + query_action + " retention policy " + DATABASE_RETENTION_POLICY_10_YEARS_NAME)
            self._influxdb_client.query(f'{query_action} RETENTION POLICY "{DATABASE_RETENTION_POLICY_10_YEARS_NAME}" ON "{database}" DURATION 520w REPLICATION 1')

    @staticmethod      
    def _convert_integers_to_floats(dictionary: Dict[str, Any]) -> Dict[str, Any]:
        # Convert integer fields to float.
        converted = {}
        # Loop on all items.
        for name, value in dictionary.items():
            if not isinstance(name, str):
                print("ERROR INSTANCE NAME")
                return
            if isinstance(value, int):
                converted[name] = float(value)
            else:
                converted[name] = value
        return converted
                
    def write_record(self, record: Record):
        # Check parameters.
        if not record:
            return
        if not record.database:
            return
        if not record.measurement:
            return
        if not record.fields or not isinstance(record.fields, Dict):
            return
        # Switch database.
        Log.debug_print("[DATABASE] * Switching and writing database " + record.database)
        self._influxdb_client.switch_database(record.database)
        # Build point.
        point = [{
            DATABASE_JSON_KEY_MEASUREMENT: record.measurement,
            DATABASE_JSON_KEY_FIELDS: record.fields
        }]
        # Add tags.
        if (record.tags):
            point[0][DATABASE_JSON_KEY_TAGS] = record.tags
        # Add current timestamp if not provided.
        if (record.timestamp):
            point[0][DATABASE_JSON_KEY_TIME] = record.timestamp
        else:
            point[0][DATABASE_JSON_KEY_TIME] = int(time.time())
        # Write data.
        try:
            Log.debug_print("[DATABASE] * Writing point " + json.dumps(point))
            # Check retention policy.
            if (record.limited_retention == False):
                Log.debug_print("[DATABASE] * Applying " + DATABASE_RETENTION_POLICY_10_YEARS_NAME + " retention policy")
                self._influxdb_client.write_points(point, time_precision='s', retention_policy=DATABASE_RETENTION_POLICY_10_YEARS_NAME)
            else:
                Log.debug_print("[DATABASE] * Applying default retention policy")
                self._influxdb_client.write_points(point, time_precision='s')
        except:
            return

    def write_records(self, record_list: List[Record]) -> None:
        # Measurements loop.
        for record in record_list:
            self.write_record(record)
        
    def read_field(self, sigfox_ep_id: str, database: str, measurement: str, field: str, limited_retention: bool) -> Any:
        # Local variables.
        result = None
        rp = "" if (limited_retention == True) else (DATABASE_RETENTION_POLICY_10_YEARS_NAME + ".")
        # Build query.
        query = "SELECT last(" + field + ") FROM " + rp + measurement + " WHERE sigfox_ep_id='" + sigfox_ep_id + "'"
        # Switch database.
        Log.debug_print("[DATABASE] * Switching and reading database " + database)
        self._influxdb_client.switch_database(database)
        # Read data.
        Log.debug_print("[DATABASE] * Sending query: " + query)
        points = self._influxdb_client.query(query)
        Log.debug_print("[DATABASE] * Result: " + str(points))
        for p in points.get_points():
            result = p[DATABASE_FIELD_LAST]
        return result
