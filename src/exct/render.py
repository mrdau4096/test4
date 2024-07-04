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

PREFERENCES, CONSTANTS = utils.GET_CONFIGS()



def SCENE(PHYS_DATA, TEXTURE_DATA, ENV_VAO_DATA, PLAYER):
	#Renders the entire scene, from the positional and texture datas included.
	ENV_VAO_VERTICES, ENV_VAO_INDICES = ENV_VAO_DATA
	COPIED_VERTS, COPIED_INDICES = copy.copy(ENV_VAO_VERTICES), copy.copy(ENV_VAO_INDICES)
	for ID, PHYS_OBJECT in PHYS_DATA[0].items(): #All physics objects, such as Items and Cubes.
		COPIED_VERTS, COPIED_INDICES = PROCESS_OBJECT(PHYS_OBJECT, PLAYER, COPIED_VERTS, COPIED_INDICES)
	for ID, DYNAMIC_STATIC in PHYS_DATA[1][1].items(): #All "dynamic statics" such as static sprites, that must face camera.
		COPIED_VERTS, COPIED_INDICES = PROCESS_OBJECT(DYNAMIC_STATIC, PLAYER, COPIED_VERTS, COPIED_INDICES)

	return [COPIED_VERTS, COPIED_INDICES]



def PROCESS_OBJECT(OBJECT_DATA, PLAYER, COPIED_VERTS, COPIED_INDICES):
	OBJECT_TYPE = type(OBJECT_DATA)
	if OBJECT_TYPE in [SPRITE_STATIC, ITEM, ENEMY]:
		COORDINATES = utils.CALC_SPRITE_POINTS(OBJECT_DATA.POSITION, PLAYER.POSITION, OBJECT_DATA.DIMENTIONS_2D)
		COPIED_VERTS, COPIED_INDICES = OBJECT_VAO_MANAGER(OBJECT_TYPE, COORDINATES, OBJECT_DATA.TEXTURE_INFO, [COPIED_VERTS, COPIED_INDICES])

	return COPIED_VERTS, COPIED_INDICES



def GL_ERRORCHECK():
	#Checks for any errors with OpenGL, and reports them to the shell (debugging)
	ERROR = glGetError()
	if ERROR != GL_NO_ERROR:
		print("OpenGL ERROR:", ERROR)
	else:
		print("OpenGL ERROR: None")



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



def BUFFERS_INIT(VERTICES=None, INDICES=None):
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

	glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(0))
	glEnableVertexAttribArray(0)
	glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * 4, ctypes.c_void_p(12))
	glEnableVertexAttribArray(1)

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
		eye = PYRR_CAMERA_POSITION,
		target = LOOK_AT,
		up = UPWARD
	)

	return VIEW_MATRIX, LOOK_AT



def FBO_QUAD_INIT(RENDER_RES):
	QUAD_VERTICES = NP.array([
		-1.0,  1.0,  0.0,	0.01, 0.99,
		-1.0, -1.0,  0.0,	0.01, 0.01,
		 1.0, -1.0,  0.0,	0.99, 0.01,
		 1.0,  1.0,  0.0,	0.99, 0.99
	], dtype=NP.float32)
	
	UI_VERTICES = NP.array([
		-1.0,  1.0,  -0.0001,	0, 1,
		-1.0, -1.0,  -0.0001,	0, 0,
		 1.0, -1.0,  -0.0001,	1, 0,
		 1.0,  1.0,  -0.0001,	1, 1
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
	FBO, TCB, DTB = CREATE_FBO(RENDER_RES)

	return VAO_QUAD, VAO_UI, FBO, TCB



def CREATE_FBO(SIZE, DEPTH=False):
	FBO = glGenFramebuffers(1)
	glBindFramebuffer(GL_FRAMEBUFFER, FBO)

	#Texture Colour Buffer
	TCB = glGenTextures(1)
	glBindTexture(GL_TEXTURE_2D, TCB)
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, int(SIZE.X), int(SIZE.Y), 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
	glBindTexture(GL_TEXTURE_2D, 0)
	glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, TCB, 0)

	DTB = None
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
		RBO = glGenRenderbuffers(1)#Render Buffer Object
		glBindRenderbuffer(GL_RENDERBUFFER, RBO)
		glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, int(SIZE.X), int(SIZE.Y))
		glBindRenderbuffer(GL_RENDERBUFFER, 0)
		glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, RBO)


	if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
		raise Exception("Framebuffer is not complete.")

	glBindFramebuffer(GL_FRAMEBUFFER, 0)
	return FBO, TCB, DTB


