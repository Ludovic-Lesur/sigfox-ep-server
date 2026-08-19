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

### Grafana

```bash
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana
sudo service grafana-server start
```

Edit the `/etc/grafana/grafana.ini` configuration file: in the **Server** section, uncomment `protocol = http` and set `http_port=<grafana_port>`.

Required plugins installation:

```bash
sudo grafana-cli plugins install grafana-clock-panel
sudo grafana-cli plugins install grafana-worldmap-panel
sudo grafana-cli plugins install fatcloud-windrose-panel
```

Copy the images to be used in Grafana in the dedicated folder:

```bash
sudo cp ./grafana/images/x.png /usr/share/grafana/public/img/
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
cd git
git clone https://github.com/Ludovic-Lesur/sigfox-ep-server.git
cd sigfox-ep-server
```

### Configuration file

Create the following `sigfox_ep_server.json` configuration file in the `sigfox-ep-server` root folder:

```json
{
    "path": <sigfox-ep-server path>,
    "http_port": <port>,
    "api_key": <api_key>,
    "sigfox_cloud": {
        "user": <user>,
        "password": <password>
    }
}
```

### Service file

```bash
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

### Devices list

```bash
cd git/sigfox_ep_server
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
