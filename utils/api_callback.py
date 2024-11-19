import requests
import json
import sys
import time

from defs import *

### MACROS ###

# Credential file.
CREDENTIALS_FILE_NAME = "credentials.json"
CREDENTIALS_JSON_HEADER_SIGFOX_EP_SERVER_ADDRESS = "sigfox_ep_server_address"
CREDENTIALS_JSON_HEADER_SIGFOX_CLOUD_USER = "sigfox_cloud_user"
CREDENTIALS_JSON_HEADER_SIGFOX_CLOUD_PASSWORD = "sigfox_cloud_password"
CREDENTIALS_JSON_HEADER_SIGFOX_DEVICE_TYPES_LIST = "sigfox_device_types_list"
CREDENTIALS_JSON_HEADER_SIGFOX_DEVICE_TYPE_NAME = "name"
CREDENTIALS_JSON_HEADER_SIGFOX_DEVICE_TYPE_ID = "id"

# Sigfox cloud API request.
SIGFOX_CLOUD_API_ADDRESS = "https://api.sigfox.com/v2/"
SIGFOX_CLOUD_API_REQUEST_DEVICES = "devices/"
SIGFOX_CLOUD_API_REQUEST_MESSAGES = "messages/"
SIGFOX_CLOUD_API_REQUEST_NONE = "None"
SIGFOX_CLOUD_API_REQUEST_DELAY_SECONDS = 1.1
SIGFOX_CLOUD_API_REQUEST_TIMEOUT_SECONDS = 10

# Sigfox cloud API JSON headers.
SIGFOX_CLOUD_API_JSON_HEADER_TIME = "time"
SIGFOX_CLOUD_API_JSON_HEADER_DATA = "data"
SIGFOX_CLOUD_API_JSON_HEADER_FIELD = "fields"
SIGFOX_CLOUD_API_JSON_FIELDS = "oob, ackRequired"
SIGFOX_CLOUD_API_JSON_HEADER_START_TIME = "since"
SIGFOX_CLOUD_API_JSON_HEADER_STOP_TIME = "before"
SIGFOX_CLOUD_API_JSON_HEADER_DEVICE_TYPE_ID = "deviceTypeId"
SIGFOX_CLOUD_API_JSON_HEADER_UL_PAYLOAD = "data"
SIGFOX_CLOUD_API_JSON_HEADER_EP_ID = "id"
SIGFOX_CLOUD_API_JSON_HEADER_MESSAGE_COUNTER = "seqNumber"
SIGFOX_CLOUD_API_JSON_HEADER_OOB = "oob"
SIGFOX_CLOUD_API_JSON_HEADER_PAGING = "paging"
SIGFOX_CLOUD_API_JSON_HEADER_NEXT_PAGE_REQUEST = "next"
SIGFOX_CONTROL_KEEP_ALIVE_MESSAGE_SIZE = 7

# Destination servers.
API_CALLBACK_SERVER_ADDRESS_LOCAL = "local"
API_CALLBACK_SERVER_ADDRESS_PRODUCTION = "production"

### GLOBAL VARIABLES ###

sigfox_ep_server_address = SIGFOX_EP_SERVER_LOCAL_ADDRESS + ":" + str(SIGFOX_EP_SERVER_HTTP_PORT)
sigfox_api_callback_credentials_json = []

### FUNCTIONS ###

# Read credentials file required to perform API requests and callback.
def API_CALLBACK_read_credentials_file() :
	# Global variables.
	global sigfox_api_callback_credentials_json
	# Local variables.
	status = False
	# Open credentials file.
	try :
		# Open file.
		credentials_file = open(CREDENTIALS_FILE_NAME, "r")
		sigfox_api_callback_credentials_json = json.load(credentials_file)
		credentials_file.close()
		# Check headers.
		if ((CREDENTIALS_JSON_HEADER_SIGFOX_EP_SERVER_ADDRESS not in sigfox_api_callback_credentials_json) or 
			(CREDENTIALS_JSON_HEADER_SIGFOX_CLOUD_USER not in sigfox_api_callback_credentials_json) or
			(CREDENTIALS_JSON_HEADER_SIGFOX_CLOUD_PASSWORD not in sigfox_api_callback_credentials_json) or
			(CREDENTIALS_JSON_HEADER_SIGFOX_DEVICE_TYPES_LIST not in sigfox_api_callback_credentials_json)) :
			print("[API CALLBACK] * ERROR: missing header in credentials file")
		else :
			status = True
			print("[API CALLBACK] * Credentials file found")
	except Exception as expection_message :
		print(expection_message)
		return status
	return status

