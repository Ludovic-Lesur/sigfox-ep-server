### COMMON MACROS ###

# HTTP server port.
SIGFOX_EP_SERVER_HTTP_PORT = 65000
SIGFOX_EP_SERVER_LOCAL_ADDRESS = "http://localhost"
SIGFOX_EP_SERVER_REQUEST_DELAY_SECONDS = 0.1

# Sigfox cloud callbacks JSON headers.
SIGFOX_CALLBACK_JSON_HEADER_TYPE = "type"
SIGFOX_CALLBACK_JSON_HEADER_TIME = "time"
SIGFOX_CALLBACK_JSON_HEADER_EP_ID = "ep_id"
SIGFOX_CALLBACK_JSON_HEADER_MESSAGE_COUNTER = "message_counter"
SIGFOX_CALLBACK_JSON_HEADER_UL_PAYLOAD = "ul_payload"
SIGFOX_CALLBACK_JSON_HEADER_BIDIRECTIONAL_FLAG = "bidirectional_flag"
SIGFOX_CALLBACK_JSON_HEADER_DL_PAYLOAD = "dl_payload"
SIGFOX_CALLBACK_JSON_HEADER_DL_SUCCESS = "dl_success"
SIGFOX_CALLBACK_JSON_HEADER_DL_STATUS = "dl_status"

# Callback types.
SIGFOX_CALLBACK_TYPE_DATA_BIDIR = "data_bidir"
SIGFOX_CALLBACK_TYPE_SERVICE_STATUS = "service_status"
SIGFOX_CALLBACK_TYPE_SERVICE_ACKNOWLEDGE = "service_acknowledge"

# Boolean types.
JSON_TRUE = "true"
JSON_FALSE = "false"