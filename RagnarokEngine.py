import pygame
import gc
from collections.abc import Callable

from TupleMath import *
from Mouse import *

#Actor

DEFAULTANIM = [pygame.transform.scale(pygame.image.load("C:/Users/ghmrg/Documents/Image Files/VikingSprite.png"), (50, 50)),
               pygame.transform.scale(pygame.image.load("C:/Users/ghmrg/Documents/Image Files/Viking/VikingSprite1.png"), (50, 50)),
               pygame.transform.scale(pygame.image.load("C:/Users/ghmrg/Documents/Image Files/Viking/VikingSprite2.png"), (50, 50)),
               pygame.transform.scale(pygame.image.load("C:/Users/ghmrg/Documents/Image Files/Viking/VikingSprite1.png"), (50, 50)),
               pygame.transform.scale(pygame.image.load("C:/Users/ghmrg/Documents/Image Files/VikingSprite.png"), (50, 50)),]

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
            self.physicsComp = PhysicsComponent(self)
            self.components.append(self.physicsComp)
    
    def update(self, dSecs, pyg):
        self.location = (self.location[0] + self.velocity[0], self.location[1] + self.velocity[1], self.location[2] + self.velocity[2])
        for component in self.components: component.update(dSecs)

'''
# The GameMode essentially represents the game itself.
# It stores "global" variables and controls the game loop of all other game objects.
'''
class GameMode(object):
    def __init__(self, screen, pygInstance, mode = 'top-down') -> None:
        self.mode = mode
        self.pyg = pygInstance
        self.screen = screen
        self.gameName = "New Saga"
        self.gameIcon = self.pyg.image.load('C:/Users/ghmrg/Documents/Image Files/Resource/VikingHelmet.png')
        self.playerController = PlayerController()
        self.playerCharacter = Character(location=(400, 300, 0), controller=self.playerController)
        self.actors = [self.playerCharacter]
        # clock is used to set a max fps
        self.clock = self.pyg.time.Clock()
        self.backgroundclr = (245, 250, 255)

    def update(self):
        # clear the screen
        self.screen.fill(self.backgroundclr)
        dTime = self.clock.get_time()/1000
        self.playerController.update(dTime, self.pyg)
        for actor in self.actors:
            actor.update(dTime, self.pyg)
        # flip() updates the screen to make our changes visible
        self.pyg.display.flip()
     
        # how many updates per second
        self.clock.tick(30)

# A Controller __?
class Controller(object):
    def update(self, dSecs, pyg):
        pass

# A PlayerController possesses a player character and does __?
class PlayerController(Controller):
    pass
'''
A Component is an object that is attached to an Actor and adds functionality to it.
Its parent is the object it is attached to.
'''
class Component(object):
    def __init__(self, parent: Actor) -> None:
        super().__init__()

        self.parent = parent
    
    def update(self, dSecs):
        pass

# A SceneComponent is a Component that has a transform in the world
class SceneComponent(Component):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.offset = (0, 0, 0)

# A PhysicsComponent handles the physics attributes, such as collisions and gravity, of its parent
class PhysicsComponent(Component):
    pass

# An InputComponent maps inputs (such as key presses and mouse movement) to methods of its parent.
class InputComponent(Component):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.events: dict[int, Callable[[None], None]] = {}
        self.mouseevents: dict[int, Callable[[None], None]] = {}
    
    def update(self, dSecs):
        super().update(dSecs)
        if self.events:
            pressed = self.parent.gameMode.pyg.key.get_pressed()
            for inp in self.events.keys():
                if pressed[inp]: self.events[inp]()
        if self.mouseevents:
            # UNTESTED
            pressed = self.parent.gameMode.pyg.mouse.get_pressed()
            mousekeys = self.mouseevents.keys()
            for i in (0, 1, 2):
                if i in mousekeys and pressed[i]: self.mouseevents[i]()
    
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


