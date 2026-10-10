"""
* meteofox_lux_uvi_calibration.py
*
*  Created on: 11 aug. 2026
*      Author: Ludo
"""

import csv
import os
import requests
import json
import subprocess
import sys
import time

from datetime import datetime
from pathlib import Path
from typing import Iterable, Tuple, Union
from utils.sigfox_cloud import *

### METEOFOX LUX UVI CALIBRATION macros ###

SIGFOX_CLOUD_API_REQUEST_DELAY_SECONDS = 1.1

METEOFOX_ERROR_VALUE_SUNSHINE_LIGHT_V3 = 0xFFFF
METEOFOX_ERROR_VALUE_SUNSHINE_UV_INDEX_V3 = 0x7F

### METEOFOX LUX UVI CALIBRATION classes ###

class MeteoFoxLuxUviCalibration:
    
    @staticmethod
    def convert_lux(lux_raw: int) -> float:
        # Sunshine light.
        unit = ((lux_raw >> 14) & 0x0003)
        lux = (lux_raw & 0x3FFF)
        if (unit == 0):
            sunshine_light = float(lux / 100.0)
        elif (unit == 1):
            sunshine_light = float(lux / 10.0)
        elif (unit == 2):
            sunshine_light = float(lux / 1.0)
        else:
            sunshine_light = float(lux * 10.0)
        return sunshine_light
            
    @staticmethod
    def convert_uvi(uvi_raw: int) -> float:
        # Sunshine UV index.
        return float(uvi_raw / 10.0)
           
    @staticmethod
    def read_all_sigfox_messages(sigfox_ep_id: str, timestamp_start_epoch_ms: int, timestamp_stop_epoch_ms: int, csv_file_name: str) -> None:
        # Print.
        print("Reading all Sigfox messages of device " + sigfox_ep_id + "...")
        # Create CSV file.
        file = open(csv_file_name, 'w', newline='', encoding='utf-8')
        writer = csv.writer(file)
        writer.writerow(['time', 'si1133_lux', 'ltr390_lux', 'veml6031_lux', 'si1133_uvi', 'ltr390_uvi', 'guva_uvi_mv'])
        # Build request.
        parameters = {
            SIGFOX_CLOUD_API_JSON_KEY_START_TIME: timestamp_start_epoch_ms,
            SIGFOX_CLOUD_API_JSON_KEY_STOP_TIME: timestamp_stop_epoch_ms
        }
        request = SIGFOX_CLOUD_API_ADDRESS + SIGFOX_CLOUD_API_REQUEST_DEVICES + sigfox_ep_id + "/" + SIGFOX_CLOUD_API_REQUEST_MESSAGES
        # Paging loop.
        while (str(request) != SIGFOX_CLOUD_API_REQUEST_NONE):
            # API request.
            response = sigfox_cloud.api_request(request, parameters, SIGFOX_CLOUD_API_REQUEST_DELAY_SECONDS)
            if ((response == None) or (response.status_code != 200)):
                break
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
            # Messages loop.
            for message in messages_list:
                timestamp = int(message.get(SIGFOX_CLOUD_API_JSON_KEY_TIME))
                ul_payload = message.get(SIGFOX_CLOUD_API_JSON_KEY_UL_PAYLOAD)
                si1133_lux_str = ''
                si1133_uvi_str = ''
                veml6031_lux_str = ''
                ltr390_lux_str = ''
                ltr390_uvi_str = ''
                guva_uvi_str = ''
                data_found = False
                # Weather data frame.
                if ((len(ul_payload) == 14) or (len(ul_payload) == 24)):
                    # SI1133 light
                    si1133_lux_raw = ((int(ul_payload[4:9], 16) >> 1) & 0xFFFF)
                    if (si1133_lux_raw != METEOFOX_ERROR_VALUE_SUNSHINE_LIGHT_V3):
                        si1133_lux_str = str(MeteoFoxLuxUviCalibration.convert_lux(si1133_lux_raw))
                        data_found = True
                    # SI1133 UV index.
                    si1133_uvi_raw = ((int(ul_payload[8:11], 16) >> 2) & 0x7F)
                    if (si1133_uvi_raw != METEOFOX_ERROR_VALUE_SUNSHINE_UV_INDEX_V3):
                        si1133_uvi_str = str(MeteoFoxLuxUviCalibration.convert_uvi(si1133_uvi_raw))
                        data_found = True
                # Lux test frame.
                elif (len(ul_payload) == 8):
                    # VEML6031 light.
                    veml6031_lux_raw = (int(ul_payload[0:4], 16) & 0xFFFF)
                    if (veml6031_lux_raw != METEOFOX_ERROR_VALUE_SUNSHINE_LIGHT_V3):
                        veml6031_lux_str = str(MeteoFoxLuxUviCalibration.convert_lux(veml6031_lux_raw))
                        data_found = True
                    # LTR390 light.
                    ltr390_lux_raw = (int(ul_payload[4:8], 16) & 0xFFFF)
                    if (ltr390_lux_raw != METEOFOX_ERROR_VALUE_SUNSHINE_LIGHT_V3):
                        ltr390_lux_str = str(MeteoFoxLuxUviCalibration.convert_lux(ltr390_lux_raw))
                        data_found = True
                # UV index test frame.
                elif (len(ul_payload) == 6):
                    # LTR390 UV index.
                    ltr390_uvi_raw = (int(ul_payload[0:2], 16) & 0xFFFF)
                    if (ltr390_uvi_raw != METEOFOX_ERROR_VALUE_SUNSHINE_UV_INDEX_V3):
                        ltr390_uvi_str = str(MeteoFoxLuxUviCalibration.convert_uvi(ltr390_uvi_raw))
                        data_found = True
                    # GUVA UV index.
                    guva_uvi_raw = (int(ul_payload[2:6], 16) & 0xFFFF)
                    if (guva_uvi_raw != 0xFFFF):
                        guva_uvi_str = str(guva_uvi_raw)
                        data_found = True
                # Check if all data has been retrieved.
                if (data_found == True):
                    # Write point.
                    writer.writerow([timestamp, si1133_lux_str, ltr390_lux_str, veml6031_lux_str, si1133_uvi_str, ltr390_uvi_str, guva_uvi_str])
        file.close()
    
    @staticmethod
    def run_octave_script(script_path: str, csv_ref: str, csv_dut: str, output_directory=None, tolerance_seconds=60, show_plots=False, timeout=300) -> None:
        # Check input files.
        for f in [csv_ref, csv_dut]:
            if not os.path.exists(f):
                raise FileNotFoundError(f'CSV file not found : {f}')
        # Build command line.
        cmd = [ 'octave', '--no-gui', '-q', script_path, csv_ref, csv_dut, '--tol', str(tolerance_seconds) ]
        if not show_plots:
            cmd.append('--no-plot')
        if output_directory:
            cmd.extend(['--save', output_directory])
        print("Calibration...")
        print(f'{" ".join(cmd)}')
        # Execute command.
        try:
            result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=timeout)
            # Print output.
            if result.stdout:
                print(result.stdout)
            if result.returncode != 0:
                raise RuntimeError(f'Octave script error: {result.returncode}')
            return { 'success': True, 'stdout': result.stdout, 'stderr': result.stderr, 'returncode': result.returncode }
        except subprocess.TimeoutExpired:
            print(f'Octave script timeout ({timeout} seconds)', file=sys.stderr)
            return {'success': False, 'error': 'timeout'}
        except Exception as e:
            print(f'Execution error : {e}', file=sys.stderr)
            return {'success': False, 'error': str(e)}
        
