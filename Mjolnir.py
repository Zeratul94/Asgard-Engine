# Copyright © Gedalya Gordon 2023, all rights reserved. #

from __future__ import annotations

import pygame
from collections.abc import Callable
import typing

from AsgardEngine import Component, SceneComponent, Actor, Pawn
from TupleMath import *

# A PhysicsComponent handles the physics attributes, such as impulses and gravity, of its parent.
# It also handles the blocking of movement when a hit is registered.
class PhysicsComponent(Component):
    def __init__(self, parent: Actor) -> None:
        super().__init__(parent)

        self.collider: CollisionComponent = None
        for comp in self.parent.components:
            if isinstance(comp, CollisionComponent):
                self.collider = comp
                break
        if not self.collider:
            self.collider = BoxCollisionComponent(self.parent)
            self.parent.components.append(self.collider)
    
    def registerHit(self, Hit):
        pass

class Hit2D:
    Location: tuple[int, int]
    Direction: tuple[int, int]

# A CollisionComponent acts as a collider for the parent actor, triggering overlap/hit events.
class CollisionComponent(SceneComponent):
    def __init__(self, parent, offset = (0, 0, 0)) -> None:
        super().__init__(parent,  offset=offset)

        self.HitBindings: list[Callable[[Hit2D], None]] = []
        self.OverlapBindings: list[Callable[[Hit2D], None]] = []

        self.blocksNavigation = False
        # 0 is Ignore, 1 is Overlap, 2 is Hit
        self.responses: dict[str, int] = {Pawn : 2,
                                          #TriggerBox : 1
                                          Actor : 2}
        
        self.worldLoc = addTuple(self.parent.location, self.offset)
    
    def update(self, dSecs):
        super().update(dSecs)

        # Update worldLoc to our new location
        self.worldLoc = addTuple(self.parent.location, self.offset)
    
    def collide(self, otheractor: Actor):
        # Find the collision type to look for: Ignore (0), Hit (2), or Overlap (1)
        collType: typing.Type
        keys = self.responses.keys()
        for key in keys:
            if isinstance(otheractor, key):
                collType = self.responses[key]
                break
        
        # Ignore Collision
        if not collType:
            return
        
        # Hit or Overlap
        for comp in otheractor.components:
            if isinstance(comp, CollisionComponent):
                collO = self.collideCollider(comp)
                if collO:
                    if collType == 2:
                        for binding in self.HitBindings:
                            binding(collO)
                    else:
                        for binding in self.OverlapBindings:
                            binding(collO)
        
    def collideCollider(self, other: CollisionComponent | pygame.Rect | pygame.Mask) -> Hit2D:
        if isinstance(other, BoxCollisionComponent):
            return self.collideCollider(other.rect)

    def BindHit(self, event: Callable[[Hit2D], None]):
        self.HitBindings.append(event)
    def BindOverlap(self, event: Callable[[Hit2D], None]):
        self.OverlapBindings.append(event)

class BoxCollisionComponent(CollisionComponent):
    def __init__(self, parent, offset = (0, 0, 0), size = (50, 50, 50)) -> None:
        super().__init__(parent, offset=offset)
        
        self.rect = self.parent.gameMode.pyg.Rect(self.worldLoc[0] - (size[0]/2),
                                                  self.worldLoc[1] - (size[1]/2),
                                                  size[0], size[1])
    
    def collideCollider(self, other: CollisionComponent | pygame.Rect | pygame.Mask) -> Hit2D:
        sup = super().collideCollider(other)
        if sup: return sup

        if isinstance(other, CircleCollisionComponent):
            return collideCircleWithRect(other, self, forRect=True)
        if isinstance(other, pygame.Rect):
            if pygame.Rect.colliderect(self.rect, other):
                outHit = Hit2D()
                cornerColls = (pygame.Rect.collidepoint(other, self.rect.left, self.rect.top), pygame.Rect.collidepoint(other, self.rect.right, self.rect.top),
                               pygame.Rect.collidepoint(other, self.rect.left, self.rect.bottom), pygame.Rect.collidepoint(other, self.rect.right, self.rect.bottom))
                cCorners = []
                for idx in range(len(cornerColls)):
                    if cornerColls[idx]: cCorners.append(subtractTuple(self.worldLoc, (self.rect.topleft if idx == 0 else self.rect.topright if idx == 1 else self.rect.bottomleft if idx == 2 else self.rect.bottomright)))
                cCornerCount = len(cCorners)
                if cCornerCount == 1:
                    outHit.Direction = normalize(cCorners[0])
                elif cCornerCount == 2:
                    if cCorners[0][0] == cCorners[1][0]:
                        outHit.Direction = normalize((cCorners[0][0], 0))
                    elif cCorners[0][1] == cCorners[1][1]:
                        outHit.Direction = normalize((0, cCorners[0][1]))
                    else:
                        outHit.Direction = (0, 0)
                elif cCornerCount == 3:
                    if cCorners[0][0] == cCorners[1][0]:
                        if cCorners[0][1] == cCorners[2][1]:
                            outHit.Direction = normalize(cCorners[0])
                        else:
                            outHit.Direction = normalize(cCorners[1])
                    elif cCorners[1][0] == cCorners[2][0]:
                        if cCorners[1][1] == cCorners[0][1]:
                            outHit.Direction = normalize(cCorners[1])
                        else:
                            outHit.Direction = normalize(cCorners[2])
                    else:
                        if cCorners[2][1] == cCorners[1][1]:
                            outHit.Direction = normalize(cCorners[2])
                        else:
                            outHit.Direction = normalize(cCorners[0])
                else:
                    outHit.Direction = (0, 0)
                return outHit
            return None

class CircleCollisionComponent(CollisionComponent):
    def __init__(self, parent, offset = (0, 0, 0), radius = 25) -> None:
        super().__init__(parent, offset=offset)
        
        self.radius = radius
    
    def collideCollider(self, other: CollisionComponent | pygame.Rect | pygame.Mask) -> Hit2D:
        sup = super().collideCollider(other)
        if sup: return sup

        if isinstance(other, CircleCollisionComponent):
            if distance(self.worldLoc, other.worldLoc) <= self.radius + other.radius:
                outHit = Hit2D()
                outHit.Direction = normalize((other.worldLoc[0] - self.worldLoc[0], other.worldLoc[1] - self.worldLoc[1]))
                outHit.Location = extend(self.worldLoc, outHit.Direction, self.radius)
                return outHit
            return None
        if isinstance(other, pygame.Rect):
            return collideCircleWithRect(self, other)

def collideCircleWithRect(circ: CircleCollisionComponent, rect: pygame.Rect, forRect = False) -> Hit2D:
    # Source: Cygon on StackOverflow: https://stackoverflow.com/questions/401847/circle-rectangle-collision-detection-intersection
    
    # Find the closest point to the circle within the rectangle
    closestRectPoint = (min(max(circ.worldLoc[0], rect.left), rect.right),
                        min(max(circ.worldLoc[1], rect.top), rect.bottom))
    
    # If the distance is less than the circle's radius, an intersection occurs
    dist = distance(closestRectPoint, circ.worldLoc)
    if dist <= circ.radius:
        outHit = Hit2D()
        outHit.Direction = normalize(subtractTuple(closestRectPoint, circ.worldLoc) if forRect else subtractTuple((circ.worldLoc[0], circ.worldLoc[1]), closestRectPoint))
        outHit.Location = closestRectPoint if forRect else extend((circ.worldLoc[0], circ.worldLoc[1]), outHit.Direction, circ.radius)
        return outHit
    return None