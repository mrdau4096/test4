"""
[py]
Short for "Utilities.py", this file contains custom maths functions that are used for mostly working with vectors in a more code-oriented method, along with a few general-purpose functions for debugging and other purposes.
Most useful for collision calculations, gravity force application, rendering, debugging and so on.

________________
Imports Modules;
-Math
-NumPy
"""
import math as maths
import random
import os, sys

π = maths.pi
πDIV2 = π / 2

sys.path.append("modules")
from pyrr import Matrix44, Vector3, Vector4
import glm

def CLAMP(VARIABLE, LOWER, UPPER): #Clamps any value between 2 bounds. Used almost exclusively for camera angle.
	match VARIABLE:
		case N if N > UPPER:
			return UPPER
		
		case N if N < LOWER:
			return LOWER
		
		case _:
			return VARIABLE



def FIND_VECTOR(COORDINATE_A, COORDINATE_B): #Finds a vector between 2 given coordinates.
	return VECTOR_3D(COORDINATE_B.X - COORDINATE_A.X, COORDINATE_B.Y - COORDINATE_A.Y, COORDINATE_B.Z - COORDINATE_A.Z)


def FIND_CUBOID_POINTS(DIMENTIONS, CENTRE): #Returns the points for any axis-aligned cuboid. Mostly helpful for initialising, due to physics rotation not allowing for axis-aligned objects often.
	HALF_DIMENTIONS = DIMENTIONS / 2

	OFFSET_X = VECTOR_3D(0.1 * DIMENTIONS.X, 	0.0,  					0.0 				)
	OFFSET_Y = VECTOR_3D(0.0,  					0.1 * DIMENTIONS.Y, 	0.0 				)
	OFFSET_Z = VECTOR_3D(0.0,  					0.0,  					0.1 * DIMENTIONS.Z	)
	
	return [
			VECTOR_3D(CENTRE.X - HALF_DIMENTIONS.X, CENTRE.Y - HALF_DIMENTIONS.Y, CENTRE.Z - HALF_DIMENTIONS.Z) + OFFSET_X + OFFSET_Y + OFFSET_Z,  # Vertex 0 (min x, min y, min z)
			VECTOR_3D(CENTRE.X + HALF_DIMENTIONS.X, CENTRE.Y - HALF_DIMENTIONS.Y, CENTRE.Z - HALF_DIMENTIONS.Z) - OFFSET_X + OFFSET_Y + OFFSET_Z,  # Vertex 1 (max x, min y, min z)
			VECTOR_3D(CENTRE.X - HALF_DIMENTIONS.X, CENTRE.Y - HALF_DIMENTIONS.Y, CENTRE.Z + HALF_DIMENTIONS.Z) + OFFSET_X + OFFSET_Y - OFFSET_Z,  # Vertex 2 (min x, min y, max z)
			VECTOR_3D(CENTRE.X + HALF_DIMENTIONS.X, CENTRE.Y - HALF_DIMENTIONS.Y, CENTRE.Z + HALF_DIMENTIONS.Z) - OFFSET_X + OFFSET_Y - OFFSET_Z,  # Vertex 3 (max x, min y, max z)
			VECTOR_3D(CENTRE.X - HALF_DIMENTIONS.X, CENTRE.Y + HALF_DIMENTIONS.Y, CENTRE.Z - HALF_DIMENTIONS.Z) + OFFSET_X - OFFSET_Y + OFFSET_Z,  # Vertex 4 (min x, max y, min z)
			VECTOR_3D(CENTRE.X + HALF_DIMENTIONS.X, CENTRE.Y + HALF_DIMENTIONS.Y, CENTRE.Z - HALF_DIMENTIONS.Z) - OFFSET_X - OFFSET_Y + OFFSET_Z,  # Vertex 5 (max x, max y, min z)
			VECTOR_3D(CENTRE.X - HALF_DIMENTIONS.X, CENTRE.Y + HALF_DIMENTIONS.Y, CENTRE.Z + HALF_DIMENTIONS.Z) + OFFSET_X - OFFSET_Y - OFFSET_Z,  # Vertex 6 (min x, max y, max z)
			VECTOR_3D(CENTRE.X + HALF_DIMENTIONS.X, CENTRE.Y + HALF_DIMENTIONS.Y, CENTRE.Z + HALF_DIMENTIONS.Z) - OFFSET_X - OFFSET_Y - OFFSET_Z   # Vertex 7 (max x, max y, max z)
		]



def FIND_CUBOID_NORMALS(POINTS): #Find the normals of a cuboid, via its 8 points. This allows the cuboid to be rotated along any axis, and still give the normals.
	VECTOR_R = FIND_VECTOR(POINTS[0], POINTS[1]) #Maximum X
	VECTOR_G = FIND_VECTOR(POINTS[0], POINTS[4]) #Maximum Y
	VECTOR_B = FIND_VECTOR(POINTS[0], POINTS[2]) #Maximum Z

	NORMAL_BOTTOM = -1 * VECTOR_G
	NORMAL_SIDE_A = -1 * VECTOR_B
	NORMAL_SIDE_B = VECTOR_B
	NORMAL_SIDE_C = -1 * VECTOR_R
	NORMAL_SIDE_D = VECTOR_R
	NORMAL_TOP = VECTOR_G

	return [NORMAL_BOTTOM, NORMAL_SIDE_A, NORMAL_SIDE_B, NORMAL_SIDE_C, NORMAL_SIDE_D, NORMAL_TOP]


def FIND_CENTROID(POINTS):
	SUM = VECTOR_3D(0.0, 0.0, 0.0)
	for PT in POINTS:
		SUM += PT
	return SUM / len(POINTS)


