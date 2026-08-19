"""
* sigfox_ep_server.py
*
*  Created on: 02 jun. 2019
*      Author: Ludo
"""

import subprocess

from collections import deque
from database.database import *
from ep.atxfox import *
from ep.common import *
from ep.dinfox import *
from ep.ep import *
from ep.homefox import *
from ep.meteofox import *
from ep.sensit import *
from ep.smarttag import *
from ep.trackfox import *
from http.server import BaseHTTPRequestHandler, HTTPServer
from log import *
import time
import threading
from urllib.parse import urlparse, parse_qs
from utils.configuration import *
from utils.sigfox_cloud import *

### SIGFOX EP SERVER macros ###

SIGFOX_UL_PAYLOAD_SIZE_ATLAS_WIFI = 12

SIGFOX_DOWNLINK_MESSAGES_FILE_NAME = os.path.join(SIGFOX_EP_SERVER_PATH, "sigfox_downlink_messages.json")
SIGFOX_DOWNLINK_MESSAGES_HEADER = "downlink_messages_list"
SIGFOX_DOWNLINK_MESSAGES_HEADER_RECORD_TIME = "record_time"
SIGFOX_DOWNLINK_MESSAGES_HEADER_EP_ID = "ep_id"
SIGFOX_DOWNLINK_MESSAGES_HEADER_DL_PAYLOAD = "dl_payload"
SIGFOX_DOWNLINK_MESSAGES_HEADER_PERMANENT = "permanent"

SIGFOX_DL_PAYLOAD_SIZE_BYTES = 8

SIGFOX_EP_SERVER_API_RATE_LIMIT_REQUESTS = 10
SIGFOX_EP_SERVER_API_RATE_LIMIT_WINDOW_SECONDS = 60
SIGFOX_EP_SERVER_API_KEY_EP = "ep"
SIGFOX_EP_SERVER_API_KEY_LATEST = "latest"
SIGFOX_EP_SERVER_API_KEY_MEASUREMENT = "measurement"
SIGFOX_EP_SERVER_API_KEY_FIELD = "field"
SIGFOX_EP_SERVER_API_KEY_TAGS = "tags"
SIGFOX_EP_SERVER_API_KEY_TIMESTAMP = "timestamp"
SIGFOX_EP_SERVER_API_KEY_VALUE = "value"

### SIGFOX EP SERVER classes ###

class RateLimiter:

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests = deque()
        self._lock = threading.Lock()

    def is_allowed(self) -> bool:
        now = time.time()
        with self._lock:
            while (self._requests and self._requests[0] < (now - self._window_seconds)):
                self._requests.popleft()
            if len(self._requests) >= self._max_requests:
                return False
            self._requests.append(now)
            return True

    def retry_after(self) -> int:
        now = time.time()
        with self._lock:
            if not self._requests:
                return 0
            return max(0, int(self._window_seconds - (now - self._requests[0])) + 1)