def RENDER_DEPTH_MAP(VAO_SHADOW, SHADOW_SHADER, DEPTH_MVP_MATRIX, FBO_SHADOW, SHADOWMAP_RESOLUTION, ENV_VAO_INDICES, SHEET_ID):
	#Bind the framebuffer for rendering
	glBindFramebuffer(GL_FRAMEBUFFER, FBO_SHADOW)
	glViewport(0, 0, int(SHADOWMAP_RESOLUTION.X), int(SHADOWMAP_RESOLUTION.Y))
	glClear(GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)

	#Use the shadow shader program
	glUseProgram(SHADOW_SHADER)

	SAVE_COLOURMAP(VECTOR_2D(2048, 2048), SHEET_ID, "colourmap.png")

	#Set the shader uniform for the depth MVP matrix
	DEPTH_MVP_MATRIX_LOC = glGetUniformLocation(SHADOW_SHADER, "depthMVP")
	glUniformMatrix4fv(DEPTH_MVP_MATRIX_LOC, 1, GL_FALSE, glm.value_ptr(DEPTH_MVP_MATRIX))

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




def SAVE_DEPTHMAP(SHADOWMAP_RESOLUTION, DEPTH_MAP, FILE_NAME, MIN_DISTANCE, MAX_DISTANCE, DEBUG=False):
	glBindTexture(GL_TEXTURE_2D, DEPTH_MAP)
	DEPTH_DATA = glGetTexImage(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, GL_FLOAT)
	DEPTH_DATA = NP.frombuffer(DEPTH_DATA, dtype=NP.float32).reshape(int(SHADOWMAP_RESOLUTION.Y), int(SHADOWMAP_RESOLUTION.X))
	DEPTH_DATA = NP.flipud(DEPTH_DATA)
	if DEBUG: print("Depth data before normalization:\n", DEPTH_DATA)
	glBindTexture(GL_TEXTURE_2D, 0)

	# Normalize depth data and ensure no NaN values
	DEPTH_MIN = utils.CLAMP(NP.min(DEPTH_DATA), MIN_DISTANCE, MAX_DISTANCE)
	DEPTH_MAX = utils.CLAMP(NP.max(DEPTH_DATA), MIN_DISTANCE, MAX_DISTANCE)
	if DEBUG:  print(f"Depth range: min={DEPTH_MIN}, max={DEPTH_MAX}")
	if DEPTH_MIN == DEPTH_MAX:
		NORMALISED_DEPTH_MAP = NP.zeros_like(DEPTH_DATA)
	else:
		NORMALISED_DEPTH_MAP = (DEPTH_DATA - DEPTH_MIN) / (DEPTH_MAX - DEPTH_MIN + 1e-7)
		if DEBUG: print(NORMALISED_DEPTH_MAP)
	IMAGE_DEPTH_MAP = Image.fromarray((NORMALISED_DEPTH_MAP * 255).astype(NP.uint8), mode='L')
	if NP.any(NP.isnan(NORMALISED_DEPTH_MAP)):
		raise ValueError("[WARNING] // NaN values found in shadow depth data; Issues may ensue.")
		NORMALISED_DEPTH_MAP = NP.nan_to_num(NORMALISED_DEPTH_MAP)

	IMAGE_DEPTH_MAP.save(FILE_NAME)



def SAVE_COLOURMAP(RESOLUTION, COLOUR_MAP, FILE_NAME, DEBUG=False):
	glBindTexture(GL_TEXTURE_2D, COLOUR_MAP)
	COLOUR_DATA = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGB, GL_UNSIGNED_BYTE)
	COLOUR_DATA = NP.frombuffer(COLOUR_DATA, dtype=NP.uint8).reshape(int(RESOLUTION.Y), int(RESOLUTION.X), 3)
	
	if DEBUG: print("Colour data before processing:\n", COLOUR_DATA)
		
	glBindTexture(GL_TEXTURE_2D, 0)

	#Flip the image data vertically
	COLOUR_DATA = NP.flipud(COLOUR_DATA)
	
	IMAGE_COLOUR_MAP = Image.fromarray(COLOUR_DATA, mode='RGB')
	
	if NP.any(NP.isnan(COLOUR_DATA)):
		raise ValueError("[WARNING] // NaN values found in colour data; Issues may ensue.")
	
	IMAGE_COLOUR_MAP.save(FILE_NAME)