def FIND_CLOSEST_CUBE_TRIS(VERTICES, PLAYER_VERTS, NORMALS):
	CUBE_CENTRE = (VERTICES[0] + VERTICES[7]) / 2
	TRIs = (
		(VERTICES[0], VERTICES[1], VERTICES[2]),  #Bottom Face; Triangle A (-Y)
		(VERTICES[1], VERTICES[3], VERTICES[2]),  #Bottom Face; Triangle B (-Y)
		(VERTICES[0], VERTICES[1], VERTICES[4]),  #Front Face; Triangle A (+Z)
		(VERTICES[1], VERTICES[5], VERTICES[4]),  #Front Face; Triangle B (+Z)
		(VERTICES[2], VERTICES[3], VERTICES[6]),  #Back Face; Triangle A (-Z)
		(VERTICES[3], VERTICES[7], VERTICES[6]),  #Back Face; Triangle B (-Z)
		(VERTICES[0], VERTICES[2], VERTICES[4]),  #Left Face; Triangle A (-X)
		(VERTICES[2], VERTICES[6], VERTICES[4]),  #Left Face; Triangle B (-X)
		(VERTICES[1], VERTICES[3], VERTICES[5]),  #Right Face; Triangle A (+X)
		(VERTICES[3], VERTICES[7], VERTICES[5]),  #Right Face; Triangle B (+X)
		(VERTICES[4], VERTICES[5], VERTICES[6]),  #Top Face; Triangle A (+Y)
		(VERTICES[5], VERTICES[7], VERTICES[6])  #Top Face; Triangle B (+Y)
	)

	FACEs = {
		"-Y": (TRIs[0], TRIs[1]),
		"+Z": (TRIs[2], TRIs[3]),
		"-Z": (TRIs[4], TRIs[5]),
		"-X": (TRIs[6], TRIs[7]),
		"+X": (TRIs[8], TRIs[9]),
		"+Y": (TRIs[10], TRIs[11])
	}
	
	PLAYER_MIN_X = PLAYER_VERTS[0].X
	PLAYER_MAX_X = PLAYER_VERTS[7].X
	PLAYER_MIN_Y = PLAYER_VERTS[0].Y
	PLAYER_MAX_Y = PLAYER_VERTS[7].Y
	PLAYER_MIN_Z = PLAYER_VERTS[0].Z
	PLAYER_MAX_Z = PLAYER_VERTS[7].Z

	RELATIVE_POSITION = {
		'-Y': PLAYER_MAX_Y < CUBE_CENTRE.Y,
		'+Z': PLAYER_MIN_Z > CUBE_CENTRE.Z,
		'-Z': PLAYER_MAX_Z < CUBE_CENTRE.Z,
		'-X': PLAYER_MAX_X < CUBE_CENTRE.X,
		'+X': PLAYER_MIN_X > CUBE_CENTRE.X,
		'+Y': PLAYER_MIN_Y > CUBE_CENTRE.Y,
	}

	CLOSEST_FACES = []

	for DIRECTION, IS_CLOSEST in RELATIVE_POSITION.items():
		if IS_CLOSEST:
			INDEX = list(RELATIVE_POSITION.keys()).index(DIRECTION)
			NORMAL = NORMALS[INDEX]
			CLOSEST_FACES.append([FACEs[DIRECTION], NORMAL])

	return CLOSEST_FACES


def CALC_SPRITE_POINTS(SPRITE_POSITION, PLAYER_POSITION, SPRITE_DIMENTIONS):
	OPPOSITE = SPRITE_POSITION.Z - PLAYER_POSITION.Z
	ADJACENT = SPRITE_POSITION.X - PLAYER_POSITION.X
	
	PLAYER_SPRITE_ANGLE = -1 * maths.atan2(OPPOSITE, ADJACENT)
	ANGLE_A = PLAYER_SPRITE_ANGLE + (π / 2)
	ANGLE_B = PLAYER_SPRITE_ANGLE - (π / 2)
	
	LEFT_SIDE_X = SPRITE_POSITION.X + ((SPRITE_DIMENTIONS.X / 2) * maths.cos(ANGLE_A))
	LEFT_SIDE_Z = SPRITE_POSITION.Z + ((SPRITE_DIMENTIONS.X / 2) * maths.sin(ANGLE_B))

	RIGHT_SIDE_X = SPRITE_POSITION.X + ((SPRITE_DIMENTIONS.X / 2) * maths.cos(ANGLE_B))
	RIGHT_SIDE_Z = SPRITE_POSITION.Z + ((SPRITE_DIMENTIONS.X / 2) * maths.sin(ANGLE_A))

	return (
			VECTOR_3D(LEFT_SIDE_X, SPRITE_POSITION.Y, LEFT_SIDE_Z),
			VECTOR_3D(RIGHT_SIDE_X, SPRITE_POSITION.Y, RIGHT_SIDE_Z),
			VECTOR_3D(RIGHT_SIDE_X, SPRITE_POSITION.Y + SPRITE_DIMENTIONS.Y, RIGHT_SIDE_Z),
			VECTOR_3D(LEFT_SIDE_X, SPRITE_POSITION.Y + SPRITE_DIMENTIONS.Y, LEFT_SIDE_Z)
		)


def GET_CONFIGS():
	try:
		PREFERENCE_FILE = open("Prefs.txt", "r")
		PREFERENCE_DATA = PREFERENCE_FILE.readlines()
		PREFERENCES = {}
		
		for LINE in PREFERENCE_DATA:
			if LINE[0].strip() not in ("/", ""):
				P_LINE_DATA = (LINE.strip()).split(' = ')
				USER_CHOICE = P_LINE_DATA[1]
				
				try:
					try:
						CHOSEN_DATA = int(USER_CHOICE)
						
						if P_LINE_DATA[0] == "FPS_LIMIT":
							USER_CHOICE = CLAMP(USER_CHOICE, 1, 10000)
					
					except:
						CHOSEN_DATA = float(USER_CHOICE)
				
				except ValueError:
					if USER_CHOICE == "True":
						CHOSEN_DATA = True
					
					elif USER_CHOICE == "False":
						CHOSEN_DATA = False
					
					else:
						CHOSEN_DATA = USER_CHOICE

				PREFERENCES[P_LINE_DATA[0]] = CHOSEN_DATA

	except FileNotFoundError:
		PREFERENCES = {}

	DATA_PATH = GET_DATA_PATH()
	CONFIG_FILE = open(f"{DATA_PATH}\\config.dat", "r")
	CONFIG_DATA = CONFIG_FILE.readlines()
	global CONSTANTS
	CONSTANTS = {}
	
	for LINE in CONFIG_DATA:
		if LINE[0].strip() not in ("/", ""):
			C_LINE_DATA = (LINE.strip()).split(' = ')
			LISTED_CONSTANT = C_LINE_DATA[1]
			FILE_VECTOR = LISTED_CONSTANT[4:].split(', ')
			match LISTED_CONSTANT[:3]:
				case "rgba:":
					OUTPUT_CONSTANT = RGBA(FILE_VECTOR[0], FILE_VECTOR[1], FILE_VECTOR[2], FILE_VECTOR[3])

				case "v3:":
					OUTPUT_CONSTANT = VECTOR_3D(FILE_VECTOR[0], FILE_VECTOR[1], FILE_VECTOR[2])

				case "v2:":
					OUTPUT_CONSTANT = VECTOR_2D(FILE_VECTOR[0], FILE_VECTOR[1])
				
				case _:
					try:
						try:
							OUTPUT_CONSTANT = int(LISTED_CONSTANT)
							
							if C_LINE_DATA[0] == "FPS_LIMIT":
								LISTED_CONSTANT = CLAMP(LISTED_CONSTANT, 1, 10000)
						
						except:
							OUTPUT_CONSTANT = float(LISTED_CONSTANT)
					
					except ValueError:
						if LISTED_CONSTANT == "True":
							OUTPUT_CONSTANT = True
						
						elif LISTED_CONSTANT == "False":
							OUTPUT_CONSTANT = False
						
						else:
							OUTPUT_CONSTANT = LISTED_CONSTANT

			CONSTANTS[C_LINE_DATA[0]] = OUTPUT_CONSTANT
	
	try:
		if PREFERENCES["DEV_TEST"]:
			CONSTANTS["FORCE_GRAV"] = 0
	except KeyError:
		pass

	return PREFERENCES, CONSTANTS

