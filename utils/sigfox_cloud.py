"""
* sigfox_cloud.py
*
*  Created on: 08 sep. 2024
*      Author: Ludo
"""

import json
import requests
import time

### SIGFOX CLOUD MACROS ###

SIGFOX_CLOUD_CREDENTIALS_FILE_NAME = "/home/ludo/git/sigfox-ep-server/sigfox_cloud_credentials.json"
SIGFOX_CLOUD_CREDENTIALS_JSON_KEY_USER = "user"
SIGFOX_CLOUD_CREDENTIALS_JSON_KEY_PASSWORD = "password"

SIGFOX_CLOUD_API_REQUEST_TIMEOUT_SECONDS = 10

SIGFOX_CLOUD_API_ADDRESS = "https://api.sigfox.com/v2/"

SIGFOX_CLOUD_API_REQUEST_DEVICES = "devices/"
SIGFOX_CLOUD_API_REQUEST_MESSAGES = "messages/"
SIGFOX_CLOUD_API_REQUEST_CONTRACT_INFOS = "contract-infos/"
SIGFOX_CLOUD_API_REQUEST_NONE = "None"

SIGFOX_CLOUD_API_JSON_KEY_TIME = "time"
SIGFOX_CLOUD_API_JSON_KEY_DATA = "data"
SIGFOX_CLOUD_API_JSON_KEY_START_TIME = "since"
SIGFOX_CLOUD_API_JSON_KEY_STOP_TIME = "before"
SIGFOX_CLOUD_API_JSON_KEY_DEVICE_TYPE_ID = "deviceTypeId"
SIGFOX_CLOUD_API_JSON_KEY_UL_PAYLOAD = "data"
SIGFOX_CLOUD_API_JSON_KEY_ID = "id"
SIGFOX_CLOUD_API_JSON_KEY_MESSAGE_COUNTER = "seqNumber"
SIGFOX_CLOUD_API_JSON_KEY_CONTRACT = "contract"
SIGFOX_CLOUD_API_JSON_KEY_OPTIONS = "options"
SIGFOX_CLOUD_API_JSON_KEY_GEOLOCATION = "geolocation"
SIGFOX_CLOUD_API_JSON_KEY_PARAMETERS = "parameters"
SIGFOX_CLOUD_API_JSON_KEY_LEVEL = "level"
SIGFOX_CLOUD_API_JSON_KEY_PAGING = "paging"
SIGFOX_CLOUD_API_JSON_KEY_NEXT_PAGE_REQUEST = "next"

SIGFOX_CLOUD_CALLBACK_TYPE_DATA_UPLINK = "data_uplink"
SIGFOX_CLOUD_CALLBACK_TYPE_DATA_BIDIR = "data_bidir"
SIGFOX_CLOUD_CALLBACK_TYPE_DATA_ADVANCED = "data_advanced"
SIGFOX_CLOUD_CALLBACK_TYPE_SERVICE_ACKNOWLEDGE = "service_acknowledge"

SIGFOX_CLOUD_CALLBACK_JSON_KEY_TYPE = "type"
SIGFOX_CLOUD_CALLBACK_JSON_KEY_TIME = "time"
SIGFOX_CLOUD_CALLBACK_JSON_KEY_EP_ID = "ep_id"
SIGFOX_CLOUD_CALLBACK_JSON_KEY_MESSAGE_COUNTER = "message_counter"
SIGFOX_CLOUD_CALLBACK_JSON_KEY_UL_PAYLOAD = "ul_payload"
SIGFOX_CLOUD_CALLBACK_JSON_KEY_BIDIRECTIONAL_FLAG = "bidirectional_flag"
SIGFOX_CLOUD_CALLBACK_JSON_KEY_GEOLOCATION = "geolocation"
SIGFOX_CLOUD_CALLBACK_JSON_KEY_GEOLOCATION_LATITUDE = "lat"
SIGFOX_CLOUD_CALLBACK_JSON_KEY_GEOLOCATION_LONGITUDE = "lng"
SIGFOX_CLOUD_CALLBACK_JSON_KEY_GEOLOCATION_RADIUS = "radius"
SIGFOX_CLOUD_CALLBACK_JSON_KEY_GEOLOCATION_SOURCE = "source"
SIGFOX_CLOUD_CALLBACK_JSON_KEY_GEOLOCATION_STATUS = "status"
SIGFOX_CLOUD_CALLBACK_JSON_KEY_DL_PAYLOAD = "dl_payload"
SIGFOX_CLOUD_CALLBACK_JSON_KEY_DL_SUCCESS = "dl_success"
SIGFOX_CLOUD_CALLBACK_JSON_KEY_DL_STATUS = "dl_status"
SIGFOX_CLOUD_CALLBACK_JSON_TRUE = "true"
SIGFOX_CLOUD_CALLBACK_JSON_FALSE = "false"

SIGFOX_CLOUD_CALLBACK_GEOLOCATION_LEVEL_NETWORK = 1
SIGFOX_CLOUD_CALLBACK_GEOLOCATION_LEVEL_WIFI = 2

SIGFOX_CLOUD_CALLBACK_GEOLOCATION_SOURCE_GPS = 1
SIGFOX_CLOUD_CALLBACK_GEOLOCATION_SOURCE_NETWORK = 2
SIGFOX_CLOUD_CALLBACK_GEOLOCATION_SOURCE_WIFI = 6

SIGFOX_CLOUD_CALLBACK_GEOLOCATION_STATUS_NO_POSITION = 0
SIGFOX_CLOUD_CALLBACK_GEOLOCATION_STATUS_OK = 1
SIGFOX_CLOUD_CALLBACK_GEOLOCATION_STATUS_FALLBACK_OF_WIFI = 2
SIGFOX_CLOUD_CALLBACK_GEOLOCATION_STATUS_INVALID_PAYLOAD = 3

SIGFOX_CLOUD_CALLBACK_DOWNLINK_TIMESTAMP_DELTA = 32

### SIGFOX CLOUD classes ###

class SigfoxCloud:
    
    def __init__(self) -> None:
        # Init context.
        self._user = None
        self._password = None
        # Open credentials file.
        try:
            # Open file.
            credentials_file = open(SIGFOX_CLOUD_CREDENTIALS_FILE_NAME, "r")
            credentials_json = json.load(credentials_file)
            credentials_file.close()
            # Check mandatory fields.
            if ((SIGFOX_CLOUD_CREDENTIALS_JSON_KEY_USER not in credentials_json) or (SIGFOX_CLOUD_CREDENTIALS_JSON_KEY_PASSWORD not in credentials_json)):
                raise Exception
            # Update credentials.
            self._user = credentials_json[SIGFOX_CLOUD_CREDENTIALS_JSON_KEY_USER]
            self._password = credentials_json[SIGFOX_CLOUD_CREDENTIALS_JSON_KEY_PASSWORD]
        except:
            return
        return
    
    def api_request(self, request: str, parameters: str, delay_seconds: int) -> str:
        # Local variables.
        response = None
        # Optional delay for rate limiting.
        if (delay_seconds > 0):
            time.sleep(delay_seconds)
        # Perform request.
        try:
            # Add the cloud address if required.
            if (SIGFOX_CLOUD_API_ADDRESS not in request):
                request = (SIGFOX_CLOUD_API_ADDRESS + request)
            response = requests.get(request, auth=(self._user, self._password), params=parameters, timeout=SIGFOX_CLOUD_API_REQUEST_TIMEOUT_SECONDS)
        except:
            return response
        return response
    
# Init shared class instance.
sigfox_cloud = SigfoxCloud()
