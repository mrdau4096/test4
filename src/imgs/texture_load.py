"""
[texture_load.py]
Loads textures from .bmp files in /imgs/
Will reuse data from previous loaded textures, to prevent repeated data.

______________________
Importing other files;
-log.py
"""
#Import Internal modules
from exct import log, utils, render
from exct.utils import *


#Import External modules
import os, sys

CURRENT_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)
sys.path.append("modules")

import pygame as PG
from pygame.locals import *
from pygame import image
from OpenGL.GL import *
from OpenGL.GLU import *

print("Imported Sub-file // texture_load.py")

"""
Texture cache;
> stores all previously loaded textures
> if a texture is called to be loaded, it is checked for duplicates in here first
> if duplicate found, return duplicate
> otherwise, load texture, add to cache and return data
"""
global SHEET_CACHE, UV_CACHE, SHEET_INDEX_LIST
SHEET_CACHE, UV_CACHE, SHEET_INDEX_LIST = {}, {}, []
PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS


#Texture loading functions


def TEXTURE_CACHE_MANAGER(TEXTURE_NAME):
	SPLIT_DATA = TEXTURE_NAME.split("-")
	SHEET_NAME = ("").join(SPLIT_DATA[:-1]) if len(SPLIT_DATA) > 1 else "base"
	UV_COORDS = SPLIT_DATA[-1]

	if SHEET_NAME in SHEET_CACHE:
		SHEET_ID = SHEET_CACHE[SHEET_NAME]
	else:
		try:
			SHEET_ID = LOAD_SHEET(SHEET_NAME)
		except FileNotFoundError:
			try:
				SHEET_ID = LOAD_SHEET("base")
			except FileNotFoundError:
				#Raise a more descriptive error for the logging system to handle.
				raise FileNotFoundError(f"Neither sheet-{ATTEMPTED_SHEET_NAME}.png nor sheet-base.png could be found in \\src\\imgs\\")

		SHEET_CACHE[SHEET_NAME] = SHEET_ID
		SHEET_INDEX_LIST.append(SHEET_NAME)


	if UV_COORDS in UV_CACHE:
		COORDINATES = UV_CACHE[UV_COORDS]
	else:
		Y_ID = int(UV_COORDS[0], 16)
		X_ID = int(UV_COORDS[1], 16)

		LEFT_X = round((X_ID / 16), 8)
		RIGHT_X = round(((X_ID + 1) / 16), 8)
		TOP_Y = round(1 - (Y_ID / 16), 8)
		BOTTOM_Y = round((1 - (Y_ID + 1) / 16) , 8)

		BL = VECTOR_2D(LEFT_X, BOTTOM_Y)	#Bottom-Left Texture Coordinate
		BR = VECTOR_2D(RIGHT_X, BOTTOM_Y)	#Bottom-Right Texture Coordinate
		TR = VECTOR_2D(RIGHT_X, TOP_Y)		#Top-Right Texture Coordinate
		TL = VECTOR_2D(LEFT_X, TOP_Y)		#Top-Left Texture Coordinate

		COORDINATES = render.CLIP_EDGES([BL, BR, TR, TL])
		UV_CACHE[UV_COORDS] = COORDINATES

	
	return SHEET_NAME, COORDINATES



def LOAD_SHEET(FILE_NAME):
	MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
	TEXTURE_PATH = os.path.join(MAIN_DIR, f"sheet-{FILE_NAME}.png")

	SURFACE = PG.image.load(TEXTURE_PATH)
	DATA = PG.image.tostring(SURFACE, 'RGBA', 1)
	WIDTH, HEIGHT = SURFACE.get_width(), SURFACE.get_height()

	SHEET_ID = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, SHEET_ID)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WIDTH, HEIGHT, 0, GL_RGBA, GL_UNSIGNED_BYTE, DATA)
	
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

	return SHEET_ID