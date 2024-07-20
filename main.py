"""
[main.py]
Contains the initialisation of data (such as screen and environment) and main game loop.
Captures keyboard/mouse input, acts on them.
Acts almost like a "hub" for all other .py files in the directory - most interactions between files / subroutines are routed through here, inside the game loop.

______________________
Importing other files;
-render.py
-physics.py
-texture_load.py
-load_scene.py
-log.py
-utils.py
"""
print("--")

try:
	import sys, os
	import math as maths
	print("Imported Module(s) // sys, math, os") #Successfully imported said modules.
	os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1" #Hides the Pygame default welcome message in console.
	sys.path.append("src") #Access the source subfolder in the path, for the data.
	from exct import log


	#All sub-files for the program - think of main.py as a hub for these other files to interface within.



	from imgs import texture_load
	from exct import render, physics, utils, ui
	from scenes import scene
	from exct.utils import *

	#Import the memory-profiler I used in testing.
	try:
		from memory_profiler import profile

	except ImportError:
		pass #If it fails, then this is not an issue - It is only used for the sake of testing anyhow, and is non-essential in actual operation.


	"""
	Importing external modules from "modules"
	-PyGame
	-PyOpenGL
	-GLM
	-Pyrr
	-NumPy
	"""
	sys.path.append("modules.zip")
	import pygame as PG
	from pygame.locals import *
	from pygame import *
	print("Imported Module(s) // PyGame")
	from OpenGL.GL import *
	from OpenGL.GLU import *
	from OpenGL.GL.shaders import compileShader, compileProgram
	print("Imported Module(s) // PyOpenGL")
	import glm
	print("Imported Module(s) // PyGLM")
	from pyrr import Matrix44, Vector3
	print("Imported Module(s) // Pyrr")
	import numpy as NP
	print("Imported Module(s) // NumPy\n--\n")

