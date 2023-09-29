# Copyright © Gedalya Gordon 2023, all rights reserved. #

from __future__ import annotations

import pygame
from enum import Enum
from collections.abc import Callable

class ButtonEvent(Enum):
    Released = 0
    Hovered = 1
    Unhovered = 2
    Pressed = 3

class HUD:
    def __init__(self, canvasOver: HUDElement, canvasUnder: HUDElement, screen: pygame.Surface) -> None:
        self.screen: pygame.Surface = screen
        self.canvasOver: HUDElement = canvasOver
        self.canvasUnder: HUDElement = canvasUnder
        self.rectsToDrawOver: list[tuple[pygame.Rect, tuple[int, int, int] | tuple[int, int, int, int], tuple[int, int, int], int]] = []
        self.rectsToDrawUnder: list[tuple[pygame.Rect, tuple[int, int, int] | tuple[int, int, int, int], tuple[int, int, int], int]] = []

    def draw_under(self):
        self.canvasUnder.update()
        self.canvasUnder.draw(self)
        for rectInfo in self.rectsToDrawUnder:
            if len(rectInfo[1]) == 4:
                rectSurf = pygame.Surface((rectInfo[0].width, rectInfo[0].height))
                rectSurf.set_alpha(rectInfo[1][3])
                rectSurf.fill((rectInfo[1][0], rectInfo[1][1], rectInfo[1][2]))
                self.screen.blit(rectSurf, (rectInfo[0].x, rectInfo[0].y))
            else:
                self.screen.fill(rectInfo[1], rectInfo[0])
            pygame.draw.rect(self.screen, rectInfo[2], rectInfo[0], width= rectInfo[3])
        
        self.rectsToDrawUnder.clear()

    def draw_over(self):
        self.canvasOver.update()
        self.canvasOver.draw(self)
        for rectInfo in self.rectsToDrawOver:
            if len(rectInfo[1]) == 4:
                rectSurf = pygame.Surface((rectInfo[0].width, rectInfo[0].height))
                rectSurf.set_alpha(rectInfo[1][3])
                rectSurf.fill((rectInfo[1][0], rectInfo[1][1], rectInfo[1][2]))
                self.screen.blit(rectSurf, (rectInfo[0].x, rectInfo[0].y))
            else:
                self.screen.fill(rectInfo[1], rectInfo[0])
            pygame.draw.rect(self.screen, rectInfo[2], rectInfo[0], width= rectInfo[3])
        
        self.rectsToDrawOver.clear()

    def add_rect_bordered_over(self, rect: pygame.Rect, rectColor: tuple[int, int, int] | tuple[int, int, int, int], borderColor: tuple[int, int, int], borderWidth: int):
        self.rectsToDrawOver.append((rect, rectColor, borderColor, borderWidth))
    def add_rect_bordered_under(self, rect: pygame.Rect, rectColor: tuple[int, int, int] | tuple[int, int, int, int], borderColor: tuple[int, int, int], borderWidth: int):
        self.rectsToDrawUnder.append((rect, rectColor, borderColor, borderWidth))

class HUDElement:
    def __init__(self, parent: HUDElement = None, offset: tuple[float, float] = (0, 0), anchors: tuple[float | str, float | str] = (0, 0), alignment: tuple[float, float] = (0, 0)) -> None:
        self.anchor: tuple[float | str, float | str] = anchors
        self.offset: tuple[float, float] = offset
        self.alignment: tuple[float, float] = alignment
        self.parent: HUDElement = parent
        self.children: list[HUDElement] = []
    
    def draw(self, target: HUD):
        for child in self.children:
            child.draw(target)
    
    def update(self):
        for child in self.children:
            child.update()

    def addChild(self, widget: HUDElement) -> HUDElement:
        self.children.append(widget)
        widget.parent = self
        return widget
    
    def get_rect(self) -> pygame.Rect:
        pos = self.get_pos()
        w, h = self.get_width(), self.get_height()
        return pygame.Rect(pos[0] - self.alignment[0]*w, pos[1] - self.alignment[1]*h, self.get_width(), self.get_height())
    
    def get_pos(self) -> tuple[float, float]:
        ax = self.anchor[0]
        ay = self.anchor[1]
        ox = self.offset[0]
        oy = self.offset[1]

        if isinstance(ax, float):
            posx = ox + ax
        else:
            posx = self.parent.get_width() if self.parent else 1920/2
        if isinstance(ay, float):
            posy = oy + ay
        else:
            posy = self.parent.get_height() if self.parent else 1080/2
        
        return (posx, posy)

    def get_width(self) -> float:
        return self.parent.get_width() if self.parent and not isinstance(self.anchor[0], float) else (50 if not self.parent else 50) # FIX!!!
    def get_height(self) -> float:
        return self.parent.get_height() if self.parent and not isinstance(self.anchor[1], float) else (50 if not self.parent else 50) # FIX!!!

