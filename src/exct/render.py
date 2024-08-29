"""
[render.py]
Renders different objects with data, such as a list of planes or a sphere from associated data
Can take a long list of objects and draw them properly, textured too.

______________________
Importing other files;
-log.py
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
	from exct import ui, utils
	from imgs import texture_load
	from exct.utils import *

except ImportError:
	log.ERROR("render.py", "Initial imports failed.")

log.REPORT_IMPORT("render.py")
PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS


#General render related functions


def GL_ERRORCHECK(DISPLAY_RESULT=False):
	#Checks for any errors with OpenGL, and either raises an exception, or reports back no issues. (used for debugging)
	ERROR = glGetError()
	if ERROR != GL_NO_ERROR:
		RESULT = f"OpenGL ERROR:, {ERROR}"
		print(RESULT)
		log.ERROR("render.py", RESULT)

	elif DISPLAY_RESULT:
		print("OpenGL ERROR: None")



def GET_TEXTURE_DATA(TEXTURE, RESOLUTION, TYPE, MIN_DISTANCE=0.0, MAX_DISTANCE=1.0):
	#Gets the data from a texture as a NumPy array.
	glBindTexture(GL_TEXTURE_2D, TEXTURE)
	DATA = None
	PROCESSED_DATA = None

	match TYPE:
		case "DEPTH":
			#Retrieve the depth data as a float.
			DATA = glGetTexImage(GL_TEXTURE_2D, 0, GL_RED, GL_FLOAT)
			if DATA is None:
				raise ValueError("[ERROR] // Failed to retrieve depth texture data")

			#Convert the byte data to a numpy array
			DATA = NP.frombuffer(DATA, dtype=NP.float32).reshape(int(RESOLUTION.Y), int(RESOLUTION.X))

			#Clip the depth values to the min/max depth values.
			DEPTH_MIN = NP.clip(NP.min(DATA), MIN_DISTANCE, MAX_DISTANCE)
			DEPTH_MAX = NP.clip(NP.max(DATA), MIN_DISTANCE, MAX_DISTANCE)

			if DEPTH_MIN == DEPTH_MAX:
				PROCESSED_DATA = NP.zeros_like(DATA)
			else:
				PROCESSED_DATA = DATA

		case "COLOUR":
			#Retrieve the color data as a set of 4 floats.
			DATA = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_FLOAT)
			if DATA is None:
				raise ValueError("[ERROR] // Failed to retrieve color texture data")

			#Convert the byte data to a NumPy array
			DATA = NP.frombuffer(DATA, dtype=NP.float32)
			
			#Reshape the data to the expected dimensions
			PROCESSED_DATA = DATA.reshape((int(RESOLUTION.Y), int(RESOLUTION.X), 4))

		case _:
			#If the type is not supported, raise an error.
			raise TypeError(f"Map type {TYPE} is not recognised. Please choose from;\nDEPTH\nCOLOUR")


	glBindTexture(GL_TEXTURE_2D, 0)


	#Processing any issues in the data
	if PROCESSED_DATA is None:
		raise ValueError("[ERROR] // Failed to process texture data")

	if NP.any(NP.isnan(PROCESSED_DATA)):
		raise ValueError("[WARNING] // NaN values found in texture data; Issues may ensue.")
		PROCESSED_DATA = NP.nan_to_num(PROCESSED_DATA)


	#The depth data must be recorded as GL_RGB formatted data, and it is currenly a list of GL_RED data. Stack to become GL_RGB.
	if TYPE == "DEPTH":
		PROCESSED_DATA = NP.stack((PROCESSED_DATA,) * 3, axis=-1)
		
	return PROCESSED_DATA





def CREATE_TEXTURE_FROM_DATA(DATA, GL_TYPE=GL_RGB, FILTER=GL_LINEAR, DATA_TYPE=GL_UNSIGNED_BYTE):
	#Creates an OpenGL texture from a NumPy array of colour values (opposite of GET_TEXTURE_DATA())
	TEXTURE_ID = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, TEXTURE_ID)

	#Set texture parameters.
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, FILTER)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, FILTER)


	#Checks and validations before creating texture;
	#Ensure that the input data is a NumPy array
	if not isinstance(DATA, NP.ndarray):
		raise ValueError("DATA must be a NumPy array.")
	
	#Ensure that the input data is the correct format
	if DATA.dtype not in [NP.uint8, NP.float32]:
		raise ValueError("DATA must be of type np.uint8 or np.float32.")

	#Adjust the OpenGL data type based on the NumPy data type
	match DATA.dtype:
		case NP.uint8:
			DATA_TYPE = GL_UNSIGNED_BYTE
			INTERNAL_FORMAT = GL_TYPE

		case NP.float32:
			DATA_TYPE = GL_FLOAT
			if GL_TYPE == GL_RGB:
				INTERNAL_FORMAT = GL_RGB32F

			elif GL_TYPE == GL_RGBA:
				INTERNAL_FORMAT = GL_RGBA32F

			else:
				raise ValueError(f"Cannot use given GL_TYPE [{GL_TYPE}] with GL_FLOAT data.")


	#Validate the shape of the data array can be converted to GL_RGB or GL_RGBA
	if DATA.ndim not in [3, 4] or DATA.shape[2] not in [3, 4]:
		raise ValueError("DATA must be a 3D array with 3 or 4 components.")


	#Upload the texture data to the GPU, to become an OpenGL texture.
	glTexImage2D(GL_TEXTURE_2D, 0, INTERNAL_FORMAT, DATA.shape[1], DATA.shape[0], 0, GL_TYPE, DATA_TYPE, DATA)
	glBindTexture(GL_TEXTURE_2D, 0)

	return TEXTURE_ID


def CALC_VIEW_MATRIX(CAMERA_POSITION, CAMERA_ROTATION):
	#Calculates a given view matrix, based on the current position and a 2D rotation vector in radians. (applies X rotation, THEN Y)
	SIN_X = maths.sin(CAMERA_ROTATION.X)
	COS_X = maths.cos(CAMERA_ROTATION.X)
	SIN_Y = -maths.sin(CAMERA_ROTATION.Y)
	COS_Y = -maths.cos(CAMERA_ROTATION.Y)

	FORWARD = Vector3([
		COS_Y * COS_X,
		SIN_Y,
		COS_Y * SIN_X
	])
	
	RIGHT = Vector3([
		-SIN_X,
		0,
		COS_X
	])

	UPWARD = FORWARD.cross(RIGHT)
	PYRR_CAMERA_POSITION = CAMERA_POSITION.CONVERT_TO_PYRR_VECTOR3()
	LOOK_AT = PYRR_CAMERA_POSITION + FORWARD

	VIEW_MATRIX = Matrix44.look_at(
		eye=PYRR_CAMERA_POSITION,
		target=LOOK_AT,
		up=UPWARD
	)

	return VIEW_MATRIX, LOOK_AT



def CALC_SPRITE_POINTS(SPRITE_POSITION, PLAYER_POSITION, SPRITE_DIMENTIONS):
	#Calculates the vertices of a sprite based on its position relative to the player, so the sprite always faces the player.
	OPPOSITE = SPRITE_POSITION.Z - PLAYER_POSITION.Z
	ADJACENT = SPRITE_POSITION.X - PLAYER_POSITION.X
	
	PLAYER_SPRITE_ANGLE = -1 * maths.atan2(OPPOSITE, ADJACENT)
	ANGLE_A = PLAYER_SPRITE_ANGLE + utils.πDIV2 #Rotate 90* (π/2 rads) ahead.
	ANGLE_B = PLAYER_SPRITE_ANGLE - utils.πDIV2 #Rotate 90* (π/2 rads) behind.
	
	#Sprite's left side coordinate values.
	LEFT_SIDE_X = SPRITE_POSITION.X + ((SPRITE_DIMENTIONS.X / 2) * maths.cos(ANGLE_A))
	LEFT_SIDE_Z = SPRITE_POSITION.Z + ((SPRITE_DIMENTIONS.X / 2) * maths.sin(ANGLE_B))

	#Sprite#s right side coordinate values.
	RIGHT_SIDE_X = SPRITE_POSITION.X + ((SPRITE_DIMENTIONS.X / 2) * maths.cos(ANGLE_B))
	RIGHT_SIDE_Z = SPRITE_POSITION.Z + ((SPRITE_DIMENTIONS.X / 2) * maths.sin(ANGLE_A))

	#Final sprite vertices.
	return (
			VECTOR_3D(LEFT_SIDE_X, SPRITE_POSITION.Y, LEFT_SIDE_Z),
			VECTOR_3D(RIGHT_SIDE_X, SPRITE_POSITION.Y, RIGHT_SIDE_Z),
			VECTOR_3D(RIGHT_SIDE_X, SPRITE_POSITION.Y + SPRITE_DIMENTIONS.Y, RIGHT_SIDE_Z),
			VECTOR_3D(LEFT_SIDE_X, SPRITE_POSITION.Y + SPRITE_DIMENTIONS.Y, LEFT_SIDE_Z)
		)



def SET_PYGAME_CONTEXT(SHEET_NAME):
	#Sets the PG context to the current PG display. Takes a sheet for the texture to render, which will inevitably be retrieved from texture_load.SHEET_CACHE.
	DISPLAY_RESOLUTION = CONSTANTS["DISPLAY_RESOLUTION"]
	RENDER_RESOLUTION = CONSTANTS["RENDER_RESOLUTION"]

	PG.display.gl_set_attribute(PG.GL_CONTEXT_MAJOR_VERSION, 3)
	PG.display.gl_set_attribute(PG.GL_CONTEXT_MINOR_VERSION, 3)
	PG.display.gl_set_attribute(PG.GL_CONTEXT_PROFILE_MASK, PG.GL_CONTEXT_PROFILE_CORE)



	#Reload all of the VAO/FBO data surrounding the UI quad and the scene data to be within this PG context.		
	SCENE_SHADER, QUAD_SHADER = SHADER_INIT(SCENE=True, QUAD=True)
	VAO_QUAD, VAO_UI, FBO_SCENE, TCB_SCENE = FBO_QUAD_INIT(RENDER_RESOLUTION)

	CURRENT_SHEET_ID = texture_load.LOAD_SHEET(SHEET_NAME, SHEET_LIST={})

	#OpenGL attributes
	VAO_SCENE, VBO_SCENE, EBO_SCENE = BUFFERS_INIT()
	glEnable(GL_DEPTH_TEST)
	glDepthFunc(GL_LESS)
	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
	if CONSTANTS["FACE_CULLING"]: #Only culls faces if the prefs file states it should, mostly for debugging and to help with scene designing.
		glEnable(GL_CULL_FACE)
		glCullFace(GL_BACK)
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
	gluPerspective(PREFERENCES["FOV"], DISPLAY_RESOLUTION.X / DISPLAY_RESOLUTION.Y, CONSTANTS["MIN_VIEW_DIST"], CONSTANTS["MAX_VIEW_DIST"])  # Example parameters
	glMatrixMode(GL_MODELVIEW)
	MODEL_MATRIX = Matrix44.identity()
	glLoadIdentity()
	

	#Recalculate the Proj. Matrix.
	PROJECTION_MATRIX = Matrix44.perspective_projection(
		PREFERENCES["FOV"],
		(DISPLAY_RESOLUTION.X / DISPLAY_RESOLUTION.Y),
		CONSTANTS["MIN_VIEW_DIST"],
		CONSTANTS["MAX_VIEW_DIST"]
	)

	return (SCENE_SHADER, QUAD_SHADER), (VAO_QUAD, VAO_UI, FBO_SCENE, TCB_SCENE), CURRENT_SHEET_ID, (VAO_SCENE, VBO_SCENE, EBO_SCENE), (MODEL_MATRIX, PROJECTION_MATRIX)




def SURFACE_TO_TEXTURE(SURFACE, RESOLUTION):
	#Converts a PG surface's data into an OpenGL texture. Used for the UI conversion.
	SURFACE_DATA = PG.image.tostring(SURFACE, "RGBA", 1)
	
	FINAL_ID = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, FINAL_ID)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, RESOLUTION.X, RESOLUTION.Y, 0, GL_RGBA, GL_UNSIGNED_BYTE, SURFACE_DATA)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glBindTexture(GL_TEXTURE_2D, 0)
	del SURFACE_DATA
	
	return FINAL_ID


def SAVE_MAP(RESOLUTION, MAP, FILE_NAME, MAP_TYPE, MIN_DISTANCE=0.0, MAX_DISTANCE=1.0, DEBUG=False, ZIP=False, ZIP_PATH=""):
	"""
	Allows you to save maps of types;
	> Colour (RGB)
	> Colour (RGBA)
	> Depth
	> Normals
	...To an image file for debugging, or other usages like screenshots.
	Can also be saved in a .zip file, if needed.
	"""
	glBindTexture(GL_TEXTURE_2D, MAP)

	if ZIP: BUFFER = io.BytesIO()
	
	match MAP_TYPE:
		case "DEPTH":
			#Depth maps. They use the same colour data for R, G and B so GL_RED works fine here.
			DATA = glGetTexImage(GL_TEXTURE_2D, 0, GL_RED, GL_FLOAT)
			DATA = NP.frombuffer(DATA, dtype=NP.float32).reshape(int(RESOLUTION.Y), int(RESOLUTION.X))
			DATA = NP.flipud(DATA)
			if DEBUG: print("Depth data before normalization:\n", DATA)

			# Normalize depth data and ensure no NaN values
			DEPTH_MIN = utils.CLAMP(NP.min(DATA), MIN_DISTANCE, MAX_DISTANCE)
			DEPTH_MAX = utils.CLAMP(NP.max(DATA), MIN_DISTANCE, MAX_DISTANCE)
			if DEBUG: print(f"Depth range: min={DEPTH_MIN}, max={DEPTH_MAX}")
			if DEPTH_MIN == DEPTH_MAX:
				NORMALISED_DATA = NP.zeros_like(DATA)
			else:
				NORMALISED_DATA = (DATA - DEPTH_MIN) / (DEPTH_MAX - DEPTH_MIN + 1e-7)
				if DEBUG: print(NORMALISED_DATA)

			if NP.any(NP.isnan(NORMALISED_DATA)):
				raise ValueError("[WARNING] // NaN values found in depth data; Issues may ensue.")
				NORMALISED_DATA = NP.nan_to_num(NORMALISED_DATA)
			
			IMAGE = Image.fromarray((NORMALISED_DATA * 255).astype(NP.uint8), mode='L')

			del NORMALISED_DATA, DEPTH_MIN, DEPTH_MAX
			

		case "NORMAL":
			#Normal maps. X=R, Y=G, Z=B.
			DATA = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGB, GL_FLOAT)
			DATA = NP.frombuffer(DATA, dtype=NP.float32).reshape(int(RESOLUTION.Y), int(RESOLUTION.X), 3)
			if DEBUG: print("Normal data before processing:\n", DATA)

			DATA = NP.flipud(DATA)

			#Scale normals from [-1, 1] to [0, 255] for visualization
			NORMAL_DATA_VIS = ((DATA + 1) / 2 * 255).astype(NP.uint8)

			if NP.any(NP.isnan(DATA)):
				raise ValueError("[WARNING] // NaN values found in normal data; Issues may ensue.")

			IMAGE = Image.fromarray(NORMAL_DATA_VIS, mode='RGB')
			del NORMAL_DATA_VIS
		

		case "COLOUR":
			#Colour with no Alpha value.
			DATA = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGB, GL_UNSIGNED_BYTE)
			DATA = NP.frombuffer(DATA, dtype=NP.uint8).reshape(int(RESOLUTION.Y), int(RESOLUTION.X), 3)
			if DEBUG: print("Colour data before processing:\n", DATA)

			# Flip the image data vertically
			DATA = NP.flipud(DATA)

			if NP.any(NP.isnan(DATA)):
				raise ValueError("[WARNING] // NaN values found in colour data; Issues may ensue.")

			IMAGE = Image.fromarray(DATA, mode='RGB')


		case "COLOUR_RGBA":
			#Colour with an Alpha value.
			DATA = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_UNSIGNED_BYTE)
			DATA = NP.frombuffer(DATA, dtype=NP.uint8).reshape(int(RESOLUTION.Y), int(RESOLUTION.X), 4)
			if DEBUG: print("Colour data before processing:\n", DATA)

			# Flip the image data vertically
			DATA = NP.flipud(DATA)

			if NP.any(NP.isnan(DATA)):
				raise ValueError("[WARNING] // NaN values found in colour data; Issues may ensue.")

			IMAGE = Image.fromarray(DATA, mode='RGBA')


		case _:
			#Raise error if type is not recognised.
			raise ValueError("[ERROR] // Invalid MAP_TYPE specified. Use 'DEPTH', 'NORMAL', 'COLOUR', or 'COLOUR_RGBA'.")
	

	if ZIP:
		#Save to zip file
		IMAGE.save(BUFFER, format="jpeg")
		IMAGE_BYTES = BUFFER.getvalue()
		BUFFER.close()

		with zipfile.ZipFile(ZIP_PATH, "a", zipfile.ZIP_DEFLATED) as ZIP_FILE:
			ZIP_FILE.writestr(FILE_NAME, IMAGE_BYTES)

	else:
		#Else just save.
		IMAGE.save(FILE_NAME)


	if DEBUG:
		#For debugging, show image onscreen.
		IMAGE.show()

	del IMAGE, DATA

	glBindTexture(GL_TEXTURE_2D, 0)



#Per-frame rendering


def SCENE(PHYS_DATA, ENV_VAO_DATA, PLAYER):
	#Renders the entire scene, from the positional and texture datas included.
	try:
		ENV_VAO_VERTICES, ENV_VAO_INDICES = ENV_VAO_DATA
		NEW_DYNAMIC_STATICS = {}

		for ID, PHYS_OBJECT in PHYS_DATA[0].items(): #All physics objects, such as Items and Cubes.
			ENV_VAO_VERTICES, ENV_VAO_INDICES = PROCESS_OBJECT(PHYS_OBJECT, PLAYER, ENV_VAO_VERTICES, ENV_VAO_INDICES)
		for ID, DYNAMIC_STATIC in PHYS_DATA[1][1].items(): #All "dynamic statics" such as static sprites, that must face camera.
			ENV_VAO_VERTICES, ENV_VAO_INDICES = PROCESS_OBJECT(DYNAMIC_STATIC, PLAYER, ENV_VAO_VERTICES, ENV_VAO_INDICES)

			if type(DYNAMIC_STATIC) == RAY:
				if DYNAMIC_STATIC.LIFETIME >= CONSTANTS["MAX_RAY_PERSIST_FRAMES"]:
					continue

			NEW_DYNAMIC_STATICS[ID] = DYNAMIC_STATIC


		PHYS_DATA = [PHYS_DATA[0], (PHYS_DATA[1][0], NEW_DYNAMIC_STATICS)]

		return [ENV_VAO_VERTICES, ENV_VAO_INDICES], PHYS_DATA

	except Exception as E:
		log.ERROR("render.SCENE", E)


def PROCESS_OBJECT(OBJECT_DATA, PLAYER, COPIED_VERTS, COPIED_INDICES):
	#Processes a given object (I.e. SPRITE_STATIC, ITEM, etc.) for its new data.
	OBJECT_TYPE = type(OBJECT_DATA)
	if OBJECT_TYPE in [SPRITE_STATIC, ITEM, ENEMY]:
		#Sprites
		SPRITE_POSITION = OBJECT_DATA.POSITION - VECTOR_3D(0.0, 0.5 * OBJECT_DATA.DIMENTIONS_2D.Y, 0.0) if OBJECT_TYPE in [ENEMY, ITEM] else OBJECT_DATA.POSITION
		COORDINATES = CALC_SPRITE_POINTS(SPRITE_POSITION, PLAYER.POSITION, OBJECT_DATA.DIMENTIONS_2D)
		OBJECT_DATA.NORMALS = ((COORDINATES[1] - COORDINATES[0]).CROSS(COORDINATES[2] - COORDINATES[0]), (COORDINATES[1] - COORDINATES[3]).CROSS(COORDINATES[2] - COORDINATES[3]))
		if OBJECT_TYPE in [ENEMY,]:
			ANGLE = utils.CALC_2D_VECTOR_ANGLE((PLAYER.POSITION - OBJECT_DATA.POSITION).NORMALISE(), OBJECT_DATA.ROTATION.NORMALISE())

			match ANGLE:
				case N if N > 100 or N <= -100:
					TEXTURES = OBJECT_DATA.TEXTURE_INFO[0]
				
				case N if N <= 100 and N > 60:
					TEXTURES = OBJECT_DATA.TEXTURE_INFO[1]

				case N if N <= 60 and N > 20:
					TEXTURES = OBJECT_DATA.TEXTURE_INFO[2]

				case N if N <= 20 and N > -20:
					TEXTURES = OBJECT_DATA.TEXTURE_INFO[3]

				case N if N <= -20 and N > -60:
					TEXTURES = OBJECT_DATA.TEXTURE_INFO[4]
				
				case N if N <= -60 and N > -100:
					TEXTURES = OBJECT_DATA.TEXTURE_INFO[5]

		else:
			TEXTURES = OBJECT_DATA.TEXTURE_INFO

		COPIED_VERTS, COPIED_INDICES = OBJECT_VAO_MANAGER(OBJECT_DATA, [COPIED_VERTS, COPIED_INDICES], TEXTURES=TEXTURES, POINTS=COORDINATES)

	elif OBJECT_TYPE in [CUBE_PHYSICS, CUBE_PATH,]:
		#Physics cubes.
		NORMALS = utils.FIND_CUBOID_NORMALS(OBJECT_DATA.POINTS)
		COPIED_VERTS, COPIED_INDICES = OBJECT_VAO_MANAGER(OBJECT_DATA, [COPIED_VERTS, COPIED_INDICES])

	elif OBJECT_TYPE == RAY:
		OBJECT_DATA.LIFETIME += 1

		if OBJECT_DATA.LIFETIME < CONSTANTS["MAX_RAY_PERSIST_FRAMES"]:
			RAY_POINTS = OBJECT_DATA.RAY_VISUAL()
			#Generic UV coordinate data for the triangles to reference.
			TEXTURES = (VECTOR_2D(0.3145, 0.9395), VECTOR_2D(0.373, 0.9395), VECTOR_2D(0.373, 0.998), VECTOR_2D(0.3145, 0.998))

			for TRI_POINTS in RAY_POINTS: #Rays visualise as 2 triangles.
				COPIED_VERTS, COPIED_INDICES = OBJECT_VAO_MANAGER(OBJECT_DATA, [COPIED_VERTS, COPIED_INDICES], TEXTURES=TEXTURES, POINTS=TRI_POINTS)


	return COPIED_VERTS, COPIED_INDICES



def OBJECT_VAO_MANAGER(OBJECT, VAO_DATA, TEXTURES=None, POINTS=None):
	#Appends the current object's data to the VAO data, depending on the type and associated data.
	#For example, a sprite would be added to the vertices as a quad, and same for the indices, with the UV data and normals data as needed.
	try:
		if POINTS is None:
			POINTS = OBJECT.POINTS
		if TEXTURES is None:
			TEXTURES = OBJECT.TEXTURE_INFO
		
		VAO_VERTICES, VAO_INDICES = VAO_DATA[0], VAO_DATA[1]

		#Ensure VAO_VERTICES is a 2D array (List of triangles; each triangle is a list of 3 vertices.), even if initially empty.
		if VAO_VERTICES.size == 0:
			VAO_VERTICES = NP.empty((0, 8), dtype=NP.float32)
		if VAO_INDICES.size == 0:
			VAO_INDICES = NP.empty(0, dtype=NP.uint32)


		#Calculate the size of NumPy arrays to pre-make.
		CLASS_TYPE = type(OBJECT)
		NUM_FACES = 6 if isinstance(OBJECT, (CUBE_STATIC, CUBE_PHYSICS, CUBE_PATH,)) else 1
		NUM_VERTS, NUM_INDICES = NUM_FACES * 4, NUM_FACES * 6
		NEW_VERTICES = NP.zeros((NUM_VERTS, 8), dtype=NP.float32)
		NEW_INDICES = NP.zeros(NUM_INDICES, dtype=NP.uint32)


		#Index offset to be added to any indices value, so that they still correspond to the right index in the vertices data.
		INDEX_OFFSET = len(VAO_VERTICES)

		if CLASS_TYPE in (CUBE_STATIC, CUBE_PHYSICS, CUBE_PATH,): #Cube-like objects.
			FACE_ORDER = [
				(0, 1, 3, 2),  # -Y | Bottom
				(0, 2, 6, 4),  # -X | Left
				(5, 7, 3, 1),  # +X | Right
				(1, 0, 4, 5),  # -Z | Back
				(7, 6, 2, 3),  # +Z | Front
				(6, 7, 5, 4)   # +Y | Top
			]

			CUBE_TEXTURE_DATA = [TEXTURES[0], TEXTURES[1], TEXTURES[1], TEXTURES[1], TEXTURES[1], TEXTURES[2]]

			#Iterate through each of the 6 faces
			for FACE_INDEX, TEX_COORDS in enumerate(CUBE_TEXTURE_DATA):
				NORMAL = OBJECT.NORMALS[FACE_INDEX]
				FACE_INDICES = FACE_ORDER[FACE_INDEX]
				INDICES_OFFSET = [INDEX_OFFSET + I for I in range(4)]

				NEW_INDICES[FACE_INDEX * 6:FACE_INDEX * 6 + 6] = [
					INDICES_OFFSET[0], INDICES_OFFSET[1], INDICES_OFFSET[2],
					INDICES_OFFSET[2], INDICES_OFFSET[3], INDICES_OFFSET[0]
				]

				#Iterate through the indices for this face.
				for I, INDEX in enumerate(FACE_INDICES):
					X, Y, Z = OBJECT.POINTS[INDEX].X, OBJECT.POINTS[INDEX].Y, OBJECT.POINTS[INDEX].Z
					TEX_COORD = TEX_COORDS[I]
					U, V = TEX_COORD.X, TEX_COORD.Y
					NEW_VERTICES[FACE_INDEX * 4 + I] = [X, Y, Z, U, V, NORMAL.X, NORMAL.Y, NORMAL.Z]

				INDEX_OFFSET += 4

		elif CLASS_TYPE in (QUAD, INTERACTABLE, SPRITE_STATIC, ITEM, ENEMY): #Quad-like objects.
			FACE_ORDER = (0, 1, 2, 3)
			NEW_INDICES = [INDEX_OFFSET, INDEX_OFFSET + 1, INDEX_OFFSET + 2, INDEX_OFFSET + 2, INDEX_OFFSET + 3, INDEX_OFFSET]

			#Iterate through the indices for this face.
			for I, INDEX in enumerate(FACE_ORDER):
				TEX_COORD = TEXTURES[I]
				X, Y, Z = POINTS[INDEX].X, POINTS[INDEX].Y, POINTS[INDEX].Z
				U, V = TEX_COORD.X, TEX_COORD.Y
				NORMAL = OBJECT.NORMALS[I // 2]  # Assuming the normal is consistent across the quad
				NEW_VERTICES[I] = [X, Y, Z, U, V, NORMAL.X, NORMAL.Y, NORMAL.Z]

		elif CLASS_TYPE in (TRI, RAY,):  # Triangles
			FACE_ORDER = (0, 1, 2)
			NEW_INDICES = [INDEX_OFFSET, INDEX_OFFSET + 1, INDEX_OFFSET + 2]
			NORMAL = OBJECT.NORMALS[0]  # Assuming all vertices in a TRI have the same normal

			#Iterate through the indices for the triangle.
			for I, INDEX in enumerate(FACE_ORDER):
				TEX_COORD = TEXTURES[I]
				X, Y, Z = POINTS[INDEX].X, POINTS[INDEX].Y, POINTS[INDEX].Z
				U, V = TEX_COORD.X, TEX_COORD.Y
				NEW_VERTICES[I] = [X, Y, Z, U, V, NORMAL.X, NORMAL.Y, NORMAL.Z]


		#Concatenate the new vertices and indices to the existing VAO_DATA arrays.
		VAO_VERTICES = NP.concatenate((VAO_VERTICES, NEW_VERTICES))
		VAO_INDICES = NP.concatenate((VAO_INDICES, NEW_INDICES))

		return (VAO_VERTICES, VAO_INDICES)

	except Exception as E:
		log.ERROR("render.OBJECT_VAO_MANAGER", E)


#Shader loading functions



def SHADER_INIT(SCENE=False, QUAD=False, SHADOW=False):
	#Loads and compiles the shaders (scene, shadow, quad,)

	def LOAD_SHADER_SOURCE(FILE_PATH):
		#Loads the source data for a shader. Only used in this function.
		with open(FILE_PATH, 'r') as FILE:
			SOURCE = FILE.read()
		return SOURCE
	

	#Get filepath to ..\src\exct\glsl\
	GLSL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'glsl')
	

	#List of shaders to return (based on which flags are set to "requested"/True)
	SHADERS = []

	if SCENE:
		#Scene Shaders (for the stuff rendered on the 1st quad.)
		SCENE_VERTEX_SHADER_SOURCE = LOAD_SHADER_SOURCE(f"{GLSL_PATH}\\scene_vertex_shader.glsl")
		SCENE_FRAGMENT_SHADER_SOURCE = LOAD_SHADER_SOURCE(f"{GLSL_PATH}\\scene_fragment_shader.glsl")
		SCENE_VERTEX_SHADER_COMPILED = compileShader(SCENE_VERTEX_SHADER_SOURCE, GL_VERTEX_SHADER)
		SCENE_FRAGMENT_SHADER_COMPILED = compileShader(SCENE_FRAGMENT_SHADER_SOURCE, GL_FRAGMENT_SHADER)
		SCENE_SHADER = compileProgram(SCENE_VERTEX_SHADER_COMPILED, SCENE_FRAGMENT_SHADER_COMPILED)
		SHADERS.append(SCENE_SHADER)

	if QUAD:
		#Quad Shaders (for the 2 quads (UI and scene TCB) to display the colour data.)
		QUAD_VERTEX_SHADER_SOURCE = LOAD_SHADER_SOURCE(f"{GLSL_PATH}\\quad_vertex_shader.glsl")
		QUAD_FRAGMENT_SHADER_SOURCE = LOAD_SHADER_SOURCE(f"{GLSL_PATH}\\quad_fragment_shader.glsl")
		QUAD_VERTEX_SHADER_COMPILED = compileShader(QUAD_VERTEX_SHADER_SOURCE, GL_VERTEX_SHADER)
		QUAD_FRAGMENT_SHADER_COMPILED = compileShader(QUAD_FRAGMENT_SHADER_SOURCE, GL_FRAGMENT_SHADER)
		QUAD_SHADER = compileProgram(QUAD_VERTEX_SHADER_COMPILED, QUAD_FRAGMENT_SHADER_COMPILED)
		SHADERS.append(QUAD_SHADER)

	if SHADOW:
		#Shadow Shaders (for the shadow-mapping stage.)
		SHADOW_VERTEX_SHADER_SOURCE = LOAD_SHADER_SOURCE(f"{GLSL_PATH}\\shadow_vertex_shader.glsl")
		SHADOW_FRAGMENT_SHADER_SOURCE = LOAD_SHADER_SOURCE(f"{GLSL_PATH}\\shadow_fragment_shader.glsl")
		SHADOW_VERTEX_SHADER_COMPILED = compileShader(SHADOW_VERTEX_SHADER_SOURCE, GL_VERTEX_SHADER)
		SHADOW_FRAGMENT_SHADER_COMPILED = compileShader(SHADOW_FRAGMENT_SHADER_SOURCE, GL_FRAGMENT_SHADER)
		SHADOW_SHADER = compileProgram(SHADOW_VERTEX_SHADER_COMPILED, SHADOW_FRAGMENT_SHADER_COMPILED)
		SHADERS.append(SHADOW_SHADER)


	#Return any shaders required, None if none were requested, and if only 1 then return that shader alone.
	return SHADERS if len(SHADERS) > 1 else None if len(SHADERS) == 0 else SHADERS[0]



#VAO, VBO, EBO, FBO.. creation functions


def FBO_QUAD_INIT(RENDER_RES):
	#Creates the quad data for the scene TCB and UI quads.
	QUAD_VERTICES = NP.array([
		-1.0,  1.0,  0.0,  0.01, 0.99,
		-1.0, -1.0,  0.0,  0.01, 0.01,
		 1.0, -1.0,  0.0,  0.99, 0.01,
		 1.0,  1.0,  0.0,  0.99, 0.99
	], dtype=NP.float32)
	
	#The UI quad is slightly in front of the TCB quad, to overlay on top.
	UI_VERTICES = NP.array([
		-1.0,  1.0,  -1e-7,  0.0, 1.0,
		-1.0, -1.0,  -1e-7,  0.0, 0.0,
		 1.0, -1.0,  -1e-7,  1.0, 0.0,
		 1.0,  1.0,  -1e-7,  1.0, 1.0
	], dtype=NP.float32)

	#Indices are the same for both; they're quads.
	INDICES = NP.array([
		0, 1, 2,
		2, 3, 0
	], dtype=NP.uint32)



	#Set up the Quad VAO, VBO, and EBO
	VAO_QUAD = glGenVertexArrays(1)
	VBO_QUAD = glGenBuffers(1)
	EBO_QUAD = glGenBuffers(1)

	glBindVertexArray(VAO_QUAD)
	glBindBuffer(GL_ARRAY_BUFFER, VBO_QUAD)
	glBufferData(GL_ARRAY_BUFFER, QUAD_VERTICES.nbytes, QUAD_VERTICES, GL_STATIC_DRAW)

	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_QUAD)
	glBufferData(GL_ELEMENT_ARRAY_BUFFER, INDICES.nbytes, INDICES, GL_STATIC_DRAW)

	glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(0))
	glEnableVertexAttribArray(0)
	glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(12))
	glEnableVertexAttribArray(1)

	glBindBuffer(GL_ARRAY_BUFFER, 0)
	glBindVertexArray(0)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)


	#Set up the UI VAO, VBO, and EBO
	VAO_UI = glGenVertexArrays(1)
	VBO_UI = glGenBuffers(1)
	EBO_UI = glGenBuffers(1)

	glBindVertexArray(VAO_UI)
	glBindBuffer(GL_ARRAY_BUFFER, VBO_UI)
	glBufferData(GL_ARRAY_BUFFER, UI_VERTICES.nbytes, UI_VERTICES, GL_STATIC_DRAW)

	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_UI)
	glBufferData(GL_ELEMENT_ARRAY_BUFFER, INDICES.nbytes, INDICES, GL_STATIC_DRAW)

	glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(0))
	glEnableVertexAttribArray(0)
	glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(12))
	glEnableVertexAttribArray(1)

	glBindBuffer(GL_ARRAY_BUFFER, 0)
	glBindVertexArray(0)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)


	#Create the Scene Framebuffer-object (FBO) and Texture-colour-buffer (TCB)
	FBO, TCB, _, _, _ = CREATE_FBO(RENDER_RES)

	return VAO_QUAD, VAO_UI, FBO, TCB



def CREATE_FBO(SIZE, DEPTH=False, NORMALS=False):
	#Creates an FBO based on what data has been requested (A base FBO with colour/render buffers if nothing is specified)
	FBO = glGenFramebuffers(1)
	glBindFramebuffer(GL_FRAMEBUFFER, FBO)

	DTB, TCB, RBO, GBO = None, None, None, None
	if DEPTH:
		DTB = glGenTextures(1) #Depth-texture-buffer (DTB) for depth values (GL_R32F)
		glBindTexture(GL_TEXTURE_2D, DTB)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_R32F, int(SIZE.X), int(SIZE.Y), 0, GL_RED, GL_FLOAT, None)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glBindTexture(GL_TEXTURE_2D, 0)

		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, DTB, 0)
		glDrawBuffers(1, [GL_COLOR_ATTACHMENT0])

	else:
		TCB = glGenTextures(1) #Texture-colour-buffer (TCB) for colour data
		glBindTexture(GL_TEXTURE_2D, TCB)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, int(SIZE.X), int(SIZE.Y), 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glBindTexture(GL_TEXTURE_2D, 0)
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, TCB, 0)

		RBO = glGenRenderbuffers(1) #Render Buffer Object (RBO) for use in rendering.
		glBindRenderbuffer(GL_RENDERBUFFER, RBO)
		glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, int(SIZE.X), int(SIZE.Y))
		glBindRenderbuffer(GL_RENDERBUFFER, 0)
		glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, RBO)

	if NORMALS:
		GBO = glGenTextures(1) #Geometry Buffer Object (GBO) for normals data
		glBindTexture(GL_TEXTURE_2D, GBO)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB16F, int(SIZE.X), int(SIZE.Y), 0, GL_RGB, GL_FLOAT, None)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, GBO, 0)
		glDrawBuffers(1, [GL_COLOR_ATTACHMENT0])


	#Ensuring the FBO creation process completed correctly.
	STATUS = glCheckFramebufferStatus(GL_FRAMEBUFFER)
	if STATUS != GL_FRAMEBUFFER_COMPLETE:
		#If an error has occurred, raise an exception.
		raise Exception(f"Framebuffer of size {SIZE} is not complete.\nError: {STATUS}")


	glBindFramebuffer(GL_FRAMEBUFFER, 0)
	return FBO, TCB, DTB, RBO, GBO



def BUFFERS_INIT(VERTICES=None, INDICES=None, NORMALS=False):
	VERTEX_BUFFER_SIZE_INITIAL = 1024 * 1024  #1MB Initial size for vertex buffer.
	INDEX_BUFFER_SIZE_INITIAL = 256 * 1024  #256KB Initial size for index buffer.

	VAO_SCENE = glGenVertexArrays(1)
	VBO_SCENE = glGenBuffers(1)
	EBO_SCENE = glGenBuffers(1)

	glBindVertexArray(VAO_SCENE)

	#If there is vertices/indices data, immediately assign it to prevent further calls of functions like UPDATE_BUFFERS() being neccessary.
	glBindBuffer(GL_ARRAY_BUFFER, VBO_SCENE)
	if VERTICES is not None:
		glBufferData(GL_ARRAY_BUFFER, VERTICES.nbytes, VERTICES, GL_DYNAMIC_DRAW) #Initialise with the correct size for the data.
	else:
		glBufferData(GL_ARRAY_BUFFER, VERTEX_BUFFER_SIZE_INITIAL, None, GL_DYNAMIC_DRAW)  #Initialise with the default size otherwise.


	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_SCENE)
	if INDICES is not None:
		glBufferData(GL_ELEMENT_ARRAY_BUFFER, INDICES.nbytes, INDICES, GL_DYNAMIC_DRAW) #Initialise with the correct size for the data.

	else:
		glBufferData(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER_SIZE_INITIAL, None, GL_DYNAMIC_DRAW)  #Initialise with the default size otherwise.


	#3 position values, 2 texture coordinate values, 3 normal values, where each value (float) is 4 bytes
	STRIDE = (3 + 2 + 3) * 4
	OFFSET = 0

	#Vertex Position XYZ
	glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, STRIDE, ctypes.c_void_p(OFFSET))
	glEnableVertexAttribArray(0)
	OFFSET += 3 * 4

	#Texture Coordinate XY
	glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, STRIDE, ctypes.c_void_p(OFFSET))
	glEnableVertexAttribArray(1)
	OFFSET += 2 * 4

	#Vertex Normal XYZ
	glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, STRIDE, ctypes.c_void_p(OFFSET))
	glEnableVertexAttribArray(2)


	glBindBuffer(GL_ARRAY_BUFFER, 0)
	glBindVertexArray(0)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

	return VAO_SCENE, VBO_SCENE, EBO_SCENE



def UPDATE_BUFFERS(UNPROCESSED_VERTS, UNPROCESSED_INDICES, VBO, EBO):
	#Updates a given VBO/EBO with new vertices/indices data for rendering.

	#Ensure these are a NumPy array before continuing.
	VERTICES = NP.array(UNPROCESSED_VERTS, dtype=NP.float32)
	INDICES = NP.array(UNPROCESSED_INDICES, dtype=NP.uint32)


	#Assign data to the VBO first (Vertices)
	glBindBuffer(GL_ARRAY_BUFFER, VBO)
	VERTEX_BUFFER_SIZE = glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)	
	glBufferData(GL_ARRAY_BUFFER, VERTICES.nbytes, VERTICES, GL_DYNAMIC_DRAW)
	glBindBuffer(GL_ARRAY_BUFFER, 0)


	#Assign data to the EBO afterward (Indices)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
	INDEX_BUFFER_SIZE = glGetBufferParameteriv(GL_ELEMENT_ARRAY_BUFFER, GL_BUFFER_SIZE)	
	glBufferData(GL_ELEMENT_ARRAY_BUFFER, INDICES.nbytes, INDICES, GL_DYNAMIC_DRAW)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)


	return VBO, EBO



#Shadowmap creation


def RENDER_DEPTH_MAP(VAO_SHADOW, SHADOW_SHADER, PROJECTION, VIEW, FBO_SHADOW, SHADOWMAP_RESOLUTION, ENV_VAO_INDICES, SHEET_ID, LIGHT):
	#Render the vertices/indices/texture data into a depth map (DTB).

	#Bind the framebuffer for rendering
	glBindFramebuffer(GL_FRAMEBUFFER, FBO_SHADOW)
	glViewport(0, 0, int(SHADOWMAP_RESOLUTION.X), int(SHADOWMAP_RESOLUTION.Y))
	glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)


	#Use the shadow shader program while rendering.
	glUseProgram(SHADOW_SHADER)


	#Get locations for and provide data for the scene shader's uniforms (such as LIGHT_POSITION).
	PROJECTION_MATRIX_LOC = glGetUniformLocation(SHADOW_SHADER, "PROJECTION_MATRIX")
	VIEW_MATRIX_LOC = glGetUniformLocation(SHADOW_SHADER, "VIEW_MATRIX")
	MODEL_MATRIX_LOC = glGetUniformLocation(SHADOW_SHADER, "MODEL_MATRIX")
	LIGHT_POSITION_LOC = glGetUniformLocation(SHADOW_SHADER, "LIGHT_POSITION")
	MAX_DIST_LOC = glGetUniformLocation(SHADOW_SHADER, "MAX_DIST")
	glUniformMatrix4fv(PROJECTION_MATRIX_LOC, 1, GL_FALSE, glm.value_ptr(PROJECTION))
	glUniformMatrix4fv(VIEW_MATRIX_LOC, 1, GL_FALSE, glm.value_ptr(VIEW))
	glUniformMatrix4fv(MODEL_MATRIX_LOC, 1, GL_FALSE, Matrix44.identity())

	glUniform3fv(LIGHT_POSITION_LOC, 1, glm.value_ptr(LIGHT.POSITION.CONVERT_TO_GLM_VEC3()))
	glUniform3f(LIGHT_POSITION_LOC, LIGHT.POSITION.X, LIGHT.POSITION.Y, LIGHT.POSITION.Z)

	glUniform1f(MAX_DIST_LOC, LIGHT.MAX_DISTANCE)


	#Set the shader uniform for the texture
	TEXTURE_LOC = glGetUniformLocation(SHADOW_SHADER, 'TEXTURE')
	glUniform1i(TEXTURE_LOC, 0)

	#Activate and bind the texture
	glActiveTexture(GL_TEXTURE0)
	glBindTexture(GL_TEXTURE_2D, SHEET_ID)


	#Bind the VAO and draw the elements
	glBindVertexArray(VAO_SHADOW)
	glDrawElements(GL_TRIANGLES, len(ENV_VAO_INDICES), GL_UNSIGNED_INT, None)
	glBindVertexArray(0)

	#Unbind the texture and framebuffer
	glBindTexture(GL_TEXTURE_2D, 0)
	glBindFramebuffer(GL_FRAMEBUFFER, 0)


	#Finally, check for errors. Raise if neccessary, as (Py)OpenGL does not do this automatically.
	GL_ERRORCHECK()



def CREATE_SHADOW_MAPS(SURFACE, I, LIGHT, VAO_DATA, SHEET_DATA):
	#Handles the entire creation of shadowmaps for a given light instance.

	SHADOWMAP_RESOLUTION = CONSTANTS["SHADOW_MAP_RESOLUTION"]
	#Uses a given GLFW surface rather than creating one here.
	glfw.make_context_current(SURFACE)
	

	glEnable(GL_DEPTH_TEST)
	glDepthFunc(GL_LESS)
	glClearDepth(1.0)
	glEnable(GL_ALPHA_TEST)
	glAlphaFunc(GL_GREATER, 0.5)
	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


	#Initialise buffers with vertices/indices data, or with a DTB (for the FBO specifically)
	VAO_SHADOW, VBO_SHADOW, EBO_SHADOW = BUFFERS_INIT(VERTICES=VAO_DATA[0], INDICES=VAO_DATA[1])
	FBO_SHADOW, DTB_SHADOW, _, _, _ = CREATE_FBO(SHADOWMAP_RESOLUTION)
	#Gets the shadow shader compiled GLSL
	SHADOW_SHADER = SHADER_INIT(SHADOW=True)

	#Re-creates the texture sheet from the given data, due to passing between contexts.
	SHEET_ID = CREATE_TEXTURE_FROM_DATA(SHEET_DATA, GL_TYPE=GL_RGBA)


	#Calculate matrices.
	LIGHT_PROJECTION_MATRIX = glm.mat4(Matrix44.perspective_projection(LIGHT.FOV, SHADOWMAP_RESOLUTION.X / SHADOWMAP_RESOLUTION.Y, LIGHT.MAX_DISTANCE/100, LIGHT.MAX_DISTANCE).tolist())
	LIGHT_VIEW_MATRIX = glm.lookAt(LIGHT.POSITION.CONVERT_TO_GLM_VEC3(), LIGHT.LOOK_AT.CONVERT_TO_GLM_VEC3(), glm.vec3(0.0, 1.0, 0.0))
	DEPTH_SPACE_MATRIX = LIGHT_PROJECTION_MATRIX * LIGHT_VIEW_MATRIX
	#Projection Matrix * View Matrix * Model Matrix -> M-V-P Matrix for shader.
	DEPTH_MVP_MATRIX = DEPTH_SPACE_MATRIX * glm.mat4(1.0)


	#Render the depth map to the DTB.
	RENDER_DEPTH_MAP(VAO_SHADOW, SHADOW_SHADER, LIGHT_PROJECTION_MATRIX, LIGHT_VIEW_MATRIX, FBO_SHADOW, SHADOWMAP_RESOLUTION, VAO_DATA[1], SHEET_ID, LIGHT)


	if PREFERENCES["DEBUG_MAPS"]:
		SAVE_MAP(CONSTANTS["SHADOW_MAP_RESOLUTION"], DTB_SHADOW, f"screenshots\\debug_maps\\depth_map_{I}.png", "COLOUR_RGBA", MIN_DISTANCE=LIGHT.MIN_DISTANCE, MAX_DISTANCE=LIGHT.MAX_DISTANCE)


	#Assign data to the Light instance, including the data from the DTB to pass accross the contexts again.
	LIGHT.SPACE_MATRIX = DEPTH_SPACE_MATRIX
	LIGHT.SHADOW_MAP_DATA = GET_TEXTURE_DATA(DTB_SHADOW, SHADOWMAP_RESOLUTION, "DEPTH")


	#Close the GLFW window to cleanup.
	glfw.terminate()

	return LIGHT