### MAIN PROGRAM ###

print("*******************************************************")
print("------- MeteoFox LUX and UVI calibration script -------")
print("*******************************************************")
print("")

# Read timestamps
sigfox_ep_id_ref = input("Sigfox EP ID REF = ")
sigfox_ep_id_dut = input("Sigfox EP ID DUT = ")
timestamp_start_epoch_ms = input("Start time (EPOCH ms) = ")
timestamp_stop_epoch_ms = input("Stop time (EPOCH ms) = ")
output_directory = input("Output directory = ")
if (timestamp_stop_epoch_ms == "now"):
    timestamp_stop_epoch_ms = str(int(time.time() * 1000))
# Create output directory.
results_directory = output_directory + "/meteofox_lux_uvi_calibration_" + sigfox_ep_id_dut
if output_directory and not os.path.exists(results_directory):
    os.makedirs(results_directory)
# Build files name.
csv_ref = results_directory + "/meteofox_lux_uvi_calibration_ref_" + sigfox_ep_id_ref + ".csv"
csv_dut = results_directory + "/meteofox_lux_uvi_calibration_dut_" + sigfox_ep_id_dut + ".csv"
script_path = "utils/meteofox_lux_uvi_calibration.m"
# Read all messages.
print("")
MeteoFoxLuxUviCalibration.read_all_sigfox_messages(sigfox_ep_id_ref, timestamp_start_epoch_ms, timestamp_stop_epoch_ms, csv_ref)
MeteoFoxLuxUviCalibration.read_all_sigfox_messages(sigfox_ep_id_dut, timestamp_start_epoch_ms, timestamp_stop_epoch_ms, csv_dut)
# Call Octave script.
print("")
result = MeteoFoxLuxUviCalibration.run_octave_script(script_path, csv_ref, csv_dut, results_directory)
if result['success']:
    print('✓ Calibration réussie')
else:
    print(f'✗ Calibration échouée : {result.get("error")}')
# End print.
print("")
print("*************************************")
sys.exit()
