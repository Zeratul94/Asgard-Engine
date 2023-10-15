# Copyright © Gedalya Gordon 2023, all rights reserved. #

import pygame
import AsgardEngine as ae
import Hlidskjalf as eye3d
from UI import HUDElement

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SNOW = (245, 250, 255)
RED = (255, 0, 0)

joinbt: ae.UI.Button = None
hostbt: ae.UI.Button = None

targetip = ''

def buttonhovered(bt):
    bt.border.brush = (15, 40, 255)
def buttonUNhovered(bt):
    bt.border.brush = (0, 0, 200)
def buttonpressed(bt):
    bt.border.brush = (0, 200, 30)

def joinbuttonreleased(bt):
    bt.border.brush = (15, 40, 255)
    ae.Bifrost.init_client(targetip)
    ae.Bifrost.add_receive_target(game.playerController.receiveresponse)

def hostbuttonreleased(bt):
    bt.border.brush = (15, 40, 255)
    game.HUD.createHostingPopup()

def interruptButtonPressed(bt):
    buttonpressed(bt)
    game.playerController.interruptedTransmission = True
def interruptButtonReleased(bt):
    bt.border.brush = (15, 40, 255)
    game.playerController.interruptedTransmission = False

class myHUD(ae.UI.HUD):
    def __init__(self, canvasOver: HUDElement, canvasUnder: HUDElement, screen: pygame.Surface) -> None:
        super().__init__(canvasOver, canvasUnder, screen)
        coolFont = ae.UI.Runes.Font("C:/Users/ghmrg/Documents/Fonts/NEON CLUB MUSIC/NEON CLUB MUSIC.otf", 30, (255, 255, 255))
        global joinbt, hostbt
        self.canvasOver.addChild(ae.UI.Border((255, 0, 0), pygame.Rect(2, -50, 200, 200)))
        joinbt = self.canvasOver.addChild(ae.UI.Button(ae.UI.Border((0, 0, 200)),
                                                       {ae.UI.ButtonEvent.Released : joinbuttonreleased,
                                                        ae.UI.ButtonEvent.Hovered : buttonhovered,
                                                        ae.UI.ButtonEvent.Unhovered : buttonUNhovered,
                                                        ae.UI.ButtonEvent.Pressed : buttonpressed},
                                                       pygame.Rect(100, 150, 120, 48)))
        joinbt.addChild(ae.UI.Text(ae.UI.Runes.Justification.Left,
                                   coolFont,
                                   anchors=(joinbt.border.get_width()/2, (joinbt.border.get_height() + 4)/2),
                                   alignment=(0.5, 0.5)))
        joinbt.children[1].setText("Join")
        hostbt = self.canvasOver.addChild(ae.UI.Button(ae.UI.Border((0, 0, 200)), 
                                                       {ae.UI.ButtonEvent.Released : hostbuttonreleased,
                                                        ae.UI.ButtonEvent.Hovered : buttonhovered,
                                                        ae.UI.ButtonEvent.Unhovered : buttonUNhovered,
                                                        ae.UI.ButtonEvent.Pressed : buttonpressed},
                                                       pygame.Rect(100, 100, 120, 48)))
        hostbt.addChild(ae.UI.Text(ae.UI.Runes.Justification.Left, 
                                   coolFont, 
                                   anchors=(hostbt.border.get_width()/2, (hostbt.border.get_height() + 4)/2),
                                   alignment=(0.5, 0.5)))
        hostbt.children[1].setText("Host")
    
    def createHostingPopup(self):
        popupWidgets = []

        popupWidgets.append(self.canvasOver.addChild(ae.UI.Border((255, 255, 255), pygame.Rect(400, 300, 300, 200))))
        popupWidgets.append(popupWidgets[0].addChild(ae.UI.Border((0, 0, 200), pygame.Rect(0, 0, 298, 198), anchors=(popupWidgets[0].get_width()/2, popupWidgets[0].get_height()/2))))

        def submitnumber(bt: ae.UI.Button):
            bt.border.brush = (15, 40, 255)

            global targetip
            targetip = ae.Bifrost.init_server(int(bt.children[1].text))

            self.canvasOver.removeChildren(popupWidgets)

            self.canvasOver.addChild(ae.UI.Button(ae.UI.Border((0, 0, 200)),
                                                  {ae.UI.ButtonEvent.Hovered : buttonhovered,
                                                   ae.UI.ButtonEvent.Unhovered : buttonUNhovered,
                                                   ae.UI.ButtonEvent.Pressed : interruptButtonPressed,
                                                   ae.UI.ButtonEvent.Released : interruptButtonReleased},
                                                   pygame.Rect(600, 200, 100, 100)))
        
        for i in range(10):
            popupWidgets.append(self.canvasOver.addChild(ae.UI.Border((255, 255, 255), pygame.Rect(269 + i*27, 349, 27, 27), alignment=(0, 0))))
            popupWidgets.append(self.canvasOver.addChild(ae.UI.Button(ae.UI.Border((0, 0, 200)),
                                                                    {ae.UI.ButtonEvent.Hovered : buttonhovered,
                                                                        ae.UI.ButtonEvent.Unhovered : buttonUNhovered,
                                                                        ae.UI.ButtonEvent.Pressed : buttonpressed,
                                                                        ae.UI.ButtonEvent.Released : submitnumber},
                                                                    pygame.Rect(270 + i*27, 350, 25, 25))))
            popupWidgets[(i*2)+3].addChild(ae.UI.Text(ae.UI.Runes.Justification.Left,
                                            ae.UI.Runes.Font("C:/Users/ghmrg/Documents/Fonts/NEON CLUB MUSIC/NEON CLUB MUSIC.otf", 20, (255, 255, 255))))
            popupWidgets[(i*2)+3].children[1].setText(str(i+1))

class bifrostTest_Controller(ae.PlayerController):
    def __init__(self) -> None:
        super().__init__()
        self.msgText: ae.UI.Text = None
        self.everyFew: int = 0
        self.interruptedTransmission = False

    def update(self, dSecs):
        if self.everyFew == 10:
            if self.msgText:
                self.msgText.setText("Received:")
            self.everyFew = 0
        else:
            self.everyFew+=1
        super().update(dSecs)
        if not self.interruptedTransmission:
            try: ae.Bifrost.send("rcast hi!")
            except Exception: pass
        else:
            try: ae.Bifrost.send("rcast move right")
            except Exception: pass

    def receiveresponse(self, msg: str):
        if msg.split(' ')[0] == 'move':
            self.controlledPawn.addMoveRight()
        if not self.msgText:
            self.msgText = self.gameMode.HUD.canvasOver.addChild(ae.UI.Text(ae.UI.Runes.Justification.Left,
                                                                            ae.UI.Runes.Font("C:/Users/ghmrg/Documents/Fonts/Chakra Petch/ChakraPetch-Regular.ttf", 30, (0, 255, 0)),
                                                                            offset=(400, 400)))
        self.msgText.setText("Received: " + msg)

ae.Game_HUDClass = myHUD
ae.Game_PlayerControllerClass = bifrostTest_Controller
ae.Game_PlayerPawnClass = ae.Character
ae.Game_Caption = "Test"
ae.Game_Background = (0, 0, 0)

game = ae.GameMode('top-down')

game.pre_start()
game.start((800, 600))