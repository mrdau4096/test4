"""
[utils.py]
Short for "Utilities.py", this file contains custom maths functions that are used for mostly working with vectors in a more code-oriented method, along with a few general-purpose functions for debugging and other purposes.
Most useful for collision calculations, gravity force application, rendering, debugging and so on.

________________
Imports Modules;
-Math
-NumPy
"""

from exct import log
try: #Module Imports
	#Importing base python modules
	import sys, os, random
	import math as maths
	import numpy as NP
	from pyrr import Matrix44, Vector3, Vector4

	#Stop PyGame from giving that annoying welcome message
	os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

	sys.path.extend(("src", r"src\exct\data", r"src\exct\glsl"))
	import pygame as PG
	from pygame import time, joystick, display, image
	import glm
	import multiprocess as MP

except ImportError:
	log.ERROR("utils.py", "Initial imports failed.")


log.REPORT_IMPORT("utils.py")


#Assorted mathematical values for use elsewhere.
e = maths.e
pi = maths.pi
piDIV2 = pi / 2


#Mathematical functions


def SIGN(VALUE):
	return 1.0 if VALUE > 0.0 else -1.0 if VALUE < 0.0 else 0.0


def CLAMP(VARIABLE, LOWER, UPPER): #Clamps any value between 2 bounds. Used almost exclusively for camera angle.
	return max(LOWER, min(VARIABLE, UPPER))


def JOYSTICK_DEADZONE(JOYSTICK):
	#Applies a deadzone to a GamePad's axis inputs to counteract drift (User can define the offset in prefs.txt)
	L_X = JOYSTICK[0].get_axis(0) if abs(JOYSTICK[0].get_axis(0)) > 0.1 else 0.0
	L_Y = JOYSTICK[0].get_axis(1) if abs(JOYSTICK[0].get_axis(1)) > 0.1 else 0.0
	R_X = JOYSTICK[0].get_axis(2) if abs(JOYSTICK[0].get_axis(2)) > 0.1 else 0.0
	R_Y = JOYSTICK[0].get_axis(3) if abs(JOYSTICK[0].get_axis(3)) > 0.1 else 0.0
	L_STICK = VECTOR_2D(L_X, L_Y)
	R_STICK = VECTOR_2D(R_X, R_Y)
	return [JOYSTICK[0], L_STICK, R_STICK]


def FIND_CUBOID_POINTS(DIMENTIONS, CENTRE):
	#Returns the points for any axis-aligned cuboid. Mostly helpful for initialising, due to physics rotation not allowing for axis-aligned objects often.
	HALF_DIMENTIONS = DIMENTIONS / 2

	OFFSET_MULTIPLIER = 0.0
	#Applies a small, configurable offset if needed.
	OFFSET_X = VECTOR_3D(OFFSET_MULTIPLIER * DIMENTIONS.X,	0.0,								0.0 							)
	OFFSET_Y = VECTOR_3D(0.0,								OFFSET_MULTIPLIER * DIMENTIONS.Y,	0.0 							)
	OFFSET_Z = VECTOR_3D(0.0,								0.0,								OFFSET_MULTIPLIER * DIMENTIONS.Z)
	
	return [
			VECTOR_3D(CENTRE.X - HALF_DIMENTIONS.X, CENTRE.Y - HALF_DIMENTIONS.Y, CENTRE.Z - HALF_DIMENTIONS.Z) + OFFSET_X + OFFSET_Y + OFFSET_Z, #Vertex 0 (min x, min y, min z)
			VECTOR_3D(CENTRE.X + HALF_DIMENTIONS.X, CENTRE.Y - HALF_DIMENTIONS.Y, CENTRE.Z - HALF_DIMENTIONS.Z) - OFFSET_X + OFFSET_Y + OFFSET_Z, #Vertex 1 (max x, min y, min z)
			VECTOR_3D(CENTRE.X - HALF_DIMENTIONS.X, CENTRE.Y - HALF_DIMENTIONS.Y, CENTRE.Z + HALF_DIMENTIONS.Z) + OFFSET_X + OFFSET_Y - OFFSET_Z, #Vertex 2 (min x, min y, max z)
			VECTOR_3D(CENTRE.X + HALF_DIMENTIONS.X, CENTRE.Y - HALF_DIMENTIONS.Y, CENTRE.Z + HALF_DIMENTIONS.Z) - OFFSET_X + OFFSET_Y - OFFSET_Z, #Vertex 3 (max x, min y, max z)
			VECTOR_3D(CENTRE.X - HALF_DIMENTIONS.X, CENTRE.Y + HALF_DIMENTIONS.Y, CENTRE.Z - HALF_DIMENTIONS.Z) + OFFSET_X - OFFSET_Y + OFFSET_Z, #Vertex 4 (min x, max y, min z)
			VECTOR_3D(CENTRE.X + HALF_DIMENTIONS.X, CENTRE.Y + HALF_DIMENTIONS.Y, CENTRE.Z - HALF_DIMENTIONS.Z) - OFFSET_X - OFFSET_Y + OFFSET_Z, #Vertex 5 (max x, max y, min z)
			VECTOR_3D(CENTRE.X - HALF_DIMENTIONS.X, CENTRE.Y + HALF_DIMENTIONS.Y, CENTRE.Z + HALF_DIMENTIONS.Z) + OFFSET_X - OFFSET_Y - OFFSET_Z, #Vertex 6 (min x, max y, max z)
			VECTOR_3D(CENTRE.X + HALF_DIMENTIONS.X, CENTRE.Y + HALF_DIMENTIONS.Y, CENTRE.Z + HALF_DIMENTIONS.Z) - OFFSET_X - OFFSET_Y - OFFSET_Z  #Vertex 7 (max x, max y, max z)
		]


def FIND_CUBOID_NORMALS(POINTS):
	#Find the normals of a cuboid, via its 8 points.
	#This allows the cuboid to be rotated along any axis, and still give the normals.
	VECTOR_R = (POINTS[1] - POINTS[0]).NORMALISE() #Maximum X
	VECTOR_G = (POINTS[4] - POINTS[0]).NORMALISE() #Maximum Y
	VECTOR_B = (POINTS[2] - POINTS[0]).NORMALISE() #Maximum Z

	NORMAL_BOTTOM = VECTOR_G * -1
	NORMAL_SIDE_A = VECTOR_R * -1
	NORMAL_SIDE_B = VECTOR_R
	NORMAL_SIDE_C = VECTOR_B * -1
	NORMAL_SIDE_D = VECTOR_B
	NORMAL_TOP = VECTOR_G

	return [NORMAL_BOTTOM, NORMAL_SIDE_A, NORMAL_SIDE_B, NORMAL_SIDE_C, NORMAL_SIDE_D, NORMAL_TOP]


def FIND_CENTROID(POINTS):
	#Finds the centroid of any number of vertices (Mostly used on quads and tris)
	SUM = VECTOR_3D(0.0, 0.0, 0.0)
	for PT in POINTS:
		SUM += PT
	return SUM / len(POINTS)


def CALC_2D_VECTOR_ANGLE(V1, V2):
	#Calculates the angle between 2 vectors, signed.
	#The signed portion is useful (DET, determinant) because the calculations for what enemy sprite to use also tests for negative angle values.
	V1_2D = VECTOR_2D(V1.X, V1.Z).NORMALISE()
	V2_2D = VECTOR_2D(V2.X, V2.Z).NORMALISE()

	DOT = V1_2D.DOT(V2_2D)
	DET = NP.sign(V1_2D.DET(V2_2D))

	return maths.degrees(DOT * DET)


def ROTATE_POINTS(POINTS, CENTRE, ANGLE):
	#Rotates a list of points around a centre by an angle.
	FINAL = []
	for POINT in POINTS:
		FINAL.append((POINT - CENTRE).ROTATE_BY(ANGLE, CENTRE))
	return FINAL


def FIND_CLOSEST_CUBE_TRIS(CUBE, PHYS_BODY):
	#Finds the closest triangle on a cube to a specific physics body.
	#Unused for now, but may become useful again in the future.
	VERTICES = CUBE.POINTS
	PHYS_BOX = PHYS_BODY.BOUNDING_BOX
	CUBE_CENTRE = (VERTICES[0] + VERTICES[7]) / 2
	FACES = {
		"-Y": ((VERTICES[0], VERTICES[1], VERTICES[2]), (VERTICES[1], VERTICES[3], VERTICES[2])),  # Bottom Face (-Y)
		"-X": ((VERTICES[0], VERTICES[2], VERTICES[4]), (VERTICES[2], VERTICES[6], VERTICES[4])),  # Left Face (-X)
		"+X": ((VERTICES[1], VERTICES[3], VERTICES[5]), (VERTICES[3], VERTICES[7], VERTICES[5])),  # Right Face (+X)
		"+Z": ((VERTICES[0], VERTICES[1], VERTICES[4]), (VERTICES[1], VERTICES[5], VERTICES[4])),  # Front Face (+Z)
		"-Z": ((VERTICES[2], VERTICES[3], VERTICES[6]), (VERTICES[3], VERTICES[7], VERTICES[6])),  # Back Face (-Z)
		"+Y": ((VERTICES[4], VERTICES[5], VERTICES[6]), (VERTICES[5], VERTICES[7], VERTICES[6])),  # Top Face (+Y)
	}

	CLOSEST_DIR, MIN_DIST = None, float("inf")

	DIRECTIONS = ("-Y", "-X", "+X", "+Z", "-Z", "+Y")

	DISTANCES = {
		"+Y": abs(PHYS_BOX.MIN_Y - CUBE.POINTS[0].Y),
		"+X": abs(PHYS_BOX.MIN_X - CUBE.POINTS[0].X),
		"-X": abs(CUBE.POINTS[7].X - PHYS_BOX.MAX_X),
		"+Z": abs(CUBE.POINTS[7].Z - PHYS_BOX.MAX_Z),
		"-Z": abs(PHYS_BOX.MIN_Z - CUBE.POINTS[0].Z),
		"-Y": abs(CUBE.POINTS[7].Y - PHYS_BOX.MAX_Y),
	}

	#Sort the distances to find the closest face(s)
	SORTED_DISTANCES = sorted(DISTANCES.items(), key=lambda ITEM: ITEM[1])
	
	#Handle the case where multiple faces are at similar distances
	MIN_DIST_FACES = [SORTED_DISTANCES[0]]
	for I in range(1, len(SORTED_DISTANCES)):
		if abs(SORTED_DISTANCES[I][1] - SORTED_DISTANCES[0][1]) < 0.01:
			MIN_DIST_FACES.append(SORTED_DISTANCES[I])
		else:
			break
	
	#Select the face based on directional priority (vertical faces last)
	FACE_PRIORITY = {"-Y": 5, "+Y": 6, "-X": 2, "+X": 4, "-Z": 1, "+Z": 3}
	MIN_DIST_FACES.sort(key=lambda ITEM: FACE_PRIORITY[ITEM[0]])
	CLOSEST_DIR = MIN_DIST_FACES[0][0]

	return FACES[CLOSEST_DIR], CUBE.NORMALS[DIRECTIONS.index(CLOSEST_DIR)]



#Other functions


def RESET_PLAYER(PLAYER_INSTANCE):
	PLAYER_INSTANCE.POSITION = CONSTANTS["PLAYER_INITIAL_POS"]
	PLAYER_INSTANCE.LATERAL_VELOCITY = VECTOR_3D(0.0, 0.0, 0.0)
	PLAYER_INSTANCE.ROTATION = VECTOR_3D(0.0, 0.0, 0.0)
	PLAYER_INSTANCE.HEALTH = CONSTANTS["PLAYER_MAX_HEALTH"]
	PLAYER_INSTANCE.ENERGY = CONSTANTS["PLAYER_START_ENERGY"]
	PLAYER_INSTANCE.ALIVE = True
	return PLAYER_INSTANCE


