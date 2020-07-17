
#!/bin/bash

set -e

sudo mkdir -p /usr/lib/budgie-desktop/plugins/budgie-pi-temp-monitor
sudo cp budgie_pi_temp_monitor.py /usr/lib/budgie-desktop/plugins/budgie-pi-temp-monitor
sudo cp BudgiePiTempMonitor.plugin /usr/lib/budgie-desktop/plugins/budgie-pi-temp-monitor
sudo cp -n sensors-temperature-symbolic.svg /usr/share/pixmaps/
sudo cp com.github.samlane-ma.budgie-pi-temp-monitor.gschema.xml /usr/share/glib-2.0/schemas
sudo sudo glib-compile-schemas /usr/share/glib-2.0/schemas
