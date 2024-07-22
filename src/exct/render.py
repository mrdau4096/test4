"""
[render.py]
Renders different objects with data, such as a list of planes or a sphere from associated data
Can take a long list of objects and draw them properly, textured too.

______________________
Importing other files;
-log.py
"""
import sys, math
from exct import log, ui, utils
from imgs import texture_load
from exct.utils import *

sys.path.append("modules.zip")
import pygame as PG
from pygame.locals import *
from pygame import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GL.shaders import compileProgram, compileShader
from pyrr import Matrix44, Vector3
import numpy as NP
import copy
import glm
from PIL import Image

print("Imported Sub-file // render.py")

PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS


#General render related functions

def GL_ERRORCHECK():
	#Checks for any errors with OpenGL, and reports them to the shell (debugging)
	ERROR = glGetError()
	if ERROR != GL_NO_ERROR:
		print("OpenGL ERROR:", ERROR)
	else:
		print("OpenGL ERROR: None")



def CALC_VIEW_MATRIX(CAMERA_POSITION, CAMERA_ROTATION):
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



def CLIP_EDGES(TEX_COORD):
	CLIP_VALUES = (
			VECTOR_2D(0.002, 0.002),
			VECTOR_2D(-0.002, 0.002),
			VECTOR_2D(-0.002, -0.002),
			VECTOR_2D(0.002, -0.002)
		)

	return [
		TEX_COORD[0] + CLIP_VALUES[0],
		TEX_COORD[1] + CLIP_VALUES[1],
		TEX_COORD[2] + CLIP_VALUES[2],
		TEX_COORD[3] + CLIP_VALUES[3],
	]


def SURFACE_TO_TEXTURE(SURFACE, RESOLUTION):
	SURFACE_DATA = PG.image.tostring(SURFACE, "RGBA", 1)
	
	FINAL_ID = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, FINAL_ID)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, RESOLUTION.X, RESOLUTION.Y, 0, GL_RGBA, GL_UNSIGNED_BYTE, SURFACE_DATA)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glBindTexture(GL_TEXTURE_2D, 0)
	del SURFACE_DATA
	
	return FINAL_ID


def SAVE_MAP(RESOLUTION, MAP, FILE_NAME, MAP_TYPE, MIN_DISTANCE=0.0, MAX_DISTANCE=1.0, DEBUG=False):
	glBindTexture(GL_TEXTURE_2D, MAP)
	
	if MAP_TYPE == "DEPTH":
		DATA = glGetTexImage(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, GL_FLOAT)
		DATA = NP.frombuffer(DATA, dtype=NP.float32).reshape(int(RESOLUTION.Y), int(RESOLUTION.X))
		DATA = NP.flipud(DATA)
		if DEBUG: print("Depth data before normalization:\n", DATA)
		glBindTexture(GL_TEXTURE_2D, 0)

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
		
	elif MAP_TYPE == "NORMAL":
		DATA = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGB, GL_FLOAT)
		DATA = NP.frombuffer(DATA, dtype=NP.float32).reshape(int(RESOLUTION.Y), int(RESOLUTION.X), 3)
		if DEBUG: print("Normal data before processing:\n", DATA)
		glBindTexture(GL_TEXTURE_2D, 0)

		DATA = NP.flipud(DATA)

		#Scale normals from [-1, 1] to [0, 255] for visualization
		NORMAL_DATA_VIS = ((DATA + 1) / 2 * 255).astype(NP.uint8)

		if NP.any(NP.isnan(DATA)):
			raise ValueError("[WARNING] // NaN values found in normal data; Issues may ensue.")

		IMAGE = Image.fromarray(NORMAL_DATA_VIS, mode='RGB')
		del NORMAL_DATA_VIS
	
	elif MAP_TYPE == "COLOUR":
		DATA = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGB, GL_UNSIGNED_BYTE)
		DATA = NP.frombuffer(DATA, dtype=NP.uint8).reshape(int(RESOLUTION.Y), int(RESOLUTION.X), 3)
		if DEBUG: print("Colour data before processing:\n", DATA)
		glBindTexture(GL_TEXTURE_2D, 0)

		# Flip the image data vertically
		DATA = NP.flipud(DATA)

		if NP.any(NP.isnan(DATA)):
			raise ValueError("[WARNING] // NaN values found in colour data; Issues may ensue.")

		IMAGE = Image.fromarray(DATA, mode='RGB')

	else:
		raise ValueError("[ERROR] // Invalid MAP_TYPE specified. Use 'depth', 'normal', or 'color'.")
	
	IMAGE.save(FILE_NAME)
	if DEBUG:
		IMAGE.show()

	del IMAGE, DATA



