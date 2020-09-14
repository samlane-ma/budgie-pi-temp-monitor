# budgie-pi-temp-monitor
CPU Temperature applet for Ubuntu Budgie on Raspberry Pi

Adds an applet to monitor the CPU temperature.
Settings allow changing of the measurement interval [5..60] seconds and switching from Celcius to Fahrenheit

Temperature icon will be dim normally, now will brighten when temperature gets close to throttle limit.
Icon gets bright at 75 degrees, Raspi throttles at 85.

Popover now shows the highest and lowest temperatures, and the time which they were recorded.

To install (for Debian/Ubuntu):

    mkdir build
    cd build
    meson --prefix=/usr --libdir=/usr/lib --datadir=/usr/share
    sudo ninja install

* for other distros omit libdir and datadir or specify the location of the distro library and data folders

This will:
* install plugin files to the Budgie Desktop plugins folder
* copy the icons to the pixmaps folder
* compile the schema
