"""
* sigfox_ep_server.py
*
*  Created on: 02 jun. 2019
*      Author: Ludo
"""

import subprocess

from database.database import *
from ep.atxfox import *
from ep.common import *
from ep.dinfox import *
from ep.homefox import *
from ep.meteofox import *
from ep.sensit import *
from ep.trackfox import *
from http.server import BaseHTTPRequestHandler, HTTPServer
from log import *
from utils.configuration import *
from utils.sigfox import *

### SIGFOX EP SERVER macros ###

SIGFOX_DOWNLINK_MESSAGES_FILE_NAME = "/home/ludo/git/sigfox-ep-server/sigfox_downlink_messages.json"
SIGFOX_DOWNLINK_MESSAGES_HEADER = "downlink_messages_list"
SIGFOX_DOWNLINK_MESSAGES_HEADER_RECORD_TIME = "record_time"
SIGFOX_DOWNLINK_MESSAGES_HEADER_EP_ID = "ep_id"
SIGFOX_DOWNLINK_MESSAGES_HEADER_DL_PAYLOAD = "dl_payload"
SIGFOX_DOWNLINK_MESSAGES_HEADER_PERMANENT = "permanent"

SIGFOX_DL_PAYLOAD_SIZE_BYTES = 8

### SIGFOX EP SERVER classes ###