#Per-frame rendering


def SCENE(PHYS_DATA, ENV_VAO_DATA, PLAYER):
	#Renders the entire scene, from the positional and texture datas included.
	ENV_VAO_VERTICES, ENV_VAO_INDICES = ENV_VAO_DATA
	#COPIED_VERTS, COPIED_INDICES = copy.copy(ENV_VAO_VERTICES), copy.copy(ENV_VAO_INDICES)
	for ID, PHYS_OBJECT in PHYS_DATA[0].items(): #All physics objects, such as Items and Cubes.
		ENV_VAO_VERTICES, ENV_VAO_INDICES = PROCESS_OBJECT(PHYS_OBJECT, PLAYER, ENV_VAO_VERTICES, ENV_VAO_INDICES)
	for ID, DYNAMIC_STATIC in PHYS_DATA[1][1].items(): #All "dynamic statics" such as static sprites, that must face camera.
		ENV_VAO_VERTICES, ENV_VAO_INDICES = PROCESS_OBJECT(DYNAMIC_STATIC, PLAYER, ENV_VAO_VERTICES, ENV_VAO_INDICES)

	return [ENV_VAO_VERTICES, ENV_VAO_INDICES]



def PROCESS_OBJECT(OBJECT_DATA, PLAYER, COPIED_VERTS, COPIED_INDICES):
	OBJECT_TYPE = type(OBJECT_DATA)
	if OBJECT_TYPE in [SPRITE_STATIC, ITEM, ENEMY]:
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

	elif OBJECT_TYPE in [CUBE_PHYSICS,]:
		NORMALS = utils.FIND_CUBOID_NORMALS(OBJECT_DATA.POINTS)
		COPIED_VERTS, COPIED_INDICES = OBJECT_VAO_MANAGER(OBJECT_DATA, [COPIED_VERTS, COPIED_INDICES])


	return COPIED_VERTS, COPIED_INDICES



