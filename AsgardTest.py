import pygame as pyg
import AsgardEngine as re
import Heimdall as eye3d

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SNOW = (245, 250, 255)
RED = (255, 0, 0)
 
# initialize pyg
pyg.init()
preview = False
screen_size = (800, 600)

# create a window
screen = pyg.display.set_mode((0, 0), pyg.FULLSCREEN) if preview else pyg.display.set_mode(screen_size)

game = re.GameMode(screen=screen, pygInstance=pyg, mode='top-down')
eye3d.init(pygInstance=pyg)

pyg.display.set_caption(game.gameName)
pyg.display.set_icon(game.gameIcon)

# create a demo surface, and draw a red line diagonally across it

running = True
while running:
    for event in pyg.event.get():
        if event.type == pyg.QUIT:
            running = False
        elif event.type == pyg.KEYDOWN:
            if event.key == pyg.K_ESCAPE:
                running = False

    game.update()

pyg.quit()
