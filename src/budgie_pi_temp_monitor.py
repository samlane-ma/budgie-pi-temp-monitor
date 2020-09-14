import gi.repository
import os
import os.path
import subprocess
import time
import threading
from datetime import datetime
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
HI_TEMP = 1
HI_TIME = 2
LOW_TEMP = 5
LOW_TIME = 6

app_settings = Gio.Settings.new("com.github.samlane-ma.budgie-pi-temp-monitor")

class PiTemp:
    
    def __init__(self, _temp = 0, _time = datetime.now()):
        self._temp = _temp
        self._time = _time
        
    def get_temp(self, celcius=True):
        ret_temp = self._temp / 1000
        if celcius:
            degree = "°C"
        else:
            ret_temp = temp_int * 9 / 5 + 32
            degree = "°F"
        return format(ret_temp, '.2f') + degree
        
    def get_time(self):
        return self._time.strftime("%x %X")


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

        sleeptime = app_settings.get_int("interval")
        celcius = app_settings.get_boolean("celcius")

        label_interval = Gtk.Label(label="Interval (s):")
        label_interval.set_halign(Gtk.Align.START)
        adjust_interval = Gtk.Adjustment (sleeptime, 5, 60, 1, 0, 0)
        spin_interval = Gtk.SpinButton(adjustment = adjust_interval, climb_rate = 1, digits = 0)
        spin_interval.set_halign(Gtk.Align.END)

        label_degreetype = Gtk.Label(label="Celcius:")
        label_degreetype.set_halign(Gtk.Align.START)
        switch_degree_type = Gtk.Switch()
        switch_degree_type.set_halign(Gtk.Align.END)
        switch_degree_type.set_active(celcius)

        app_settings.bind("interval", spin_interval, "value", Gio.SettingsBindFlags.DEFAULT)
        app_settings.bind("celcius", switch_degree_type, "active", Gio.SettingsBindFlags.DEFAULT)

        self.attach(label_interval, 0, 1, 2, 1)
        self.attach_next_to(spin_interval, label_interval, Gtk.PositionType.RIGHT, 1, 1)
        self.attach(label_degreetype, 0, 2, 2, 1)
        self.attach_next_to(switch_degree_type, label_degreetype, Gtk.PositionType.RIGHT, 1, 1)
        self.show_all()

class BudgiePiTempApplet(Budgie.Applet):
    """ Budgie.Applet is in fact a Gtk.Bin """
    manager = None

    def __init__(self, uuid):

        Budgie.Applet.__init__(self)

        self.uuid = uuid
        self.label_names = ["Highest Temp","","","","Lowest Temp:","",""]
        self.currenttemp = "--"
        self.sleeptime = app_settings.get_int("interval")
        self.celcius = app_settings.get_boolean("celcius")
        self.overheat = False

        self.panel_box = Gtk.EventBox()
        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.panel_box.add(self.box)
        self.add(self.panel_box)
        self.cputemp = Gtk.Label(self.currenttemp+"°C")
        self.temp_icon = Gtk.Image.new_from_icon_name("sensors-temperature-symbolic",Gtk.IconSize.MENU)
        self.box.pack_start(self.cputemp, expand = True, fill = True, padding = 0)
        self.box.pack_end(self.temp_icon, expand = True, fill = True, padding = 0)
        self.temp_icon.get_style_context().add_class("dim-label")
        self.menu_box = Gtk.Grid()
        self.labels = []
        for n in range(7):
            label = Gtk.Label(label=self.label_names[n])
            self.labels.append(label)
            self.menu_box.attach(self.labels[n],0,n,1,1)
        self.popover = Budgie.Popover.new(self.panel_box)
        self.popover.add(self.menu_box)
        self.panel_box.connect("button-press-event", self.on_press)
        self.menu_box.show_all()
        self.show_all()

        self.hi_temp = PiTemp(0)
        self.low_temp = PiTemp(1000000)
        self.labels[HI_TEMP].set_text(self.hi_temp.get_temp())
        self.labels[HI_TIME].set_text(self.hi_temp.get_time())
        self.labels[LOW_TEMP].set_text(self.low_temp.get_temp())
        self.labels[LOW_TIME].set_text(self.low_temp.get_time())

        app_settings.connect("changed",self.load_settings)

        GObject.threads_init()
        self.updatethread = threading.Thread(target=self.update_temp)
        self.updatethread.setDaemon(True)
        self.updatethread.start()

    def load_settings(self, *args):
        self.sleeptime = app_settings.get_int("interval")
        self.celcius = app_settings.get_boolean("celcius")
        GObject.idle_add(self.update_panel)

    def update_temp(self):
        while True:
            cputempfile = open("/sys/class/thermal/thermal_zone0/temp")
            self.currenttemp = cputempfile.read()
            cputempfile.close()
            GObject.idle_add(self.update_panel)
            time.sleep(self.sleeptime)

    def update_panel(self):
        temp_int = int(self.currenttemp)
        if self.overheat and temp_int < 75000:
            self.temp_icon.get_style_context().add_class("dim-label")
            self.overheat = False
        elif not self.overheat and temp_int >= 75000:
            self.temp_icon.get_style_context().remove_class("dim-label")
            self.overheat = True
        if temp_int > self.hi_temp._temp:
            self.hi_temp._temp = temp_int
            self.hi_temp._time = datetime.now()
            self.labels[HI_TEMP].set_text(self.hi_temp.get_temp())
            self.labels[HI_TIME].set_text(self.hi_temp.get_time())
        if temp_int < self.low_temp._temp:
            self.low_temp._temp = temp_int
            self.low_temp._time = datetime.now()
            self.labels[LOW_TEMP].set_text(self.low_temp.get_temp())
            self.labels[LOW_TIME].set_text(self.low_temp.get_time())
        temp_int = temp_int / 1000
        if not self.celcius:
            suffix = "°F"
            temp_int = temp_int * 9 / 5 + 32
        else:
            suffix = "°C"
        temp = str(round(temp_int))
        self.cputemp.set_text(temp + suffix)

    def on_press(self, panel_box, event):
        if event.button == 1:
            self.manager.show_popover(self.panel_box)

    def do_update_popovers(self, manager):
        self.manager = manager
        self.manager.register_popover(self.panel_box, self.popover)

    def do_supports_settings(self):
        """Return True if support setting through Budgie Setting,
        False otherwise.
        """
        return True

    def do_get_settings_ui(self):
        """Return the applet settings with given uuid"""
        return BudgiePiTempSettings(self.get_applet_settings(self.uuid))