def GET_GAME_DATA():
	#Gets the hostiles.dat and supplies.dat file data for use elsewhere.
	DATA_PATH = GET_DATA_PATH()
	HOSTILES, SUPPLIES, PROJECTILES = {}, {}, {}

	HOSTILES_FILE = open(f"{DATA_PATH}\\hostiles.dat", "r")
	SUPPLIES_FILE = open(f"{DATA_PATH}\\supplies.dat", "r")
	PROJECTILES_FILE = open(f"{DATA_PATH}\\projectiles.dat", "r")

	HOSTILES_DATA = HOSTILES_FILE.readlines()
	SUPPLIES_DATA = SUPPLIES_FILE.readlines()
	PROJECTILES_DATA = PROJECTILES_FILE.readlines()

	H_FORMATTING = ("float", "float", "hex", "list")#Max-Health, Speed, Weapon, Items-to-drop
	S_FORMATTING = ("hex", "int")#What-to-give, Quantity,
	P_FORMATTING = ("bool", "float")#Create-explosion, Strength

	for H_DATA, S_DATA, P_DATA in zip(HOSTILES_DATA, SUPPLIES_DATA, PROJECTILES_DATA):
		PROCESSED_H = PROCESS_LINE(H_DATA, H_FORMATTING)
		PROCESSED_S = PROCESS_LINE(S_DATA, S_FORMATTING)
		PROCESSED_P = PROCESS_LINE(P_DATA, P_FORMATTING)

		if PROCESSED_H is not None: HOSTILES[PROCESSED_H[0]] = PROCESSED_H[1:]
		if PROCESSED_S is not None: SUPPLIES[PROCESSED_S[0]] = PROCESSED_S[1:]
		if PROCESSED_P is not None: PROJECTILES[PROCESSED_P[0]] = PROCESSED_P[1:]

	HOSTILES_FILE.close()
	SUPPLIES_FILE.close()
	PROJECTILES_FILE.close()

	return HOSTILES, SUPPLIES, PROJECTILES

def PROCESS_LINE(LINE, FORMATTING):
	if LINE != "":
		if LINE[0] != "/":
			DATA = LINE.split(" | ")
			TYPE = DATA[0]
			MASS = DATA[2]
			TEXTURES = list(DATA[-1].split("/"))
			SIZE_RAW = DATA[1].split(", ")
			COLLISION_SIZE = VECTOR_3D(SIZE_RAW[0], SIZE_RAW[1], SIZE_RAW[2])
			OUT = [TYPE, COLLISION_SIZE, MASS]

			for FORM, INFO in zip(FORMATTING, DATA[3:-1]):
				match FORM:
					case "vect":
						FILE_VECTOR = INFO.split(', ')
						OUT.append(VECTOR_3D(round(float(FILE_VECTOR[0]), 8), round(float(FILE_VECTOR[1]), 8), round(float(FILE_VECTOR[2]), 8)))

					case "bool":
						BOOLEAN = INFO.split(".")
						for I, BOOL in enumerate(BOOLEAN):
							if BOOL == "T":
								BOOLEAN[I] = True
							elif BOOL == "F":
								BOOLEAN[I] = False
						OUT.append(BOOLEAN)

					case "rgba":
						FILE_VECTOR = INFO.split(', ')
						OUT.append(RGBA(round(float(FILE_VECTOR[0]), 8), round(float(FILE_VECTOR[1]), 8), round(float(FILE_VECTOR[2]), 8), round(float(FILE_VECTOR[2]), 8)))

					case "int":
						OUT.append(int(INFO))

					case "float":
						OUT.append(float(INFO))

					case "hex":
						OUT.append(int(INFO, 16))

					case "list":
						OUT.append(INFO.split(":"))

					case "str":
						OUT.append(INFO)

			LOADED_TEXTURES = []
			for TX in TEXTURES:
				pass#LOADED_TEXTURES.append(texture_load.TEXTURE_CACHE_MANAGER(TX))
			
			OUT.append(LOADED_TEXTURES)

			return OUT
	return None



def GET_DATA_PATH():
	#Path for the ..\\test4.2.2\\exct\\data\\.. data files.
	return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

def GET_GLSL_PATH():
	#Path for the ..\\test4.2.2\\exct\\glsl\\.. shader files.
	return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'glsl')

def PRINT_GRID(GRID): #Prints the contents of any array, list, grid, dictionary etc in helpful lines. Used for debugging.
	for ENTRY in GRID:
		print(ENTRY)

def TO_VECTOR_2D(LIST):
	return VECTOR_2D(LIST[0], LIST[1])

def TO_VECTOR_3D(LIST):
	return VECTOR_3D(LIST[0], LIST[1], LIST[2])




"""
Custom Classes, for objects and datatypes {O.O.P.};
- Static, Environmental objects [WORLD_OBJECT]'s children.
- Physics-based objects [PHYSICS_OBJECT]'s children.
- RGBA format and functions for colour manipulation.
- VECTOR_2D/VECTOR_3D and their related mathematical functions.
"""
#Parent Classes
class WORLD_OBJECT:
	def __init__(self, OBJECT_ID, POSITION, COLLISION, TEXTURE_INFO=None, NORMALS=None, BOUNDING_BOX=None):
		self.POSITION = POSITION
		self.COLLISION = bool(COLLISION)

		if COLLISION:
			self.BOUNDING_BOX = BOUNDING_BOX
			FINAL_NORMALS_LIST = []
			for NORMAL in NORMALS:
				FINAL_NORMALS_LIST.append(NORMAL.NORMALISE())
			self.NORMALS = tuple(FINAL_NORMALS_LIST)

		if OBJECT_ID is not None: self.ID = int(OBJECT_ID)

		if TEXTURE_INFO is not None:
			self.TEXTURE_INFO = TEXTURE_INFO