def OBJECT_VAO_MANAGER(OBJECT, VAO_DATA, TEXTURES=None, POINTS=None):
	if POINTS is None:
		POINTS = OBJECT.POINTS
	if TEXTURES is None:
		TEXTURES = OBJECT.TEXTURE_INFO
	
	VAO_VERTICES, VAO_INDICES = VAO_DATA[0], VAO_DATA[1]

	# Ensure VAO_VERTICES is a 2D array, even if initially empty
	if VAO_VERTICES.size == 0:
		VAO_VERTICES = NP.empty((0, 8), dtype=NP.float32)
	if VAO_INDICES.size == 0:
		VAO_INDICES = NP.empty(0, dtype=NP.uint32)

	CLASS_TYPE = type(OBJECT)
	NUM_FACES = 6 if isinstance(OBJECT, (CUBE_STATIC, CUBE_PHYSICS, CUBE_PATH)) else 1
	NUM_VERTS, NUM_INDICES = NUM_FACES * 4, NUM_FACES * 6
	NEW_VERTICES = NP.zeros((NUM_VERTS, 8), dtype=NP.float32)
	NEW_INDICES = NP.zeros(NUM_INDICES, dtype=NP.uint32)

	INDEX_OFFSET = len(VAO_VERTICES)

	if CLASS_TYPE in (CUBE_STATIC, CUBE_PHYSICS, CUBE_PATH):  # Cubes
		FACE_ORDER = [
			(0, 1, 3, 2),  # -Y | Bottom
			(0, 2, 6, 4),  # -X | Left
			(5, 7, 3, 1),  # +X | Right
			(1, 0, 4, 5),  # -Z | Back
			(7, 6, 2, 3),  # +Z | Front
			(6, 7, 5, 4)   # +Y | Top
		]

		CUBE_TEXTURE_DATA = [TEXTURES[0], TEXTURES[1], TEXTURES[1], TEXTURES[1], TEXTURES[1], TEXTURES[2]]

		for FACE_INDEX, TEX_COORDS in enumerate(CUBE_TEXTURE_DATA):
			NORMAL = OBJECT.NORMALS[FACE_INDEX]
			FACE_INDICES = FACE_ORDER[FACE_INDEX]
			INDICES_OFFSET = [INDEX_OFFSET + I for I in range(4)]

			NEW_INDICES[FACE_INDEX * 6:FACE_INDEX * 6 + 6] = [
				INDICES_OFFSET[0], INDICES_OFFSET[1], INDICES_OFFSET[2],
				INDICES_OFFSET[2], INDICES_OFFSET[3], INDICES_OFFSET[0]
			]

			for I, INDEX in enumerate(FACE_INDICES):
				X, Y, Z = OBJECT.POINTS[INDEX].X, OBJECT.POINTS[INDEX].Y, OBJECT.POINTS[INDEX].Z
				TEX_COORD = TEX_COORDS[I]
				U, V = TEX_COORD.X, TEX_COORD.Y
				NEW_VERTICES[FACE_INDEX * 4 + I] = [X, Y, Z, U, V, NORMAL.X, NORMAL.Y, NORMAL.Z]

			INDEX_OFFSET += 4

	elif CLASS_TYPE in (QUAD, INTERACTABLE, SPRITE_STATIC, ITEM, ENEMY):  # Quads
		FACE_ORDER = (0, 1, 2, 3)
		NEW_INDICES = [INDEX_OFFSET, INDEX_OFFSET + 1, INDEX_OFFSET + 2, INDEX_OFFSET + 2, INDEX_OFFSET + 3, INDEX_OFFSET]

		for I, INDEX in enumerate(FACE_ORDER):
			TEX_COORD = TEXTURES[I]
			X, Y, Z = POINTS[INDEX].X, POINTS[INDEX].Y, POINTS[INDEX].Z
			U, V = TEX_COORD.X, TEX_COORD.Y
			NORMAL = OBJECT.NORMALS[I // 2]  # Assuming the normal is consistent across the quad
			NEW_VERTICES[I] = [X, Y, Z, U, V, NORMAL.X, NORMAL.Y, NORMAL.Z]

	elif CLASS_TYPE == TRI:  # Triangles
		FACE_ORDER = (0, 1, 2)
		NEW_INDICES = [INDEX_OFFSET, INDEX_OFFSET + 1, INDEX_OFFSET + 2]
		NORMAL = OBJECT.NORMALS[0]  # Assuming all vertices in a TRI have the same normal

		for I, INDEX in enumerate(FACE_ORDER):
			TEX_COORD = TEXTURES[I]
			X, Y, Z = OBJECT.POINTS[INDEX].X, OBJECT.POINTS[INDEX].Y, OBJECT.POINTS[INDEX].Z
			U, V = TEX_COORD.X, TEX_COORD.Y
			NEW_VERTICES[I] = [X, Y, Z, U, V, NORMAL.X, NORMAL.Y, NORMAL.Z]

	# Concatenate the new vertices and indices to the existing VAO data
	VAO_VERTICES = NP.concatenate((VAO_VERTICES, NEW_VERTICES))
	VAO_INDICES = NP.concatenate((VAO_INDICES, NEW_INDICES))

	return (VAO_VERTICES, VAO_INDICES)



#Shader loading functions


def LOAD_SHADER_SOURCE(FILE_PATH):
	with open(FILE_PATH, 'r') as FILE:
		SOURCE = FILE.read()
	return SOURCE



def SHADER_INIT():
	GLSL_PATH = utils.GET_GLSL_PATH()
	
	#Scene Shaders
	SCENE_VERTEX_SHADER_SOURCE = LOAD_SHADER_SOURCE(f"{GLSL_PATH}\\scene_vertex_shader.glsl")
	SCENE_FRAGMENT_SHADER_SOURCE = LOAD_SHADER_SOURCE(f"{GLSL_PATH}\\scene_fragment_shader.glsl")
	SCENE_VERTEX_SHADER_COMPILED = compileShader(SCENE_VERTEX_SHADER_SOURCE, GL_VERTEX_SHADER)
	SCENE_FRAGMENT_SHADER_COMPILED = compileShader(SCENE_FRAGMENT_SHADER_SOURCE, GL_FRAGMENT_SHADER)
	SCENE_SHADER = compileProgram(SCENE_VERTEX_SHADER_COMPILED, SCENE_FRAGMENT_SHADER_COMPILED)

	#Quad Shaders
	QUAD_VERTEX_SHADER_SOURCE = LOAD_SHADER_SOURCE(f"{GLSL_PATH}\\quad_vertex_shader.glsl")
	QUAD_FRAGMENT_SHADER_SOURCE = LOAD_SHADER_SOURCE(f"{GLSL_PATH}\\quad_fragment_shader.glsl")
	QUAD_VERTEX_SHADER_COMPILED = compileShader(QUAD_VERTEX_SHADER_SOURCE, GL_VERTEX_SHADER)
	QUAD_FRAGMENT_SHADER_COMPILED = compileShader(QUAD_FRAGMENT_SHADER_SOURCE, GL_FRAGMENT_SHADER)
	QUAD_SHADER = compileProgram(QUAD_VERTEX_SHADER_COMPILED, QUAD_FRAGMENT_SHADER_COMPILED)

	#Shadow Shaders
	SHADOW_VERTEX_SHADER_SOURCE = LOAD_SHADER_SOURCE(f"{GLSL_PATH}\\shadow_vertex_shader.glsl")
	SHADOW_FRAGMENT_SHADER_SOURCE = LOAD_SHADER_SOURCE(f"{GLSL_PATH}\\shadow_fragment_shader.glsl")
	SHADOW_VERTEX_SHADER_COMPILED = compileShader(SHADOW_VERTEX_SHADER_SOURCE, GL_VERTEX_SHADER)
	SHADOW_FRAGMENT_SHADER_COMPILED = compileShader(SHADOW_FRAGMENT_SHADER_SOURCE, GL_FRAGMENT_SHADER)
	SHADOW_SHADER = compileProgram(SHADOW_VERTEX_SHADER_COMPILED, SHADOW_FRAGMENT_SHADER_COMPILED)

	return SCENE_SHADER, QUAD_SHADER, SHADOW_SHADER



#VAO, VBO, EBO, FBO.. creation functions

def FBO_QUAD_INIT(RENDER_RES):
	QUAD_VERTICES = NP.array([
		-1.0,  1.0,  0.0,  0.01, 0.99,
		-1.0, -1.0,  0.0,  0.01, 0.01,
		 1.0, -1.0,  0.0,  0.99, 0.01,
		 1.0,  1.0,  0.0,  0.99, 0.99
	], dtype=NP.float32)
	
	UI_VERTICES = NP.array([
		-1.0,  1.0,  -1e-7,  0.0, 1.0,
		-1.0, -1.0,  -1e-7,  0.0, 0.0,
		 1.0, -1.0,  -1e-7,  1.0, 0.0,
		 1.0,  1.0,  -1e-7,  1.0, 1.0
	], dtype=NP.float32)

	INDICES = NP.array([
		0, 1, 2,
		2, 3, 0
	], dtype=NP.uint32)

	#Set up the scene quad VAO, VBO, and EBO
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

	#Set up the UI quad VAO, VBO, and EBO
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

	#Create framebuffer
	FBO, TCB, DTB, _, _ = CREATE_FBO(RENDER_RES)

	return VAO_QUAD, VAO_UI, FBO, TCB



def CREATE_FBO(SIZE, DEPTH=False, NORMALS=False):
	FBO = glGenFramebuffers(1)
	glBindFramebuffer(GL_FRAMEBUFFER, FBO)

	DTB, TCB, RBO, GBO = None, None, None, None
	if DEPTH:
		DTB = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, DTB)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32, int(SIZE.X), int(SIZE.Y), 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
		glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glBindTexture(GL_TEXTURE_2D, 0)

		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, DTB, 0)
		glDrawBuffer(GL_NONE)
		glReadBuffer(GL_NONE)

	else:
		TCB = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, TCB)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, int(SIZE.X), int(SIZE.Y), 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glBindTexture(GL_TEXTURE_2D, 0)
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, TCB, 0)

		RBO = glGenRenderbuffers(1) #Render Buffer Object
		glBindRenderbuffer(GL_RENDERBUFFER, RBO)
		glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, int(SIZE.X), int(SIZE.Y))
		glBindRenderbuffer(GL_RENDERBUFFER, 0)
		glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, RBO)

	if NORMALS:
		GBO = glGenTextures(1) #Geometry Buffer Object
		glBindTexture(GL_TEXTURE_2D, GBO)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB16F, int(SIZE.X), int(SIZE.Y), 0, GL_RGB, GL_FLOAT, None)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
		glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, GBO, 0)
		glDrawBuffers(1, [GL_COLOR_ATTACHMENT0])


	STATUS = glCheckFramebufferStatus(GL_FRAMEBUFFER)
	if STATUS != GL_FRAMEBUFFER_COMPLETE:
		raise Exception(f"Framebuffer is not complete.\nError: {STATUS}")

	glBindFramebuffer(GL_FRAMEBUFFER, 0)
	return FBO, TCB, DTB, RBO, GBO