def XOR(A, B):
	#Returns A XOR B, using its decomposition.
	return (A and not B) or (B and not A)


def REMOVE_INDEXED_DUPLICATES(ARRAY):
    SEEN, RESULT = set(), []

    for ENTRY in ARRAY:
        if ENTRY not in SEEN:
            SEEN.add(ENTRY)
            RESULT.append(ENTRY)

    return RESULT


def POINT_IN_RECTANGLE(POINT, RECTANGLE_POSITION, RECTANGLE_DIMENTIONS):
	if (POINT.X < RECTANGLE_POSITION.X or POINT.X > RECTANGLE_POSITION.X+RECTANGLE_DIMENTIONS.X) or (POINT.Y < RECTANGLE_POSITION.Y or POINT.Y > RECTANGLE_POSITION.Y+RECTANGLE_DIMENTIONS.Y):
		return False
	return True


def DIVIDE_DICTS(DICT_A, DICT_B, N):
	def SPLIT_DICT(DICT, N):
		ITEMS = list(DICT.items())
		SEGMENT_SIZE = len(ITEMS) // N
		LEFTOVER = len(ITEMS) % N
		
		START = 0
		for i in range(N):
			END = START + SEGMENT_SIZE + (1 if i < LEFTOVER else 0)
			yield dict(ITEMS[START:END])
			START = END


	A = SPLIT_DICT(DICT_A, N)
	B = SPLIT_DICT(DICT_B, N)

	return [list(zip(A_SEGMENT, B_SEGMENT)) for A_SEGMENT, B_SEGMENT in zip(A, B)]
	

def PRINT_GRID(GRID):
	#Prints the contents of any array, list, grid, dictionary etc in helpful lines. Used for debugging.
	for ENTRY in GRID:
		print(''.join(ENTRY))


#Data retrieval functions


def GET_CUBOID_FACE_INDICES():
	#Gives the face indices of a cube.
	#Must be standardised, as a lot of functions require it in this order.
	return (
		(0, 1, 3, 2),
		(4, 6, 2, 0),
		(5, 7, 3, 1),
		(5, 4, 0, 1),
		(7, 6, 2, 3),
		(4, 5, 7, 6)
	)


def GET_DATA_PATH():
	#Path for the ..\\test4.2.2\\exct\\data\\.. data files.
	return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def SAVE_CONFIGS(DATA):
	PREFERENCES, CONSTANTS = DATA
	try:
		# Handle Prefs.txt
		with open("Prefs.txt", "r") as PREFERENCE_FILE:
			PREFERENCE_DATA = PREFERENCE_FILE.readlines()

		with open("Prefs.txt", "w") as PREFERENCE_FILE:
			for LINE in PREFERENCE_DATA:
				STRIPPED_LINE = LINE.strip()
				if STRIPPED_LINE and STRIPPED_LINE[0] != "/":  # If not a comment or empty line
					KEY, _ = STRIPPED_LINE.split(' = ')
					KEY = KEY.strip()
					if KEY in PREFERENCES:
						# Replace the line with updated value from the dictionary
						NEW_VALUE = PREFERENCES[KEY]
						if isinstance(NEW_VALUE, bool):
							NEW_VALUE = "True" if NEW_VALUE else "False"
						LINE = f"{KEY} = {NEW_VALUE}\n"
				PREFERENCE_FILE.write(LINE)

	except Exception as E:
		log.ERROR("utils.py", E)


	try:
		# Handle config.dat
		DATA_PATH = GET_DATA_PATH()
		CONFIG_FILE_PATH = f"{DATA_PATH}\\config.dat"

		with open(CONFIG_FILE_PATH, "r") as CONFIG_FILE:
			CONFIG_DATA = CONFIG_FILE.readlines()

		with open(CONFIG_FILE_PATH, "w") as CONFIG_FILE:
			for LINE in CONFIG_DATA:
				STRIPPED_LINE = LINE.strip()
				if STRIPPED_LINE and not STRIPPED_LINE.startswith("//"):  #If not a comment or empty line
					KEY, _ = STRIPPED_LINE.split('=')
					KEY = KEY.strip()
					if KEY in CONSTANTS:
						#Replace the line with updated value from the dictionary
						NEW_VALUE = CONSTANTS[KEY]
						if isinstance(NEW_VALUE, bool):
							NEW_VALUE = "True" if NEW_VALUE else "False"
						LINE = f"{KEY} = {NEW_VALUE}\n"
				CONFIG_FILE.write(LINE)

	except Exception as E:
		log.ERROR("utils.py", E)


def GET_CONFIGS():
	#Gets the user-defined config files (prefs.txt and config.dat) and their data.
	try:
		#prefs.txt
		with open("Prefs.txt", "r") as PREFERENCE_FILE:
			PREFERENCE_DATA = PREFERENCE_FILE.readlines()
			PREFERENCES = {}
			
			for LINE in PREFERENCE_DATA:
				if LINE[0].strip() != "" and not LINE.startswith("//"):
					P_LINE_DATA = (LINE.strip()).split('=')
					USER_CHOICE = P_LINE_DATA[1].strip()
					
					try:
						try:
							CHOSEN_DATA = int(USER_CHOICE)
							
							if P_LINE_DATA[0] == "FPS_LIMIT":
								CHOSEN_DATA = int(CLAMP(CHOSEN_DATA, 1, 250))
						
						except:
							CHOSEN_DATA = float(USER_CHOICE)
					
					except ValueError:
						if USER_CHOICE == "True":
							CHOSEN_DATA = True
						
						elif USER_CHOICE == "False":
							CHOSEN_DATA = False
						
						else:
							CHOSEN_DATA = USER_CHOICE

					PREFERENCES[P_LINE_DATA[0].strip()] = CHOSEN_DATA



	except FileNotFoundError as E:
		#If file is not found, log error.
		log.ERROR("utils.py", E)


	try:
		#prefs.txt
		with open(f"{GET_DATA_PATH()}\\config.dat", "r") as CONSTANTS_FILE:
			CONSTANTS_DATA = CONSTANTS_FILE.readlines()
			CONSTANTS = {}
			
			for LINE in CONSTANTS_DATA:
				if LINE[0].strip() not in ("/", ""):
					C_LINE_DATA = (LINE.strip()).split('=')
					USER_CHOICE = C_LINE_DATA[1].strip()

					if USER_CHOICE.startswith("<VECTOR_2D: [") and USER_CHOICE.endswith("]>"):
						DATA = USER_CHOICE.replace("<VECTOR_2D: [", "").replace("]>","").split(",")
						CHOSEN_DATA = VECTOR_2D(*[float(DATUM.strip()) for DATUM in DATA])

					elif USER_CHOICE.startswith("<VECTOR_3D: [") and USER_CHOICE.endswith("]>"):
						DATA = USER_CHOICE.replace("<VECTOR_3D: [", "").replace("]>", "").split(",")
						CHOSEN_DATA = VECTOR_3D(*[float(DATUM.strip()) for DATUM in DATA])

					elif USER_CHOICE.startswith("<RGBA: [") and USER_CHOICE.endswith("]>"):
						DATA = USER_CHOICE.replace("<RGBA: [", "").replace("]>", "").split(",")
						CHOSEN_DATA = RGBA(*[float(DATUM.strip()) for DATUM in DATA])

					else:					
						try:
							try:
								CHOSEN_DATA = int(USER_CHOICE)
							
							except:
								CHOSEN_DATA = float(USER_CHOICE)
						
						except ValueError:
							if USER_CHOICE == "True":
								CHOSEN_DATA = True
							
							elif USER_CHOICE == "False":
								CHOSEN_DATA = False
							
							else:
								CHOSEN_DATA = USER_CHOICE

					CONSTANTS[C_LINE_DATA[0].strip()] = CHOSEN_DATA



	except FileNotFoundError as E:
		#If file is not found, log error.
		log.ERROR("utils.py", E)
	


	return PREFERENCES, CONSTANTS


def GET_GAME_DATA(SHEETS_USED, PROCESS_SHEETS_USED=True):
	#Gets the hostiles.dat, supplies.dat and projectiles.dat file data for use elsewhere.
	DATA_PATH = GET_DATA_PATH()
	HOSTILES, SUPPLIES, PROJECTILES, ITEMS = {}, {}, {}, {}
	SHEET_LIST = []

	HOSTILES_FILE = open(f"{DATA_PATH}\\hostiles.dat", "r")
	SUPPLIES_FILE = open(f"{DATA_PATH}\\supplies.dat", "r")
	PROJECTILES_FILE = open(f"{DATA_PATH}\\projectiles.dat", "r")
	ITEMS_FILE = open(f"{DATA_PATH}\\items.dat", "r")

	HOSTILES_DATA = HOSTILES_FILE.readlines()
	SUPPLIES_DATA = SUPPLIES_FILE.readlines()
	PROJECTILES_DATA = PROJECTILES_FILE.readlines()
	ITEMS_DATA = ITEMS_FILE.readlines()

	HOSTILES_FORMATTING =		("float", "str", "list", "list",						) #Max-Health, Speed, Weapon, Items-to-drop, Textures (Front, FL, BL, Back, BR, FR - Hexagonal)
	SUPPLIES_FORMATTING =		("str", "int",											) #What-to-give, Quantity.
	PROJECTILES_FORMATTING =	("bool", "float",										) #Create-explosion, Strength.
	ITEMS_FORMATTING = 			("str", "int", "bool", "str", "float", "float", "str",	) #Name, Energy per use, Raycast (T/F), Projectile type (if not Raycast), Firing velocity (if not Raycast), Image name.

	
	for HOSTILES_LINE in HOSTILES_DATA:
		PROCESSED_HOSTILES_LINE, EXTRA = PROCESS_LINE(HOSTILES_LINE, HOSTILES_FORMATTING, SHEETS_USED, PROCESS_SHEETS_USED, SHEET_LIST)
		if PROCESSED_HOSTILES_LINE is not None:
			HOSTILES[PROCESSED_HOSTILES_LINE[0].strip()] = PROCESSED_HOSTILES_LINE[1:]
			(SHEETS_USED, SHEET_LIST) = EXTRA
	
	for SUPPLIES_LINE in SUPPLIES_DATA:
		PROCESSED_SUPPLIES_LINE, EXTRA = PROCESS_LINE(SUPPLIES_LINE, SUPPLIES_FORMATTING, SHEETS_USED, PROCESS_SHEETS_USED, SHEET_LIST)
		if PROCESSED_SUPPLIES_LINE is not None:
			SUPPLIES[PROCESSED_SUPPLIES_LINE[0].strip()] = PROCESSED_SUPPLIES_LINE[1:]
			(SHEETS_USED, SHEET_LIST) = EXTRA
	
	for PROJECTILES_LINE in PROJECTILES_DATA:
		PROCESSED_PROJECTILES_LINE, EXTRA = PROCESS_LINE(PROJECTILES_LINE, PROJECTILES_FORMATTING, SHEETS_USED, PROCESS_SHEETS_USED, SHEET_LIST)
		if PROCESSED_PROJECTILES_LINE is not None:
			PROJECTILES[PROCESSED_PROJECTILES_LINE[0].strip()] = PROCESSED_PROJECTILES_LINE[1:]
			(SHEETS_USED, SHEET_LIST) = EXTRA
	
	for ITEM_LINE in ITEMS_DATA:
		PROCESSED_ITEMS_LINE, EXTRA = PROCESS_LINE(ITEM_LINE, ITEMS_FORMATTING, SHEETS_USED, PROCESS_SHEETS_USED, SHEET_LIST)
		if PROCESSED_ITEMS_LINE is not None:
			ITEMS[PROCESSED_ITEMS_LINE[0].strip()] = PROCESSED_ITEMS_LINE[1:]
			(SHEETS_USED, SHEET_LIST) = EXTRA



	#Close the files.
	HOSTILES_FILE.close()
	SUPPLIES_FILE.close()
	PROJECTILES_FILE.close()
	ITEMS_FILE.close()

	SHEET_DATA = SHEETS_USED if PROCESS_SHEETS_USED else (SHEETS_USED, SHEET_LIST)
	return HOSTILES, SUPPLIES, PROJECTILES, ITEMS, SHEET_DATA