# Update Sigfox EP server address.
def API_CALLBACK_update_sigfox_ep_server_address(sigfox_ep_server_name):
	# Global variables.
	global sigfox_ep_server_address
	global sigfox_api_callback_credentials_json
	# Local variables.
	status = False
	# Check destination.
	if (sigfox_ep_server_name == API_CALLBACK_SERVER_ADDRESS_LOCAL) :
		# Use local address.
		sigfox_ep_server_address = SIGFOX_EP_SERVER_LOCAL_ADDRESS + ":" + str(SIGFOX_EP_SERVER_HTTP_PORT)
		print("[API CALLBACK] * Using local Sigfox EP server (" + sigfox_ep_server_address + ")")
		status = True
	elif (sigfox_ep_server_name == API_CALLBACK_SERVER_ADDRESS_PRODUCTION) :
		# Use address from credentials file.
		sigfox_ep_server_address = sigfox_api_callback_credentials_json[CREDENTIALS_JSON_HEADER_SIGFOX_EP_SERVER_ADDRESS] + ":" + str(SIGFOX_EP_SERVER_HTTP_PORT)
		print("[API CALLBACK] * Using production Sigfox EP server (" + sigfox_ep_server_address + ")")
		status = True
	else :
		print("[API CALLBACK] * Invalid Sigfox EP server address")
	return status

# Get device type ID from credentials file.
def API_CALLBACK_get_device_type_id(device_type_name) :
	# Global variables.
	global sigfox_api_callback_credentials_json
	# Local variables.
	status = False
	device_type_id = "00"
	# Device types loop.
	try :
		device_types_list = sigfox_api_callback_credentials_json[CREDENTIALS_JSON_HEADER_SIGFOX_DEVICE_TYPES_LIST]
		for device_type_idx, device_type in enumerate(device_types_list) :
			# Check headers.
			if ((CREDENTIALS_JSON_HEADER_SIGFOX_DEVICE_TYPE_NAME not in device_type) or
				(CREDENTIALS_JSON_HEADER_SIGFOX_DEVICE_TYPE_ID not in device_type)) :
				print("[API CALLBACK] * ERROR: missing header in device type " + str(device_type_idx) + " of credentials file")
			else :
				if (device_type[CREDENTIALS_JSON_HEADER_SIGFOX_DEVICE_TYPE_NAME] == device_type_name) :
					device_type_id = device_type[CREDENTIALS_JSON_HEADER_SIGFOX_DEVICE_TYPE_ID]
					status = True
					break
	except Exception as expection_message :
		print(expection_message)
		return status, device_type_id
	if (status == False) :
		print("[API CALLBACK] * ERROR: Unknown device type")
	return status, device_type_id

# Perform a Sigfox cloud API request.
def API_CALLBACK_send_sigfox_cloud_api_request(request, parameters) :
	# Local variables.
	status = False
	response = "null"
	# Read Sigfox cloud credentials.
	sigfox_cloud_user = sigfox_api_callback_credentials_json[CREDENTIALS_JSON_HEADER_SIGFOX_CLOUD_USER]
	sigfox_cloud_password = sigfox_api_callback_credentials_json[CREDENTIALS_JSON_HEADER_SIGFOX_CLOUD_PASSWORD]
	# Delay for rate limiting.
	time.sleep(SIGFOX_CLOUD_API_REQUEST_DELAY_SECONDS)
	# Perform request.
	try :
		response = requests.get(request, auth=(sigfox_cloud_user, sigfox_cloud_password), params=parameters, timeout=SIGFOX_CLOUD_API_REQUEST_TIMEOUT_SECONDS)
		if (response.status_code == 200) :
			print("[SIGFOX CLOUD API REQUEST] * OK")
			status = True
		else:
			print("[SIGFOX CLOUD API REQUEST] * ERROR: status_code=" + str(response.status_code) + " content=" + response.text)
	except Exception as expection_message :
		print(expection_message)
	return status, response

