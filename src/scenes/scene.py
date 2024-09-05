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
	import sys
	import math as maths
	import numpy as NP

	sys.path.extend(("src", r"src\exct\data", r"src\exct\glsl"))

	#Import other sub-files.
	from exct.utils import *
	from imgs import texture_load
	from exct import log, utils, render

except ImportError:
	log.ERROR("ui.py", "Initial imports failed.")


log.REPORT_IMPORT("scene.py")

global CURRENT_ID #Make global, so any other sub-file or function can use a unique object ID.
PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS
OVERHANG, CURRENT_ID = 1, 0

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
	8:  (INTERACTABLE, ("vect", "vect", "vect", "vect", "str", "texture")), 			#Interactable
	9:  (CUBE_PATH, ("vect", "vect", "vect", "float", "str", "texture")),				#Moving surface (i.e. door)
	10: (ENEMY, ("vect", "vect", "str", "texture")),									#Hostile Enemy
	11: (CUBE_PHYSICS, ("vect", "vect", "float", "texture")), 							#Physics cube
	12: (LIGHT, ("vect", "vect", "rgba", "float", "float", "float", "str")),			#Light object
	13: (NPC_PATH_NODE, ("vect", "hex", "list")),  										#NPC Path node
	14: (LOGIC, ("str", "str")),														#Flag-Logic gate (Not rendered.)
	15: (None, ()),																		#Unused, Placeholder
	#Unavailable in file, but here for the sake of completeness.						--------------------
	16: (PROJECTILE, ("vect", "float", "vect", "str", "texture")),						#Projectile
	17: (EXPLOSION, ("vect", "vect", "float", "float", "texture")),						#Explosion
}



#File loading functions


