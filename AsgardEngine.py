# Copyright © Gedalya Gordon 2023, all rights reserved. #

from __future__ import annotations

import pygame
import gc
import typing
import threading

from TupleMath import *

#Actor

DEFAULTANIM = [pygame.transform.scale(pygame.image.load("C:/Users/ghmrg/Documents/Image Files/VikingSprite.png"), (50, 50)),
               pygame.transform.scale(pygame.image.load("C:/Users/ghmrg/Documents/Image Files/Viking/VikingSprite1.png"), (50, 50)),
               pygame.transform.scale(pygame.image.load("C:/Users/ghmrg/Documents/Image Files/Viking/VikingSprite2.png"), (50, 50)),
               pygame.transform.scale(pygame.image.load("C:/Users/ghmrg/Documents/Image Files/Viking/VikingSprite1.png"), (50, 50)),
               pygame.transform.scale(pygame.image.load("C:/Users/ghmrg/Documents/Image Files/VikingSprite.png"), (50, 50)),]

# A Controller __?
class Controller():
    def __init__(self) -> None:
        for obj in gc.get_objects():
            if isinstance(obj, GameMode):
                self.gameMode = obj
                break
        self.controlledPawn: Pawn = None
    
    def update(self, dSecs):
        pass

# A PlayerController possesses a player character and does __?
class PlayerController(Controller):
    def __init__(self) -> None:
        super().__init__()

        self.activeCamera: CameraComponent = None
    
    def update(self, dSecs):
        super().update(dSecs)

        if not self.activeCamera:
            for comp in self.controlledPawn.components:
                if isinstance(comp, CameraComponent):
                    self.activeCamera = comp
                    break

'''
A Component is an object that is attached to an Actor and adds functionality to it.
Its parent is the object it is attached to.
'''
class Component():
    def __init__(self, parent: Actor) -> None:
        super().__init__()

        self.parent = parent
    
    def update(self, dSecs):
        pass

# A SceneComponent is a Component that has a transform in the world
class SceneComponent(Component):
    def __init__(self, parent, offset = (0, 0, 0)) -> None:
        super().__init__(parent)

        self.offset = offset

# A CharacterMovementComponent is attached to a Character and handles its movement in the game world.
class CharacterMovementComponent(Component):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.groundSpeed = 5
        self.maxGroundSpeed = self.groundSpeed
        self.speed = self.groundSpeed
        self.jumpForce = 7.5
        self.terminalVelocity = 10
        if self.parent.gameMode.mode == 'side':
            self.physComp = Mjolnir.PhysicsComponent(self.parent)
        self.idleImage = [self.parent.renderComp.image[0]] # temp/weird
        self.runImage = self.parent.renderComp.image

    def movementInput(self, direction: tuple[float, float], magnitude: float = 1):
        if direction[0] != 0 or direction[1] != 0:
            self.parent.rotation = (self.parent.rotation[0], self.parent.rotation[1], -90.0 - math.degrees(math.atan2(direction[1], direction[0])))
                                                                                    # get the sign of velocity[0] and negate it
        #if direction[0] == 0 and self.parent.velocity[0] != 0: direction = (-abs(self.parent.velocity[0])/self.parent.velocity[0], direction[1], direction[2])
        if self.parent.gameMode.mode == 'top-down':                                 # get the sign of velocity[1] and negate it
            #if direction[1] == 0 and self.parent.velocity[1] != 0: direction = (direction[0], -abs(self.parent.velocity[1])/self.parent.velocity[1], direction[2])
            self.parent.velocity = addTuple(self.parent.velocity, scale(direction, magnitude*self.speed))
        elif self.parent.gameMode.mode == 'side':
            scaledtup = scale(direction, magnitude*self.speed)
            self.parent.velocity = addTuple(self.parent.velocity, (scaledtup[0], direction[1] * magnitude * self.jumpForce, scaledtup[2]))
        if direction[0] == 0 and direction[1] == 0:
            if self.parent.renderComp.image == self.runImage: self.parent.renderComp.image = self.idleImage
            self.parent.renderComp.currentImage = self.idleImage[0]
        else:
            if self.parent.renderComp.image == self.idleImage: self.parent.renderComp.currentImage = self.runImage[0]
            self.parent.renderComp.image = self.runImage

