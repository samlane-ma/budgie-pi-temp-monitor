import gi.repository
import os
import os.path
import subprocess
import time
import threading
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
    
    Icons made by Freepik from http://www.freepik.com
    https://www.flaticon.com
"""

app_settings = Gio.Settings.new("com.github.samlane-ma.budgie-pi-temp-monitor")

def load_settings():
    ret_interval = app_settings.get_int("interval")
    ret_degree = app_settings.get_boolean("celcius")   
    return ret_interval, ret_degree


def save_degree_setting(save_degree):
    app_settings.set_boolean("celcius",save_degree)
    
def save_interval_setting(save_interval):
    app_settings.set_int("interval",save_interval)  
  
  
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
        
        sleeptime, celcius = load_settings()

        self.spin_label = Gtk.Label("Temperature check interval (s):")
        self.spin_label.set_justify(Gtk.Justification.LEFT)
        spin_adjust = Gtk.Adjustment (sleeptime, 5, 60, 1, 0, 0)
        self.interval_spin = Gtk.SpinButton(adjustment = spin_adjust, climb_rate = 1, digits = 0)
        self.interval_spin.set_halign(Gtk.Align.END)
        self.interval_spin.connect("value-changed", self.change_interval)
        
        self.degree_label = Gtk.Label("Show temperature in Farenheit :")
        self.degree_label.set_justify(Gtk.Justification.LEFT)
        self.degree_type = Gtk.Switch()
        self.degree_type.set_halign(Gtk.Align.END)
        self.degree_type.set_active(not celcius)
        self.degree_type.connect("notify::active", self.change_degree_type)
        
        self.attach(self.spin_label,    0, 1, 2, 1)
        self.attach_next_to(self.interval_spin, self.spin_label, Gtk.PositionType.RIGHT, 1, 1)
        self.attach(self.degree_label,  0, 2, 2, 1)
        self.attach_next_to(self.degree_type, self.degree_label, Gtk.PositionType.RIGHT, 1, 1)
        
        self.show_all()
        
        
        
    def change_interval(self, event):
        sleeptime = self.interval_spin.get_value_as_int()
        save_interval_setting(sleeptime)

        
    def change_degree_type(self, button, active):
        if button.get_active():
            celcius = False
        else:
            celcius = True
        save_degree_setting(celcius)
  


class BudgiePiTempApplet(Budgie.Applet):
    """ Budgie.Applet is in fact a Gtk.Bin """
    manager = None

    
    def __init__(self, uuid):
        
        Budgie.Applet.__init__(self)
        
        self.uuid = uuid
        self.connect("destroy",Gtk.main_quit)

        currenttemp = "--"
   
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
            sleeptime, celcius = load_settings()
            cputempfile = open("/sys/class/thermal/thermal_zone0/temp")
            self.currenttemp = cputempfile.read()
            cputempfile.close()
            GObject.idle_add(self.updatelabel, celcius)
            time.sleep(sleeptime)
 
            
    def updatelabel(self, celcius):
        use_celcius = celcius
        if use_celcius:
            self.cputemp.set_text(str(int(int(self.currenttemp) /1000))+"°C")
        else:
            farenheit = int(int(self.currenttemp) / 1000 * 9 / 5 + 32)
            self.cputemp.set_text(str(farenheit)+"°F")

    
    def do_supports_settings(self):
        """Return True if support setting through Budgie Setting,
        False otherwise.
        """
        return True
        
    
    def do_get_settings_ui(self):
        """Return the applet settings with given uuid"""
        return BudgiePiTempSettings(self.get_applet_settings(self.uuid))        

            