def LOAD_FILE(FILE_NAME):
	"""
	Loads a file with given name FILE_NAME, returning all data and loading all required textures using load_texture.py
	This info will get given to render.py via main.py, as it contains info for all of the scene's planes and other shapes.
	"""
	try:
		CURRENT_ID = 0
		PLAYER_ID = None

		FILE_NAME_FORMATTED = f"scene-{FILE_NAME}.dat"
		main_dir = os.path.dirname(os.path.abspath(__file__))
		file_path = os.path.join(main_dir, FILE_NAME_FORMATTED)

		#Load the given scene.dat file
		with open(file_path, 'r') as FILE:
			FILE_CONTENTS_RAW = FILE.readlines()
		
		FILE_CONTENTS, RENDER_DATASET = [], []
		FLAG_STATES = {"CONST_ON": True,}
		
		for LINE_RAW in FILE_CONTENTS_RAW:
			FILE_CONTENTS.append(LINE_RAW.strip('\n'))#Remove uneccessary auto-formatting from the file

		#Get the game-data for use here.
		HOSTILES, SUPPLIES, PROJECTILES = utils.GET_GAME_DATA()


		ENV_VAO_DATA = [NP.array([]), NP.array([])]
		KINETICS, STATICS, LIGHTS, LOGIC_GATES = {}, [{}, {}], [], [] #Preparing the arrays and dictionaries for data.
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
										match BOOL:
											case "T":
												BOOLEAN[I] = True
											case "F":
												BOOLEAN[I] = False

									BOOLEAN = BOOLEAN if len(BOOLEAN) > 1 else BOOLEAN[0]

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
					FLAG = None

					if CLASS_TYPE == SCENE:
						#Scene is handled differently to the rest, as it isn't particularly "anywhere" in the scene.
						FINALISED_OBJECT = SCENE(CONSTANTS["VOID_COLOUR"], CONSTANTS["GRAVITY"], CONSTANTS["MULT_AIR_RES"])


					elif CLASS_TYPE == LOGIC:
						#Same story for the LOGIC, as it isn't at any set location.
						GATE_FUNCTION = OBJECT_DATA[0].split(" ")

						match len(GATE_FUNCTION):
							case 3: #For most gates: flagA OR flagB
								FLAG_A, GATE_TYPE, FLAG_B = GATE_FUNCTION

							case 2: #For NOT gates: NOT flagA
								FLAG_B, (GATE_TYPE, FLAG_A) = None, GATE_FUNCTION

							case _:
								raise ValueError(f"Incorrect LOGIC data found for GATE_TYPE: {OBJECT_DATA[0]}")


						OUTPUT_GATE = OBJECT_DATA[1]
						
						FINALISED_OBJECT = LOGIC(FLAG_A, FLAG_B, GATE_TYPE, OUTPUT_GATE)
						LOGIC_GATES.append(FINALISED_OBJECT)




					elif CLASS_TYPE in (CUBE_STATIC, TRI, QUAD, NPC_PATH_NODE, LIGHT, INTERACTABLE, SPRITE_STATIC, TRIGGER,):
						#Static, non-physics based objects.
						CURRENT_ID += 1


						if CLASS_TYPE == CUBE_STATIC:
							POINTS = utils.FIND_CUBOID_POINTS(OBJECT_DATA[1], OBJECT_DATA[0])
							NORMALS = utils.FIND_CUBOID_NORMALS(POINTS)

							for TEXTURE in OBJECT_DATA[3]:
								TEXTURE_DATA.append(texture_load.TEXTURE_CACHE_MANAGER(str(TEXTURE)))


							FINALISED_OBJECT = CUBE_STATIC(CURRENT_ID, OBJECT_DATA[0], OBJECT_DATA[1], OBJECT_DATA[2], TEXTURE_DATA)


						elif CLASS_TYPE == QUAD:
							POINTS = OBJECT_DATA[:4]
							TEXTURE_DATA = texture_load.TEXTURE_CACHE_MANAGER(str(OBJECT_DATA[5][0]))

							FINALISED_OBJECT = QUAD(CURRENT_ID, POINTS, OBJECT_DATA[4], TEXTURE_DATA)


						elif CLASS_TYPE == TRI:
							POINTS = OBJECT_DATA[0:3]
							TEXTURE_DATA = texture_load.TEXTURE_CACHE_MANAGER(str(OBJECT_DATA[4][0]))

							FINALISED_OBJECT = TRI(CURRENT_ID, POINTS, OBJECT_DATA[3], TEXTURE_DATA)


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
							FLAG = OBJECT_DATA[4]
							TEXTURE_DATA = texture_load.TEXTURE_CACHE_MANAGER(str(OBJECT_DATA[5][0]))

							FINALISED_OBJECT = INTERACTABLE(CURRENT_ID, POINTS, OBJECT_DATA[4], TEXTURE_DATA, FLAG)


						elif CLASS_TYPE == SPRITE_STATIC:
							CENTRE = OBJECT_DATA[0]
							DIMENTIONS = OBJECT_DATA[1]
							TEXTURE_DATA = texture_load.TEXTURE_CACHE_MANAGER(str(OBJECT_DATA[2][0]))

							FINALISED_OBJECT = SPRITE_STATIC(CURRENT_ID, CENTRE, DIMENTIONS, TEXTURE_DATA)


						elif CLASS_TYPE == TRIGGER:
							POINTS = utils.FIND_CUBOID_POINTS(OBJECT_DATA[1], OBJECT_DATA[0])
							NORMALS = utils.FIND_CUBOID_NORMALS(POINTS)
							FLAG = OBJECT_DATA[2]

							FINALISED_OBJECT = TRIGGER(CURRENT_ID, OBJECT_DATA[0], OBJECT_DATA[1], FLAG)



						if TEXTURE_DATA != [] and CLASS_TYPE not in [SPRITE_STATIC,]:
							#Add to the VAO data, as long as it isnt a dynamic object like a STATIC_SPRITE.
							ENV_VAO_DATA = render.OBJECT_VAO_MANAGER(FINALISED_OBJECT, ENV_VAO_DATA)



						#If object has a flag, add it to FLAG_STATES
						if FLAG is not None and FLAG not in FLAG_STATES:
							FLAG_STATES[FLAG] = False


						#STATICS for the environmental objects.
						if FINALISED_OBJECT.COLLISION:
							#If it has collision, add it to the dict physics.py checks.
							STATICS[0][CURRENT_ID] = FINALISED_OBJECT
						elif type(FINALISED_OBJECT) not in (LIGHT, NPC_PATH_NODE,):
							#If not, it still must be rendered - add to the dict physics.py DOESNT check.
							STATICS[1][CURRENT_ID] = FINALISED_OBJECT



					elif CLASS_TYPE in (PLAYER, SPRITE_STATIC, ITEM, ENEMY, CUBE_PHYSICS, CUBE_PATH,):
						#Physics based objects.
						CURRENT_ID += 1


						if CLASS_TYPE == PLAYER:
							PLAYER_ID = CURRENT_ID
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


						elif CLASS_TYPE == CUBE_PATH:
							"""
							While not a child-class of PHYSICS_OBJECT, in terms of physics and rendering it must be treated in an odd way.
							CUBE_PATH is not static (unchanging on a frame-by-frame basis) so STATICS[0] & the parent class WORLD_OBJECT would not be ideal
							CUBE_PATH must have physics applied, (unlike STATICS[1] with SPRITE_STATIC), to block the PLAYER or CUBE_PHYSICS classes etc.
							CUBE_PATH may not need its own gravity calculations or be pushed, but PHYSICS_OBJECT is the closest option for its needs.
							It is treated as having infinite mass (therefore cannot be pushed) and skips gravity calculations.
							It has its own specialised use-case, and yet must be handled in the same time that other objects are.
							"""
							CENTRE = OBJECT_DATA[0]
							DIMENTIONS = OBJECT_DATA[1]
							MOVEMENT = OBJECT_DATA[2].NORMALISE()
							MAX_DISTANCE = abs(OBJECT_DATA[2])
							SPEED = OBJECT_DATA[3]
							FLAG = OBJECT_DATA[4]
							for TEXTURE in OBJECT_DATA[5]:
								CURRENT_TEXTURE_DATA.append(texture_load.TEXTURE_CACHE_MANAGER(str(TEXTURE)))

							FINALISED_OBJECT = CUBE_PATH(CURRENT_ID, CENTRE, DIMENTIONS, CURRENT_TEXTURE_DATA, MOVEMENT, SPEED, FLAG, MAX_DISTANCE)


						#Add it to the physics list (Kinetics)
						KINETICS[CURRENT_ID] = FINALISED_OBJECT



		PHYS_DATA = (KINETICS, STATICS)
		RENDER_DATA = (ENV_VAO_DATA, LIGHTS)
		FLAG_DATA = (FLAG_STATES, LOGIC_GATES)
		return RENDER_DATA, PHYS_DATA, SHEET_ID, FLAG_DATA, PLAYER_ID

	except Exception as E:
		log.ERROR("scene.LOAD_FILE", E)
