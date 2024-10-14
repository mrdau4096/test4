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
UV_CACHE, SHEET_CACHE, IMG_CACHE = {}, {}, {}
FALLBACK_TEXTURE = "fallback"


#Texture loading functions


def UV_CACHE_MANAGER(HEX_ID):
		"""
		Loads a set of UV coordinates based off of a 2-hex-digit positional ID (FF is bottom right, X=16, Y=16)
		If already in the UV-cache, give that data to prevent re-loading of information
		"""
	#try:
		if HEX_ID in UV_CACHE:
			TEXTURE_COORDINATES = UV_CACHE[HEX_ID]

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
			UV_CACHE[HEX_ID] = TEXTURE_COORDINATES

		return TEXTURE_COORDINATES

	#except Exception as E:
		#log.ERROR("texture_load.UV_CACHE_MANAGER", E)



def LOAD_SHEET(FILE_NAME, SUBFOLDER=None, SHEET=True, SHEET_CACHE=SHEET_CACHE, FALLBACK=False):
	#Loads a texture sheet or other image file.
	try:
		if FILE_NAME in SHEET_CACHE:
			DATA, (WIDTH, HEIGHT) = SHEET_CACHE[FILE_NAME]

		else:
			if SUBFOLDER is None:
				MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
				TEXTURE_PATH = os.path.join(MAIN_DIR, f"{'sheet-' if SHEET else ''}{FILE_NAME}.png")

			else:
				#Loads from a specified sub-folder rather than \src\imgs\ by default.
				MAIN_DIR = os.path.dirname(os.path.abspath(__file__)).replace(r"\src\imgs", SUBFOLDER)
				TEXTURE_PATH = os.path.join(MAIN_DIR, f"{FILE_NAME}.png")


			SURFACE = PG.image.load(TEXTURE_PATH)
			RESIZED_SURFACE = PG.transform.scale(SURFACE, (2048, 2048))
			BYTES_DATA = PG.image.tostring(RESIZED_SURFACE, 'RGBA', 1)
			DATA = NP.frombuffer(BYTES_DATA, dtype=NP.uint8).reshape((2048, 2048, 4))
			WIDTH, HEIGHT = SURFACE.get_width(), SURFACE.get_height()

			SHEET_CACHE[FILE_NAME] = (DATA, (WIDTH, HEIGHT))
		
		return DATA, (WIDTH, HEIGHT)

		
	except FileNotFoundError:
		if not FALLBACK:
			PREFIX = 'sheet-' if SHEET else ''
			return LOAD_SHEET(FALLBACK_TEXTURE, SHEET=False, FALLBACK=True)
		else:
			log.ERROR("texture_load.py // LOAD_SHEET", f"Neither {PREFIX}{FILE_NAME}.png nor the fallback texture were found.")
	except Exception as E:
		log.ERROR("texture_load.py // LOAD_SHEET", E)



def LOAD_IMG(FILE_NAME, SUBFOLDER=None, OPENGL=False, FALLBACK=False):
	#Loads a texture sheet or other image file.
	try:
		if FILE_NAME in IMG_CACHE:
			STRING_DATA = IMG_CACHE[FILE_NAME]
			BYTES_DATA = NP.frombuffer(STRING_DATA, dtype=NP.uint8).reshape((2048, 2048, 4))

			if OPENGL:
				DATA = render.CREATE_TEXTURE_FROM_DATA(
					BYTES_DATA,
					GL_TYPE=GL_RGBA,
					FILTER=GL_NEAREST,
					DATA_TYPE=GL_UNSIGNED_BYTE
				)
			else:
				DATA = STRING_DATA

		else:
			if SUBFOLDER is None:
				MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
				TEXTURE_PATH = os.path.join(MAIN_DIR, f"{FILE_NAME}.png")

			else:
				#Loads from a specified sub-folder rather than \src\imgs\ by default.
				MAIN_DIR = os.path.dirname(os.path.abspath(__file__)).replace(r"\src\imgs", SUBFOLDER)
				TEXTURE_PATH = os.path.join(MAIN_DIR, f"{FILE_NAME}.png")


			SURFACE = PG.image.load(TEXTURE_PATH)
			RESIZED_SURFACE = PG.transform.scale(SURFACE, (2048, 2048))
			STRING_DATA = PG.image.tostring(RESIZED_SURFACE, 'RGBA', 1)
			BYTES_DATA = NP.frombuffer(STRING_DATA, dtype=NP.uint8).reshape((2048, 2048, 4))

			IMG_CACHE[FILE_NAME] = STRING_DATA

			if OPENGL:
				DATA = render.CREATE_TEXTURE_FROM_DATA(
					BYTES_DATA,
					GL_TYPE=GL_RGBA,
					FILTER=GL_NEAREST,
					DATA_TYPE=GL_UNSIGNED_BYTE
				)
			else:
				DATA = STRING_DATA
		
		return DATA

		
	except FileNotFoundError:
		if not FALLBACK:
			PREFIX = 'sheet-' if SHEET else ''
			return LOAD_SHEET(FALLBACK_TEXTURE, SHEET=False, FALLBACK=True)
		else:
			log.ERROR("texture_load.py // LOAD_SHEET", f"Neither {PREFIX}{FILE_NAME}.png nor the fallback texture were found.")
	except Exception as E:
		log.ERROR("texture_load.py // LOAD_SHEET", E)



def CREATE_SHEET_ARRAY(SHEETS, FROM_FILE=False, DIMENTIONS=CONSTANTS["TEXTURE_SHEET_DIMENTIONS"], GL_TYPE=GL_RGBA, DATA_TYPE=GL_UNSIGNED_BYTE):
	TEXTURE_WIDTH, TEXTURE_HEIGHT = int(DIMENTIONS.X), int(DIMENTIONS.Y)
	if FROM_FILE:
		SHEETS_DATA = NP.zeros((len(SHEETS), TEXTURE_HEIGHT, TEXTURE_WIDTH, 4), dtype=NP.uint8)
		for I, SHEET_NAME in enumerate(SHEETS):
			SHEETS_DATA[I] = (LOAD_SHEET(SHEET_NAME)[0])
	else:
		SHEETS_DATA = SHEETS

	if DATA_TYPE == GL_FLOAT:
		INTERNAL_FORMAT = GL_RGB32F
	else:
		INTERNAL_FORMAT = GL_RGBA

	ARRAY_ID = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D_ARRAY, ARRAY_ID)

	glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_NEAREST)


	glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, INTERNAL_FORMAT, TEXTURE_HEIGHT, TEXTURE_WIDTH, SHEETS_DATA.shape[0], 0, GL_TYPE, DATA_TYPE, SHEETS_DATA)

	glBindTexture(GL_TEXTURE_2D_ARRAY, 0)

	render.GL_ERRORCHECK()

	return ARRAY_ID
