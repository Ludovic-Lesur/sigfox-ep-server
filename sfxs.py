from __future__ import print_function
from BaseHTTPServer import BaseHTTPRequestHandler
import SocketServer
import json

from database.influx_db import *
from log import *
from parsers.atxfox import *
from parsers.dinfox import *
from parsers.meteofox import *
from parsers.sensit import *
from parsers.trackfox import *
from version import *

### PUBLIC MACROS ###

# HTTP server port.
SFXS_HTTP_PORT = 65000
# Backend JSON headers.
SFXS_BACKEND_JSON_HEADER_TIME = "time"
SFXS_BACKEND_JSON_HEADER_EP_ID = "device"
SFXS_BACKEND_JSON_HEADER_DATA = "data"

### PUBLIC FUNCTIONS ###

# Function to update Influx DB database.
def SFXS_update_data_base(timestamp, sigfox_ep_id, data):
    # Meteofox.
    if (sigfox_ep_id in METEOFOX_EP_ID):
        METEOFOX_fill_data_base(timestamp, sigfox_ep_id, data)
    # ATXFox.
    elif (sigfox_ep_id in ATXFOX_EP_ID):
        ATXFOX_fill_data_base(timestamp, sigfox_ep_id, data)
    # TrackFox.
    elif (sigfox_ep_id in TRACKFOX_EP_ID):
        TRACKFOX_fill_data_base(timestamp, sigfox_ep_id, data)
    # Sensit.
    elif (sigfox_ep_id in SENSIT_EP_ID):
        SENSIT_fill_data_base(timestamp, sigfox_ep_id, data)
    # DinFox
    elif (sigfox_ep_id in DINFOX_EP_ID):
        DINFOX_fill_data_base(timestamp, sigfox_ep_id, data)
    else:
        LOG_print_timestamp("[SFXS] * Unknown Sigfox EP-ID")
        
### CLASS DECLARATIONS ###

class ServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        LOG_print("")
        LOG_print_timestamp("[SFXS] * GET request received.")
        self.send_response(200)     
    def do_HEAD(self):
        LOG_print("")
        LOG_print_timestamp("[SFXS] * HEAD request received.")
        self.send_response(200)   
    def do_POST(self):
        LOG_print("")
        LOG_print_timestamp("[SFXS] * POST request received.")
        # Get JSON content.
        post_length = int(self.headers.getheader('content-length', 0))
        post_json = json.loads(self.rfile.read(post_length))
        # Parse data.
        timestamp = int(post_json[SFXS_BACKEND_JSON_HEADER_TIME])
        sigfox_ep_id = (post_json[SFXS_BACKEND_JSON_HEADER_EP_ID]).upper()
        data = (post_json[SFXS_BACKEND_JSON_HEADER_DATA]).upper()
        LOG_print_timestamp("[SFXS] * SIGFOX backend callback * timestamp=" + str(timestamp) + " sigfox_ep_id=" + sigfox_ep_id + " data=" + data)
        # Update database.
        SFXS_update_data_base(timestamp, sigfox_ep_id, data)
        # Send HTTP response.
        self.send_response(200)

### MAIN PROGRAM ###

LOG_print("\n*******************************************************")
LOG_print("------------ Sigfox Devices Server (SFXS) -------------")
LOG_print("*******************************************************\n")

# Init Influx DB database.
INFLUX_DB_init()
# Add script version in database.
version = "SW" + str(GIT_MAJOR_VERSION) + "." + str(GIT_MINOR_VERSION) + "." + str(GIT_COMMIT_INDEX)
if (GIT_DIRTY_FLAG != 0) :
    version = version + ".d"
json_body = [
{
    "time" : int(time.time()),
    "measurement" : INFLUX_DB_MEASUREMENT_METADATA,
    "fields": {
        INFLUX_DB_FIELD_TIME_LAST_STARTUP : int(time.time()),
        INFLUX_DB_FIELD_VERSION : version,
        INFLUX_DB_FIELD_VERSION_MAJOR : GIT_MAJOR_VERSION,
        INFLUX_DB_FIELD_VERSION_MINOR : GIT_MINOR_VERSION,
        INFLUX_DB_FIELD_VERSION_COMMIT_INDEX : GIT_COMMIT_INDEX,
        INFLUX_DB_FIELD_VERSION_COMMIT_ID : GIT_COMMIT_ID,
        INFLUX_DB_FIELD_VERSION_DIRTY_FLAG : GIT_DIRTY_FLAG,
    }
}]
INFLUX_DB_write_data(INFLUX_DB_DATABASE_SFXS, json_body)
# Start server.
SocketServer.TCPServer.allow_reuse_address = True
mfxs_handler = ServerHandler
mfxs = SocketServer.TCPServer(("", SFXS_HTTP_PORT), mfxs_handler)
LOG_print_timestamp("[SFXS] * Starting server at port " + str(SFXS_HTTP_PORT) + ".")
mfxs.serve_forever()