def PROCESS_LINE(LINE, FORMATTING, SHEETS_USED, PROCESS_SHEETS_USED, SHEET_LIST):
	#Process a line of a .dat file.
	if LINE != "" and not LINE.startswith("//"):
		DATA = LINE.split("|")
		TYPE = DATA[0]
		MASS = DATA[2]
		TEXTURES = list(DATA[-1].strip().split("/"))

		TEXTURE_LIST = []
		for TEXTURE in TEXTURES:
			TEXTURE_PARTS = TEXTURE.split(">")
			if len(TEXTURE_PARTS) == 2:
				SHEET_NAME, TEXTURE_UV = TEXTURE_PARTS
			else:
				SHEET_NAME, TEXTURE_UV = "base", TEXTURE_PARTS[0]
			
			if not PROCESS_SHEETS_USED and SHEET_NAME not in SHEET_LIST: SHEET_LIST.append(SHEET_NAME)
			TEXTURE_LIST.append((SHEET_NAME, TEXTURE_UV))

		SIZE_RAW = [ENTRY.strip() for ENTRY in DATA[1].split(",")]
		COLLISION_SIZE = VECTOR_3D(SIZE_RAW[0], SIZE_RAW[1], SIZE_RAW[2])
		OUT = [TYPE, COLLISION_SIZE, MASS, TEXTURE_LIST,]

		for FORM, INFO in zip(FORMATTING, DATA[3:]):
			#Match the found data's type to the formatting step provided.
			INFO = INFO.strip()
			match FORM:
				case "vect":
					FILE_VECTOR = [ENTRY.strip() for ENTRY in INFO.split(',')]
					OUT.append(VECTOR_3D(round(float(FILE_VECTOR[0]), 8), round(float(FILE_VECTOR[1]), 8), round(float(FILE_VECTOR[2]), 8)))

				case "bool":
					BOOLEAN = INFO.split(".")
					for I, BOOL in enumerate(BOOLEAN):
						if BOOL.strip().upper() == "T":
							BOOLEAN[I] = True
						elif BOOL.strip().upper() == "F":
							BOOLEAN[I] = False
						else:
							log.ERROR("utils.GET_GAME_DATA", f"Unknown Bool {BOOL}, expected (T, F)")
					if len(BOOLEAN) == 1: BOOLEAN = BOOLEAN[0]
					OUT.append(BOOLEAN)

				case "rgba":
					FILE_VECTOR = [ENTRY.strip() for ENTRY in INFO.split(',')]
					OUT.append(RGBA(round(float(FILE_VECTOR[0]), 8), round(float(FILE_VECTOR[1]), 8), round(float(FILE_VECTOR[2]), 8), round(float(FILE_VECTOR[2]), 8)))

				case "int":
					OUT.append(int(INFO))

				case "float":
					OUT.append(float(INFO))

				case "hex":
					OUT.append(hex(int(INFO.strip())))

				case "list":
					OUT.append([ENTRY.strip() for ENTRY in INFO.split(":")])

				case "str":
					OUT.append(INFO.strip())

		
		return OUT, (SHEETS_USED, SHEET_LIST)
	return None, (None, None)





"""
Custom Classes, for objects and datatypes {O.O.P.};
- Static, Environmental objects // [WORLD_OBJECT]'s children classes.
- Physics-based objects // [PHYSICS_OBJECT]'s children classes.
- Bounding boxes // instances of [BOUNDING_BOX].
- Rays for raycasting // instances of [RAY].
- Logic gates for flag-state manipulation // instances of [LOGIC].
- Scene-wide data // instances of [SCENE].
- RGBA format and functions for colour manipulation // instances of [RGBA].
- VECTOR_2D/VECTOR_3D and their related mathematical functions // instances of [VECTOR_2D/VECTOR_3D].
"""
#Parent Classes



class WORLD_OBJECT:
	#Static objects (Environmental)
	def __init__(self, OBJECT_ID, POSITION, COLLISION, TEXTURE_INFO=None, NORMALS=None, BOUNDING_BOX=None):
		self.POSITION = POSITION
		self.COLLISION = bool(COLLISION)

		if NORMALS is not None:
			FINAL_NORMALS_LIST = []
			for NORMAL in NORMALS:
				FINAL_NORMALS_LIST.append(NORMAL.NORMALISE())
			self.NORMALS = tuple(FINAL_NORMALS_LIST)

		if OBJECT_ID is not None: self.ID = int(OBJECT_ID)
		if TEXTURE_INFO is not None: self.TEXTURE_INFO = TEXTURE_INFO
		if COLLISION: self.BOUNDING_BOX = BOUNDING_BOX


class PHYSICS_OBJECT:
	#Objects with physics calculations (Gravity etc)
	def __init__(self, OBJECT_ID, POSITION, ROTATION, NORMALS, BOUNDING_BOX, MASS, TEXTURE_INFO, LATERAL_VELOCITY=None):
		self.POSITION = POSITION
		self.MASS = float(MASS)
		self.COLLISION = True
		self.BOUNDING_BOX = BOUNDING_BOX
		self.NORMALS = tuple(NORMALS)
		self.ID = int(OBJECT_ID)
		self.ROTATIONAL_VELOCITY = VECTOR_3D(0.0, 0.0, 0.0)
		self.PREVIOUS_COLLISION = False
		if LATERAL_VELOCITY is not None: self.LATERAL_VELOCITY = VECTOR_3D(*LATERAL_VELOCITY)
		else: self.LATERAL_VELOCITY = VECTOR_3D(0.0, 0.0, 0.0)
		self.TEXTURE_INFO = TEXTURE_INFO if TEXTURE_INFO is not None else None
		if ROTATION is None: self.ROTATION = VECTOR_3D(0.0, 0.0, 0.0)
		else: self.ROTATION = ROTATION.RADIANS()


class BOUNDING_BOX:
	#Bounding boxes for the physics system
	def __init__(self, POSITION, OBJECT_POINTS, OFFSET=1.0):		
		self.MIN_X = min(POINT.X for POINT in OBJECT_POINTS) - OFFSET
		self.MAX_X = max(POINT.X for POINT in OBJECT_POINTS) + OFFSET
		self.MIN_Y = min(POINT.Y for POINT in OBJECT_POINTS) - OFFSET
		self.MAX_Y = max(POINT.Y for POINT in OBJECT_POINTS) + OFFSET
		self.MIN_Z = min(POINT.Z for POINT in OBJECT_POINTS) - OFFSET
		self.MAX_Z = max(POINT.Z for POINT in OBJECT_POINTS) + OFFSET
		
		BOX_POINTS = FIND_CUBOID_POINTS(VECTOR_3D(self.MAX_X-self.MIN_X, self.MAX_Y-self.MIN_Y, self.MAX_Z-self.MIN_Z), POSITION)

		self.POSITION = VECTOR_3D(*list(POSITION))
		self.NORMALS = NORMALS = FIND_CUBOID_NORMALS(BOX_POINTS)
		self.POINTS = BOX_POINTS

	def __repr__(self):
		return f"<BOUNDING_BOX [POSITION: {self.POSITION} // X: {self.MIN_X, self.MAX_X} // Y: {self.MIN_Y, self.MAX_Y} // Z: {self.MIN_Z, self.MAX_Z}]>"

	def UPDATE(self, NEW_POSITION, NEW_POINTS, OFFSET=1.0): #Updates original data using __init__() without creating a new AABB Object
		self.__init__(NEW_POSITION, NEW_POINTS, OFFSET=OFFSET)
		return self


