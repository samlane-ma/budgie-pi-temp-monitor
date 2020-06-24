
#!/bin/bash

set -e

sudo mkdir -p /usr/lib/budgie-desktop/plugins/budgie-pi-temp-monitor
sudo cp budgie_pi_temp_monitor.py /usr/lib/budgie-desktop/plugins/budgie-pi-temp-monitor
sudo cp BudgiePiTempMonitor.plugin /usr/lib/budgie-desktop/plugins/budgie-pi-temp-monitor
sudo cp -n sensors-temperature-symbolic.svg /usr/share/pixmaps/
