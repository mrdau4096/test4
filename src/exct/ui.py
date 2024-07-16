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
from exct import log, utils
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

def HUD(PLAYER, FPS):
	UI_COLOURS = {"SMOKY_BLACK": (20, 17, 15), "DAVYS_GRAY": (72, 71, 74), "SILVER": (186, 186, 186), "WHITE_SMOKE": (245, 245, 245), "MOSS_GREEN": (116, 142, 84)}

	#Create the surface to render the UI to.
	UI_SURFACE = PG.Surface(CONSTANTS["UI_RESOLUTION"].TO_LIST(), PG.SRCALPHA)
	UI_SURFACE.fill([0, 0, 0, 0])

	#Create the "Crosshair".
	PG.draw.circle(UI_SURFACE, UI_COLOURS["SILVER"], (320, 180), 5, 1)

	#Create the lower-left info panel.
	PG.draw.rect(UI_SURFACE, UI_COLOURS["SILVER"], (0, 319, 95, 41))
	PG.draw.polygon(UI_SURFACE, UI_COLOURS["SILVER"], ((95, 322.5), (95, 362.5), (105, 362.5)))
	DRAW_TEXT(UI_SURFACE, str(PLAYER.AMMO[0]).zfill(2), (10.5, 345), 16, COLOUR=UI_COLOURS["SMOKY_BLACK"])
	DRAW_TEXT(UI_SURFACE, str(PLAYER.HEALTH).zfill(3), (54, 345), 16, COLOUR=UI_COLOURS["SMOKY_BLACK"])
	DRAW_IMG(UI_SURFACE, "ammo2.png", (20, 322), (10, 16))
	DRAW_IMG(UI_SURFACE, "health2.png", (67.5, 323), (16, 14))
	PG.draw.line(UI_SURFACE, UI_COLOURS["MOSS_GREEN"], (0, 319), (95, 319), 2)
	PG.draw.line(UI_SURFACE, UI_COLOURS["SMOKY_BLACK"], (0, 340), (100, 340), 2)
	PG.draw.line(UI_SURFACE, UI_COLOURS["SMOKY_BLACK"], (50, 320), (50, 360), 2)
	PG.draw.line(UI_SURFACE, UI_COLOURS["MOSS_GREEN"], (95, 320), (105, 360), 2)

	#FPS counter.
	PG.draw.rect(UI_SURFACE, UI_COLOURS["SILVER"], (580, 0, 120, 10))
	PG.draw.polygon(UI_SURFACE, UI_COLOURS["SILVER"], ((580, 10), (580, 0), (575, 0)))
	PG.draw.line(UI_SURFACE, UI_COLOURS["MOSS_GREEN"], (579, 10), (574, 0), 2)
	PG.draw.line(UI_SURFACE, UI_COLOURS["MOSS_GREEN"], (579, 10), (640, 10), 2)
	DRAW_TEXT(UI_SURFACE, f"FPS: {str(maths.floor(FPS)).zfill(2)}", (583, 2), 8, COLOUR=UI_COLOURS["SMOKY_BLACK"])

	UI_SURFACE_ID = SURFACE_TO_TEXTURE(UI_SURFACE)

	return UI_SURFACE_ID

def DRAW_TEXT(SCREEN, TEXT, POSITION, FONT_SIZE, COLOUR=(255, 255, 255)):
	FONT = PG.font.Font('src\\exct\\fonts\\PressStart2P-Regular.ttf', FONT_SIZE)
	text_surface = FONT.render(str(TEXT), True, COLOUR)
	SCREEN.blit(text_surface, POSITION)

def DRAW_IMG(SCREEN, IMG_NAME, POSITION, SCALE):
	IMAGE = PG.image.load(f"src\\imgs\\{IMG_NAME}")
	SCALED_IMAGE = PG.transform.scale(IMAGE, SCALE)
	SCREEN.blit(SCALED_IMAGE, POSITION)

def SURFACE_TO_TEXTURE(UI_SURFACE):
	NEW_SCALE = CONSTANTS["UI_RESOLUTION"].TO_INT()
	UI_DATA = PG.image.tostring(UI_SURFACE, "RGBA", 1)
	
	FINAL_ID = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, FINAL_ID)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, int(NEW_SCALE.X), int(NEW_SCALE.Y), 0, GL_RGBA, GL_UNSIGNED_BYTE, UI_DATA)
	
	# Use nearest-neighbor filtering
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	
	return FINAL_ID