class SigfoxEpServer:
    
    def __init__(self) -> None :
        # Init context.
        self._database = Database()
        self._downlink_hash = 0
        self._database_name = None
        self._get_tags_pfn = None
        self._get_record_list_pfn = None
        self._get_default_dl_payload_pfn = None
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
            
    def _set_database_pointers(self, sigfox_ep_id: str) -> None:
        # ATXFox.
        if (sigfox_ep_id in ATXFOX_SIGFOX_EP_ID_LIST):
            self._database_name = DATABASE_ATXFOX
            self._get_tags_pfn = ATXFox.get_tags
            self._get_record_list_pfn = ATXFox.get_record_list
            self._get_default_dl_payload_pfn = ATXFox.get_default_dl_payload
        # DinFox.
        elif (sigfox_ep_id in DINFOX_SIGFOX_EP_ID_LIST):
            self._database_name = DATABASE_DINFOX
            self._get_tags_pfn = DINFox.get_tags
            self._get_record_list_pfn = DINFox.get_record_list
            self._get_default_dl_payload_pfn = DINFox.get_default_dl_payload
        # HomeFox.
        elif (sigfox_ep_id in HOMEFOX_SIGFOX_EP_ID_LIST):
            self._database_name = DATABASE_HOMEFOX
            self._get_tags_pfn = HomeFox.get_tags
            self._get_record_list_pfn = HomeFox.get_record_list
            self._get_default_dl_payload_pfn = HomeFox.get_default_dl_payload
        # MeteoFox.
        elif (sigfox_ep_id in METEOFOX_SIGFOX_EP_ID_LIST):
            self._database_name = DATABASE_METEOFOX
            self._get_tags_pfn = MeteoFox.get_tags
            self._get_record_list_pfn = MeteoFox.get_record_list
            self._get_default_dl_payload_pfn = MeteoFox.get_default_dl_payload
        # Sensit.
        elif (sigfox_ep_id in SENSIT_SIGFOX_EP_ID_LIST):
            self._database_name = DATABASE_SENSIT
            self._get_tags_pfn = Sensit.get_tags
            self._get_record_list_pfn = Sensit.get_record_list
            self._get_default_dl_payload_pfn = Sensit.get_default_dl_payload
        # TrackFox.
        elif (sigfox_ep_id in TRACKFOX_SIGFOX_EP_ID_LIST):
            self._database_name = DATABASE_TRACKFOX
            self._get_tags_pfn = TrackFox.get_tags
            self._get_record_list_pfn = TrackFox.get_record_list
            self._get_default_dl_payload_pfn = TrackFox.get_default_dl_payload
        # Unknown device.
        else:
            self._database_name = None
            self._get_tags_pfn = None
            self._get_record_list_pfn = None
            self._get_default_dl_payload_pfn = None
            
    # Function to compute dynamic DL payload.
    def _compute_dl_payload(self, sigfox_ep_id: str):
        # Local variables.
        timestamp_now = int(time.time())
        dl_message_found = False
        dl_message_record_time = timestamp_now
        record = Record()
        # Initialize with default payload if there is any.
        dl_payload = self._get_default_dl_payload_pfn(sigfox_ep_id)
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
                    if (dl_message[SIGFOX_DOWNLINK_MESSAGES_HEADER_PERMANENT] == SIGFOX_CALLBACK_JSON_FALSE):
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
                    # Log downlink in database.
                    record.database = self._database_name
                    record.measurement = DATABASE_MEASUREMENT_SIGFOX_DOWNLINK
                    record.timestamp = timestamp_now,
                    record.fields = {
                        DATABASE_FIELD_SIGFOX_DOWNLINK_HASH: self._downlink_hash,
                        DATABASE_FIELD_SIGFOX_DOWNLINK_RECORD_TIME: dl_message_record_time,
                        DATABASE_FIELD_SIGFOX_DOWNLINK_SERVER_TIME: timestamp_now,
                        DATABASE_FIELD_SIGFOX_DOWNLINK_PAYLOAD: dl_payload.upper(),
                    }
                    record.tags = self._get_tags_pfn(sigfox_ep_id)
                    record.limited_retention = True
                    self._database.write_record(record)
            return dl_payload
        return dl_payload
    
    def execute_callback(self, json_in: str) -> None:
        # Local variables.
        timestamp_now = int(time.time())
        record_list = List[Record]
        record = Record()
        http_return_code = 204
        json_out = []
        try:
            # Check mandatory JSON fields.
            if ((SIGFOX_CALLBACK_JSON_KEY_TYPE not in json_in) or
                (SIGFOX_CALLBACK_JSON_KEY_TIME not in json_in) or
                (SIGFOX_CALLBACK_JSON_KEY_EP_ID not in json_in)):
                Log.debug_print("[SIGFOX EP SERVER] * ERROR: missing headers in callback JSON (common fields)")
                http_return_code = 415
                raise Exception
            # Read fields.
            callback_type = json_in[SIGFOX_CALLBACK_JSON_KEY_TYPE]
            timestamp = int(json_in[SIGFOX_CALLBACK_JSON_KEY_TIME])
            sigfox_ep_id = json_in[SIGFOX_CALLBACK_JSON_KEY_EP_ID].upper()
            # Update functions pointer.
            self._set_database_pointers(sigfox_ep_id)
            # Directly returns if the end-point ID is unknown.
            if (self._database_name == None):
                Log.debug_print("[SIGFOX EP SERVER] * ERROR: unknown Sigfox EP-ID.")
                raise Exception
            # Data bidirectional callback.
            if ((callback_type == SIGFOX_CALLBACK_TYPE_DATA_BIDIR) or (callback_type == SIGFOX_CALLBACK_TYPE_SERVICE_STATUS)):
                # Check type.
                if (callback_type == SIGFOX_CALLBACK_TYPE_DATA_BIDIR):
                    # Check mandatory JSON fields.
                    if ((SIGFOX_CALLBACK_JSON_KEY_MESSAGE_COUNTER not in json_in) or
                        (SIGFOX_CALLBACK_JSON_KEY_UL_PAYLOAD not in json_in) or
                        (SIGFOX_CALLBACK_JSON_KEY_BIDIRECTIONAL_FLAG not in json_in)):
                        Log.debug_print("[SIGFOX EP SERVER] * ERROR: missing headers in callback JSON (specific fields)")
                        http_return_code = 424
                        raise Exception
                    # Parse fields.
                    message_counter = int(json_in[SIGFOX_CALLBACK_JSON_KEY_MESSAGE_COUNTER])
                    bidirectional_flag = json_in[SIGFOX_CALLBACK_JSON_KEY_BIDIRECTIONAL_FLAG]
                    ul_payload = json_in[SIGFOX_CALLBACK_JSON_KEY_UL_PAYLOAD].upper()
                else:
                    # Set fields.
                    message_counter = 0
                    bidirectional_flag = SIGFOX_CALLBACK_JSON_FALSE
                    ul_payload = COMMON_UL_PAYLOAD_KEEP_ALIVE
                Log.debug_print("[SIGFOX EP SERVER] * Data bidirectional callback: timestamp=" + str(timestamp) + " sigfox_ep_id=" + sigfox_ep_id + " message_counter=" + str(message_counter) + " ul_payload=" + ul_payload + " bidirectional_flag=" + bidirectional_flag)
                # Parse UL payload.
                record_list = self._get_record_list_pfn(self._database, timestamp, sigfox_ep_id, ul_payload)
                # Check parsing status.
                if (len(record_list) > 0):
                    # Create metadata measurement.
                    record.database = self._database_name
                    record.measurement = DATABASE_MEASUREMENT_METADATA
                    record.timestamp = timestamp
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                    }
                    record.tags = record_list[0].tags
                    record.limited_retention = False
                    record_list.append(copy.copy(record))
                    # Write data base.
                    self._database.write_records(record_list)
                    # Check bidirectional flag.
                    if (bidirectional_flag == SIGFOX_CALLBACK_JSON_TRUE):
                        # Use uplink message counter as downlink message hash.
                        self._downlink_hash = message_counter
                        # Compute DL payload.
                        dl_payload = self._get_default_dl_payload_pfn(sigfox_ep_id)
                        # Check result.
                        if (dl_payload is not None):
                            # Check size.
                            if (len(dl_payload) == (2 * SIGFOX_DL_PAYLOAD_SIZE_BYTES)):
                                # Build response.
                                http_return_code = 200
                                json_out = {sigfox_ep_id: {"downlinkData": dl_payload}}
                                Log.debug_print("[SIGFOX EP SERVER] * Bidirectional request response: dl_payload=" + dl_payload)
            # Data advanced callback.
            elif (callback_type == SIGFOX_CALLBACK_TYPE_DATA_ADVANCED):
                # Check mandatory JSON fields.
                if (SIGFOX_CALLBACK_JSON_KEY_GEOLOCATION not in json_in):
                    Log.debug_print("[SIGFOX EP SERVER] * ERROR: missing headers in callback JSON (specific fields)")
                    http_return_code = 424
                    raise Exception
                # Parse fields.
                geolocation = json_in[SIGFOX_CALLBACK_JSON_KEY_GEOLOCATION]
                latitude = float(geolocation[SIGFOX_CALLBACK_JSON_KEY_GEOLOCATION_LATITUDE])
                longitude = float(geolocation[SIGFOX_CALLBACK_JSON_KEY_GEOLOCATION_LONGITUDE])
                radius = int(geolocation[SIGFOX_CALLBACK_JSON_KEY_GEOLOCATION_RADIUS])
                source = int(geolocation[SIGFOX_CALLBACK_JSON_KEY_GEOLOCATION_SOURCE])
                status = int(geolocation[SIGFOX_CALLBACK_JSON_KEY_GEOLOCATION_STATUS])
                Log.debug_print("[SIGFOX EP SERVER] * Data advanced callback: timestamp=" + str(timestamp) + " sigfox_ep_id=" + sigfox_ep_id + " latitude=" + str(latitude) + " longitude=" + str(longitude) + " radius=" + str(radius) + " source=" + str(source) + " status=" + str(status))
                # Check status.
                if ((status == SIGFOX_CALLBACK_GEOLOCATION_STATUS_OK) or (status == SIGFOX_CALLBACK_GEOLOCATION_STATUS_FALLBACK_OR_WIFI)):
                    # Check source.
                    if (source == SIGFOX_CALLBACK_GEOLOCATION_SOURCE_NETWORK):
                        geolocation_source = DATABASE_FIELD_GEOLOCATION_SOURCE_SIGFOX_ATLAS_NATIVE
                    elif (source == SIGFOX_CALLBACK_GEOLOCATION_SOURCE_WIFI):
                        geolocation_source = DATABASE_FIELD_GEOLOCATION_SOURCE_SIGFOX_ATLAS_WIFI
                    else:
                        Log.debug_print("[SIGFOX EP SERVER] * ERROR: invalid data advanced callback (geolocation_source=" + str(source) + ")")
                        raise Exception
                    # Create geolocation record.
                    record.database = self._database_name
                    record.measurement = DATABASE_MEASUREMENT_GEOLOCATION
                    record.timestamp = timestamp
                    record.fields = {
                        DATABASE_FIELD_LAST_DATA_TIME: timestamp,
                        DATABASE_FIELD_GEOLOCATION_LATITUDE: float(latitude),
                        DATABASE_FIELD_GEOLOCATION_LONGITUDE: float(longitude),
                        DATABASE_FIELD_GEOLOCATION_SOURCE: geolocation_source,
                        DATABASE_FIELD_GEOLOCATION_RADIUS: float(radius)
                    }
                    record.tags = self._get_tags_pfn(sigfox_ep_id)
                    record.limited_retention = True
                    self._database.write_record(record)
            # Service status callback.
            elif (callback_type == SIGFOX_CALLBACK_TYPE_SERVICE_STATUS):
                Log.debug_print("[SIGFOX EP SERVER] * Service status callback: timestamp=" + str(timestamp) + " sigfox_ep_id=" + sigfox_ep_id)
            # Service acknowledge callback.
            elif (callback_type == SIGFOX_CALLBACK_TYPE_SERVICE_ACKNOWLEDGE):
                # Check mandatory JSON fields.
                if ((SIGFOX_CALLBACK_JSON_KEY_DL_PAYLOAD not in json_in) or
                    (SIGFOX_CALLBACK_JSON_KEY_DL_SUCCESS not in json_in) or
                    (SIGFOX_CALLBACK_JSON_KEY_DL_STATUS not in json_in)):
                    Log.debug_print("[SIGFOX EP SERVER] * ERROR: missing headers in callback JSON (specific fields)")
                    http_return_code = 424
                    raise Exception
                # Parse fields.
                dl_payload = json_in[SIGFOX_CALLBACK_JSON_KEY_DL_PAYLOAD].upper()
                dl_success = json_in[SIGFOX_CALLBACK_JSON_KEY_DL_SUCCESS]
                dl_status = json_in[SIGFOX_CALLBACK_JSON_KEY_DL_STATUS]
                Log.debug_print("[SIGFOX EP SERVER] * Service acknowledge callback: timestamp=" + str(timestamp) + " sigfox_ep_id=" + sigfox_ep_id + " dl_payload=" + dl_payload + " dl_success=" + dl_success + " dl_status=" + dl_status)
                # Log downlink network status in database.
                record.database = self._database_name
                record.measurement = DATABASE_MEASUREMENT_SIGFOX_DOWNLINK
                record.timestamp = timestamp_now
                record.fields = {
                    DATABASE_FIELD_SIGFOX_DOWNLINK_HASH: self._downlink_hash,
                    DATABASE_FIELD_SIGFOX_DOWNLINK_NETWORK_TIME: timestamp_now,
                    DATABASE_FIELD_SIGFOX_DOWNLINK_PAYLOAD: dl_payload,
                    DATABASE_FIELD_SIGFOX_DOWNLINK_SUCCESS: dl_success,
                    DATABASE_FIELD_SIGFOX_DOWNLINK_STATUS: dl_status
                }
                record.tags = self._get_tags_pfn(sigfox_ep_id)
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
        self.send_response(400)

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
    # Start server.
    sigfox_ep_server_handler = HTTPServer(("", SIGFOX_EP_SERVER_HTTP_PORT), SigfoxEpServerHandler)
    sigfox_ep_server_handler.timeout = 10
    Log.debug_print("")
    Log.debug_print("[SIGFOX EP SERVER] * Starting server at port " + str(SIGFOX_EP_SERVER_HTTP_PORT))
    # Main loop.
    while True:
        Log.debug_print("[SIGFOX EP SERVER] * Handle request")
        sigfox_ep_server_handler.handle_request()
