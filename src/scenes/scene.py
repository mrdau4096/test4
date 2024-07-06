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
#Importing Internal modules
from imgs import texture_load
from exct import log, utils, render
from exct.utils import *

#Importing External modules
import os, sys
CURRENT_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)
sys.path.append("modules.zip")
import numpy as NP

print("Imported Sub-file // scene.py")

FIND_VECTOR = utils.FIND_VECTOR

global OVERHANG
PREFERENCES, CONSTANTS = utils.GET_CONFIGS()
OVERHANG = 1

FORMATTING = {
	0:  (SCENE, ("rgba", "int", "int")),			 									#Scene data (skybox, lighting etc)
	1:  (PLAYER, ("vect", "vect", "list")), 											#Playerdata
	2:  (CUBE_STATIC, ("vect", "vect", "bool", "texture")), 							#Static cube
	3:  (QUAD, ("vect", "vect", "vect", "vect", "bool", "texture")), 					#Quad
	4:  (TRI, ("vect", "vect", "vect", "bool", "texture")), 							#Triangle
	5:  (SPRITE_STATIC, ("vect", "vect", "bool", "texture")), 							#Static Sprite
	6:  (ITEM, ("vect", "hex", "str", "texture")), 										#Item
	7:  (TRIGGER, ("vect", "vect", "str")), 											#Trigger
	8:  (INTERACTABLE, ("vect", "vect", "vect", "vect", "str", "bool", "texture")), 	#Interactable
	9:  (CUBE_PATH, ("vect", "vect", "vect", "int", "str", "texture")),	 				#Moving surface (i.e. door)
	10: (ENEMY, ("vect", "vect", "str")), 												#Hostile
	11: (CUBE_PHYSICS, ("vect", "vect", "float", "texture")), 							#Phys-cube
	12: (LIGHT, ("vect", "vect", "rgba", "float", "float", "float", "str")),			#Light
	13: (NPC_PATH_NODE, ("vect", "hex", "list")),  										#NPC Path node
	14: (None, ()),																		#Unused
	15: (None, ())																		#Unused
}


def READ_COORDS(LINE, NUMBER_OF_COORDS, START_CHAR, MULTIPLIER):
	OUTPUT = []
	for I in range(NUMBER_OF_COORDS):
		COORDINATE = LINE[(I*4)+START_CHAR:((I+1)*4)+START_CHAR]
		OUTPUT.append(int(COORDINATE, 16)/10)
	
	return OUTPUT


def PREPARE_SCENE(SCENE_NAME):
	RENDER_DATA, PHYS_DATA, SHEET_ID = LOAD_FILE(SCENE_NAME)
	CURRENT_SHEET_ID = texture_load.LOAD_SHEET(SHEET_ID)
	for OBJECT_ID, OBJECT in PHYS_DATA[0].items():
		if type(OBJECT) == PLAYER:
			PLAYER_ID = OBJECT.ID



	return RENDER_DATA, PHYS_DATA, CURRENT_SHEET_ID, PLAYER_ID


