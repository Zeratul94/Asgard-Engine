# Copyright © Gedalya Gordon 2023, all rights reserved. #

from __future__ import annotations
import time

import pygame
from enum import Enum
import threading
from collections.abc import Callable

import Runes

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
        
        # Ideally this would only be called once text becomes necessary, if at all.
        pygame.font.init()

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

    def removeChild(self, child: HUDElement) -> HUDElement:
        if child in self.children:
            self.children.remove(child)
            return child
        return None
    def removeChildren(self, children: list[HUDElement]):
        for child in children:
            if child in self.children:
                self.children.remove(child)
    
    def get_rect(self) -> pygame.Rect:
        pos = self.get_pos()
        w, h = self.get_width(), self.get_height()
        return pygame.Rect(pos[0] - self.alignment[0]*w, pos[1] - self.alignment[1]*h, self.get_width(), self.get_height())
    
    def get_pos(self) -> tuple[float, float]:
        ax = self.anchor[0]
        ay = self.anchor[1]
        ox = self.offset[0]
        oy = self.offset[1]
        
        if isinstance(ax, str):
            posx = self.parent.get_pos()[0] if self.parent else 0
        else:
            posx = ox + ax + (self.parent.get_pos()[0] if self.parent else 0)
        if isinstance(ay, str):
            posy = self.parent.get_pos()[1] if self.parent else 0
        else:
            posy = oy + ay + (self.parent.get_pos()[1] if self.parent else 0)

        return (posx, posy)

    def get_width(self) -> float:
        return self.parent.get_width() if self.parent and isinstance(self.anchor[0], str) else (50 if not self.parent else 50) # FIX!!!
    def get_height(self) -> float:
        return self.parent.get_height() if self.parent and isinstance(self.anchor[1], str) else (50 if not self.parent else 50) # FIX!!!

class CanvasPanel(HUDElement):
    def __init__(self, parent: HUDElement | None = None, offset: tuple[float, float] = (0, 0), anchors: tuple[float | str, float | str] = (0, 0), alignment: tuple[float, float] = (0, 0)) -> None:
        super().__init__(parent, offset, anchors, alignment)
    
    def get_width(self) -> float:
        return self.parent.get_width() if self.parent and isinstance(self.anchor[0], str) else (50 if not self.parent else 50) # FIX!!!
    def get_height(self) -> float:
        return self.parent.get_height() if self.parent and isinstance(self.anchor[1], str) else (50 if not self.parent else 50) # FIX!!!

class Border(HUDElement):
    def __init__(self, brush: pygame.Surface | tuple[int, int, int], collider: pygame.Mask | pygame.Rect | float = None, offset: tuple[float, float] = (0, 0), anchors: tuple[float | str, float | str] = ('fill', 'fill'), alignment: tuple[float, float] = (0.5, 0.5)) -> None:
        super().__init__(None, offset, anchors, alignment)
        self.collider: pygame.Mask | pygame.Rect | float = collider
        self.brush = brush
    
    def draw(self, target: HUD):
        if isinstance(self.brush, pygame.Surface):
            if (isinstance(self.anchor[0], str) and self.brush.get_width() != self.collider.width) or (isinstance(self.anchor[1], str) and self.brush.get_height() != self.collider.height):
                self.brush = pygame.transform.scale(self.brush, (self.collider.width if isinstance(self.anchor[0], str) else self.brush.get_width(), self.collider.height if isinstance(self.anchor[1], str) else self.brush.get_height()))
        if isinstance(self.brush, pygame.Surface):
            drawbrush = self.brush
        else:
            drawbrush = pygame.Surface((self.collider.width, self.collider.height))
            drawbrush.fill(self.brush)
        pos = self.get_pos()
        target.screen.blit(drawbrush, (self.pos[0] - self.collider, self.pos[1] - self.collider) if isinstance(self.collider, float) or isinstance(self.collider, int) else pos)
        super().draw(target)
    
    def get_pos(self) -> tuple[float, float]:
        if self.collider:
            if isinstance(self.collider, pygame.Rect):
                return (self.collider.left - self.alignment[0]*self.collider.width + (self.parent.get_pos()[0] if self.parent else 0) + (self.anchor[0] if not isinstance(self.anchor[0], str) else 0),
                        self.collider.top - self.alignment[1]*self.collider.height + (self.parent.get_pos()[1] if self.parent else 0) + (self.anchor[1] if not isinstance(self.anchor[1], str) else 0))
        return super().get_pos()
    
    def get_width(self) -> float:
        if self.collider:
            if isinstance(self.collider, pygame.Rect):
                return self.collider.width
            if isinstance(self.collider, pygame.Surface):
                return self.collider.get_width()
            return self.collider*2
    
    def get_height(self) -> float:
        if self.collider:
            if isinstance(self.collider, pygame.Rect):
                return self.collider.height
            if isinstance(self.collider, pygame.Surface):
                return self.collider.get_height()
            return self.collider*2

