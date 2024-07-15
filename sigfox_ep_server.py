from __future__ import print_function
from BaseHTTPServer import BaseHTTPRequestHandler
import SocketServer
import json

from database.influx_db import *
from log import *
from ep.atxfox import *
from ep.common import *
from ep.dinfox import *
from ep.meteofox import *
from ep.sensit import *
from ep.trackfox import *
from utils.common import *
from version import *

### LOCAL MACROS ###

# Downlink messages file.
SIGFOX_DOWNLINK_MESSAGES_FILE_NAME = "/home/ludo/git/sigfox-ep-server/sigfox_downlink_messages.json"
SIGFOX_DOWNLINK_MESSAGES_HEADER = "downlink_messages_list"
SIGFOX_DOWNLINK_MESSAGES_HEADER_RECORD_TIME = "record_time"
SIGFOX_DOWNLINK_MESSAGES_HEADER_EP_ID = "ep_id"
SIGFOX_DOWNLINK_MESSAGES_HEADER_DL_PAYLOAD = "dl_payload"
SIGFOX_DOWNLINK_MESSAGES_HEADER_PERMANENT = "permanent"
SIGFOX_DL_PAYLOAD_SIZE_BYTES = 8

### LOCAL GLOBAL VARIABLES ###

sigfox_ep_server_downlink_message_hash = 0
sigfox_ep_server_database_name = COMMON_ERROR_DATA
SIGFOX_EP_SERVER_parse_ul_payload = COMMON_ERROR_DATA
SIGFOX_EP_SERVER_get_default_dl_payload = COMMON_ERROR_DATA
SIGFOX_EP_SERVER_add_ep_tag = COMMON_ERROR_DATA

### LOCAL FUNCTIONS ###

# Init database.
def SIGFOX_EP_SERVER_init_database() :
    # Init Influx DB database.
    INFLUX_DB_init()

# Update startup time and script software version in database.
def SIGFOX_EP_SERVER_write_software_version() :
    # Add script version in database.
    sigfox_ep_server_version = "sw" + str(GIT_MAJOR_VERSION) + "." + str(GIT_MINOR_VERSION) + "." + str(GIT_COMMIT_INDEX)
    if (GIT_DIRTY_FLAG != 0) :
        sigfox_ep_server_version = sigfox_ep_server_version + ".d"
    LOG_print("")
    LOG_print("[SIGFOX EP SERVER] * version=" + sigfox_ep_server_version)
    json_body = [
    {
        "time" : int(time.time()),
        "measurement" : INFLUX_DB_MEASUREMENT_METADATA,
        "fields": {
            INFLUX_DB_FIELD_TIME_LAST_STARTUP : int(time.time()),
            INFLUX_DB_FIELD_VERSION : sigfox_ep_server_version,
            INFLUX_DB_FIELD_VERSION_MAJOR : GIT_MAJOR_VERSION,
            INFLUX_DB_FIELD_VERSION_MINOR : GIT_MINOR_VERSION,
            INFLUX_DB_FIELD_VERSION_COMMIT_INDEX : GIT_COMMIT_INDEX,
            INFLUX_DB_FIELD_VERSION_COMMIT_ID : GIT_COMMIT_ID,
            INFLUX_DB_FIELD_VERSION_DIRTY_FLAG : GIT_DIRTY_FLAG,
        }
    }]
    INFLUX_DB_write_data(INFLUX_DB_DATABASE_SIGFOX_EP_SERVER, json_body)
    
# Init downlink message file.
def SIGFOX_EP_SERVER_init_downlink_messages_file() :
    # Check if file already exists.
    LOG_print("")
    try :
        # Open file.
        downlink_messages_file = open(SIGFOX_DOWNLINK_MESSAGES_FILE_NAME, "r")
        downlink_messages_json = json.load(downlink_messages_file)
        downlink_messages_file.close()
        # Check header.
        if (SIGFOX_DOWNLINK_MESSAGES_HEADER not in downlink_messages_json) :
            raise Exception
        LOG_print("[SIGFOX EP SERVER] * Downlink messages file found")
    except :
        # Create file.
        LOG_print("[SIGFOX EP SERVER] * Creating downlink messages file")
        downlink_messages_json = {
            SIGFOX_DOWNLINK_MESSAGES_HEADER : []
        }
        downlink_messages_file = open(SIGFOX_DOWNLINK_MESSAGES_FILE_NAME, "w+")
        json.dump(downlink_messages_json, downlink_messages_file, indent=4)
        downlink_messages_file.close()