class CanvasPanel(HUDElement):
    def __init__(self, parent: HUDElement | None = None, offset: tuple[float, float] = (0, 0), anchors: tuple[float | str, float | str] = (0, 0), alignment: tuple[float, float] = (0, 0)) -> None:
        super().__init__(parent, offset, anchors, alignment)
    
    def get_width(self):
        return self.parent.get_width() if self.parent and not isinstance(self.anchor[0], float) else (50 if not self.parent else 50) # FIX!!!
    def get_height(self):
        return self.parent.get_height() if self.parent and not isinstance(self.anchor[1], float) else (50 if not self.parent else 50) # FIX!!!

class Border(HUDElement):
    def __init__(self, brush: pygame.Surface | tuple[int, int, int], offset: tuple[float, float] = (0, 0), anchors: tuple[float | str, float | str] = ('fill', 'fill'), alignment: tuple[float, float] = (0.5, 0.5)) -> None:
        super().__init__(None, offset, anchors, alignment)
        self.collider: pygame.Mask | pygame.Rect | float = pygame.Rect(self.get_pos()[0], self.get_pos()[1], self.get_width(), self.get_height())
        self.brush = brush
    
    def draw(self, target: HUD):
        drawpos = self.get_pos()
        if isinstance(self.brush, pygame.Surface):
            drawbrush = self.brush
        else:
            drawbrush = pygame.Surface((self.collider.width, self.collider.height))
            drawbrush.fill(self.brush)
        target.screen.blit(drawbrush, (drawpos[0] - self.alignment[0]*self.get_width(), drawpos[1] - self.alignment[1]*self.get_height()))
        super().draw(target)

class Button(HUDElement):
    def __init__(self, drawBorder: Border, events: dict[int, Callable[[None], None]], collider: pygame.Mask | pygame.Rect | float, anchors: tuple[float | str, float | str] = (0, 0), alignment: tuple[float, float] = (0, 0)) -> None:
        # Calculate the offset to pass to the super initialization
        ox = collider.x
        oy = collider.y
        if isinstance(anchors[0], float):
            posx = ox + anchors[0]
        else:
            posx = 1920/2 # FIX!!!
        if isinstance(anchors[1], float):
            posy = oy + anchors[1]
        else:
            posy = 1080/2 # FIX!!!
        offset: tuple[float, float] = (posx, posy)
        
        super().__init__(offset, anchors, alignment)
        self.border: Border = drawBorder
        self.border.offset = self.offset
        self.border.anchor = self.anchor
        self.border.alignment = self.alignment
        self.border.collider = collider
        self.addChild(self.border)

        self.events: dict[int, Callable[[None], None]] = events
        self.validEvents = self.events.keys()
        self.hovered = False
        self.pressed = False
    
    def update(self):
        super().update()
        if len(self.events) > 0:
            LMBDown = pygame.mouse.get_pressed()[0]
            if self.get_hovered(): # If this button is being hovered, record that and trigger our hover event.
                if not self.hovered:
                    if ButtonEvent.Hovered in self.validEvents:
                        self.events[ButtonEvent.Hovered]()
                    self.hovered = True
                if LMBDown: # Also, if the mouse is pressed, record it and trigger that event.
                    if not self.pressed:
                        if ButtonEvent.Pressed in self.validEvents:
                            self.events[ButtonEvent.Pressed]()
                elif self.pressed: # If the mouse is released, record that and trigger that event.
                    if ButtonEvent.Released in self.validEvents:
                        self.events[ButtonEvent.Released]()
                    self.pressed = False
            elif self.hovered: # If we aren't being hovered, record that and trigger our unhover event.
                if ButtonEvent.Unhovered in self.validEvents:
                    self.events[ButtonEvent.Unhovered]()
                self.hovered = False
                # Also still check for a release from being pressed.
                if ButtonEvent.Released in self.validEvents and self.pressed and not LMBDown:
                    self.events[ButtonEvent.Released]()

    def addEvent(self, eventType: int, target: Callable[[None], None]):
        self.events[eventType] = target

    def get_hovered(self) -> bool:
        (mouseX, mouseY) = pygame.mouse.get_pos()
        # Check if our brush contains the mouse's locations
        match type(self.border.collider):
            # (Fancy) Image
            case pygame.Mask:
                return False # FIX!!!
            # Rectangle
            case pygame.Rect:
                return self.border.collider.collidepoint(mouseX, mouseY)
            # Circle
            case float:
                borderpos = self.border.get_pos()
                
                # alignment = 1 -> offset = -collider
                # alignment = 0.5 -> offset = 0
                # alignment = 0 -> offset = collider
                ctroffset = (self.border.collider * ((self.border.alignment[0]-0.5)*-2), self.border.collider * ((self.border.alignment[1]-0.5)*-2))

                return (mouseX - (borderpos[0] + ctroffset[0]))**2 + (mouseY - (borderpos[1] + ctroffset[1]))**2 <= self.border.collider**2