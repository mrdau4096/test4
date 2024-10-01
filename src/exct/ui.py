"""
[ui.py]
Creates the UI, based off of "prompts" such as player stats and current item.
Makes use of pygame blit functions
______________________
Importing other files;
-texture_load.py
-log.py
"""
#Importing Internal modules
from imgs import texture_load
from exct import log, utils, render
from exct.utils import *

#Importing External Modules
import sys, os
import math as maths
sys.path.append("modules.zip")
import pygame as PG
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

print("Imported Sub-file // ui.py")

PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS
UI_SURFACE = PG.Surface(CONSTANTS["UI_RESOLUTION"].TO_LIST(), PG.SRCALPHA)


#General UI related functions


def DRAW_TEXT(SCREEN, TEXT, POSITION, FONT_SIZE, COLOUR=(255, 255, 255)):
	FONT = PG.font.Font('src\\exct\\fonts\\PressStart2P-Regular.ttf', FONT_SIZE)
	text_surface = FONT.render(str(TEXT), True, COLOUR)
	SCREEN.blit(text_surface, POSITION)

def DRAW_IMG(SCREEN, IMG_NAME, POSITION, SCALE):
	IMAGE = PG.image.load(f"src\\imgs\\{IMG_NAME}")
	SCALED_IMAGE = PG.transform.scale(IMAGE, SCALE)
	SCREEN.blit(SCALED_IMAGE, POSITION)


#Per-Frame HUD


def HUD(PLAYER, FPS):
	UI_COLOURS = {
		"SMOKY_BLACK": (20, 17, 15),
		"DAVYS_GRAY": (72, 71, 74),
		"SILVER": (186, 186, 186),
		"WHITE_SMOKE": (245, 245, 245),
		"MOSS_GREEN": (116, 142, 84),
		"GOLD_TIPS": (229, 172, 43),
	}

	#Create the surface to render the UI to.
	UI_SURFACE.fill([0, 0, 0, 0])

	#Create the "Crosshair".
	PG.draw.circle(UI_SURFACE, UI_COLOURS["SILVER"], (320, 180), 7, 2)

	#Create the lower-left info panel.
	DRAW_TEXT(UI_SURFACE, str(PLAYER.ENERGY).zfill(3), (105, 322), 16, COLOUR=UI_COLOURS["GOLD_TIPS"])
	DRAW_TEXT(UI_SURFACE, str(PLAYER.HEALTH).zfill(3), (105, 343), 16, COLOUR=UI_COLOURS["GOLD_TIPS"])
	DRAW_IMG(UI_SURFACE, "ENERGY.png", (5, 322), (94, 16))
	DRAW_IMG(UI_SURFACE, "HEALTH.png", (5, 343), (88, 16))

	#FPS counter.
	DRAW_TEXT(UI_SURFACE, f"FPS: {str(maths.floor(FPS)).zfill(2)}", (583, 2), 8, COLOUR=UI_COLOURS["GOLD_TIPS"])

	UI_SURFACE_ID = render.SURFACE_TO_TEXTURE(UI_SURFACE, CONSTANTS["UI_RESOLUTION"].TO_INT())

	return UI_SURFACE_ID
