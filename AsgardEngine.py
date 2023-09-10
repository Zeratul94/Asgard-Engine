from __future__ import annotations

import pygame
import pathfinding.core.grid as pgrid
import pathfinding.finder.a_star as astar
import pathfinding.core.diagonal_movement as dmove
import gc
from collections.abc import Callable
import typing

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
    
    def update(self, dSecs):
        self.location = (self.location[0] + self.velocity[0], self.location[1] + self.velocity[1], self.location[2] + self.velocity[2])
        self.velocity = (0, 0, 0)
        for component in self.components: component.update(dSecs)

'''
# The GameMode essentially represents the game itself.
# It stores "global" variables and controls the game loop of all other game objects.
'''
class GameMode():
    def __init__(self, screen: pygame.Surface, pygInstance, mode: str = 'top-down') -> None:
        self.mode: str = mode
        self.pyg = pygInstance
        self.screen: pygame.Surface = screen
        self.gameName: str = Game_Caption
        self.gameIcon: pygame.Surface = self.pyg.image.load(Game_IconPath)
        self.navmesh: NavMesh = None
        self.playerController: PlayerController = Game_PlayerControllerClass()
        self.playerPawn: Pawn = Game_PlayerPawnClass(location=Game_PlayerStart_Loc, controller=self.playerController)
        self.actors: list[Actor] = [self.playerPawn]
        self.HUD: HUD = Game_HUDClass(pygInstance=self.pyg, screen=self.screen)
        # clock is used to set a max fps
        self.clock: pygame.time.Clock = self.pyg.time.Clock()
        self.backgroundbg: pygame.Surface | tuple[int, int, int] = Game_Background
        self.map_size: tuple[int, int] = (1920, 1080)
        if isinstance(self.backgroundbg, pygame.Surface): self.map_size = self.backgroundbg.get_size()


    def pre_start(self):
        if self.navmesh:
            self.navmesh.Build(self.navmesh.resolution)

    def start(self):
        running = True
        while running:
            for event in self.pyg.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            self.update()
            

        self.pyg.quit()

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
        self.pyg.display.flip()
     
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