# Update database pointers.
def SIGFOX_EP_SERVER_set_database_pointers(sigfox_ep_id) :
    # Global variables.
    global sigfox_ep_server_database_name
    global SIGFOX_EP_SERVER_parse_ul_payload
    global SIGFOX_EP_SERVER_get_default_dl_payload
    global SIGFOX_EP_SERVER_add_ep_tag
    # ATXFox.
    if (sigfox_ep_id in ATXFOX_EP_ID_LIST) :
        sigfox_ep_server_database_name = INFLUX_DB_DATABASE_ATXFOX
        SIGFOX_EP_SERVER_add_ep_tag = ATXFOX_add_ep_tag
        SIGFOX_EP_SERVER_parse_ul_payload = ATXFOX_parse_ul_payload
        SIGFOX_EP_SERVER_get_default_dl_payload = ATXFOX_get_default_dl_payload
    # DinFox
    elif (sigfox_ep_id in DINFOX_EP_ID_LIST) :
        sigfox_ep_server_database_name = INFLUX_DB_DATABASE_DINFOX
        SIGFOX_EP_SERVER_add_ep_tag = DINFOX_add_ep_tag
        SIGFOX_EP_SERVER_parse_ul_payload = DINFOX_parse_ul_payload
        SIGFOX_EP_SERVER_get_default_dl_payload = DINFOX_get_default_dl_payload
    # MeteoFox.
    elif (sigfox_ep_id in METEOFOX_EP_ID_LIST) :
        sigfox_ep_server_database_name = INFLUX_DB_DATABASE_METEOFOX
        SIGFOX_EP_SERVER_add_ep_tag = METEOFOX_add_ep_tag
        SIGFOX_EP_SERVER_parse_ul_payload = METEOFOX_parse_ul_payload
        SIGFOX_EP_SERVER_get_default_dl_payload = METEOFOX_get_default_dl_payload
    # Sensit.
    elif (sigfox_ep_id in SENSIT_EP_ID_LIST) :
        sigfox_ep_server_database_name = INFLUX_DB_DATABASE_SENSIT
        SIGFOX_EP_SERVER_add_ep_tag = SENSIT_add_ep_tag
        SIGFOX_EP_SERVER_parse_ul_payload = SENSIT_parse_ul_payload
        SIGFOX_EP_SERVER_get_default_dl_payload = SENSIT_get_default_dl_payload
    # TrackFox.
    elif (sigfox_ep_id in TRACKFOX_EP_ID_LIST) :
        sigfox_ep_server_database_name = INFLUX_DB_DATABASE_TRACKFOX
        SIGFOX_EP_SERVER_add_ep_tag = TRACKFOX_add_ep_tag
        SIGFOX_EP_SERVER_parse_ul_payload = TRACKFOX_parse_ul_payload
        SIGFOX_EP_SERVER_get_default_dl_payload = TRACKFOX_get_default_dl_payload
    else :
        sigfox_ep_server_database_name = COMMON_ERROR_DATA
        SIGFOX_EP_SERVER_add_ep_tag = COMMON_ERROR_DATA
        SIGFOX_EP_SERVER_parse_ul_payload = COMMON_ERROR_DATA
        SIGFOX_EP_SERVER_get_default_dl_payload = COMMON_ERROR_DATA
 
