import gi
import logging
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args):
    return Switch_printerPanel(*args)
class Switch_printerPanel(ScreenPanel):
    def initialize(self, panel_name):
        _ = self.lang.gettext
        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        self.labels['Printer1'] = self._gtk.ButtonImage("print", _("Flsun-V400"), "color1")
        self.labels['Printer1'].connect("clicked", self.switch_printer1)
        self.labels['Printer2'] = self._gtk.ButtonImage("print", _("Printer-2"), "color2")
        self.labels['Printer2'].connect("clicked", self.switch_printer2)
        self.labels['Printer3'] = self._gtk.ButtonImage("print", _("Printer-3"), "color3")
        self.labels['Printer3'].connect("clicked", self.switch_printer3)
        self.labels['Printer4'] = self._gtk.ButtonImage("settings", _("Configuration"), "color4")
        self.labels['Printer4'].connect("clicked", self.menu_item_clicked, "Printer4", { "panel": "confie_printer", "name": _("Switch Printer")})
        grid.attach(self.labels['Printer1'], 0, 0, 1, 1)
        grid.attach(self.labels['Printer2'], 1, 0, 1, 1)
        grid.attach(self.labels['Printer3'], 0, 1, 1, 1)
        grid.attach(self.labels['Printer4'], 1, 1, 1, 1)
        self.grid = grid
        self.content.add(grid)
        self._screen.wake_screen()
    def process_update(self, action, data):
        pass
    def switch_printer1(self, data):
        os.system("echo port1 > /home/pi/klipper_config/printer1.tmp | sh /home/pi/KlipperScreen/scripts/printer/usb.sh")

    def switch_printer2(self, data):
        os.system("echo port2 > /home/pi/klipper_config/printer2.tmp | sh /home/pi/KlipperScreen/scripts/printer/usb.sh")

    def switch_printer3(self, data):
        os.system("echo port3 > /home/pi/klipper_config/printer3.tmp | sh /home/pi/KlipperScreen/scripts/printer/usb.sh")