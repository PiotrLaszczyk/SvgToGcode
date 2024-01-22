from svg_to_gcode.svg_parser import parse_string
from svg_to_gcode.compiler import Compiler, interfaces
from svg_to_gcode.formulas import linear_map


class CustomInterface(interfaces.Gcode):
    def __init__(self):
        super().__init__()
        self.fan_speed = 1

    # Override the laser_off method such that it also powers off the fan.
    #def _laser_off(self):
    #    return "M107;\n" + "M5;"  # Turn off the fan + turn off the laser

    # Override the __set_laser_power method
    #def __set_laser_power(self, power):
    #    if power < 0 or power > 1:
    #        raise ValueError(f"{power} is out of bounds. Laser power must be given between 0 and 1. "
    #                         f"The interface will scale it correctly.")

    #    return f"M106 S255\n" + f"M3 S{linear_map(0, 255, power)};"  # Turn on the fan + change laser power


def run_test(svg_string):

    gcode_compiler = Compiler(CustomInterface, 1000, 300, 0, dwell_time=400)

    curves = parse_string(svg_string)
    gcode_compiler.append_curves(curves)
    return gcode_compiler.compile()
