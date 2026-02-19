"""
* common.py
*
*  Created on: 23 oct. 2022
*      Author: Ludo
"""

import copy

from database.database import *
from log import *

### COMMON public macros ###

COMMON_UNKNOWN = "unknown"

COMMON_UL_PAYLOAD_KEEP_ALIVE = "control_keep_alive_payload"

COMMON_UL_PAYLOAD_SIZE_STARTUP = 8
COMMON_UL_PAYLOAD_SIZE_GEOLOC = 11
COMMON_UL_PAYLOAD_SIZE_GEOLOC_TIMEOUT = 2

### COMMON classes ###

class Common:

    @staticmethod
    def one_complement_to_value(one_complement_data: int, sign_bit_position: int) -> int:
        mask = ((1 << sign_bit_position) - 1)
        value = (one_complement_data & mask);
        if ((one_complement_data & (1 << sign_bit_position)) != 0):
            value = (-1) * value
        return value
    
    @staticmethod
    def get_record_startup(template: Record, timestamp: int, ul_payload: str, record_list: List[Record]) -> None:
        # Local variables.
        record = template
        # Parse fields.
        reset_flags = int(ul_payload[0:2], 16)
        sw_version_major = int(ul_payload[2:4], 16)
        sw_version_minor = int(ul_payload[4:6], 16)
        sw_version_commit_index = int(ul_payload[6:8], 16)
        sw_version_commit_id = (ul_payload[8:15]).lower()
        sw_version_dirty_flag = int(ul_payload[15:16], 16)
        sw_version = "sw" + str(sw_version_major) + "." + str(sw_version_minor) + "." + str(sw_version_commit_index)
        if (sw_version_dirty_flag != 0):
            sw_version += ".dev"
        # Create metadata record.
        record.measurement = DATABASE_MEASUREMENT_METADATA
        record.fields = {
            DATABASE_FIELD_LAST_STARTUP_TIME: timestamp,
            DATABASE_FIELD_RESET_FLAGS: reset_flags,
            DATABASE_FIELD_SW_VERSION: sw_version,
            DATABASE_FIELD_SW_VERSION_MAJOR: sw_version_major,
            DATABASE_FIELD_SW_VERSION_MINOR: sw_version_minor,
            DATABASE_FIELD_SW_VERSION_COMMIT_INDEX: sw_version_commit_index,
            DATABASE_FIELD_SW_VERSION_COMMIT_ID: sw_version_commit_id,
            DATABASE_FIELD_SW_VERSION_DIRTY_FLAG: sw_version_dirty_flag
        }
        record.limited_retention = False
        record_list.append(copy.copy(record))
    
    @staticmethod
    def get_record_geolocation(template: Record, timestamp: int, ul_payload: str, record_list: List[Record]) -> None:
        # Local variables.
        record = template
        # Parse fields.
        latitude_degrees = int(ul_payload[0:2], 16)
        latitude_minutes = (int(ul_payload[2:4], 16) >> 2) & 0x3F
        latitude_seconds = (((((int(ul_payload[2:8], 16) & 0x03FFFE) >> 1) & 0x01FFFF) / (100000.0)) * 60.0)
        latitude_north = int(ul_payload[6:8], 16) & 0x01
        latitude = latitude_degrees + (latitude_minutes / 60.0) + (latitude_seconds / 3600.0)
        if (latitude_north == 0):
            latitude = -latitude
        longitude_degrees = int(ul_payload[8:10], 16)
        longitude_minutes = (int(ul_payload[10:12], 16) >> 2) & 0x3F
        longitude_seconds = (((((int(ul_payload[10:16], 16) & 0x03FFFE) >> 1) & 0x01FFFF) / (100000.0)) * 60.0)
        longitude_east = int(ul_payload[14:16], 16) & 0x01
        longitude = longitude_degrees + (longitude_minutes / 60.0) + (longitude_seconds / 3600.0)
        if (longitude_east == 0):
            longitude = -longitude
        altitude_m = int(ul_payload[16:20], 16)
        gps_acquisition_time_seconds = int(ul_payload[20:22], 16)
        # Manually add a success status into database.
        gps_acquisition_status = 0
        # Create geoloc record.
        record.measurement = DATABASE_MEASUREMENT_GEOLOCATION
        record.fields = {
            DATABASE_FIELD_LAST_DATA_TIME: timestamp,
            DATABASE_FIELD_GEOLOCATION_LATITUDE: float(latitude),
            DATABASE_FIELD_GEOLOCATION_LONGITUDE: float(longitude),
            DATABASE_FIELD_GEOLOCATION_ALTITUDE: float(altitude_m),
            DATABASE_FIELD_GPS_ACQUISITION_STATUS: gps_acquisition_status,
            DATABASE_FIELD_GPS_ACQUISITION_TIME: float(gps_acquisition_time_seconds)
        }
        record.limited_retention = True
        record_list.append(copy.copy(record))
    
    @staticmethod
    def get_record_geolocation_timeout(template: Record, timestamp: int, ul_payload: str, record_list: List[Record]) -> None:
        # Local variables.
        record = template
        # Unused parameter.
        _ = timestamp
        # Parse fields
        gps_acquisition_status = int(ul_payload[0:2], 16)
        gps_acquisition_time_seconds = int(ul_payload[2:4], 16)
        # Create geoloc record.
        record.measurement = DATABASE_MEASUREMENT_GEOLOCATION
        record.fields = {
             DATABASE_FIELD_GPS_ACQUISITION_STATUS: gps_acquisition_status,
             DATABASE_FIELD_GPS_ACQUISITION_TIMEOUT_TIME: float(gps_acquisition_time_seconds)
        }
        record.limited_retention = True
        record_list.append(copy.copy(record))
    
    @staticmethod
    def get_record_error_stack(template: Record, timestamp: int, ul_payload: str, number_of_errors: int, record_list: List[Record]) -> None:
        # Local variables.
        record = template
        record.measurement = DATABASE_MEASUREMENT_METADATA
        record.limited_retention = True
        # Parse fields.
        for idx in range(0, number_of_errors):
            # Get error.
            error = int(ul_payload[(idx * 4): ((idx * 4) + 4)], 16)
            # Store error code if not null.
            if (error != 0):
                record.timestamp = (timestamp + idx)
                record.fields = {
                     DATABASE_FIELD_ERROR: error
                }
                record_list.append(copy.copy(record))