# Function to compute dynamic DL payload.       
def SIGFOX_EP_SERVER_compute_dl_payload(sigfox_ep_id) :
    # Global variables.
    global sigfox_ep_server_downlink_message_hash
    global sigfox_ep_server_database_name
    global SIGFOX_EP_SERVER_add_ep_tag
    # Local variables.
    dl_message_found = False
    dl_message_record_time = int(time.time())
    # Initialize with default payload if there is any.
    dl_payload = SIGFOX_EP_SERVER_get_default_dl_payload(sigfox_ep_id)
    # Open downlink messages file.
    try :
        # Load JSON data.
        downlink_messages_file = open(SIGFOX_DOWNLINK_MESSAGES_FILE_NAME, "r")
        downlink_messages_json = json.load(downlink_messages_file)
        downlink_messages_file.close()
        # Check header.
        if (SIGFOX_DOWNLINK_MESSAGES_HEADER not in downlink_messages_json) :
            LOG_print("[SIGFOX EP SERVER] * ERROR: downlink messages file header not found")
            raise Exception
        # Messages loop (since the JSON file is written in chronological order, the oldest element is the first one during reading).
        downlink_messages = downlink_messages_json[SIGFOX_DOWNLINK_MESSAGES_HEADER]
        for dl_message_idx, dl_message in enumerate(downlink_messages) :
            # Check fields.
            if ((SIGFOX_DOWNLINK_MESSAGES_HEADER_RECORD_TIME not in dl_message) or
                (SIGFOX_DOWNLINK_MESSAGES_HEADER_EP_ID not in dl_message) or
                (SIGFOX_DOWNLINK_MESSAGES_HEADER_DL_PAYLOAD not in dl_message) or 
                (SIGFOX_DOWNLINK_MESSAGES_HEADER_PERMANENT not in dl_message)) :
                LOG_print("[SIGFOX EP SERVER] * ERROR: missing headers in downlink messages file")
                raise Exception
            # Compare EP-ID.
            if (int(dl_message[SIGFOX_DOWNLINK_MESSAGES_HEADER_EP_ID], 16) == int(sigfox_ep_id, 16)) :
                # Select the oldest non permanent message, or the oldest permanent message.
                if (dl_message_found == False) :
                    # Read record time payload and.
                    dl_message_record_time = int(dl_message[SIGFOX_DOWNLINK_MESSAGES_HEADER_RECORD_TIME])
                    dl_payload = dl_message[SIGFOX_DOWNLINK_MESSAGES_HEADER_DL_PAYLOAD]
                    # Update flag.
                    dl_message_found = True
                # Check mode.
                if (dl_message[SIGFOX_DOWNLINK_MESSAGES_HEADER_PERMANENT] == JSON_FALSE) :
                    # Force reading.
                    dl_message_record_time = int(dl_message[SIGFOX_DOWNLINK_MESSAGES_HEADER_RECORD_TIME])
                    dl_payload = dl_message[SIGFOX_DOWNLINK_MESSAGES_HEADER_DL_PAYLOAD]
                    # Remove message from the file.
                    del downlink_messages[dl_message_idx]
                    # Update file.
                    downlink_messages_file = open(SIGFOX_DOWNLINK_MESSAGES_FILE_NAME, "w+")
                    json.dump(downlink_messages_json, downlink_messages_file, indent=4)
                    downlink_messages_file.close()
                    break
        raise Exception
    except :
        # Check final result.
        if (dl_payload is not None) :
            # Check size.
            if (len(dl_payload) == (2 * SIGFOX_DL_PAYLOAD_SIZE_BYTES)) :
                # Log downlink in database.
                json_dl_data = [
                {
                    "measurement": INFLUX_DB_MEASUREMENT_DOWNLINK,
                    "time": int(time.time()),
                    "fields": {
                        INFLUX_DB_FIELD_DOWNLINK_HASH : sigfox_ep_server_downlink_message_hash,
                        INFLUX_DB_FIELD_TIME_DOWNLINK_RECORD : dl_message_record_time,
                        INFLUX_DB_FIELD_TIME_DOWNLINK_SERVER : int(time.time()),
                        INFLUX_DB_FIELD_DL_PAYLOAD : dl_payload.upper(),
                    }
                } ]
                SIGFOX_EP_SERVER_add_ep_tag(json_dl_data, sigfox_ep_id)
                INFLUX_DB_write_data(sigfox_ep_server_database_name, json_dl_data)
        return dl_payload
    return dl_payload