# A RenderComponent causes an actor to be drawn to the screen at its location.
# It can also render animations from a flipbook list.
class ActorRenderComponent(Component):
    def __init__(self, parent, drawOffset = (-25, -25, 0)) -> None:
        super().__init__(parent=parent)
        self.image = DEFAULTANIM
        self.currentImage = self.image[0]
        self.renderOffset = self.desiredOffset = drawOffset
        self.mask = [pygame.mask.from_surface(frame) for frame in self.image]
        self.currentMask = self.mask[0]
        self.imgCenter: tuple[int, int] = (0, 0)
    
    def update(self, dSecs):
        super().update(dSecs)
        self.draw()
        newFrameIdx = (self.image.index(self.currentImage) + 1) % len(self.image)
        self.currentImage = pygame.transform.rotate(self.image[newFrameIdx], self.parent.rotation[2])
        self.currentMask = self.mask[newFrameIdx] if abs(self.parent.rotation[2]) <= 1 else pygame.mask.from_surface(self.currentImage)
        self.imgCenter = self.currentImage.get_rect(topleft = (self.parent.location[0] + self.renderOffset[0], self.parent.location[1] + self.renderOffset[1])).center

    def draw(self):
        img_rect = self.currentImage.get_rect(center = self.imgCenter)
        self.parent.gameMode.screen.blit(self.currentImage, img_rect)

# A CameraComponent views the world. So far, only one camera can exist in
# the world at a time or they will all try to override each other.
class CameraComponent(SceneComponent):
    def __init__(self, parent, offset = (0, 0, 20)) -> None:
        super().__init__(parent, offset=offset)

        self.projection = addTuple(self.offset, self.parent.location)
    
    def update(self, dSecs):
        super().update(dSecs)

        self.projection = addTuple(self.offset, self.parent.location)
        for obj in gc.get_objects():
            if isinstance(obj, ActorRenderComponent):
                obj.renderOffset = subtractTuple(obj.desiredOffset, self.projection)

import Mjolnir

'''
An Actor is the most basic game entity. It can be spawned into
the world, rotated, and populated with Components to add
functionality. It is meant to be subclassed to create the specific
entities necessary for a game, such as characters, particle
effects, trigger boxes, and terrain (as just a few examples).
'''
class Actor(pygame.sprite.Sprite):
    def __init__(self, location = (0, 0, 0), rotation = (0, 0, 0), renderable = False, physical = False) -> None:
        super().__init__()
        self.location = location
        self.rotation = rotation
        self.velocity = (0, 0, 0)
        self.components = []
        for obj in gc.get_objects():
            if isinstance(obj, GameMode):
                self.gameMode = obj
                break
        if renderable:
            self.renderComp = ActorRenderComponent(self)
            self.components.append(self.renderComp)
        if physical:
            self.physicsComp = Mjolnir.PhysicsComponent(self)
            self.components.append(self.physicsComp)
    
    def update(self, dSecs):
        self.location = (self.location[0] + self.velocity[0], self.location[1] + self.velocity[1], self.location[2] + self.velocity[2])
        self.velocity = (0, 0, 0)
        for component in self.components: component.update(dSecs)

'''
A Pawn is an Actor that can be "possessed" by a controller.
Pawns are renderable and have physics enabled by default.
'''
class Pawn(Actor):
    def __init__(self, location = (0, 0, 0), rotation = (0, 0, 0), controller = None) -> None:
        super().__init__(location, rotation, renderable=True, physical=True)

        self.controller = controller if controller else AI.AIController(self.gameMode.navmesh)
        self.controller.controlledPawn = self

import Input

# A Character is a Pawn with built-in input-based movement
class Character(Pawn):
    def __init__(self, location = (0, 0, 0), rotation = (0, 0, 0), controller = None) -> None:
        super().__init__(location, rotation, controller=controller)

        self.components = [component for component in self.components if type(component) != Mjolnir.CollisionComponent]
        self.capsuleComp = Mjolnir.CircleCollisionComponent(self)
        self.components.append(self.capsuleComp)
        self.physicsComp.collider = self.capsuleComp

        self.moveComp = CharacterMovementComponent(self)
        self.inpComp = Input.InputComponent(self)
        self.components.extend((self.moveComp, self.inpComp))

        self.movecommands = [0] * 4
    
    def update(self, dSecs):
        super().update(dSecs)

        self.moveComp.movementInput((self.movecommands[1] - self.movecommands[0], self.movecommands[3] - self.movecommands[2], 0))
        self.movecommands = [0] * 4

    def addMoveUp(self):
        self.movecommands[2] = 1
    def addMoveDown(self):
        self.movecommands[3] = 1
    def addMoveLeft(self):
        self.movecommands[0] = 1
    def addMoveRight(self):
        self.movecommands[1] = 1

import AI
import UI
import Bifrost

