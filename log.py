"""
* log.py
*
*  Created on: 17 nov. 2021
*      Author: Ludo
"""

import datetime
import time

### LOG local macros ###

LOG_ENABLE = False

### LOG classes ###

class Log:

    @staticmethod
    def debug_print(message):
        if (LOG_ENABLE == True):
            log_timestamp = datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S') + " *** "
            print(log_timestamp + message)