class SigfoxEpServer:
    
    def __init__(self) -> None :
        # Init context.
        self._database = Database()
        self._downlink_hash = 0
        self._ep_class = None
        self._ep_database = None
        self._api_key = SIGFOX_EP_SERVER_API_KEY
        # Update Git version in database.
        self._update_git_version()
        # Init downlink messages file.
        self._init_downlink_messages_file()
        
    def _update_git_version(self) -> None:
        # Local variables.
        timestamp_now = int(time.time())
        record = Record()
        dirty_flag = 0
        try:
            # Read last tag.
            tag = subprocess.check_output(["git", "describe", "--tags", "--match", "sw*", "--abbrev=0"], stderr=subprocess.DEVNULL, universal_newlines=True).strip()
            major, minor = map(int, tag.replace("sw", "").split("."))
            # Read number of commits since last tag.
            commit_index = int(subprocess.check_output(["git", "rev-list", "--count", f"{tag}..HEAD"], stderr=subprocess.DEVNULL, universal_newlines=True).strip())
            # Read commit hash.
            commit_id = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, universal_newlines=True).strip().lower()
            # Check dirty state.
            result = subprocess.run(["git", "status", "--porcelain"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            is_dirty = bool(result.stdout.strip())
            # Build version
            version = f"{tag}.{commit_index}"
            if is_dirty:
                dirty_flag = 1
                version += ".dev"
            Log.debug_print("")
            Log.debug_print("[SIGFOX EP SERVER] * Updating Git version in database (" + version + ")")
            record.database = DATABASE_SIGFOX_EP_SERVER
            record.measurement = DATABASE_MEASUREMENT_METADATA
            record.timestamp = timestamp_now
            record.fields = {
                DATABASE_FIELD_LAST_STARTUP_TIME: timestamp_now,
                DATABASE_FIELD_SW_VERSION: version,
                DATABASE_FIELD_SW_VERSION_MAJOR: major,
                DATABASE_FIELD_SW_VERSION_MINOR: minor,
                DATABASE_FIELD_SW_VERSION_COMMIT_INDEX: commit_index,
                DATABASE_FIELD_SW_VERSION_COMMIT_ID: commit_id,
                DATABASE_FIELD_SW_VERSION_DIRTY_FLAG: dirty_flag,
            }
            record.limited_retention = False
            self._database.write_record(record)
        except:
            return
        
    def _init_downlink_messages_file(self) -> None:
        # Check if file already exists.
        Log.debug_print("")
        try:
            # Open file.
            downlink_messages_file = open(SIGFOX_DOWNLINK_MESSAGES_FILE_NAME, "r")
            downlink_messages_json = json.load(downlink_messages_file)
            downlink_messages_file.close()
            # Check header.
            if (SIGFOX_DOWNLINK_MESSAGES_HEADER not in downlink_messages_json):
                raise Exception
            Log.debug_print("[SIGFOX EP SERVER] * Downlink messages file found")
        except:
            # Create file.
            Log.debug_print("[SIGFOX EP SERVER] * Creating downlink messages file")
            downlink_messages_json = {
                SIGFOX_DOWNLINK_MESSAGES_HEADER: []
            }
            downlink_messages_file = open(SIGFOX_DOWNLINK_MESSAGES_FILE_NAME, "w+")
            json.dump(downlink_messages_json, downlink_messages_file, indent = 4)
            downlink_messages_file.close()

    def _set_ep_class_and_database(self, sigfox_ep_id: str) -> None:
        # ATXFox.
        if (sigfox_ep_id in ATXFOX_SIGFOX_EP_ID_LIST):
            self._ep_class = ATXFox
            self._ep_database = DATABASE_ATXFOX
        # DinFox.
        elif (sigfox_ep_id in DINFOX_SIGFOX_EP_ID_LIST):
            self._ep_class = DINFox
            self._ep_database = DATABASE_DINFOX
        # HomeFox.
        elif (sigfox_ep_id in HOMEFOX_SIGFOX_EP_ID_LIST):
            self._ep_class = HomeFox
            self._ep_database = DATABASE_HOMEFOX
        # MeteoFox.
        elif (sigfox_ep_id in METEOFOX_SIGFOX_EP_ID_LIST):
            self._ep_class = MeteoFox
            self._ep_database = DATABASE_METEOFOX
        # Sensit.
        elif (sigfox_ep_id in SENSIT_SIGFOX_EP_ID_LIST):
            self._ep_class = Sensit
            self._ep_database = DATABASE_SENSIT
        # SmartTag.
        elif (sigfox_ep_id in SMARTTAG_SIGFOX_EP_ID_LIST):
            self._ep_class = SmartTag
            self._ep_database = DATABASE_SMARTTAG
        # TrackFox.
        elif (sigfox_ep_id in TRACKFOX_SIGFOX_EP_ID_LIST):
            self._ep_class = TrackFox
            self._ep_database = DATABASE_TRACKFOX
        # Unknown device.
        else:
            self._ep_class = None
            self._ep_database = None

    # Function to compute dynamic DL payload.
    def _compute_dl_payload(self, sigfox_ep_id: str):
        # Local variables.
        timestamp_now = int(time.time())
        dl_message_found = False
        dl_message_record_time = timestamp_now
        record = Record()
        # Initialize with default payload if there is any.
        dl_payload = self._ep_class.get_default_dl_payload(sigfox_ep_id)
        # Open downlink messages file.
        try:
            # Load JSON data.
            downlink_messages_file = open(SIGFOX_DOWNLINK_MESSAGES_FILE_NAME, "r")
            downlink_messages_json = json.load(downlink_messages_file)
            downlink_messages_file.close()
            # Check header.
            if (SIGFOX_DOWNLINK_MESSAGES_HEADER not in downlink_messages_json):
                Log.debug_print("[SIGFOX EP SERVER] * ERROR: downlink messages file header not found")
                raise Exception
            # Messages loop (since the JSON file is written in chronological order, the oldest element is the first one during reading).
            downlink_messages = downlink_messages_json[SIGFOX_DOWNLINK_MESSAGES_HEADER]
            for dl_message_idx, dl_message in enumerate(downlink_messages):
                # Check fields.
                if ((SIGFOX_DOWNLINK_MESSAGES_HEADER_RECORD_TIME not in dl_message) or
                    (SIGFOX_DOWNLINK_MESSAGES_HEADER_EP_ID not in dl_message) or
                    (SIGFOX_DOWNLINK_MESSAGES_HEADER_DL_PAYLOAD not in dl_message) or
                    (SIGFOX_DOWNLINK_MESSAGES_HEADER_PERMANENT not in dl_message)):
                    Log.debug_print("[SIGFOX EP SERVER] * ERROR: missing headers in downlink messages file")
                    raise Exception
                # Compare EP-ID.
                if (int(dl_message[SIGFOX_DOWNLINK_MESSAGES_HEADER_EP_ID], 16) == int(sigfox_ep_id, 16)):
                    # Select the oldest non permanent message, or the oldest permanent message.
                    if (dl_message_found == False):
                        # Read record time payload and.
                        dl_message_record_time = int(dl_message[SIGFOX_DOWNLINK_MESSAGES_HEADER_RECORD_TIME])
                        dl_payload = dl_message[SIGFOX_DOWNLINK_MESSAGES_HEADER_DL_PAYLOAD]
                        # Update flag.
                        dl_message_found = True
                    # Check mode.
                    if (dl_message[SIGFOX_DOWNLINK_MESSAGES_HEADER_PERMANENT] == SIGFOX_CLOUD_CALLBACK_JSON_FALSE):
                        # Force reading.
                        dl_message_record_time = int(dl_message[SIGFOX_DOWNLINK_MESSAGES_HEADER_RECORD_TIME])
                        dl_payload = dl_message[SIGFOX_DOWNLINK_MESSAGES_HEADER_DL_PAYLOAD]
                        # Remove message from the file.
                        del downlink_messages[dl_message_idx]
                        # Update file.
                        downlink_messages_file = open(SIGFOX_DOWNLINK_MESSAGES_FILE_NAME, "w+")
                        json.dump(downlink_messages_json, downlink_messages_file, indent = 4)
                        downlink_messages_file.close()
                        break
            raise Exception
        except:
            # Check final result.
            if (dl_payload is not None):
                # Check size.
                if (len(dl_payload) == (2 * SIGFOX_DL_PAYLOAD_SIZE_BYTES)):
                    # Update dynamic fields.
                    dl_payload = self._ep_class.update_dl_payload(sigfox_ep_id, dl_payload)
                    # Log downlink in database.
                    record.database = self._ep_database
                    record.measurement = DATABASE_MEASUREMENT_SIGFOX_DOWNLINK
                    record.timestamp = timestamp_now
                    record.fields = {
                        DATABASE_FIELD_SIGFOX_DOWNLINK_HASH: self._downlink_hash,
                        DATABASE_FIELD_SIGFOX_DOWNLINK_RECORD_TIME: dl_message_record_time,
                        DATABASE_FIELD_SIGFOX_DOWNLINK_SERVER_TIME: timestamp_now,
                        DATABASE_FIELD_SIGFOX_DOWNLINK_PAYLOAD: dl_payload.upper(),
                    }
                    record.tags = self._ep_class.get_tags(sigfox_ep_id)
                    record.limited_retention = True
                    self._database.write_record(record)
            return dl_payload
        return dl_payload

    def _is_atlas_wifi_message(self, sigfox_ep_id:str, ul_payload: str) -> bool:
        # Local variables.
        atlas_wifi_message = False
        log_message = "invalid UL payload size"
        try:
            # Check UL payload size.
            if ((len(ul_payload) // 2) == SIGFOX_UL_PAYLOAD_SIZE_ATLAS_WIFI):
                log_message = "invalid I/G bit"
                # Check I/G bit of the first byte.
                if (((int(ul_payload[0:2], 16)) & 0x01) == 0):
                    log_message = "no WiFi option in contract"
                    # Check if the device has an Atlas WiFi contract.
                    # Get device informations.
                    response = sigfox_cloud.api_request(SIGFOX_CLOUD_API_REQUEST_DEVICES, { SIGFOX_CLOUD_API_JSON_KEY_ID: sigfox_ep_id }, 0)
                    if ((response == None) or (response.status_code != 200)):
                        raise Exception
                    device_info = json.loads(response.text)
                    # Get contract ID.
                    contract_id = (device_info.get(SIGFOX_CLOUD_API_JSON_KEY_DATA)[0]).get(SIGFOX_CLOUD_API_JSON_KEY_CONTRACT).get(SIGFOX_CLOUD_API_JSON_KEY_ID)
                    # Get contract informations.
                    response = sigfox_cloud.api_request((SIGFOX_CLOUD_API_REQUEST_CONTRACT_INFOS + str(contract_id)), None, 0)
                    if ((response == None) or (response.status_code != 200)):
                        raise Exception
                    contract_info = json.loads(response.text)
                    # Get contract options.
                    contract_options = contract_info.get(SIGFOX_CLOUD_API_JSON_KEY_OPTIONS)
                    # Get geolocation level.
                    geolocation_level = SIGFOX_CLOUD_CALLBACK_GEOLOCATION_LEVEL_NETWORK
                    for idx in range(len(contract_options)):
                        option = contract_options[idx]
                        if (option.get(SIGFOX_CLOUD_API_JSON_KEY_ID) == SIGFOX_CLOUD_API_JSON_KEY_GEOLOCATION):
                            geolocation_level = option.get(SIGFOX_CLOUD_API_JSON_KEY_PARAMETERS).get(SIGFOX_CLOUD_API_JSON_KEY_LEVEL)
                            Log.debug_print("[SIGFOX EP SERVER] * API REQUEST: Geolocation level = " + str(geolocation_level) + " (index " + str(idx) + ")")
                            break
                    # Check geolocation level.
                    if (geolocation_level == SIGFOX_CLOUD_CALLBACK_GEOLOCATION_LEVEL_WIFI):
                        log_message = "all checks passed"
                        atlas_wifi_message = True
        except:
            return atlas_wifi_message
        Log.debug_print("[SIGFOX EP SERVER] * Atlas WiFi message = " + str(atlas_wifi_message) + " (" + log_message + ")")
        return atlas_wifi_message

    def execute_callback(self, json_in: str) -> None:
        # Local variables.
        timestamp_now = int(time.time())
        record_list = List[Record]
        record = Record()
        http_return_code = 204
        json_out = []
        try:
            # Check mandatory JSON fields.
            if ((SIGFOX_CLOUD_CALLBACK_JSON_KEY_TYPE not in json_in) or
                (SIGFOX_CLOUD_CALLBACK_JSON_KEY_TIME not in json_in) or
                (SIGFOX_CLOUD_CALLBACK_JSON_KEY_EP_ID not in json_in)):
                Log.debug_print("[SIGFOX EP SERVER] * ERROR: missing headers in callback JSON (common fields)")
                http_return_code = 415
                raise Exception
            # Read fields.
            callback_type = json_in[SIGFOX_CLOUD_CALLBACK_JSON_KEY_TYPE]
            timestamp = int(json_in[SIGFOX_CLOUD_CALLBACK_JSON_KEY_TIME])
            sigfox_ep_id = Ep.format_sigfox_ep_id(json_in[SIGFOX_CLOUD_CALLBACK_JSON_KEY_EP_ID])
            # Update class pointer and database.
            self._set_ep_class_and_database(sigfox_ep_id)
            # Directly returns if the end-point ID is unknown.
            if ((self._ep_class == None) or (self._ep_database == None)):
                Log.debug_print("[SIGFOX EP SERVER] * ERROR: unknown Sigfox EP-ID.")
                raise Exception
            # Data callback.
            if ((callback_type == SIGFOX_CLOUD_CALLBACK_TYPE_DATA_UPLINK) or (callback_type == SIGFOX_CLOUD_CALLBACK_TYPE_DATA_BIDIR)):
                # Check mandatory JSON fields.
                if ((SIGFOX_CLOUD_CALLBACK_JSON_KEY_MESSAGE_COUNTER not in json_in) or (SIGFOX_CLOUD_CALLBACK_JSON_KEY_UL_PAYLOAD not in json_in)):
                    Log.debug_print("[SIGFOX EP SERVER] * ERROR: missing headers in callback JSON (specific fields)")
                    http_return_code = 424
                    raise Exception
                # Extract common fields.
                message_counter = int(json_in[SIGFOX_CLOUD_CALLBACK_JSON_KEY_MESSAGE_COUNTER])
                ul_payload = json_in[SIGFOX_CLOUD_CALLBACK_JSON_KEY_UL_PAYLOAD].upper()
                # Data uplink callback.
                if (callback_type == SIGFOX_CLOUD_CALLBACK_TYPE_DATA_UPLINK):
                    # Update fields.
                    callback_type_str = "Data uplink"
                    bidirectional_flag = SIGFOX_CLOUD_CALLBACK_JSON_FALSE
                # Data bidirectional callback.
                else:
                    # Check mandatory JSON fields.
                    if (SIGFOX_CLOUD_CALLBACK_JSON_KEY_BIDIRECTIONAL_FLAG not in json_in):
                        Log.debug_print("[SIGFOX EP SERVER] * ERROR: missing headers in callback JSON (specific fields)")
                        http_return_code = 424
                        raise Exception
                    # Update fields.
                    callback_type_str = "Data bidirectional"
                    bidirectional_flag = json_in[SIGFOX_CLOUD_CALLBACK_JSON_KEY_BIDIRECTIONAL_FLAG]
                Log.debug_print("[SIGFOX EP SERVER] * " + callback_type_str + " callback: timestamp=" + str(timestamp) + " sigfox_ep_id=" + sigfox_ep_id + " message_counter=" + str(message_counter) + " ul_payload=" + ul_payload + " bidirectional_flag=" + bidirectional_flag)
                # Parse UL payload.
                [data_type, record_list] = self._ep_class.get_record_list(self._database, timestamp, sigfox_ep_id, ul_payload)
                # Check parsing status.
                if ((data_type != DATABASE_FIELD_DATA_TYPE_UNKNOWN) and (len(record_list) > 0)):
                    # Add common metadata record.
                    record.database = self._ep_database
                    record.measurement = DATABASE_MEASUREMENT_METADATA
                    record.timestamp = timestamp
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_SIGFOX_UPLINK_MESSAGE_COUNTER: message_counter,
                        DATABASE_FIELD_DATA_TYPE: data_type
                    }
                    record.tags = record_list[0].tags
                    record.limited_retention = False
                    record_list.append(copy.copy(record))
                    # Write data base.
                    self._database.write_records(record_list)
                    # Check bidirectional flag.
                    if (bidirectional_flag == SIGFOX_CLOUD_CALLBACK_JSON_TRUE):
                        # Use uplink message counter as downlink message hash.
                        self._downlink_hash = message_counter
                        # Compute DL payload.
                        dl_payload = self._compute_dl_payload(sigfox_ep_id)
                        # Check result.
                        if (dl_payload is not None):
                            # Check size.
                            if (len(dl_payload) == (2 * SIGFOX_DL_PAYLOAD_SIZE_BYTES)):
                                # Build response.
                                http_return_code = 200
                                json_out = {sigfox_ep_id: {"downlinkData": dl_payload}}
                                Log.debug_print("[SIGFOX EP SERVER] * Bidirectional request response: dl_payload=" + dl_payload)
            # Data advanced callback.
            elif (callback_type == SIGFOX_CLOUD_CALLBACK_TYPE_DATA_ADVANCED):
                # Check mandatory JSON fields.
                if ((SIGFOX_CLOUD_CALLBACK_JSON_KEY_MESSAGE_COUNTER not in json_in) or (SIGFOX_CLOUD_CALLBACK_JSON_KEY_UL_PAYLOAD not in json_in) or (SIGFOX_CLOUD_CALLBACK_JSON_KEY_GEOLOCATION not in json_in)):
                    Log.debug_print("[SIGFOX EP SERVER] * ERROR: missing headers in callback JSON (specific fields)")
                    http_return_code = 424
                    raise Exception
                # Parse fields.
                message_counter = int(json_in[SIGFOX_CLOUD_CALLBACK_JSON_KEY_MESSAGE_COUNTER])
                ul_payload = json_in[SIGFOX_CLOUD_CALLBACK_JSON_KEY_UL_PAYLOAD].upper()
                geolocation = json_in[SIGFOX_CLOUD_CALLBACK_JSON_KEY_GEOLOCATION]
                latitude = float(geolocation[SIGFOX_CLOUD_CALLBACK_JSON_KEY_GEOLOCATION_LATITUDE])
                longitude = float(geolocation[SIGFOX_CLOUD_CALLBACK_JSON_KEY_GEOLOCATION_LONGITUDE])
                radius = int(geolocation[SIGFOX_CLOUD_CALLBACK_JSON_KEY_GEOLOCATION_RADIUS])
                source = int(geolocation[SIGFOX_CLOUD_CALLBACK_JSON_KEY_GEOLOCATION_SOURCE])
                status = int(geolocation[SIGFOX_CLOUD_CALLBACK_JSON_KEY_GEOLOCATION_STATUS])
                Log.debug_print("[SIGFOX EP SERVER] * Data advanced callback: timestamp=" + str(timestamp) + " sigfox_ep_id=" + sigfox_ep_id + " ul_payload=" + ul_payload + " latitude=" + str(latitude) + " longitude=" + str(longitude) + " radius=" + str(radius) + " source=" + str(source) + " status=" + str(status))
                # Check status.
                if ((status == SIGFOX_CLOUD_CALLBACK_GEOLOCATION_STATUS_OK) or (status == SIGFOX_CLOUD_CALLBACK_GEOLOCATION_STATUS_FALLBACK_OF_WIFI)):
                    # GPS location.
                    if (source == SIGFOX_CLOUD_CALLBACK_GEOLOCATION_SOURCE_GPS):
                        geolocation_source = DATABASE_FIELD_GEOLOCATION_SOURCE_GPS
                        data_type = DatabaseFieldDataType.GEOLOCATION_GPS.value
                        radius = DATABASE_FIELD_GEOLOCATION_RADIUS_GPS
                    # Atlas WiFi location.
                    elif (source == SIGFOX_CLOUD_CALLBACK_GEOLOCATION_SOURCE_WIFI):
                        geolocation_source = DATABASE_FIELD_GEOLOCATION_SOURCE_SIGFOX_ATLAS_WIFI
                        data_type = DatabaseFieldDataType.GEOLOCATION_SIGFOX_ATLAS_WIFI.value
                    # Atlas Native location.
                    elif (source == SIGFOX_CLOUD_CALLBACK_GEOLOCATION_SOURCE_NETWORK):
                        geolocation_source = DATABASE_FIELD_GEOLOCATION_SOURCE_SIGFOX_ATLAS_NATIVE
                        # Set the data type according to the payload type (override the status field which is always set to fallback for WiFi devices).
                        if (self._is_atlas_wifi_message(sigfox_ep_id, ul_payload) == True):
                            data_type = DatabaseFieldDataType.GEOLOCATION_SIGFOX_ATLAS_NATIVE_FALLBACK_OF_WIFI.value
                        else:
                            data_type = DatabaseFieldDataType.GEOLOCATION_SIGFOX_ATLAS_NATIVE.value
                    else:
                        Log.debug_print("[SIGFOX EP SERVER] * ERROR: invalid data advanced callback (geolocation_source=" + str(source) + ")")
                        raise Exception
                    # Change timestamp to avoid overwriting custom GPS message with Atlas Native.
                    geolocation_timestamp = (timestamp + 1)
                    # Create metadata record.
                    record.database = self._ep_database
                    record.measurement = DATABASE_MEASUREMENT_METADATA
                    record.timestamp = geolocation_timestamp
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: geolocation_timestamp,
                        DATABASE_FIELD_SIGFOX_UPLINK_MESSAGE_COUNTER: message_counter,
                        DATABASE_FIELD_DATA_TYPE: data_type
                    }
                    record.tags = self._ep_class.get_tags(sigfox_ep_id)
                    record.limited_retention = False
                    self._database.write_record(record)
                    # Create geolocation record.
                    record.database = self._ep_database
                    record.measurement = DATABASE_MEASUREMENT_GEOLOCATION
                    record.timestamp = geolocation_timestamp
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: geolocation_timestamp,
                        DATABASE_FIELD_GEOLOCATION_LATITUDE: float(latitude),
                        DATABASE_FIELD_GEOLOCATION_LONGITUDE: float(longitude),
                        DATABASE_FIELD_GEOLOCATION_SOURCE: geolocation_source,
                        DATABASE_FIELD_GEOLOCATION_RADIUS: float(radius)
                    }
                    if (source == SIGFOX_CLOUD_CALLBACK_GEOLOCATION_SOURCE_WIFI):
                        record.add_field(0x00, 0xFF, DATABASE_FIELD_WIFI_SCAN_STATUS, 0x00)
                    record.tags = self._ep_class.get_tags(sigfox_ep_id)
                    record.limited_retention = True
                    self._database.write_record(record)
            # Service acknowledge callback.
            elif (callback_type == SIGFOX_CLOUD_CALLBACK_TYPE_SERVICE_ACKNOWLEDGE):
                # Check mandatory JSON fields.
                if ((SIGFOX_CLOUD_CALLBACK_JSON_KEY_DL_PAYLOAD not in json_in) or
                    (SIGFOX_CLOUD_CALLBACK_JSON_KEY_DL_SUCCESS not in json_in) or
                    (SIGFOX_CLOUD_CALLBACK_JSON_KEY_DL_STATUS not in json_in)):
                    Log.debug_print("[SIGFOX EP SERVER] * ERROR: missing headers in callback JSON (specific fields)")
                    http_return_code = 424
                    raise Exception
                # Parse fields.
                dl_payload = json_in[SIGFOX_CLOUD_CALLBACK_JSON_KEY_DL_PAYLOAD].upper()
                dl_success = json_in[SIGFOX_CLOUD_CALLBACK_JSON_KEY_DL_SUCCESS]
                dl_status = json_in[SIGFOX_CLOUD_CALLBACK_JSON_KEY_DL_STATUS]
                Log.debug_print("[SIGFOX EP SERVER] * Service acknowledge callback: timestamp=" + str(timestamp) + " sigfox_ep_id=" + sigfox_ep_id + " dl_payload=" + dl_payload + " dl_success=" + dl_success + " dl_status=" + dl_status)
                # Log downlink network status in database.
                record.database = self._ep_database
                record.measurement = DATABASE_MEASUREMENT_SIGFOX_DOWNLINK
                record.timestamp = timestamp_now
                record.fields = {
                    DATABASE_FIELD_SIGFOX_DOWNLINK_HASH: self._downlink_hash,
                    DATABASE_FIELD_SIGFOX_DOWNLINK_NETWORK_TIME: timestamp_now,
                    DATABASE_FIELD_SIGFOX_DOWNLINK_PAYLOAD: dl_payload,
                    DATABASE_FIELD_SIGFOX_DOWNLINK_SUCCESS: dl_success,
                    DATABASE_FIELD_SIGFOX_DOWNLINK_STATUS: dl_status
                }
                record.tags = self._ep_class.get_tags(sigfox_ep_id)
                record.limited_retention = True
                self._database.write_record(record)
            # Invalid callback type.
            else:
                Log.debug_print("[SIGFOX EP SERVER] * ERROR: invalid callback type")
                raise Exception
        except:
            pass
        return http_return_code, json_out

class SigfoxEpServerHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        Log.debug_print("")
        Log.debug_print("[SIGFOX EP SERVER] * GET request received")
        # Check API key.
        api_key = self.headers.get("X-API-Key")
        if ((sigfox_ep_server._api_key is None) or (api_key != sigfox_ep_server._api_key)):
            self.send_response(401)
            self.end_headers()
            return
        # Check rate limiting.
        if not rate_limiter.is_allowed():
            self.send_response(429)
            self.send_header("Retry-After", str(rate_limiter.retry_after()))
            self.end_headers()
            return
        # Parse URL.
        parsed = urlparse(self.path)
        parts = parsed.path.strip("/").split("/")
        params = parse_qs(parsed.query)
        if ((len(parts) == 3) and (parts[0] == SIGFOX_EP_SERVER_API_KEY_EP) and (parts[2] == SIGFOX_EP_SERVER_API_KEY_LATEST)):
            ep = parts[1]
            measurement = params.get(SIGFOX_EP_SERVER_API_KEY_MEASUREMENT, [None])[0]
            field = params.get(SIGFOX_EP_SERVER_API_KEY_FIELD, [None])[0]
            # Check if database exists.
            ep_database = (ep + "_db")
            if ep_database not in DATABASE_LIST:
                self.send_response(404)
                self.end_headers()
                return
            # Check mandatory fields.
            if not measurement or not field:
                self.send_response(400)
                self.end_headers()
                return
            # Extract tags.
            reserved_parameters = {SIGFOX_EP_SERVER_API_KEY_MEASUREMENT, SIGFOX_EP_SERVER_API_KEY_FIELD}
            tag_filter = {
                k: v[0] for k, v in params.items() if k not in reserved_parameters
            }
            # Check if at least one tag has been given.
            if not tag_filter:
                self.send_response(400)
                self.end_headers()
                return
            # Perform InfluxDB request.
            where_parts  = [f'"{k}"=\'{v}\'' for k, v in tag_filter.items()]
            where_clause = " AND ".join(where_parts)
            retention_flag = (measurement != DATABASE_MEASUREMENT_METADATA)
            value, timestamp = sigfox_ep_server._database.read_field(ep_database, where_clause, measurement, field, limited_retention=retention_flag)
            # Check if data has been found.
            if ((value is None) or (timestamp is None)):
                self.send_response(404)
                self.end_headers()
                return
            # Build output JSON.
            json_out = {
                SIGFOX_EP_SERVER_API_KEY_EP: ep,
                SIGFOX_EP_SERVER_API_KEY_TAGS: tag_filter,
                SIGFOX_EP_SERVER_API_KEY_MEASUREMENT: measurement,
                SIGFOX_EP_SERVER_API_KEY_FIELD: field,
                SIGFOX_EP_SERVER_API_KEY_TIMESTAMP: timestamp,
                SIGFOX_EP_SERVER_API_KEY_VALUE: value
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(json_out).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_HEAD(self):
        Log.debug_print("")
        Log.debug_print("[SIGFOX EP SERVER] * HEAD request received")
        self.send_response(400)
        self.end_headers()

    def do_POST(self):
        Log.debug_print("")
        Log.debug_print("[SIGFOX EP SERVER] * POST request received")
        # Check content type.
        if ((self.headers.get("content-type")) == "application/json"):
            # Get JSON content.
            json_length = int(self.headers.get("content-length", 0))
            json_in = json.loads(self.rfile.read(json_length))
            # Parse callback.
            http_return_code, json_out = sigfox_ep_server.execute_callback(json_in)
            # Send HTTP response.
            self.send_response(http_return_code)
            if (json_out is not None):
                if (len(json_out) > 0):
                    self.send_header("content-type", "application/json")
                    self.end_headers()
                    self.wfile.write((json.dumps(json_out)).encode())
                else:
                    self.end_headers()
            else:
                self.end_headers()
        else:
            Log.debug_print("ERROR: invalid HTTP content type")
            self.send_response(400)
            self.end_headers()

### SIGFOX EP SERVER main function ###

if __name__ == "__main__":
    # Start print.
    Log.debug_print("**************************************************")
    Log.debug_print("------------ Sigfox End-Point Server -------------")
    Log.debug_print("**************************************************")
    Log.debug_print("")
    # Init server.
    sigfox_ep_server = SigfoxEpServer()
    rate_limiter = RateLimiter(SIGFOX_EP_SERVER_API_RATE_LIMIT_REQUESTS, SIGFOX_EP_SERVER_API_RATE_LIMIT_WINDOW_SECONDS)
    # Start server.
    sigfox_ep_server_handler = HTTPServer(("", SIGFOX_EP_SERVER_HTTP_PORT), SigfoxEpServerHandler)
    sigfox_ep_server_handler.timeout = 10
    Log.debug_print("")
    Log.debug_print("[SIGFOX EP SERVER] * Starting server at port " + str(SIGFOX_EP_SERVER_HTTP_PORT))
    # Main loop.
    while True:
        Log.debug_print("[SIGFOX EP SERVER] * Handle request")
        sigfox_ep_server_handler.handle_request()
