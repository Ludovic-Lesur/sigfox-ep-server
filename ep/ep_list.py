"""
* ep_list.py
*
*  Created on: 28 jul. 2026
*      Author: Ludo & Copilot
"""

from database.database import *
import json
from typing import Dict, List, Optional, Type

### EP LIST local macros ###

SIGFOX_EP_LIST_FILE_NAME = "/home/ludo/git/sigfox-ep-server/sigfox_ep_list.json"

### EP LIST classes ###

class EpList:
    
    def __init__(self) -> None:
        # Local variables.
        self.device_types: Dict[str, List[Dict]] = {}
        self.device_class_map: Dict[str, Type] = {}
        # Load devices list.
        try:
            # Open file.
            sigfox_ep_list_file = open(SIGFOX_EP_LIST_FILE_NAME, "r")
            ep_list_json = json.load(sigfox_ep_list_file)
            sigfox_ep_list_file.close()
            Log.debug_print("[SIGFOX EP SERVER] * Downlink messages file found")
            # Check content.
            if not isinstance(ep_list_json, dict):
                raise Exception
            # Read devices list.
            for device_type, items in ep_list_json.items():
                if not isinstance(items, list):
                    raise Exception
                self.device_types[device_type] = []
                for item in items:
                    if not isinstance(item, dict):
                        raise Exception
                    sigfox_ep_id = item.get(DATABASE_TAG_SIGFOX_EP_ID)
                    if not sigfox_ep_id:
                        raise Exception
                    meta = dict(item)
                    meta[DATABASE_TAG_SIGFOX_EP_ID] = EpList.format_sigfox_ep_id(sigfox_ep_id)
                    self.device_types[device_type].append(meta)
        except:
            return    
    
    def get_devices(self, device_type: str) -> List[Dict]:
        return list(self.device_types.get(device_type, []))

    def get(self, device_type: str, tag: str) -> Optional[Dict]:
        return [d[tag] for d in self.get_devices(device_type)]
    
    @staticmethod
    def format_sigfox_ep_id(sigfox_ep_id) -> str:
        try:
            # Convert to integer.
            if isinstance(sigfox_ep_id, int):
                value = sigfox_ep_id
            else:
                s = str(sigfox_ep_id).strip()
                # Remove prefix.
                if s.lower().startswith("0x"):
                    s = s[2:]
                value = int(s, 16)
            # Check range
            if value < 0 or value > 0xFFFFFFFF:
                raise Exception
        except:
            value = 0
        return f"{value:08X}"
    
# Init shared class instance.
ep_list = EpList()
    