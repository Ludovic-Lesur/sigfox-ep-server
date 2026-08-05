"""
* api_callback.py
*
*  Created on: 26 nov. 2023
*      Author: Ludo
"""

import requests
import json
import sys
import time

from ep.ep import *
from utils.configuration import *
from utils.sigfox_cloud import *

### API CALLBACK macros ###

API_CALLBACK_SIGFOX_CLOUD_API_REQUEST_DELAY_SECONDS = 1.1
API_CALLBACK_SIGFOX_EP_SERVER_TIMEOUT_SECONDS = 10

### API CALLBACK classes ###

class ApiCallback:

    def __init__(self, server_address: str) -> None:
        # Init context.
        self._server_address = server_address

    # Send callback to server.
    def _send_sigfox_ep_server_callback(self, ep_id, messages_list):
        # Message loop.
        for message in messages_list:
            # Create JSON for data bidirectional callback.
            json_callback = {
                SIGFOX_CLOUD_CALLBACK_JSON_KEY_TYPE: SIGFOX_CLOUD_CALLBACK_TYPE_DATA_BIDIR,
                SIGFOX_CLOUD_CALLBACK_JSON_KEY_TIME: str(int(message.get(SIGFOX_CLOUD_API_JSON_KEY_TIME)) // 1000),
                SIGFOX_CLOUD_CALLBACK_JSON_KEY_EP_ID: ep_id,
                SIGFOX_CLOUD_CALLBACK_JSON_KEY_MESSAGE_COUNTER: str(message.get(SIGFOX_CLOUD_API_JSON_KEY_MESSAGE_COUNTER)),
                SIGFOX_CLOUD_CALLBACK_JSON_KEY_UL_PAYLOAD: message.get(SIGFOX_CLOUD_API_JSON_KEY_UL_PAYLOAD),
                SIGFOX_CLOUD_CALLBACK_JSON_KEY_BIDIRECTIONAL_FLAG: SIGFOX_CLOUD_CALLBACK_JSON_FALSE
            }
            print("[SIGFOX_EP_SERVER] * Sending callback for message [time=" + str(message.get(SIGFOX_CLOUD_API_JSON_KEY_TIME)) + ", ul_payload=" + message.get(SIGFOX_CLOUD_API_JSON_KEY_UL_PAYLOAD) + "]")
            # Sigfox EP server callback.
            try:
                response = requests.post(self._server_address, json=json_callback, timeout=API_CALLBACK_SIGFOX_EP_SERVER_TIMEOUT_SECONDS)
                if ((response.status_code == 200) or (response.status_code == 204)):
                    print("[SIGFOX_EP_SERVER] * OK")
                else:
                    print("[SIGFOX_EP_SERVER] * ERROR: status_code=" + str(response.status_code))
            except Exception as expection_message:
                print(expection_message)
            # Delay between callbacks.
            time.sleep(SIGFOX_EP_SERVER_REQUEST_DELAY_SECONDS)

    def restore_all_data(self, timestamp_start_epoch_ms: int, timestamp_stop_epoch_ms: int) -> None:
        # Get devices list.
        sigfox_ep_id_list = ep.get_sigfox_ep_id_list()
        # Build parameters.
        parameters = None
        if (int(timestamp_start_epoch_ms) != 0) and (int(timestamp_stop_epoch_ms) != 0):
            # Retrieve messages in specified time range.
            parameters = {
                SIGFOX_CLOUD_API_JSON_KEY_START_TIME: timestamp_start_epoch_ms,
                SIGFOX_CLOUD_API_JSON_KEY_STOP_TIME: timestamp_stop_epoch_ms
            }
        # Devices loop.
        for sigfox_ep_id in sigfox_ep_id_list:
            print("[API CALLBACK] * Reading all messages of Sigfox EP ID " + sigfox_ep_id)
            # Build request.
            request = SIGFOX_CLOUD_API_REQUEST_DEVICES + sigfox_ep_id + "/" + SIGFOX_CLOUD_API_REQUEST_MESSAGES
            # Paging loop.
            while (str(request) != SIGFOX_CLOUD_API_REQUEST_NONE):
                # API request.
                response = sigfox_cloud.api_request(request, parameters, API_CALLBACK_SIGFOX_CLOUD_API_REQUEST_DELAY_SECONDS)
                if ((response == None) or (response.status_code != 200)):
                    return
                # Open JSON structure.
                messages_list_json = json.loads(response.text)
                messages_list = messages_list_json.get(SIGFOX_CLOUD_API_JSON_KEY_DATA)
                # Check if there are messages to process.
                if (len(messages_list) == 0):
                    request = SIGFOX_CLOUD_API_REQUEST_NONE
                    break
                else:
                    # Get next page request.
                    paging = messages_list_json.get(SIGFOX_CLOUD_API_JSON_KEY_PAGING)
                    request = paging.get(SIGFOX_CLOUD_API_JSON_KEY_NEXT_PAGE_REQUEST)
                # Send callbacks to server.
                self._send_sigfox_ep_server_callback(sigfox_ep_id, messages_list)
        return

### MAIN PROGRAM ###

print("****************************")
print("------- API callback -------")
print("****************************")
print("")

# Read server address.
sigfox_ep_server_name = input("Sigfox EP server address = ")
sigfox_ep_server_address = sigfox_ep_server_name + ":" + str(SIGFOX_EP_SERVER_HTTP_PORT)
print("")

# Read timestamps
timestamp_start_epoch_ms = input("Retrieve data from (EPOCH ms) = ")
timestamp_stop_epoch_ms = input("Retrieve data to (EPOCH ms) = ")
print("")

api_callback = ApiCallback(sigfox_ep_server_address)
api_callback.restore_all_data(timestamp_start_epoch_ms, timestamp_stop_epoch_ms)

print("")
print("***********************")
sys.exit()
