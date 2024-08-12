"""
[load_scene.py]
Loads data for objects, planes, physics bodies, etc from the .dat files
Gives a list of object types, textures, coordinates, dimentions... for render.py to use (via main.py)

______________________
Importing other files;
-texture_load.py
-log.py
-utils.py
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
	from exct.utils import *
	from imgs import texture_load
	from exct import log, utils, render

except ImportError:
	log.ERROR("ui.py", "Initial imports failed.")


log.REPORT_IMPORT("scene.py")

PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS
OVERHANG = 1

#Formatting for each class type's file representation
FORMATTING = {
	0:  (SCENE, ("rgba", "int", "int")),			 									#Scene data (skybox, lighting etc)
	1:  (PLAYER, ("vect", "vect", "list")), 											#Playerdata
	2:  (CUBE_STATIC, ("vect", "vect", "bool", "texture")), 							#Static cube
	3:  (QUAD, ("vect", "vect", "vect", "vect", "bool", "texture")), 					#Quad/Plane
	4:  (TRI, ("vect", "vect", "vect", "bool", "texture")), 							#Triangle
	5:  (SPRITE_STATIC, ("vect", "vect", "texture")), 									#Static Sprite
	6:  (ITEM, ("vect", "hex", "str", "texture")), 										#Item/Suppli-Object
	7:  (TRIGGER, ("vect", "vect", "str")), 											#Trigger Box
	8:  (INTERACTABLE, ("vect", "vect", "vect", "vect", "str", "bool", "texture")), 	#Interactable
	9:  (CUBE_PATH, ("vect", "vect", "vect", "float", "int", "str", "texture")),		#Moving surface (i.e. door)
	10: (ENEMY, ("vect", "vect", "str", "texture")),									#Hostile Enemy
	11: (CUBE_PHYSICS, ("vect", "vect", "float", "texture")), 							#Physics cube
	12: (LIGHT, ("vect", "vect", "rgba", "float", "float", "float", "str")),			#Light object
	13: (NPC_PATH_NODE, ("vect", "hex", "list")),  										#NPC Path node
	14: (LOGIC, ("str", "str", "str", "str")),											#Flag-Logic gate (Not rendered.)
	15: (None, ()),																		#Unused, Placeholder
	#Unavailable in file, but here for the sake of completeness.						--------------------
	16: (PROJECTILE, ("vect", "float", "vect", "str", "texture")),						#Projectile
	17: (EXPLOSION, ("vect", "vect", "float", "float", "texture")),						#Explosion
}



#File loading functions


def PREPARE_SCENE(SCENE_NAME):
	#Prepares the data for a scene.
	RENDER_DATA, PHYS_DATA, SHEET_NAME = LOAD_FILE(SCENE_NAME)
	for OBJECT_ID, OBJECT in PHYS_DATA[0].items():
		if type(OBJECT) == PLAYER:
			PLAYER_ID = OBJECT.ID

	return RENDER_DATA, PHYS_DATA, SHEET_NAME, PLAYER_ID



def LOAD_FILE(FILE_NAME):
	"""
	Loads a file with given name FILE_NAME, returning all data and loading all required textures using load_texture.py
	This info will get given to render.py via main.py, as it contains info for all of the scene's planes and other shapes.
	"""
	CURRENT_ID = 0

	FILE_NAME_FORMATTED = f"scene-{FILE_NAME}.dat"
	main_dir = os.path.dirname(os.path.abspath(__file__))
	file_path = os.path.join(main_dir, FILE_NAME_FORMATTED)

	#Load the given scene.dat file
	with open(file_path, 'r') as FILE:
		FILE_CONTENTS_RAW = FILE.readlines()
	
	FILE_CONTENTS, RENDER_DATASET = [], []
	
	for LINE_RAW in FILE_CONTENTS_RAW:
		FILE_CONTENTS.append(LINE_RAW.strip('\n'))#Remove uneccessary auto-formatting from the file

	#Get the game-data for use here.
	HOSTILES, SUPPLIES, PROJECTILES = utils.GET_GAME_DATA()


	ENV_VAO_DATA = [NP.array([]), NP.array([])]
	KINETICS, STATICS, LIGHTS = {}, [{}, {}], []
	for LINE in FILE_CONTENTS:
		#Read every line
		if LINE not in (""):
			#If the line isnt empty..
			if LINE[0].strip() == ">":
				#Current sheet is given by "> ID"
				SHEET_ID = (LINE.strip()).split(" ")[-1]

			elif LINE[0].strip() not in ("/",):
				#"/" marks a comment, so if it is NOT that, read the line.
				LINE_DATA = (LINE.strip()).split(' | ')
				OBJECT_TYPE = int(LINE_DATA[0], 16)

				CLASS_TYPE, FORMAT = FORMATTING[OBJECT_TYPE]
				OBJECT_DATA = []


				for SECTION, RAW_DATA in zip(FORMAT, LINE_DATA[1:]):
					#Read each part of the data-line, and interpret said part using the formatting for each type.
					DATA = RAW_DATA.strip(" ")
					if DATA != "":
						match SECTION:
							case "vect":
								FILE_VECTOR = DATA.split(', ')
								OBJECT_DATA.append(VECTOR_3D(round(float(FILE_VECTOR[0]), 8), round(float(FILE_VECTOR[1]), 8), round(float(FILE_VECTOR[2]), 8)))

							case "texture":
								TEXTURE_IDs = DATA.split("/")
								OBJECT_DATA.append(TEXTURE_IDs)

							case "bool":
								BOOLEAN = DATA.split(".")
								for I, BOOL in enumerate(BOOLEAN):
									if BOOL == "T":
										BOOLEAN[I] = True
									elif BOOL == "F":
										BOOLEAN[I] = False
								OBJECT_DATA.append(BOOLEAN)

							case "rgba":
								FILE_VECTOR = DATA.split(', ')
								OBJECT_DATA.append(RGBA(round(float(FILE_VECTOR[0]), 8), round(float(FILE_VECTOR[1]), 8), round(float(FILE_VECTOR[2]), 8), round(float(FILE_VECTOR[2]), 8)))

							case "int":
								OBJECT_DATA.append(int(DATA))

							case "float":
								OBJECT_DATA.append(float(DATA))

							case "hex":
								OBJECT_DATA.append(hex(int(DATA, 16)))

							case "list":
								OBJECT_DATA.append(DATA.split(":"))

							case "str":
								OBJECT_DATA.append(DATA)

				
				TEXTURE_DATA = []
				CURRENT_TEXTURE_DATA = []
				texture_load.SHEET_ID = None

				if CLASS_TYPE == SCENE:
					#Scene is handled differently to the rest, as it isn't particularly "anywhere" in the scene.
					FINALISED_OBJECT = SCENE(CONSTANTS["VOID_COLOUR"], CONSTANTS["GRAVITY"], CONSTANTS["MULT_AIR_RES"])


				elif CLASS_TYPE == LOGIC:
					#Same story for the LOGIC, as it isn't at any set location.
					pass



				elif CLASS_TYPE in [CUBE_STATIC, TRI, QUAD, NPC_PATH_NODE, LIGHT, INTERACTABLE, CUBE_PATH, SPRITE_STATIC]:
					#Static, non-physics based objects.
					CURRENT_ID += 1

					if CLASS_TYPE == CUBE_STATIC:
						POINTS = utils.FIND_CUBOID_POINTS(OBJECT_DATA[1], OBJECT_DATA[0])
						NORMALS = utils.FIND_CUBOID_NORMALS(POINTS)

						for TEXTURE in OBJECT_DATA[3]:
							TEXTURE_DATA.append(texture_load.TEXTURE_CACHE_MANAGER(str(TEXTURE)))

						FINALISED_OBJECT = CUBE_STATIC(CURRENT_ID, OBJECT_DATA[0], OBJECT_DATA[1], OBJECT_DATA[3], TEXTURE_DATA)

					elif CLASS_TYPE == QUAD:
						POINTS = OBJECT_DATA[:4]
						TEXTURE_DATA = texture_load.TEXTURE_CACHE_MANAGER(str(OBJECT_DATA[5][0]))

						FINALISED_OBJECT = QUAD(CURRENT_ID, POINTS, OBJECT_DATA[4], TEXTURE_DATA)

					elif CLASS_TYPE == TRI:
						POINTS = OBJECT_DATA[0:3]
						TEXTURE_DATA = texture_load.TEXTURE_CACHE_MANAGER(str(OBJECT_DATA[4][0]))

						FINALISED_OBJECT = TRI(CURRENT_ID, POINTS, OBJECT_DATA[3][0], TEXTURE_DATA)

					elif CLASS_TYPE == NPC_PATH_NODE:
						CENTRE = OBJECT_DATA[0]
						FLAG = OBJECT_DATA[1]
						NEIGHBOURS = OBJECT_DATA[2]

						FINALISED_OBJECT = NPC_PATH_NODE(CENTRE, FLAG, NEIGHBOURS)

					elif CLASS_TYPE == LIGHT:
						POSITION = OBJECT_DATA[0]
						LOOK_AT = OBJECT_DATA[1]
						COLOUR = OBJECT_DATA[2]
						INTENSITY = OBJECT_DATA[3]
						FOV = OBJECT_DATA[4]
						MAX_DIST = OBJECT_DATA[5]
						FLAG = OBJECT_DATA[6]

						FINALISED_OBJECT = LIGHT(CURRENT_ID, POSITION, LOOK_AT, FOV, COLOUR, INTENSITY, MAX_DIST, FLAG)
						LIGHTS.append(FINALISED_OBJECT)

					elif CLASS_TYPE == INTERACTABLE:
						POINTS = OBJECT_DATA[:4]
						FLAG = OBJECT_DATA[5]
						TEXTURE_DATA = texture_load.TEXTURE_CACHE_MANAGER(str(OBJECT_DATA[5][0]))

						FINALISED_OBJECT = INTERACTABLE(CURRENT_ID, POINTS, OBJECT_DATA[4], TEXTURE_DATA, FLAG)

					elif CLASS_TYPE == CUBE_PATH:
						CENTRE = OBJECT_DATA[0]
						DIMENTIONS = OBJECT_DATA[1]
						MOVEMENT = OBJECT_DATA[2]
						MAX_DISTANCE = OBJECT_DATA[3]
						SPEED = OBJECT_DATA[4]
						FLAG = OBJECT_DATA[5]
						for TEXTURE in OBJECT_DATA[6]:
							CURRENT_TEXTURE_DATA.append(texture_load.TEXTURE_CACHE_MANAGER(str(TEXTURE)))

						FINALISED_OBJECT = CUBE_PATH(CURRENT_ID, CENTRE, DIMENTIONS, CURRENT_TEXTURE_DATA, MOVEMENT, SPEED, FLAG, MAX_DISTANCE)

					elif CLASS_TYPE == SPRITE_STATIC:
						CENTRE = OBJECT_DATA[0]
						DIMENTIONS = OBJECT_DATA[1]
						TEXTURE_DATA = texture_load.TEXTURE_CACHE_MANAGER(str(OBJECT_DATA[2][0]))

						FINALISED_OBJECT = SPRITE_STATIC(CURRENT_ID, CENTRE, DIMENTIONS, TEXTURE_DATA)

					if TEXTURE_DATA != [] and CLASS_TYPE not in [SPRITE_STATIC,]:
						#Add to the VAO data, as long as it isnt a dynamic object like a STATIC_SPRITE.
						ENV_VAO_DATA = render.OBJECT_VAO_MANAGER(FINALISED_OBJECT, ENV_VAO_DATA)

					#STATICS for the environmental objects.
					if FINALISED_OBJECT.COLLISION:
						#If it has collision, add it to the dict physics.py checks.
						STATICS[0][CURRENT_ID] = FINALISED_OBJECT
					else:
						#If not, it still must be rendered - add to the dict physics.py DOESNT check.
						STATICS[1][CURRENT_ID] = FINALISED_OBJECT



				elif CLASS_TYPE in [PLAYER, SPRITE_STATIC, ITEM, ENEMY, CUBE_PHYSICS]:
					#Physics based objects.
					CURRENT_ID += 1

					if CLASS_TYPE == PLAYER:
						CENTRE = OBJECT_DATA[0]
						CONSTANTS["PLAYER_INITIAL_POS"] = CENTRE
						FINALISED_OBJECT = PLAYER(CURRENT_ID, CENTRE, OBJECT_DATA[1], OBJECT_DATA[2])

					elif CLASS_TYPE == ITEM:
						CENTRE = OBJECT_DATA[0]
						ITEM_TYPE = OBJECT_DATA[2]
						TEXTURE_DATA = texture_load.TEXTURE_CACHE_MANAGER(str(OBJECT_DATA[3][0]))

						FINALISED_OBJECT = ITEM(CURRENT_ID, CENTRE, False, TEXTURE_DATA, ITEM_TYPE)

					elif CLASS_TYPE == ENEMY:
						CENTRE = OBJECT_DATA[0]
						ROTATION = OBJECT_DATA[1]
						ENEMY_TYPE = OBJECT_DATA[2]

						TEXTURES = []
						for TEXTURE in OBJECT_DATA[3]:
							TEXTURES.append(texture_load.TEXTURE_CACHE_MANAGER(str(TEXTURE)))

						FINALISED_OBJECT = ENEMY(CURRENT_ID, CENTRE, ENEMY_TYPE, TEXTURES, ROTATION)

					elif CLASS_TYPE == CUBE_PHYSICS:
						CENTRE = OBJECT_DATA[0]
						DIMENTIONS = OBJECT_DATA[1]
						MASS = OBJECT_DATA[2]

						for TEXTURE in OBJECT_DATA[3]:
							CURRENT_TEXTURE_DATA.append(texture_load.TEXTURE_CACHE_MANAGER(str(TEXTURE)))

						FINALISED_OBJECT = CUBE_PHYSICS(CURRENT_ID, CENTRE, DIMENTIONS, MASS, VECTOR_3D(0, 0, 0), CURRENT_TEXTURE_DATA)


					#Add it to the physics list (Kinetics)
					KINETICS[CURRENT_ID] = FINALISED_OBJECT



	PHYS_DATA = (KINETICS, STATICS)
	RENDER_DATA = (ENV_VAO_DATA, LIGHTS)
	return RENDER_DATA, PHYS_DATA, SHEET_ID


