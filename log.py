import datetime
import time

### LOCAL MACROS ###

# Enable or disable debug prints.
__LOG = True

### PUBLIC FUNCTIONS ###

# Function to print a log line.
def LOG_print(message) :
    if (__LOG == True) :
        print(message)

# Function to print a log line with timestamp.
def LOG_print_timestamp(message) :
    log_timestamp = datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S') + " *** "
    if (__LOG == True) :
        print(log_timestamp + message)
