import gi
import logging
import os
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel



def create_panel(*args):
    return GuidePanel(*args)

class GuidePanel(ScreenPanel):

    def initialize(self, panel_name):
        _ = self.lang.gettext

        grid = Gtk.Grid()
        grid.set_column_homogeneous(True)
        printers = ["Flsun-V400","Flsun-SR","Flsun-Q5","Flsun-QQS"]
        for printer in printers:
            self.labels[printer] = self._gtk.ButtonImage("print", _(printer), "color1")
            self.labels[printer].connect("clicked", self.confirm, printer)
        
        grid.attach(self.labels[printers[0]], 0, 0, 1, 1)
        grid.attach(self.labels[printers[1]], 1, 0, 1, 1)
        grid.attach(self.labels[printers[2]], 2, 0, 1, 1)
        grid.attach(self.labels[printers[3]], 3, 0, 1, 1)
        
        self.grid = grid
        self.content.add(grid)
        self._screen.wake_screen()

    def confirm(self, data, printer):
        _ = self.lang.gettext
        buttons = [
            {"name": _("Accept"), "response": Gtk.ResponseType.OK},
            {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL}
        ]

        label = Gtk.Label()
        label.set_markup(_("Are you sure switch %s to port1") % printer)
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.CENTER)
        label.set_vexpand(True)
        label.set_valign(Gtk.Align.CENTER)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        dialog = self._gtk.Dialog(self._screen, buttons, label, self.switch_port, printer)
    
    def switch_port(self, widget, response_id, printer):
        if response_id == Gtk.ResponseType.OK:
            logging.debug("switch to port1")
            os.system("echo " + printer + " > /home/pi/klipper_config/port1.tmp | sh /home/pi/KlipperScreen/scripts/printer/printer.sh")
        widget.destroy()

