"""
* configuration.py
*
*  Created on: 08 sep. 2024
*      Author: Ludo
"""

import json
import os
from utils.log import *

### CONFIGURATION local macros ###

SIGFOX_EP_SERVER_CONFIG_FILE_NAME = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "sigfox_ep_server.json")

SIGFOX_EP_SERVER_CONFIG_JSON_KEY_PATH = "path"
SIGFOX_EP_SERVER_CONFIG_JSON_KEY_HTTP_PORT = "http_port"
SIGFOX_EP_SERVER_CONFIG_JSON_KEY_API_KEY = "api_key"
SIGFOX_EP_SERVER_CONFIG_JSON_KEY_SIGFOX_CLOUD = "sigfox_cloud"
SIGFOX_EP_SERVER_CONFIG_JSON_KEY_USER = "user"
SIGFOX_EP_SERVER_CONFIG_JSON_KEY_PASSWORD = "password"
SIGFOX_EP_SERVER_CONFIG_JSON_KEY_DL_MESSAGES_FILE_PATH = "dl_messages_file_path"

### CONFIGURATION macros ###

SIGFOX_EP_SERVER_PATH = None
SIGFOX_EP_SERVER_HTTP_PORT = None
SIGFOX_EP_SERVER_LOCAL_ADDRESS = "http://localhost"
SIGFOX_EP_SERVER_REQUEST_DELAY_SECONDS = 0.1
SIGFOX_EP_SERVER_API_KEY = None
SIGFOX_CLOUD_USER = None
SIGFOX_CLOUD_PASSWORD = None
SIGFOX_EP_DL_MESSAGES_FILE_PATH = None

### CONFIGURATION loading ###

try:
    _config_file = open(SIGFOX_EP_SERVER_CONFIG_FILE_NAME, "r")
    _config_json = json.load(_config_file)
    _config_file.close()
    SIGFOX_EP_SERVER_PATH = _config_json[SIGFOX_EP_SERVER_CONFIG_JSON_KEY_PATH]
    SIGFOX_EP_SERVER_HTTP_PORT = int(_config_json[SIGFOX_EP_SERVER_CONFIG_JSON_KEY_HTTP_PORT])
    SIGFOX_EP_SERVER_API_KEY = _config_json[SIGFOX_EP_SERVER_CONFIG_JSON_KEY_API_KEY]
    SIGFOX_CLOUD_USER = _config_json[SIGFOX_EP_SERVER_CONFIG_JSON_KEY_SIGFOX_CLOUD][SIGFOX_EP_SERVER_CONFIG_JSON_KEY_USER]
    SIGFOX_CLOUD_PASSWORD = _config_json[SIGFOX_EP_SERVER_CONFIG_JSON_KEY_SIGFOX_CLOUD][SIGFOX_EP_SERVER_CONFIG_JSON_KEY_PASSWORD]
    SIGFOX_EP_DL_MESSAGES_FILE_PATH = _config_json[SIGFOX_EP_SERVER_CONFIG_JSON_KEY_DL_MESSAGES_FILE_PATH]
except Exception as e:
    # Stop server.
    Log.debug_print("[SIGFOX EP SERVER] * ERROR: Failed to load configuration file (" + str(e) + ")")
    exit(1)
