"""
* meteofox.py
*
*  Created on: 17 nov. 2021
*      Author: Ludo
"""

import math

from database.database import *
from ep.common import *
from log import *

### METEOFOX public macros ###

METEOFOX_SIGFOX_EP_ID_LIST = [ "53B5", "5436", "546C", "5477", "5497", "549D", "54B6", "54E4" ]

### METEOFOX local macros ###

METEOFOX_TAG_SITE = [ "Proto_HW1.0", "Proto_HW2.0", "Lamothe_Capdeville", "Prat_Albis", "Eaunes", "Escalquens", "Saint_Leon", "Kourou" ]

METEOFOX_UL_PAYLOAD_SIZE_MONITORING = 9
METEOFOX_UL_PAYLOAD_SIZE_WEATHER_IM = 6
METEOFOX_UL_PAYLOAD_SIZE_WEATHER_CM = 10
METEOFOX_UL_PAYLOAD_SIZE_ERROR_STACK = 12

METEOFOX_ERROR_VALUE_VSRC = 0xFFFF
METEOFOX_ERROR_VALUE_VCAP = 0xFFF
METEOFOX_ERROR_VALUE_VMCU = 0xFFF
METEOFOX_ERROR_VALUE_TEMPERATURE = 0x7F
METEOFOX_ERROR_VALUE_HUMIDITY = 0xFF
METEOFOX_ERROR_VALUE_LIGHT = 0xFF
METEOFOX_ERROR_VALUE_UV_INDEX = 0xFF
METEOFOX_ERROR_VALUE_PRESSURE = 0xFFFF
METEOFOX_ERROR_VALUE_WIND = 0xFF
METEOFOX_ERROR_VALUE_RAIN = 0xFF

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
        record_list = []
        record = Record()
        # Common properties.
        record.database = DATABASE_METEOFOX
        record.timestamp = timestamp
        record.tags = MeteoFox.get_tags(sigfox_ep_id)
        record.limited_retention = True
        # Keep alive frame (only for embedded software version older than sw1.2.42).
        if (ul_payload == COMMON_UL_PAYLOAD_KEEP_ALIVE):
            record.measurement = DATABASE_MEASUREMENT_METADATA
            record.fields = {
                DATABASE_FIELD_LAST_STARTUP_TIME: timestamp,
            }
            record.limited_retention = False
            record_list.append(copy.copy(record))
        # Startup frame.
        elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_SIZE_STARTUP)):
            Common.get_record_startup(record, timestamp, ul_payload, record_list)
        # Geolocation frame.
        elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_SIZE_GPS)):
            Common.get_record_gps(record, timestamp, ul_payload, record_list)
        # Geolocation timeout frame.
        elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_SIZE_GPS_TIMEOUT)):
            Common.get_record_gps_timeout(record, timestamp, ul_payload, record_list)
        # Error stack frame.
        elif (len(ul_payload) == (2 * METEOFOX_UL_PAYLOAD_SIZE_ERROR_STACK)):
            Common.get_record_error_stack(record, timestamp, ul_payload, (METEOFOX_UL_PAYLOAD_SIZE_ERROR_STACK // 2), record_list)
        # Monitoring frame.
        elif (len(ul_payload) == (2 * METEOFOX_UL_PAYLOAD_SIZE_MONITORING)):
            # Parse fields.
            tmcu_degrees_one_complement = int(ul_payload[0:2], 16)
            tpcb_degrees_one_complement = int(ul_payload[2:4], 16)
            hpcb_percent = int(ul_payload[4:6], 16)
            vsrc_mv = int(ul_payload[6:10], 16)
            vcap_mv = int(ul_payload[10:13], 16)
            vmcu_mv = int(ul_payload[13:16], 16)
            status = int(ul_payload[16:18], 16)
            # Create monitoring record.
            record.measurement = DATABASE_MEASUREMENT_MONITORING
            record.fields = {
                DATABASE_FIELD_STATUS: status,
                DATABASE_FIELD_LAST_DATA_TIME: timestamp
            }
            record.add_field(tmcu_degrees_one_complement, METEOFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_MCU_TEMPERATURE, float(Common.one_complement_to_value(tmcu_degrees_one_complement, 7)))
            record.add_field(tpcb_degrees_one_complement, METEOFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_TEMPERATURE, float(Common.one_complement_to_value(tpcb_degrees_one_complement, 7)))
            record.add_field(hpcb_percent, METEOFOX_ERROR_VALUE_HUMIDITY, DATABASE_FIELD_HUMIDITY, float(hpcb_percent))
            record.add_field(vsrc_mv, METEOFOX_ERROR_VALUE_VSRC, DATABASE_FIELD_SOURCE_VOLTAGE, float(vsrc_mv / 1000.0))
            record.add_field(vcap_mv, METEOFOX_ERROR_VALUE_VCAP, DATABASE_FIELD_STORAGE_VOLTAGE, float(vcap_mv / 1000.0))
            record.add_field(vmcu_mv, METEOFOX_ERROR_VALUE_VMCU, DATABASE_FIELD_MCU_VOLTAGE, float(vmcu_mv / 1000.0))
            record_list.append(copy.copy(record))
        # Weather data frame.
        elif ((len(ul_payload) == (2 * METEOFOX_UL_PAYLOAD_SIZE_WEATHER_IM)) or (len(ul_payload) == (2 * METEOFOX_UL_PAYLOAD_SIZE_WEATHER_CM))):
            # Parse fields.
            tamb_degrees_one_complement = int(ul_payload[0:2], 16)
            hamb_percent = int(ul_payload[2:4], 16)
            light_percent = int(ul_payload[4:6], 16)
            uv_index = int(ul_payload[6:8], 16)
            patm_abs_pa = int(ul_payload[8:12], 16)
            patm_sea_pa = METEOFOX_ERROR_VALUE_PRESSURE
            wind_speed_average_kmh = METEOFOX_ERROR_VALUE_WIND
            wind_speed_peak_kmh = METEOFOX_ERROR_VALUE_WIND
            wind_direction_average_two_degrees = METEOFOX_ERROR_VALUE_WIND
            rain_byte = METEOFOX_ERROR_VALUE_RAIN
            rainfall_mm = METEOFOX_ERROR_VALUE_RAIN
            # CM message only.
            if (len(ul_payload) == (2 * METEOFOX_UL_PAYLOAD_SIZE_WEATHER_CM)):
                # Parse additional fields.
                wind_speed_average_kmh = int(ul_payload[12:14], 16)
                wind_speed_peak_kmh = int(ul_payload[14:16], 16)
                wind_direction_average_two_degrees = int(ul_payload[16:18], 16)
                rain_byte = int(ul_payload[18:20], 16)
            # Compute sea level pressure.
            if ((patm_abs_pa != METEOFOX_ERROR_VALUE_PRESSURE) and (tamb_degrees_one_complement != METEOFOX_ERROR_VALUE_TEMPERATURE)):
                try:
                    altitude_query = database.read_field(sigfox_ep_id, DATABASE_METEOFOX, DATABASE_MEASUREMENT_GEOLOCATION, DATABASE_FIELD_GEOLOCATION_ALTITUDE, True)
                    if (altitude_query):
                        altitude = int(altitude_query)
                        Log.debug_print("[METEOFOX] * Computing sea-level pressure at altitude " + str(altitude) + "m")
                        patm_sea_pa = MeteoFox._compute_sea_level_pressure(patm_abs_pa, altitude, Common.one_complement_to_value(tamb_degrees_one_complement, 7))
                    else:
                        Log.debug_print("[METEOFOX] * Altitude not available for sea-level pressure computation")
                except:
                    pass
            # Compute rainfall.
            if (rain_byte != METEOFOX_ERROR_VALUE_RAIN):
                try:
                    sw_version_major_query = database.read_field(sigfox_ep_id, DATABASE_METEOFOX, DATABASE_MEASUREMENT_METADATA, DATABASE_FIELD_SW_VERSION_MAJOR, False)
                    sw_version_minor_query = database.read_field(sigfox_ep_id, DATABASE_METEOFOX, DATABASE_MEASUREMENT_METADATA, DATABASE_FIELD_SW_VERSION_MINOR, False)
                    # Check results.
                    if (sw_version_major_query and sw_version_minor_query):
                        sw_version_major = int(sw_version_major_query)
                        sw_version_minor = int(sw_version_minor_query)
                        Log.debug_print("[METEOFOX] * Computing rainfall for firmware version sw" + str(sw_version_major) + "." + str(sw_version_minor))
                        # Check version.
                        if ((sw_version_major > 6) or ((sw_version_major >= 6) and (sw_version_minor >= 5))):
                            # Format with dynamic unit.
                            unit = (rain_byte >> 7)
                            if (unit == 0):
                                rainfall_mm = ((rain_byte & 0x7F) / 10.0)
                            else:
                                rainfall_mm = (rain_byte & 0x7F)
                        else:
                            # Format in mm.
                            rainfall_mm = rain_byte
                    else:
                        Log.debug_print("[METEOFOX] * Firmware version not available for rainfall computation")
                except:
                    pass
            # Create weather record.
            record.measurement = DATABASE_MEASUREMENT_WEATHER
            record.fields = {
                DATABASE_FIELD_LAST_DATA_TIME: timestamp
            }
            record.add_field(tamb_degrees_one_complement, METEOFOX_ERROR_VALUE_TEMPERATURE, DATABASE_FIELD_TEMPERATURE, float(Common.one_complement_to_value(tamb_degrees_one_complement, 7)))
            record.add_field(hamb_percent, METEOFOX_ERROR_VALUE_HUMIDITY, DATABASE_FIELD_HUMIDITY, float(hamb_percent))
            record.add_field(light_percent, METEOFOX_ERROR_VALUE_LIGHT, DATABASE_FIELD_SUNSHINE_LIGHT, float(light_percent))
            record.add_field(uv_index, METEOFOX_ERROR_VALUE_UV_INDEX, DATABASE_FIELD_SUNSHINE_UV_INDEX, float(uv_index))
            record.add_field(patm_abs_pa, METEOFOX_ERROR_VALUE_PRESSURE, DATABASE_FIELD_PRESSURE_ATMOSPHERIC_ABSOLUTE, float(patm_abs_pa / 10.0))
            record.add_field(patm_sea_pa, METEOFOX_ERROR_VALUE_PRESSURE, DATABASE_FIELD_PRESSURE_ATMOSPHERIC_SEA_LEVEL, float(patm_sea_pa / 10.0))
            record.add_field(wind_speed_average_kmh, METEOFOX_ERROR_VALUE_WIND, DATABASE_FIELD_WIND_SPEED_AVERAGE, float(wind_speed_average_kmh))
            record.add_field(wind_speed_peak_kmh, METEOFOX_ERROR_VALUE_WIND, DATABASE_FIELD_WIND_SPEED_PEAK, float(wind_speed_peak_kmh))
            record.add_field(wind_direction_average_two_degrees, METEOFOX_ERROR_VALUE_WIND, DATABASE_FIELD_WIND_DIRECTION_AVERAGE, float(wind_direction_average_two_degrees * 2.0))
            record.add_field(rainfall_mm, METEOFOX_ERROR_VALUE_RAIN, DATABASE_FIELD_RAINFALL, float(rainfall_mm))
            record_list.append(copy.copy(record))
        else:
            Log.debug_print("[METEOFOX] * Invalid UL payload")
        return record_list
    
    @staticmethod
    def get_default_dl_payload(sigfox_ep_id: str) -> str:
        # Local variables.
        dl_payload = []
        # Check ID.
        if (sigfox_ep_id in METEOFOX_SIGFOX_EP_ID_LIST):
            dl_payload = "0000000000000000"
        return dl_payload
