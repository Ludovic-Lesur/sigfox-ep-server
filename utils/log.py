"""
* log.py
*
*  Created on: 17 nov. 2021
*      Author: Ludo
"""

import datetime
import time

### LOG classes ###

class Log:

    _enabled = False

    @classmethod
    def enable(cls) -> None:
        cls._enabled = True

    @staticmethod
    def debug_print(message: str) -> None:
        if Log._enabled:
            log_timestamp = datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S') + " *** "
            print(log_timestamp + message)