class NavMesh():
    def __init__(self, gameMode: GameMode, resolution: float = 12.5) -> None:
        self.gameMode = gameMode
        self.finder: astar.AStarFinder = astar.AStarFinder(diagonal_movement=dmove.DiagonalMovement.always)
        self.gridLODs: dict[float, pgrid.Grid] = {}
        self.grid: pgrid.Grid = None

        self.resolution: float = resolution
        self.matrixLODs: dict[float, list[list[int]]] = {resolution : [[1 for j in range(self.gameMode.map_size[0]//self.resolution)] for i in range(self.gameMode.map_size[1]//self.resolution)]}
        self.matrix = self.matrixLODs[resolution]

        self.drawDebug = False

    # Adds and builds a new resolution for the navmesh
    # DO NOT USE FOR PRE-GAME INITIALIZATION. Instead
    # pass the desired resolution as a construction
    # parameter.
    def addLOD(self, newResolution: float):
        self.matrixLODs[newResolution] = [[1 for j in range(self.gameMode.map_size[0]//self.resolution)] for i in range(self.gameMode.map_size[1]//self.resolution)]
        self.Build(newResolution)
    
    def setLOD(self, newLODRes: float) -> bool:
        assert newLODRes in self.matrixLODs, "NavMesh has not been initialized for the desired LOD.\nMake sure to call navmesh.addLOD(blocker_size) sometime before."
        assert newLODRes in self.gridLODs, "NavMesh has not been built for the desired LOD.\nMake sure to call navmesh.addLOD(blocker_size) sometime before."

        self.matrix = self.matrixLODs[newLODRes]
        self.grid = self.gridLODs[newLODRes]

    def Build(self, buildResolution: float):
        tilesX, tilesY = self.gameMode.map_size[0]//buildResolution, self.gameMode.map_size[1]//buildResolution

        self.matrixLODs[buildResolution] = [[1 for j in range(tilesX)] for i in range(tilesY)]

        for actor in self.gameMode.actors:
            for comp in actor.components:
                if isinstance(comp, CollisionComponent) and comp.blocksNavigation:
                    for keyLoc in self.calculateAIBlocking(comp):
                        self.matrixLODs[buildResolution][keyLoc[1]][keyLoc[0]] = 0

        self.gridLODs[buildResolution] = pgrid.Grid(matrix=self.matrixLODs[buildResolution])
    
    def updateBlocker(self, blocker: CollisionComponent, currentResolutionOnly = False):
        assert blocker.blocksNavigation, "NavMesh attempted recalculate but collider is not set to block navigation."
        
        # Update the matrix with the blocker's blocking.
        if currentResolutionOnly:
            hasbeenmodified = False
            for keyLoc in self.calculateAIBlocking(blocker):
                self.matrixLODs[self.resolution][keyLoc[1]][keyLoc[0]] = 0
                if not hasbeenmodified: hasbeenmodified = True
            
            # If the tests resulted in any modification to the matrix, regenerate the navgrid.
            if hasbeenmodified:
                self.gridLODs[self.resolution] = pgrid.Grid(matrix=self.matrixLODs[self.resolution])
        else:
            # Store the actual current value of self.resolution so we can change it back later.
            meshres = self.resolution
            for res in self.matrixLODs:
                # Modify self.resolution so that calculateAIBlocking works properly.
                self.resolution = res

                hasbeenmodified = False
                for keyLoc in self.calculateAIBlocking(blocker):
                    self.matrixLODs[self.resolution][keyLoc[1]][keyLoc[0]] = 0
                    if not hasbeenmodified: hasbeenmodified = True
            
            # If the tests resulted in any modification to the matrix, regenerate the navgrid.
            if hasbeenmodified:
                self.gridLODs[self.resolution] = pgrid.Grid(matrix=self.matrixLODs[self.resolution])

            # Change it back.
            self.resolution = meshres

    def calculateAIBlocking(self, collider: CollisionComponent) -> list[tuple[int, int]]:
        
        blockedCells: list[tuple[int, int]] = []

        (test_width, test_height) = (0, 0)
        if isinstance(collider, CircleCollisionComponent):
            test_width = test_height = collider.radius*2
        elif isinstance(collider, BoxCollisionComponent):
            (test_width, test_height) = collider.rect.size
        
        testCells: dict[tuple[int, int], pygame.Rect] = {}
        
        for x in range(int(collider.worldLoc[0] - test_width//2), int(collider.worldLoc[0] + test_width//2 + 1), int(self.resolution)):
            for y in range(int(collider.worldLoc[1] - test_height//2), int(collider.worldLoc[1] + test_height//2 + 1), int(self.resolution)):
                if x < self.gameMode.map_size[0] and y < self.gameMode.map_size[1]:
                    cellx, celly = int(x/self.resolution), int(y/self.resolution)
                    
                    if (cellx, celly) not in testCells:
                        testCells[(cellx, celly)] = pygame.Rect(cellx*self.resolution, celly*self.resolution, self.resolution, self.resolution)
        
        for key in testCells.keys():
            if collider.collideCollider(testCells[key]):
                blockedCells.append(key)
        
        return blockedCells
    
    def Pathfind(self, start: tuple[int, int, int], end: tuple[int, int, int]) -> list[tuple[int, int, int]]:
        pathpts = []

        start_gridLoc = (int(start[0]/self.resolution), int(start[1]/self.resolution))
        end_gridLoc = (int(end[0]/self.resolution), int(end[1]/self.resolution))
        
        startnode = self.grid.node(start_gridLoc[0], start_gridLoc[1])
        endnode = self.grid.node(end_gridLoc[0], end_gridLoc[1])
        path, itrs = self.finder.find_path(startnode, endnode, self.grid)
        self.grid.cleanup()

        for gridpt in path:
            pathpts.append((self.resolution*(gridpt.x + 0.5), self.resolution*(gridpt.y + 0.5), start[2]))

        pathpts.append(end)
        return pathpts

class HUD():
    def __init__(self, pygInstance, screen: pygame.Surface) -> None:
        self.pyg = pygInstance
        self.screen: pygame.Surface = screen
        self.rectsToDrawOver: list[tuple[pygame.Rect, tuple[int, int, int] | tuple[int, int, int, int], tuple[int, int, int], int]] = []
        self.rectsToDrawUnder: list[tuple[pygame.Rect, tuple[int, int, int] | tuple[int, int, int, int], tuple[int, int, int], int]] = []
    
    def draw_under(self):
        for rectInfo in self.rectsToDrawUnder:
            if len(rectInfo[1]) == 4:
                rectSurf = self.pyg.Surface((rectInfo[0].width, rectInfo[0].height))
                rectSurf.set_alpha(rectInfo[1][3])
                rectSurf.fill((rectInfo[1][0], rectInfo[1][1], rectInfo[1][2]))
                self.screen.blit(rectSurf, (rectInfo[0].x, rectInfo[0].y))
            else:
                self.screen.fill(rectInfo[1], rectInfo[0])
            self.pyg.draw.rect(self.screen, rectInfo[2], rectInfo[0], width= rectInfo[3])
        
        self.rectsToDrawUnder.clear()


    def draw_over(self):
        for rectInfo in self.rectsToDrawOver:
            if len(rectInfo[1]) == 4:
                rectSurf = self.pyg.Surface((rectInfo[0].width, rectInfo[0].height))
                rectSurf.set_alpha(rectInfo[1][3])
                rectSurf.fill((rectInfo[1][0], rectInfo[1][1], rectInfo[1][2]))
                self.screen.blit(rectSurf, (rectInfo[0].x, rectInfo[0].y))
            else:
                self.screen.fill(rectInfo[1], rectInfo[0])
            self.pyg.draw.rect(self.screen, rectInfo[2], rectInfo[0], width= rectInfo[3])
        
        self.rectsToDrawOver.clear()


    def add_rect_bordered_over(self, rect: pygame.Rect, rectColor: tuple[int, int, int] | tuple[int, int, int, int], borderColor: tuple[int, int, int], borderWidth: int):
        self.rectsToDrawOver.append((rect, rectColor, borderColor, borderWidth))
    def add_rect_bordered_under(self, rect: pygame.Rect, rectColor: tuple[int, int, int] | tuple[int, int, int, int], borderColor: tuple[int, int, int], borderWidth: int):
        self.rectsToDrawUnder.append((rect, rectColor, borderColor, borderWidth))

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

class AIController(Controller):
    def __init__(self, navmesh: NavMesh = None) -> None:
        super().__init__()

        self.navmesh = navmesh

    def moveToLocation(self, destination: tuple[int, int, int], tolerance: int):
        assert isinstance(self.controlledPawn, Character), "AIController 'moveToLocation' cannot affect a non-Character Pawn."
        assert self.controlledPawn.location, "AIController 'moveTo' requires the controller to have a defined controlledPawn."
        assert 50. in self.navmesh.gridLODs, "NavMesh has not been built for the blocker's size.\nMake sure to call navmesh.addLOD(blocker_size) sometime before." # pawn.width #FN#
        self.navmesh.setLOD(50.) # pawn.width #FN#
        pathpts = self.navmesh.Pathfind(self.controlledPawn.location, destination)
        choseNextDestination: bool = False
        if pathpts:
            print(str(self.controlledPawn) + "'s", "path to follow will be:\n" + str(pathpts))
            for i in range(len(pathpts)):
                if distance(self.controlledPawn.location, pathpts[i]) <= self.navmesh.resolution and i+1 < len(pathpts):
                    self.moveDirectlyToward(pathpts[i+1], tolerance)
                    print("next destination:", pathpts[i+1])
                    choseNextDestination = True
                    break
            if not choseNextDestination:
                self.moveDirectlyToward(pathpts[0], tolerance)
                print("next destination:", pathpts[0])
        
    def moveDirectlyToward(self, target: tuple[int, int, int], tolerance: int):
        assert isinstance(self.controlledPawn, Character), "AIController 'moveDirectlyToward' cannot affect a non-Character Pawn."
        assert self.controlledPawn.location, "AIController 'moveTo' requires the controller to have a defined controlledPawn."
        if distance(self.controlledPawn.location, target) >= tolerance:
                dir = normalize((target[0] - self.controlledPawn.location[0], target[1] - self.controlledPawn.location[1], target[2] - self.controlledPawn.location[2]))
                self.controlledPawn.moveComp.movementInput(dir)

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

# An InputComponent maps inputs (such as key presses and mouse movement) to methods of its parent.
class InputComponent(Component):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.events: dict[int, Callable[[None], None]] = {}
        self.mouseevents: dict[int, Callable[[any], None]] = {}
    
    def update(self, dSecs):
        super().update(dSecs)
        if self.events:
            pressed = self.parent.gameMode.pyg.key.get_pressed()
            for inp in self.events.keys():
                if pressed[inp]: self.events[inp]()
        if self.mouseevents:
            pressed = self.parent.gameMode.pyg.mouse.get_pressed()
            mousekeys = self.mouseevents.keys()
            for i in (0, 1, 2):
                if i in mousekeys and pressed[i]: self.mouseevents[i]()
            
            mousepos = self.parent.gameMode.pyg.mouse.get_pos()
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
            self.physComp = PhysicsComponent(self.parent)
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

'''
A Pawn is an Actor that can be "possessed" by a controller.
Pawns are renderable and have physics enabled by default.
'''
class Pawn(Actor):
    def __init__(self, location = (0, 0, 0), rotation = (0, 0, 0), controller = None) -> None:
        super().__init__(location, rotation, renderable=True, physical=True)

        self.controller = controller if controller else AIController(self.gameMode.navmesh)
        self.controller.controlledPawn = self

# A Character is a Pawn with built-in input-based movement
class Character(Pawn):
    def __init__(self, location = (0, 0, 0), rotation = (0, 0, 0), controller = None) -> None:
        super().__init__(location, rotation, controller=controller)

        self.components = [component for component in self.components if type(component) != CollisionComponent]
        self.capsuleComp = CircleCollisionComponent(self)
        self.components.append(self.capsuleComp)
        self.physicsComp.collider = self.capsuleComp

        self.moveComp = CharacterMovementComponent(self)
        self.inpComp = InputComponent(self)
        self.components.extend((self.moveComp, self.inpComp))

        self.movecommands = [0, 0, 0, 0]
    
    def update(self, dSecs):
        self.clearMoveCommands()

        super().update(dSecs)
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

Game_PlayerControllerClass: typing.Type = PlayerController
Game_PlayerPawnClass: typing.Type = Character
Game_HUDClass: typing.Type = HUD
Game_IconPath: str = 'C:/Users/ghmrg/Documents/Image Files/Resource/VikingHelmet.png'
Game_PlayerStart_Loc: tuple[int, int, int] = (400, 300, 0)
Game_Background: pygame.Surface | tuple[int, int, int] = (245, 250, 255)
Game_Caption: str = 'New Saga'