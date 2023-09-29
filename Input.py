# Copyright © Gedalya Gordon 2023, all rights reserved. #

import pygame
from enum import Enum
from collections.abc import Callable

from AsgardEngine import Component

class Mouse(Enum):
    LMB = 0
    MMB = 1
    RMB = 2

    X = 3
    Y = 4

# An InputComponent maps inputs (such as key presses and mouse movement) to methods of its parent.
class InputComponent(Component):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.events: dict[int, Callable[[None], None]] = {}
        self.mouseevents: dict[int, Callable[[any], None]] = {}
    
    def update(self, dSecs):
        super().update(dSecs)
        if self.events:
            pressed = pygame.key.get_pressed()
            for inp in self.events.keys():
                if pressed[inp]: self.events[inp]()
        if self.mouseevents:
            pressed = pygame.mouse.get_pressed()
            mousekeys = self.mouseevents.keys()
            for i in (0, 1, 2):
                if i in mousekeys and pressed[i]: self.mouseevents[i]()
            
            mousepos = pygame.mouse.get_pos()
            if 3 in mousekeys:
                # Mouse X-Axis
                self.mouseevents[3](mousepos[0])
            if 4 in mousekeys:
                # Mouse Y-Axis
                self.mouseevents[4](mousepos[1])
    
    # The code 'inputcomp.Bind(pyg.K_UP, someactor.somefunc)' creates
    # a binding such that, when the input pyg.K_UP is triggered (the
    # up arrow-key is pressed) someactor.somefunc() will be executed.
    def Bind(self, input: int, targetevent: Callable[[None], None]):
        self.events[input] = targetevent
    def BindMulti(self, inputs: list[int], targetevents: list[Callable[[None], None]]):
        for i in range(len(inputs)):
            self.Bind(inputs[i], targetevents[i])
    def BindAlts(self, inputs: list[int], targetevent: Callable[[None], None]):
        for i in range(len(inputs)):
            self.Bind(inputs[i], targetevent)
    
    # Mouse and Keyboard events must be handled separately, because of
    # how Pyame handles mouse input
    def BindMouse(self, mousebutton: int, targetevent: Callable[[None], None]):
        self.mouseevents[mousebutton] = targetevent
    def BindMouseMulti(self, mousebuttons: list[int], targetevents: list[Callable[[None], None]]):
        for i in range(len(mousebuttons)):
            self.BindMouse(mousebuttons[i], targetevents[i])
    def BindMouseAlts(self, mousebuttons: list[int], targetevent: Callable[[None], None]):
        for i in range(len(mousebuttons)):
            self.BindMouse(mousebuttons[i], targetevent)
    def BindMouseAxis(self, mouseaxis: int, targetevent: Callable[[float], None]):
        self.mouseevents[mouseaxis] = targetevent
    def BindMouseAxes(self, targetevX: Callable[[int], None], targetevY: Callable[[int], None]):
        self.mouseevents[3] = targetevX
        self.mouseevents[4] = targetevY