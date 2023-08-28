# Changes Start
import gi
import logging
import re
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

from ks_includes.KlippyGcodes import KlippyGcodes
from ks_includes.screen_panel import ScreenPanel

def create_panel(*args):
    return ZCalibratePanel(*args)

class ZCalibratePanel(ScreenPanel):
    user_selecting = False

    bs = 0
    bs_delta = "0.05"
    bs_deltas = ["0.01", "0.05", "0.1"]

    def initialize(self, panel_name):
        _ = self.lang.gettext

        grid = self._gtk.HomogeneousGrid()
        grid.set_row_homogeneous(False)
        logging.debug("ZCalibratePanel")

        self.labels['start'] = self._gtk.ButtonImage('arrow-down', _("Move Z0"), 'color1')
        self.labels['start'].connect("clicked", self.go_to_z0, "start")
        self.labels['home'] = self._gtk.ButtonImage("z-tilt", _("Calibrate"), "color1")
        self.labels['home'].connect("clicked", self.go_to_home, "home")
        self.labels['z+'] = self._gtk.ButtonImage("z-farther", _("Raise Nozzle"), "color1")  
        self.labels['z+'].connect("clicked", self.change_babystepping, "+")
        self.labels['zoffset'] = Gtk.Label("0.00" + _("mm"))         
        self.labels['z-'] = self._gtk.ButtonImage("z-closer", _("Lower Nozzle"), "color1")
        self.labels['z-'].connect("clicked", self.change_babystepping, "-")
        self.labels['blank'] = Gtk.Label()

        grid.attach(self.labels['start'], 0, 1, 1, 1)
        grid.attach(self.labels['home'], 0, 0, 1, 1)
        grid.attach(self.labels['z+'], 1, 0, 2, 1)
        grid.attach(self.labels['z-'],  1, 1, 2, 1)
        grid.attach(self.labels['blank'], 0, 3, 1, 1)
        grid.attach(self.labels['zoffset'], 0, 5, 1, 1)

        
        bsgrid = Gtk.Grid()
        j = 0
        for i in self.bs_deltas:
            self.labels[i] = self._gtk.ToggleButton(i)
            self.labels[i].connect("clicked", self.change_bs_delta, i)
            ctx = self.labels[i].get_style_context()
            if j == 0:
                ctx.add_class("distbutton_top")
            elif j == len(self.bs_deltas)-1:
                ctx.add_class("distbutton_bottom")
            else:
                ctx.add_class("distbutton")
            if i == self.bs_delta:
                ctx.add_class("distbutton_active")
            bsgrid.attach(self.labels[i], j, 0, 1, 1)
            j += 1
        grid.attach(bsgrid, 1, 5, 2, 1)

        self.content.add(grid)

    def process_update(self, action, data):
        _ = self.lang.gettext

        if action != "notify_status_update":
            return

        if "gcode_move" in data:
            if "homing_origin" in data["gcode_move"]:
                self.labels['zoffset'].set_text("Z Offset: %.2fmm" % data["gcode_move"]["homing_origin"][2])

    def change_babystepping(self, widget, dir):
        if dir == "+":
            gcode = "SET_GCODE_OFFSET Z_ADJUST=%s MOVE=1" % self.bs_delta
        else:
            gcode = "SET_GCODE_OFFSET Z_ADJUST=-%s MOVE=1" % self.bs_delta

        self._screen._ws.klippy.gcode_script(gcode)

    def go_to_home(self, widget, home):
        _ = self.lang.gettext
        buttons = [
            {"name": _("Continue"), "response": Gtk.ResponseType.OK},
            {"name": _("Cancel"), "response": Gtk.ResponseType.CANCEL}
        ]
        label = Gtk.Label()
        label.set_markup(_("Please plug in leveling switch before auto-leveling"))
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.CENTER)
        label.set_vexpand(True)
        label.set_valign(Gtk.Align.CENTER)
        label.set_line_wrap(True)
        label.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        dialog = self._gtk.Dialog(self._screen, buttons, label, self.cancel_confirm)
        self.disable_button("pause", "cancel")

    def cancel_confirm(self, widget, response_id):
        _ = self.lang.gettext
        widget.destroy()
        if response_id == Gtk.ResponseType.CANCEL:
            self.enable_button("pause", "cancel")
            return
        
        self.labe = Gtk.Label()
        # 2023.7.26弹窗
        # self.labels['stop'] = self._gtk.ButtonImage("emergency", "emergency","color1",1,1)
        # self.labels['stop'].connect("clicked", self.temergency_stop)
        self.labe.set_markup(_("<big><b>Bed Leveling,please wait...</b></big>"))
        self.dialog = self._gtk.Dialog_button(self._screen, self.labe)  
        GLib.timeout_add_seconds(277, self.destroy_dialog)
        logging.debug("Canceling auto-leveling")
        gcode = "SET_GCODE_OFFSET Z=0\nG28\nDELTA_CALIBRATE\nG1 X0 Y0 Z50 F1000\nSAVE_CONFIG"
        self._screen._ws.klippy.gcode_script(gcode)
        os.system("sed -i 's/autolevel0/autolevel1/g' /home/pi/KlipperScreen/warning.txt")
    def destroy_dialog(self):
        self.dialog.destroy()     
    # def temergency_stop(self, widget):
    #     _ = self.lang.gettext
    #     if self._config.get_main_config_option('confirm_estop') == "True":
    #         self._screen._confirm_send_action(widget, _("Are you sure you want to run Emergency Stop?"),
    #                                           "printer.emergency_stop")
    #     else:
    #         self._screen._ws.klippy.emergency_stop()
    #     self._screen._ws.klippy.restart_firmware()  
    #     GLib.timeout_add_seconds(10, self.destroy_dialog)   
    def go_to_z0(self, widget, start):
        _ = self.lang.gettext
        script = {"script": "G28\nG1 Z0 F1000"}
        self._screen._confirm_send_action(
            None,
            _("Please remove leveling switch before move Z0"),
            "printer.gcode.script",
            script
        )

        os.system("sed -i 's/autolevel2/autolevel0/g' /home/pi/KlipperScreen/warning.txt")

    def change_bs_delta(self, widget, bs):
        if self.bs_delta == bs:
            return
        logging.info("### BabyStepping " + str(bs))

        ctx = self.labels[str(self.bs_delta)].get_style_context()
        ctx.remove_class("distbutton_active")

        self.bs_delta = bs
        ctx = self.labels[self.bs_delta].get_style_context()
        ctx.add_class("distbutton_active")
        for i in self.bs_deltas:
            if i == self.bs_delta:
                continue
            self.labels[i].set_active(False)
