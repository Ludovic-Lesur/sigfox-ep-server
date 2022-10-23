from __future__ import print_function
import math

from common import *
from influx_db import *
from log import *

### LOCAL MACROS ###

# MeteoFox tags.
__METEOFOX_SITE = ["Proto_HW1.0", "Proto_HW2.0", "Le_Vigan", "Prat_Albis", "Eaunes", "Labege", "Le_Lien", "Kourou"]
# Sigfox frame lengths.
__METEOFOX_MONITORING_DATA_LENGTH_BYTES = 9
__METEOFOX_IM_WEATHER_DATA_LENGTH_BYTES = 6
__METEOFOX_CM_WEATHER_DATA_LENGTH_BYTES = 10
__METEOFOX_ERROR_STACK_DATA_LENGTH_BYTES = 12

### PUBLIC MACROS ###

# MeteoFox EP-IDs.
METEOFOX_EP_ID = ["53B5", "5436", "546C", "5477", "5497", "549D", "54B6", "54E4"]

### LOCAL FUNCTIONS ###

# Function performing Sigfox ID to MeteoFox site conversion.
def __METEOFOX_get_site(sigfox_ep_id) :
    # Default is unknown.
    site = "unknown"
    if (sigfox_ep_id in METEOFOX_EP_ID):
        site = __METEOFOX_SITE[METEOFOX_EP_ID.index(sigfox_ep_id)]
    return site

# Function adding the specific MeteoFox tags.
def __METEOFOX_add_tags(json_body, sigfox_ep_id) :
    for idx in range(len(json_body)) :
        json_body[idx]["tags"] = {
            INFLUX_DB_TAG_SIGFOX_EP_ID : sigfox_ep_id,
            INFLUX_DB_TAG_SITE : __METEOFOX_get_site(sigfox_ep_id)
        }

# Function to compute sea-level pressure (barometric formula).
def __METEOFOX_compute_sea_level_pressure(absolute_pressure, altitude, temperature) :
    # a^(x) = exp(x*ln(a))
    temperature_kelvin = temperature + 273.15
    return (absolute_pressure * math.exp(-5.255 * math.log((temperature_kelvin) / (temperature_kelvin + 0.0065 * altitude))))

### PUBLIC FUNCTIONS ###

