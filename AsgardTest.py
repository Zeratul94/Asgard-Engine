# Copyright © Gedalya Gordon 2023, all rights reserved. #

import pygame
import AsgardEngine as ae
import Hlidskjalf as eye3d
from UI import HUDElement

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SNOW = (245, 250, 255)
RED = (255, 0, 0)

bt: ae.UI.Button = None

def buttonhovered():
    bt.border.brush = (0, 255, 0)
    print("hi")
def buttonUNhovered():
    bt.border.brush = (0, 0, 255)

class myHUD(ae.UI.HUD):
    def __init__(self, canvasOver: HUDElement, canvasUnder: HUDElement, screen: pygame.Surface) -> None:
        super().__init__(canvasOver, canvasUnder, screen)
        global bt
        bt = self.canvasOver.addChild(ae.UI.Button(ae.UI.Border((128, 0, 255)),
                                                {ae.UI.ButtonEvent.Hovered : buttonhovered, ae.UI.ButtonEvent.Unhovered : buttonUNhovered},
                                              pygame.Rect(100, 200, 75, 70)))

ae.Game_HUDClass = myHUD

game = ae.GameMode('top-down')

game.pre_start()
game.start((800, 600))