from __future__ import print_function
import math

from influx_db import *
from log import *

### MACROS ###

# Devices ID and associated informations.
MFX_SIGFOX_DEVICES_ID = ["53B5", "5436", "546C", "5477", "5497", "549D", "54B6", "54E4"]
MFX_SIGFOX_DEVICES_SITE = ["INSA Toulouse", "Proto V2", "Le Vigan", "Prat Albis", "Eaunes", "Labege", "Le Lien", "Concarneau"]

# Sigfox frame lengths.
MFX_SIGFOX_OOB_DATA = "OOB"
MFX_SIGFOX_STARTUP_FRAME_LENGTH_BYTES = 8
MFX_SIGFOX_MONITORING_FRAME_LENGTH_BYTES = 9
MFX_SIGFOX_INTERMITTENT_WEATHER_DATA_FRAME_LENGTH_BYTES = 6
MFX_SIGFOX_CONTINUOUS_WEATHER_DATA_FRAME_LENGTH_BYTES = 10
MFX_SIGFOX_GEOLOCATION_FRAME_LENGTH_BYTES = 11
MFX_SIGFOX_GEOLOCATION_TIMEOUT_FRAME_LENGTH_BYTES = 1
MFX_SIGFOX_ERROR_STACK_FRAME_LENGTH_BYTES = 12

# Error values.
MFX_TEMPERATURE_ERROR = 0x7F
MFX_HUMIDITY_ERROR = 0xFF
MFX_UV_INDEX_ERROR = 0xFF
MFX_PRESSURE_ERROR = 0xFFFF
MFX_WIND_ERROR = 0xFF

### FUNCTIONS ###

# Function performing Sigfox ID to MeteoFox site conversion.
def MFX_GetSite(device_id):
    # Default is unknown.
    meteofox_site = "Unknown site (" + str(device_id) + ")"
    if (device_id in MFX_SIGFOX_DEVICES_ID):
        meteofox_site = MFX_SIGFOX_DEVICES_SITE[MFX_SIGFOX_DEVICES_ID.index(device_id)]
    return meteofox_site

# Function to compute sea-level pressure (barometric formula).
def MFX_GetSeaLevelPressure(absolute_pressure, altitude, temperature):
    # a^(x) = exp(x*ln(a))
    temperature_kelvin = temperature + 273.15
    return (absolute_pressure * math.exp(-5.255 * math.log((temperature_kelvin) / (temperature_kelvin + 0.0065 * altitude))))

