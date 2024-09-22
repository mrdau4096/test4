"""
[texture_load.py]
Loads textures from .bmp files in /imgs/
Will reuse data from previous loaded textures, to prevent repeated data.

______________________
Importing other files;
-log.py
"""

from exct import log
try:
	#Importing base python modules
	import sys, os
	import math as maths
	import numpy as NP

	#Stop PyGame from giving that annoying welcome message
	os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

	sys.path.extend(("src", r"src\exct\data", r"src\exct\glsl"))
	import pygame as PG
	from pygame import time, joystick, display, image
	from OpenGL.GL import *
	from OpenGL.GLU import *
	from OpenGL.GL.shaders import compileProgram, compileShader

	#Import other sub-files.
	from exct import utils, render
	from exct.utils import *

except Exception as E:
	log.ERROR("texture_load.py", E)

log.REPORT_IMPORT("texture_load.py")


"""
Texture cache;
> stores all previously loaded textures and their UV coordinates
> if a texture is called to be loaded, it is checked for duplicates in here first
> if duplicate found, return duplicate
> otherwise, load texture, add to cache and return data

Sheet cache;
> same as Texture cache, but for OpenGL sheet IDs
> no need to re-load a texture.
"""
PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS
global TEXTURE_CACHE, SHEET_CACHE
TEXTURE_CACHE = {}
SHEET_CACHE = {}


#Texture loading functions


def TEXTURE_CACHE_MANAGER(HEX_ID):
	#Loads a set texture based off of a 2-hex-digit positional ID (FF is bottom right, X=16, Y=16)
	#If already in the texture cache, give that data to prevent re-loading of information
	#try:
		if HEX_ID in TEXTURE_CACHE:
			return TEXTURE_CACHE[HEX_ID]

		else:
			Y_ID = int(HEX_ID[0], 16)
			X_ID = int(HEX_ID[1], 16)

			PIXELS_PER_TILE = 128

			LEFT_X_PIXELS = X_ID * PIXELS_PER_TILE
			RIGHT_X_PIXELS = ((X_ID + 1) * PIXELS_PER_TILE) - 5
			TOP_Y_PIXELS = Y_ID * PIXELS_PER_TILE
			BOTTOM_Y_PIXELS = ((Y_ID + 1) * PIXELS_PER_TILE) - 5

			LEFT_X = LEFT_X_PIXELS / 2048.0
			RIGHT_X = RIGHT_X_PIXELS / 2048.0
			TOP_Y = 1.0 - (TOP_Y_PIXELS / 2048.0)
			BOTTOM_Y = 1.0 - (BOTTOM_Y_PIXELS / 2048.0)

			BL = VECTOR_2D(LEFT_X, BOTTOM_Y)	#Bottom-Left
			BR = VECTOR_2D(RIGHT_X, BOTTOM_Y)	#Bottom-Right
			TR = VECTOR_2D(RIGHT_X, TOP_Y)		#Top-Right
			TL = VECTOR_2D(LEFT_X, TOP_Y)		#Top-Left

			TEXTURE_COORDINATES = (BL, BR, TR, TL)
			TEXTURE_CACHE[HEX_ID] = TEXTURE_COORDINATES

			return TEXTURE_COORDINATES

	#except Exception as E:
		#log.ERROR("texture_load.TEXTURE_CACHE_MANAGER", E)



def LOAD_SHEET(FILE_NAME, SUBFOLDER=None, SHEET=True, SHEET_LIST=SHEET_CACHE):
	#Loads a texture sheet or other image file.
	#try:
		if FILE_NAME in SHEET_LIST:
			SHEET_ID = SHEET_LIST[FILE_NAME]

		else:
			if SUBFOLDER is None:
				MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
				TEXTURE_PATH = os.path.join(MAIN_DIR, f"{'sheet-' if SHEET else ''}{FILE_NAME}.png")

			else:
				#Loads from a specified sub-folder rather than \src\imgs\ by default.
				MAIN_DIR = os.path.dirname(os.path.abspath(__file__)).replace(r"\src\imgs", SUBFOLDER)
				TEXTURE_PATH = os.path.join(MAIN_DIR, f"{FILE_NAME}.png")


			SURFACE = PG.image.load(TEXTURE_PATH)
			DATA = PG.image.tostring(SURFACE, 'RGBA', 1)
			WIDTH, HEIGHT = SURFACE.get_width(), SURFACE.get_height()

			SHEET_ID = glGenTextures(1)
			glBindTexture(GL_TEXTURE_2D, SHEET_ID)
			glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WIDTH, HEIGHT, 0, GL_RGBA, GL_UNSIGNED_BYTE, DATA)
			
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

			#Write to sheet cache to prevent re-generating if required again
			SHEET_LIST[FILE_NAME] = SHEET_ID

		SHEET_CACHE = SHEET_LIST
		return SHEET_ID

		
	#except Exception as E:
		#log.ERROR("texture_load.LOAD_SHEET", E)