def BUFFERS_INIT(VERTICES=None, INDICES=None, NORMALS=False):
	VERTEX_BUFFER_SIZE_INITIAL = 1024 * 1024  # 1MB for vertex buffer (adjust as needed)
	INDEX_BUFFER_SIZE_INITIAL = 256 * 1024  # 256KB for index buffer (adjust as needed)

	VAO_SCENE = glGenVertexArrays(1)
	VBO_SCENE = glGenBuffers(1)
	EBO_SCENE = glGenBuffers(1)

	glBindVertexArray(VAO_SCENE)

	glBindBuffer(GL_ARRAY_BUFFER, VBO_SCENE)
	if VERTICES is not None:
		glBufferData(GL_ARRAY_BUFFER, VERTICES.nbytes, VERTICES, GL_DYNAMIC_DRAW)
	else:
		glBufferData(GL_ARRAY_BUFFER, VERTEX_BUFFER_SIZE_INITIAL, None, GL_DYNAMIC_DRAW)  # Initialize with a default size

	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO_SCENE)
	if INDICES is not None:
		glBufferData(GL_ELEMENT_ARRAY_BUFFER, INDICES.nbytes, INDICES, GL_DYNAMIC_DRAW)
	else:
		glBufferData(GL_ELEMENT_ARRAY_BUFFER, INDEX_BUFFER_SIZE_INITIAL, None, GL_DYNAMIC_DRAW)  # Initialize with a default size

	stride = (3 + 2 + 3) * 4  # 3 position floats, 2 texture coordinate floats, 3 normal floats, each float is 4 bytes
	offset = 0

	glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset))
	glEnableVertexAttribArray(0)
	offset += 3 * 4  # Move offset to account for positions (3 floats * 4 bytes)

	# Texture coordinate attribute (location = 1)
	glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset))
	glEnableVertexAttribArray(1)
	offset += 2 * 4  # Move offset to account for texture coordinates (2 floats * 4 bytes)

	# Normal attribute (location = 2)
	glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset))
	glEnableVertexAttribArray(2)


	glBindBuffer(GL_ARRAY_BUFFER, 0)
	glBindVertexArray(0)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

	return VAO_SCENE, VBO_SCENE, EBO_SCENE



