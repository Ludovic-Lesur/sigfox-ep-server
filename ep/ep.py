"""
* ep.py
*
*  Created on: 28 jul. 2026
*      Author: Ludo & Copilot
"""

from database.database import *
import json
from typing import Dict, List, Optional, Type
from utils.configuration import *

### EP LIST local macros ###

EP_LIST_FILE_NAME = os.path.join(SIGFOX_EP_SERVER_PATH, "sigfox_ep_list.json")

### EP LIST classes ###

class Ep:

    def __init__(self) -> None:
        # Init context.
        self._device_types: Dict[str, List[Dict]] = {}
        # Load devices list.
        try:
            # Open file.
            sigfox_ep_list_file = open(EP_LIST_FILE_NAME, "r")
            ep_list_json = json.load(sigfox_ep_list_file)
            sigfox_ep_list_file.close()
            # Check content.
            if not isinstance(ep_list_json, dict):
                raise Exception
            # Read devices list.
            for device_type, items in ep_list_json.items():
                if not isinstance(items, list):
                    raise Exception
                self._device_types[device_type] = []
                for item in items:
                    if not isinstance(item, dict):
                        raise Exception
                    sigfox_ep_id = item.get(DATABASE_TAG_SIGFOX_EP_ID)
                    if not sigfox_ep_id:
                        raise Exception
                    meta = dict(item)
                    meta[DATABASE_TAG_SIGFOX_EP_ID] = Ep.format_sigfox_ep_id(sigfox_ep_id)
                    self._device_types[device_type].append(meta)
        except:
            return

    def _get_devices_list(self, device_type: str) -> List[Dict]:
        return list(self._device_types.get(device_type, []))

    def get_sigfox_ep_id_list(self) -> List[str]:
        ep_id_list: List[str] = []
        for device_list in self._device_types.values():
            for device in device_list:
                ep_id_list.append(device[DATABASE_TAG_SIGFOX_EP_ID])
        return ep_id_list

    def get_tags_list(self, device_type: str, tag: str) -> Optional[Dict]:
        return [d[tag] for d in self._get_devices_list(device_type)]

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
ep = Ep()
    