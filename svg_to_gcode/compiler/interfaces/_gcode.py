import warnings
import math

from svg_to_gcode import formulas
from svg_to_gcode.compiler.interfaces import Interface
from svg_to_gcode.geometry import Vector
from svg_to_gcode import TOLERANCES

verbose = False


class Gcode(Interface):

    def __init__(self):
        self.position = None
        self._next_speed = None
        self._current_speed = None

        # Round outputs to the same number of significant figures as the operational tolerance.
        self.precision = abs(round(math.log(TOLERANCES["operation"], 10)))
    
    def set_movement_speed(self, speed):
        self._next_speed = speed
        return ''

    def linear_move(self, x=None, y=None, z=None):

        if self._next_speed is None:
            raise ValueError("Undefined movement speed. Call set_movement_speed before executing movement commands.")

        # Don't do anything if linear move was called without passing a value.
        if x is None and y is None and z is None:
            warnings.warn("linear_move command invoked without arguments.")
            return ''

        # Todo, investigate G0 command and replace movement speeds with G1 (normal speed) and G0 (fast move)
        command = "G1"

        if self._current_speed != self._next_speed:
            self._current_speed = self._next_speed

        command += " F{}".format(self._current_speed)

        # Move if not 0 and not None
        command += " X{:.6f}".format(x) if x is not None else ''
        command += " Y{:.6f}".format(y) if y is not None else ''
        command += " Z{:.6f}".format(z) if z is not None else ''

        if self.position is not None or (x is not None and y is not None):
            if x is None:
                x = self.position.x

            if y is None:
                y = self.position.y

            self.position = Vector(x, y)

        if verbose:
            print("Move to {:.6f}, {:.6f}, {:.6f}".format(x, y, z))

        return command

    def drill_to_safe_position(self):
        safeZposition = 0.1
        return "G1 F120 Z{:.6f}".format(safeZposition)

    def set_drill_to_working_position(self, workingDeep):
        return "G1 F120 Z{:.6f}".format(-1 * workingDeep)

    def set_absolute_coordinates(self):
        return "G90"

    def set_relative_coordinates(self):
        return "G91"

    def dwell(self, milliseconds):
        return "G4 P{}".format(milliseconds)

    def set_origin_at_position(self):
        self.position = Vector(0, 0)
        return "G92 X{:.6f} Y{:.6f} Z{:.6f}".format(0, 0, 0)

    def set_unit(self, unit):
        if unit == "mm":
            return "G21"

        if unit == "in":
            return "G20"

        return ''

    def home_axes(self):
        return "G28"

    def fast_movement(self):
        return "G00"
    
    def right_direction_rotation(self):
        return "M03"