class PHYSICS_OBJECT:
	def __init__(self, OBJECT_ID, POSITION, ROTATION, NORMALS, BOUNDING_BOX, MASS, TEXTURE_INFO, LATERAL_VELOCITY=None):
		self.POSITION = POSITION
		if ROTATION is None: self.ROTATION = VECTOR_3D(0.0, 0.0, 0.0)
		else: self.ROTATION = ROTATION.RADIANS()
		self.MASS = float(MASS)
		self.COLLISION = True
		self.BOUNDING_BOX = BOUNDING_BOX
		self.NORMALS = tuple(NORMALS)
		self.ID = int(OBJECT_ID)
		self.TEXTURE_INFO = tuple(TEXTURE_INFO) if TEXTURE_INFO is not None else None

		if LATERAL_VELOCITY is not None:
			self.LATERAL_VELOCITY = VECTOR_3D(*LATERAL_VELOCITY)
		else:
			self.LATERAL_VELOCITY = VECTOR_3D(0.0, 0.0, 0.0)

		self.ROTATIONAL_VELOCITY = VECTOR_3D(0.0, 0.0, 0.0)
		self.PREVIOUS_COLLISION = False

class BOUNDING_BOX:
	def __init__(self, POSITION, OBJECT_POINTS):
		OFFSET = 1.0
		self.MIN_X = min(POINT.X for POINT in OBJECT_POINTS) - OFFSET
		self.MAX_X = max(POINT.X for POINT in OBJECT_POINTS) + OFFSET
		self.MIN_Y = min(POINT.Y for POINT in OBJECT_POINTS) - OFFSET
		self.MAX_Y = max(POINT.Y for POINT in OBJECT_POINTS) + OFFSET
		self.MIN_Z = min(POINT.Z for POINT in OBJECT_POINTS) - OFFSET
		self.MAX_Z = max(POINT.Z for POINT in OBJECT_POINTS) + OFFSET
		
		BOX_POINTS = FIND_CUBOID_POINTS(VECTOR_3D(self.MAX_X-self.MIN_X, self.MAX_Y-self.MIN_Y, self.MAX_Z-self.MIN_Z), POSITION)

		NORMALS = FIND_CUBOID_NORMALS(BOX_POINTS)
		self.POSITION = VECTOR_3D(*POSITION.TO_LIST())
		self.NORMALS = tuple(NORMALS)
		self.POINTS = BOX_POINTS




#Static Objects
class SCENE():
	def __init__(self, VOID_COLOUR, GRAVITY, AIR_RES_MULT):
		self.VOID = RGBA(VOID_COLOUR)
		self.GRAVITY = GRAVITY
		self.AIR_RES_MULT = AIR_RES_MULT

	def __repr__(self):
		return f"<SCENE: [VOID_COLOUR: {self.VOID} // GRAVITY: {self.GRAVITY} // AIR_RES_MULT: {AIR_RES_MULT}]>"


class TRI(WORLD_OBJECT):
	def __init__(self, ID, VERTICES, COLLISION, TEXTURE_COORDINATES):
		CENTROID = FIND_CENTROID(VERTICES)
		NORMAL = (VERTICES[0].CROSS(VERTICES[1]),) #Should be edges not vertices?
		BOUNDING_BOX_OBJ = BOUNDING_BOX(CENTROID, VERTICES)
		super().__init__(ID, CENTROID, COLLISION, TEXTURE_INFO=TEXTURE_COORDINATES, NORMALS=NORMAL, BOUNDING_BOX=BOUNDING_BOX_OBJ)

		self.POINTS = VERTICES

	def __repr__(self):
		if self.COLLISION:
			return f"<TRI: [CENTROID: {self.POSITION} // NORMAL: {self.NORMALS} // COLLISION: {self.COLLISION} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS}]>"
		else:
			return f"<TRI: [CENTROID: {self.POSITION} // COLLISION: {self.COLLISION} // VERTICES: {self.POINTS}]>"


class QUAD(WORLD_OBJECT):
	def __init__(self, ID, VERTICES, COLLISION, TEXTURE_COORDINATES):
		CENTROID = FIND_CENTROID(VERTICES)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(CENTROID, VERTICES)
		NORMALS = ((VERTICES[1] - VERTICES[0]).CROSS(VERTICES[2] - VERTICES[0]), (VERTICES[1] - VERTICES[3]).CROSS(VERTICES[2] - VERTICES[3]))
		super().__init__(ID, CENTROID, COLLISION, TEXTURE_INFO=TEXTURE_COORDINATES, NORMALS=NORMALS, BOUNDING_BOX=BOUNDING_BOX_OBJ)

		self.POINTS = VERTICES

	def __repr__(self):
		return f"<QUAD_STATIC: [CENTROID: {self.POSITION} // NORMALS: {self.NORMALS} // COLLISION: {self.COLLISION} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS}]>"


class CUBE_STATIC(WORLD_OBJECT):
	def __init__(self, ID, POSITION, DIMENTIONS, COLLISION, TEXTURE_INFO):
		POINTS = FIND_CUBOID_POINTS(DIMENTIONS, POSITION)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)
		super().__init__(ID, POSITION, COLLISION, TEXTURE_INFO=TEXTURE_INFO, NORMALS=NORMALS, BOUNDING_BOX=BOUNDING_BOX_OBJ)

		self.DIMENTIONS = DIMENTIONS
		self.POINTS = tuple(POINTS)

	def __repr__(self):
		return f"<CUBE_STATIC: [POSITION: {self.POSITION} // DIMENTIONS: {self.DIMENTIONS} // COLLISION: {self.COLLISION} // NORMALS: {self.NORMALS} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS}]>"


class SPRITE_STATIC(WORLD_OBJECT):
	def __init__(self, ID, POSITION, COLLISION_DIMENTIONS, COLLISION, TEXTURE_COORDINATES):
		POINTS = FIND_CUBOID_POINTS(COLLISION_DIMENTIONS, POSITION)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		super().__init__(ID, POSITION, COLLISION, TEXTURE_INFO=TEXTURE_COORDINATES, NORMALS=NORMALS, BOUNDING_BOX=BOUNDING_BOX_OBJ)

		AVG_X = (COLLISION_DIMENTIONS.X + COLLISION_DIMENTIONS.Z) / 2
		self.DIMENTIONS_2D = VECTOR_2D(AVG_X, COLLISION_DIMENTIONS.Y)

	def __repr__(self):
		return f"<SPRITE_STATIC: [POSITION: {self.POSITION} // NORMALS: {self.NORMALS} // COLLISION: {self.COLLISION} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS}]>"


