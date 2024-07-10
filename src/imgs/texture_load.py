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

DIMENTIONS is a 2 item list for the lengths of each side (Left, Top), mostly for planes;
-When N/A (Like spheres) it is None
-in Cubes/Cuboids it is the side lengths
-in "sprites" (pretend sprites, real implementation non-existant in my code) it is also None, as it is always (1, 1)
"""
global TEXTURE_CACHE, SHEET_CACHE
TEXTURE_CACHE = {}
SHEET_CACHE = {}
PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS


def TEXTURE_CACHE_MANAGER(HEX_ID):
	if HEX_ID in TEXTURE_CACHE:
		return SHEET_ID, TEXTURE_CACHE[HEX_ID]

	else:
		Y_ID = int(HEX_ID[0], 16)
		X_ID = int(HEX_ID[1], 16)

		LEFT_X = round((X_ID / 16), 8)
		RIGHT_X = round(((X_ID + 1) / 16), 8)
		TOP_Y = round(1 - (Y_ID / 16), 8)
		BOTTOM_Y = round((1 - (Y_ID + 1) / 16) , 8)

		BL = VECTOR_2D(LEFT_X, BOTTOM_Y) #Bottom-Left
		BR = VECTOR_2D(RIGHT_X, BOTTOM_Y) #Bottom-Right
		TR = VECTOR_2D(RIGHT_X, TOP_Y) #Top-Right
		TL = VECTOR_2D(LEFT_X, TOP_Y) #Top-Left


		TEXTURE_COORDINATES = render.CLIP_EDGES([BL, BR, TR, TL])

		return TEXTURE_COORDINATES

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

	SHEET_CACHE[FILE_NAME] = SHEET_ID

	return SHEET_ID



def FILE_FORMAT(HEX_ID):
	TEXTURE_ID = str(HEX_ID)
	FILE_FORMAT="png"
	return f"{TEXTURE_ID}.{FILE_FORMAT}"



def LOAD_NEW_TEXTURE(FILE_NAME):
	MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
	TEXTURE_PATH = os.path.join(MAIN_DIR, FILE_NAME)

	SURFACE = PG.image.load(TEXTURE_PATH)
	DATA = PG.image.tostring(SURFACE, 'RGBA', 1)
	WIDTH, HEIGHT = SURFACE.get_width(), SURFACE.get_height()

	TEXTURE_ID = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, TEXTURE_ID)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WIDTH, HEIGHT, 0, GL_RGBA, GL_UNSIGNED_BYTE, DATA)

	TEXTURE_CACHE[FILE_NAME] = TEXTURE_ID
	
	return TEXTURE_ID

	"""
	TEXTURE_COORDINATES = ((0, 0), (1, 0), (1, 1), (0, 1))

	FILE_NAME = FILE_FORMAT(HEX_ID)
	
	if FILE_NAME in TEXTURE_CACHE:
		TEXTURE_ID =  TEXTURE_CACHE[FILE_NAME]
	
	else:
		TEXTURE_ID = LOAD_NEW_TEXTURE(FILE_NAME)
		
	return (TEXTURE_ID, TEXTURE_COORDINATES)
	"""
