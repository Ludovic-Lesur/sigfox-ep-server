"""
* meteofox.py
*
*  Created on: 17 nov. 2021
*      Author: Ludo
"""

import math

from database.database import *
from ep.common import *
from ep.ep import *
from utils.log import *
from utils.sigfox_cloud import *
from datetime import datetime, timedelta

### METEOFOX public macros ###

METEOFOX_DEVICE_TYPE_NAME = "meteofox"
METEOFOX_SIGFOX_EP_ID_LIST = ep.get_tags_list(METEOFOX_DEVICE_TYPE_NAME, DATABASE_TAG_SIGFOX_EP_ID)

### METEOFOX local macros ###

METEOFOX_TAG_SITE = ep.get_tags_list(METEOFOX_DEVICE_TYPE_NAME, DATABASE_TAG_SITE)

METEOFOX_UL_PAYLOAD_SIZE_MONITORING = 9

METEOFOX_UL_PAYLOAD_SIZE_WEATHER_IM_V1_V2 = 6
METEOFOX_UL_PAYLOAD_SIZE_WEATHER_IM_V3 = 7

METEOFOX_UL_PAYLOAD_SIZE_WEATHER_CM_V1_V2 = 10
METEOFOX_UL_PAYLOAD_SIZE_WEATHER_CM_V3 = 12

METEOFOX_UL_PAYLOAD_SIZE_ERROR_STACK_V1_V2 = 12
METEOFOX_UL_PAYLOAD_SIZE_ERROR_STACK_V3 = 10

METEOFOX_ERROR_VALUE_TEMPERATURE_V1 = 0x7F
METEOFOX_ERROR_VALUE_TEMPERATURE_V2 = 0x7FF
METEOFOX_ERROR_VALUE_TEMPERATURE_V3 = 0x7FF

METEOFOX_ERROR_VALUE_HUMIDITY_V1 = 0xFF
METEOFOX_ERROR_VALUE_HUMIDITY_V2 = 0xFF
METEOFOX_ERROR_VALUE_HUMIDITY_V3 = 0x7F

METEOFOX_ERROR_VALUE_SUNSHINE_LIGHT_V1 = 0xFF
METEOFOX_ERROR_VALUE_SUNSHINE_LIGHT_V2 = 0xFF
METEOFOX_ERROR_VALUE_SUNSHINE_LIGHT_V3 = 0xFFFF

METEOFOX_ERROR_VALUE_SUNSHINE_UV_INDEX_V1 = 0xFF
METEOFOX_ERROR_VALUE_SUNSHINE_UV_INDEX_V2 = 0xF
METEOFOX_ERROR_VALUE_SUNSHINE_UV_INDEX_V3 = 0x7F

METEOFOX_ERROR_VALUE_PRESSURE_ATMOSPHERIC_ABSOLUTE_V1 = 0xFFFF
METEOFOX_ERROR_VALUE_PRESSURE_ATMOSPHERIC_ABSOLUTE_V2 = 0xFFFF
METEOFOX_ERROR_VALUE_PRESSURE_ATMOSPHERIC_ABSOLUTE_V3 = 0x3FFF

METEOFOX_ERROR_VALUE_WIND_SPEED_V1 = 0xFF
METEOFOX_ERROR_VALUE_WIND_SPEED_V2 = 0xFF
METEOFOX_ERROR_VALUE_WIND_SPEED_V3 = 0x7FF

METEOFOX_ERROR_VALUE_WIND_DIRECTION_V1 = 0xFF
METEOFOX_ERROR_VALUE_WIND_DIRECTION_V2 = 0xFF
METEOFOX_ERROR_VALUE_WIND_DIRECTION_V3 = 0x1FF

METEOFOX_ERROR_VALUE_RAINFALL_V1 = 0xFF
METEOFOX_ERROR_VALUE_RAINFALL_V2 = 0xFF
METEOFOX_ERROR_VALUE_RAINFALL_V3 = 0x1FF

METEOFOX_ERROR_VALUE_SOURCE_VOLTAGE_V1 = 0xFFFF
METEOFOX_ERROR_VALUE_SOURCE_VOLTAGE_V2 = 0xFFF

METEOFOX_ERROR_VALUE_STORAGE_VOLTAGE = 0xFFF

