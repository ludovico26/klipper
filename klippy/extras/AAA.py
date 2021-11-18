import math, logging
import stepper, chelper

class ModifyRotation:
    def __init__(self, config, extruder_num):
        self.printer = config.get_printer()
        self.name = config.get_name()
        toolhead = self.printer.lookup_object('toolhead')
        self.stepper = stepper.PrinterStepper(config)
        toolhead = self.printer.lookup_object('toolhead')
        gcode = self.printer.lookup_object('gcode')
        if self.name == 'stepper_z':
            gcode.register_mux_command("SET_Z_DISTANCE",
                                       "STEPPER_Z",self.name,
                                       self.cmd_SET_Z_DISTANCE,
                                   desc=self.cmd_SET_Z_DISTANCE_help)
    cmd_SET_Z_DISTANCE_help = "Set extruder step distance"
    def cmd_SET_Z_DISTANCE(self, gcmd):
        toolhead = self.printer.lookup_object('toolhead')
        dist = gcmd.get_float('DISTANCE', None, above=0.)
        if dist is None:
            step_dist = self.stepper.get_step_dist()
            gcmd.respond_info("Stepper_z '%s' step distance is %0.6f"
                              % (self.name, step_dist))
            return
        toolhead.flush_step_generation()
        self.stepper.set_step_dist(dist)
        gcmd.respond_info("Stepper_z '%s' step distance set to %0.6f"
                          % (self.name, dist))
    def get_name(self):
        return self.name
def load_config(config):
    return ModifyRotation(config)
