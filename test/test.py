from __future__ import print_function
import requests
import time

# HTTP server port.
SIGFOX_EP_SERVER_HTTP_ADDRESS = "http://localhost:65000"
SIGFOX_EP_SERVER_HTTP_REQUEST_DELAY_SECONDS = 0.1

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

# Old OOB data.
COMMON_UL_PAYLOAD_KEEP_ALIVE = "keep_alive"

METEOFOX_TEST_REQUEST = [
    # MeteoFox old startup data.
    [SIGFOX_CALLBACK_TYPE_SERVICE_STATUS, "1666374000", "53b5"],
    # MeteoFox startup data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374001", "53b5", "1", "1401041175753760", "false"],
    # MeteoFox monitoring data without error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374002", "53b5", "2", "10173d3d4ca45d387e", "false"],
    # MeteoFox monitoring data with error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374003", "53b5", "3", "117f401830a43d593f", "false"],
    # MeteoFox geoloc data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374006", "53b5", "4", "2b81e249017a1cbf00a653", "false"],
    # MeteoFox IM weather data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374004", "53b5", "5", "183a03002726", "false"],
    # MeteoFox CM weather data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374005", "53b5", "6", "1456030026c804185700", "false"],
    # MeteoFox geoloc timeout data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374007", "53b5", "7", "78", "false"],
    # MeteoFox error stack data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374008", "53b5", "8", "270d00000000000000000000", "false"],
    # MeteoFox invalid Sigfox EP-ID.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374009", "0123", "9", "050c3900f29d1d2f7f", "false"],
    # MeteoFox invalid data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374010", "53b5", "10", "010203", "false"]
]

SENSIT_TEST_REQUEST = [
    # Sensit monitoring data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374100", "b437b2", "100", "ae096e97", "false"],
    # Sensit configuration data
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374101", "b437b2", "101", "b609759846003f0f8004223c", "false"],
    # MeteoFox invalid Sigfox EP-ID.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374102", "0123", "102", "050c3900f29d", "false"],
    # MeteoFox invalid data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374103", "b437b2", "103", "010203", "false"]
]

ATXFOX_TEST_REQUEST = [
    # ATXFox startup data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374200", "868e", "200", "1c020201749a0be1", "false"],
    # ATXFox startup data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374201", "868e", "201", "01", "false"],
    # ATXFox shutdown data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374202", "868e", "202", "00", "false"],
    # ATXFox invalid data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374203", "868e", "203", "31", "false"],
    # ATXFox monitoring data without error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374204", "868e", "204", "2fa302063bad0d5f1d", "false"], 
    # ATXFox monitoring data with error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374205", "868e", "205", "0d9903ffffff0d611e", "false"],
    # ATXFox error stack data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374206", "868e", "206", "1d031d031d03000000000000", "false"],
    # ATXFox invalid Sigfox EP-ID.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374207", "abcd", "207", "050c3900f29d1d2f7f", "false"],
    # ATXFox invalid data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374208", "868e", "208", "010203", "false"]
]

TRACKFOX_TEST_REQUEST = [
    # TrackFox startup data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374300", "4257", "300", "0c010601fd3256e0", "false"],
    # TrackFox monitoring data without error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374301", "4257", "301", "1741180000a55bca7c", "false"],
    # TrackFox monitoring data with error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374302", "4257", "302", "17ff180000a55bca7c", "false"],
    # TrackFox geoloc data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374303", "4257", "303", "2b883feb017084a7009606", "false"],
    # TrackFox geoloc timeout data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374304", "4257", "304", "210f08", "false"],
    # TrackFox error stack data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374305", "4257", "305", "1f0200000000000000000000", "false"],
    # TrackFox invalid Sigfox EP-ID.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374306", "aabb", "306", "121203138e7bc6f0", "false"],
    # TrackFox invalid data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374307", "4257", "307", "010203", "false"]
]