class RAY:
	#Ray for raycasting calculations
	def __init__(self, START_POINT, RAY_TYPE, RENDER_START_POINT=None, DIRECTION_VECTOR=None, ANGLE=None, MAX_DISTANCE=64.0, OWNER=None):
		#Optionally direction vector or angle.
		self.START_POINT = START_POINT
		self.RAY_TYPE = RAY_TYPE
		self.LIFETIME = CONSTANTS["MAX_RAY_PERSIST_SECONDS"] #Ray gets removed after a certain number of frames, if rendered.
		self.OWNER = OWNER


		if ANGLE is not None:
			#Invert Y (pitch)
			#Subtract [piDIV2 // 90*] from X (yaw)
			DIRECTION_VECTOR = VECTOR_3D(
				maths.cos(-ANGLE.Y) * maths.sin(ANGLE.X - piDIV2),
				maths.sin(-ANGLE.Y),
				-maths.cos(-ANGLE.Y) * maths.cos(ANGLE.X - piDIV2)
			)

		elif DIRECTION_VECTOR is None:
			raise ValueError("RAY must have either a DIRECTION_VECTOR or an ANGLE.")
			#If handled, set end point to start point.
			DIRECTION_VECTOR = VECTOR_3D(0.0, 0.0, 0.0)

		self.ANGLE = ANGLE
		self.DIRECTION_VECTOR = DIRECTION_VECTOR.NORMALISE()

		self.RENDER_START_POINT = RENDER_START_POINT if RENDER_START_POINT is not None else START_POINT



		self.MAX_DISTANCE = MAX_DISTANCE
		self.END_POINT = START_POINT + (MAX_DISTANCE * DIRECTION_VECTOR)

		BOUNDING_BOX_OBJ = BOUNDING_BOX(FIND_CENTROID((self.START_POINT, self.END_POINT)), (self.START_POINT, self.END_POINT))
		self.BOUNDING_BOX = BOUNDING_BOX_OBJ


	def __repr__(self):
		return f"<RAY [RAY_TYPE: {self.RAY_TYPE} // START_POINT: {self.START_POINT} // END_POINT: {self.END_POINT} // MAX_DISTANCE: {self.MAX_DISTANCE}]"


	def CHECK_COLLISION(self, OTHER, BOUNDING_BOX_COLLISION, RAY_TRI_INTERSECTION):
		#Checks if a ray and another object are colliding.
		STATIC_TYPE = type(OTHER)
		VERTICES = OTHER.POINTS


		if BOUNDING_BOX_COLLISION(self.BOUNDING_BOX, OTHER.BOUNDING_BOX):
			if STATIC_TYPE in (CUBE_STATIC, CUBE_PHYSICS, CUBE_PATH, ENEMY, PLAYER,): #Cube-like objects
				for FACE in OTHER.FACES:
					TRIANGLES = (
						(VERTICES[FACE[0]], VERTICES[FACE[1]], VERTICES[FACE[2]]),
						(VERTICES[FACE[0]], VERTICES[FACE[3]], VERTICES[FACE[2]])
					)

					for TRIANGLE in TRIANGLES:
						COLLISION = RAY_TRI_INTERSECTION(self, TRIANGLE)
						if COLLISION is not None:
							return COLLISION
			

			elif STATIC_TYPE in (QUAD, INTERACTABLE,): #Quad-like Objects
				TRIANGLES = (
					(VERTICES[0], VERTICES[1], VERTICES[2]),
					(VERTICES[0], VERTICES[3], VERTICES[2])
				)

				for I, TRIANGLE in enumerate(TRIANGLES):
					COLLISION = RAY_TRI_INTERSECTION(self, TRIANGLE)
					if COLLISION is not None:
						return COLLISION
			

			elif STATIC_TYPE == TRI: #Only Tris are singular triangles.
				TRIANGLE = (VERTICES[0], VERTICES[1], VERTICES[2])
				return RAY_TRI_INTERSECTION(self, TRIANGLE)
		

		#If no collision found, return False.
		return float("inf")





	def CHECK_FOR_INTERSECTS(self, BOUNDING_BOX_COLLISION, RAY_TRI_INTERSECTION, PHYS_DATA):
		def THREAD_RAY_CHECK(RAY, OBJECT_DATASET, BOUNDING_BOX_COLLISION, RAY_TRI_INTERSECTION):
			KINETICS, STATICS = OBJECT_DATASET
			RAY_COLLISION_DISTANCES = []
			COLLIDED_OBJECTS = {}
			for STATIC_ID, STATIC in STATICS.items():
				COLLISION_DATA = RAY.CHECK_COLLISION(STATIC, BOUNDING_BOX_COLLISION, RAY_TRI_INTERSECTION)
				
				if COLLISION_DATA is not None:
					RAY_COLLISION_DISTANCES.append(COLLISION_DATA)
					COLLIDED_OBJECTS[COLLISION_DATA] = STATIC
			
			for KINETIC_ID, KINETIC in KINETICS.items():
				if KINETIC_ID == self.OWNER: continue
				COLLISION_DATA = RAY.CHECK_COLLISION(KINETIC, BOUNDING_BOX_COLLISION, RAY_TRI_INTERSECTION)
				
				if COLLISION_DATA is not None:
					RAY_COLLISION_DISTANCES.append(COLLISION_DATA)
					COLLIDED_OBJECTS[COLLISION_DATA] = KINETIC


			SHORTEST_DISTANCE = min(RAY_COLLISION_DISTANCES)
			if SHORTEST_DISTANCE is not None:
				CLOSEST_OBJECT = COLLIDED_OBJECTS[SHORTEST_DISTANCE] if (SHORTEST_DISTANCE <= self.MAX_DISTANCE) else None

				return CLOSEST_OBJECT, SHORTEST_DISTANCE

			else:
				return None, float('inf')



		KINETICS, STATICS = PHYS_DATA

		RESULTING_COLLISION, RESULTING_DISTANCE = THREAD_RAY_CHECK(self, (KINETICS, STATICS[0]), BOUNDING_BOX_COLLISION, RAY_TRI_INTERSECTION)

		if RESULTING_DISTANCE <= self.MAX_DISTANCE:
			self.END_POINT = self.START_POINT + (self.DIRECTION_VECTOR * RESULTING_DISTANCE)
			return RESULTING_COLLISION

		else:
			return None



	def RAY_VISUAL(self, WIDTH=0.025):
		#Creates a ray visual, when called.
		#Looks like 2 long triangles between their widest end at the start location and final point at the end point.

		VERTICAL_OFFSET = VECTOR_3D(0.0, WIDTH, 0.0)
		HORIZONTAL_OFFSET = VECTOR_3D(
			1 * maths.sin(self.ANGLE.X),
			0,
			-1 * maths.cos(self.ANGLE.X)
		) * WIDTH

		TRIANGLE_A = (
			self.END_POINT,
			self.RENDER_START_POINT + VERTICAL_OFFSET,
			self.RENDER_START_POINT - VERTICAL_OFFSET
		)

		TRIANGLE_B = (
			self.END_POINT,
			self.RENDER_START_POINT + HORIZONTAL_OFFSET,
			self.RENDER_START_POINT - HORIZONTAL_OFFSET
		)

		NORMAL = VECTOR_3D(0.0, 0.0, 0.0)
		self.NORMALS = (NORMAL, NORMAL)

		return (TRIANGLE_A, TRIANGLE_B)


class LOGIC:
	#Logic gates for manipulating the values of flag-states.
	def __init__(self, INPUT_A, INPUT_B, TYPE, OUTPUT_FLAG):
		self.GATE_TYPE = TYPE
		self.INPUT_A = INPUT_A
		self.INPUT_B = INPUT_B
		self.OUTPUT_FLAG = OUTPUT_FLAG

		self.STATE = False #Only used for [LATCH, SWITCH, PULSE] but good to give all this value.


	def UPDATE(self, FLAG_STATES):
		#Updates the LOGIC gate based on its type and the current inputs.
		VALUE_A = FLAG_STATES[self.INPUT_A]
		VALUE_B = FLAG_STATES[self.INPUT_B] if self.INPUT_B is not None else None
		#If not applicable (e.g. NOT gate) then VALUE_B is None.

		match self.GATE_TYPE:
			case "AND": #AND
				RESULT = VALUE_A and VALUE_B

			case "OR": #OR
				RESULT = VALUE_A or VALUE_B

			case "NOT": #NOT
				RESULT = not VALUE_A

			case "NAND": #Not AND
				RESULT = not (VALUE_A and VALUE_B)

			case "NOR": #Not OR
				RESULT = not (VALUE_A or VALUE_B)

			case "XOR": #eXclusive OR
				RESULT = (VALUE_A and (not VALUE_B)) or ((not VALUE_A) and VALUE_B)

			case "LATCH": #JK flip-flop behavior: A sets, B resets the state
				if VALUE_A and not VALUE_B:
					self.STATE = True
				elif VALUE_B and not VALUE_A:
					self.STATE = False

				RESULT = self.STATE

			case "SWITCH": #Toggles between 2 states with 1 input
				if VALUE_A:
					self.STATE = not self.STATE
				RESULT = self.STATE

			case "PULSE": #Outputs a singular frame if A is true
				if VALUE_A and not self.STATE:
					RESULT = True
					self.STATE = True
				elif not VALUE_A and self.STATE:
					self.STATE = False
					RESULT = False
				else:
					RESULT = False

			case _:
				raise TypeError(f"Invalid flag-logic GATE_TYPE; [{self.GATE_TYPE}]")


		FLAG_STATES[self.OUTPUT_FLAG] = RESULT
		return FLAG_STATES

	def __repr__(self):
		LOGIC_TYPE = f"{self.INPUT_A} {self.GATE_TYPE} {self.INPUT_B}" if self.INPUT_B is not None else f"{self.GATE_TYPE} {self.INPUT_A}"
		return f"<LOGIC [{LOGIC_TYPE} -> {self.OUTPUT_FLAG})]>"


class NPC_PATH_NODE:
	#Pathing node for ENEMY class.
	def __init__(self, FLAG, POSITION, CONNECTIONS):
		self.FLAG = FLAG
		self.POSITION = POSITION
		self.CONNECTIONS = CONNECTIONS
		self.PREDECESSOR = None

	def __repr__(self):
		return f"<NPC_PATH_NODE: [FLAG: {self.FLAG}, POSITION: {self.POSITION}, CONNECTIONS: {self.CONNECTIONS}, PREDECESSOR: {self.PREDECESSOR}]>"


class SCENE:
	#Scene object for scene-wide data like gravity values. (Likely deprecated.)
	def __init__(self, VOID_COLOUR, GRAVITY, AIR_RES_MULT):
		self.VOID = RGBA(VOID_COLOUR)
		self.GRAVITY = GRAVITY
		self.AIR_RES_MULT = AIR_RES_MULT

	def __repr__(self):
		return f"<SCENE: [VOID_COLOUR: {self.VOID} // GRAVITY: {self.GRAVITY} // AIR_RES_MULT: {AIR_RES_MULT}]>"



class UI_ELEMENT():
	def __init__(self, POSITION, DIMENTIONS, OFF_COLOUR, ON_COLOUR, OFF_TEXT=None, ON_TEXT=None, TEXT_COLOUR=None, START_STATE=None):
		self.TL_POSITION = POSITION
		self.BR_POSITION = POSITION + DIMENTIONS
		self.DIMENTIONS = DIMENTIONS
		self.OFF_COLOUR, self.ON_COLOUR = OFF_COLOUR, ON_COLOUR
		self.OFF_TEXT, self.ON_TEXT = OFF_TEXT, ON_TEXT
		self.STATE = False if START_STATE is None else START_STATE
		self.PRESSED_PREV_FRAME = False
		self.TEXT_COLOUR = TEXT_COLOUR if TEXT_COLOUR is not None else RGBA(255, 255, 255, 255)

	def DRAW(self, UI_SURFACE):
		BUTTON_RECT = PG.Rect(self.TL_POSITION.X, self.TL_POSITION.Y, self.DIMENTIONS.X, self.DIMENTIONS.Y)
		CURRENT_TEXT = self.ON_TEXT if self.STATE else self.OFF_TEXT
		CURRENT_TEXT = CURRENT_TEXT if CURRENT_TEXT is not None else ""
		CURRENT_COLOUR = list(self.ON_COLOUR) if self.STATE else list(self.OFF_COLOUR,)
		PG.draw.rect(UI_SURFACE, CURRENT_COLOUR, BUTTON_RECT)
		PG.draw.rect(UI_SURFACE, (229, 172, 43, 255), BUTTON_RECT, width=2)
		self.DRAW_TEXT(UI_SURFACE, CURRENT_TEXT, ((self.TL_POSITION.X + 0.5*self.DIMENTIONS.X) - 6*len(CURRENT_TEXT), self.TL_POSITION.Y+(self.DIMENTIONS.Y/4)), self.DIMENTIONS.Y/2, self.TEXT_COLOUR)

	def DRAW_TEXT(self, UI_SURFACE, TEXT, POSITION, FONT_SIZE, COLOUR):
		FONT = PG.font.Font('src\\exct\\fonts\\PressStart2P-Regular.ttf', round(FONT_SIZE))
		TEXT_SURFACE = FONT.render(str(TEXT), True, list(COLOUR))
		UI_SURFACE.blit(TEXT_SURFACE, POSITION)


class SLIDER:
	def __init__(self, POSITION, DIMENTIONS, MAX_SLIDE, COLOUR, ATTACHED_OBJECTS=None, VERTICAL=False):
		self.START_POSITION = POSITION
		self.CURRENT_SLIDER_POS = POSITION
		self.DIMENTIONS = DIMENTIONS
		self.MAX_SLIDE = MAX_SLIDE
		self.CURRENT_SLIDE = 0
		self.COLOUR = COLOUR
		self.VERTICAL = VERTICAL #If False, then Horizontal.
		self.SLIDE_RATIO = 0
		self.ATTACHED_OBJECTS = ATTACHED_OBJECTS

	def SLIDE_CHECK(self, MOUSE_POS, MOUSE_MOVE, KEY_STATES):
		if POINT_IN_RECTANGLE(MOUSE_POS, self.CURRENT_SLIDER_POS, self.DIMENTIONS) and KEY_STATES[1]:
			self.CURRENT_SLIDE += MOUSE_MOVE[1] if self.VERTICAL else MOUSE_MOVE[0]
			self.CURRENT_SLIDE = max(0, min(self.CURRENT_SLIDE, self.MAX_SLIDE))
			
			if self.CURRENT_SLIDE > 0 and self.CURRENT_SLIDE < self.MAX_SLIDE:
				if self.VERTICAL:
					self.CURRENT_SLIDER_POS = (self.CURRENT_SLIDER_POS[0], self.START_POSITION[1] + self.CURRENT_SLIDE)
				else:
					(self.START_POSITION[0] + self.CURRENT_SLIDE, self.CURRENT_SLIDER_POS[1])

				self.SLIDE_RATIO = self.CURRENT_SLIDE/self.MAX_SLIDE

	def DRAW(self):
		SLIDER_RECT = PG.Rect(self.CURRENT_SLIDER_POS, self.DIMENTIONS)
		PG.draw.rect(SCREEN, self.COLOUR, SLIDER_RECT)



