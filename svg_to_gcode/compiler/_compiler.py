import typing
import warnings

from svg_to_gcode.compiler.interfaces import Interface
from svg_to_gcode.geometry import Curve, Line
from svg_to_gcode.geometry import LineSegmentChain
from svg_to_gcode import UNITS, TOLERANCES


class Compiler:
    """
    The Compiler class handles the process of drawing geometric objects using interface commands and assembling
    the resulting numerical control code.
    """

    def __init__(self, interface_class: typing.Type[Interface], movement_speed, cutting_speed, pass_depth,
                 dwell_time=0, unit=None, custom_header=None, custom_footer=None):
        """

        :param interface_class: Specify which interface to use. The most common is the gcode interface.
        :param movement_speed: the speed at which to move the tool when moving. (units are determined by the printer)
        :param cutting_speed: the speed at which to move the tool when cutting. (units are determined by the printer)
        :param pass_depth: AKA, the depth your drilling machine cuts in a pass.
        :param dwell_time: the number of ms the tool should wait before moving to another cut. Useful for pen plotters.
        :param unit: specify a unit to the machine
        :param custom_header: A list of commands to be executed before all generated commands. Default is [drill_to_safe_position,]
        :param custom_footer: A list of commands to be executed after all generated commands. Default is [drill_to_safe_position,]
        """
        self.interface = interface_class()
        self.movement_speed = movement_speed
        self.cutting_speed = cutting_speed
        self.pass_depth = abs(pass_depth)
        self.dwell_time = dwell_time
        self.custom_header = custom_header
        self.custom_footer = custom_footer
        self.unit = unit

        if (self.unit is not None) and (self.unit not in UNITS):
            raise ValueError(f"Unknown unit {self.unit}. Please specify one of the following: {UNITS}")

        if self.custom_header is not None:
            self.header = [self.interface.fast_movement(), 
                           self.interface.set_unit(self.unit), 
                           self.interface.right_direction_rotation(), 
                           self.interface.set_initial_coordinates(), 
                           self.interface.set_absolute_coordinates(),
                           self.custom_header
                           ]
        else:
            self.header = [self.interface.fast_movement(), 
                           self.interface.set_unit(self.unit), 
                           self.interface.right_direction_rotation(), 
                           self.interface.set_initial_coordinates(),
                           self.interface.set_absolute_coordinates(),
                           ]  #, self.interface.drill_to_safe_position()

        if self.custom_footer is not None:
            self.footer = self.custom_footer
        else:
            self.footer = [self.interface.drill_to_safe_position()]

        self.body = []

    def compile(self, passes=1):

        """
        Assembles the code in the header, body and footer, saving it to a file.


        :param passes: the number of passes that should be made. Every pass the machine moves_down (z-axis) by
        self.pass_depth and self.body is repeated.
        :return returns the assembled code. self.header + [self.body, -self.pass_depth] * passes + self.footer
        """

        if len(self.body) == 0:
            warnings.warn("Compile with an empty body (no curves). Is this intentional?")

        gcode = []

        gcode.extend(self.header)
        for i in range(passes):
            gcode.extend(self.body)

            if i < passes - 1:  # If it isn't the last pass, put drill to safe position and move down
                gcode.append(self.interface.drill_to_safe_position())
                gcode.append(self.interface.set_initial_coordinates())

                #if self.pass_depth > 0:
                #    gcode.append(self.interface.set_relative_coordinates())
                #    gcode.append(self.interface.linear_move(z=-self.pass_depth))
                #    gcode.append(self.interface.set_absolute_coordinates())

        gcode.extend(self.footer)

        gcode = filter(lambda command: len(command) > 0, gcode)

        gcodeWithLinenNmbers = []
        lineCounter = 1
        for _code in gcode:
            gcodeWithLinenNmbers.append("N{} {}".format(lineCounter, _code))
            lineCounter += 1

        return '\n'.join(gcodeWithLinenNmbers)

    def compile_to_file(self, file_name: str, passes=1):
        """
        A wrapper for the self.compile method. Assembles the code in the header, body and footer, saving it to a file.

        :param file_name: the path to save the file.
        :param passes: the number of passes that should be made. Every pass the machine moves_down (z-axis) by
        self.pass_depth and self.body is repeated.
        """

        with open(file_name, 'w') as file:
            file.write(self.compile(passes=passes))

    def append_line_chain(self, line_chain: LineSegmentChain):
        """
        Draws a LineSegmentChain by calling interface.linear_move() for each segment. The resulting code is appended to
        self.body
        """

        if line_chain.chain_size() == 0:
            warnings.warn("Attempted to parse empty LineChain")
            return []

        code = []

        start = line_chain.get(0).start

        # Don't dwell and turn drilling machine to safe position if the new start is at the current position
        if self.interface.position is None or abs(self.interface.position - start) > TOLERANCES["operation"]:

            code = [self.interface.drill_to_safe_position(), 
                    self.interface.set_movement_speed(self.movement_speed),
                    self.interface.linear_move(start.x, start.y, 5.0), 
                    self.interface.set_movement_speed(self.cutting_speed),
                    self.interface.set_drill_to_working_position(self.pass_depth)]

            if self.dwell_time > 0:
                code = [self.interface.dwell(self.dwell_time)] + code

        for line in line_chain:
            code.append(self.interface.linear_move(line.end.x, line.end.y, -self.pass_depth))

        self.body.extend(code)

    def append_curves(self, curves: [typing.Type[Curve]]):
        """
        Draws curves by approximating them as line segments and calling self.append_line_chain(). The resulting code is
        appended to self.body
        """

        for curve in curves:
            line_chain = LineSegmentChain()

            approximation = LineSegmentChain.line_segment_approximation(curve)

            line_chain.extend(approximation)

            self.append_line_chain(line_chain)