METEOFOX_ERROR_VALUE_MCU_TEMPERATURE = 0x7F
METEOFOX_ERROR_VALUE_MCU_VOLTAGE = 0xFFF

### METEOFOX classes ###

class MeteoFox:
    
    @staticmethod
    def _compute_sea_level_pressure(absolute_pressure_pa: float, altitude_m: float, temperature_degrees: float) -> float:
        temperature_kelvin = (temperature_degrees + 273.15)
        return float(absolute_pressure_pa * math.exp(-5.255 * math.log((temperature_kelvin) / (temperature_kelvin + 0.0065 * altitude_m))))
    
    @staticmethod
    def _get_site(sigfox_ep_id: str) -> str:
        # Default is unknown.
        site = COMMON_UNKNOWN
        if (sigfox_ep_id in METEOFOX_SIGFOX_EP_ID_LIST):
            site = METEOFOX_TAG_SITE[METEOFOX_SIGFOX_EP_ID_LIST.index(sigfox_ep_id)]
        return site

    @staticmethod
    def get_tags(sigfox_ep_id: str) -> Dict[str, Any]:
        # Local variables.
        tags = {
            DATABASE_TAG_SIGFOX_EP_ID: sigfox_ep_id,
            DATABASE_TAG_SITE: MeteoFox._get_site(sigfox_ep_id)
        }
        return tags

    @staticmethod
    def get_record_list(database: Database, timestamp: int, sigfox_ep_id: str, ul_payload: str) -> List[Record]:
        # Local variables.
        data_type = DATABASE_FIELD_DATA_TYPE_UNKNOWN
        record_list = []
        record = Record()
        where_clause = DATABASE_TAG_SITE + "='" + MeteoFox._get_site(sigfox_ep_id) + "'"
        # Common properties.
        record.database = DATABASE_METEOFOX
        record.timestamp = timestamp
        record.tags = MeteoFox.get_tags(sigfox_ep_id)
        record.limited_retention = True
        # Startup frame.
        if (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_SIZE_STARTUP)):
            data_type = Common.get_record_startup(record, timestamp, ul_payload, record_list)
        # Geolocation frame.
        elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_SIZE_GPS)):
            data_type = Common.get_record_gps(record, timestamp, ul_payload, record_list)
        # Geolocation timeout frame.
        elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_SIZE_GPS_TIMEOUT)):
            data_type = Common.get_record_gps_timeout(record, timestamp, ul_payload, record_list)
        # Other frames format depends on software version.
        else:
            # Read software version.
            sw_version_major_query, _ = database.read_field(DATABASE_METEOFOX, where_clause, DATABASE_MEASUREMENT_METADATA, DATABASE_FIELD_SW_VERSION_MAJOR, False)
            sw_version_minor_query, _ = database.read_field(DATABASE_METEOFOX, where_clause, DATABASE_MEASUREMENT_METADATA, DATABASE_FIELD_SW_VERSION_MINOR, False)
            # Check results.
            if ((sw_version_major_query is not None) and (sw_version_minor_query is not None)):
                sw_version_major = int(sw_version_major_query)
                sw_version_minor = int(sw_version_minor_query)
                Log.debug_print("[METEOFOX] * Parsing frame for firmware version sw" + str(sw_version_major) + "." + str(sw_version_minor))
                # Update frames size.
                if (sw_version_major >= 8):
                    ul_payload_size_weather_im = METEOFOX_UL_PAYLOAD_SIZE_WEATHER_IM_V3
                    ul_payload_size_weather_cm = METEOFOX_UL_PAYLOAD_SIZE_WEATHER_CM_V3
                    ul_payload_size_error_stack = METEOFOX_UL_PAYLOAD_SIZE_ERROR_STACK_V3
                else:
                    ul_payload_size_weather_im = METEOFOX_UL_PAYLOAD_SIZE_WEATHER_IM_V1_V2
                    ul_payload_size_weather_cm = METEOFOX_UL_PAYLOAD_SIZE_WEATHER_CM_V1_V2
                    ul_payload_size_error_stack = METEOFOX_UL_PAYLOAD_SIZE_ERROR_STACK_V1_V2
                # Error stack frame.
                if (len(ul_payload) == (2 * ul_payload_size_error_stack)):
                    data_type = Common.get_record_error_stack(record, timestamp, ul_payload, (ul_payload_size_error_stack // 2), record_list)
                # Monitoring frame.
                if (len(ul_payload) == (2 * METEOFOX_UL_PAYLOAD_SIZE_MONITORING)):
                    # Check version.
                    if (sw_version_major >= 7):
                        # Temperature.
                        temperature_signed_magnitude = int(ul_payload[0:3], 16)
                        temperature_degrees = float((Common.signed_magnitude_to_value(temperature_signed_magnitude, 11)) / (10.0))
                        temperature_error_value = METEOFOX_ERROR_VALUE_TEMPERATURE_V2
                        # Humidity.
                        humidity_percent = float(int(ul_payload[3:5], 16))
                        humidity_error_value = METEOFOX_ERROR_VALUE_HUMIDITY_V2
                        # Source voltage
                        source_voltage_ten_mv = int(ul_payload[5:8], 16)
                        source_voltage_volts = float(source_voltage_ten_mv / 100.0)
                        source_voltage_error_value = METEOFOX_ERROR_VALUE_SOURCE_VOLTAGE_V2
                        # Storage voltage.
                        storage_voltage = int(ul_payload[8:11], 16)
                        storage_voltage_volts = float(storage_voltage / 1000.0)
                        # MCU temperature.
                        mcu_temperature_signed_magnitude = int(ul_payload[11:13], 16)
                        mcu_temperature_degrees = float(Common.signed_magnitude_to_value(mcu_temperature_signed_magnitude, 7))
                        # MCU voltage.
                        mcu_voltage_mv = int(ul_payload[13:16], 16)
                        mcu_voltage_volts = float(mcu_voltage_mv / 1000.0)
                        # Status.
                        status = int(ul_payload[16:18], 16)
                    else:
                        # MCU temperature.
                        mcu_temperature_signed_magnitude = int(ul_payload[0:2], 16)
                        mcu_temperature_degrees = float(Common.signed_magnitude_to_value(mcu_temperature_signed_magnitude, 7))
                        # Temperature.
                        temperature_signed_magnitude = int(ul_payload[2:4], 16)
                        temperature_degrees = float(Common.signed_magnitude_to_value(temperature_signed_magnitude, 7))
                        temperature_error_value = METEOFOX_ERROR_VALUE_TEMPERATURE_V1
                        # Humidity.
                        humidity_percent = float(int(ul_payload[4:6], 16))
                        humidity_error_value = METEOFOX_ERROR_VALUE_HUMIDITY_V1
                        # Source voltage
                        source_voltage_ten_mv = int(ul_payload[6:10], 16)
                        source_voltage_volts = float(source_voltage_ten_mv / 1000.0)
                        source_voltage_error_value = METEOFOX_ERROR_VALUE_SOURCE_VOLTAGE_V1
                        # Storage voltage.
                        storage_voltage_mv = int(ul_payload[10:13], 16)
                        storage_voltage_volts = float(storage_voltage / 1000.0)
                        # MCU voltage.
                        mcu_voltage_mv = int(ul_payload[13:16], 16)
                        mcu_voltage_volts = float(mcu_voltage_mv / 1000.0)
                        # Status.
                        status = int(ul_payload[16:18], 16)
                    # Create monitoring record.
                    record.measurement = DATABASE_MEASUREMENT_MONITORING
                    record.fields = {
                        DATABASE_FIELD_STATUS: status,
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(temperature_signed_magnitude, temperature_error_value, DATABASE_FIELD_TEMPERATURE, float(temperature_degrees))
                    record.add_field(humidity_percent, humidity_error_value, DATABASE_FIELD_HUMIDITY, float(humidity_percent))
                    record.add_field(source_voltage_ten_mv, source_voltage_error_value, DATABASE_FIELD_SOURCE_VOLTAGE, float(source_voltage_volts))
                    record.add_field(storage_voltage_mv, METEOFOX_ERROR_VALUE_STORAGE_VOLTAGE, DATABASE_FIELD_STORAGE_VOLTAGE, float(storage_voltage_volts))
                    record.add_field(mcu_temperature_signed_magnitude, METEOFOX_ERROR_VALUE_MCU_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, float(mcu_temperature_degrees))
                    record.add_field(mcu_voltage_mv, METEOFOX_ERROR_VALUE_MCU_VOLTAGE, DATABASE_FIELD_MCU_VOLTAGE, float(mcu_voltage_volts))
                    record_list.append(copy.copy(record))
                    data_type = DatabaseFieldDataType.PERIODIC_MONITORING.value
                # Weather data frame.
                elif ((len(ul_payload) == (2 * ul_payload_size_weather_im)) or (len(ul_payload) == (2 * ul_payload_size_weather_cm))):
                    # Check version.
                    if (sw_version_major >= 8):
                        # Temperature.
                        temperature_signed_magnitude = int(ul_payload[0:3], 16)
                        temperature_degrees = float((Common.signed_magnitude_to_value(temperature_signed_magnitude, 11)) / (10.0))
                        temperature_error_value = METEOFOX_ERROR_VALUE_TEMPERATURE_V3
                        # Humidity.
                        humidity_percent = float((int(ul_payload[3:5], 16) >> 1) & 0x7F)
                        humidity_error_value = METEOFOX_ERROR_VALUE_HUMIDITY_V3
                        # Sunshine light.
                        sunshine_light_raw = ((int(ul_payload[4:9], 16) >> 1) & 0xFFFF)
                        sunshine_light_unit = ((sunshine_light_raw >> 14) & 0x0003)
                        sunshine_light_value = (sunshine_light_raw & 0x3FFF)
                        sunshine_light_error_value = METEOFOX_ERROR_VALUE_SUNSHINE_LIGHT_V3
                        if (sunshine_light_unit == 0):
                            sunshine_light = float(sunshine_light_value / 100.0)
                        elif (sunshine_light_unit == 1):
                            sunshine_light = float(sunshine_light_value / 10.0)
                        elif (sunshine_light_unit == 2):
                            sunshine_light = float(sunshine_light_value / 1.0)
                        else:
                            sunshine_light = float(sunshine_light_value * 10.0)
                        # Sunshine UV index.
                        sunshine_uv_index = float(((int(ul_payload[8:11], 16) >> 2) & 0x7F) / 10.0)
                        sunshine_uv_index_error_value = METEOFOX_ERROR_VALUE_SUNSHINE_UV_INDEX_V3
                        # Absolute pressure.
                        pressure_atmospheric_absolute_pa = (int(ul_payload[10:14], 16) & 0x3FFF)
                        pressure_atmospheric_absolute_hpa = float(pressure_atmospheric_absolute_pa / 10.0)
                        pressure_atmospheric_error_value = METEOFOX_ERROR_VALUE_PRESSURE_ATMOSPHERIC_ABSOLUTE_V3
                        # Continuous measurements.
                        wind_speed_average_raw = METEOFOX_ERROR_VALUE_WIND_SPEED_V3
                        wind_speed_average_kmh = METEOFOX_ERROR_VALUE_WIND_SPEED_V3
                        wind_speed_peak_raw = METEOFOX_ERROR_VALUE_WIND_SPEED_V3
                        wind_speed_peak_kmh = METEOFOX_ERROR_VALUE_WIND_SPEED_V3
                        wind_speed_error_value = METEOFOX_ERROR_VALUE_WIND_SPEED_V3
                        wind_direction_average_raw = METEOFOX_ERROR_VALUE_WIND_DIRECTION_V3
                        wind_direction_average_degrees = METEOFOX_ERROR_VALUE_WIND_DIRECTION_V3
                        wind_direction_average_error_value = METEOFOX_ERROR_VALUE_WIND_DIRECTION_V3
                        rainfall_raw = METEOFOX_ERROR_VALUE_RAINFALL_V3
                        rainfall_mm = METEOFOX_ERROR_VALUE_RAINFALL_V3
                        rainfall_error_value = METEOFOX_ERROR_VALUE_RAINFALL_V3
                        # Check UL payload size.
                        if (len(ul_payload) == (2 * ul_payload_size_weather_cm)):
                            # Wind speed.
                            wind_speed_average_raw = ((int(ul_payload[14:17], 16) >> 1) & 0x7FF)
                            wind_speed_average_kmh = float(wind_speed_average_raw / 10.0)
                            wind_speed_peak_raw = ((int(ul_payload[16:20], 16) >> 2) & 0x7FF)
                            wind_speed_peak_kmh = float(wind_speed_peak_raw / 10.0)
                            # Wind direction.
                            wind_direction_average_raw = ((int(ul_payload[19:23], 16) >> 1) & 0x01FF)
                            wind_direction_average_degrees = float(wind_direction_average_raw)
                            # Rainfall.
                            rainfall_raw = (int(ul_payload[22:24], 16) & 0x01FF)
                            rainfall_unit = ((rainfall_raw >> 8) & 0x01)
                            rainfall_value = (rainfall_raw & 0x0FF)
                            if (rainfall_unit == 0):
                                rainfall_mm = float(rainfall_value / 10.0)
                            else:
                                rainfall_mm = float(rainfall_value / 1.0)
                    elif (sw_version_major >= 7):
                        # Temperature.
                        temperature_signed_magnitude = int(ul_payload[0:3], 16)
                        temperature_degrees = float((Common.signed_magnitude_to_value(temperature_signed_magnitude, 11)) / (10.0))
                        temperature_error_value = METEOFOX_ERROR_VALUE_TEMPERATURE_V2
                        # Humidity.
                        humidity_percent = float(int(ul_payload[3:5], 16))
                        humidity_error_value = METEOFOX_ERROR_VALUE_HUMIDITY_V2
                        # Sunshine light.
                        sunshine_light = float(int(ul_payload[5:7], 16))
                        sunshine_light_error_value = METEOFOX_ERROR_VALUE_SUNSHINE_LIGHT_V2
                        # Sunshine UV index.
                        sunshine_uv_index = float(int(ul_payload[7:8], 16))
                        sunshine_uv_index_error_value = METEOFOX_ERROR_VALUE_SUNSHINE_UV_INDEX_V2
                        # Absolute pressure.
                        pressure_atmospheric_absolute_pa = int(ul_payload[8:12], 16)
                        pressure_atmospheric_absolute_hpa = float(pressure_atmospheric_absolute_pa / 10.0)
                        pressure_atmospheric_error_value = METEOFOX_ERROR_VALUE_PRESSURE_ATMOSPHERIC_ABSOLUTE_V2
                        # Continuous measurements.
                        wind_speed_average_raw = METEOFOX_ERROR_VALUE_WIND_SPEED_V2
                        wind_speed_average_kmh = METEOFOX_ERROR_VALUE_WIND_SPEED_V2
                        wind_speed_peak_raw = METEOFOX_ERROR_VALUE_WIND_SPEED_V2
                        wind_speed_peak_kmh = METEOFOX_ERROR_VALUE_WIND_SPEED_V2
                        wind_speed_error_value = METEOFOX_ERROR_VALUE_WIND_SPEED_V2
                        wind_direction_average_raw = METEOFOX_ERROR_VALUE_WIND_DIRECTION_V2
                        wind_direction_average_degrees = METEOFOX_ERROR_VALUE_WIND_DIRECTION_V2
                        wind_direction_average_error_value = METEOFOX_ERROR_VALUE_WIND_DIRECTION_V2
                        rainfall_raw = METEOFOX_ERROR_VALUE_RAINFALL_V2
                        rainfall_mm = METEOFOX_ERROR_VALUE_RAINFALL_V2
                        rainfall_error_value = METEOFOX_ERROR_VALUE_RAINFALL_V2
                        # Check UL payload size.
                        if (len(ul_payload) == (2 * ul_payload_size_weather_cm)):
                            # Wind speed.
                            wind_speed_average_raw = int(ul_payload[12:14], 16)
                            wind_speed_average_kmh = float(wind_speed_average_raw)
                            wind_speed_peak_raw = int(ul_payload[14:16], 16)
                            wind_speed_peak_kmh = float(wind_speed_peak_raw)
                            # Wind direction.
                            wind_direction_average_raw = int(ul_payload[16:18], 16)
                            wind_direction_average_degrees = float(wind_direction_average_raw * 2.0)
                            # Rainfall.
                            rainfall_raw = int(ul_payload[18:20], 16)
                            rainfall_unit = ((rainfall_raw >> 7) & 0x01)
                            rainfall_value = (rainfall_raw & 0x7F)
                            if (rainfall_unit == 0):
                                rainfall_mm = float(rainfall_value / 10.0)
                            else:
                                rainfall_mm = float(rainfall_value / 1.0)
                    else:
                        # Temperature.
                        temperature_signed_magnitude = int(ul_payload[0:2], 16)
                        temperature_degrees = float(Common.signed_magnitude_to_value(temperature_signed_magnitude, 7))
                        temperature_error_value = METEOFOX_ERROR_VALUE_TEMPERATURE_V1
                        # Humidity.
                        humidity_percent = float(int(ul_payload[2:4], 16))
                        humidity_error_value = METEOFOX_ERROR_VALUE_HUMIDITY_V1
                        # Sunshine light.
                        sunshine_light = float(int(ul_payload[4:6], 16))
                        sunshine_light_error_value = METEOFOX_ERROR_VALUE_SUNSHINE_LIGHT_V1
                        # Sunshine UV index.
                        sunshine_uv_index = float(int(ul_payload[6:8], 16))
                        sunshine_uv_index_error_value = METEOFOX_ERROR_VALUE_SUNSHINE_UV_INDEX_V1
                        # Absolute pressure.
                        pressure_atmospheric_absolute_pa = int(ul_payload[8:12], 16)
                        pressure_atmospheric_absolute_hpa = float(pressure_atmospheric_absolute_pa / 10.0)
                        pressure_atmospheric_error_value = METEOFOX_ERROR_VALUE_PRESSURE_ATMOSPHERIC_ABSOLUTE_V1
                        # Continuous measurements.
                        wind_speed_average_raw = METEOFOX_ERROR_VALUE_WIND_SPEED_V1
                        wind_speed_average_kmh = METEOFOX_ERROR_VALUE_WIND_SPEED_V1
                        wind_speed_peak_raw = METEOFOX_ERROR_VALUE_WIND_SPEED_V1
                        wind_speed_peak_kmh = METEOFOX_ERROR_VALUE_WIND_SPEED_V1
                        wind_speed_error_value = METEOFOX_ERROR_VALUE_WIND_SPEED_V1
                        wind_direction_average_raw = METEOFOX_ERROR_VALUE_WIND_DIRECTION_V1
                        wind_direction_average_degrees = METEOFOX_ERROR_VALUE_WIND_DIRECTION_V1
                        wind_direction_average_error_value = METEOFOX_ERROR_VALUE_WIND_DIRECTION_V1
                        rainfall_raw = METEOFOX_ERROR_VALUE_RAINFALL_V1
                        rainfall_mm = METEOFOX_ERROR_VALUE_RAINFALL_V1
                        rainfall_error_value = METEOFOX_ERROR_VALUE_RAINFALL_V1
                        # Check UL payload size.
                        if (len(ul_payload) == (2 * ul_payload_size_weather_cm)):
                            # Wind speed.
                            wind_speed_average_raw = int(ul_payload[12:14], 16)
                            wind_speed_average_kmh = float(wind_speed_average_raw)
                            wind_speed_peak_raw = int(ul_payload[14:16], 16)
                            wind_speed_peak_kmh = float(wind_speed_peak_raw)
                            # Wind direction.
                            wind_direction_average_raw = int(ul_payload[16:18], 16)
                            wind_direction_average_degrees = float(wind_direction_average_raw * 2.0)
                            # Rainfall.
                            rainfall_raw = int(ul_payload[18:20], 16)
                            # Check software version.
                            if ((sw_version_major > 6) or ((sw_version_major >= 6) and (sw_version_minor >= 5))):
                                # Format with dynamic unit.
                                rainfall_unit = ((rainfall_raw >> 7) & 0x01)
                                rainfall_value = (rainfall_raw & 0x7F)
                                if (rainfall_unit == 0):
                                    rainfall_mm = float(rainfall_value / 10.0)
                                else:
                                    rainfall_mm = float(rainfall_value / 1.0)
                            else:
                                rainfall_mm = float(rainfall_raw)
                    # Compute sea level pressure.
                    pressure_atmospheric_sea_level_pa = pressure_atmospheric_error_value
                    if ((pressure_atmospheric_absolute_pa != pressure_atmospheric_error_value) and (temperature_signed_magnitude != temperature_error_value)):
                        try:
                            altitude_query, _ = database.read_field(DATABASE_METEOFOX, where_clause, DATABASE_MEASUREMENT_GEOLOCATION, DATABASE_FIELD_GEOLOCATION_ALTITUDE, True)
                            if (altitude_query):
                                altitude = int(altitude_query)
                                Log.debug_print("[METEOFOX] * Computing sea-level pressure at altitude " + str(altitude) + "m")
                                pressure_atmospheric_sea_level_pa = MeteoFox._compute_sea_level_pressure(pressure_atmospheric_absolute_pa, altitude, temperature_degrees)
                                pressure_atmospheric_sea_level_hpa = float(pressure_atmospheric_sea_level_pa / 10.0)
                            else:
                                Log.debug_print("[METEOFOX] * Altitude not available for sea-level pressure computation")
                        except:
                            pass
                    # Create weather record.
                    record.measurement = DATABASE_MEASUREMENT_WEATHER
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp
                    }
                    record.add_field(temperature_signed_magnitude, temperature_error_value, DATABASE_FIELD_TEMPERATURE, temperature_degrees)
                    record.add_field(humidity_percent, humidity_error_value, DATABASE_FIELD_HUMIDITY, float(humidity_percent))
                    record.add_field(sunshine_light, sunshine_light_error_value, DATABASE_FIELD_SUNSHINE_LIGHT, float(sunshine_light))
                    record.add_field(sunshine_uv_index, sunshine_uv_index_error_value, DATABASE_FIELD_SUNSHINE_UV_INDEX, float(sunshine_uv_index))
                    record.add_field(pressure_atmospheric_absolute_pa, pressure_atmospheric_error_value, DATABASE_FIELD_PRESSURE_ATMOSPHERIC_ABSOLUTE, float(pressure_atmospheric_absolute_hpa))
                    record.add_field(pressure_atmospheric_sea_level_pa, pressure_atmospheric_error_value, DATABASE_FIELD_PRESSURE_ATMOSPHERIC_SEA_LEVEL, float(pressure_atmospheric_sea_level_hpa))
                    record.add_field(wind_speed_average_raw, wind_speed_error_value, DATABASE_FIELD_WIND_SPEED_AVERAGE, float(wind_speed_average_kmh))
                    record.add_field(wind_speed_peak_raw, wind_speed_error_value, DATABASE_FIELD_WIND_SPEED_PEAK, float(wind_speed_peak_kmh))
                    record.add_field(wind_direction_average_raw, wind_direction_average_error_value, DATABASE_FIELD_WIND_DIRECTION_AVERAGE, float(wind_direction_average_degrees))
                    record.add_field(rainfall_raw, rainfall_error_value, DATABASE_FIELD_RAINFALL, float(rainfall_mm))
                    record_list.append(copy.copy(record))
                    data_type = DatabaseFieldDataType.PERIODIC_WEATHER.value
                else:
                    Log.debug_print("[METEOFOX] * Invalid UL payload")
            else:
                Log.debug_print("[METEOFOX] * Firmware version not available for parsing")
        return [data_type, record_list]
    
    @staticmethod
    def get_default_dl_payload(sigfox_ep_id: str) -> str:
        # Local variables.
        dl_payload = []
        # Check ID.
        if (sigfox_ep_id in METEOFOX_SIGFOX_EP_ID_LIST):
            dl_payload = "0000000000000000"
        return dl_payload

    @staticmethod
    def update_dl_payload(sigfox_ep_id: str, dl_payload: str) -> str:
        # Check ID.
        if (sigfox_ep_id in METEOFOX_SIGFOX_EP_ID_LIST):
            # Convert to byte array.
            payload_bytes = bytearray.fromhex(dl_payload)
            # Check operation code.
            if (payload_bytes[0] == 3):
                # Update time.
                dl_timestamp = datetime.utcnow() + timedelta(seconds=SIGFOX_CLOUD_CALLBACK_DOWNLINK_TIMESTAMP_DELTA)
                payload_bytes[1] = ((dl_timestamp.year >> 8) & 0xFF)
                payload_bytes[2] = ((dl_timestamp.year >> 0) & 0xFF)
                payload_bytes[3] = dl_timestamp.month
                payload_bytes[4] = dl_timestamp.day
                payload_bytes[5] = dl_timestamp.hour
                payload_bytes[6] = dl_timestamp.minute
                payload_bytes[7] = dl_timestamp.second
            # Convert to string.
            dl_payload = payload_bytes.hex().lower()
        return dl_payload