# A CharacterMovementComponent is attached to a Character and handles its movement in the game world
class CharacterMovementComponent(Component):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.groundSpeed = 5
        self.maxGroundSpeed = self.groundSpeed
        self.speed = self.groundSpeed
        self.jumpForce = 7.5
        self.terminalVelocity = 10
        if self.parent.gameMode.mode == 'side':
            self.physComp = PhysicsComponent(self.parent)
        self.idleImage = [DEFAULTANIM[0]]
        self.runImage = DEFAULTANIM

    def movementInput(self, direction, magnitude = 1):
        if direction[0] != 0 or direction[1] != 0:
            self.parent.rotation = (self.parent.rotation[0], self.parent.rotation[1], -90.0 - math.degrees(math.atan2(direction[1], direction[0])))
                                                                                    # get the sign of velocity[0] and negate it
        if direction[0] == 0 and self.parent.velocity[0] != 0: direction = (-abs(self.parent.velocity[0])/self.parent.velocity[0], direction[1], direction[2])
        if self.parent.gameMode.mode == 'top-down':                                 # get the sign of velocity[1] and negate it
            if direction[1] == 0 and self.parent.velocity[1] != 0: direction = (direction[0], -abs(self.parent.velocity[1])/self.parent.velocity[1], direction[2])
            self.parent.velocity = normalizeTuple(clampTuple(addTuple(self.parent.velocity, scaleTuple(direction, magnitude*self.speed)), ((-self.speed, self.speed), (-self.speed, self.speed), (-self.speed, self.speed))))
        elif self.parent.gameMode.mode == 'side':
            scaledtup = scaleTuple(direction, magnitude*self.speed)
            self.parent.velocity = clampTuple(addTuple(self.parent.velocity, (scaledtup[0], direction[1] * magnitude * self.jumpForce, scaledtup[2])), ((-self.speed, self.speed), (-self.terminalVelocity, self.jumpForce), (-self.speed, self.speed)))
        self.parent.velocity = roundToward(self.parent.velocity, tolerance=2.5)
        if direction[0] == 0 and direction[1] == 0:
            if self.parent.renderComp.image == self.runImage: self.parent.renderComp.image = self.idleImage
            self.parent.renderComp.currentImage = self.idleImage[0]
        else:
            if self.parent.renderComp.image == self.idleImage: self.parent.renderComp.currentImage = self.runImage[0]
            self.parent.renderComp.image = self.runImage

# A RenderComponent causes an actor to be drawn to the screen at its location
# It can also render animations from a flibook list
class ActorRenderComponent(SceneComponent):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.image = DEFAULTANIM
        self.currentImage = self.image[0]
        self.offset = (-25, -25, 0)
    
    def update(self, dSecs):
        super().update(dSecs)
        self.draw()
        self.currentImage = self.image[(self.image.index(self.currentImage) + 1) % len(self.image)]
    
    def draw(self):
        rotated_image = pygame.transform.rotate(self.currentImage, self.parent.rotation[2])
        img_rect = rotated_image.get_rect(center = self.currentImage.get_rect(topleft = (self.parent.location[0] + self.offset[0], self.parent.location[1] + self.offset[1])).center)
        self.parent.gameMode.screen.blit(rotated_image, img_rect)

'''
A Pawn is an Actor that can be "possessed" by and receive input from a controller.
Pawns are renderable and have physics enabled by default.
'''
class Pawn(Actor):
    def __init__(self, location = (0, 0, 0), rotation = (0, 0, 0), controller = PlayerController()) -> None:
        super().__init__(location, rotation, renderable=True, physical=True)

        self.controller = controller

# A Character is a Pawn with built-in input-based movement
class Character(Pawn):
    def __init__(self, location = (0, 0, 0), rotation = (0, 0, 0), controller = PlayerController()) -> None:
        super().__init__(location, rotation, controller=controller)

        self.moveComp = CharacterMovementComponent(self)
        self.inpComp = InputComponent(self)
        self.components.extend((self.moveComp, self.inpComp))

        self.inpComp.BindAlts([pygame.K_UP, pygame.K_w], self.addMoveUp)
        self.inpComp.BindAlts([pygame.K_LEFT, pygame.K_a], self.addMoveLeft)
        self.inpComp.BindAlts([pygame.K_RIGHT, pygame.K_d], self.addMoveRight)
        self.inpComp.BindAlts([pygame.K_DOWN, pygame.K_s], self.addMoveDown)

        self.movecommands = [0, 0, 0, 0]
    
    def update(self, dSecs, pyg):
        self.clearMoveCommands()

        super().update(dSecs, pyg)
        self.moveComp.movementInput((self.movecommands[1] - self.movecommands[0], self.movecommands[3] - self.movecommands[2], 0))

    def clearMoveCommands(self):
        self.movecommands = [0] * 4
    def addMoveUp(self):
        self.movecommands[2] = 1
    def addMoveDown(self):
        self.movecommands[3] = 1
    def addMoveLeft(self):
        self.movecommands[0] = 1
    def addMoveRight(self):
        self.movecommands[1] = 1