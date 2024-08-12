"""
[main.py]
Contains the initialisation of data (such as screen and environment) and main game loop.
Captures keyboard/mouse input, acts on them.
Acts almost like a "hub" for all other .py files in the directory - most interactions between files / subroutines are routed through here, inside the game loop.

______________________
Importing other sub-files;
-render.py
-physics.py
-texture_load.py
-load_scene.py
-log.py
-utils.py
"""
print("--")

#Import log.py, so that any ImportErrors can be properly logged.
from src.exct import log

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
	from imgs import texture_load
	from exct import render, physics, utils, ui
	from scenes import scene
	from exct.utils import *

except ImportError:
	log.ERROR("main.py", "Initial imports failed.")

#Formatting for the terminal output.
print("--\n")



try:
	#Import the memory-profiler I used in testing.
	from memory_profiler import profile

except ImportError:
	#If it fails, then this is not an issue
	#It is only used for the sake of testing anyhow, and is non-essential in actual program.
	pass



def MAIN():
	#try:
		"""
		[if main:]
		Preparing the game:
		- Initialise and configure PyGame.
		- Properly connect the OpenGL output to the PyGame window.

		[else:]
		Give error to log.py, something is set up severely incorrectly.
		"""

		#General preference-gathering & Data assignment.
		PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS
		DISPLAY_RESOLUTION = CONSTANTS["DISPLAY_RESOLUTION"]
		SCALING_FACTOR = CONSTANTS["RENDER_SCALING_FACTOR"]
		RENDER_RESOLUTION = DISPLAY_RESOLUTION / SCALING_FACTOR
		DISPLAY_CENTRE = DISPLAY_RESOLUTION / 2
		CONSTANTS["RENDER_RESOLUTION"] = RENDER_RESOLUTION

		#Print user-specified values for reference.
		print("Current user configs;")
		for OPTION in PREFERENCES:
			print(f"{OPTION}: {PREFERENCES[OPTION]}")
		print("\n")


		if PREFERENCES["DYNAMIC_SHADOWS"]:
			#Warn the user of issues relating to the preference DYNAMIC_SHADOWS.
			#This feature will likely be removed, as the process of shadow-mapping is too time consuming for real time.
			print("DYNAMIC_SHADOWS is enabled, this WILL cause issues.\nBe advised.")


		#Generic value assignments, like the colour of the void-fog and the states of keyboard inputs.
		VOID_COLOUR = RGBA(0, 0, 0, 0).TO_DECIMAL()
		PLAYER_COLLISION_CUBOID = CONSTANTS["PLAYER_COLLISION_CUBOID"]
		CAMERA_OFFSET = CONSTANTS["CAMERA_OFFSET"]
		FPS_CAP = PREFERENCES["FPS_LIMIT"]
		KEY_STATES = {
			PG.K_w: False, PG.K_s: False,			#Forward/Backwards keys
			PG.K_a: False, PG.K_d: False,			#Left/Right keys
			PG.K_e: False, PG.K_q: False,			#Interaction keys
			PG.K_SPACE: False, PG.K_LCTRL: False,	#Vertical control keys
			PG.K_LSHIFT: False, PG.K_x: False,		#Movement speed keys
			PG.K_RETURN: False,						#Debug key
			PG.K_c: False,							#Zoom key
			"CROUCH": False,						#If currently crouching (Toggle)
			"JUMP_GRACE": 0,						#Allows for a "grace period" to jump after leaving the floor
			"PAD_JUMP_PREV": False,					#To stop multiple GamePad jump inputs
		}



		#Assorted PyGame setup.
		PG.init()
		PG.joystick.init()
		JOYSTICK = None
		PAD_COUNT = PG.joystick.get_count()
		CLOCK = PG.time.Clock()


		#Create a GLFW window to initialise the OpenGL VAOs, Shaders, FBOs etc. within.
		if not glfw.init():
			raise Exception("GLFW could not be initialised.")

		glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
		OPENGL_SETUP_WINDOW = glfw.create_window(int(DISPLAY_RESOLUTION.X), int(DISPLAY_RESOLUTION.Y), "Hidden Window", None, None)
		if not OPENGL_SETUP_WINDOW:
			glfw.terminate()
			raise Exception("GLFW could not create OpenGL setup window.")
		glfw.make_context_current(OPENGL_SETUP_WINDOW)


		#PyOpenGL & VAO/VBO/EBO setup.
		
		RENDER_DATA, PHYS_DATA, SHEET_NAME, PLAYER_ID = scene.PREPARE_SCENE(PREFERENCES["SCENE"])
		BLANK_TEXTURE = texture_load.LOAD_SHEET("_")
		CURRENT_SHEET_ID = texture_load.LOAD_SHEET(SHEET_NAME)
		(ENV_VAO_VERTICES, ENV_VAO_INDICES), LIGHTS = RENDER_DATA


		#Mid-loading Shadow-Mapping
		SHADOWMAP_RESOLUTION = CONSTANTS["SHADOW_MAP_RESOLUTION"]
		SHEET_DATA = render.GET_TEXTURE_DATA(CURRENT_SHEET_ID, VECTOR_2D(2048, 2048), "COLOUR")
		glfw.terminate()
		for I, LIGHT in enumerate(LIGHTS):
			"""
			Iterate through every LIGHT class in the list of LIGHTs, and calculate their shadow-maps.
			Due to differing OpenGL contexts and issues with context sharing, I pass the texture data to the CREATE_SHADOW_MAPS function and convert back.
			Similar for the LIGHT.SHADOW_MAP data.
			"""
			if not glfw.init():
				raise Exception("GLFW could not be initialised.")

			glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
			SURFACE = glfw.create_window(int(SHADOWMAP_RESOLUTION.X), int(SHADOWMAP_RESOLUTION.Y), "Hidden Window", None, None)
			if not SURFACE:
				glfw.terminate()
				raise Exception("GLFW could not create window.")
			glfw.make_context_current(SURFACE)

			LIGHTS[I] = render.CREATE_SHADOW_MAPS(SURFACE, I, LIGHT, (NP.array(ENV_VAO_VERTICES, dtype=NP.float32), NP.array(ENV_VAO_INDICES, dtype=NP.uint32)), SHEET_DATA)



		#Set the context back as the main PG window, and convert any shadow map data.
		PG.display.set_caption("test4.2.4//main.py")
		PG.display.set_icon(PG.image.load("src\\imgs\\main.ico"))
		SCREEN = PG.display.set_mode(DISPLAY_RESOLUTION.TO_LIST(), PG.DOUBLEBUF | PG.OPENGL | PG.RESIZABLE)
		
		(SCENE_SHADER, QUAD_SHADER), (VAO_QUAD, VAO_UI, FBO_SCENE, TCB_SCENE), CURRENT_SHEET_ID, (VAO_SCENE, VBO_SCENE, EBO_SCENE), (MODEL_MATRIX, PROJECTION_MATRIX) = render.SET_PYGAME_CONTEXT(SHEET_NAME)

		for I, LIGHT in enumerate(LIGHTS):
			LIGHT.SHADOW_MAP = render.CREATE_TEXTURE_FROM_DATA(LIGHT.SHADOW_MAP_DATA, FILTER=GL_NEAREST)


		RUN = True
		PREVIOUS_FRAME, WINDOW_FOCUS = None, 0
		#Main game loop.
		while RUN:
			MOUSE_MOVE = [0, 0]
			PLAYER = PHYS_DATA[0][PLAYER_ID]
			FPS = utils.CLAMP(CLOCK.get_fps(), 0, FPS_CAP)
			"""
			Getting Mouse/Keyboard/GamePad inputs
			Getting other general events (Like window resize or window close events)
			"""
			
			for EVENT in PG.event.get():
				match EVENT.type:
					case PG.QUIT:
						#Quit the game.
						RUN = False

					case PG.ACTIVEEVENT:
						if EVENT.state == 2:
							#Display size changes handled
							WINDOW_FOCUS = EVENT.gain

					case PG.KEYDOWN:
						if EVENT.key in KEY_STATES:
							#Set the value in KEY_STATES to True.
							KEY_STATES[EVENT.key] = True
						
						match EVENT.key:
							case PG.K_q:
								#Q is the screenshot key.
								if PREVIOUS_FRAME != None:
									RAW_TIME = log.GET_TIME()
									CURRENT_TIME = f"{RAW_TIME[:8]}.{RAW_TIME[10:]}".replace(":", "-")
									render.SAVE_MAP(RENDER_RESOLUTION, PREVIOUS_FRAME, f"screenshots\\{CURRENT_TIME}.png", "COLOUR")
									print(f"Saved screenshot as [{CURRENT_TIME}.png]")

							case PG.K_ESCAPE:
								#Quit the game.
								RUN = False
							
							case PG.K_LCTRL:
								#Change collision hitbox size for crouching.
								CAMERA_OFFSET = CONSTANTS["CAMERA_OFFSET_CROUCH"]
								PLAYER.COLLISION_CUBOID = CONSTANTS["PLAYER_COLLISION_CUBOID_CROUCH"]
								PLAYER.POSITION -= (CONSTANTS["PLAYER_COLLISION_CUBOID"] - CONSTANTS["PLAYER_COLLISION_CUBOID_CROUCH"]) / 2

							case PG.K_c:
								#C is the zoom key.
								PROJECTION_MATRIX = Matrix44.perspective_projection(
									PREFERENCES["FOV"] // 3,
									(DISPLAY_RESOLUTION.X / DISPLAY_RESOLUTION.Y),
									CONSTANTS["MIN_VIEW_DIST"],
									CONSTANTS["MAX_VIEW_DIST"]
								)

					case PG.KEYUP:
						if EVENT.key in KEY_STATES:
							#Set the value in KEY_STATES to False.
							KEY_STATES[EVENT.key] = False
						
						match EVENT.key:
							case PG.K_LCTRL:
								#Uncrouch must also change hitbox size.
								CAMERA_OFFSET = CONSTANTS["CAMERA_OFFSET"]
								PLAYER.COLLISION_CUBOID = CONSTANTS["PLAYER_COLLISION_CUBOID"]
								PLAYER.POSITION += (CONSTANTS["PLAYER_COLLISION_CUBOID"] - CONSTANTS["PLAYER_COLLISION_CUBOID_CROUCH"])/4

							case PG.K_c:
								#Reset the FOV when zoom is toggled off.
								PROJECTION_MATRIX = Matrix44.perspective_projection(
									PREFERENCES["FOV"],
									(DISPLAY_RESOLUTION.X / DISPLAY_RESOLUTION.Y),
									CONSTANTS["MIN_VIEW_DIST"],
									CONSTANTS["MAX_VIEW_DIST"]
								)
					
					case PG.VIDEORESIZE:
						#Display size changes handled
						DISPLAY_RESOLUTION = VECTOR_2D(EVENT.w, EVENT.h)
						RENDER_RESOLUTION = DISPLAY_RESOLUTION / CONSTANTS["RENDER_SCALING_FACTOR"]  #Set render resolution to be half of the screen resolution
						CONSTANTS["RENDER_RESOLUTION"] = RENDER_RESOLUTION
						utils.CONSTANTS["DISPLAY_RESOLUTION"] = DISPLAY_RESOLUTION
						SCREEN = PG.display.set_mode(DISPLAY_RESOLUTION.TO_LIST(), PG.DOUBLEBUF | PG.OPENGL | PG.RESIZABLE)
						FBO_SCENE, TCB_SCENE, _, _, _ = render.CREATE_FBO(RENDER_RESOLUTION)
						glViewport(0, 0, int(RENDER_RESOLUTION.X), int(RENDER_RESOLUTION.Y))
						DISPLAY_CENTRE = DISPLAY_RESOLUTION / 2


					case PG.JOYDEVICEADDED:
						#New GamePad connected;
						NEW_PAD = [PG.joystick.Joystick(EVENT.device_index), None, None]
						JOYSTICK = utils.JOYSTICK_DEADZONE(NEW_PAD)

					case PG.JOYDEVICEREMOVED:
						#GamePad disconnected;
						JOYSTICK = None



			if JOYSTICK is not None:
				#GamePad specific controls
				JOYSTICK = utils.JOYSTICK_DEADZONE(JOYSTICK)
				PAD_JUMP = JOYSTICK[0].get_button(0)
				KEY_STATES[PG.K_x] = bool(JOYSTICK[0].get_button(2))
				PAD_ZOOM = bool(JOYSTICK[0].get_button(3))
				KEY_STATES[PG.K_c] = PAD_ZOOM
				KEY_STATES[PG.K_LSHIFT] = bool(JOYSTICK[0].get_button(8))
				PAD_CROUCH = JOYSTICK[0].get_button(9)

				if PAD_JUMP and not (KEY_STATES["PAD_JUMP_PREV"] or KEY_STATES[PG.K_SPACE]):
					KEY_STATES[PG.K_SPACE] = True
					KEY_STATES["PAD_JUMP_PREV"] = True

				elif not PAD_JUMP:
					KEY_STATES["PAD_JUMP_PREV"] = False


				if PAD_ZOOM:
					PROJECTION_MATRIX = Matrix44.perspective_projection(
						PREFERENCES["FOV"] // 3,
						(DISPLAY_RESOLUTION.X / DISPLAY_RESOLUTION.Y),
						CONSTANTS["MIN_VIEW_DIST"],
						CONSTANTS["MAX_VIEW_DIST"]
					)

				elif not PAD_ZOOM:
					PROJECTION_MATRIX = Matrix44.perspective_projection(
						PREFERENCES["FOV"],
						(DISPLAY_RESOLUTION.X / DISPLAY_RESOLUTION.Y),
						CONSTANTS["MIN_VIEW_DIST"],
						CONSTANTS["MAX_VIEW_DIST"]
					)


				if PAD_CROUCH:
					CAMERA_OFFSET = CONSTANTS["CAMERA_OFFSET_CROUCH"]

				else:
					CAMERA_OFFSET = CONSTANTS["CAMERA_OFFSET"]

				if JOYSTICK[0].get_button(1):
					RUN = False
					continue

				if JOYSTICK[0].get_axis(4) > -1 and PREFERENCES["DEV_TEST"]:
					PREFERENCES["NORMALS_DEBUG"] = True
				else:
					PREFERENCES["NORMALS_DEBUG"] = False

				if JOYSTICK[0].get_button(5) and PREVIOUS_FRAME is not None:
					RAW_TIME = log.GET_TIME()
					CURRENT_TIME = f"{RAW_TIME[:8]}.{RAW_TIME[10:]}".replace(":", "-")
					render.SAVE_MAP(RENDER_RESOLUTION, PREVIOUS_FRAME, f"screenshots\\{CURRENT_TIME}.png", "COLOUR")


			else:
				if KEY_STATES[PG.K_RETURN] and PREFERENCES["DEV_TEST"]:
					PREFERENCES["NORMALS_DEBUG"] = True
				else:
					PREFERENCES["NORMALS_DEBUG"] = False



			if (WINDOW_FOCUS == 1):
				#Mouse/Gamepad inputs for player view rotation only apply when window is focussed.
				ZOOM_MULT = 0.3333333 if KEY_STATES[PG.K_c] else 1.0 #Zoom changes sensitivity
				if JOYSTICK is not None:
					PLAYER.ROTATION.X += (JOYSTICK[2].X + PREFERENCES["AXIS_2_OFFSET"]) * PREFERENCES["PLAYER_SPEED_TURN_PAD"] * (FPS/PREFERENCES["FPS_LIMIT"]) * ZOOM_MULT
					PLAYER.ROTATION.Y -= (JOYSTICK[2].Y + PREFERENCES["AXIS_3_OFFSET"]) * PREFERENCES["PLAYER_SPEED_TURN_PAD"] * (FPS/PREFERENCES["FPS_LIMIT"]) * -ZOOM_MULT
				
				if EVENT.type == PG.MOUSEMOTION:
					MOUSE_MOVE = [EVENT.pos[0] - (DISPLAY_RESOLUTION.X // 2), EVENT.pos[1] - (DISPLAY_RESOLUTION.Y // 2)]
					PLAYER.ROTATION.X += MOUSE_MOVE[0] * PREFERENCES["PLAYER_SPEED_TURN_MOUSE"] * (FPS/PREFERENCES["FPS_LIMIT"]) * ZOOM_MULT
					PLAYER.ROTATION.Y -= MOUSE_MOVE[1] * PREFERENCES["PLAYER_SPEED_TURN_MOUSE"] * (FPS/PREFERENCES["FPS_LIMIT"]) * -ZOOM_MULT
				
				#Limit the camera's vertical movement to ~±90*
				PLAYER.ROTATION = PLAYER.ROTATION.CLAMP(Y_BOUNDS=(-89.9, 89.9))
			

			if WINDOW_FOCUS == 0:
				#If window is not in focus, set the FPS to the "idle", lower value and show the mouse.
				PG.mouse.set_visible(True)
				FPS_CAP = PREFERENCES["FPS_LOW"]
			else:
				#Otherwise move mouse to centre of screen (hidden) and use the "active", higher FPS.
				PG.mouse.set_pos(DISPLAY_CENTRE.TO_LIST())
				PG.mouse.set_visible(False)	
				FPS_CAP = PREFERENCES["FPS_LIMIT"]
			
			CLOCK.tick_busy_loop(FPS_CAP)


			#Set player data, Calculate physics, Get player data.
			PHYS_DATA[0][PLAYER_ID] = PLAYER
			PHYS_DATA = physics.UPDATE_PHYSICS(PHYS_DATA, FPS, KEY_STATES, JOYSTICK)
			PLAYER = PHYS_DATA[0][PLAYER_ID]
			CAMERA_POSITION = PLAYER.POSITION + CAMERA_OFFSET


			#Give the VAO/VBO/EBO the data for any "dynamic" objects such as a sprite's coordinates.
			#Applied over the top of other, environmental/static objects like Tris.
			COPIED_VAO_VERTICES, COPIED_VAO_INDICES = render.SCENE(PHYS_DATA, [ENV_VAO_VERTICES, ENV_VAO_INDICES], PLAYER)
			VBO_SCENE, EBO_SCENE = render.UPDATE_BUFFERS(COPIED_VAO_VERTICES, COPIED_VAO_INDICES, VBO_SCENE, EBO_SCENE)
			CAMERA_VIEW_MATRIX, CAMERA_LOOK_AT_VECTOR = render.CALC_VIEW_MATRIX(CAMERA_POSITION, PLAYER.ROTATION.RADIANS())


			#Pre-FBO render tasks (UI, dynamic shadows)

			if PREFERENCES["DYNAMIC_SHADOWS"]:
				#If dynamic shadows are enabled, recalculate the shadow map every frame.
				#Not reccomended to use, but is present and incredibly broken.

				for LIGHT in LIGHTS:
					LIGHTS[I] = render.CREATE_SHADOW_MAPS(SURFACE, I, LIGHT, (NP.array(COPIED_VAO_VERTICES, dtype=NP.float32), NP.array(COPIED_VAO_INDICES, dtype=NP.uint32)), SHEET_DATA)


				#Set OpenGL context back to main display.
				SCREEN = PG.display.set_mode(DISPLAY_RESOLUTION.TO_LIST(), PG.DOUBLEBUF | PG.OPENGL | PG.RESIZABLE)
				(SCENE_SHADER, QUAD_SHADER), (VAO_QUAD, VAO_UI, FBO_SCENE, TCB_SCENE), CURRENT_SHEET_ID, (VAO_SCENE, VBO_SCENE, EBO_SCENE), (MODEL_MATRIX, PROJECTION_MATRIX) = render.SET_PYGAME_CONTEXT(SHEET_NAME)


				for I, LIGHT in enumerate(LIGHTS):
					#Get shadow data from the map.
					LIGHT.SHADOW_MAP = render.CREATE_TEXTURE_FROM_DATA(LIGHT.SHADOW_MAP_DATA, FILTER=GL_NEAREST)
					if PREFERENCES["DEBUG_MAPS"]:
						render.SAVE_MAP(CONSTANTS["SHADOW_MAP_RESOLUTION"], LIGHT.SHADOW_MAP, f"debug_maps\\depth_map_{I}.png", "DEPTH", MIN_DISTANCE=LIGHT.MIN_DISTANCE, MAX_DISTANCE=LIGHT.MAX_DISTANCE)

			
			#Render the current UI with the player's data (Health, etc.)
			UI_TEXTURE_ID = ui.HUD(PLAYER, FPS)
			if PREFERENCES["DEBUG_UI"]:
				#Save map if DEBUG_UI is enabled.
				render.SAVE_MAP(CONSTANTS["UI_RESOLUTION"], UI_TEXTURE_ID, f"screenshots\\debug_maps\\colour_map_ui.png", "COLOUR")


			#Rendering the main scene.

			glLoadIdentity()

			#Bind FBO, set relevant OpenGL configs such as the void fog colour or the current texture.
			glBindFramebuffer(GL_FRAMEBUFFER, FBO_SCENE)
			glUseProgram(SCENE_SHADER)
			glViewport(0, 0, int(RENDER_RESOLUTION.X), int(RENDER_RESOLUTION.Y))
			glClearColor(VOID_COLOUR.R, VOID_COLOUR.G, VOID_COLOUR.B, VOID_COLOUR.A)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			glClearDepth(1.0)
			glActiveTexture(GL_TEXTURE0)
			glBindTexture(GL_TEXTURE_2D, CURRENT_SHEET_ID)


			#Get locations for and provide data for the scene shader's uniforms (such as CAMERA_POSITION).
			MODEL_LOC = glGetUniformLocation(SCENE_SHADER, 'MODEL_MATRIX')
			VIEW_LOC = glGetUniformLocation(SCENE_SHADER, 'VIEW_MATRIX')
			PROJECTION_LOC = glGetUniformLocation(SCENE_SHADER, 'PROJECTION_MATRIX')
			TEXTURE_LOC = glGetUniformLocation(SCENE_SHADER, 'TRI_TEXTURE')
			VIEW_DIST_LOC = glGetUniformLocation(SCENE_SHADER, 'VIEW_MAX_DIST')
			CAMERA_POS_LOC = glGetUniformLocation(SCENE_SHADER, 'CAMERA_POSITION')
			#VOID_COLOUR_LOC = glGetUniformLocation(SCENE_SHADER, 'VOID_COLOUR')
			LIGHT_COUNT_LOC = glGetUniformLocation(SCENE_SHADER, "LIGHT_COUNT")
			NORMAL_DEBUG_LOC = glGetUniformLocation(SCENE_SHADER, "NORMAL_DEBUG")

			glUniformMatrix4fv(MODEL_LOC, 1, GL_FALSE, MODEL_MATRIX)
			glUniformMatrix4fv(VIEW_LOC, 1, GL_FALSE, CAMERA_VIEW_MATRIX)
			glUniformMatrix4fv(PROJECTION_LOC, 1, GL_FALSE, PROJECTION_MATRIX)
			#glUniformMatrix4fv(VOID_COLOUR_LOC, 1, GL_FALSE, glm.value_ptr(VOID_COLOUR.CONVERT_TO_GLM_VEC4()))
			glUniform1i(LIGHT_COUNT_LOC, len(LIGHTS))
			glUniform1i(NORMAL_DEBUG_LOC, PREFERENCES["NORMALS_DEBUG"])
			glUniform1f(VIEW_DIST_LOC, CONSTANTS["MAX_VIEW_DIST"])
			glUniform3fv(CAMERA_POS_LOC, 1, glm.value_ptr(CAMERA_POSITION.CONVERT_TO_GLM_VEC3()))
			glUniform1i(TEXTURE_LOC, 0)


			for I, LIGHT in enumerate(LIGHTS):
				#Iterate through every light, again, to hand their data to the glsl equivalent struct to the python class.

				#Check if the light's flag is "enabled" in the list of FLAG_STATES
				#if not FLAG_STATES[LIGHT.FLAG]:
				#	continue


				LIGHT_POSITION_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].POSITION")
				LIGHT_LOOK_AT_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].LOOK_AT")
				LIGHT_COLOUR_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].COLOUR")
				LIGHT_INTENSITY_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].INTENSITY")
				LIGHT_FOV_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].FOV")
				LIGHT_MAX_DIST_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].MAX_DIST")
				LIGHT_SPACE_MATRIX_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].LIGHT_SPACE_MATRIX")
				SHADOW_MAP_LOC = glGetUniformLocation(SCENE_SHADER, f'LIGHTS[{I}].SHADOW_MAP')

				glUniform3fv(LIGHT_POSITION_LOC, 1, glm.value_ptr(LIGHT.POSITION.CONVERT_TO_GLM_VEC3()))
				glUniform3fv(LIGHT_LOOK_AT_LOC, 1, glm.value_ptr(LIGHT.LOOK_AT.CONVERT_TO_GLM_VEC3()))
				glUniform3fv(LIGHT_COLOUR_LOC, 1, glm.value_ptr(LIGHT.COLOUR.CONVERT_TO_GLM_VEC4()))
				glUniform1f(LIGHT_INTENSITY_LOC, LIGHT.INTENSITY)
				glUniform1f(LIGHT_FOV_LOC, LIGHT.FOV)
				glUniform1f(LIGHT_MAX_DIST_LOC, LIGHT.MAX_DISTANCE)
				glUniformMatrix4fv(LIGHT_SPACE_MATRIX_LOC, 1, GL_FALSE, glm.value_ptr(LIGHT.SPACE_MATRIX))
				glActiveTexture(GL_TEXTURE1 + I)
				glBindTexture(GL_TEXTURE_2D, LIGHT.SHADOW_MAP)
				glUniform1i(SHADOW_MAP_LOC, I + 1)


			#Finally, instruct OpenGL to render the triangles of the scene with their assigned data, texture, etc.
			glActiveTexture(GL_TEXTURE0)
			glBindVertexArray(VAO_SCENE)
			glBindTexture(GL_TEXTURE_2D, CURRENT_SHEET_ID)
			glDrawElements(GL_TRIANGLES, len(COPIED_VAO_INDICES), GL_UNSIGNED_INT, None)
			glBindTexture(GL_TEXTURE_2D, 0)
			glBindVertexArray(0)

			glBindFramebuffer(GL_FRAMEBUFFER, 0)


			#Reset values to align with the display size.
			glViewport(0, 0, int(DISPLAY_RESOLUTION.X), int(DISPLAY_RESOLUTION.Y))
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			
			glUseProgram(QUAD_SHADER)

			RESOLUTION_LOC = glGetUniformLocation(QUAD_SHADER, "RESOLUTION")
			SCALING_FACTOR_LOC = glGetUniformLocation(QUAD_SHADER, "PIXEL_SIZE")
			SCREEN_TEXTURE_LOC = glGetUniformLocation(QUAD_SHADER, "SCREEN_TCB")
			glUniform2f(RESOLUTION_LOC, RENDER_RESOLUTION.X, RENDER_RESOLUTION.Y)
			glUniform1f(SCALING_FACTOR_LOC, SCALING_FACTOR)
			glUniform1i(SCREEN_TEXTURE_LOC, 0)



			#Save the current frame, for a screenshot the next frame.
			PREVIOUS_FRAME = TCB_SCENE

			#Draw the current frame to a quad in the camera's view to apply any effects to it.
			glBindVertexArray(VAO_QUAD)
			glActiveTexture(GL_TEXTURE0)
			glBindTexture(GL_TEXTURE_2D, TCB_SCENE)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
			glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
			glBindTexture(GL_TEXTURE_2D, 0)
			glBindVertexArray(0)
			

			#Draw UI on a quad slightly closer to the camera to overlay on the scene.			
			glBindVertexArray(VAO_UI)
			glActiveTexture(GL_TEXTURE0)
			glBindTexture(GL_TEXTURE_2D, UI_TEXTURE_ID)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
			glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
			glBindTexture(GL_TEXTURE_2D, 0)
			glBindVertexArray(0)


			#Finally delete the current UI data to prevent a memory overflow
			#Display current frame to user.
			glDeleteTextures([UI_TEXTURE_ID])
			PG.display.flip()


		#Quitting/Deleting all that needs to be done, when RUN == False
		FRAME_BUFFERS = [FBO_SCENE,]
		VERTEX_BUFFERS = [VAO_SCENE, VAO_QUAD, VAO_UI]
		DATA_BUFFERS = [VBO_SCENE, EBO_SCENE, TCB_SCENE]

		glDeleteFramebuffers(len(FRAME_BUFFERS), FRAME_BUFFERS)
		glDeleteVertexArrays(len(VERTEX_BUFFERS), VERTEX_BUFFERS)
		glDeleteBuffers(len(DATA_BUFFERS), DATA_BUFFERS)
		glDeleteTextures([CURRENT_SHEET_ID, PREVIOUS_FRAME])

		PG.mouse.set_visible(True)
		PG.joystick.quit()
		PG.quit()
		quit()

	#except Exception as E:
		#log.ERROR("Mainloop", E)



if __name__ == "__main__":
	MAIN()

else:
	# If this isn't being run as __main__, something has gone very wrong and needs to be logged - it is not intended to ever occur.
	log.ERROR("main.py", "IsNotMain")