def UPDATE_BUFFERS(UNPROCESSED_VERTS, UNPROCESSED_INDICES, VBO, EBO):
	VERTICES = NP.array(UNPROCESSED_VERTS, dtype=NP.float32)
	INDICES = NP.array(UNPROCESSED_INDICES, dtype=NP.uint32)

	glBindBuffer(GL_ARRAY_BUFFER, VBO)
	VERTEX_BUFFER_SIZE = glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)
	
	if VERTEX_BUFFER_SIZE >= VERTICES.nbytes:
		glBufferSubData(GL_ARRAY_BUFFER, 0, VERTICES.nbytes, VERTICES)
	
	else: #Resize the buffer
		glBufferData(GL_ARRAY_BUFFER, VERTICES.nbytes, VERTICES, GL_DYNAMIC_DRAW)
	glBindBuffer(GL_ARRAY_BUFFER, 0)

	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
	INDEX_BUFFER_SIZE = glGetBufferParameteriv(GL_ELEMENT_ARRAY_BUFFER, GL_BUFFER_SIZE)
	if INDEX_BUFFER_SIZE >= INDICES.nbytes:
		glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, INDICES.nbytes, INDICES)
	else:
		print("Error: Index buffer size is too small. Resizing buffer.")
		glBufferData(GL_ELEMENT_ARRAY_BUFFER, INDICES.nbytes, INDICES, GL_DYNAMIC_DRAW)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

	return VBO, EBO



#Shadowmap creation