class BUTTON(UI_ELEMENT):
	def __init__(self, POSITION, DIMENTIONS, FUNCTION, OFF_COLOUR, ON_COLOUR, OFF_TEXT, ON_TEXT, FUNCTION_VALUES=None, TOGGLE=False, TEXT_COLOUR=None, START_STATE=None):
		super().__init__(POSITION, DIMENTIONS, OFF_COLOUR, ON_COLOUR, OFF_TEXT=OFF_TEXT, ON_TEXT=ON_TEXT, TEXT_COLOUR=TEXT_COLOUR, START_STATE=START_STATE)

		self.FUNCTION = FUNCTION
		self.FUNCTION_VALUES = FUNCTION_VALUES
		self.TOGGLE = TOGGLE


	def __repr__(self):
		return f"<BUTTON [POSITION: {self.TL_POSITION}, DIMENTIONS: {self.DIMENTIONS}, FUNCTION: {self.FUNCTION}, TOGGLE: {self.TOGGLE}]>"


	def EVALUATE_STATE(self, MOUSE_POSITION, KEY_STATES, MOUSEBUTTONUP):
		if KEY_STATES[1] and POINT_IN_RECTANGLE(MOUSE_POSITION, self.TL_POSITION, self.DIMENTIONS):
			
			if self.TOGGLE and not self.PRESSED_PREV_FRAME:
				self.PRESSED_PREV_FRAME = True
				self.STATE = not self.STATE
			
			elif not self.TOGGLE:
				self.STATE = True


		elif not self.TOGGLE:
			self.STATE = False

		elif self.PRESSED_PREV_FRAME:
			self.PRESSED_PREV_FRAME = False


		if self.STATE and MOUSEBUTTONUP or (self.TOGGLE == False and MOUSEBUTTONUP and POINT_IN_RECTANGLE(MOUSE_POSITION, self.TL_POSITION, self.DIMENTIONS)):
			if "PROCESS_UI_STATE" in str(self.FUNCTION): #For recursive UI pages in menus (Such as options)
				RESULT = self.FUNCTION(self.FUNCTION_VALUES[0], self.FUNCTION_VALUES[1], self.FUNCTION_VALUES[2], self.FUNCTION_VALUES[3], self.FUNCTION_VALUES[4])
			elif "UPDATE_CONFIG" in str(self.FUNCTION): #For editing values
				RESULT = self.FUNCTION(self.FUNCTION_VALUES[0], self.FUNCTION_VALUES[1], self)
			else:
				RESULT = self.FUNCTION() if self.FUNCTION_VALUES is None else self.FUNCTION(self.FUNCTION_VALUES)
			if RESULT is not None:
				return RESULT

		return None





"""
Static Objects
> TRI (Triangles)
> QUAD (quads/planes)
> CUBE_STATIC (A static cube)
> SPRITE_STATIC (A sprite for decoration, non-collideable)
> CUBE_PATH (For moving doors/walls)
> TRIGGER (Bounding box that gives a flag value when stood inside of by player)
> INTERACTABLE (Quad that gives a flag value when player interacts with it)
> LIGHT (Light that casts shadows)
> EXPLOSION (Explosion that harms PLAYER/ENEMY)
"""



class TRI(WORLD_OBJECT):
	#Static triangle object.
	def __init__(self, ID, VERTICES, COLLISION, TEXTURE_COORDINATES):
		CENTROID = FIND_CENTROID(VERTICES)
		NORMAL = ((VERTICES[0] - VERTICES[2]).CROSS(VERTICES[1] - VERTICES[2]),)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(CENTROID, VERTICES)
		super().__init__(ID, CENTROID, COLLISION, TEXTURE_INFO=TEXTURE_COORDINATES, NORMALS=NORMAL, BOUNDING_BOX=BOUNDING_BOX_OBJ)
		self.POINTS = VERTICES

	def __repr__(self):
		if self.COLLISION:
			return f"<TRI: [CENTROID: {self.POSITION} // NORMAL: {self.NORMALS} // COLLISION: {self.COLLISION} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS}]>"
		else:
			return f"<TRI: [CENTROID: {self.POSITION} // COLLISION: {self.COLLISION} // VERTICES: {self.POINTS}]>"


class QUAD(WORLD_OBJECT):
	#Static quad/plane object.
	def __init__(self, ID, VERTICES, COLLISION, TEXTURE_COORDINATES):
		CENTROID = FIND_CENTROID(VERTICES)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(CENTROID, VERTICES)
		SIDE_A = VERTICES[1] - VERTICES[0]
		SIDE_B = VERTICES[2] - VERTICES[0]
		SIDE_C = VERTICES[1] - VERTICES[3]
		SIDE_D = VERTICES[2] - VERTICES[3]
		NORMALS = (SIDE_A.CROSS(SIDE_B), SIDE_C.CROSS(SIDE_D))
		super().__init__(ID, CENTROID, COLLISION, TEXTURE_INFO=TEXTURE_COORDINATES, NORMALS=NORMALS, BOUNDING_BOX=BOUNDING_BOX_OBJ)

		self.POINTS = VERTICES

	def __repr__(self):
		return f"<QUAD_STATIC: [CENTROID: {self.POSITION} // NORMALS: {self.NORMALS} // COLLISION: {self.COLLISION} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS}]>"


class CUBE_STATIC(WORLD_OBJECT):
	#Static cube object.
	def __init__(self, ID, POSITION, DIMENTIONS, COLLISION, TEXTURE_INFO, TEXTURE_SHEETS_USED):
		POINTS = FIND_CUBOID_POINTS(DIMENTIONS, POSITION)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)
		super().__init__(ID, POSITION, COLLISION, TEXTURE_INFO=TEXTURE_INFO, NORMALS=NORMALS, BOUNDING_BOX=BOUNDING_BOX_OBJ)
		self.TEXTURE_SHEETS_USED = TEXTURE_SHEETS_USED

		FACES = GET_CUBOID_FACE_INDICES()
		self.FACES = FACES
		

		self.DIMENTIONS = DIMENTIONS
		self.POINTS = tuple(POINTS)

	def __repr__(self):
		return f"<CUBE_STATIC: [POSITION: {self.POSITION} // DIMENTIONS: {self.DIMENTIONS} // COLLISION: {self.COLLISION} // NORMALS: {self.NORMALS} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS}]>"


class SPRITE_STATIC(WORLD_OBJECT):
	#Static decorational sprite
	def __init__(self, ID, POSITION, COLLISION_DIMENTIONS, TEXTURE_COORDINATES, TEXTURE_SHEETS_USED):
		POINTS = FIND_CUBOID_POINTS(COLLISION_DIMENTIONS, POSITION)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		super().__init__(ID, POSITION, False, TEXTURE_INFO=TEXTURE_COORDINATES, NORMALS=NORMALS, BOUNDING_BOX=BOUNDING_BOX_OBJ)
		self.TEXTURE_SHEETS_USED = TEXTURE_SHEETS_USED

		AVG_X = (COLLISION_DIMENTIONS.X + COLLISION_DIMENTIONS.Z) / 2
		self.DIMENTIONS_2D = VECTOR_2D(AVG_X, COLLISION_DIMENTIONS.Y)

	def __repr__(self):
		return f"<SPRITE_STATIC: [POSITION: {self.POSITION} // NORMALS: {self.NORMALS} // COLLISION: {self.COLLISION} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS}]>"


class CUBE_PATH(WORLD_OBJECT):
	#Used for moving doors/walls.
	def __init__(self, ID, POSITION, DIMENTIONS, TEXTURE_DATA, MOVEMENT_VECTOR, SPEED, FLAG, MAX_DISTANCE, TEXTURE_SHEETS_USED):
		self.POINTS = FIND_CUBOID_POINTS(DIMENTIONS, POSITION)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, self.POINTS)
		NORMALS = FIND_CUBOID_NORMALS(self.POINTS)
		super().__init__(ID, POSITION, True, TEXTURE_INFO=TEXTURE_DATA, NORMALS=NORMALS, BOUNDING_BOX=BOUNDING_BOX_OBJ)
		self.TEXTURE_SHEETS_USED = TEXTURE_SHEETS_USED
		
		FACES = GET_CUBOID_FACE_INDICES()
		self.FACES = FACES
		
		self.DIMENTIONS = DIMENTIONS
		self.MAX_DISTANCE = MAX_DISTANCE
		self.MOVEMENT = MOVEMENT_VECTOR
		self.SPEED = CLAMP(SPEED, 0.0, MAX_DISTANCE) / CONSTANTS["PHYSICS_ITERATIONS"]
		self.FLAG = FLAG
		self.TRIGGERED = False
		self.CURRENT_DISTANCE = 0.0


	def ADVANCE(self, FLAG_STATES):
		#Moves the cube forward by its speed in a frame, if that doesnt go past its max distance.
		STATE = FLAG_STATES[self.FLAG]


		if STATE and self.CURRENT_DISTANCE < self.MAX_DISTANCE:
			#If moving forward and not at max distance
			MOVE_DIST = min(self.SPEED, self.MAX_DISTANCE - self.CURRENT_DISTANCE)

		elif not STATE and self.CURRENT_DISTANCE > 0:
			#if Moving backward and not at 0 distance
			MOVE_DIST = -min(self.SPEED, self.CURRENT_DISTANCE)

		else:
			MOVE_DIST = 0.0



		self.CURRENT_DISTANCE = CLAMP(self.CURRENT_DISTANCE + MOVE_DIST, 0.0, self.MAX_DISTANCE)
		self.POSITION += self.MOVEMENT * MOVE_DIST


		POINTS = FIND_CUBOID_POINTS(self.DIMENTIONS, self.POSITION)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(self.POSITION, POINTS)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		super().__init__(self.ID, self.POSITION, True, TEXTURE_INFO=self.TEXTURE_INFO, NORMALS=self.NORMALS, BOUNDING_BOX=BOUNDING_BOX_OBJ)
		return self


	def __repr__(self):
		return f"<CUBE_PATH: [CENTROID: {self.POSITION} // NORMALS: {self.NORMALS} // COLLISION: {self.COLLISION} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS} // MOTION: {self.MOVEMENT} // SPEED: {self.SPEED} // FLAG: {self.FLAG}]>"


class TRIGGER(WORLD_OBJECT):
	#Sets its flag to True when collided with. Only while player is inside, but there is a LOGIC type for retaining the value.
	def __init__(self, ID, POSITION, DIMENTIONS, FLAG):
		POINTS = FIND_CUBOID_POINTS(DIMENTIONS, POSITION)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)
		super().__init__(ID, POSITION, True, BOUNDING_BOX=BOUNDING_BOX_OBJ)
		
		FACES = GET_CUBOID_FACE_INDICES()
		self.FACES = FACES
		

		self.DIMENTIONS = DIMENTIONS
		self.POINTS = tuple(POINTS)
		self.FLAG = FLAG
		self.TRIGGERED = False

	def __repr__(self):
		return f"<TRIGGER: [POSITION: {self.POSITION} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS} // FLAG: {self.FLAG}]>"


