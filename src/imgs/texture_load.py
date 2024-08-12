"""
[texture_load.py]
Loads textures from .bmp files in /imgs/
Will reuse data from previous loaded textures, to prevent repeated data.

______________________
Importing other files;
-log.py
"""
import sys, os
import math as maths
import zipfile
import io
import copy
import numpy as NP

#Load log.py, from the subfolder \src\exct\
sys.path.extend(("src", r"src\modules", r"src\exct\data", r"src\exct\glsl"))
from exct import log
#Load modules stored in \src\modules\
import glm, glfw

import pygame as PG
from pygame import time, joystick, display, image

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import compileProgram, compileShader

from PIL import Image

from pyrr import Matrix44, Vector3, Vector4

from exct import log, utils, render
from exct.utils import *


log.REPORT_IMPORT("texture_load.py")
"""
Texture cache;
> stores all previously loaded textures
> if a texture is called to be loaded, it is checked for duplicates in here first
> if duplicate found, return duplicate
> otherwise, load texture, add to cache and return data
"""
PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS
global TEXTURE_CACHE, SHEET_CACHE
TEXTURE_CACHE = {}
SHEET_CACHE = {}


#Texture loading functions


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



def LOAD_SHEET(FILE_NAME, SUBFOLDER=None):
	if SUBFOLDER is None:
		MAIN_DIR = os.path.dirname(os.path.abspath(__file__))
		TEXTURE_PATH = os.path.join(MAIN_DIR, f"sheet-{FILE_NAME}.png")
	else:
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
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

	SHEET_CACHE[FILE_NAME] = SHEET_ID

	return SHEET_ID