class CUBE_PATH(WORLD_OBJECT):
	def __init__(self, ID, POSITION, DIMENTIONS, TEXTURE_DATA, MOVEMENT_VECTOR, SPEED, FLAG):
		POINTS = FIND_CUBOID_POINTS(DIMENTIONS, POSITION)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		super().__init__(ID, POSITION, True, TEXTURE_INFO=TEXTURE_DATA, NORMALS=NORMALS, BOUNDING_BOX=BOUNDING_BOX_OBJ)
		
		self.DIMENTIONS = DIMENTIONS
		self.MOVEMENT = MOVEMENT_VECTOR
		self.SPEED = SPEED
		self.FLAG = FLAG
		self.TRIGGERED = False

	def __repr__(self):
		return f"<CUBE_PATH: [CENTROID: {self.POSITION} // NORMALS: {self.NORMALS} // COLLISION: {self.COLLISION} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS} // MOTION: {self.MOVEMENT} // SPEED: {self.SPEED} // FLAG: {self.FLAG}]>"


class TRIGGER(WORLD_OBJECT):
	def __init__(self, ID, POSITION, DIMENTIONS, FLAG):
		POINTS = FIND_CUBOID_POINTS(DIMENTIONS, POSITION)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)
		super().__init__(ID, POSITION, True, BOUNDING_BOX=BOUNDING_BOX_OBJ)
		
		self.FLAG = FLAG
		self.TRIGGERED = False

	def __repr__(self):
		return f"<TRIGGER: [POSITION: {self.POSITION} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS} // FLAG: {self.FLAG}]>"


class INTERACTABLE(WORLD_OBJECT):
	def __init__(self, ID, VERTICES, COLLISION, TEXTURE_COORDINATES, FLAG):
		CENTROID = FIND_CENTROID(VERTICES)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(CENTROID, VERTICES)
		NORMALS = (VERTICES[0].CROSS(VERTICES[1]), VERTICES[2].CROSS(VERTICES[3]))
		super().__init__(ID, CENTROID, COLLISION, TEXTURE_INFO=TEXTURE_COORDINATES, NORMALS=NORMALS, BOUNDING_BOX=BOUNDING_BOX_OBJ)

		self.POINTS = VERTICES
		
		self.FLAG = FLAG
		self.TRIGGERED = False

	def __repr__(self):
		return f"<INTERACTABLE: [CENTROID: {self.POSITION} // NORMALS: {self.NORMALS} // COLLISION: {self.COLLISION} // BOUNDING_BOX: {self.BOUNDING_BOX} // VERTICES: {self.POINTS}]>"


class LIGHT(WORLD_OBJECT):
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
	def __init__(self, POSITION, SIZE, FORCE, STRENGTH, TEXTURE_INFO):
		POINTS = FIND_CUBOID_POINTS([SIZE, SIZE, SIZE], POSITION)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)

		super().__init__(-1, POSITION, True, TEXTURE_INFO=TEXTURE_INFO, NORMALS=NORMALS, BOUNDING_BOX=BOUNDING_BOX_OBJ)

		self.DIMENTIONS_2D = VECTOR_2D(*SIZE)
		self.DIMENTIONS_3D = VECTOR_3D(*SIZE)
		self.STRENGTH = STRENGTH
		self.PUSH_FORCE = FORCE
		self.POINTS = POINTS

	def __repr__(self):
		return f"<EXPLOSION: [POSITION: {self.POSITION} // DIMENTIONS_2D: {self.DIMENTIONS_2D} // DIMENTIONS_3D: {self.DIMENTIONS_3D} // STRENGTH: {self.STRENGH} // PUSH_FORCE: {self.PUSH_FORCE} // BOUNDING_BOX: {BOUNDING_BOX_OBJ} // VERTICES: {POINTS}]>"


class NPC_PATH_NODE(WORLD_OBJECT):
	def __init__(self, POSITION, FLAG, CONNECTIONS):
		super().__init__(None, POSITION, False)

		self.FLAG = FLAG
		self.CONNECTIONS = CONNECTIONS

	def __repr__(self):
		return f"<NPC_PATH_NODE: [POSITION: {self.POSITION} // FLAG: {self.FLAG} // CONNECTIONS: {CONNECTIONS}]>"







#Physics Objects
class CUBE_PHYSICS(PHYSICS_OBJECT):
	def __init__(self, ID, POSITION, DIMENTIONS, MASS, ROTATION, TEXTURE_INFO):
		POINTS = FIND_CUBOID_POINTS(DIMENTIONS, POSITION)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)

		super().__init__(ID, POSITION, ROTATION, NORMALS, BOUNDING_BOX_OBJ, MASS, TEXTURE_INFO)

		self.DIMENTIONS = DIMENTIONS
		self.POINTS = POINTS

	def __repr__(self):
		return f"<CUBE_PHYSICS: [POSITION: {self.POSITION} // ROTATION: {self.ROTATION} // DIMENTIONS: {self.DIMENTIONS} // MASS: {self.MASS} // POINTS: {self.POINTS} // LATERAL_VELOCITY: {self.LATERAL_VELOCITY} // ROTATIONAL_VELOCITY: {ROTATIONAL_VELOCITY}]>"


class ITEM(PHYSICS_OBJECT):
	def __init__(self, ID, POSITION, POP, TEXTURE_INFO, TYPE):
		_, SUPPLIES, _ = GET_GAME_DATA()
		TYPE_DATA = SUPPLIES[TYPE]
		MASS = TYPE_DATA[1]
		POINTS = FIND_CUBOID_POINTS(TYPE_DATA[0], POSITION)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)

		super().__init__(ID, POSITION, None, NORMALS, BOUNDING_BOX_OBJ, MASS, TEXTURE_INFO)

		if POP:
			#Whether or not the item should "pop" (mostly for items dropped by enemies)
			#Has a random direction and magnitude, within limits to make the item slightly "pop" in a direction on creation.
			MAGNITUDE = random.uniform(0.25, 0.75)
			ANGLE_X = maths.radians(random.randint(0, 360))
			ANGLE_Y = maths.radians(random.randint(0, 90))

			LATERAL_VELOCITY = VECTOR_3D(
				MAGNITUDE * maths.cos(ANGLE_Y) * maths.cos(ANGLE_X),
				MAGNITUDE * maths.cos(ANGLE_Y) * maths.sin(ANGLE_X),
				MAGNITUDE * maths.sin(ANGLE_Y)
			)

		else:
			LATERAL_VELOCITY = VECTOR_3D(0.0, 0.0, 0.0)

		self.TYPE = TYPE
		self.DIMENTIONS_2D = VECTOR_2D((TYPE_DATA[0].X + TYPE_DATA[0].Z) / 2, TYPE_DATA[0].Y)
		self.DIMENTIONS_3D = TYPE_DATA[0]
		self.POINTS = POINTS
		self.LATERAL_VELOCITY = LATERAL_VELOCITY
		self.QUANTITY = TYPE_DATA[3]
		self.EMPTY = False

	def __repr__(self):
		return f"<ITEM: [POSITION: {self.POSITION} // ITEM_TYPE: {self.TYPE} // DIMENTIONS_2D: {self.DIMENTIONS_2D} // DIMENTIONS_3D: {self.DIMENTIONS_3D} // POINTS: {self.POINTS} // LATERAL_VELOCITY: {self.LATERAL_VELOCITY}]>"

	def TAKE(self, AMOUNT_TO_TAKE):
		self.QUANTITY -= AMOUNT_TO_TAKE
		if self.QUANTITY <= 0:
			self.EMPTY = True
		return self