class INTERACTABLE(WORLD_OBJECT):
	#Sets its flag state to True when interacted with. Only while held, but there is a LOGIC type for retaining the value.
	def __init__(self, ID, VERTICES, COLLISION, TEXTURE_COORDINATES, FLAG):
		CENTROID = FIND_CENTROID(VERTICES)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(CENTROID, VERTICES)
		SIDE_A = VERTICES[1] - VERTICES[0]
		SIDE_B = VERTICES[2] - VERTICES[0]
		SIDE_C = VERTICES[1] - VERTICES[3]
		SIDE_D = VERTICES[2] - VERTICES[3]
		NORMALS = (SIDE_A.CROSS(SIDE_B), SIDE_C.CROSS(SIDE_D))
		super().__init__(ID, CENTROID, COLLISION, TEXTURE_INFO=TEXTURE_COORDINATES, NORMALS=NORMALS, BOUNDING_BOX=BOUNDING_BOX_OBJ)

		self.POINTS = VERTICES
		
		self.FLAG = FLAG
		self.TRIGGERED = False

	def __repr__(self):
		return f"<INTERACTABLE: [CENTROID: {self.POSITION} // NORMALS: {self.NORMALS} // COLLISION: {self.COLLISION} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS}]>"


class LIGHT(WORLD_OBJECT):
	#Casts shadows, emits light.
	def __init__(self, ID, POSITION, RAW_LOOK_AT, FOV, COLOUR, INTENSITY, MAX_DISTANCE, FLAG):
		super().__init__(ID, POSITION, False)

		self.LOOK_AT = POSITION + (RAW_LOOK_AT - POSITION).NORMALISE()
		self.FOV = FOV
		self.COLOUR = COLOUR
		self.INTENSITY = float(INTENSITY)
		self.MIN_DISTANCE = MAX_DISTANCE / 100
		self.MAX_DISTANCE = float(MAX_DISTANCE)
		self.SPACE_MATRIX = None #Will be populated later, when calculating shadow mapping.
		self.SHADOW_MAP = None #Same here.
		self.FLAG = FLAG

	def __repr__(self):
		return f"<LIGHT: [POSITION: {self.POSITION} // LOOK_AT: {self.LOOK_AT} // COLOUR: {self.COLOUR} // FOV: {self.FOV} // INTENSITY: {self.INTENSITY} // MIN_DISTANCE: {self.MIN_DISTANCE} // MAX_DISTANCE: {self.MAX_DISTANCE} // SPACE_MATRIX: {self.SPACE_MATRIX} // SHADOW_MAP: {self.SHADOW_MAP}]>"


class EXPLOSION(WORLD_OBJECT):
	#Hurts/moves ENEMY/PLAYER
	def __init__(self, POSITION, DIMENTIONS, STRENGTH, TEXTURE_INFO):
		POINTS = FIND_CUBOID_POINTS(DIMENTIONS, POSITION)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)

		super().__init__(-1, POSITION, True, TEXTURE_INFO=TEXTURE_INFO, NORMALS=NORMALS, BOUNDING_BOX=BOUNDING_BOX_OBJ)
		self.TEXTURE_SHEETS_USED = CONSTANTS["EXPLOSION_GRAPHIC_SHEET"]

		self.DIMENTIONS_2D = VECTOR_2D((DIMENTIONS.X + DIMENTIONS.Z) / 2, DIMENTIONS.Y)
		self.DIMENTIONS_3D = DIMENTIONS
		self.DAMAGE_STRENGTH = STRENGTH
		self.PUSH_FORCE = CONSTANTS["EXPLOSION_PUSH_FORCE"]
		self.POINTS = POINTS
		self.LIFETIME = CONSTANTS["MAX_EXPLOSION_PERSIST_SECONDS"]
		self.EXPLODED = False

	def __repr__(self):
		return f"<EXPLOSION: [POSITION: {self.POSITION} // DIMENTIONS_2D: {self.DIMENTIONS_2D} // DIMENTIONS_3D: {self.DIMENTIONS_3D} // STRENGTH: {self.DAMAGE_STRENGTH} // PUSH_FORCE: {self.PUSH_FORCE} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS}]>"



"""
Physics Objects
> CUBE_PHYSICS (Physics-cube)
> ITEM (Gives supplies to the player when touched)
> ENEMY (Hostile towards the player)
> PROJECTILE (Harms ENEMY/PLAYER)
> PLAYER (Player data)
"""


class CUBE_PHYSICS(PHYSICS_OBJECT):
	#Physics cube.
	def __init__(self, ID, POSITION, DIMENTIONS, MASS, ROTATION, TEXTURE_INFO, TEXTURE_SHEETS_USED):
		POINTS = FIND_CUBOID_POINTS(DIMENTIONS, POSITION)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)

		super().__init__(ID, POSITION, ROTATION, NORMALS, BOUNDING_BOX_OBJ, MASS, TEXTURE_INFO)
		self.TEXTURE_SHEETS_USED = TEXTURE_SHEETS_USED

		FACES = GET_CUBOID_FACE_INDICES()
		self.FACES = FACES
		

		self.DIMENTIONS = DIMENTIONS
		self.POINTS = POINTS

	def __repr__(self):
		return f"<CUBE_PHYSICS: [POSITION: {self.POSITION} // ROTATION: {self.ROTATION} // DIMENTIONS: {self.DIMENTIONS} // MASS: {self.MASS} // POINTS: {self.POINTS} // LATERAL_VELOCITY: {self.LATERAL_VELOCITY} // ROTATIONAL_VELOCITY: {self.ROTATIONAL_VELOCITY}]>"


class ITEM(PHYSICS_OBJECT):
	#Item that gives supplies when touched
	def __init__(self, ID, POSITION, POP, TEXTURE_INFO, TYPE, TEXTURE_SHEETS_USED):
		SUPPLIES = GET_GAME_DATA(TEXTURE_SHEETS_USED)[1]
		TYPE_DATA = SUPPLIES[TYPE]
		MASS = TYPE_DATA[1]
		POINTS = FIND_CUBOID_POINTS(TYPE_DATA[0], POSITION)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)

		if POP:
			#Whether or not the item should "pop" (mostly for items dropped by enemies)
			#Has a random direction and magnitude, within limits to make the item slightly "pop" in a direction on creation.
			MAGNITUDE = random.uniform(0.1, 0.5)
			ANGLE_X = maths.radians(random.randint(0, 360))
			ANGLE_Y = maths.radians(random.randint(23, 68))

			LATERAL_VELOCITY = VECTOR_3D(
				MAGNITUDE * maths.cos(ANGLE_Y) * maths.cos(ANGLE_X),
				MAGNITUDE * maths.cos(ANGLE_Y) * maths.sin(ANGLE_X),
				MAGNITUDE * maths.sin(ANGLE_Y)
			)

		else:
			LATERAL_VELOCITY = VECTOR_3D(0.0, 0.0, 0.0)

		super().__init__(ID, POSITION, None, NORMALS, BOUNDING_BOX_OBJ, MASS, TEXTURE_INFO, LATERAL_VELOCITY=LATERAL_VELOCITY)
		self.TEXTURE_SHEETS_USED = TEXTURE_SHEETS_USED

		self.TYPE = TYPE
		self.DIMENTIONS_2D = VECTOR_2D((TYPE_DATA[0].X + TYPE_DATA[0].Z) / 2, TYPE_DATA[0].Y)
		self.DIMENTIONS_3D = TYPE_DATA[0]
		

		self.POINTS = POINTS
		self.SUPPLY = TYPE_DATA[3].upper()
		self.QUANTITY = TYPE_DATA[4]
		self.EMPTY = False


	def __repr__(self):
		return f"<ITEM: [POSITION: {self.POSITION} // ITEM_TYPE: {self.TYPE} // DIMENTIONS_2D: {self.DIMENTIONS_2D} // DIMENTIONS_3D: {self.DIMENTIONS_3D} // POINTS: {self.POINTS} // LATERAL_VELOCITY: {self.LATERAL_VELOCITY}]>"


	def TAKE(self, PLAYER_INSTANCE):
		#When touched; removes as much as possible, and if not all; retains some.
		match self.SUPPLY:
			case "ENERGY":
				PLAYER_VALUE = PLAYER_INSTANCE.ENERGY
				MAX_VALUE = CONSTANTS["PLAYER_START_ENERGY"]
			case "HEALTH":
				PLAYER_VALUE = PLAYER_INSTANCE.HEALTH
				MAX_VALUE = CONSTANTS["PLAYER_MAX_HEALTH"]
			case _:
				log.ERROR("utils.py // <ITEM>", f"Unknown supply type; {self.SUPPLY}")


		#Only take integer amounts, > 0 and <= the current quantity in the supply.
		AMOUNT_TO_TAKE = round(min(MAX_VALUE - PLAYER_VALUE, self.QUANTITY))
		
		if AMOUNT_TO_TAKE == 0:
			return

		match self.SUPPLY:
			case "ENERGY":
				PLAYER_INSTANCE.ENERGY += AMOUNT_TO_TAKE
			case "HEALTH":
				PLAYER_INSTANCE.HEALTH += AMOUNT_TO_TAKE
			case _:
				log.ERROR("utils.py // <ITEM>", f"Unknown supply type; {self.SUPPLY}")

		self.QUANTITY -= AMOUNT_TO_TAKE
		if self.QUANTITY <= 0:
			self.EMPTY = True
		


class ENEMY(PHYSICS_OBJECT):
	#Hostile enemy towards the player.
	def __init__(self, ID, POSITION, TYPE, TEXTURES, ROTATION, TEXTURE_SHEETS_USED, SCENE_SHEETS_USED):
		HOSTILES = GET_GAME_DATA(SCENE_SHEETS_USED)[0]
		TYPE_DATA = HOSTILES[TYPE]
		POINTS = FIND_CUBOID_POINTS(TYPE_DATA[0], POSITION)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)
		MASS = TYPE_DATA[1]
		#Textures would be loaded here, but that would mean circular imports to \imgs\texture_load.py\, so have been avoided.
		#Textures are instead loaded outside of this class, and passed in. (Always defined outside of \utils.py\)
		super().__init__(ID, POSITION, ROTATION, NORMALS, BOUNDING_BOX_OBJ, MASS, TEXTURES)
		self.TEXTURE_SHEETS_USED = TEXTURE_SHEETS_USED

		self.DIMENTIONS_2D = VECTOR_2D((TYPE_DATA[0].X + TYPE_DATA[0].Z) / 2, TYPE_DATA[0].Y)
		self.DIMENTIONS = TYPE_DATA[0]
		
		FACES = GET_CUBOID_FACE_INDICES()
		self.FACES = FACES


		self.TARGET = NPC_PATH_NODE("None", POSITION, {})
		self.SPEED = 0.02 #Standard speed for enemies.
		

		self.POINTS = POINTS
		self.TYPE = TYPE
		self.MAX_HEALTH = TYPE_DATA[3]
		self.HEALTH = TYPE_DATA[3]
		self.HELD_ITEM = TYPE_DATA[4]
		self.LOOT = TYPE_DATA[5]
		self.ALIVE = True
		self.AWAKE = False
		self.ATTACK_STRENGTH = 1.0
		self.LIFETIME = CONSTANTS["MAX_DECEASED_PERSIST_SECONDS"] #5 Seconds of "lifetime" after self.ALIVE is set to False.
		self.COOLDOWN = 0.0 #5 Seconds of cooldown maximum is counted between attacks.


	def __repr__(self):
		return f"<ENEMY: [POSITION: {self.POSITION} // ENEMY_TYPE: {self.TYPE} // DIMENTIONS_2D: {self.DIMENTIONS_2D} // POINTS: {self.POINTS} // LATERAL_VELOCITY: {self.LATERAL_VELOCITY} // ATTACK_STRENGTH: {self.ATTACK_STRENGTH} // HEALTH: {self.HEALTH} // ALIVE: {self.ALIVE}]>"


	def HURT(self, DAMAGE, PHYS_DATA, CURRENT_ID):
		#Harms the enemy, and sets their state to ALIVE=False if HEALTH<=0.
		self.HEALTH = round(CLAMP(self.HEALTH - DAMAGE, 0, self.MAX_HEALTH))
		self.AWAKE = True
		if self.HEALTH == 0 and self.ALIVE:
			self.ALIVE = False
			return self.DROP_ITEMS(PHYS_DATA, CURRENT_ID)

		return PHYS_DATA


	def DROP_ITEMS(self, PHYS_DATA, CURRENT_ID):
		ITEMS_DATA = GET_GAME_DATA(None, PROCESS_SHEETS_USED=False)[1]
		for ITEM_TYPE in self.LOOT:
			if ITEM_TYPE in ITEMS_DATA:
				CURRENT_ID += 1
				SPECIFIC_ITEM_DATA = ITEMS_DATA[ITEM_TYPE]
				PHYS_DATA[0][CURRENT_ID] = ITEM(
					CURRENT_ID,									#Item ID
					self.POSITION + VECTOR_3D(0.0, 0.05, 0.0),	#Position + an offset, so the items don't get stuck in the surface the ENEMY was standing on.
					True,										#Make the item "Pop" (Small jump in a random direction)
					SPECIFIC_ITEM_DATA[2][0][1],				#Texture Data
					ITEM_TYPE,									#Item Type
					SPECIFIC_ITEM_DATA[2][0][0],				#Texture Sheet used
				)
			else:
				log.ERROR("utils.py // <ENEMY>", f"Unknown item type; {ITEM}\n    Valid item types; {ITEMS_DATA.keys()}")

		return PHYS_DATA


