"""
* test.py
*
*  Created on: 23 oct. 2022
*      Author: Ludo
"""

import requests
import time

from typing import List
from utils.defs import *

# HTTP server.
SIGFOX_EP_SERVER_ADDRESS = SIGFOX_EP_SERVER_LOCAL_ADDRESS + ":" + str(SIGFOX_EP_SERVER_HTTP_PORT)
SIGFOX_EP_SERVER_REQUEST_DELAY_SECONDS = 0.1

METEOFOX_TEST_REQUEST = [
    # MeteoFox old startup data.
    [SIGFOX_CALLBACK_TYPE_SERVICE_STATUS, "53b5"],
    # MeteoFox startup data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "53b5", "1401041175753760", JSON_FALSE],
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "5436", "1406050075753760", JSON_FALSE],
    # MeteoFox monitoring data without error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "53b5", "10173d3d4ca45d387e", JSON_FALSE],
    # MeteoFox monitoring data with error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "53b5", "117f401830a43d593f", JSON_FALSE],
    # MeteoFox geoloc data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "53b5", "2b81e249017a1cbf00a653", JSON_FALSE],
    # MeteoFox IM weather data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "53b5", "183a03002726", JSON_FALSE],
    # MeteoFox CM weather data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "53b5", "1456030026c804185707", JSON_FALSE],
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "5436", "1456030026c804185707", JSON_FALSE],
    # MeteoFox geoloc timeout data V1.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "53b5", "78", JSON_FALSE],
    # MeteoFox geoloc timeout data V2.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "53b5", "210e40", JSON_FALSE],
    # MeteoFox geoloc timeout data V3.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "53b5", "0178", JSON_FALSE],
    # MeteoFox error stack data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "53b5", "270d00000000000000000000", JSON_FALSE],
    # MeteoFox invalid Sigfox EP-ID.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "0123", "050c3900f29d1d2f7f", JSON_FALSE],
    # MeteoFox invalid data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "53b5", "01020304", JSON_FALSE]
]

SENSIT_TEST_REQUEST = [
    # Sensit monitoring data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "86bd75", "ae096e97", JSON_FALSE],
    # Sensit configuration data
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "86bd75", "b609759846003f0f8004223c", JSON_TRUE],
    # Sensit invalid data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "86bd75", "010203", JSON_FALSE],
    # Sensit invalid Sigfox EP-ID.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "012345", "050c3900f29d", JSON_FALSE]
]

ATXFOX_TEST_REQUEST = [
    # ATXFox startup data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "868e", "1c020201749a0be1", JSON_FALSE],
    # ATXFox monitoring data without error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "868e", "2fa302063bad0d5f1d", JSON_FALSE],
    # ATXFox monitoring data with error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "868e", "0d9903ffffff0d611e", JSON_FALSE],
    # ATXFox error stack data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "868e", "1d031d031d03000000000000", JSON_FALSE],
    # ATXFox invalid Sigfox EP-ID.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "0123", "050c3900f29d1d2f7f", JSON_FALSE],
    # ATXFox invalid data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "868e", "010203", JSON_FALSE]
]

TRACKFOX_TEST_REQUEST = [
    # TrackFox startup data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4257", "0c010601fd3256e0", JSON_FALSE],
    # TrackFox monitoring data without error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4257", "163b12a5094f74", JSON_FALSE],
    # TrackFox monitoring data with error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4257", "16ff0007094e7c", JSON_FALSE],
    # TrackFox geoloc data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4257", "2b883feb017084a7009606", JSON_FALSE],
    # TrackFox geoloc timeout data V2.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4257", "210f08", JSON_FALSE],
    # MeteoFox geoloc timeout data V3.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4257", "0250", JSON_FALSE],
    # TrackFox error stack data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4257", "1f0200000000000000000000", JSON_FALSE],
    # TrackFox invalid Sigfox EP-ID.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "0123", "121203138e7bc6f0", JSON_FALSE],
    # TrackFox invalid data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4257", "01020304", JSON_FALSE]
]