class ENEMY(PHYSICS_OBJECT):
	def __init__(self, ID, POSITION, TYPE, ROTATION):
		HOSTILES, _, _ = GET_GAME_DATA()
		TYPE_DATA = HOSTILES[TYPE]
		POINTS = FIND_CUBOID_POINTS(TYPE_DATA[0], POSITION)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)
		MASS = TYPE_DATA[1]

		super().__init__(ID, POSITION, ROTATION, NORMALS, BOUNDING_BOX_OBJ, MASS, None)

		self.DIMENTIONS_2D = VECTOR_2D((TYPE_DATA[0].X + TYPE_DATA[0].Z) / 2, TYPE_DATA[0].Y)
		self.POINTS = POINTS
		self.TYPE = TYPE
		self.MAX_HEALTH = TYPE_DATA[3]
		self.HEALTH = TYPE_DATA[3]
		self.HELD_ITEM = TYPE_DATA[4]
		self.LOOT = TYPE_DATA[5]
		self.ALIVE = True

	def __repr__(self):
		return f"<ENEMY: [POSITION: {self.POSITION} // ENEMY_TYPE: {self.TYPE} // DIMENTIONS_2D: {self.DIMENTIONS_2D} // POINTS: {self.POINTS} // LATERAL_VELOCITY: {self.LATERAL_VELOCITY} // ATTACK_TYPE: {self.ATTACK_TYPE} // ATTACK_STRENGTH: {self.ATTACK_STRENGTH} // HEALTH: {self.HEALTH} // ALIVE: {self.ALIVE}]>"

	def HURT(self, DAMAGE):
		self.HEALTH = CLAMP(self.HEALTH - DAMAGE, 0, self.MAX_HEALTH)
		if self.HEALTH <= 0:
			self.ALIVE = False
		return self


class PROJECTILE(PHYSICS_OBJECT):
	def __init__(self, POSITION, MASS, FIRED_VELOCITY, TYPE, TEXTURE_INFO):
		TYPE_DATA = PROJECTILES[hex(TYPE)]
		POINTS = FIND_CUBOID_POINTS(TYPE_DATA["Dimentions"], POSITION)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)

		super().__init__(ID, POSITION, None, None, BOUNDING_BOX_OBJ, MASS, TEXTURE_INFO, LATERAL_VELOCITY = FIRED_VELOCITY)

		AVG_X = (TYPE_DATA["Dimentions"][0] + TYPE_DATA["Dimentions"][2]) / 2
		self.DIMENTIONS_2D = VECTOR_2D(AVG_X, TYPE_DATA["Dimentions"][1])
		self.POINTS = POINTS
		self.TYPE = hex(TYPE)
		self.DAMAGE_TYPE = TYPE_DATA["Damage Type"]
		self.DAMAGE_STRENGTH = TYPE_DATA["Damage Strength"]
		self.CREATE_EXPLOSION = bool(TYPE_DATA["Create Explosion"])

	def __repr__(self):
		return f"<PROJECTILE: [POSITION: {self.POSITION} // PROJECTILE_TYPE: {self.TYPE} // DIMENTIONS_2D: {self.DIMENTIONS_2D} // POINTS: {self.POINTS} // LATERAL_VELOCITY: {self.LATERAL_VELOCITY} // DAMAGE_TYPE: {self.DAMAGE_TYPE} // DAMAGE_STRENGTH: {self.DAMAGE_STRENGTH} // CREATE_EXPLOSION: {self.CREATE_EXPLOSION}]>"


class PLAYER(PHYSICS_OBJECT):
	def __init__(self, ID, POSITION, ROTATION, ITEMS):
		COLLISION_CUBOID = CONSTANTS["PLAYER_COLLISION_CUBOID"]
		POINTS = FIND_CUBOID_POINTS(COLLISION_CUBOID, POSITION)
		NORMALS = FIND_CUBOID_NORMALS(POINTS)
		BOUNDING_BOX_OBJ = BOUNDING_BOX(POSITION, POINTS)

		super().__init__(ID, POSITION, ROTATION, NORMALS, BOUNDING_BOX_OBJ, CONSTANTS["PLAYER_MASS"], None)

		self.MAX_HEALTH = CONSTANTS["PLAYER_MAX_HEALTH"]
		self.HEALTH = CONSTANTS["PLAYER_MAX_HEALTH"]
		self.ITEMS = ITEMS
		self.AMMO = [0 for _ in range(len(ITEMS))]
		self.ALIVE = True

	def __repr__(self):
		return f"<PLAYER: [POSITION: {self.POSITION} // LATERAL_VELOCITY: {self.LATERAL_VELOCITY} // ITEMS: {self.ITEMS} // AMMUNITION: {self.AMMO} // HEALTH: {self.HEALTH} // ALIVE: {self.ALIVE}]>"

	def HURT(self, DAMAGE):
		self.HEALTH = CLAMP(self.HEALTH - DAMAGE, 0, self.MAX_HEALTH)
		if self.HEALTH <= 0:
			self.ALIVE = False
		return self