class Button(HUDElement):
    def __init__(self, drawBorder: Border, events: dict[int, Callable[[Button], None]], collider: pygame.Mask | pygame.Rect | float, anchors: tuple[float | str, float | str] = (0, 0), alignment: tuple[float, float] = (0, 0)) -> None:
        # Calculate the offset to pass to the super initialization
        ox = collider.x
        oy = collider.y
        if isinstance(anchors[0], str):
            posx = 1920/2 # FIX!!!
        else:
            posx = ox + anchors[0]
        if isinstance(anchors[1], str):
            posy = 1080/2 # FIX!!!
        else:
            posy = oy + anchors[1]
        offset: tuple[float, float] = (posx, posy)
        
        super().__init__(None, offset, anchors, alignment)
        self.border: Border = drawBorder
        self.border.offset = self.offset
        self.border.anchor = ('fill', 'fill')
        self.border.alignment = self.alignment
        self.border.collider = pygame.Rect(0, 0, collider.width, collider.height)
        self.addChild(self.border)

        self.events: dict[int, Callable[[Button], None]] = events
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
                        self.events[ButtonEvent.Hovered](self)
                    self.hovered = True
                if LMBDown: # Also, if the mouse is pressed, record it and trigger that event.
                    if not self.pressed:
                        if ButtonEvent.Pressed in self.validEvents:
                            self.events[ButtonEvent.Pressed](self)
                        self.pressed = True
                elif self.pressed: # If the mouse is released, record that and trigger that event.
                    if ButtonEvent.Released in self.validEvents:
                        self.events[ButtonEvent.Released](self)
                    self.pressed = False
            elif self.hovered: # If we aren't being hovered, record that and trigger our unhover event.
                if ButtonEvent.Unhovered in self.validEvents:
                    self.events[ButtonEvent.Unhovered](self)
                self.hovered = False
                # Also still check for a release from being pressed.
                if ButtonEvent.Released in self.validEvents and self.pressed and not LMBDown:
                    self.events[ButtonEvent.Released](self)

    def addEvent(self, eventType: int, target: Callable[[Button], None]):
        self.events[eventType] = target

    def get_hovered(self) -> bool:
        (mouseX, mouseY) = pygame.mouse.get_pos()
        # Check if our brush contains the mouse's locations
        borderpos = self.border.get_pos()
        match type(self.border.collider):
            # (Fancy) Image
            case pygame.Mask:
                return False # FIX!!!
            # Rectangle
            case pygame.Rect:
                return self.border.collider.collidepoint(mouseX - borderpos[0], mouseY - borderpos[1])
            # Circle
            case float:
                # alignment = 1 -> offset = -collider
                # alignment = 0.5 -> offset = 0
                # alignment = 0 -> offset = collider
                ctroffset = (self.border.collider * ((self.border.alignment[0]-0.5)*-2), self.border.collider * ((self.border.alignment[1]-0.5)*-2))

                return (mouseX - (borderpos[0] + ctroffset[0]))**2 + (mouseY - (borderpos[1] + ctroffset[1]))**2 <= self.border.collider**2

class Text(HUDElement):
    def __init__(self, justification: int, font: Runes.Font, offset: tuple[float, float] = (0, 0), anchors: tuple[float | str, float | str] = (0, 0), alignment: tuple[float, float] = (0, 0)) -> None:
        super().__init__(None, offset, anchors, alignment)
        self.text: str = None
        self.justification = justification
        self.font: Runes.Font = font
        self.drawSurfs: list[pygame.Surface] = None
    
    def draw(self, target: HUD):
        if self.text != None:
            for i in range(len(self.drawSurfs)):
                target.screen.blit(self.drawSurfs[i], self.get_pos(i))
        super().draw(target)
    
    def setText(self, newText: str):
        self.text = newText
        self.drawSurfs = []
        lines = self.text.split('\n')
        for line in lines:
            self.drawSurfs.append(self.font.pygFont.render(line, True, self.font.color))
    
    def get_width(self) -> float:
        return max(surf.get_width() for surf in self.drawSurfs)
    def get_height(self) -> float:
        return sum(surf.get_height() for surf in self.drawSurfs)
    
    def get_pos(self, line=0) -> tuple[float, float]:
        if line >= len(self.drawSurfs): return 0

        basis = self.parent.get_pos()
        i=0
        voffset = 0
        while i < line:
            voffset += self.drawSurfs[i].get_height()
            i+=1
        
        return (basis[0] + (self.anchor[0] if not isinstance(self.anchor, str) else 0) + self.offset[0] - (self.alignment[0]*self.get_width()) - (0 if self.justification == Runes.Justification.Left
                                                                                                                                            else (self.drawSurfs[line].get_width()/2) if self.justification == Runes.Justification.Center
                                                                                                                                            else  self.drawSurfs[line].get_width()),
                basis[1]+ (self.anchor[1] if not isinstance(self.anchor, str) else 0) + self.offset[1] - (self.alignment[1]*self.get_height()) + voffset)