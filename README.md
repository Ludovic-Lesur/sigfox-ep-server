## System update

```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get autoremove
```

## Influx DB

### Installation

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

### Data requests

```bash
influx
USE meteofox_db
SELECT rain FROM weather WHERE sigfox_ep_id='5477'
INSERT weather,sigfox_ep_id=549D,site=Labege rain=0i 1597831208000000000
INSERT electrical,sigfox_ep_id=4761,system=Test_bench,node_address=33,\
       node=LVRM_1,board_id=0 iout=0i 1701853317000000000
INSERT monitoring,sigfox_ep_id=53B5,site=Proto_HW1.0 vcap=2620i 1597831208000000000
```

## Grafana

### Installation

```bash
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana
sudo service grafana-server start
```

Edit the `/etc/grafana/grafana.ini` configuration file: in the **Server** section, uncomment `protocol = http` and set `http_port=<grafana_port>`.

### Plugins

```bash
sudo grafana-cli plugins install grafana-clock-panel
sudo grafana-cli plugins install grafana-worldmap-panel
sudo grafana-cli plugins install fatcloud-windrose-panel
```

### Images

```bash
sudo cp ./grafana/images/x.png /usr/share/grafana/public/img/
```

## Python libraries

```bash
sudo apt install python3-pip
pip3 install requests
pip3 install HTTPServer
pip3 install influxdb
```

## Service file

```bash
sudo cp sigfox_ep_server.service /lib/systemd/system
sudo systemctl daemon-reload
```

## Server update

```bash
cd git/sigfox_ep_server
sudo service sigfox_ep_server stop
git pull
./git_version.sh
sudo service sigfox_ep_server start
```