except Exception as E:
	log.ERROR("main.py, init()", E)
	quit()



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

		# General preference-gathering.
		PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS
		DISPLAY_RESOLUTION = CONSTANTS["DISPLAY_RESOLUTION"]
		SCALING_FACTOR = CONSTANTS["RENDER_SCALING_FACTOR"]
		RENDER_RESOLUTION = DISPLAY_RESOLUTION / SCALING_FACTOR
		print("Current user configs;")
		for OPTION in PREFERENCES:
			print(f"{OPTION}: {PREFERENCES[OPTION]}")
		print("\n")

		#PyGame setup.
		CLOCK = PG.time.Clock()
		PG.init()
		PG.joystick.init()
		JOYSTICK = None
		PAD_COUNT = PG.joystick.get_count()
		SCREEN = PG.display.set_mode(DISPLAY_RESOLUTION.TO_LIST(), DOUBLEBUF | OPENGL | RESIZABLE | HIDDEN)
		PG.display.set_caption("test4.2.3b//main.py")
		PG.display.set_icon(PG.image.load("src\\imgs\\main.ico"))
		DISPLAY_CENTRE = DISPLAY_RESOLUTION / 2


		#PyOpenGL setup.
		SCENE_SHADER, QUAD_SHADER, SHADOW_SHADER = render.SHADER_INIT()
		VAO_QUAD, VAO_UI, SCENE_FBO, SCENE_TCB = render.FBO_QUAD_INIT(RENDER_RESOLUTION)

		VOID_COLOUR = RGBA(0, 0, 0, 0).TO_DECIMAL()#RGBA(47, 121, 221, 255).TO_DECIMAL()
		PLAYER_COLLISION_CUBOID = CONSTANTS["PLAYER_COLLISION_CUBOID"]
		KEY_STATES = {
			PG.K_w: False,
			PG.K_s: False,
			PG.K_a: False,
			PG.K_d: False,
			PG.K_SPACE: False,
			PG.K_LCTRL: False,
			PG.K_LSHIFT: False,
			PG.K_RETURN: False,
			PG.K_c: False,
			PG.K_x: False,
			"CROUCH": False,
			"JUMP_GRACE": 0,
			"PAD_JUMP_PREV": False,
		}

		"""
		Main Game Loop - handles rendering, inputs, physics updates and so on. Only plays while RUN is true.
		Also any variables required are set up, such as (but not limited to):
		- KEY_STATES {Any keys required as inputs are logged here, to aid in detection within the loop}
		- PLAYER_COLLISION_CUBOID {The shape of the player's pre-defined "Hitbox", for the physics system}
		- RENDER_DATA / PHYS_DATA {Data for render.py and physics.py respectively}
		- etc.
		"""
		RENDER_DATA, PHYS_DATA, CURRENT_SHEET_ID, PLAYER_ID = scene.PREPARE_SCENE(PREFERENCES["SCENE"])
		BLANK_TEXTURE = texture_load.LOAD_SHEET("_")
		(ENV_VAO_VERTICES, ENV_VAO_INDICES), LIGHTS = RENDER_DATA

		SHADOWMAP_RESOLUTION = CONSTANTS["SHADOW_MAP_RESOLUTION"]

		for I, LIGHT in enumerate(LIGHTS):
			SHADOW_MAP, LIGHTS[I] = render.CREATE_LIGHT_MAPS(LIGHT, (NP.array(ENV_VAO_VERTICES, dtype=NP.float32), NP.array(ENV_VAO_INDICES, dtype=NP.uint32)), SHADOW_SHADER, CONSTANTS["SHADOW_MAP_RESOLUTION"], CURRENT_SHEET_ID)
			LIGHT.SHADOW_MAP = SHADOW_MAP
			
			if PREFERENCES["DEBUG_MAPS"]:
				render.SAVE_MAP(CONSTANTS["SHADOW_MAP_RESOLUTION"], SHADOW_MAP, f"screenshots\\debug_maps\\depth_map_{I}.png", "DEPTH", MIN_DISTANCE=LIGHT.MIN_DISTANCE, MAX_DISTANCE=LIGHT.MAX_DISTANCE)			


		#Setup OpenGL scene data
		SCREEN = PG.display.set_mode(DISPLAY_RESOLUTION.TO_LIST(), DOUBLEBUF | OPENGL | RESIZABLE)
		VAO_SCENE, VBO_SCENE, EBO_SCENE = render.BUFFERS_INIT()
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
		gluPerspective(PREFERENCES["FOV"], float(DISPLAY_RESOLUTION.X) / float(DISPLAY_RESOLUTION.Y), CONSTANTS["MIN_VIEW_DIST"], CONSTANTS["MAX_VIEW_DIST"])  # Example parameters
		glMatrixMode(GL_MODELVIEW)
		MODEL_MATRIX = Matrix44.identity()
		glLoadIdentity()
		
		PROJECTION_MATRIX = Matrix44.perspective_projection(
			PREFERENCES["FOV"],
			(DISPLAY_RESOLUTION.X / DISPLAY_RESOLUTION.Y),
			CONSTANTS["MIN_VIEW_DIST"],
			CONSTANTS["MAX_VIEW_DIST"]
		)

		RUN = True
		PREVIOUS_FRAME, WINDOW_FOCUS = None, 0
		FPS_CAP = PREFERENCES["FPS_LIMIT"]
		while RUN:
			FPS = utils.CLAMP(CLOCK.get_fps(), 0, FPS_CAP)
			"""
			Getting Mouse/Keyboard/GamePad inputs
			Getting other general events (Like window resize or window close events)
			"""
			MOUSE_MOVE = [0, 0]
			
			for EVENT in PG.event.get():
				match EVENT.type:
					case PG.QUIT:
						RUN = False

					case PG.ACTIVEEVENT:
						if EVENT.state == 2:
							WINDOW_FOCUS = EVENT.gain

					case PG.KEYDOWN:
						if EVENT.key in KEY_STATES:
							KEY_STATES[EVENT.key] = True
						
						match EVENT.key:
							case PG.K_q:
								if PREVIOUS_FRAME != None:
									RAW_TIME = log.GET_TIME()
									CURRENT_TIME = f"{RAW_TIME[:8]}.{RAW_TIME[10:]}".replace(":", "-")
									render.SAVE_MAP(RENDER_RESOLUTION, PREVIOUS_FRAME, f"screenshots\\{CURRENT_TIME}.jpeg", "COLOUR")

							case PG.K_ESCAPE:
								RUN = False
							
							case PG.K_LCTRL:
								if not PREFERENCES["DEV_TEST"]:
									CONSTANTS["CAMERA_OFFSET"] = VECTOR_3D(0.0, 0.0, 0.0)

							case PG.K_c:
								PROJECTION_MATRIX = Matrix44.perspective_projection(
									PREFERENCES["FOV"] // 3,
									(DISPLAY_RESOLUTION.X / DISPLAY_RESOLUTION.Y),
									CONSTANTS["MIN_VIEW_DIST"],
									CONSTANTS["MAX_VIEW_DIST"]
								)

					case PG.KEYUP:
						if EVENT.key in KEY_STATES:
							KEY_STATES[EVENT.key] = False
						
						match EVENT.key:
							case PG.K_LCTRL:
								if not PREFERENCES["DEV_TEST"]:
									CONSTANTS["CAMERA_OFFSET"] = VECTOR_3D(0.0, 0.25, 0.0)

							case PG.K_c:
								PROJECTION_MATRIX = Matrix44.perspective_projection(
									PREFERENCES["FOV"],
									(DISPLAY_RESOLUTION.X / DISPLAY_RESOLUTION.Y),
									CONSTANTS["MIN_VIEW_DIST"],
									CONSTANTS["MAX_VIEW_DIST"]
								)
					
					case PG.VIDEORESIZE:
						DISPLAY_RESOLUTION = VECTOR_2D(EVENT.w, EVENT.h)
						RENDER_RESOLUTION = DISPLAY_RESOLUTION / CONSTANTS["RENDER_SCALING_FACTOR"]  #Set render resolution to be half of the screen resolution
						utils.CONSTANTS["DISPLAY_RESOLUTION"] = DISPLAY_RESOLUTION
						SCREEN = PG.display.set_mode(DISPLAY_RESOLUTION.TO_LIST(), DOUBLEBUF | OPENGL | RESIZABLE)
						SCENE_FBO, SCENE_TCB, _, _, _ = render.CREATE_FBO(RENDER_RESOLUTION)
						glViewport(0, 0, int(RENDER_RESOLUTION.X), int(RENDER_RESOLUTION.Y))
						DISPLAY_CENTRE = DISPLAY_RESOLUTION / 2


					case PG.JOYDEVICEADDED:
						NEW_PAD = [PG.joystick.Joystick(EVENT.device_index), None, None]
						JOYSTICK = utils.JOYSTICK_DEADZONE(NEW_PAD)

					case PG.JOYDEVICEREMOVED:
						JOYSTICK = None

			if JOYSTICK is not None:
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


				if PAD_CROUCH and not PREFERENCES["DEV_TEST"]:
					CONSTANTS["CAMERA_OFFSET"] = VECTOR_3D(0.0, 0.0, 0.0)

				elif not PAD_CROUCH and not PREFERENCES["DEV_TEST"]:
					CONSTANTS["CAMERA_OFFSET"] = VECTOR_3D(0.0, 0.25, 0.0)

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
					render.SAVE_MAP(RENDER_RESOLUTION, PREVIOUS_FRAME, f"screenshots\\{CURRENT_TIME}.jpeg", "COLOUR")


			else:
				if KEY_STATES[K_RETURN] and PREFERENCES["DEV_TEST"]:
					PREFERENCES["NORMALS_DEBUG"] = True
				else:
					PREFERENCES["NORMALS_DEBUG"] = False




			PLAYER = PHYS_DATA[0][PLAYER_ID]
			if (WINDOW_FOCUS == 1): #Mouse/Gamepad inputs for player view rotation.
				ZOOM_MULT = 0.3333333 if KEY_STATES[PG.K_c] else 1.0
				if JOYSTICK is not None:
					PLAYER.ROTATION.X += (JOYSTICK[2].X + PREFERENCES["AXIS_2_OFFSET"]) * PREFERENCES["PLAYER_SPEED_TURN_PAD"] * (FPS/PREFERENCES["FPS_LIMIT"]) * ZOOM_MULT
					PLAYER.ROTATION.Y -= (JOYSTICK[2].Y + PREFERENCES["AXIS_3_OFFSET"]) * PREFERENCES["PLAYER_SPEED_TURN_PAD"] * (FPS/PREFERENCES["FPS_LIMIT"]) * -ZOOM_MULT
				
				if EVENT.type == PG.MOUSEMOTION:
					MOUSE_MOVE = [EVENT.pos[0] - (DISPLAY_RESOLUTION.X // 2), EVENT.pos[1] - (DISPLAY_RESOLUTION.Y // 2)]
					PLAYER.ROTATION.X += MOUSE_MOVE[0] * PREFERENCES["PLAYER_SPEED_TURN_MOUSE"] * (FPS/PREFERENCES["FPS_LIMIT"]) * ZOOM_MULT
					PLAYER.ROTATION.Y -= MOUSE_MOVE[1] * PREFERENCES["PLAYER_SPEED_TURN_MOUSE"] * (FPS/PREFERENCES["FPS_LIMIT"]) * -ZOOM_MULT
				
				PLAYER.ROTATION = PLAYER.ROTATION.CLAMP(Y_BOUNDS=(-89.9, 89.9))
			
			if WINDOW_FOCUS == 0:
				PG.mouse.set_visible(True)
				FPS_CAP = PREFERENCES["FPS_LOW"]
			else:
				PG.mouse.set_pos(DISPLAY_CENTRE.TO_LIST())
				PG.mouse.set_visible(False)	
				FPS_CAP = PREFERENCES["FPS_LIMIT"]
			


			glLoadIdentity()



			"""
			FPS is the current frames per second - usually around the max FPS set just beforehand, and is used for a basic Δt-type force application system.
			physics.UPDATE_PHYSICS() moves all movable objects like boxes to their next, velocity-defined position, applies forces, calculates collisions, etc.
			render.SCENE() visually displays the scene, from the data provided when the scene was loaded.
			ui.HUD() simply draws any HUD-elements, such as information or text, to the screen as a flat overlay image.
			"""
			CLOCK.tick_busy_loop(FPS_CAP)

			PHYS_DATA[0][PLAYER_ID] = PLAYER
			CONSTANTS["PLAYER_COLLISION_CUBOID"] = PLAYER_COLLISION_CUBOID
			PHYS_DATA = physics.UPDATE_PHYSICS(PHYS_DATA, FPS, KEY_STATES, JOYSTICK)
			PLAYER = PHYS_DATA[0][PLAYER_ID]
			CAMERA_POSITION = PLAYER.POSITION + CONSTANTS["CAMERA_OFFSET"]

			COPIED_VAO_VERTICES, COPIED_VAO_INDICES = render.SCENE(PHYS_DATA, [ENV_VAO_VERTICES, ENV_VAO_INDICES], PLAYER)
			VBO_SCENE, EBO_SCENE = render.UPDATE_BUFFERS(COPIED_VAO_VERTICES, COPIED_VAO_INDICES, VBO_SCENE, EBO_SCENE)
			CAMERA_VIEW_MATRIX, CAMERA_LOOK_AT_VECTOR = render.CALC_VIEW_MATRIX(CAMERA_POSITION, PLAYER.ROTATION.RADIANS())



			#Pre-FBO render tasks (UI, dynamic shadows)

			if PREFERENCES["DYNAMIC_SHADOWS"]:
				#If dynamic shadows are enabled, recalculate the shadow map every frame. Not reccomended to use, but is present.
				#!CURRENTLY BROKEN!
				for LIGHT in LIGHTS:
					SHADOW_MAP, LIGHT = render.CREATE_LIGHT_MAPS(LIGHT, (NP.array(COPIED_VAO_VERTICES, dtype=NP.float32), NP.array(COPIED_VAO_INDICES, dtype=NP.uint32)), SHADOW_SHADER, CONSTANTS["SHADOW_MAP_RESOLUTION"], CURRENT_SHEET_ID)
					LIGHT.SHADOW_MAP = SHADOW_MAP
					if PREFERENCES["DEBUG_MAPS"]:
						render.SAVE_MAP(CONSTANTS["SHADOW_MAP_RESOLUTION"], SHADOW_MAP, f"screenshots\\debug_maps\\depth_map_{I}.png", "DEPTH", MIN_DISTANCE=LIGHT.MIN_DISTANCE, MAX_DISTANCE=LIGHT.MAX_DISTANCE)			

				SCREEN = PG.display.set_mode(DISPLAY_RESOLUTION.TO_LIST(), DOUBLEBUF | OPENGL | RESIZABLE)
			
			UI_TEXTURE_ID = ui.HUD(PLAYER, FPS)



			#Rendering the main scene.


			glBindFramebuffer(GL_FRAMEBUFFER, SCENE_FBO)
			glViewport(0, 0, int(RENDER_RESOLUTION.X), int(RENDER_RESOLUTION.Y))
			glClearColor(VOID_COLOUR.R, VOID_COLOUR.G, VOID_COLOUR.B, VOID_COLOUR.A)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			glClearDepth(1.0)
			glUseProgram(SCENE_SHADER)
			glActiveTexture(GL_TEXTURE0)
			glBindTexture(GL_TEXTURE_2D, CURRENT_SHEET_ID)

			MODEL_LOC = glGetUniformLocation(SCENE_SHADER, 'MODEL_MATRIX')
			VIEW_LOC = glGetUniformLocation(SCENE_SHADER, 'VIEW_MATRIX')
			PROJECTION_LOC = glGetUniformLocation(SCENE_SHADER, 'PROJ_MATRIX')
			TEXTURE_LOC = glGetUniformLocation(SCENE_SHADER, 'TRI_TEXTURE')
			VIEW_DIST_LOC = glGetUniformLocation(SCENE_SHADER, 'VIEW_MAX_DIST')
			CAMERA_POS_LOC = glGetUniformLocation(SCENE_SHADER, 'CAMERA_POSITION')
			VOID_COLOUR_LOC = glGetUniformLocation(SCENE_SHADER, 'VOID_COLOUR')
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


			glActiveTexture(GL_TEXTURE0)
			glBindVertexArray(VAO_SCENE)
			glBindTexture(GL_TEXTURE_2D, CURRENT_SHEET_ID)
			glDrawElements(GL_TRIANGLES, len(COPIED_VAO_INDICES), GL_UNSIGNED_INT, None)
			glBindTexture(GL_TEXTURE_2D, 0)
			glBindVertexArray(0)

			glBindFramebuffer(GL_FRAMEBUFFER, 0)


			glViewport(0, 0, int(DISPLAY_RESOLUTION.X), int(DISPLAY_RESOLUTION.Y))
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			
			glUseProgram(QUAD_SHADER)

			RESOLUTION_LOC = glGetUniformLocation(QUAD_SHADER, "resolution")
			SCALING_FACTOR_LOC = glGetUniformLocation(QUAD_SHADER, "pixelSize")
			SCREEN_TEXTURE_LOC = glGetUniformLocation(QUAD_SHADER, "screenTexture")
			glUniform2f(RESOLUTION_LOC, RENDER_RESOLUTION.X, RENDER_RESOLUTION.Y)
			glUniform1f(SCALING_FACTOR_LOC, SCALING_FACTOR)
			glUniform1i(SCREEN_TEXTURE_LOC, 0)



			#Draw the current frame to a quad in the camera's view
			
			PREVIOUS_FRAME = SCENE_TCB

			glBindVertexArray(VAO_QUAD)
			glActiveTexture(GL_TEXTURE0)
			glBindTexture(GL_TEXTURE_2D, SCENE_TCB)
			glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
			glBindTexture(GL_TEXTURE_2D, 0)
			glBindVertexArray(0)
			

			#Draw UI on a quad slightly closer to the camera
			
			glBindVertexArray(VAO_UI)
			glActiveTexture(GL_TEXTURE0)
			glBindTexture(GL_TEXTURE_2D, UI_TEXTURE_ID)
			glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
			glBindTexture(GL_TEXTURE_2D, 0)
			glBindVertexArray(0)
			glDeleteTextures([UI_TEXTURE_ID])
			PG.display.flip()

		# Quitting all that needs to be done, when RUN == False
		PG.mouse.set_visible(True)
		PG.joystick.quit()
		PG.quit()
		quit()

	#except Exception as E:
	#	log.ERROR("Mainloop", E)



if __name__ == "__main__":
	MAIN()

else:
	# If this isn't being run as __main__, something has gone very wrong and needs to be logged - it is not intended to ever occur.
	log.ERROR("main.py", "IsNotMain")