# Function for parsing MeteoFox device payload and fill database.
def MFX_FillDataBase(timestamp, device_id, data):
    # Format parameters.
    influxdb_device_id = device_id.upper()
    influxdb_timestamp = int(timestamp)
    # OOB frame.
    if data == MFX_SIGFOX_OOB_DATA:
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LAST_STARTUP_TIMESTAMP : influxdb_timestamp,
                INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        }]
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "MFX ID=" + str(device_id) + " * Start up.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_MFX_DATABASE_NAME, json_body)
    # Startup frame.
    if len(data) == (2 * MFX_SIGFOX_STARTUP_FRAME_LENGTH_BYTES):
        # Parse fields.
        reset_byte = int(data[0:2], 16)
        major_version = int(data[2:4], 16)
        minor_version = int(data[4:6], 16)
        commit_index = int(data[6:8], 16)
        commit_id = int(data[8:15], 16)
        dirty_flag = int(data[15:16], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp,
                INFLUX_DB_FIELD_LAST_STARTUP_TIMESTAMP : influxdb_timestamp,
                INFLUX_DB_FIELD_RESET_BYTE : reset_byte,
                INFLUX_DB_FIELD_VERSION_MAJOR : major_version,
                INFLUX_DB_FIELD_VERSION_MINOR : minor_version,
                INFLUX_DB_FIELD_VERSION_COMMIT_INDEX : commit_index,
                INFLUX_DB_FIELD_VERSION_COMMIT_ID : commit_id,
                INFLUX_DB_FIELD_VERSION_DIRTY_FLAG : dirty_flag
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        }]
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "MFX ID=" + str(device_id) + " * Startup data * Reset=" + hex(reset_byte) + " * Version=" + str(major_version) + "." + str(minor_version) + "." + str(commit_index) + " (" + hex(commit_id) + ", " + str(dirty_flag) + ")")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_MFX_DATABASE_NAME, json_body)
    # Monitoring frame.
    if len(data) == (2 * MFX_SIGFOX_MONITORING_FRAME_LENGTH_BYTES):
        # Parse fields.
        mcu_temperature_raw = int(data[0:2], 16)
        mcu_temperature = mcu_temperature_raw & 0x7F
        if ((mcu_temperature_raw & 0x80) != 0):
            mcu_temperature = (-1) * mcu_temperature
        solar_cell_voltage = int(data[6:10], 16)
        supercap_voltage = int(data[10:13], 16)
        mcu_voltage = int(data[13:16], 16)
        status_byte = int(data[16:18], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUX_DB_MEASUREMENT_MONITORING,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_MCU_TEMPERATURE : mcu_temperature,
                INFLUX_DB_FIELD_SOLAR_CELL_VOLTAGE : solar_cell_voltage,
                INFLUX_DB_FIELD_SUPERCAP_VOLTAGE : supercap_voltage,
                INFLUX_DB_FIELD_MCU_VOLTAGE : mcu_voltage,
                INFLUX_DB_FIELD_STATUS_BYTE : status_byte,
                INFLUX_DB_FIELD_LAST_MONITORING_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        },
        {
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        }]
        # Manage error values.
        pcb_temperature = "error"
        if (int(data[2:4], 16) != MFX_TEMPERATURE_ERROR):
            pcb_temperature_raw = int(data[2:4], 16)
            pcb_temperature = pcb_temperature_raw & 0x7F
            if ((pcb_temperature_raw & 0x80) != 0):
                pcb_temperature = (-1) * pcb_temperature
            json_body[0]["fields"][INFLUX_DB_FIELD_PCB_TEMPERATURE] = pcb_temperature
        pcb_humidity = "error"
        if (int(data[4:6], 16) != MFX_HUMIDITY_ERROR):
            pcb_humidity = int(data[4:6], 16)
            json_body[0]["fields"][INFLUX_DB_FIELD_PCB_HUMIDITY] = pcb_humidity
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "MFX ID=" + str(device_id) + " * Monitoring data * Tmcu=" + str(mcu_temperature) + "dC, Tpcb=" + str(pcb_temperature) + "dC, Hpcb=" + str(pcb_humidity) + "%, Vsrc=" + str(solar_cell_voltage) + "mV, Vcap=" + str(supercap_voltage) + "mV, Vmcu=" + str(mcu_voltage) + "mV, Status=" + str(status_byte) + ".")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_MFX_DATABASE_NAME, json_body)
    # Intermittent weather data frame.
    if len(data) == (2 * MFX_SIGFOX_INTERMITTENT_WEATHER_DATA_FRAME_LENGTH_BYTES):
        # Parse fields.
        light = int(data[4:6], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUX_DB_MEASUREMENT_WEATHER,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LIGHT : light,
                INFLUX_DB_FIELD_LAST_WEATHER_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        },
        {
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        }]
        # Manage error values.
        temperature = "error"
        if (int(data[0:2], 16) != MFX_TEMPERATURE_ERROR):
            temperature_raw = int(data[0:2], 16)
            temperature = temperature_raw & 0x7F
            if ((temperature_raw & 0x80) != 0):
                temperature = (-1) * temperature
            json_body[0]["fields"][INFLUX_DB_FIELD_TEMPERATURE] = temperature
        humidity = "error"
        if (int(data[2:4], 16) != MFX_HUMIDITY_ERROR):
            humidity = int(data[2:4], 16)
            json_body[0]["fields"][INFLUX_DB_FIELD_HUMIDITY] = humidity
        uv_index = "error"
        if (int(data[6:8], 16) != MFX_UV_INDEX_ERROR):
            uv_index = int(data[6:8], 16)
            json_body[0]["fields"][INFLUX_DB_FIELD_UV_INDEX] = uv_index
        absolute_pressure = "error"
        sea_level_pressure = "error"
        if (int(data[8:12], 16) != MFX_PRESSURE_ERROR):
            absolute_pressure = (int(data[8:12], 16) / 10.0)
            json_body[0]["fields"][INFLUX_DB_FIELD_ABSOLUTE_PRESSURE] = absolute_pressure
            if (int(data[0:2], 16) != MFX_TEMPERATURE_ERROR):
                try:
                    altitude_query = "SELECT last(altitude) FROM geoloc WHERE sigfox_device_id='" + influxdb_device_id + "'"
                    altitude_query_result = INFLUX_DB_ReadData(INFLUX_DB_MFX_DATABASE_NAME, altitude_query)
                    altitude_points = altitude_query_result.get_points()
                    for point in altitude_points:
                        altitude = int(point["last"])
                    sea_level_pressure = MFX_GetSeaLevelPressure(absolute_pressure, altitude, temperature)
                    json_body[0]["fields"][INFLUX_DB_FIELD_SEA_LEVEL_PRESSURE] = sea_level_pressure
                except:
                    # Altitude is not available yet for this device.
                    sea_level_pressure = "error"
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "MFX ID=" + str(device_id) + " * Weather data * T=" + str(temperature) + "dC, H=" + str(humidity) + "%, L=" + str(light) + "%, UV=" + str(uv_index) + ", Pabs=" + str(absolute_pressure) + "hPa, Psea=" + str(sea_level_pressure) + "hpa.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_MFX_DATABASE_NAME, json_body)
    # Continuous weather data frame.
    if len(data) == (2 * MFX_SIGFOX_CONTINUOUS_WEATHER_DATA_FRAME_LENGTH_BYTES):
        # Parse fields.
        light = int(data[4:6], 16)
        average_wind_speed = int(data[12:14], 16)
        peak_wind_speed = int(data[14:16], 16)
        rain = int(data[18:20], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUX_DB_MEASUREMENT_WEATHER,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LIGHT : light,
                INFLUX_DB_FIELD_AVERAGE_WIND_SPEED : average_wind_speed,
                INFLUX_DB_FIELD_PEAK_WIND_SPEED : peak_wind_speed,
                INFLUX_DB_FIELD_RAIN : rain,
                INFLUX_DB_FIELD_LAST_WEATHER_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        },
        {
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        }]
        # Manage error values.
        temperature = "error"
        if (int(data[0:2], 16) != MFX_TEMPERATURE_ERROR):
            temperature_raw = int(data[0:2], 16)
            temperature = temperature_raw & 0x7F
            if ((temperature_raw & 0x80) != 0):
                temperature = (-1) * temperature
            json_body[0]["fields"][INFLUX_DB_FIELD_TEMPERATURE] = temperature
        humidity = "error"
        if (int(data[2:4], 16) != MFX_HUMIDITY_ERROR):
            humidity = int(data[2:4], 16)
            json_body[0]["fields"][INFLUX_DB_FIELD_HUMIDITY] = humidity
        uv_index = "error"
        if (int(data[6:8], 16) != MFX_UV_INDEX_ERROR):
            uv_index = int(data[6:8], 16)
            json_body[0]["fields"][INFLUX_DB_FIELD_UV_INDEX] = uv_index
        absolute_pressure = "error"
        sea_level_pressure = "error"
        if (int(data[8:12], 16) != MFX_PRESSURE_ERROR):
            absolute_pressure = (int(data[8:12], 16) / 10.0)
            json_body[0]["fields"][INFLUX_DB_FIELD_ABSOLUTE_PRESSURE] = absolute_pressure
            if (int(data[0:2], 16) != MFX_TEMPERATURE_ERROR):
                try:
                    altitude_query = "SELECT last(altitude) FROM geoloc WHERE sigfox_device_id='" + influxdb_device_id + "'"
                    altitude_query_result = INFLUX_DB_ReadData(INFLUX_DB_MFX_DATABASE_NAME, altitude_query)
                    altitude_points = altitude_query_result.get_points()
                    for point in altitude_points:
                        altitude = int(point["last"])
                    sea_level_pressure = MFX_GetSeaLevelPressure(absolute_pressure, altitude, temperature)
                    json_body[0]["fields"][INFLUX_DB_FIELD_SEA_LEVEL_PRESSURE] = sea_level_pressure
                except:
                    # Altitude is not available yet for this device.
                    sea_level_pressure = "error"
        average_wind_direction = "error"
        if (int(data[16:18], 16) != MFX_WIND_ERROR):
            average_wind_direction = 2 * int(data[16:18], 16)
            json_body[0]["fields"][INFLUX_DB_FIELD_AVERAGE_WIND_DIRECTION] = average_wind_direction
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "MFX ID=" + str(device_id) + " * Weather data * T=" + str(temperature) + "C, H=" + str(humidity) + "%, L=" + str(light) + "%, UV=" + str(uv_index) + ", Pabs=" + str(absolute_pressure) + "hPa, Psea=" + str(sea_level_pressure) + "hPa, Wavg=" + str(average_wind_speed) + "km/h, Wpeak=" + str(peak_wind_speed) + "km/h, Wdir=" + str(average_wind_direction) + "d, R=" + str(rain) + "mm.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_MFX_DATABASE_NAME, json_body)
    # Geolocation frame.
    if len(data) == (2 * MFX_SIGFOX_GEOLOCATION_FRAME_LENGTH_BYTES):
        # Parse fields.
        latitude_degrees = int(data[0:2], 16)
        latitude_minutes = (int(data[2:4], 16) >> 2) & 0x3F
        latitude_seconds = ((((int(data[2:8], 16) & 0x03FFFE) >> 1) & 0x01FFFF) / (100000.0)) * 60.0
        latitude_north = int(data[6:8], 16) & 0x01
        latitude = latitude_degrees + (latitude_minutes / 60.0) + (latitude_seconds / 3600.0)
        if (latitude_north == 0):
            latitude = -latitude
        longitude_degrees = int(data[8:10], 16)
        longitude_minutes = (int(data[10:12], 16) >> 2) & 0x3F
        longitude_seconds = ((((int(data[10:16], 16) & 0x03FFFE) >> 1) & 0x01FFFF) / (100000.0)) * 60.0
        longitude_east = int(data[14:16], 16) & 0x01
        longitude = longitude_degrees + (longitude_minutes / 60.0) + (longitude_seconds / 3600.0)
        if (longitude_east == 0):
            longitude = -longitude
        altitude = int(data[16:20], 16)
        gps_fix_duration = int(data[20:22], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUX_DB_MEASUREMENT_GEOLOC,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LATITUDE : latitude,
                INFLUX_DB_FIELD_LONGITUDE : longitude,
                INFLUX_DB_FIELD_ALTITUDE : altitude,
                INFLUX_DB_FIELD_GPS_FIX_DURATION : gps_fix_duration,
                INFLUX_DB_FIELD_LAST_GEOLOC_DATA_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        },
        {
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        }]
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "MFX ID=" + str(device_id) + " * Geoloc data * Lat=" + str(latitude) + ", Long=" + str(longitude) + ", Alt=" + str(altitude) + "m, GpsFixDur=" + str(gps_fix_duration) + "s.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_MFX_DATABASE_NAME, json_body)
    # Geolocation timeout frame.
    if len(data) == (2 * MFX_SIGFOX_GEOLOCATION_TIMEOUT_FRAME_LENGTH_BYTES):
        # Parse field.
        gps_timeout_duration = int(data[0:2], 16)
        # Create JSON object.
        json_body = [
        {
            "measurement": INFLUX_DB_MEASUREMENT_GEOLOC,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_GPS_TIMEOUT_DURATION : gps_timeout_duration
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        },
        {
            "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
            "time": influxdb_timestamp,
            "fields": {
                INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp
            },
            "tags": {
                INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                INFLUX_DB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
            }
        }]
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "MFX ID=" + str(device_id) + " * Geoloc timeout * GpsFixDur=" + str(gps_timeout_duration) + "s.")
        # Fill data base.
        INFLUX_DB_WriteData(INFLUX_DB_MFX_DATABASE_NAME, json_body)
    # Error stack frame.
    if len(data) == (2 * MFX_SIGFOX_ERROR_STACK_FRAME_LENGTH_BYTES):
        # Parse field.
        for idx in range(0, (MFX_SIGFOX_ERROR_STACK_FRAME_LENGTH_BYTES / 2)):
            error = int(data[(idx * 4) : ((idx * 4) + 4)], 16)
            # Store error code if not null.
            if (error != 0):
                # Create JSON object.
                json_body = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_GLOBAL,
                    "time": (influxdb_timestamp - idx),
                    "fields": {
                        INFLUX_DB_FIELD_LAST_COMMUNICATION_TIMESTAMP : influxdb_timestamp,
                        INFLUX_DB_FIELD_ERROR : error
                    },
                    "tags": {
                        INFLUX_DB_TAG_SIGFOX_DEVICE_ID : influxdb_device_id,
                        INFLUX_DB_TAG_METEOFOX_SITE : MFX_GetSite(influxdb_device_id)
                    }
                }]
                if LOG == True:
                    print(LOG_GetCurrentTimestamp() + "MFX ID=" + str(device_id) + " * Error stack * Code=" + hex(error))
                # Fill data base.
                INFLUX_DB_WriteData(INFLUX_DB_MFX_DATABASE_NAME, json_body)