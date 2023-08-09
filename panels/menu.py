import gettext
import gi
import logging

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib,Pango
from jinja2 import Environment, Template

from ks_includes.screen_panel import ScreenPanel

def create_panel(*args):
    return MenuPanel(*args)

class MenuPanel(ScreenPanel):
    i = 0
    j2_data = None
    def initialize(self, panel_name, display_name, items):
        _ = self.lang.gettext

        self.items = items
        self.create_menu_items()

        self.grid = Gtk.Grid()
        self.grid.set_row_homogeneous(True)
        self.grid.set_column_homogeneous(True)
        self.content.add(self.grid)

    def activate(self):
        if not self.j2_data:
            self.j2_data = self._printer.get_printer_status_data()
        self.j2_data.update({
            'moonraker_connected': self._screen._ws.is_connected()
        })
        self.arrangeMenuItems(self.items, 4)

    def arrangeMenuItems(self, items, columns, expandLast=False):
        for child in self.grid.get_children():
            self.grid.remove(child)

        length = len(items)
        i = 0
        for item in items:
            key = list(item)[0]
            logging.debug("Evaluating item: %s" % key)
            if not self.evaluate_enable(item[key]['enable']):
                continue

            if columns == 4:
                if length <= 4:
                    # Arrange 2 x 2
                    columns = 2
                elif length > 4 and length <= 6:
                    # Arrange 3 x 2
                    columns = 3

            if self._screen.vertical_mode:
                row = i % columns
                col = int(i/columns)
            else:
                col = i % columns
                row = int(i/columns)

            width = height = 1
            if expandLast is True and i+1 == length and length % 2 == 1:
                if self._screen.vertical_mode:
                    height = 2
                else:
                    width = 2

            self.grid.attach(self.labels[key], col, row, width, height)
            i += 1

        return self.grid

    def create_menu_items(self):
        for i in range(len(self.items)):
            key = list(self.items[i])[0]
            item = self.items[i][key]

            env = Environment(extensions=["jinja2.ext.i18n"])
            env.install_gettext_translations(self.lang)
            j2_temp = env.from_string(item['name'])
            parsed_name = j2_temp.render()

            b = self._gtk.ButtonImage(
                item['icon'], parsed_name, "color"+str((i % 4)+1)
            )
            if item['panel'] is not False:
                if item['panel'] != "input_shaper":
                    b.connect("clicked", self.menu_item_clicked, item['panel'], item)
                else:
                    b.connect("clicked", self.use_accelerometer)
            elif item['method'] is not False:
                params = item['params'] if item['params'] is not False else {}
                if item['confirm'] is not False:
                    b.connect("clicked", self._screen._confirm_send_action, item['confirm'], item['method'], params)
                else:
                    b.connect("clicked", self._screen._send_action, item['method'], params)
            else:
                b.connect("clicked", self._screen._go_to_submenu, key)
            self.labels[key] = b
    #2023.7.27flsun，add
    def use_accelerometer(self,widget):
        _ = self.lang.gettext
        buttons = [
            {"name": _("Continue"), "response": Gtk.ResponseType.OK},
            {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL}
        ]

        label = Gtk.Label()
        label.set_markup(_("Please insert the accelerometer"))
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.CENTER)
        label.set_vexpand(True)
        label.set_valign(Gtk.Align.CENTER)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.acce_dialog = self._gtk.Dialog(self._screen, buttons, label, self.accelerometer)
        
    def accelerometer(self, widget, response_id):
        _ = self.lang.gettext
        if response_id == Gtk.ResponseType.OK:
            logging.debug("OK")
            self.menu_item_clicked("gg","input_shaper", {"panel": "input_shaper", "name": _("Input Shaper")})
        if response_id == Gtk.ResponseType.CANCEL:
            logging.debug("cancel")
        self.acce_dialog.destroy()        
        

    def evaluate_enable(self, enable):
        if enable is True:
            return True
        if enable is False:
            return False

        if not self.j2_data:
            self.j2_data = self._printer.get_printer_status_data()
        try:
            logging.debug("Template: '%s'" % enable)
            logging.debug("Data: %s" % self.j2_data)
            j2_temp = Template(enable)
            result = j2_temp.render(self.j2_data)
            if result == 'True':
                return True
            return False
        except Exception:
            logging.debug("Error evaluating enable statement: %s", enable)
            return False