def LOAD_FILE(FILE_NAME):
	CURRENT_ID = 0
	"""
	Loads a file with given name FILE_NAME, returning all data and loading all required textures using load_texture.py
	This info will get given to render.py by main.py, as it contains info for all of the scene's planes and other shapes.
	"""
	FILE_NAME_FORMATTED = f"scene-{FILE_NAME}.dat"
	main_dir = os.path.dirname(os.path.abspath(__file__))
	file_path = os.path.join(main_dir, FILE_NAME_FORMATTED)

	with open(file_path, 'r') as FILE:
		FILE_CONTENTS_RAW = FILE.readlines()
	
	FILE_CONTENTS, RENDER_DATASET = [], []
	
	for LINE_RAW in FILE_CONTENTS_RAW:
		FILE_CONTENTS.append(LINE_RAW.strip('\n'))#Remove uneccessary auto-formatting from the file

	ENV_VAO_DATA = [NP.array([]), NP.array([])]
	KINETICS, STATICS, LIGHTS = {}, [{}, {}], []
	for LINE in FILE_CONTENTS:
		if LINE not in (""):
			if LINE[0].strip() == ">":
				SHEET_ID = (LINE.strip()).split(" ")[-1]

			elif LINE[0].strip() not in ("/",):
				LINE_DATA = (LINE.strip()).split(' | ')
				OBJECT_TYPE = int(LINE_DATA[0], 16)

				CLASS_TYPE, FORMAT = FORMATTING[OBJECT_TYPE]
				OBJECT_DATA = []


				for SECTION, PURE_DATA in zip(FORMAT, LINE_DATA[1:]):
					DATA = PURE_DATA.strip(" ")
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
					FINALISED_OBJECT = SCENE(CONSTANTS["VOID_COLOUR"], CONSTANTS["GRAVITY"], CONSTANTS["MULT_AIR_RES"])

				elif CLASS_TYPE in [CUBE_STATIC, TRI, QUAD, NPC_PATH_NODE, LIGHT, INTERACTABLE, CUBE_PATH, SPRITE_STATIC]:
					CURRENT_ID += 1

					if CLASS_TYPE == CUBE_STATIC:
						POINTS = utils.FIND_CUBOID_POINTS(OBJECT_DATA[1], OBJECT_DATA[0])
						NORMALS = utils.FIND_CUBOID_NORMALS(POINTS)

						for TEXTURE in OBJECT_DATA[3]:
							CURRENT_TEXTURE_DATA.append(texture_load.TEXTURE_CACHE_MANAGER(str(TEXTURE)))
						TEXTURE_DATA.append(CURRENT_TEXTURE_DATA)

						FINALISED_OBJECT = CUBE_STATIC(CURRENT_ID, OBJECT_DATA[0], OBJECT_DATA[1], OBJECT_DATA[3], TEXTURE_DATA)

					elif CLASS_TYPE == QUAD:
						POINTS = OBJECT_DATA[:4]
						TEXTURE_DATA.append(texture_load.TEXTURE_CACHE_MANAGER(str(OBJECT_DATA[5][0])))

						FINALISED_OBJECT = QUAD(CURRENT_ID, POINTS, OBJECT_DATA[4], TEXTURE_DATA)

					elif CLASS_TYPE == TRI:
						POINTS = OBJECT_DATA[0:3]
						TEXTURE_DATA.append(texture_load.TEXTURE_CACHE_MANAGER(str(OBJECT_DATA[4][0])))

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
						TEXTURE_DATA.append(texture_load.TEXTURE_CACHE_MANAGER(str(OBJECT_DATA[5][0])))

						FINALISED_OBJECT = INTERACTABLE(CURRENT_ID, POINTS, OBJECT_DATA[4], TEXTURE_DATA, FLAG)

					elif CLASS_TYPE == CUBE_PATH:
						CENTRE = OBJECT_DATA[0]
						DIMENTIONS = OBJECT_DATA[1]
						MOVEMENT = OBJECT_DATA[2]
						SPEED = OBJECT_DATA[3]
						FLAG = OBJECT_DATA[4]
						for TEXTURE in OBJECT_DATA[5]:
							CURRENT_TEXTURE_DATA.append(texture_load.TEXTURE_CACHE_MANAGER(str(TEXTURE)))
						TEXTURE_DATA.append(CURRENT_TEXTURE_DATA)

						FINALISED_OBJECT = CUBE_PATH(CURRENT_ID, CENTRE, DIMENTIONS, TEXTURE_DATA, MOVEMENT, SPEED, FLAG)

					elif CLASS_TYPE == SPRITE_STATIC:
						CENTRE = OBJECT_DATA[0]
						DIMENTIONS = OBJECT_DATA[1]
						TEXTURE_DATA.append(texture_load.TEXTURE_CACHE_MANAGER(str(OBJECT_DATA[2][0])))

						FINALISED_OBJECT = SPRITE_STATIC(CURRENT_ID, CENTRE, DIMENTIONS, TEXTURE_DATA)

					if TEXTURE_DATA != [] and CLASS_TYPE not in [SPRITE_STATIC,]:
						ENV_VAO_DATA = render.OBJECT_VAO_MANAGER(CLASS_TYPE, FINALISED_OBJECT.NORMALS, POINTS, TEXTURE_DATA[0], ENV_VAO_DATA)

					if FINALISED_OBJECT.COLLISION: #If it has collision, add it to the dict physics.py checks.
						STATICS[0][CURRENT_ID] = FINALISED_OBJECT
					else: #If not, it still must be rendered - add to the dict physics.py DOESNT check.
						STATICS[1][CURRENT_ID] = FINALISED_OBJECT

				elif CLASS_TYPE in [PLAYER, SPRITE_STATIC, ITEM, ENEMY, CUBE_PHYSICS]:
					CURRENT_ID += 1

					if CLASS_TYPE == PLAYER:
						CENTRE = OBJECT_DATA[0]
						FINALISED_OBJECT = PLAYER(CURRENT_ID, CENTRE, OBJECT_DATA[1], OBJECT_DATA[2])

					elif CLASS_TYPE == ITEM:
						CENTRE = OBJECT_DATA[0]
						ITEM_TYPE = OBJECT_DATA[2]
						TEXTURE_DATA.append(texture_load.TEXTURE_CACHE_MANAGER(str(OBJECT_DATA[3][0])))

						FINALISED_OBJECT = ITEM(CURRENT_ID, CENTRE, False, TEXTURE_DATA, ITEM_TYPE)

					elif CLASS_TYPE == ENEMY:
						CENTRE = OBJECT_DATA[0]
						ROTATION = OBJECT_DATA[1]
						ENEMY_TYPE = OBJECT_DATA[2]

						FINALISED_OBJECT = ENEMY(CURRENT_ID, CENTRE, ENEMY_TYPE, ROTATION)

					elif CLASS_TYPE == CUBE_PHYSICS:
						DIMENTIONS = OBJECT_DATA[0]
						CENTRE = OBJECT_DATA[1]
						MASS = OBJECT_DATA[2]

						for TEXTURE in OBJECT_DATA[3]:
							CURRENT_TEXTURE_DATA.append(texture_load.TEXTURE_CACHE_MANAGER(str(TEXTURE)))
						TEXTURE_DATA.append(CURRENT_TEXTURE_DATA)

						FINALISED_OBJECT = CUBE_PHYSICS(CURRENT_ID, CENTRE, DIMENTIONS, MASS, VECTOR_3D(0, 0, 0), TEXTURE_DATA)

					KINETICS[CURRENT_ID] = FINALISED_OBJECT



	PHYS_DATA = (KINETICS, STATICS)
	RENDER_DATA = (ENV_VAO_DATA, LIGHTS)
	return RENDER_DATA, PHYS_DATA, SHEET_ID


