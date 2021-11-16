import logging
import stepper

class RotationDistanceModifier:
    def _init_(self,config):
        self.printer = config.get_printer()
        self.steppers= stepper.PrinterStepper(config)
        gcode.register_mux_command("SET_STEPPER_STEP_DISTANCE", "STEPPER",
                                   self.name, self.cmd_SET_STEP_DISTANCE,
                                   desc=self.cmd_SET_STEP_DISTANCE_help)
    cmd_SET_STEP_DISTANCE_help = "Set extruder step distance"
    def cmd_SET_STEP_DISTANCE(self, gcmd):
        toolhead = self.printer.lookup_object('toolhead')
        dist = gcmd.get_float('DISTANCE', None, above=0.)
        if dist is None:
            step_dist = self.stepper.get_step_dist()
            gcmd.respond_info("Stepper '%s' step distance is %0.6f"
                              % (self.name, step_dist))
            return
        toolhead.flush_step_generation()
        self.stepper.set_step_dist(dist)
        gcmd.respond_info("Stepper '%s' step distance set to %0.6f"
                          % (self.name, dist))
def load_config(config):
    return RotationDistanceModifier(config)
