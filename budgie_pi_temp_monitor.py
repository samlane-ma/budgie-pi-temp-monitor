import gi.repository
import os
import os.path
import subprocess
import time
import threading
gi.require_version('Budgie', '1.0')
from gi.repository import Budgie, GObject, Gtk, Gio, GLib

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
path = "com.solus-project.budgie-panel"

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
        self.connect("destroy",Gtk.main_quit)
        self.keep_running = True

        self.currenttemp = "--"
        self.sleeptime = app_settings.get_int("interval")
        self.celcius = app_settings.get_boolean("celcius")

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(box)
        self.cputemp = Gtk.Label(self.currenttemp+"°C")
        self.temp_icon = Gtk.Image.new_from_icon_name("sensors-temperature-symbolic",Gtk.IconSize.MENU)
        box.pack_start(self.cputemp, expand = True, fill = True, padding = 0)
        box.pack_end(self.temp_icon, expand = True, fill = True, padding = 0)
        self.show_all()

        app_settings.connect("changed",self.load_settings)

        GObject.threads_init()
        self.updatethread = threading.Thread(target=self.update_temp)
        self.updatethread.setDaemon(True)
        self.updatethread.start()

        GLib.idle_add(self.watch_applet, self.uuid)

    def load_settings(self, *args):
        self.sleeptime = app_settings.get_int("interval")
        self.celcius = app_settings.get_boolean("celcius")
        GObject.idle_add(self.update_panel)

    def update_temp(self):
        while self.keep_running:
            cputempfile = open("/sys/class/thermal/thermal_zone0/temp")
            self.currenttemp = cputempfile.read()
            cputempfile.close()
            GObject.idle_add(self.update_panel)
            time.sleep(self.sleeptime)

    def update_panel(self):
        temp_int = int(self.currenttemp) / 1000
        if not self.celcius:
            suffix = "°F"
            temp_int = temp_int * 9 / 5 + 32
        else:
            suffix = "°C"
        temp = str(round(temp_int))
        self.cputemp.set_text(temp + suffix)

    def find_applet (self, check_uuid, applets):
        for find_uuid in applets:
            if find_uuid == check_uuid:
                return True
        return False 

    def watch_applet (self, check_uuid):
        applets = []
        panel_settings = Gio.Settings(path);
        allpanels_list = panel_settings.get_strv("panels")
        for p in allpanels_list:
            panelpath = "/com/solus-project/budgie-panel/panels/{" + p + "}/"
            self.currpanelsubject_settings = Gio.Settings.new_with_path(path + ".panel", panelpath)
            applets = self.currpanelsubject_settings.get_strv("applets")
            if self.find_applet(check_uuid, applets):
                # Need this signal id to disconnect it on quit
                self.panel_signal_id = self.currpanelsubject_settings.connect(
                              "changed::applets", self.is_applet_running, check_uuid)
        return False

    def is_applet_running (self, arg1, arg2, check_uuid):
        applets =self.currpanelsubject_settings.get_strv("applets")
        if not self.find_applet(check_uuid, applets):
            # Disconnect the signals
            self.currpanelsubject_settings.disconnect(self.panel_signal_id)
            self.keep_running = False

    def do_supports_settings(self):
        """Return True if support setting through Budgie Setting,
        False otherwise.
        """
        return True

    def do_get_settings_ui(self):
        """Return the applet settings with given uuid"""
        return BudgiePiTempSettings(self.get_applet_settings(self.uuid))

