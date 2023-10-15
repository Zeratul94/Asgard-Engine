# Copyright © Gedalya Gordon 2023, all rights reserved. #

import pygame
from enum import Enum

class Justification(Enum):
    Left = 0
    Center = 1
    Right = 2

class Font:
    def __init__(self, fontPath: str, size: int, color: tuple[int, int, int]) -> None:
                                                        #maybe need to fix path?
        self.pygFont: pygame.font.Font = pygame.font.Font(fontPath, size)
        self.color: tuple[int, int, int] = color