def CREATE_LIGHT_DEPTHMAP(LIGHT, VAO_DATA, SHADOW_SHADER, SHADOWMAP_RESOLUTION, SHEET_ID):
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

	VAO_SHADOW, VBO_SHADOW, EBO_SHADOW = BUFFERS_INIT(VERTICES=VAO_DATA[0], INDICES=VAO_DATA[1])
	FBO_SHADOW, _, DTB_SHADOW = CREATE_FBO(SHADOWMAP_RESOLUTION, DEPTH=True)

	LIGHT_PROJECTION_MATRIX = glm.mat4(Matrix44.perspective_projection(LIGHT.FOV, SHADOWMAP_RESOLUTION.X / SHADOWMAP_RESOLUTION.Y, 0.1, LIGHT.MAX_DISTANCE).tolist())
	LIGHT_VIEW_MATRIX = glm.lookAt(LIGHT.POSITION.CONVERT_TO_GLM_VEC3(), LIGHT.LOOK_AT.CONVERT_TO_GLM_VEC3(), glm.vec3(0.0, 1.0, 0.0))
	
	DEPTH_SPACE_MATRIX = LIGHT_PROJECTION_MATRIX * LIGHT_VIEW_MATRIX
	DEPTH_MVP_MATRIX = DEPTH_SPACE_MATRIX * glm.mat4(1.0) #Projection Matrix * View Matrix * Model Matrix -> M-V-P Matrix for shader.

	RENDER_DEPTH_MAP(VAO_SHADOW, SHADOW_SHADER, DEPTH_MVP_MATRIX, FBO_SHADOW, SHADOWMAP_RESOLUTION, VAO_DATA[1], SHEET_ID)

	LIGHT.SPACE_MATRIX = DEPTH_SPACE_MATRIX

	#Disable these, as they are reassigned as needed for the main FBO.
	glDisable(GL_DEPTH_TEST)
	glDisable(GL_ALPHA_TEST)
	glDisable(GL_BLEND)
	glDisable(GL_POLYGON_OFFSET_FILL)

	return DTB_SHADOW, LIGHT



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



def OBJECT_VAO_MANAGER(CLASS_TYPE, POINTS, TEXTURE_DATA, VAO_DATA):
	VAO_VERTICES, VAO_INDICES = VAO_DATA
	NEW_VERTICES, NEW_INDICES = [], []

	INDEX_OFFSET = len(VAO_VERTICES)

	if CLASS_TYPE == CUBE_STATIC:#Cube
		FACE_ORDER = [
			(0, 1, 3, 2),	# Bottom face
			(4, 6, 2, 0),	# Left face
			(5, 7, 3, 1),	# Right face
			(5, 4, 0, 1),	# Front face
			(7, 6, 2, 3),	# Back face
			(4, 5, 7, 6)	# Top face
		]

		CUBE_TEXTURE_DATA = [TEXTURE_DATA[0], TEXTURE_DATA[1], TEXTURE_DATA[1], TEXTURE_DATA[1], TEXTURE_DATA[1], TEXTURE_DATA[2]]

		for FACE_INDEX, TEX_COORDS in enumerate(CUBE_TEXTURE_DATA):
			FACE_INDICES = FACE_ORDER[FACE_INDEX]
			offset_indices = [INDEX_OFFSET + i for i in range(4)]

			NEW_INDICES.extend([
				offset_indices[0], offset_indices[1], offset_indices[2],
				offset_indices[2], offset_indices[3], offset_indices[0]
			])

			for I, idx in enumerate(FACE_INDICES):
				X, Y, Z = POINTS[idx].X, POINTS[idx].Y, POINTS[idx].Z
				TEX_COORD = TEX_COORDS[I]
				U, V = TEX_COORD.X, TEX_COORD.Y
				NEW_VERTICES.append([X, Y, Z, U, V])

			INDEX_OFFSET += 4

		VAO_VERTICES.extend(NEW_VERTICES)
		VAO_INDICES.extend(NEW_INDICES)

	elif CLASS_TYPE in (QUAD, SPRITE_STATIC, ITEM, INTERACTABLE, ENEMY):#Quad
		FACE_ORDER = (0, 1, 2, 3)
		NEW_INDICES.extend([INDEX_OFFSET, INDEX_OFFSET + 1, INDEX_OFFSET + 2, INDEX_OFFSET + 2, INDEX_OFFSET + 3, INDEX_OFFSET])

		for I, INDEX in enumerate(FACE_ORDER):
			TEX_COORD = TEXTURE_DATA[I]
			X, Y, Z = POINTS[INDEX].X, POINTS[INDEX].Y, POINTS[INDEX].Z
			U, V = TEX_COORD.X, TEX_COORD.Y
			NEW_VERTICES.append([X, Y, Z, U, V])

		VAO_VERTICES.extend(NP.array(NEW_VERTICES, dtype=NP.float32))
		VAO_INDICES.extend(NP.array(NEW_INDICES, dtype=NP.uint32).flatten())

	elif CLASS_TYPE == TRI:#Tri
		FACE_ORDER = (0, 1, 2)
		NEW_INDICES.extend([INDEX_OFFSET, INDEX_OFFSET + 1, INDEX_OFFSET + 2])
		for I, INDEX in enumerate(FACE_ORDER):
			TEX_COORD = TEXTURE_DATA[I]
			X, Y, Z = POINTS[INDEX].X, POINTS[INDEX].Y, POINTS[INDEX].Z
			U, V = TEX_COORD.X, TEX_COORD.Y
			NEW_VERTICES.append([X, Y, Z, U, V])

		VAO_VERTICES.extend(NP.array(NEW_VERTICES, dtype=NP.float32))
		VAO_INDICES.extend(NP.array(NEW_INDICES, dtype=NP.uint32).flatten())

	return (VAO_VERTICES, VAO_INDICES)