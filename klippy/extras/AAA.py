import logging
class RotationDistanceModifier:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name()
        self.steppers = stepper.PrinterStepper(config)
        config.getboolean("enable", False)
        self.gcode = self.printer.lookup.object('gcode')
        gcode.register_mux_command("SET_STEPPER_ROTATION_DISTANCE",
                                   "STEPPER",self.name,
                                   self.cmd_SET_STEPPER_ROTATION,
                                   desc=self.cmd_cmd_SET_STEPPER_ROTATION_help)
        gcode.register_mux_command("SET_STEP_DISTANCE", "STEPPER",
                                   self.name, self.cmd_SET_STEP_DISTANCE,
                                   desc=self.cmd_SET_STEP_DISTANCE_help)
    cmd_SET_STEP_DISTANCE_help = "Set step dist of individual stepper"
    def cmd_SET_STEP_DISTANCE(self, gcmd):
        toolhead = self.printer.lookup_object('toolhead')
        stepper_name = gcmd.get('STEPPER', None)
        dist = gcmd.get_float('DISTANCE', None, above=0.)
        if stepper_name not in self.steppers:
            gcmd.respond_info('SET_STEPPER_ENABLE: Invalid stepper "%s"'
                              % (stepper_name,))
            return
        if dist is None:
            step_dist = self.stepper.get_step_dist()
            gcmd.respond_info("stepper '%s' step distance is %0.6f"
                              % (self.name, step_dist))
            return
        toolhead.flush_step_generation()
        self.stepper.set_step_dist(dist)
        rotation_dist = gcmd.get_float('DISTANCE', above=0.)
        gcmd.respond_info(
            "stepper '%s' step distance set to %0.6f"
            % (self.name, dist))
    cmd_SET_STEPPER_ROTATION_help = "Change rot dist of stepper"
    def cmd_SET_STEPPER_ROTATION(self, gcmd):
        toolhead = self.printer.lookup_object('toolhead')
        stepper_name = gcmd.get('STEPPER', None)
        dist = gcmd.get_float('DISTANCE', None, above=0.)
        if stepper_name not in self.steppers:
            gcmd.respond_info('SET_STEPPER_DISTANCE: Invalid stepper "%s"'
                              % (stepper_name,))
            return
        if dist is None:
            step_dist = self.stepper.get_step_dist()
            gcmd.respond_info("stepper '%s' step distance is %0.6f"
                              % (stepper_name, step_dist))
            return
        toolhead.flush_step_generation()
        configfile = self.printer.lookup_object('configfile')
        configfile.set(stepper_name, "rotation_distance", dist)
        gcmd.respond_info("stepper '%s' rotation distance set to %0.6f"
                          % (stepper_name, dist))
        self.gcode.respond_info(
            "The SAVE_CONFIG command will update the printer config\n"
            "file with these parameters and restart the printer.")
    def get_name(self):
        return self.name
def load_config(config):
    return RotationDistanceModifier(config)