DINFOX_TEST_REQUEST = [
    # DINFox DMM startup data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374400", "4761", "400", "00081c00020c06b1ce60", "false"],
    # DINFox LVRM monitoring payload without error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374401", "4761", "401", "20000bb91a", "false"],
    # DINFox LVRM monitoring payload with error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374402", "4761", "402", "2000ffff1a", "false"],
    # DINFox LVRM electrical payload without error
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374403", "4761", "403", "200000000007000000", "false"],
    # DINFox BPSM monitoring payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374404", "4761", "404", "08010bbd1c", "false"],
    # DINFox BPSM electrical payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374405", "47ea", "405", "080100070ac835fb00", "true"],
    # Network acknowledge.
    [SIGFOX_CALLBACK_TYPE_SERVICE_ACKNOWLEDGE, "1666374405", "47a7", "020C0F0030001000", "true", "0"],
    # DINFox DDRM monitoring payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374406", "47a7", "406", "31020bb91c", "false"],
    # DINFox DDRM electrical payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374407", "47a7", "407", "310200000b04000000", "false"],
    # DINFox UHFM monitoring payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374408", "4761", "408", "0c030bb6170b480bb7", "false"],
    # DINFox GPSM monitoring payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374409", "4761", "409", "10040bb8190bb00bb7", "false"],
    # DINFox SM monitoring payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374410", "4761", "410", "14050bb21c", "false"],
    # DINFox SM electrical payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374411", "4761", "411", "14050123ffff023404560b", "false"],
    # DINFox SM sensor payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374412", "4761", "412", "14051433", "false"],
    # DINFox DMM monitoring payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374413", "4761", "413", "000814290bb8000008", "false"],
    # DINFox R4S8CR electrical payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374414", "479c", "414", "700ac981", "false"],
    # DINFox invalid Sigfox EP-ID.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374415", "aabb", "415", "20000bb91a", "false"],
    # DINFox invalid data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374416", "4761", "416", "2000", "false"],
    # DINFox DMM error stack data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374417", "4761", "417", "0008200f200f000000000000", "false"],
    # DINFox MPMCM electrical mains voltage payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374418", "47ea", "418", "1c0911892d892f893b", "false"],
    # DINFox MPMCM electrical mains frequency payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374419", "47ea", "419", "1c09138213841393", "false"],
    # DINFox MPMCM electrical mains power payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374420", "47ea", "420", "1c0900072c08c00b050dd8", "false"],
    # DINFox MPMCM electrical mains power factor payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1666374421", "47ea", "421", "1c0903c2c2cf", "false"]
]

# Function to send a test requests list.
def TEST_make(log_message, request_table):
    # Loval variables.
    json_from_backend = []
    print(log_message)
    for idx in range(len(request_table)) :
        # Check callback type.
        callback_type = request_table[idx][0]
        if (callback_type == SIGFOX_CALLBACK_TYPE_DATA_BIDIR) :
            # Create JSON body.
            json_from_backend = {
                SIGFOX_CALLBACK_JSON_HEADER_TYPE : request_table[idx][0],
                SIGFOX_CALLBACK_JSON_HEADER_TIME : request_table[idx][1],
                SIGFOX_CALLBACK_JSON_HEADER_EP_ID : request_table[idx][2],
                SIGFOX_CALLBACK_JSON_HEADER_MESSAGE_COUNTER : request_table[idx][3],
                SIGFOX_CALLBACK_JSON_HEADER_UL_PAYLOAD : request_table[idx][4],
                SIGFOX_CALLBACK_JSON_HEADER_BIDIRECTIONAL_FLAG : request_table[idx][5]
            }
        elif (callback_type == SIGFOX_CALLBACK_TYPE_SERVICE_ACKNOWLEDGE) :
            # Create JSON body.
            json_from_backend = {
                SIGFOX_CALLBACK_JSON_HEADER_TYPE : request_table[idx][0],
                SIGFOX_CALLBACK_JSON_HEADER_TIME : request_table[idx][1],
                SIGFOX_CALLBACK_JSON_HEADER_EP_ID : request_table[idx][2],
                SIGFOX_CALLBACK_JSON_HEADER_DL_PAYLOAD : request_table[idx][3],
                SIGFOX_CALLBACK_JSON_HEADER_DL_SUCCESS : request_table[idx][4],
                SIGFOX_CALLBACK_JSON_HEADER_DL_STATUS : request_table[idx][5]
            }
        elif (callback_type == SIGFOX_CALLBACK_TYPE_SERVICE_STATUS) :
            # Create JSON body.
            json_from_backend = {
                SIGFOX_CALLBACK_JSON_HEADER_TYPE : request_table[idx][0],
                SIGFOX_CALLBACK_JSON_HEADER_TIME : request_table[idx][1],
                SIGFOX_CALLBACK_JSON_HEADER_EP_ID : request_table[idx][2],
            }
        r = requests.post(SIGFOX_EP_SERVER_HTTP_ADDRESS, json=json_from_backend)
        print("Sending request " + str(idx) + r.text)
        time.sleep(SIGFOX_EP_SERVER_HTTP_REQUEST_DELAY_SECONDS)
        
### MAIN PROGRAM ###

TEST_make("METEOFOX requests test", METEOFOX_TEST_REQUEST)
TEST_make("SENSIT requests test", SENSIT_TEST_REQUEST)
TEST_make("ATXFOX requests test", ATXFOX_TEST_REQUEST)
TEST_make("TRACKFOX requests test", TRACKFOX_TEST_REQUEST)
TEST_make("DINFOX requests test", DINFOX_TEST_REQUEST)
