import gi.repository
import os
import os.path
import subprocess
import time
import threading
from configparser import SafeConfigParser
gi.require_version('Budgie', '1.0')
from gi.repository import Budgie, GObject, Gtk, Gio

"""
    Budgie Pi Temperature Monitor Plugin - Show the Current CPU Temp on Raspberry Pi
    Copyright (C) 2020  Samuel Lane

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
    
    Icon made by Hirschwolf <https://www.flaticon.com/authors/hirschwolf>
    https://www.flaticon.com
"""

sleeptime = 10
celcius = True

def load_settings(config_file):

    # Load the settings from the config file.
    # If the config file does not exist, create it.
    # If the config file has invalid data, reset it.
    
    need_new = False
    if not os.path.isfile(config_file):
        need_new = True
    config = SafeConfigParser()
    config.read(config_file)
    if not config.has_option('Default','Interval'):
        need_new = True
    if not config.has_option('Default','Celcius'):
        need_new = True
    if need_new:
        create_settings(config_file)
        need_new = False
    config.read(config_file)
    read_interval = config.get('Default','Interval')
    read_degree = config.get('Default','Celcius')
    if not read_degree in ['True','False']:
        need_new = True
    if not int(read_interval) in range(5,60):
        need_new = True
    if need_new:
        create_settings(config_file)

    config.read(config_file)
    read_interval = config.get('Default','Interval')
    read_degree = config.get('Default','Celcius')       
            
    ret_interval = int(read_interval)
    if read_degree == "True":
        ret_degree = True
    else:
        ret_degree = False    
    
    return ret_interval, ret_degree


def save_settings(save_interval, save_degree, config_file):

    # saves the settings to the config file

    config = SafeConfigParser()
    config.read(config_file)
    config.set('Default','Interval',str(save_interval))
    config.set('Default','Celcius',str(save_degree))
    with open(config_file, 'w') as f:
        config.write (f)
        
    
def create_settings(config_file):
    
    # Deletes the config file if it exists, and creates a new one
    # using default values.  Called when file is missing or invalid.

    if os.path.isfile(config_file):
        os.remove(config_file)
    config = SafeConfigParser()
    config.read(self.config_file)
    config.add_section('Default')
    config.set('Default','Interval','10')
    config.set('Default','Celcius','True')
    with open(config_file, 'w') as f:
        config.write (f)
        

class BudgiePiTemp(GObject.GObject, Budgie.Plugin):
    """ This is simply an entry point into your Budgie Applet implementation.
        Note you must always override Object, and implement Plugin.
    """
    # Good manners, make sure we have unique name in GObject type system
    __gtype_name__ = "BudgiePiTemp"
    
    def __init__(self):
        """ Initialisation is important.
        """
        GObject.Object.__init__(self)
    
    def do_get_panel_widget(self, uuid):
        """ This is where the real fun happens. Return a new Budgie.Applet
            instance with the given UUID. The UUID is determined by the
            BudgiePanelManager, and is used for lifetime tracking.
        """
        return BudgiePiTempApplet(uuid)
        
        

class BudgiePiTempSettings(Gtk.Grid):

    def __init__(self, setting):
        super().__init__()
        
        global sleeptime
        global celcius
        
        self.config_path = os.getenv("HOME")+'/.config/pi-temp-monitor.ini'
        sleeptime, celcius = load_settings(self.config_path)

        self.spin_label = Gtk.Label("Temperature check interval (s):")
        self.spin_label.set_justify(Gtk.Justification.LEFT)
        spin_adjust = Gtk.Adjustment (sleeptime, 5, 60, 1, 0, 0)
        self.interval_spin = Gtk.SpinButton(adjustment = spin_adjust, climb_rate = 1, digits = 0)
        self.interval_spin.connect("value-changed", self.change_interval)
        
        self.degree_label = Gtk.Label("Show temperature in fahrenheit :")
        self.degree_label.set_justify(Gtk.Justification.LEFT)
        self.degree_type = Gtk.Switch()
        self.degree_type.set_active(not celcius)
        self.degree_type.connect("notify::active", self.change_degree_type)
        
        self.attach(self.spin_label,    0, 1, 2, 1)
        self.attach_next_to(self.interval_spin, self.spin_label, Gtk.PositionType.RIGHT, 1, 1)
        self.attach(self.degree_label,  0, 2, 2, 1)
        self.attach_next_to(self.degree_type, self.degree_label, Gtk.PositionType.RIGHT, 1, 1)
        
        self.show_all()
        
        
        
    def change_interval(self, event):
        global sleeptime
        global celcius
        sleeptime = self.interval_spin.get_value_as_int()
        save_settings(str(sleeptime),str(celcius), self.config_path)

        
    def change_degree_type(self, button, active):
        global sleeptime
        global celcius
        if button.get_active():
            celcius = False
        else:
            celcius = True
        save_settings(str(sleeptime),str(celcius), self.config_path)
  


class BudgiePiTempApplet(Budgie.Applet):
    """ Budgie.Applet is in fact a Gtk.Bin """
    manager = None

    
    def __init__(self, uuid):
        
        Budgie.Applet.__init__(self)
        
        self.uuid = uuid
        self.connect("destroy",Gtk.main_quit)

        currenttemp = "--"
        
        global sleeptime
        global celcius
        
        self.config_path = os.getenv("HOME")+'/.config/pi-temp-monitor.ini'
        sleeptime, celcius = load_settings(self.config_path)
    
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        self.add(box)
        self.cputemp = Gtk.Label(currenttemp+"°C")
        self.temp_icon = Gtk.Image.new_from_icon_name("sensors-temperature-symbolic",Gtk.IconSize.MENU)
        box.pack_start(self.cputemp, expand = True, fill = True, padding = 0)
        box.pack_end(self.temp_icon, expand = True, fill = True, padding = 0)
        self.show_all()
        
        GObject.threads_init()
        self.updatethread = threading.Thread(target=self.updatetemp)
        self.updatethread.setDaemon(True)
        self.updatethread.start()


   	     
    def updatetemp(self):
        while True:
            cputempfile = open("/sys/class/thermal/thermal_zone0/temp")
            self.currenttemp = cputempfile.read()
            cputempfile.close()
            GObject.idle_add(self.updatelabel)
            time.sleep(sleeptime)
 
            
    def updatelabel(self):
        if celcius:
            self.cputemp.set_text(str(int(int(self.currenttemp) /1000))+"°C")
        else:
            fahrenheit = int(int(self.currenttemp) / 1000 * 9 / 5 + 32)
            self.cputemp.set_text(str(fahrenheit)+"°F")

    
    def do_supports_settings(self):
        """Return True if support setting through Budgie Setting,
        False otherwise.
        """
        return True
        
    
    def do_get_settings_ui(self):
        """Return the applet settings with given uuid"""
        return BudgiePiTempSettings(self.get_applet_settings(self.uuid))        

            