class PROJECTILE(PHYSICS_OBJECT):
	#Harms ENEMY/PLAYER.
	def __init__(self, ID, POSITION, FIRED_VELOCITY, TYPE, TEXTURE_INFO, TEXTURE_SHEETS_USED, OWNER):
		PROJECTILES = GET_GAME_DATA(TEXTURE_SHEETS_USED)[2]
		TYPE_DATA = PROJECTILES[TYPE]
		POINTS = FIND_CUBOID_POINTS(TYPE_DATA[0], POSITION)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)
		MASS = TYPE_DATA[1]

		super().__init__(ID, POSITION, None, NORMALS, BOUNDING_BOX_OBJ, MASS, TEXTURE_INFO, LATERAL_VELOCITY=FIRED_VELOCITY)
		self.TEXTURE_SHEETS_USED = TEXTURE_SHEETS_USED

		AVG_X = (TYPE_DATA[0].X + TYPE_DATA[0].Z) / 2
		self.DIMENTIONS_2D = VECTOR_2D(AVG_X, TYPE_DATA[0].Y)
		self.DIMENTIONS = TYPE_DATA[0]
		

		self.POINTS = POINTS
		self.TYPE = TYPE
		self.CREATE_EXPLOSION = TYPE_DATA[3]
		self.DAMAGE_STRENGTH = TYPE_DATA[4]
		self.OWNER = OWNER
		self.LIFETIME = CONSTANTS["MAX_PROJECTILE_LIFESPAN_SECONDS"]

	def __repr__(self):
		return f"<PROJECTILE: [POSITION: {self.POSITION} // PROJECTILE_TYPE: {self.TYPE} // DIMENTIONS_2D: {self.DIMENTIONS_2D} // POINTS: {self.POINTS} // LATERAL_VELOCITY: {self.LATERAL_VELOCITY} // DAMAGE_STRENGTH: {self.DAMAGE_STRENGTH} // CREATE_EXPLOSION: {self.CREATE_EXPLOSION}]>"


class PLAYER(PHYSICS_OBJECT):
	#Player Data.
	def __init__(self, ID, POSITION, ROTATION, ITEMS):
		self.DIMENTIONS = CONSTANTS["PLAYER_COLLISION_CUBOID"]
		POINTS = FIND_CUBOID_POINTS(self.DIMENTIONS, POSITION)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)

		super().__init__(ID, POSITION, ROTATION, NORMALS, BOUNDING_BOX_OBJ, CONSTANTS["PLAYER_MASS"], None)
		
		
		FACES = GET_CUBOID_FACE_INDICES()
		self.FACES = FACES
		

		self.POINTS = POINTS
		self.MAX_HEALTH = CONSTANTS["PLAYER_MAX_HEALTH"]
		self.HEALTH = CONSTANTS["PLAYER_MAX_HEALTH"]
		self.ITEMS = ITEMS
		self.HELD_ITEM = None
		self.ENERGY = CONSTANTS["PLAYER_START_ENERGY"]
		self.ALIVE = True


	def __repr__(self):
		return f"<PLAYER: [POSITION: {self.POSITION} // LATERAL_VELOCITY: {self.LATERAL_VELOCITY} // ITEMS: {list(self.ITEMS.keys())} // MASS: {self.MASS} // ENERGY: {self.ENERGY} // HEALTH: {self.HEALTH} // ALIVE: {self.ALIVE}]>"


	def HURT(self, DAMAGE, PHYS_DATA, CURRENT_ID):
		#Harms the player, and sets their state to ALIVE=False if HEALTH<=0.
		self.HEALTH = round(CLAMP(self.HEALTH - DAMAGE, 0, self.MAX_HEALTH))
		if self.HEALTH == 0:
			self.ALIVE = False
		return PHYS_DATA



#Data-structuring classes (Vectors, Colours)



class RGBA:
	"""
	RGB Colour type.
	Has 4 values (RGBA), as either floats (0-1) or integers (0-255)
	Allows for further colour manipulation
	"""
	def __init__(self, R, G, B, A, RANGE=(0, 255)): #Formatting as [R, G, B, A]
		self.R = round(CLAMP(R, RANGE[0], RANGE[1]), 8)
		self.G = round(CLAMP(G, RANGE[0], RANGE[1]), 8)
		self.B = round(CLAMP(B, RANGE[0], RANGE[1]), 8)
		self.A = round(CLAMP(A, RANGE[0], RANGE[1]), 8)

	def __add__(self, OTHER):
		R = self.R + OTHER
		G = self.G + OTHER
		B = self.B + OTHER
		A = self.A + OTHER

		return RGBA(R, G, B, A)

	def __sub__(self, OTHER):
		R = self.R - OTHER
		G = self.G - OTHER
		B = self.B - OTHER
		A = self.A - OTHER

		return RGBA(R, G, B, A)

	def __mul__(self, OTHER):
		if type(OTHER) == RGBA:
			self_DECIMAL = self.TO_DECIMAL()
			OTHER_DECIMAL = OTHER.TO_DECIMAL()
			R = (self_DECIMAL.R * OTHER_DECIMAL.R) * 255
			G = (self_DECIMAL.G * OTHER_DECIMAL.G) * 255
			B = (self_DECIMAL.B * OTHER_DECIMAL.B) * 255
			A = (self_DECIMAL.A * OTHER_DECIMAL.A) * 255

		elif type(OTHER) in [int, float]:
			R = self.R * OTHER
			G = self.G * OTHER
			B = self.B * OTHER
			A = self.A * OTHER

		else:
			raise TypeError(f"Cannot multiply type {type(OTHER)} and RGBA.")

		return RGBA(R, G, B, A)

	def __rmul__(self, OTHER):
		return self * OTHER

	def __truediv__(self, SCALAR):
		if type(OTHER) == RGBA:
			R = self.R / OTHER.R
			G = self.G / OTHER.G
			B = self.B / OTHER.B
			A = self.A / OTHER.A

		elif type(OTHER) in [int, float]:
			R = self.R / OTHER
			G = self.G / OTHER
			B = self.B / OTHER
			A = self.A / OTHER

		else:
			raise TypeError(f"Cannot divide type [{type(OTHER)}] and RGBA.")

		return RGBA(R, G, B, A)

	def __iadd__(self, OTHER):
		self.X += OTHER.X
		self.Y += OTHER.Y
		self.Z += OTHER.Z

	def __isub__(self, OTHER):
		self.R -= OTHER.R
		self.G -= OTHER.G
		self.B -= OTHER.B
		self.A -= OTHER.A

	def __eq__(self, OTHER):
		return self.R == OTHER.R and self.G == OTHER.G and self.B == OTHER.B and self.A == OTHER.B

	def __ne__(self, OTHER):
		return not self == OTHER
	
	def __repr__(self):
		return f"<RGBA: [{self.R}, {self.G}, {self.B}, {self.A}]>"

	def __iter__(self):
		return iter([self.R, self.G, self.B, self.A])

	def TO_DECIMAL(self, CURRENT_RANGE=(0, 255)):
		return RGBA(
			(self.R - CURRENT_RANGE[0]) / CURRENT_RANGE[1],
			(self.G - CURRENT_RANGE[0]) / CURRENT_RANGE[1],
			(self.B - CURRENT_RANGE[0]) / CURRENT_RANGE[1],
			(self.A - CURRENT_RANGE[0]) / CURRENT_RANGE[1],
			RANGE = (0.0, 1.0)
		)

	def CONVERT_TO_PYRR_VECTOR4(self):
		return Vector4(list(self))

	def CONVERT_TO_GLM_VEC4(self):
		return glm.vec4(self.R, self.G, self.B, self.A)