# Function to parse and execute callback from Sigfox cloud.
def SIGFOX_EP_SERVER_execute_callback(json_in) :
    # Global variables.
    global sigfox_ep_server_downlink_message_hash
    global SIGFOX_EP_SERVER_parse_ul_payload
    global SIGFOX_EP_SERVER_add_ep_tag
    # Local variables.
    http_return_code = 204
    json_out = []
    try :
        # Check mandatory JSON fields.
        if ((SIGFOX_CALLBACK_JSON_HEADER_TYPE not in json_in) or
            (SIGFOX_CALLBACK_JSON_HEADER_TIME not in json_in) or
            (SIGFOX_CALLBACK_JSON_HEADER_EP_ID not in json_in)) : 
            LOG_print("[SIGFOX EP SERVER] * ERROR: missing headers in callback JSON (common fields)")
            http_return_code = 415
            raise Exception
        # Read fields.
        callback_type = json_in[SIGFOX_CALLBACK_JSON_HEADER_TYPE]
        timestamp = int(json_in[SIGFOX_CALLBACK_JSON_HEADER_TIME])
        sigfox_ep_id = json_in[SIGFOX_CALLBACK_JSON_HEADER_EP_ID].upper()
        # Update functions pointer.
        SIGFOX_EP_SERVER_set_database_pointers(sigfox_ep_id)
        # Directly returns if the end-point ID is unknown.
        if (sigfox_ep_server_database_name == COMMON_ERROR_DATA) :
            LOG_print("[SIGFOX EP SERVER] * ERROR: unknown Sigfox EP-ID.")
            raise Exception
        # Data bidir callback.
        if (callback_type == SIGFOX_CALLBACK_TYPE_DATA_BIDIR) :
            # Check mandatory JSON fields.
            if ((SIGFOX_CALLBACK_JSON_HEADER_MESSAGE_COUNTER not in json_in) or
                (SIGFOX_CALLBACK_JSON_HEADER_UL_PAYLOAD not in json_in) or
                (SIGFOX_CALLBACK_JSON_HEADER_BIDIRECTIONAL_FLAG not in json_in)) :
                LOG_print("[SIGFOX EP SERVER] * ERROR: missing headers in callback JSON (specific fields)")
                http_return_code = 424
                raise Exception
            # Parse fields.
            message_counter = int(json_in[SIGFOX_CALLBACK_JSON_HEADER_MESSAGE_COUNTER])
            ul_payload = json_in[SIGFOX_CALLBACK_JSON_HEADER_UL_PAYLOAD].upper()
            bidirectional_flag = json_in[SIGFOX_CALLBACK_JSON_HEADER_BIDIRECTIONAL_FLAG]
            LOG_print("[SIGFOX EP SERVER] * Data bidir callback: timestamp=" + str(timestamp) + " sigfox_ep_id=" + sigfox_ep_id + " message_counter=" + str(message_counter) + " ul_payload=" + ul_payload + " bidirectional_flag=" + bidirectional_flag)    
            # Parse UL payload.
            json_ul_data = SIGFOX_EP_SERVER_parse_ul_payload(timestamp, sigfox_ep_id, ul_payload)
            # Fill data base.
            if (json_ul_data is not None) :
                if (len(json_ul_data) > 0) :
                    SIGFOX_EP_SERVER_add_ep_tag(json_ul_data, sigfox_ep_id)
                    INFLUX_DB_write_data(sigfox_ep_server_database_name, json_ul_data)
            # Check bidirectional flag.
            if (bidirectional_flag == JSON_TRUE):
                # Use uplink message counter as downlink message hash.
                sigfox_ep_server_downlink_message_hash = message_counter
                # Compute DL payload.
                dl_payload = SIGFOX_EP_SERVER_compute_dl_payload(sigfox_ep_id)
                # Check result.
                if (dl_payload is not None) :
                    # Check size.
                    if (len(dl_payload) == (2 * SIGFOX_DL_PAYLOAD_SIZE_BYTES)) :
                        # Build response.
                        http_return_code = 200
                        json_out = {sigfox_ep_id : {"downlinkData" : dl_payload}}
                        LOG_print("[SIGFOX EP SERVER] * Bidir request response: dl_payload=" + dl_payload)
        # Service status callback.
        elif (callback_type == SIGFOX_CALLBACK_TYPE_SERVICE_STATUS) :
            LOG_print("[SIGFOX EP SERVER] * Service status callback: timestamp=" + str(timestamp) + " sigfox_ep_id=" + sigfox_ep_id)
            # Parse keep alive frame.
            json_ul_data = SIGFOX_EP_SERVER_parse_ul_payload(timestamp, sigfox_ep_id, COMMON_UL_PAYLOAD_KEEP_ALIVE)
            # Fill data base.
            if (json_ul_data is not None) :
                if (len(json_ul_data) > 0) :
                    SIGFOX_EP_SERVER_add_ep_tag(json_ul_data, sigfox_ep_id)
                    INFLUX_DB_write_data(sigfox_ep_server_database_name, json_ul_data)
        # Service acknowledge callback.
        elif (callback_type == SIGFOX_CALLBACK_TYPE_SERVICE_ACKNOWLEDGE) :
            # Check mandatory JSON fields.
            if ((SIGFOX_CALLBACK_JSON_HEADER_DL_PAYLOAD not in json_in) or
                (SIGFOX_CALLBACK_JSON_HEADER_DL_SUCCESS not in json_in) or
                (SIGFOX_CALLBACK_JSON_HEADER_DL_STATUS not in json_in)) :
                LOG_print("[SIGFOX EP SERVER] * ERROR: missing headers in callback JSON (specific fields)")
                http_return_code = 424
                raise Exception
            # Parse fields.
            dl_payload = json_in[SIGFOX_CALLBACK_JSON_HEADER_DL_PAYLOAD].upper()
            dl_success = json_in[SIGFOX_CALLBACK_JSON_HEADER_DL_SUCCESS]
            dl_status = json_in[SIGFOX_CALLBACK_JSON_HEADER_DL_STATUS]
            LOG_print("[SIGFOX EP SERVER] * Service acknowledge callback: timestamp=" + str(timestamp) + " sigfox_ep_id=" + sigfox_ep_id + " dl_payload=" + dl_payload + " dl_success=" + dl_success + " dl_status=" + dl_status)
            # Log downlink network status in database.
            json_dl_data = [
            {
                "measurement": INFLUX_DB_MEASUREMENT_DOWNLINK,
                "time": int(time.time()),
                "fields": {
                    INFLUX_DB_FIELD_DOWNLINK_HASH : sigfox_ep_server_downlink_message_hash,
                    INFLUX_DB_FIELD_TIME_DOWNLINK_NETWORK : int(time.time()),
                    INFLUX_DB_FIELD_DL_PAYLOAD : dl_payload,
                    INFLUX_DB_FIELD_DL_SUCCESS : dl_success,
                    INFLUX_DB_FIELD_DL_STATUS : dl_status
                }
            } ]
            SIGFOX_EP_SERVER_add_ep_tag(json_dl_data, sigfox_ep_id)
            INFLUX_DB_write_data(sigfox_ep_server_database_name, json_dl_data)
        # Invalid callback type.
        else :
            LOG_print("[SIGFOX EP SERVER] * ERROR: invalid callback type")
        raise Exception
    except :
        return http_return_code, json_out
    return http_return_code, json_out
        
