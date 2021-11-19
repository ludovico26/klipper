

import logging


class StableZHome:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name()
        self.steppers = stepper.PrinterStepper(config)
        self.gcode = self.printer.lookup_object('gcode')
        gcode_macro = self.printer.load_object(config, 'gcode_macro')
        self.before_homing_gcode = gcode_macro.load_template(config, 'gcode')
        self.default_max_retries = config.getint("retries", 20, minval=0)
        self.default_retry_tolerance = \
            config.getfloat("retry_tolerance", 1 / 400., above=1/1000.)
        self.default_window = config.getint("window", 4, minval=3)
        # Register STABLE_Z_HOME command
        self.gcode.register_command(
            'STABLE_Z_HOME', self.cmd_STABLE_Z_HOME,
            desc=self.cmd_STABLE_Z_HOME_help)
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
    cmd_STABLE_Z_HOME_help = (
        "Repeatedly home Z until the Z stepper position stabilizes")
    def cmd_STABLE_Z_HOME(self, gcmd):
        max_retries = gcmd.get_int('RETRIES', self.default_max_retries,
                                   minval=0)
        retry_tolerance = gcmd.get_float('RETRY_TOLERANCE',
                                         self.default_retry_tolerance,
                                         minval=1/1000.)
        window = gcmd.get_int('WINDOW', self.default_window, minval=3)

        toolhead = self.printer.lookup_object('toolhead', None)
        if toolhead is None:
            raise gcmd.error("Printer not ready")
        kin = toolhead.get_kinematics()

        # Check X and Y are homed first.
        curtime = self.printer.get_reactor().monotonic()
        homed_axes = kin.get_status(curtime)['homed_axes']
        if 'x' not in homed_axes or 'y' not in homed_axes:
            raise gcmd.error("Must home X and Y axes first")

        steppers = kin.get_steppers()
        stepper = None
        for s in steppers:
            if s.get_name().startswith('stepper_z'):
                stepper = s
                break
        if stepper is None:
            raise gcmd.error("No Z steppers found")

        self.gcode.respond_info(
            'Stable Z home: %.4f tolerance, window %d, %d max retries\n'
            % (retry_tolerance, window, max_retries))

        mcu_z_readings = []
        retries = 1
        retry_tolerance += 1e-4  # allow for floating point rounding errors
        while retries <= max_retries:
            try:
                self.gcode.run_script_from_command(
                    self.before_homing_gcode.render())
            except Exception:
                logging.exception("Exception running pre-home script")
                raise self.gcode.error('Pre-home Gcode failed')

            self.gcode.run_script_from_command('G28 Z')

            mcu_position_offset = -stepper.mcu_to_commanded_position(0)
            mcu_pos = stepper.get_commanded_position() + mcu_position_offset
            mcu_z_readings.append(mcu_pos)
            mcu_z_readings = mcu_z_readings[-window:]
            if len(mcu_z_readings) == window:
                window_range = max(mcu_z_readings) - min(mcu_z_readings)
            else:
                window_range = None

            window_range_str = \
                '%.4f' % (window_range,) if window_range is not None else '-'
            self.gcode.respond_info(
                'Retry %d: %s position %.4f, window range %s\n'
                % (retries, stepper.get_name(), mcu_pos, window_range_str))

            if window_range is not None and window_range <= retry_tolerance:
                self.gcode.respond_info('Succeeded\n')
                break

            retries += 1

        if retries > max_retries:
            raise self.gcode.error('Max retries exceeded\n')


def load_config(config):
    return StableZHome(config)
