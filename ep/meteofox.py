from __future__ import print_function
import math

from database.influx_db import *
from log import *
from ep.common import *

### LOCAL MACROS ###

# MeteoFox tags.
__METEOFOX_SITE = ["Proto_HW1.0", "Proto_HW2.0", "Lamothe_Capdeville", "Prat_Albis", "Eaunes", "Escalquens", "Saint_Leon", "Kourou"]
# Sigfox frame lengths.
__METEOFOX_UL_PAYLOAD_MONITORING_SIZE = 9
__METEOFOX_UL_PAYLOAD_WEATHER_IM_SIZE = 6
__METEOFOX_UL_PAYLOAD_WEATHER_CM_SIZE = 10
__METEOFOX_UL_PAYLOAD_ERROR_STACK_SIZE = 12

### PUBLIC MACROS ###

# MeteoFox EP-IDs.
METEOFOX_EP_ID_LIST = ["53B5", "5436", "546C", "5477", "5497", "549D", "54B6", "54E4"]

### LOCAL FUNCTIONS ###

# Function to compute sea-level pressure (barometric formula).
def __METEOFOX_compute_sea_level_pressure(absolute_pressure, altitude, temperature):
    # a^(x) = exp(x*ln(a))
    temperature_kelvin = temperature + 273.15
    return (absolute_pressure * math.exp(-5.255 * math.log((temperature_kelvin) / (temperature_kelvin + 0.0065 * altitude))))

# Function performing Sigfox ID to MeteoFox site conversion.
def __METEOFOX_get_site(sigfox_ep_id):
    # Default is unknown.
    site = "unknown"
    if (sigfox_ep_id in METEOFOX_EP_ID_LIST):
        site = __METEOFOX_SITE[METEOFOX_EP_ID_LIST.index(sigfox_ep_id)]
    return site

### PUBLIC FUNCTIONS ###

# Function adding the specific MeteoFox tags.
def METEOFOX_add_ep_tag(json_ul_data, sigfox_ep_id):
    for idx in range(len(json_ul_data)):
        if ("tags" in json_ul_data[idx]):
            json_ul_data[idx]["tags"][INFLUX_DB_TAG_SIGFOX_EP_ID] = sigfox_ep_id
            json_ul_data[idx]["tags"][INFLUX_DB_TAG_SITE] = __METEOFOX_get_site(sigfox_ep_id)
        else:
            json_ul_data[idx]["tags"] = {
                INFLUX_DB_TAG_SIGFOX_EP_ID: sigfox_ep_id,
                INFLUX_DB_TAG_SITE: __METEOFOX_get_site(sigfox_ep_id)
            }