class VECTOR_2D:
	"""
	Custom 2D Vector type.
	Has X and Y coordinate.
	Allows for many basic and mid-level operations internally, and is used for more advanced cases (e.g. Angle comparisons) externally.
	"""
	def __init__(self, X, Y): #Formatting as [X, Y]
		self.X = float(X)
		self.Y = float(Y)

	def __add__(self, OTHER): #Add self and OTHER // {self} + {OTHER}
		X = self.X + OTHER.X
		Y = self.Y + OTHER.Y
		return VECTOR_2D(X, Y)

	def __sub__(self, OTHER): #Subtract OTHER from self // {self} - {OTHER}
		X = self.X - OTHER.X
		Y = self.Y - OTHER.Y
		return VECTOR_2D(X, Y)

	def __mul__(self, SCALAR): #Multiply self by OTHER // {self} * {OTHER}
		X = self.X * SCALAR
		Y = self.Y * SCALAR
		return VECTOR_2D(X, Y)

	def __rmul__(self, SCALAR): #Multiply OTHER by self // {OTHER} * {self}
		return self * SCALAR

	def __truediv__(self, SCALAR): #Divide self by SCALAR // {self} / {SCALAR}
		X = self.X / SCALAR
		Y = self.Y / SCALAR
		return VECTOR_2D(X, Y)

	def __iadd__(self, OTHER): #Support for +=
		return self + OTHER

	def __isub__(self, OTHER): #Support for -=
		return self - OTHER
	
	def __imul__(self, SCALAR): #Support for *=
		return self * OTHER

	def __idiv__(self, SCALAR): #Support for /=
		return self / OTHER
	
	def __abs__(self): #Magnitude of self // abs({self})
		return (self.X ** 2 + self.Y ** 2) ** 0.5

	def __lt__(self, OTHER): #self Less Than OTHER // {self} < {OTHER}
		return abs(self) < abs(OTHER)

	def __le__(self, OTHER): #self Less Than or Equal To OTHER // {self} <= {OTHER}
		return abs(self) <= abs(OTHER)

	def __gt__(self, OTHER): #self Greater Than OTHER // {self} > {OTHER}
		return abs(self) > abs(OTHER)

	def __ge__(self, OTHER): #self Greater Than or Equal To OTHER // {self} >= {OTHER}
		return abs(self) >= abs(OTHER)

	def __eq__(self, OTHER): #self perfectly equal to OTHER // {self} == {OTHER}
		return self.X == OTHER.X and self.Y == OTHER.Y

	def __ne__(self, OTHER): #self not perfectly equal to OTHER // {self} != {OTHER}
		return self.X != OTHER.X and self.Y != OTHER.Y

	def __repr__(self):
		return f"<VECTOR_2D: [{self.X}, {self.Y}]>"

	def __iter__(self):
		return iter([self.X, self.Y])

	def TO_INT(self):
		X = int(self.X)
		Y = int(self.Y)
		return VECTOR_2D(X, Y)

	def TO_FLOAT(self):
		X = float(self.X)
		Y = float(self.Y)
		return VECTOR_2D(X, Y)


	def SIGN(self): #Gives the sign of each value in the vector.
		X = 1.0 if self.X > 0 else -1.0 if self.X < 0 else 0.0
		Y = 1.0 if self.Y > 0 else -1.0 if self.Y < 0 else 0.0
		return VECTOR_2D(X, Y)

	def NORMALISE(self): #Normalise self // {self}.NORMALISE()
		MAGNITUDE = abs(self)
		if MAGNITUDE != 0:
			return self / MAGNITUDE

		return VECTOR_2D(0.0, 0.0)

	def DOT(self, OTHER): #Dot product of self and OTHER // {self}.DOT({OTHER})
		return (self.X * OTHER.X) + (self.Y * OTHER.Y)

	def DET(self, OTHER): #Determinant of self and OTHER // {self}.DET({OTHER})
		return self.X * OTHER.Y - self.Y * OTHER.X

	def PROJECT(self, OTHER): #Project point (OTHER) onto axis (self) // {AXIS}.PROJECT({POINT})
		DOT_PRODUCTS = DOT(OTHER, self)
		return [min(DOT_PRODUCTS), max(DOT_PRODUCTS)]

	def IN_LIST(self, OTHER): #If self in OTHER (list) // {self}.IN_LIST({OTHER})
		for ITEM in OTHER:
			if self == ITEM:
				return True
		return False

	def RADIANS(self): #Converts to radians.
		X = maths.radians(self.X)
		Y = maths.radians(self.Y)
		return VECTOR_2D(X, Y)

	def DEGREES(self): #Converts to degrees.
		X = maths.degrees(self.X)
		Y = maths.degrees(self.Y)
		return VECTOR_2D(X, Y)

	def CLAMP(self, X_BOUNDS=None, Y_BOUNDS=None):
		#Clamps within a set of boundaries.
		if X_BOUNDS is not None:
			self.X = CLAMP(self.X, X_BOUNDS[0], X_BOUNDS[1])
		if Y_BOUNDS is not None:
			self.Y = CLAMP(self.Y, Y_BOUNDS[0], Y_BOUNDS[1])
		return self

	def ROTATE_BY(self, ANGLE):
		#Rotates by a 2D angle vector, around (0,0)
		X = (self.X * maths.cos(ANGLE)) - (self.Y * maths.sin(ANGLE))
		Y = (self.X * maths.sin(ANGLE)) + (self.Y * maths.cos(ANGLE))
		return VECTOR_2D(X, Y)



class VECTOR_3D:
	"""
	Custom 3D Vector type.
	Has X, Y and Z coordinate.
	Allows for many basic and mid-level operations internally, and is used for more advanced cases (e.g. S.A.T.) externally.
	"""
	def __init__(self, X, Y, Z): #Formatting as [X, Y, Z]
		self.X = float(X)
		self.Y = float(Y)
		self.Z = float(Z)
	
	def __add__(self, OTHER): #Add self and OTHER // {self} + {OTHER}
		X = self.X + OTHER.X
		Y = self.Y + OTHER.Y
		Z = self.Z + OTHER.Z
		return VECTOR_3D(X, Y, Z)

	def __sub__(self, OTHER): #Subtract OTHER from self // {self} - {OTHER}
		X = self.X - OTHER.X
		Y = self.Y - OTHER.Y
		Z = self.Z - OTHER.Z
		return VECTOR_3D(X, Y, Z)

	def __mul__(self, SCALAR): #Multiply self by OTHER // {self} * {OTHER}
		X = self.X * SCALAR
		Y = self.Y * SCALAR
		Z = self.Z * SCALAR
		return VECTOR_3D(X, Y, Z)

	def __rmul__(self, SCALAR): #Multiply OTHER by self // {OTHER} * {self}
		return self * SCALAR

	def __truediv__(self, SCALAR): #Divide self by SCALAR // {self} / {SCALAR}
		X = self.X / SCALAR
		Y = self.Y / SCALAR
		Z = self.Z / SCALAR
		return VECTOR_3D(X, Y, Z)

	def __iadd__(self, OTHER): #Support for +=
		return self + OTHER

	def __isub__(self, OTHER): #Support for -=
		return self - OTHER
	
	def __imul__(self, SCALAR): #Support for *=
		return self * SCALAR

	def __idiv__(self, SCALAR): #Support for /=
		return self / SCALAR

	def __abs__(self): #Magnitude of self // abs({self})
		return (self.X ** 2 + self.Y ** 2 + self.Z ** 2) ** 0.5

	def __lt__(self, OTHER): #self Less Than OTHER // {self} < {OTHER}
		return abs(self) < abs(OTHER)

	def __le__(self, OTHER): #self Less Than or Equal To OTHER // {self} <= {OTHER}
		return abs(self) <= abs(OTHER)

	def __gt__(self, OTHER): #self Greater Than OTHER // {self} > {OTHER}
		return abs(self) > abs(OTHER)

	def __ge__(self, OTHER): #self Greater Than or Equal To OTHER // {self} >= {OTHER}
		return abs(self) >= abs(OTHER)

	def __eq__(self, OTHER): #self perfectly equal to OTHER // {self} == {OTHER}
		return self.X == OTHER.X and self.Y == OTHER.Y and self.Z == OTHER.Z

	def __ne__(self, OTHER): #self not perfectly equal to OTHER // {self} != {OTHER}
		return self.X != OTHER.X and self.Y != OTHER.Y and self.Z != OTHER.Z

	def __repr__(self):
		return f"<VECTOR_3D: [{self.X}, {self.Y}, {self.Z}]>"

	def __iter__(self): #Creates an iterable of itself
		return iter([self.X, self.Y, self.Z])

	def TO_INT(self):
		X = int(self.X)
		Y = int(self.Y)
		Z = int(self.Z)
		return VECTOR_3D(X, Y, Z)

	def TO_FLOAT(self):
		X = float(self.X)
		Y = float(self.Y)
		Z = float(self.Z)
		return VECTOR_3D(X, Y, Z)

	def TO_VECTOR_2D(self):
		return VECTOR_2D(self.X, self.Z)
	
	def SIGN(self): #Gets the sign of each value in the vector.
		X = 1.0 if self.X > 0.0 else -1.0 if self.X < 0.0 else 0.0
		Y = 1.0 if self.Y > 0.0 else -1.0 if self.Y < 0.0 else 0.0
		Z = 1.0 if self.Z > 0.0 else -1.0 if self.Z < 0.0 else 0.0
		return VECTOR_3D(X, Y, Z)

	def RECIPROCAL(self):
		INV_X = 1/self.X if self.X != 0 else 0.0
		INV_Y = 1/self.Y if self.Y != 0 else 0.0
		INV_Z = 1/self.Z if self.Z != 0 else 0.0
		return VECTOR_3D(INV_X, INV_Y, INV_Z)

	def NORMALISE(self): #Normalise self // {self}.NORMALISE()if PREFERENCES["PROFILER_DEBUG"]: ##@profile
		MAGNITUDE = abs(self)
		if MAGNITUDE != 0:
			self /= MAGNITUDE
		else:
			self.X, self.Y, self.Z = 0.0, 0.0, 0.0
		return self


	def DOT(self, OTHER): #Dot product of self and OTHER // {self}.DOT({OTHER})
		return (self.X * OTHER.X) + (self.Y * OTHER.Y) + (self.Z * OTHER.Z)

	def CROSS(self, OTHER): #Cross product of self and OTHER // {self}.CROSS({OTHER})
		X = self.Y * OTHER.Z - self.Z * OTHER.Y
		Y = self.Z * OTHER.X - self.X * OTHER.Z
		Z = self.X * OTHER.Y - self.Y * OTHER.X
		return VECTOR_3D(X, Y, Z)

	def PROJECT(self, OTHER): #Project points (OTHER) onto axis (self) // {AXIS}.PROJECT({POINTS})
		MIN_PROJ, MAX_PROJ = float('inf'), float('-inf')
		for POINT in OTHER:
			DOT_PROD = self.DOT(POINT)
			if DOT_PROD < MIN_PROJ:
				MIN_PROJ = DOT_PROD
			if DOT_PROD > MAX_PROJ:
				MAX_PROJ = DOT_PROD
		return [MIN_PROJ, MAX_PROJ]

	def IN_LIST(self, OTHER): #If self in OTHER (list) // {self}.IN_LIST({OTHER})
		for ITEM in OTHER:
			if self == ITEM:
				return True
		return False

	def RADIANS(self): #Converts to radians.
		X = maths.radians(self.X)
		Y = maths.radians(self.Y)
		Z = maths.radians(self.Z)
		return VECTOR_3D(X, Y, Z)

	def DEGREES(self): #Converts to degrees.
		X = maths.degrees(self.X)
		Y = maths.degrees(self.Y)
		Z = maths.degrees(self.Z)
		return VECTOR_3D(X, Y, Z)

	def CLAMP(self, X_BOUNDS=None, Y_BOUNDS=None, Z_BOUNDS=None):
		#Clamps each within set boundaries.
		if X_BOUNDS is not None:
			self.X = CLAMP(self.X, X_BOUNDS[0], X_BOUNDS[1])
		if Y_BOUNDS is not None:
			self.Y = CLAMP(self.Y, Y_BOUNDS[0], Y_BOUNDS[1])
		if Z_BOUNDS is not None:
			self.Z = CLAMP(self.Z, Z_BOUNDS[0], Z_BOUNDS[1])
		return self

	def ROTATE_BY(self, ANGLE, CENTRE):
		#Rotates around a centrepoint, using a 3D rotational matrix.
		sinX, cosX = maths.sin(ANGLE.X), maths.cos(ANGLE.X)
		sinY, cosY = maths.sin(ANGLE.Y), maths.cos(ANGLE.Y)
		sinZ, cosZ = maths.sin(ANGLE.Z), maths.cos(ANGLE.Z)
		MATRIX = NP.array([
			[cosY * cosZ,	(sinX * sinY * cosZ) - (cosX * sinZ),	(cosX * sinY * cosZ) + (sinX * sinZ)],
			[cosY * sinZ,	(sinX * sinY * sinZ) + (cosX * cosZ),	(cosX * sinY * sinZ) - (sinX * cosZ)],
			[-sinY,			sinX * cosY,							cosX * cosY							]
		])

		X, Y, Z = NP.dot(MATRIX, self.CONVERT_TO_NP_ARRAY())
		return VECTOR_3D(X + CENTRE.X, Y + CENTRE.Y, Z + CENTRE.Z)

	def CONVERT_TO_NP_ARRAY(self, DTYPE=NP.float64): #Convert to a NumPy array.
		return NP.array(list(self), dtype=DTYPE)

	def CONVERT_TO_PYRR_VECTOR3(self): #Convert to a pyrr Vector3.
		return Vector3(list(self))

	def CONVERT_TO_GLM_VEC3(self): #Convert to a GLM vec3.
		return glm.vec3(*list(self))




#Program-wide values, that must be sync-ed between all files.
#(Uses utils.py as a "hub" for this data, as all other files import these functions/data.)
global PREFERENCES, CONSTANTS
PREFERENCES, CONSTANTS = GET_CONFIGS()