# Function for parsing MeteoFox device payload and fill database.
def METEOFOX_fill_data_base(timestamp, sigfox_ep_id, data) :
    # Init JSON object.
    json_body = []
    # OOB frame (only for SW version older than 1.2.42).
    if (data == COMMON_OOB_DATA) :
        # Create JSON object.
        json_body = [
        {
            "time" : timestamp,
            "measurement" : INFLUX_DB_MEASUREMENT_GLOBAL,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_STARTUP : timestamp,
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
            }
        }]
        LOG_print_timestamp("[METEOFOX] * Startup * site=" + __METEOFOX_get_site(sigfox_ep_id))
    # Startup frame.
    if (len(data) == (2 * COMMON_STARTUP_DATA_LENGTH_BYTES)) :
        # Create JSON object.
        result = COMMON_create_json_startup_data(timestamp, data)
        json_body = result[0]
        log_data = result[1]
        LOG_print_timestamp("[METEOFOX] * Startup data * site=" + __METEOFOX_get_site(sigfox_ep_id) + " " + log_data)
    # Geolocation frame.
    if (len(data) == (2 * COMMON_GEOLOC_DATA_LENGTH_BYTES)) :
        # Create JSON object.
        result = COMMON_create_json_geoloc_data(timestamp, data)
        json_body = result[0]
        log_data = result[1]
        LOG_print_timestamp("[METEOFOX] * Geoloc data * site=" + __METEOFOX_get_site(sigfox_ep_id) + " " + log_data)
    # Geolocation timeout frame.
    if (len(data) == (2 * COMMON_GEOLOC_TIMEOUT_DATA_LENGTH_BYTES)) :
        # Create JSON object.
        result = COMMON_create_json_geoloc_timeout_data(timestamp, data)
        json_body = result[0]
        log_data = result[1]
        LOG_print_timestamp("[METEOFOX] * Geoloc timeout * site=" + __METEOFOX_get_site(sigfox_ep_id) + " " + log_data)
    # Error stack frame.
    if (len(data) == (2 * __METEOFOX_ERROR_STACK_DATA_LENGTH_BYTES)) :
        # Create JSON object.
        result = COMMON_create_json_error_stack_data(timestamp, data, (__METEOFOX_ERROR_STACK_DATA_LENGTH_BYTES / 2))
        json_body = result[0]
        log_data = result[1]
        LOG_print_timestamp("[METEOFOX] * Error stack * site=" + __METEOFOX_get_site(sigfox_ep_id) + " " + log_data)
    # Monitoring frame.
    if (len(data) == (2 * __METEOFOX_MONITORING_DATA_LENGTH_BYTES)) :
        # Parse fields.
        tmcu_degrees = COMMON_one_complement_to_value(int(data[0:2], 16), 7) if (int(data[0:2], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
        tpcb_degrees = COMMON_one_complement_to_value(int(data[2:4], 16), 7) if (int(data[2:4], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
        hpcb_percent = int(data[4:6], 16) if (int(data[4:6], 16) != COMMON_ERROR_VALUE_HUMIDITY) else COMMON_ERROR_DATA
        vsrc_mv = int(data[6:10], 16) if (int(data[6:10], 16) != COMMON_ERROR_VALUE_ANALOG_16BITS) else COMMON_ERROR_DATA
        vcap_mv = int(data[10:13], 16) if (int(data[10:13], 16) != COMMON_ERROR_VALUE_ANALOG_12BITS) else COMMON_ERROR_DATA
        vmcu_mv = int(data[13:16], 16) if (int(data[13:16], 16) != COMMON_ERROR_VALUE_ANALOG_12BITS) else COMMON_ERROR_DATA
        status = int(data[16:18], 16)
        # Create JSON object.
        json_body = [
        {
            "time" : timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
            "fields": {
                INFLUX_DB_FIELD_STATUS : status,
                INFLUX_DB_FIELD_TIME_LAST_MONITORING_DATA : timestamp
            },
        },
        {
            "time" : timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
            },
        }]
        # Add valid fields to JSON.
        if (tmcu_degrees != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_TMCU] = tmcu_degrees
        if (tpcb_degrees != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_TPCB] = tpcb_degrees
        if (hpcb_percent != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_HPCB] = hpcb_percent
        if (vsrc_mv != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_VSRC] = vsrc_mv
        if (vcap_mv != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_VCAP] = vcap_mv
        if (vmcu_mv != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_VMCU] = vmcu_mv
        LOG_print_timestamp("[METEOFOX] * Monitoring data * site=" + __METEOFOX_get_site(sigfox_ep_id) + " tmcu=" + str(tmcu_degrees) + "dC tpcb=" + str(tpcb_degrees) + "dC hpcb=" + str(hpcb_percent) + "% vsrc=" + str(vsrc_mv) + "mV vcap=" + str(vcap_mv) + "mV vmcu=" + str(vmcu_mv) + "mV status=" + hex(status))
    # IM weather data frame.
    if (len(data) == (2 * __METEOFOX_IM_WEATHER_DATA_LENGTH_BYTES)) :
        # Parse fields.
        tamb_degrees = COMMON_one_complement_to_value(int(data[0:2], 16), 7) if (int(data[0:2], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
        hamb_percent = int(data[2:4], 16) if (int(data[2:4], 16) != COMMON_ERROR_VALUE_HUMIDITY) else COMMON_ERROR_DATA
        light_percent = int(data[4:6], 16) if (int(data[4:6], 16) != COMMON_ERROR_VALUE_LIGHT) else COMMON_ERROR_DATA
        uv_index = int(data[6:8], 16) if (int(data[6:8], 16) != COMMON_ERROR_VALUE_UV_INDEX) else COMMON_ERROR_DATA
        patm_abs_hpa = (int(data[8:12], 16) / 10.0) if (int(data[8:12], 16) != COMMON_ERROR_VALUE_PRESSURE) else COMMON_ERROR_DATA
        # Compute sea level pressure.
        patm_sea_hpa = COMMON_ERROR_DATA
        try :
            altitude_query = "SELECT last(altitude) FROM geoloc WHERE sigfox_sigfox_ep_id='" + sigfox_ep_id + "'"
            altitude_query_result = INFLUX_DB_read_data(INFLUX_DB_DATABASE_METEOFOX, altitude_query)
            altitude_points = altitude_query_result.get_points()
            for point in altitude_points :
                altitude = int(point["last"])
            patm_sea_hpa = __METEOFOX_compute_sea_level_pressure(patm_abs_hpa, altitude, tamb_degrees)
        except:
            # Altitude not available.
            patm_sea_hpa = COMMON_ERROR_DATA
        # Create JSON object.
        json_body = [
        {
            "time" : timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_WEATHER,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_WEATHER_DATA : timestamp
            },
        },
        {
            "time" : timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
            },
        }]
        if (tamb_degrees != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_TAMB] = tamb_degrees
        if (hamb_percent != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_HAMB] = hamb_percent
        if (light_percent != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_LIGHT] = light_percent
        if (uv_index != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_UV_INDEX] = uv_index
        if (patm_abs_hpa != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_PATM_ABS] = patm_abs_hpa
        if (patm_sea_hpa != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_PATM_SEA] = patm_sea_hpa
        LOG_print_timestamp("[METEOFOX] * IM weather data * site=" + __METEOFOX_get_site(sigfox_ep_id) + " tamb=" + str(tamb_degrees) + "dC hamb=" + str(hamb_percent) + "% light=" + str(light_percent) + "% uv_index=" + str(uv_index) + " patm_abs=" + str(patm_abs_hpa) + "hPa patm_sea=" + str(patm_sea_hpa) + "hpa")
    # CM weather data frame.
    if (len(data) == (2 * __METEOFOX_CM_WEATHER_DATA_LENGTH_BYTES)) :
        # Parse fields.
        tamb_degrees = COMMON_one_complement_to_value(int(data[0:2], 16), 7) if (int(data[0:2], 16) != COMMON_ERROR_VALUE_TEMPERATURE) else COMMON_ERROR_DATA
        hamb_percent = int(data[2:4], 16) if (int(data[2:4], 16) != COMMON_ERROR_VALUE_HUMIDITY) else COMMON_ERROR_DATA
        light_percent = int(data[4:6], 16) if (int(data[4:6], 16) != COMMON_ERROR_VALUE_LIGHT) else COMMON_ERROR_DATA
        uv_index = int(data[6:8], 16) if (int(data[6:8], 16) != COMMON_ERROR_VALUE_UV_INDEX) else COMMON_ERROR_DATA
        patm_abs_hpa = (int(data[8:12], 16) / 10.0) if (int(data[8:12], 16) != COMMON_ERROR_VALUE_PRESSURE) else COMMON_ERROR_DATA
        wind_speed_average_kmh = int(data[12:14], 16) if (int(data[12:14], 16) != COMMON_ERROR_VALUE_WIND) else COMMON_ERROR_DATA
        wind_speed_peak_kmh = int(data[14:16], 16) if (int(data[14:16], 16) != COMMON_ERROR_VALUE_WIND) else COMMON_ERROR_DATA
        wind_direction_average_degrees = (int(data[16:18], 16) * 2) if (int(data[16:18], 16) != COMMON_ERROR_VALUE_WIND) else COMMON_ERROR_DATA
        rain_mm = int(data[18:20], 16) if (int(data[18:20], 16) != COMMON_ERROR_VALUE_WIND) else COMMON_ERROR_DATA
        # Compute sea level pressure.
        patm_sea_hpa = COMMON_ERROR_DATA
        try :
            altitude_query = "SELECT last(altitude) FROM geoloc WHERE sigfox_sigfox_ep_id='" + sigfox_ep_id + "'"
            altitude_query_result = INFLUX_DB_read_data(INFLUX_DB_DATABASE_METEOFOX, altitude_query)
            altitude_points = altitude_query_result.get_points()
            for point in altitude_points :
                altitude = int(point["last"])
            patm_sea_hpa = __METEOFOX_compute_sea_level_pressure(patm_abs_hpa, altitude, tamb_degrees)
        except:
            # Altitude not available.
            patm_sea_hpa = COMMON_ERROR_DATA
        # Create JSON object.
        json_body = [
        {
            "time" : timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_WEATHER,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_WEATHER_DATA : timestamp
            },
        },
        {
            "time" : timestamp,
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "fields": {
                INFLUX_DB_FIELD_TIME_LAST_COMMUNICATION : timestamp
            },
        }]
        if (tamb_degrees != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_TAMB] = tamb_degrees
        if (hamb_percent != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_HAMB] = hamb_percent
        if (light_percent != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_LIGHT] = light_percent
        if (uv_index != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_UV_INDEX] = uv_index
        if (patm_abs_hpa != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_PATM_ABS] = patm_abs_hpa
        if (patm_sea_hpa != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_PATM_SEA] = patm_sea_hpa
        if (wind_speed_average_kmh != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_WSPD_AVRG] = wind_speed_average_kmh
        if (wind_speed_peak_kmh != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_WSPD_PEAK] = wind_speed_peak_kmh
        if (wind_direction_average_degrees != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_WDIR_AVRG] = wind_direction_average_degrees
        if (rain_mm != COMMON_ERROR_DATA) :
            json_body[0]["fields"][INFLUX_DB_FIELD_RAIN] = rain_mm
        LOG_print_timestamp("[METEOFOX] * CM weather data * site=" + __METEOFOX_get_site(sigfox_ep_id) + " tamb=" + str(tamb_degrees) + "dC, hamb=" + str(hamb_percent) + "% light=" + str(light_percent) + "% uv_index=" + str(uv_index) + " patm_abs=" + str(patm_abs_hpa) + "hPa patm_sea=" + str(patm_sea_hpa) + "hPa wind_speed_average=" + str(wind_speed_average_kmh) + "km/h wind_speed_peak=" + str(wind_speed_peak_kmh) + "km/h, wind_direction_average=" + str(wind_direction_average_degrees) + "d, rain=" + str(rain_mm) + "mm")
    # Fill data base.
    if (len(json_body) > 0) :
        __METEOFOX_add_tags(json_body, sigfox_ep_id)
        INFLUX_DB_write_data(INFLUX_DB_DATABASE_METEOFOX, json_body)
    else :
        LOG_print_timestamp("[METEOFOX] * Invalid frame")