def RENDER_DEPTH_MAP(VAO_SHADOW, SHADOW_SHADER, PROJECTION, VIEW, FBO_SHADOW, SHADOWMAP_RESOLUTION, ENV_VAO_INDICES, SHEET_ID):
	#Bind the framebuffer for rendering
	glBindFramebuffer(GL_FRAMEBUFFER, FBO_SHADOW)
	glViewport(0, 0, int(SHADOWMAP_RESOLUTION.X), int(SHADOWMAP_RESOLUTION.Y))
	glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)

	#Use the shadow shader program
	glUseProgram(SHADOW_SHADER)

	#Set the shader uniform for the depth MVP matrix
	PROJECTION_MATRIX_LOC = glGetUniformLocation(SHADOW_SHADER, "projection")
	VIEW_MATRIX_LOC = glGetUniformLocation(SHADOW_SHADER, "view")
	MODEL_MATRIX_LOC = glGetUniformLocation(SHADOW_SHADER, "model")
	glUniformMatrix4fv(PROJECTION_MATRIX_LOC, 1, GL_FALSE, glm.value_ptr(PROJECTION))
	glUniformMatrix4fv(VIEW_MATRIX_LOC, 1, GL_FALSE, glm.value_ptr(VIEW))
	glUniformMatrix4fv(MODEL_MATRIX_LOC, 1, GL_FALSE, Matrix44.identity())

	#Set the shader uniform for the texture
	TEXTURE_LOC = glGetUniformLocation(SHADOW_SHADER, 'screenTexture')
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

	ERROR = glGetError()
	if ERROR != GL_NO_ERROR:
		raise Exception(f"OpenGL Error: {ERROR}")



def CREATE_LIGHT_MAPS(LIGHT, VAO_DATA, SHADOW_SHADER, SHADOWMAP_RESOLUTION, SHEET_ID):
	SCREEN = PG.display.set_mode(SHADOWMAP_RESOLUTION.TO_LIST(), DOUBLEBUF | OPENGL | HIDDEN)

	glEnable(GL_DEPTH_TEST)
	glDepthFunc(GL_LESS)
	glClearDepth(1.0)
	glEnable(GL_ALPHA_TEST)
	glAlphaFunc(GL_GREATER, 0.5)
	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	glEnable(GL_POLYGON_OFFSET_FILL)
	glPolygonOffset(10, 1)
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


	VAO_SHADOW, VBO_SHADOW, EBO_SHADOW = BUFFERS_INIT(VERTICES=VAO_DATA[0], INDICES=VAO_DATA[1], NORMALS=True)
	FBO_SHADOW, _, DTB_SHADOW, _, _ = CREATE_FBO(SHADOWMAP_RESOLUTION, DEPTH=True)

	LIGHT_PROJECTION_MATRIX = glm.mat4(Matrix44.perspective_projection(LIGHT.FOV, SHADOWMAP_RESOLUTION.X / SHADOWMAP_RESOLUTION.Y, 0.1, LIGHT.MAX_DISTANCE).tolist())
	LIGHT_VIEW_MATRIX = glm.lookAt(LIGHT.POSITION.CONVERT_TO_GLM_VEC3(), LIGHT.LOOK_AT.CONVERT_TO_GLM_VEC3(), glm.vec3(0.0, 1.0, 0.0))
	
	DEPTH_SPACE_MATRIX = LIGHT_PROJECTION_MATRIX * LIGHT_VIEW_MATRIX
	DEPTH_MVP_MATRIX = DEPTH_SPACE_MATRIX * glm.mat4(1.0) #Projection Matrix * View Matrix * Model Matrix -> M-V-P Matrix for shader.

	RENDER_DEPTH_MAP(VAO_SHADOW, SHADOW_SHADER, LIGHT_PROJECTION_MATRIX, LIGHT_VIEW_MATRIX, FBO_SHADOW, SHADOWMAP_RESOLUTION, VAO_DATA[1], SHEET_ID)

	LIGHT.SPACE_MATRIX = DEPTH_SPACE_MATRIX

	#Disable these, as they are reassigned as needed for the main FBO.
	glDisable(GL_DEPTH_TEST)
	glDisable(GL_ALPHA_TEST)
	glDisable(GL_BLEND)
	glDisable(GL_POLYGON_OFFSET_FILL)

	return DTB_SHADOW, LIGHT