"""
Formatting;
- RGBA
- VECTOR_2D
- VECTOR_3D
"""
class RGBA:
	"""
	RGB Colour type.
	Has 4 values (RGBA)
	"""
	def __init__(self, R, G, B, A, RANGE=(0, 255)): #Formatting as [R, G, B, A]
		self.R = round(CLAMP(R, RANGE[0], RANGE[1]), 8)
		self.G = round(CLAMP(G, RANGE[0], RANGE[1]), 8)
		self.B = round(CLAMP(B, RANGE[0], RANGE[1]), 8)
		self.A = round(CLAMP(A, RANGE[0], RANGE[1]), 8)

	def __add__(self, OTHER):
		self.R += OTHER.R
		self.G += OTHER.G
		self.B += OTHER.B
		self.A += OTHER.A
		return self

	def __sub__(self, OTHER):
		self.R -= OTHER.R
		self.G -= OTHER.G
		self.B -= OTHER.B
		self.A -= OTHER.A
		return self

	def __mul__(self, OTHER):
		if type(OTHER) == RGBA:
			self_DECIMAL = self.DECIMAL()
			OTHER_DECIMAL = OTHER.DECIMAL()
			self.R = self_DECIMAL[0] * OTHER_DECIMAL[0]
			self.G = self_DECIMAL[1] * OTHER_DECIMAL[1]
			self.B = self_DECIMAL[2] * OTHER_DECIMAL[2]
			self.A = self_DECIMAL[3] * OTHER_DECIMAL[3]

			return self * 255

		elif type(OTHER) in [int, float]:
			self.R *= OTHER
			self.G *= OTHER
			self.B *= OTHER
			self.A *= OTHER
			return self

		else:
			raise TypeError(f"Cannot multiply type {type(OTHER)} and RGBA.")

	def __rmul__(self, OTHER):
		return self * OTHER

	def __truediv__(self, SCALAR):
		if type(OTHER) == RGBA:
			self.R /= OTHER.R
			self.G /= OTHER.G
			self.B /= OTHER.B
			self.A /= OTHER.A
			return self

		elif type(OTHER) in [int, float]:
			self.R /= OTHER
			self.G /= OTHER
			self.B /= OTHER
			self.A /= OTHER
			return self

		else:
			raise TypeError(f"Cannot divide type [{type(OTHER)}] and RGBA.")

	def __iadd__(self, OTHER):
		self.X += OTHER.X
		self.Y += OTHER.Y
		self.Z += OTHER.Z
		return self

	def __isub__(self, OTHER):
		self.R -= OTHER.R
		self.G -= OTHER.G
		self.B -= OTHER.B
		self.A -= OTHER.A
		return self

	def __eq__(self, OTHER):
		return self.R == OTHER.R and self.G == OTHER.G and self.B == OTHER.B and self.A == OTHER.B

	def __ne__(self, OTHER):
		return not self == OTHER
	
	def __repr__(self):
		return f"<RGBA: [{self.R}, {self.G}, {self.B}, {self.A}]>"

	def TO_DECIMAL(self, CURRENT_RANGE=(0, 255)):
		return RGBA(
			(self.R - CURRENT_RANGE[0]) / CURRENT_RANGE[1],
			(self.G - CURRENT_RANGE[0]) / CURRENT_RANGE[1],
			(self.B - CURRENT_RANGE[0]) / CURRENT_RANGE[1],
			(self.A - CURRENT_RANGE[0]) / CURRENT_RANGE[1],
			RANGE = (0.0, 1.0)
		)

	def TO_LIST(self, CURRENT_RANGE=(0, 255)):
		return [
			(self.R - CURRENT_RANGE[0]) / CURRENT_RANGE[1],
			(self.G - CURRENT_RANGE[0]) / CURRENT_RANGE[1],
			(self.B - CURRENT_RANGE[0]) / CURRENT_RANGE[1],
			(self.A - CURRENT_RANGE[0]) / CURRENT_RANGE[1]
		]

	def CONVERT_TO_PYRR_VECTOR4(self):
		return Vector4(self.TO_LIST())

	def CONVERT_TO_GLM_VEC4(self):
		return glm.vec4(self.R, self.G, self.B, self.A)



class VECTOR_2D:
	"""
	Custom 2D Vector type.
	Has X and Y coordinate.
	Allows for many basic and mid-level operations.
	"""
	def __init__(self, X, Y): #Formatting as [X, Y]
		self.X = float(X)
		self.Y = float(Y)

	def __add__(self, OTHER): #Add self and OTHER // {self} + {OTHER}
		return VECTOR_2D(self.X + OTHER.X, self.Y + OTHER.Y)

	def __sub__(self, OTHER): #Subtract OTHER from self // {self} - {OTHER}
		return VECTOR_2D(self.X - OTHER.X, self.Y - OTHER.Y)

	def __mul__(self, SCALAR): #Multiply self by OTHER // {self} * {OTHER}
		return VECTOR_2D(self.X * SCALAR, self.Y * SCALAR)

	def __rmul__(self, SCALAR): #Multiply OTHER by self // {OTHER} * {self}
		return self * SCALAR

	def __truediv__(self, SCALAR): #Divide self by SCALAR // {self} / {SCALAR}
		return VECTOR_2D(self.X / SCALAR, self.Y / SCALAR)

	def __iadd__(self, OTHER):
		self.X += OTHER.X
		self.Y += OTHER.Y
		self.Z += OTHER.Z
		return self

	def __isub__(self, OTHER):
		self.X -= OTHER.X
		self.Y -= OTHER.Y
		self.Z -= OTHER.Z
		return self

	def __str__(self): #String representation // str({self})
		return f"<VECTOR_2D: ({self.X}, {self.Y})>"

	def __abs__(self): #Magnitude of self // abs({self})
		return (self.X ** 2 + self.Y ** 2) ** 0.5

	def __lt__(self, OTHER): #self Less Than OTHER // {self} < {OTHER}
		return self.__abs__() < OTHER.__abs__()

	def __le__(self, OTHER): #self Less Than or Equal To OTHER // {self} <= {OTHER}
		return self.__abs__() <= OTHER.__abs__()

	def __gt__(self, OTHER): #self Greater Than OTHER // {self} > {OTHER}
		return self.__abs() > OTHER.__abs__()

	def __ge__(self, OTHER): #self Greater Than or Equal To OTHER // {self} >= {OTHER}
		return self.__abs__ >= OTHER.__abs__()

	def __eq__(self, OTHER): #self perfectly equal to OTHER // {self} == {OTHER}
		return self.X == OTHER.X and self.Y == OTHER.Y

	def __ne__(self, OTHER): #self not perfectly equal to OTHER // {self} != {OTHER}
		return self.X != OTHER.X and self.Y != OTHER.Y

	def __repr__(self):
		return f"<VECTOR_2D: [{self.X}, {self.Y}]>"

	def NORMALISE(self): #Normalise self // {self}.NORMALISE()
		MAGNITUDE = self.__abs__()
		if MAGNITUDE != 0:
			return self.__truediv__(MAGNITUDE)
		return VECTOR_2D(0.0, 0.0, 0.0)

	def DOT(self, OTHER): #Dot product of self and OTHER // {self}.DOT({OTHER})
		return self.X * OTHER.X + self.Y + OTHER.Y

	def CROSS(self, OTHER): #Cross product of self and OTHER // {self}.CROSS({OTHER})
		CROSS_MAGNITUDE = maths.abs(self.X * OTHER.Y - self.Y * OTHER.X)
		return maths.degrees(maths.asin(CROSS_MAGNITUDE / (abs(self) * abs(OTHER)))) #Needs some fixes

	def PROJECT(self, OTHER): #Project point (OTHER) onto axis (self) // {AXIS}.PROJECT({POINT})
		DOT_PRODUCTS = DOT(OTHER, self)
		return [min(DOT_PRODUCTS), max(DOT_PRODUCTS)]

	def IN_LIST(self, OTHER): #If self in OTHER (list) // {self}.IN_LIST({OTHER})
		for ITEM in OTHER:
			if self == ITEM:
				return True
		return False

	def TO_LIST(self):
		return [self.X, self.Y]

	def RADIANS(self):
		return VECTOR_3D(maths.radians(self.X), maths.radians(self.Y))

	def CLAMP(self, X_BOUNDS=None, Y_BOUNDS=None):
		if X_BOUNDS is not None:
			self.X = CLAMP(self.X, X_BOUNDS[0], X_BOUNDS[1])
		if Y_BOUNDS is not None:
			self.Y = CLAMP(self.Y, Y_BOUNDS[0], Y_BOUNDS[1])
		return self

	def PRINT(self):
		print(f"<{self.X}, {self.Y}>")