# Send callback to server.
def API_CALLBACK_send_sigfox_ep_server_callback(ep_id, messages_list) :
	# Global variables.
	global sigfox_ep_server_address
	# Message loop.
	for message in messages_list:
		# Check OOB flag.
		if ((message.get(SIGFOX_CLOUD_API_JSON_HEADER_OOB) == True) and (len(message.get(SIGFOX_CLOUD_API_JSON_HEADER_UL_PAYLOAD)) == (2 * SIGFOX_CONTROL_KEEP_ALIVE_MESSAGE_SIZE))) :
			# Create JSON for service status.
			json_callback = {
				SIGFOX_CALLBACK_JSON_HEADER_TYPE : SIGFOX_CALLBACK_TYPE_SERVICE_STATUS,
				SIGFOX_CALLBACK_JSON_HEADER_TIME : str(int(message.get(SIGFOX_CLOUD_API_JSON_HEADER_TIME)) // 1000),
				SIGFOX_CALLBACK_JSON_HEADER_EP_ID : ep_id,
			}
		else :
			# Create JSON for data bidir.
			json_callback = {
				SIGFOX_CALLBACK_JSON_HEADER_TYPE : SIGFOX_CALLBACK_TYPE_DATA_BIDIR,
				SIGFOX_CALLBACK_JSON_HEADER_TIME : str(int(message.get(SIGFOX_CLOUD_API_JSON_HEADER_TIME)) // 1000),
				SIGFOX_CALLBACK_JSON_HEADER_EP_ID : ep_id,
				SIGFOX_CALLBACK_JSON_HEADER_MESSAGE_COUNTER : str(message.get(SIGFOX_CLOUD_API_JSON_HEADER_MESSAGE_COUNTER)),
				SIGFOX_CALLBACK_JSON_HEADER_UL_PAYLOAD : message.get(SIGFOX_CLOUD_API_JSON_HEADER_UL_PAYLOAD),
				SIGFOX_CALLBACK_JSON_HEADER_BIDIRECTIONAL_FLAG : JSON_FALSE
			}
		print("[SIGFOX_EP_SERVER] * Sending callback for message [time=" + str(message.get(SIGFOX_CLOUD_API_JSON_HEADER_TIME)) + ", ul_payload=" + message.get(SIGFOX_CLOUD_API_JSON_HEADER_UL_PAYLOAD) + "]")
		# Sigfox EP server callback.
		try:		
			response = requests.post(sigfox_ep_server_address, json=json_callback, timeout=10)
			if ((response.status_code == 200) or (response.status_code == 204)) :
				print("[SIGFOX_EP_SERVER] * OK")
			else:
				print("[SIGFOX_EP_SERVER] * ERROR: status_code=" + str(response.status_code))
		except Exception as expection_message :
			print(expection_message)
		# Delay between callbacks.
		time.sleep(SIGFOX_EP_SERVER_REQUEST_DELAY_SECONDS)

# Generic function to end script.
def API_CALLBACK_end_program() :
	print("")
	print("***********************")
	sys.exit()

### MAIN PROGRAM ###

print("****************************")
print("------- API callback -------")
print("****************************")
print("")

# Read credentials file.
status = API_CALLBACK_read_credentials_file()
if (status == False) :
	API_CALLBACK_end_program()
	
# Read server address.
print("")
sigfox_ep_server_name = input("Sigfox EP server address = ")
print("")

# Update server address.
status = API_CALLBACK_update_sigfox_ep_server_address(sigfox_ep_server_name)
if (status == False) :
	API_CALLBACK_end_program()

# Read device type.
print("")
device_type_name = input("Device type name = ")
print("")

# Get device type ID.
status, device_type_id = API_CALLBACK_get_device_type_id(device_type_name)
if (status == False) :
	API_CALLBACK_end_program()
	
# Get all devices of the device type.
print("[API CALLBACK] * Reading devices list of the device type " + device_type_name)

devices_list_request = SIGFOX_CLOUD_API_ADDRESS + SIGFOX_CLOUD_API_REQUEST_DEVICES
devices_list_request_parameters = {SIGFOX_CLOUD_API_JSON_HEADER_DEVICE_TYPE_ID : device_type_id}
status, device_list_request_response = API_CALLBACK_send_sigfox_cloud_api_request(devices_list_request, devices_list_request_parameters)
if (status == False) :
	API_CALLBACK_end_program()

# Read timestamps
print("")
timestamp_start_epoch_ms = input("Retrieve data from (EPOCH ms) = ")
timestamp_stop_epoch_ms = input("Retrieve data to (EPOCH ms) = ")
print("")

# Get devices list.
sigfox_cloud_api_json = json.loads(device_list_request_response.text)
devices_list = sigfox_cloud_api_json.get(SIGFOX_CLOUD_API_JSON_HEADER_DATA)
# Devices loop.
for device in devices_list:
	# Get ID.
	ep_id = device.get(SIGFOX_CLOUD_API_JSON_HEADER_EP_ID)
	# Build request.
	messages_list_request = SIGFOX_CLOUD_API_ADDRESS + SIGFOX_CLOUD_API_REQUEST_DEVICES + str(ep_id) + "/" + SIGFOX_CLOUD_API_REQUEST_MESSAGES
	# Build parameters.
	if (int(timestamp_start_epoch_ms) == 0) and (int(timestamp_stop_epoch_ms) == 0) :
		# Retrieve all messages.
		messages_list_request_parameters = {
			SIGFOX_CLOUD_API_JSON_HEADER_FIELD : SIGFOX_CLOUD_API_JSON_FIELDS,
			SIGFOX_CLOUD_API_JSON_HEADER_OOB : JSON_TRUE
		}
	else :
		# Retrieve messages in specified time range.
		messages_list_request_parameters = {
			SIGFOX_CLOUD_API_JSON_HEADER_FIELD : SIGFOX_CLOUD_API_JSON_FIELDS,
			SIGFOX_CLOUD_API_JSON_HEADER_OOB : JSON_TRUE,
			SIGFOX_CLOUD_API_JSON_HEADER_START_TIME : timestamp_start_epoch_ms,
			SIGFOX_CLOUD_API_JSON_HEADER_STOP_TIME : timestamp_stop_epoch_ms
		}
	print("[API CALLBACK] * Reading all messages of EP-ID " + ep_id)
	# Paging loop.
	while (str(messages_list_request) != SIGFOX_CLOUD_API_REQUEST_NONE) :
		# API request.
		status, messages_list_request_response = API_CALLBACK_send_sigfox_cloud_api_request(messages_list_request, messages_list_request_parameters)
		if (status == False):
			API_CALLBACK_end_program()
		# Open JSON structure.
		sigfox_cloud_api_json = json.loads(messages_list_request_response.text)
		messages_list = sigfox_cloud_api_json.get(SIGFOX_CLOUD_API_JSON_HEADER_DATA)
		# Check if there are messages to process.
		if (len(messages_list) == 0) :
			messages_list_request = SIGFOX_CLOUD_API_REQUEST_NONE
			break
		else :
			# Get next page request.
			paging = sigfox_cloud_api_json.get(SIGFOX_CLOUD_API_JSON_HEADER_PAGING)
			messages_list_request = paging.get(SIGFOX_CLOUD_API_JSON_HEADER_NEXT_PAGE_REQUEST)
		# Send callbacks to server.
		API_CALLBACK_send_sigfox_ep_server_callback(ep_id, messages_list)

# Program end.	
API_CALLBACK_end_program()
