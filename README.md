## Description

This project is a Python server dedicated to Sigfox applications, implementing the following features:

* **Sigfox cloud callbacks** processing: uplink, bidirectional, data advanced and service.
* Dynamic **radio payloads parsing** for multiple device types.
* **Data storage** in **InfluxDB**.
* Dynamic **downlink messages processing** (managed with the [sigfox-ep-dl-interface](https://github.com/Ludovic-Lesur/sigfox-ep-dl-interface))

## Architecture

<p align="center">
<img src="https://github.com/Ludovic-Lesur/sigfox-ep-server/wiki/images/sigfox-ep-server-architecture.drawio.png"/>
</p>

## Installation

### System update

```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get autoremove
```

### Influx DB

```bash
wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add -
source /etc/lsb-release
echo "deb https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" \
     | sudo tee /etc/apt/sources.list.d/influxdb.list
sudo apt-get update
sudo apt-get install influxdb
sudo systemctl unmask influxdb.service
sudo systemctl start influxdb
```

Edit the `/etc/influxdb/influxdb.conf` configuration file: in the **HTTP** section, uncomment `enabled = true`, `bind address` and `auth_enabled` lines.

Examples of data requests:

```bash
influx
USE meteofox_db
SELECT rainfall FROM weather WHERE sigfox_ep_id='00005477'
INSERT weather,sigfox_ep_id=0000549D,site=Labege \
       rainfall=0.0 1597831208000000000
INSERT electrical,sigfox_ep_id=00004761,system=Test_bench,node_address=33,\
       node=LVRM_1,board_id=0 \
       output_current=0.0 1701853317000000000
INSERT monitoring,sigfox_ep_id=000053B5,site=Proto_HW1.0 \
       storage_voltage=2620.0 1597831208000000000
```

### Server

Install the required Python packages:

```bash
sudo apt install python3-pip
pip3 install requests
pip3 install HTTPServer
pip3 install influxdb
```

Install the server:

```bash
mkdir git
cd git
git clone https://github.com/Ludovic-Lesur/sigfox-ep-server.git
```

### Configuration file

In the `sigfox-ep-server` root folder, create the `sigfox_ep_server.json` configuration file, according to the following structure:

```json
{
    "path": "<sigfox-ep-server path>",
    "http_port": <port>,
    "api_key": "<api_key>",
    "sigfox_cloud": {
        "user": "<user>",
        "password": "<password>"
    },
    "dl_messages_file_path": "<sigfox_ep_dl_messages.json path>"
}
```

### Devices tree

In the `sigfox-ep-server` root folder, create the `sigfox_ep_list.json` file containing the list of registered devices, according to the following structure:

```json
{
    "<ep1>": [
        { "sigfox_ep_id": "<id1>", "<tag>": "<value1>" },
        { "sigfox_ep_id": "<id2>", "<tag>": "<value2>" }
    ],
    "<ep2>": [
        { "sigfox_ep_id": "<id3>", "<tag>": "<value3>" },
        { "sigfox_ep_id": "<id4>", "<tag>": "<value4>" }
    ],
    ...
}
```

### Service file

```bash
cd git/sigfox_ep_server
sudo cp sigfox_ep_server.service /lib/systemd/system
```

Edit the copied service file by replacing the `<user>` and `<absolute_path>` fields.

```bash
sudo systemctl daemon-reload
sudo service sigfox_ep_server start
```

## Update

### Server

```bash
cd git/sigfox_ep_server
sudo service sigfox_ep_server stop
git pull
sudo service sigfox_ep_server start
```

### Configuration and devices tree

```bash
sudo scp -P <port> sigfox_ep_server.json <user>@<server>:<sigfox-ep-server path>
sudo scp -P <port> sigfox_ep_list.json <user>@<server>:<sigfox-ep-server path>
```

## API

### Authentication

All requests must include the following header:

| Header | Value |
|---|---|
| `X-API-Key` | API key defined in the `sigfox_ep_server.json` configuration file |

### Read the last data of a device

```bash
GET /ep/<ep>/latest?<parameters>
```

| Parameters | Type | Description | Values |
|---|---|---|---|
| `<ep>` | string | Group of the device | `atxfox` `dinfox` `homefox` `meteofox` `sensit` `smarttag` `trackfox` |
| `<tag>` | string | Tag(s) to identify the device | |
| `measurement` | string | Measurement of the field to read | See [database class](https://github.com/Ludovic-Lesur/sigfox-ep-server/blob/master/database/database.py) |
| `field` | string | Data field to read | See [database class](https://github.com/Ludovic-Lesur/sigfox-ep-server/blob/master/database/database.py) |