'''
# The GameMode essentially represents the game itself.
# It stores "global" variables and controls the game loop of all other game objects.
'''
class GameMode:
    def __init__(self, mode: str = 'top-down') -> None:
        self.mode: str = mode
        self.screen: pygame.Surface = None
        self.navmesh: AI.NavMesh = None
        self.playerController: PlayerController = None
        self.playerPawn: Pawn = None
        self.actors: list[Actor] = None
        self.HUD: UI.HUD = None
        # clock is used to set a max fps
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.backgroundbg: pygame.Surface | tuple[int, int, int] = None
        self.map_size: tuple[int, int] = None
        if Game_EnableOperationalMultithreading: self.thread = None

    def pre_start(self):
        self.playerController = Game_PlayerControllerClass()
        self.playerPawn = Game_PlayerPawnClass(location=Game_PlayerStart_Loc, controller=self.playerController)
        self.actors = [self.playerPawn]

        self.backgroundbg = Game_Background
        if isinstance(self.backgroundbg, pygame.Surface): self.map_size = self.backgroundbg.get_size()
        else: self.map_size = (1920, 1080)
        
        if Game_EnableOperationalMultithreading: self.thread = threading.Thread(target=self._start_loop, args=[])

    def start(self, screen_size: tuple[int, int] | str):
        pygame.init()

        # create a window
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN) if type(screen_size) == str else pygame.display.set_mode(screen_size)
        pygame.display.set_caption(Game_Caption)
        pygame.display.set_icon(pygame.image.load(Game_IconPath))

        self.HUD = Game_HUDClass(canvasOver = UI.CanvasPanel(), canvasUnder = UI.CanvasPanel(), screen=self.screen)
        if Game_EnableOperationalMultithreading: self.thread.start()
        else:
            self._start_loop()
    
    def _start_loop(self):
        # clock is used to set a max fps
        self.clock: pygame.time.Clock = pygame.time.Clock()
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            self.update()
        
        # Quit from the network, if applicable
        try: Bifrost.quit()
        except Exception: pass

        pygame.quit()

    def update(self):
        # render the background
        if isinstance(self.backgroundbg, pygame.Surface):
            self.drawBackgroundImg()
            
        else: self.screen.fill(self.backgroundbg)

        dTime = self.clock.get_time()/1000
        
        # If applicable, draw debug for the NavMesh
        if self.navmesh and self.navmesh.drawDebug and self.playerController.activeCamera:
            for laty in range(len(self.navmesh.matrix)):
                for latx in range(len(self.navmesh.matrix[laty])):
                    latticerect = pygame.Rect(latx*self.navmesh.resolution - self.playerController.activeCamera.projection[0], laty*self.navmesh.resolution - self.playerController.activeCamera.projection[1], self.navmesh.resolution, self.navmesh.resolution)
                    latticecol = (128, 255, 0) if self.navmesh.matrix[laty][latx] else (255, 128, 0)
                    bordercol = (0 if latticecol[0] == 128 else 255, 0 if latticecol[1] == 128 else 255, latticecol[2])
                    self.HUD.add_rect_bordered_under(latticerect, latticecol, bordercol, 1)

        # Draw the HUD elements that go below everything else
        self.HUD.draw_under()

        self.playerController.update(dTime)
        for actor in self.actors:
            actor.update(dTime)
        
        if self.navmesh:
            for res in self.navmesh.gridLODs:
                self.navmesh.Build(res)

        # Draw the HUD that go on top of everything else
        self.HUD.draw_over()
        # flip() updates the screen to make our changes visible
        pygame.display.flip()
     
        # how many updates per second
        self.clock.tick(30)

    def drawBackgroundImg(self):
        for obj in gc.get_objects():
                if isinstance(obj, ActorRenderComponent):
                    r = obj
                    break
        try:
            bgimg_rect = self.backgroundbg.get_rect(center = self.backgroundbg.get_rect(topleft = (r.renderOffset[0] - r.desiredOffset[0], r.renderOffset[1] - r.desiredOffset[0])).center)
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.backgroundbg, bgimg_rect)
        except NameError:
            pass

Game_PlayerControllerClass: typing.Type = PlayerController
Game_PlayerPawnClass: typing.Type = Character
Game_HUDClass: typing.Type = UI.HUD
Game_IconPath: str = 'C:/Users/ghmrg/Documents/Image Files/Resource/VikingHelmet.png'
Game_PlayerStart_Loc: tuple[int, int, int] = (400, 300, 0)
Game_Background: pygame.Surface | tuple[int, int, int] = (245, 250, 255)
Game_Caption: str = 'New Saga'
Game_EnableOperationalMultithreading: bool = False