### CLASS DECLARATIONS ###

class ServerHandler(BaseHTTPRequestHandler):
    # Get request.
    def do_GET(self):
        LOG_print("")
        LOG_print("[SIGFOX EP SERVER] * GET request received")
        self.send_response(400)
    # Head request.
    def do_HEAD(self):
        LOG_print("")
        LOG_print("[SIGFOX EP SERVER] * HEAD request received")
        self.send_response(400)
    # Post request.
    def do_POST(self):
        LOG_print("")
        LOG_print("[SIGFOX EP SERVER] * POST request received")
        # Check content type.
        if ((self.headers.getheader("content-type")) == "application/json") :
            # Get JSON content.
            json_length = int(self.headers.getheader("content-length", 0))
            json_in = json.loads(self.rfile.read(json_length))
            # Parse callback.
            http_return_code, json_out = SIGFOX_EP_SERVER_execute_callback(json_in)
            # Send HTTP response.
            self.send_response(http_return_code)
            if (json_out is not None) :
                if (len(json_out) > 0) :
                    self.send_header("content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(json_out))
        else :
            LOG_print("ERROR: invalid HTTP content type")
            self.send_response(400)

### MAIN PROGRAM ###

LOG_print("**************************************************")
LOG_print("------------ Sigfox End-Point Server -------------")
LOG_print("**************************************************")
LOG_print("")

# Init Influx DB database.
SIGFOX_EP_SERVER_init_database()
# Update startup time and software version.
SIGFOX_EP_SERVER_write_software_version()
# Init downlink messages file.
SIGFOX_EP_SERVER_init_downlink_messages_file()
# Start server.
SocketServer.TCPServer.allow_reuse_address = True
sigfox_ep_server_handler = ServerHandler
sigfox_ep_server = SocketServer.TCPServer(("", SIGFOX_EP_SERVER_HTTP_PORT), sigfox_ep_server_handler)
sigfox_ep_server.timeout = 10
LOG_print("")
LOG_print("[SIGFOX EP SERVER] * Starting server at port " + str(SIGFOX_EP_SERVER_HTTP_PORT))
# Main loop.
while True:
    LOG_print("[SIGFOX EP SERVER] * Handle request")
    sigfox_ep_server.handle_request()