class VECTOR_3D:
	"""
	Custom 3D Vector type.
	Has X, Y and Z coordinate.
	Allows for many basic and mid-level operations.
	"""
	def __init__(self, X, Y, Z): #Formatting as [X, Y, Z]
		self.X = float(X)
		self.Y = float(Y)
		self.Z = float(Z)

	def __add__(self, OTHER): #Add self and OTHER // {self} + {OTHER}
		return VECTOR_3D(self.X + OTHER.X, self.Y + OTHER.Y, self.Z + OTHER.Z)

	def __sub__(self, OTHER): #Subtract OTHER from self // {self} - {OTHER}
		return VECTOR_3D(self.X - OTHER.X, self.Y - OTHER.Y, self.Z - OTHER.Z)

	def __mul__(self, OTHER): #Multiply self by OTHER // {self} * {OTHER}
		if type(OTHER) == VECTOR_3D:
			return VECTOR_3D(self.X * OTHER.X, self.Y * OTHER.Y, self.Z * OTHER.Z)
		else:
			return VECTOR_3D(self.X * OTHER, self.Y * OTHER, self.Z * OTHER)

	def __rmul__(self, OTHER): #Multiply OTHER by self // {OTHER} * {self}
		return self.__mul__(OTHER)

	def __truediv__(self, SCALAR): #Divide self by SCALAR // {self} / {SCALAR}
		return VECTOR_3D(self.X / SCALAR, self.Y / SCALAR, self.Z / SCALAR)

	def __str__(self): #String representation // str({self})
		return f"<VECTOR_3D: ({self.X}, {self.Y}, {self.Z})>"

	def __abs__(self): #Magnitude of self // abs({self})
		return (self.X ** 2 + self.Y ** 2 + self.Z ** 2) ** 0.5

	def __lt__(self, OTHER): #self Less Than OTHER // {self} < {OTHER}
		return self.__abs__() < OTHER.__abs__()

	def __le__(self, OTHER): #self Less Than or Equal To OTHER // {self} <= {OTHER}
		return self.__abs__() <= OTHER.__abs__()

	def __gt__(self, OTHER): #self Greater Than OTHER // {self} > {OTHER}
		return self.__abs() > OTHER.__abs__()

	def __ge__(self, OTHER): #self Greater Than or Equal To OTHER // {self} >= {OTHER}
		return self.__abs__ >= OTHER.__abs__()

	def __eq__(self, OTHER): #self perfectly equal to OTHER // {self} == {OTHER}
		return self.X == OTHER.X and self.Y == OTHER.Y and self.Z == OTHER.Z

	def __ne__(self, OTHER): #self not perfectly equal to OTHER // {self} != {OTHER}
		return self.X != OTHER.X and self.Y != OTHER.Y and self.Z != OTHER.Z

	def __repr__(self):
		return f"<VECTOR_3D: [{self.X}, {self.Y}, {self.Z}]>"

	def NORMALISE(self): #Normalise self // {self}.NORMALISE()
		MAGNITUDE = self.__abs__()
		if MAGNITUDE != 0:
			return self.__truediv__(MAGNITUDE)
		return VECTOR_3D(0.0, 0.0, 0.0)

	def DOT(self, OTHER): #Dot product of self and OTHER // {self}.DOT({OTHER})
		return (self.X * OTHER.X) + (self.Y * OTHER.Y) + (self.Z * OTHER.Z)

	def CROSS(self, OTHER): #Cross product of self and OTHER // {self}.CROSS({OTHER})
		return VECTOR_3D(
				self.Y * OTHER.Z - self.Z * OTHER.Y,
				self.Z * OTHER.X - self.X * OTHER.Z,
				self.X * OTHER.Y - self.Y * OTHER.X
			)

	def PROJECT(self, OTHER): #Project point (OTHER) onto axis (self) // {AXIS}.PROJECT({POINT})
		DOT_PRODUCTS = []
		for POINT in OTHER:
			DOT_PRODUCTS.append(self.DOT(POINT))
		return [min(DOT_PRODUCTS), max(DOT_PRODUCTS)]

	def IN_LIST(self, OTHER): #If self in OTHER (list) // {self}.IN_LIST({OTHER})
		for ITEM in OTHER:
			if self == ITEM:
				return True
		return False

	def DISTANCE(self, OTHER):
		return ((self.X - OTHER.X) ** 2 + (self.Y - OTHER.Y) ** 2 + (self.Z - OTHER.Z) ** 2) ** 0.5

	def TO_LIST(self):
		return [self.X, self.Y, self.Z]

	def RADIANS(self):
		return VECTOR_3D(maths.radians(self.X), maths.radians(self.Y), maths.radians(self.Z))

	def CLAMP(self, X_BOUNDS=None, Y_BOUNDS=None, Z_BOUNDS=None):
		if X_BOUNDS is not None:
			self.X = CLAMP(self.X, X_BOUNDS[0], X_BOUNDS[1])
		if Y_BOUNDS is not None:
			self.Y = CLAMP(self.Y, Y_BOUNDS[0], Y_BOUNDS[1])
		if Z_BOUNDS is not None:
			self.Z = CLAMP(self.Z, Z_BOUNDS[0], Z_BOUNDS[1])
		return self
	
	def PRINT(self):
		print(f"<{self.X}, {self.Y}, {self.Z}>")

	def CONVERT_TO_PYRR_VECTOR3(self):
		return Vector3(self.TO_LIST())

	def CONVERT_TO_GLM_VEC3(self):
		return glm.vec3(self.X, self.Y, self.Z)
