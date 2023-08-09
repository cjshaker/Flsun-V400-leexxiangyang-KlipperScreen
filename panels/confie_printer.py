import gi
import logging
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args):
    return Confie_printerPanel(*args)

class Confie_printerPanel(ScreenPanel):
    def initialize(self, panel_name):
        _ = self.lang.gettext
        self.settings = {}
        self.macros = {}
        self.menu_cur = 'main_box'
        self.menu = ['main_box']

        self.labels['main_box'] = self.create_box('main')
        self.labels['macros_box'] = self.create_box('macros')

        printbox = Gtk.Box(spacing=0)
        printbox.set_vexpand(False)
        self.labels['add_printer_button'] = self._gtk.Button(_("Add Printer"), "color1")
        self.labels['printers_box'] = self.create_box('printers', printbox)
        #flsun modify,2022.8.26
        #options = self._config.get_configurable_options().copy()
        printers = ["Flsun-V400","Flsun-SR","Flsun-Q5","Flsun-QQS"]
        options = []
        for printer in printers:
            options.append({printer: {
                    "section": "main", "name": _(printer), "type": "dropdown",
                    "value": "none", "options": [
                        {"name": _("port1"), "value": "port1"},
                        {"name": _("port2"), "value": "port2"},
                        {"name": _("port3"), "value": "port3"}]}})
                  
        for option in options:
            name = list(option)[0]
            self.add_option('main', self.settings, name, option[name])

        for macro in self._printer.get_config_section_list("gcode_macro "):
            macro = macro[12:]
            # Support for hiding macros by name
            if macro.startswith("_"):
                continue
            self.macros[macro] = {
                "name": macro,
                "section": "displayed_macros %s" % self._screen.connected_printer,
                "type": "macro"
            }

        for macro in list(self.macros):
            self.add_option('macros', self.macros, macro, self.macros[macro])

        self.printers = {}
        for printer in self._config.get_printers():
            logging.debug("Printer: %s" % printer)
            pname = list(printer)[0]
            self.printers[pname] = {
                "name": pname,
                "section": "printer %s" % pname,
                "type": "printer",
                "moonraker_host": printer[pname]['moonraker_host'],
                "moonraker_port": printer[pname]['moonraker_port'],
            }
            self.add_option("printers", self.printers, pname, self.printers[pname])

        self.content.add(self.labels['main_box'])

    def activate(self):
        while len(self.menu) > 1:
            self.unload_menu()

    def back(self):
        if len(self.menu) > 1:
            self.unload_menu()
            return True
        return False

    def create_box(self, name, insert=None):
        # Create a scroll window for the macros
        scroll = Gtk.ScrolledWindow()
        scroll.set_property("overlay-scrolling", False)
        scroll.set_vexpand(True)
        scroll.add_events(Gdk.EventMask.TOUCH_MASK)
        scroll.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

        # Create a grid for all macros
        self.labels[name] = Gtk.Grid()
        scroll.add(self.labels[name])

        # Create a box to contain all of the above
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_vexpand(True)
        if insert is not None:
            box.pack_start(insert, False, False, 0)
        box.pack_start(scroll, True, True, 0)
        return box

    def add_option(self, boxname, opt_array, opt_name, option):
        if option['type'] is None:
            return

        frame = Gtk.Frame()
        frame.set_property("shadow-type", Gtk.ShadowType.NONE)
        frame.get_style_context().add_class("frame-item")

        name = Gtk.Label()
        name.set_markup("<big><b>%s</b></big>" % (option['name']))
        name.set_hexpand(True)
        name.set_vexpand(True)
        name.set_halign(Gtk.Align.START)
        name.set_valign(Gtk.Align.CENTER)
        name.set_line_wrap(True)
        name.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        labels.add(name)

        dev = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        dev.set_hexpand(True)
        dev.set_vexpand(False)
        dev.set_valign(Gtk.Align.CENTER)

        dev.add(labels)
        if option['type'] == "binary" or option['type'] == "macro":
            box = Gtk.Box()
            box.set_vexpand(False)
            switch = Gtk.Switch()
            switch.set_hexpand(False)
            switch.set_vexpand(False)
            if option['type'] == "macro":
                switch.set_active(self._config.get_config().getboolean(option['section'], opt_name, fallback=True))
            else:
                switch.set_active(self._config.get_config().getboolean(option['section'], opt_name))
            switch.connect("notify::active", self.switch_config_option, option['section'], opt_name,
                           option['options'][1]['callback'] if "callback" in option else None)
            switch.set_property("width-request", round(self._gtk.get_font_size()*7))
            switch.set_property("height-request", round(self._gtk.get_font_size()*3.5))
            box.add(switch)
            dev.add(box)
        elif option['type'] == "dropdown":
            dropdown = Gtk.ComboBoxText()
            i = 0
            for opt in option['options']:
                dropdown.append(opt['value'], opt['name'])
                if opt['value'] == self._config.get_config()[option['section']].get(opt_name, option['value']):
                    dropdown.set_active(i)
                i += 1
            dropdown.connect("changed", self.on_dropdown_change, option['section'], opt_name
                             )
            logging.debug("opt_name is %s" % opt_name)
            dropdown.set_entry_text_column(0)
            dev.add(dropdown)
            logging.debug("Children: %s" % dropdown.get_children())
        elif option['type'] == "scale":
            val = int(self._config.get_config().get(option['section'], opt_name, fallback=option['value']))
            adj = Gtk.Adjustment(val, option['range'][0], option['range'][1], option['step'], option['step']*5)
            scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adj)
            scale.set_hexpand(True)
            scale.set_digits(0)
            scale.connect("button-release-event", self.scale_moved, option['section'], opt_name)
            scale.set_property("width-request", round(self._screen.width/2.2))
            dev.add(scale)
        elif option['type'] == "printer":
            logging.debug("Option: %s" % option)
            box = Gtk.Box()
            box.set_vexpand(False)
            label = Gtk.Label()
            url = "%s:%s" % (option['moonraker_host'], option['moonraker_port'])
            label.set_markup("<big>%s</big>\n%s" % (option['name'], url))
            box.add(label)
            dev.add(box)
        elif option['type'] == "menu":
            open = self._gtk.ButtonImage("settings", None, "color3")
            open.connect("clicked", self.load_menu, option['menu'])
            open.set_hexpand(False)
            open.set_halign(Gtk.Align.END)
            dev.add(open)

        frame.add(dev)
        frame.show_all()

        opt_array[opt_name] = {
            "name": option['name'],
            "row": frame
        }

        opts = sorted(opt_array)
        opts = sorted(list(opt_array), key=lambda x: opt_array[x]['name'])
        pos = opts.index(opt_name)

        self.labels[boxname].insert_row(pos)
        self.labels[boxname].attach(opt_array[opt_name]['row'], 0, pos, 1, 1)
        self.labels[boxname].show_all()

    def load_menu(self, widget, name):
        if ("%s_box" % name) not in self.labels:
            return

        for child in self.content.get_children():
            self.content.remove(child)

        self.menu.append('%s_box' % name)
        self.content.add(self.labels[self.menu[-1]])
        self.content.show_all()

    def unload_menu(self, widget=None):
        logging.debug("self.menu: %s" % self.menu)
        if len(self.menu) <= 1 or self.menu[-2] not in self.labels:
            return

        self.menu.pop()
        for child in self.content.get_children():
            self.content.remove(child)
        self.content.add(self.labels[self.menu[-1]])
        self.content.show_all()

    def on_dropdown_change(self, combo, section, option, callback=None):  #flsun modify
        tree_iter = combo.get_active_iter()
        if tree_iter is not None:
            model = combo.get_model()
            value = model[tree_iter][1]
            logging.debug("[%s] %s changed to %s" % (section, option, value))#the value is port1,port2,or port3
            self._config.set(section, option, value)
            self._config.save_user_config_options()
            #file_name = option + ".sh"
            if callback is not None:
                callback(value)
            _ = self.lang.gettext
            if value == "port1":
                buttons = [
                    #{"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL},
                    #{"name": _("Confirm"), "response": Gtk.ResponseType.OK}
                    {"name": _("Accept"), "response": Gtk.ResponseType.OK},
                    {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL}
                ]

                label = Gtk.Label()
                label.set_markup(_("Are you sure switch %s to %s") % (option, value))
                label.set_hexpand(True)
                label.set_halign(Gtk.Align.CENTER)
                label.set_vexpand(True)
                label.set_valign(Gtk.Align.CENTER)
                label.set_line_wrap(True)
                label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

                dialog = self._gtk.Dialog(self._screen, buttons, label, self.switch_port1, option)
                #os.system("echo port1 > /home/pi/klipper_config/port1.tmp | bash /home/pi/KlipperScreen/scripts/printer/" + file_name)
            if value == "port2":
                buttons = [
                    {"name": _("Accept"), "response": Gtk.ResponseType.OK},
                    {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL}
                ]

                label = Gtk.Label()
                label.set_markup(_("Are you sure switch %s to %s") % (option, value))
                label.set_hexpand(True)
                label.set_halign(Gtk.Align.CENTER)
                label.set_vexpand(True)
                label.set_valign(Gtk.Align.CENTER)
                label.set_line_wrap(True)
                label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

                dialog = self._gtk.Dialog(self._screen, buttons, label, self.switch_port2, option)
                #os.system("echo port2 > /home/pi/klipper_config/port2.tmp | bash /home/pi/KlipperScreen/scripts/printer/" + file_name)
            if value == "port3":
                buttons = [
                    {"name": _("Accept"), "response": Gtk.ResponseType.OK},
                    {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL}
                ]

                label = Gtk.Label()
                label.set_markup(_("Are you sure switch %s to %s") % (option, value))
                label.set_hexpand(True)
                label.set_halign(Gtk.Align.CENTER)
                label.set_vexpand(True)
                label.set_valign(Gtk.Align.CENTER)
                label.set_line_wrap(True)
                label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

                dialog = self._gtk.Dialog(self._screen, buttons, label, self.switch_port3, option)
                #os.system("echo port3 > /home/pi/klipper_config/port3.tmp | bash /home/pi/KlipperScreen/scripts/printer/" + file_name)
        
    def switch_port1(self, widget, response_id, option):
        if response_id == Gtk.ResponseType.OK:
            logging.debug("switch to port1")
            os.system("echo " + option + " > /home/pi/klipper_config/port1.tmp | sh /home/pi/KlipperScreen/scripts/printer/printer.sh")
        widget.destroy()

    def switch_port2(self, widget, response_id, option):
        if response_id == Gtk.ResponseType.OK:
            logging.debug("switch to port2")
            os.system("echo " + option + " > /home/pi/klipper_config/port2.tmp | sh /home/pi/KlipperScreen/scripts/printer/printer.sh")
        widget.destroy()

    def switch_port3(self, widget, response_id, option):
        if response_id == Gtk.ResponseType.OK:
            logging.debug("switch to port3")
            os.system("echo " + option + " > /home/pi/klipper_config/port3.tmp | sh /home/pi/KlipperScreen/scripts/printer/printer.sh")
        widget.destroy()

    def scale_moved(self, widget, event, section, option):
        logging.debug("[%s] %s changed to %s" % (section, option, widget.get_value()))
        if section not in self._config.get_config().sections():
            self._config.get_config().add_section(section)
        self._config.set(section, option, str(int(widget.get_value())))
        self._config.save_user_config_options()

    def switch_config_option(self, switch, gparam, section, option, callback=None):
        logging.debug("[%s] %s toggled %s" % (section, option, switch.get_active()))
        if section not in self._config.get_config().sections():
            self._config.get_config().add_section(section)
        self._config.set(section, option, "True" if switch.get_active() else "False")
        self._config.save_user_config_options()
        if callback is not None:
            callback(switch.get_active())

    def add_gcode_option(self):
        macros = self._screen.printer.get_gcode_macros()
        for x in macros:
            self.add_gcode_macro("macros", self.macros, x, {
                "name": x[12:],
                "type": binary
            })

    def run_gcode_macro(self, widget, macro):
        self._screen._ws.klippy.gcode_script(macro)



