"""
[ui.py]
Creates the UI, based off of data such as player stats and current item.
Makes use of PyGame drawing/image manipulation functions.
______________________
Importing other files;
-texture_load.py
-log.py
"""
from exct import log
try:
	#Importing base python modules
	import sys, os
	import math as maths
	import zipfile
	import io
	import copy
	import numpy as NP

	#Stop PyGame from giving that annoying welcome message
	os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

	#Load modules stored in \src\modules\
	sys.path.extend(("src", r"src\modules", r"src\exct\data", r"src\exct\glsl"))
	import glm, glfw
	import pygame as PG
	from pygame import time, joystick, display, image
	from OpenGL.GL import *
	from OpenGL.GLU import *
	from OpenGL.GL.shaders import compileProgram, compileShader
	from PIL import Image
	from pyrr import Matrix44, Vector3, Vector4

	#Import other sub-files.
	from imgs import texture_load
	from exct import log, utils, render
	from exct.utils import *

except ImportError:
	log.ERROR("ui.py", "Initial imports failed.")


log.REPORT_IMPORT("ui.py")


PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS
UI_SURFACE = PG.Surface(CONSTANTS["UI_RESOLUTION"].TO_LIST(), PG.SRCALPHA)
#Dictionary of "standard" UI colours.
UI_COLOURS = {
	"SMOKY_BLACK": (20, 17, 15),
	"DAVYS_GRAY": (72, 71, 74),
	"SILVER": (186, 186, 186),
	"WHITE_SMOKE": (245, 245, 245),
	"MOSS_GREEN": (116, 142, 84),
	"GOLD_TIPS": (229, 172, 43),
}


#General UI related functions


def DRAW_TEXT(SCREEN, TEXT, POSITION, FONT_SIZE, COLOUR=(255, 255, 255)):
	#Draws text on a given surface, with colour, size and position.
	FONT = PG.font.Font('src\\exct\\fonts\\PressStart2P-Regular.ttf', FONT_SIZE)
	text_surface = FONT.render(str(TEXT), True, COLOUR)
	SCREEN.blit(text_surface, POSITION)

def DRAW_IMG(SCREEN, IMG_NAME, POSITION, SCALE):
	#Draws an image loaded from the file structure (in \src\imgs\) to a position and with scale.
	IMAGE = PG.image.load(f"src\\imgs\\{IMG_NAME}")
	SCALED_IMAGE = PG.transform.scale(IMAGE, SCALE)
	SCREEN.blit(SCALED_IMAGE, POSITION)


#Per-Frame HUD


def HUD(PLAYER, FPS):
	#Draws the heads-up display (HUD) user-interface (UI) onto a PyGame surface, which is then returned as an OpenGL texture.
	#Uses data about the player, such as Health and Energy.

	#Fill the UI surface with transparent pixels first.
	UI_SURFACE.fill([0, 0, 0, 0])

	#Draw the "Crosshair" cross.
	PG.draw.line(UI_SURFACE, UI_COLOURS["SMOKY_BLACK"], (320, 177), (320, 183.5), 3)
	PG.draw.line(UI_SURFACE, UI_COLOURS["SMOKY_BLACK"], (317, 180), (323.5, 180), 3)
	PG.draw.line(UI_SURFACE, UI_COLOURS["SILVER"], (320, 177.5), (320, 183.5), 1)
	PG.draw.line(UI_SURFACE, UI_COLOURS["SILVER"], (317.5, 180), (323.5, 180), 1)

	#Draw the lower-left info panel.
	DRAW_TEXT(UI_SURFACE, str(PLAYER.ENERGY).zfill(3), (105, 322), 16, COLOUR=UI_COLOURS["GOLD_TIPS"])
	DRAW_TEXT(UI_SURFACE, str(PLAYER.HEALTH).zfill(3), (105, 343), 16, COLOUR=UI_COLOURS["GOLD_TIPS"])
	DRAW_IMG(UI_SURFACE, "ENERGY.png", (5, 322), (94, 16))
	DRAW_IMG(UI_SURFACE, "HEALTH.png", (5, 343), (88, 16))

	#Top-Right corner's FPS counter.
	DRAW_TEXT(UI_SURFACE, f"FPS: {str(maths.floor(FPS)).zfill(2)}", (583, 2), 8, COLOUR=UI_COLOURS["GOLD_TIPS"])

	#Top-Left debug notices.
	DEBUG_TYPES = {
		"DEBUG_MAPS": PREFERENCES["DEBUG_MAPS"],
		"DEBUG_UI": PREFERENCES["DEBUG_UI"],
		"DEBUG_NORMALS": PREFERENCES["DEBUG_NORMALS"],
		"DEBUG_PROFILER": PREFERENCES["DEBUG_PROFILER"],
		"DEV_TEST": PREFERENCES["DEV_TEST"]
	}
	SHOWN_DEBUG_TYPES = []
	for DEBUG_TYPE, ENABLED in DEBUG_TYPES.items():
		if ENABLED:
			SHOWN_DEBUG_TYPES.append(DEBUG_TYPE)

	for I, DEBUG_TYPE in enumerate(SHOWN_DEBUG_TYPES):
		DRAW_TEXT(UI_SURFACE, DEBUG_TYPE, (5, (10*I) + 2), 8, COLOUR=UI_COLOURS["GOLD_TIPS"])
		

	#Convert to an OpenGL texture.
	UI_SURFACE_ID = render.SURFACE_TO_TEXTURE(UI_SURFACE, CONSTANTS["UI_RESOLUTION"].TO_INT())

	return UI_SURFACE_ID