DINFOX_TEST_REQUEST = [
    # DINFox startup data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4761", "00081c00020c06b1ce60", JSON_FALSE],
    # DINFox LVRM monitoring payload without error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4761", "20000bb90104", JSON_FALSE],
    # DINFox LVRM monitoring payload with error.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4761", "2000ffff0104", JSON_FALSE],
    # DINFox LVRM electrical payload without error
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4761", "200000000007000000", JSON_FALSE],
    # DINFox BPSM monitoring payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4761", "02010bbd0918", JSON_FALSE],
    # DINFox BPSM electrical payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "47ea", "020100070ac835fb00", JSON_TRUE],
    # Network acknowledge.
    [SIGFOX_CALLBACK_TYPE_SERVICE_ACKNOWLEDGE, "47a7", "020C0F0030001000", JSON_TRUE, "0"],
    # DinFox action log payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4761", "2100fd510c0000000180", JSON_FALSE],
    # DINFox DDRM monitoring payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "47a7", "29020bb90118", JSON_FALSE],
    # DINFox DDRM electrical payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "47a7", "290200000b04000000", JSON_FALSE],
    # DINFox UHFM monitoring payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4761", "03030bb600e60b480bb700", JSON_FALSE],
    # DINFox GPSM monitoring payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4761", "04040bb800fa0bb00bb700", JSON_FALSE],
    # DINFox SM monitoring payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4761", "05050bb20110", JSON_FALSE],
    # DINFox SM electrical payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4761", "05050123ffff023404560b", JSON_FALSE],
    # DINFox SM sensor payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4761", "050500cf33", JSON_FALSE],
    # DINFox DMM monitoring payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4761", "000814290bb8000008", JSON_FALSE],
    # DINFox DMM error stack data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4761", "0008200f2010201120122013", JSON_FALSE],
    # DINFox R4S8CR electrical payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "479c", "700ac981", JSON_FALSE],
    # DINFox invalid Sigfox EP-ID.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "0123", "20000bb91a", JSON_FALSE],
    # DINFox invalid data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "4761", "2000", JSON_FALSE],
    # DINFox MPMCM status payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "47ea", "060929", JSON_FALSE],
    # DINFox MPMCM electrical mains voltage payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "47ea", "060904892d892f893b", JSON_FALSE],
    # DINFox MPMCM electrical mains frequency payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "47ea", "0609138213841393", JSON_FALSE],
    # DINFox MPMCM electrical mains power payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "47ea", "060900072c08c00b050dd8", JSON_FALSE],
    # DINFox MPMCM electrical mains power factor payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "47ea", "060903c2c2cf", JSON_FALSE],
    # DINFox MPMCM electrical mains energy payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "47ea", "0609031c231c41", JSON_FALSE],
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "47ea", "06090203330444", JSON_FALSE],
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "47ea", "0609041c001b00", JSON_FALSE],
    # DINFox BCM monitoring payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "47ea", "070b0bb21c", JSON_FALSE],
    # DINFox BCM electrical payload.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "47ea", "070b051232ba19b8137d0a", JSON_FALSE]
]

HOMEFOX_TEST_REQUEST = [
    # HomeFox startup data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1230", "140008027f1dfa90", JSON_FALSE],
    # HomeFox monitoring data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1230", "0f9700cd407d", JSON_FALSE],
    # HomeFox air quality data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1230", "002101a44a6b2a", JSON_FALSE],
    # HomeFox motion data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1230", "a0", JSON_FALSE],
    # HomeFox error stack data.
    [SIGFOX_CALLBACK_TYPE_DATA_BIDIR, "1230", "371700000000000000000000", JSON_FALSE],
]

### TEST classes ###

class Test:

    @staticmethod
    def make(log_message: str, request_table: List[str]) -> None:
        # Local variables.
        json_from_backend = []
        print(log_message)
        # Requests loop.
        for idx in range(len(request_table)):
            # Get callback type.
            callback_type = request_table[idx][0]
            # Create JSON body.
            json_from_backend = {
                SIGFOX_CALLBACK_JSON_HEADER_TYPE: callback_type,
                SIGFOX_CALLBACK_JSON_HEADER_TIME: str(int(time.time() + idx)),
                SIGFOX_CALLBACK_JSON_HEADER_EP_ID: request_table[idx][1],
                SIGFOX_CALLBACK_JSON_HEADER_MESSAGE_COUNTER: str(idx)
            }
            # Check callback type.
            if (callback_type == SIGFOX_CALLBACK_TYPE_DATA_BIDIR):
                # Data bidirectional.
                json_from_backend[SIGFOX_CALLBACK_JSON_HEADER_UL_PAYLOAD] = request_table[idx][2]
                json_from_backend[SIGFOX_CALLBACK_JSON_HEADER_BIDIRECTIONAL_FLAG] = request_table[idx][3]
            elif (callback_type == SIGFOX_CALLBACK_TYPE_SERVICE_ACKNOWLEDGE):
                # Service acknowledge.
                json_from_backend[SIGFOX_CALLBACK_JSON_HEADER_DL_PAYLOAD] = request_table[idx][2]
                json_from_backend[SIGFOX_CALLBACK_JSON_HEADER_DL_SUCCESS] = request_table[idx][3]
                json_from_backend[SIGFOX_CALLBACK_JSON_HEADER_DL_STATUS] = request_table[idx][4]
            # Post request.
            response = requests.post(SIGFOX_EP_SERVER_ADDRESS, json = json_from_backend)
            print("Sending request " + str(idx) + response.text)
            time.sleep(SIGFOX_EP_SERVER_REQUEST_DELAY_SECONDS)

### TEST main function ###

if __name__ == "__main__":
    # Perform all devices types test.
    Test.make("METEOFOX requests test", METEOFOX_TEST_REQUEST)
    Test.make("SENSIT requests test", SENSIT_TEST_REQUEST)
    Test.make("ATXFOX requests test", ATXFOX_TEST_REQUEST)
    Test.make("TRACKFOX requests test", TRACKFOX_TEST_REQUEST)
    Test.make("DINFOX requests test", DINFOX_TEST_REQUEST)
    Test.make("HOMEFOX requests test", HOMEFOX_TEST_REQUEST)