# Function for parsing MeteoFox device payload and fill database.
def METEOFOX_parse_ul_payload(timestamp, sigfox_ep_id, ul_payload):
    # Init JSON object.
    json_ul_data = []
    # Keep alive frame (only for embedded software version older than sw1.2.42).
    if (ul_payload == COMMON_UL_PAYLOAD_KEEP_ALIVE):
        # Create JSON object.
        json_ul_data = [
        {
            "time": timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_METADATA,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_STARTUP: timestamp,
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION: timestamp
            }
        }]
        LOG_print("[METEOFOX] * Startup * site=" + __METEOFOX_get_site(sigfox_ep_id))
    # Startup frame.
    elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_STARTUP_SIZE)):
        # Create JSON object.
        result = COMMON_create_json_startup_data(timestamp, ul_payload)
        json_ul_data = result[0]
        log_data = result[1]
        LOG_print("[METEOFOX] * Startup data * site=" + __METEOFOX_get_site(sigfox_ep_id) + " " + log_data)
    # Geolocation frame.
    elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_GEOLOC_SIZE)):
        # Create JSON object.
        result = COMMON_create_json_geoloc_data(timestamp, ul_payload)
        json_ul_data = result[0]
        log_data = result[1]
        LOG_print("[METEOFOX] * Geoloc data * site=" + __METEOFOX_get_site(sigfox_ep_id) + " " + log_data)
    # Geolocation timeout frame V1.
    elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_GEOLOC_TIMEOUT_SIZE_V1)):
        # Create JSON object.
        result = COMMON_create_json_geoloc_timeout_data(timestamp, ul_payload, COMMON_UL_PAYLOAD_GEOLOC_TIMEOUT_SIZE_V1)
        json_ul_data = result[0]
        log_data = result[1]
        LOG_print("[METEOFOX] * Geoloc timeout V1 * site=" + __METEOFOX_get_site(sigfox_ep_id) + " " + log_data)
    # Geolocation timeout frame V2.
    elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_GEOLOC_TIMEOUT_SIZE_V2)):
        # Create JSON object.
        result = COMMON_create_json_geoloc_timeout_data(timestamp, ul_payload, COMMON_UL_PAYLOAD_GEOLOC_TIMEOUT_SIZE_V2)
        json_ul_data = result[0]
        log_data = result[1]
        LOG_print("[METEOFOX] * Geoloc timeout V2 * site=" + __METEOFOX_get_site(sigfox_ep_id) + " " + log_data)
    # Geolocation timeout frame V3.
    elif (len(ul_payload) == (2 * COMMON_UL_PAYLOAD_GEOLOC_TIMEOUT_SIZE_V3)):
        # Create JSON object.
        result = COMMON_create_json_geoloc_timeout_data(timestamp, ul_payload, COMMON_UL_PAYLOAD_GEOLOC_TIMEOUT_SIZE_V3)
        json_ul_data = result[0]
        log_data = result[1]
        LOG_print("[METEOFOX] * Geoloc timeout V3 * site=" + __METEOFOX_get_site(sigfox_ep_id) + " " + log_data)
    # Error stack frame.
    elif (len(ul_payload) == (2 * __METEOFOX_UL_PAYLOAD_ERROR_STACK_SIZE)):
        # Create JSON object.
        result = COMMON_create_json_error_stack_data(timestamp, ul_payload, (__METEOFOX_UL_PAYLOAD_ERROR_STACK_SIZE // 2))
        json_ul_data = result[0]
        log_data = result[1]
        LOG_print("[METEOFOX] * Error stack * site=" + __METEOFOX_get_site(sigfox_ep_id) + " " + log_data)
    # Monitoring frame.
    elif (len(ul_payload) == (2 * __METEOFOX_UL_PAYLOAD_MONITORING_SIZE)):
        # Parse fields.
        tmcu_degrees = COMMON_one_complement_to_value(int(ul_payload[0:2], 16), 7) if (int(ul_payload[0:2], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
        tpcb_degrees = COMMON_one_complement_to_value(int(ul_payload[2:4], 16), 7) if (int(ul_payload[2:4], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
        hpcb_percent = int(ul_payload[4:6], 16) if (int(ul_payload[4:6], 16) != COMMON_ERROR_VALUE_HUMIDITY) else COMMON_ERROR_DATA
        vsrc_mv = int(ul_payload[6:10], 16) if (int(ul_payload[6:10], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
        vcap_mv = int(ul_payload[10:13], 16) if (int(ul_payload[10:13], 16) != COMMON_ERROR_VALUE_ANALOG_12BITS) else COMMON_ERROR_DATA
        vmcu_mv = int(ul_payload[13:16], 16) if (int(ul_payload[13:16], 16) != COMMON_ERROR_VALUE_ANALOG_12BITS) else COMMON_ERROR_DATA
        status = int(ul_payload[16:18], 16)
        # Create JSON object.
        json_ul_data = [
        {
            "time": timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
            "fields": {
                INFLUX_DB_FIELD_STATUS: status,
                INFLUX_DB_FIELD_TIME_LAST_MONITORING_DATA: timestamp
            },
        },
        {
            "time": timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_METADATA,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION: timestamp
            },
        }]
        # Add valid fields to JSON.
        if (tmcu_degrees != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
        if (tpcb_degrees != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_TPCB] = tpcb_degrees
        if (hpcb_percent != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_HPCB] = hpcb_percent
        if (vsrc_mv != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_VSRC] = vsrc_mv
        if (vcap_mv != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_VCAP] = vcap_mv
        if (vmcu_mv != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
        LOG_print("[METEOFOX] * Monitoring data * site=" + __METEOFOX_get_site(sigfox_ep_id) +
                  " tmcu=" + str(tmcu_degrees) + "dC tpcb=" + str(tpcb_degrees) + "dC hpcb=" + str(hpcb_percent) +
                  "% vsrc=" + str(vsrc_mv) + "mV vcap=" + str(vcap_mv) + "mV vmcu=" + str(vmcu_mv) + "mV status=" + hex(status))
    # IM weather data frame.
    elif (len(ul_payload) == (2 * __METEOFOX_UL_PAYLOAD_WEATHER_IM_SIZE)):
        # Parse fields.
        tamb_degrees = COMMON_one_complement_to_value(int(ul_payload[0:2], 16), 7) if (int(ul_payload[0:2], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
        hamb_percent = int(ul_payload[2:4], 16) if (int(ul_payload[2:4], 16) != COMMON_ERROR_VALUE_HUMIDITY) else COMMON_ERROR_DATA
        light_percent = int(ul_payload[4:6], 16) if (int(ul_payload[4:6], 16) != COMMON_ERROR_VALUE_LIGHT) else COMMON_ERROR_DATA
        uv_index = int(ul_payload[6:8], 16) if (int(ul_payload[6:8], 16) != COMMON_ERROR_VALUE_UV_INDEX) else COMMON_ERROR_DATA
        patm_abs_hpa = (int(ul_payload[8:12], 16) / 10.0) if (int(ul_payload[8:12], 16) != COMMON_ERROR_VALUE_PRESSURE) else COMMON_ERROR_DATA
        # Compute sea level pressure.
        patm_sea_hpa = COMMON_ERROR_DATA
        try:
            altitude_query = "SELECT last(altitude) FROM geoloc WHERE sigfox_ep_id='" + sigfox_ep_id + "'"
            altitude_query_result = INFLUX_DB_read_data(INFLUX_DB_DATABASE_METEOFOX, altitude_query)
            altitude_points = altitude_query_result.get_points()
            for point in altitude_points:
                altitude = int(point["last"])
            patm_sea_hpa = __METEOFOX_compute_sea_level_pressure(patm_abs_hpa, altitude, tamb_degrees)
        except:
            # Altitude not available.
            patm_sea_hpa = COMMON_ERROR_DATA
        # Create JSON object.
        json_ul_data = [
        {
            "time": timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_WEATHER,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_WEATHER_DATA: timestamp
            },
        },
        {
            "time": timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_METADATA,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION: timestamp
            },
        }]
        if (tamb_degrees != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_TAMB] = tamb_degrees
        if (hamb_percent != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_HAMB] = hamb_percent
        if (light_percent != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_LIGHT] = light_percent
        if (uv_index != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_UV_INDEX] = uv_index
        if (patm_abs_hpa != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_PATM_ABS] = patm_abs_hpa
        if (patm_sea_hpa != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_PATM_SEA] = patm_sea_hpa
        LOG_print("[METEOFOX] * IM weather data * site=" + __METEOFOX_get_site(sigfox_ep_id) +
                  " tamb=" + str(tamb_degrees) + "dC hamb=" + str(hamb_percent) + "% light=" + str(light_percent) + "% uv_index=" + str(uv_index) +
                  " patm_abs=" + str(patm_abs_hpa) + "hPa patm_sea=" + str(patm_sea_hpa) + "hpa")
    # CM weather data frame.
    elif (len(ul_payload) == (2 * __METEOFOX_UL_PAYLOAD_WEATHER_CM_SIZE)):
        # Parse fields.
        tamb_degrees = COMMON_one_complement_to_value(int(ul_payload[0:2], 16), 7) if (int(ul_payload[0:2], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
        hamb_percent = int(ul_payload[2:4], 16) if (int(ul_payload[2:4], 16) != COMMON_ERROR_VALUE_HUMIDITY) else COMMON_ERROR_DATA
        light_percent = int(ul_payload[4:6], 16) if (int(ul_payload[4:6], 16) != COMMON_ERROR_VALUE_LIGHT) else COMMON_ERROR_DATA
        uv_index = int(ul_payload[6:8], 16) if (int(ul_payload[6:8], 16) != COMMON_ERROR_VALUE_UV_INDEX) else COMMON_ERROR_DATA
        patm_abs_hpa = (int(ul_payload[8:12], 16) / 10.0) if (int(ul_payload[8:12], 16) != COMMON_ERROR_VALUE_PRESSURE) else COMMON_ERROR_DATA
        wind_speed_average_kmh = int(ul_payload[12:14], 16) if (int(ul_payload[12:14], 16) != COMMON_ERROR_VALUE_WIND) else COMMON_ERROR_DATA
        wind_speed_peak_kmh = int(ul_payload[14:16], 16) if (int(ul_payload[14:16], 16) != COMMON_ERROR_VALUE_WIND) else COMMON_ERROR_DATA
        wind_direction_average_degrees = (int(ul_payload[16:18], 16) * 2) if (int(ul_payload[16:18], 16) != COMMON_ERROR_VALUE_WIND) else COMMON_ERROR_DATA
        rain_mm = COMMON_ERROR_DATA
        rain_byte = int(ul_payload[18:20], 16)
        # Compute rainfall.
        if (rain_byte != COMMON_ERROR_VALUE_RAIN):
            # Compute rainfall.
            try:
                query = "SELECT last(version_major) FROM metadata WHERE sigfox_ep_id='" + sigfox_ep_id + "'"
                query_result = INFLUX_DB_read_data(INFLUX_DB_DATABASE_METEOFOX, query)
                for point in query_result.get_points():
                    version_major = int(point["last"])
                query = "SELECT last(version_minor) FROM metadata WHERE sigfox_ep_id='" + sigfox_ep_id + "'"
                query_result = INFLUX_DB_read_data(INFLUX_DB_DATABASE_METEOFOX, query)
                for point in query_result.get_points():
                    version_minor = int(point["last"])
                # Check version.
                if ((version_major > 6) or ((version_major >= 6) and (version_minor >= 5))):
                    # Format with dynamic unit.
                    unit = (rain_byte >> 7)
                    if (unit == 0):
                        rain_mm = ((rain_byte & 0x7F) / 10.0)
                    else:
                        rain_mm = (rain_byte & 0x7F)
                else:
                    # Format in mm.
                    rain_mm = rain_byte
            except:
                # Software version not available.
                rain_mm = COMMON_ERROR_DATA
        # Compute sea level pressure.
        patm_sea_hpa = COMMON_ERROR_DATA
        try:
            altitude_query = "SELECT last(altitude) FROM geoloc WHERE sigfox_ep_id='" + sigfox_ep_id + "'"
            altitude_query_result = INFLUX_DB_read_data(INFLUX_DB_DATABASE_METEOFOX, altitude_query)
            altitude_points = altitude_query_result.get_points()
            for point in altitude_points:
                altitude = int(point["last"])
            patm_sea_hpa = __METEOFOX_compute_sea_level_pressure(patm_abs_hpa, altitude, tamb_degrees)
        except:
            # Altitude not available.
            patm_sea_hpa = COMMON_ERROR_DATA
        # Create JSON object.
        json_ul_data = [
        {
            "time": timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_WEATHER,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_WEATHER_DATA: timestamp
            },
        },
        {
            "time": timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_METADATA,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION: timestamp
            },
        }]
        if (tamb_degrees != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_TAMB] = tamb_degrees
        if (hamb_percent != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_HAMB] = hamb_percent
        if (light_percent != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_LIGHT] = light_percent
        if (uv_index != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_UV_INDEX] = uv_index
        if (patm_abs_hpa != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_PATM_ABS] = patm_abs_hpa
        if (patm_sea_hpa != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_PATM_SEA] = patm_sea_hpa
        if (wind_speed_average_kmh != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_WSPD_AVRG] = wind_speed_average_kmh
        if (wind_speed_peak_kmh != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_WSPD_PEAK] = wind_speed_peak_kmh
        if (wind_direction_average_degrees != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_WDIR_AVRG] = wind_direction_average_degrees
        if (rain_mm != COMMON_ERROR_DATA):
            json_ul_data[0]["fields"][INFLUX_DB_FIELD_RAIN] = rain_mm
        LOG_print("[METEOFOX] * CM weather data * site=" + __METEOFOX_get_site(sigfox_ep_id) +
                  " tamb=" + str(tamb_degrees) + "dC, hamb=" + str(hamb_percent) + "% light=" + str(light_percent) +
                  "% uv_index=" + str(uv_index) + " patm_abs=" + str(patm_abs_hpa) + "hPa patm_sea=" + str(patm_sea_hpa) +
                  "hPa wind_speed_average=" + str(wind_speed_average_kmh) + "km/h wind_speed_peak=" + str(wind_speed_peak_kmh) +
                  "km/h, wind_direction_average=" + str(wind_direction_average_degrees) + "d, rain=" + str(rain_mm) + "mm")
    else:
        LOG_print("[METEOFOX] * Invalid UL payload")
    return json_ul_data

# Returns the default downlink payload to sent back to the device.
def METEOFOX_get_default_dl_payload(sigfox_ep_id):
    # Local variables.
    dl_payload = []
    if (sigfox_ep_id in METEOFOX_EP_ID_LIST):
        dl_payload = "0000000000000000"
    return dl_payload
