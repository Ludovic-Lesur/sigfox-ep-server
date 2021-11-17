import datetime
import time

### MACROS ###

# Enable or disable debug prints.
LOG = False

### FUNCTIONS ###

# Function to get current timestamp in pretty format.
def LOG_GetCurrentTimestamp():
    return datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S') + " *** "