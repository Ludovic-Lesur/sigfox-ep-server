from __future__ import print_function
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import json

from atxfox import *
from influx_db import *
from meteofox import *
from sensit import *
from solarfox import *
from synchrofox import *
from trackfox import *
from log import *

### MACROS ###

# HTTP server port.
SFXS_HTTP_PORT = 65000

# Backend JSON headers.
SFXS_BACKEND_JSON_HEADER_TIME = "time"
SFXS_BACKEND_JSON_HEADER_DEVICE_ID = "device"
SFXS_BACKEND_JSON_HEADER_DATA = "data"

### FUNCTIONS ###

# Function to update Influx DB database.
def SFXS_UpdateDataBase(sfxs_timestamp, sfxs_device_id, sfxs_data):
    # Meteofox.
    if (sfxs_device_id in MFX_SIGFOX_DEVICES_ID):
        MFX_FillDataBase(int(sfxs_timestamp), sfxs_device_id, sfxs_data)
    # ATXFox.
    elif (sfxs_device_id in ATXFX_SIGFOX_DEVICES_ID):
        ATXFX_FillDataBase(int(sfxs_timestamp), sfxs_device_id, sfxs_data)
    # SolarFox
    elif (sfxs_device_id in SLFX_SIGFOX_DEVICES_ID):
        SLFX_FillDataBase(int(sfxs_timestamp), sfxs_device_id, sfxs_data)
    # SynchroFox.
    elif (sfxs_device_id in SYNCFX_SIGFOX_DEVICES_ID):
        SYNCFX_FillDataBase(int(sfxs_timestamp), sfxs_device_id, sfxs_data)
    # TrackFox.
    elif (sfxs_device_id in TKFX_SIGFOX_DEVICES_ID):
        TKFX_FillDataBase(int(sfxs_timestamp), sfxs_device_id, sfxs_data)
    # Sensit.
    elif (sfxs_device_id in SENSIT_SIGFOX_DEVICES_ID):
        SENSIT_FillDataBase(int(sfxs_timestamp), sfxs_device_id, sfxs_data)
    else:
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "SFXS Unknown Sigfox device ID.")
        
### CLASS DECLARATIONS ###

class ServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if LOG == True:
            print("")
            print(LOG_GetCurrentTimestamp() + "SFXS GET request received.")
        self.send_response(200)     
    def do_HEAD(self):
        if LOG == True:
            print("")
            print(LOG_GetCurrentTimestamp() + "SFXS HEAD request received.")
        self.send_response(200)   
    def do_POST(self):
        # Get JSON content.
        post_length = int(self.headers.getheader('content-length', 0))
        post_json = json.loads(self.rfile.read(post_length))
        if LOG == True:
            print("")
            print(LOG_GetCurrentTimestamp() + "SFXS POST request received.")
        # Parse data.
        callback_timestamp = post_json[SFXS_BACKEND_JSON_HEADER_TIME]
        callback_device_id = post_json[SFXS_BACKEND_JSON_HEADER_DEVICE_ID]
        callback_data = post_json[SFXS_BACKEND_JSON_HEADER_DATA]
        if LOG == True:
            print(LOG_GetCurrentTimestamp() + "SFXS SIGFOX backend callback * Timestamp=" + callback_timestamp + " ID=" + callback_device_id + " Data=" + callback_data)
        # Update database.
        SFXS_UpdateDataBase(callback_timestamp, callback_device_id, callback_data)
        # Send HTTP response.
        self.send_response(200)

### MAIN PROGRAM ###

if LOG == True:
    print("\n*******************************************************")
    print("------------ Sigfox Devices Server (SFXS) -------------")
    print("*******************************************************\n")

# Init Influx DB database.
INFLUX_DB_Init()
# Start server.
SocketServer.TCPServer.allow_reuse_address = True
mfxs_handler = ServerHandler
mfxs = SocketServer.TCPServer(("", SFXS_HTTP_PORT), mfxs_handler)
if LOG == True:
    print (LOG_GetCurrentTimestamp() + "SFXS Starting server at port " + str(SFXS_HTTP_PORT) + ".")
mfxs.serve_forever()