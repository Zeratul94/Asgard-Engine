# Copyright © Gedalya Gordon 2023, all rights reserved. #

import pygame
import pathfinding.core.grid as pgrid
import pathfinding.finder.a_star as astar
import pathfinding.core.diagonal_movement as dmove

import AsgardEngine as ae
from Mjolnir import  CollisionComponent, CircleCollisionComponent, BoxCollisionComponent
from AsgardEngine import Controller, Character
from TupleMath import *

class NavMesh():
    def __init__(self, game, resolution: float = 12.5) -> None:
        self.gameMode = game
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

    # Must be called by the developer
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
        if len(pathpts) > 1: pathpts.pop(0)
        return pathpts

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
            for i in range(len(pathpts)):
                if distance(self.controlledPawn.location, pathpts[i]) <= self.navmesh.resolution and i+1 < len(pathpts):
                    self.moveDirectlyToward(pathpts[i+1], tolerance)
                    choseNextDestination = True
                    break
            if not choseNextDestination:
                self.moveDirectlyToward(pathpts[0], tolerance)
        
    def moveDirectlyToward(self, target: tuple[int, int, int], tolerance: int):
        assert isinstance(self.controlledPawn, Character), "AIController 'moveDirectlyToward' cannot affect a non-Character Pawn."
        assert self.controlledPawn.location, "AIController 'moveTo' requires the controller to have a defined controlledPawn."
        if distance(self.controlledPawn.location, target) >= tolerance:
                dir = normalize((target[0] - self.controlledPawn.location[0], target[1] - self.controlledPawn.location[1], target[2] - self.controlledPawn.location[2]))
                self.controlledPawn.moveComp.movementInput(dir)