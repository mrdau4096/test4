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
	import copy
	import numpy as NP

	#Stop PyGame from giving that annoying welcome message
	os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"


	sys.path.extend(("src", r"src\exct\data", r"src\exct\glsl"))
	import glm, glfw
	import pygame as PG
	from pygame import time, joystick, display, image
	from OpenGL.GL import *
	from OpenGL.GLU import *
	from OpenGL.GL.shaders import compileProgram, compileShader

	#Import other sub-files.
	from imgs import texture_load
	from exct import render, physics, utils, ui
	from scenes import scene
	from exct.utils import *
	

except Exception as E:
	log.ERROR("main.py", E)

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
		DISPLAY_CENTRE = DISPLAY_RESOLUTION / 2

		#Print user-specified values for reference.
		print("Current user configs;")
		for OPTION in PREFERENCES:
			print(f"{OPTION}: {PREFERENCES[OPTION]}")
		print("\n")



		#Generic value assignments, like the colour of the void-fog and the states of keyboard inputs.
		VOID_COLOUR = RGBA(0, 0, 0, 0).TO_DECIMAL()
		PLAYER_COLLISION_CUBOID = CONSTANTS["PLAYER_COLLISION_CUBOID"]
		CAMERA_OFFSET = CONSTANTS["CAMERA_OFFSET"]
		HEADLAMP_ENABLED = False
		FPS_CAP = PREFERENCES["FPS_LIMIT"]
		KEY_STATES = {
			1: False, 2: False, 3: False,			#Mouse buttons (LMB, MMB, RMB)
			PG.K_w: False, PG.K_s: False,			#Forward/Backwards keys
			PG.K_a: False, PG.K_d: False,			#Left/Right keys
			PG.K_e: False, PG.K_q: False,			#Interaction keys
			PG.K_SPACE: False, PG.K_LCTRL: False,	#Vertical control keys
			PG.K_LSHIFT: False, PG.K_x: False,		#Movement speed keys
			PG.K_RETURN: False,						#Debug key
			PG.K_c: False, PG.K_f: False,			#Zoom key & Headlamp key
			"CROUCH": False,						#If currently crouching (Toggle)
			"JUMP_GRACE": 0,						#Allows for a "grace period" to jump after leaving the floor
			"PAD_JUMP_PREV": False,					#To stop multiple GamePad jump inputs
		}



		#Assorted PyGame setup.
		PG.init()
		CLOCK = PG.time.Clock()


		#Create a GLFW window to initialise the OpenGL VAOs, Shaders, FBOs etc. within.
		if not glfw.init():
			raise Exception("GLFW could not be initialised.")

		glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
		OPENGL_SETUP_WINDOW = glfw.create_window(int(DISPLAY_RESOLUTION.X), int(DISPLAY_RESOLUTION.Y), "OpenGL Setup Window", None, None)
		if not OPENGL_SETUP_WINDOW:
			glfw.terminate()
			raise Exception("GLFW could not create OpenGL setup window.")
		glfw.make_context_current(OPENGL_SETUP_WINDOW)


		#PyOpenGL & VAO/VBO/EBO setup.
		
		RENDER_DATA, PHYS_DATA, SHEET_NAME, FLAG_DATA, PLAYER_ID = scene.LOAD_FILE(PREFERENCES["SCENE"])
		BLANK_TEXTURE = texture_load.LOAD_SHEET("_")
		CURRENT_SHEET_ID = texture_load.LOAD_SHEET(SHEET_NAME)
		(ENV_VAO_VERTICES, ENV_VAO_INDICES), LIGHTS = RENDER_DATA
		FLAG_STATES, LOGIC_GATES = FLAG_DATA


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
		PG.display.set_caption("test4.2.5//main.py")
		PG.display.set_icon(PG.image.load("src\\imgs\\main.ico"))
		SCREEN = PG.display.set_mode(DISPLAY_RESOLUTION.TO_LIST(), PG.DOUBLEBUF | PG.OPENGL | PG.RESIZABLE)
		
		(SCENE_SHADER, QUAD_SHADER), (VAO_QUAD, VAO_UI, FBO_SCENE, TCB_SCENE), CURRENT_SHEET_ID, (VAO_SCENE, VBO_SCENE, EBO_SCENE), (MODEL_MATRIX, PROJECTION_MATRIX) = render.SET_PYGAME_CONTEXT(SHEET_NAME)

		for I, LIGHT in enumerate(LIGHTS):
			LIGHT.SHADOW_MAP = render.CREATE_TEXTURE_FROM_DATA(LIGHT.SHADOW_MAP_DATA, FILTER=GL_NEAREST)

	#except Exception as E:
		#log.ERROR("Main.py Value initialisation", E)

	#try:
		OPTIONS_DATA = (SCREEN, ui.OPTIONS_MENU, KEY_STATES, (VAO_QUAD, VAO_UI), QUAD_SHADER)
		RUN, SCREEN, WINDOW_FOCUS = ui.PROCESS_UI_STATE(SCREEN, ui.MAIN_MENU, KEY_STATES, (VAO_QUAD, VAO_UI), QUAD_SHADER, BACKGROUND=texture_load.LOAD_SHEET("menu_background", SHEET=False), BACKGROUND_SHADE=False, UI_DATA=OPTIONS_DATA)
		DISPLAY_RESOLUTION = utils.CONSTANTS["DISPLAY_RESOLUTION"]
		FBO_SCENE, TCB_SCENE, _, _, _ = render.CREATE_FBO(DISPLAY_RESOLUTION)
		DISPLAY_CENTRE = DISPLAY_RESOLUTION/2


		PREVIOUS_FRAME = None
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
						PG.mouse.set_visible(True)
						PG.quit()
						sys.exit()

					case PG.ACTIVEEVENT:
						if EVENT.state == 2:
							WINDOW_FOCUS = EVENT.gain

					case PG.MOUSEBUTTONDOWN:
						if EVENT.button in KEY_STATES:
							KEY_STATES[EVENT.button] = True

						match EVENT.button:
							case 1:
								#LMB Pressed
								current_frame = 0

					case PG.MOUSEBUTTONUP:
						if EVENT.button in KEY_STATES:
							KEY_STATES[EVENT.button] = False

					case PG.KEYDOWN:
						if EVENT.key in KEY_STATES:
							KEY_STATES[EVENT.key] = True
						
						match EVENT.key:
							case PG.K_q:
								#Q is the screenshot key.
								if PREVIOUS_FRAME != None:
									RAW_TIME = log.GET_TIME()
									CURRENT_TIME = f"{RAW_TIME[:8]}.{RAW_TIME[10:]}".replace(":", "-")
									render.SAVE_MAP(RENDER_RESOLUTION, PREVIOUS_FRAME, f"screenshots\\{CURRENT_TIME}.png", "COLOUR")
									print(f"Saved screenshot as [{CURRENT_TIME}.png]")

							case PG.K_BACKSPACE:
								PG.mouse.set_visible(True)
								PG.quit()
								sys.exit()

							case PG.K_ESCAPE:
								RUN, SCREEN, WINDOW_FOCUS = ui.PROCESS_UI_STATE(SCREEN, ui.PAUSE_MENU, KEY_STATES, (VAO_QUAD, VAO_UI), QUAD_SHADER, BACKGROUND=PREVIOUS_FRAME, UI_DATA=OPTIONS_DATA)
								PG.mouse.set_visible(False)
							
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

							case PG.K_e:
								#Interacting with buttons/similar
								RAYCAST = RAY(CAMERA_POSITION, "INTERACT_RAY", RENDER_START_POINT=PLAYER.POSITION, ANGLE=VECTOR_2D(maths.radians(PLAYER.ROTATION.X), maths.radians(PLAYER.ROTATION.Y)), MAX_DISTANCE=1.25)

								if PREFERENCES["DEBUG_RAYS"]:
									scene.CURRENT_ID += 1
									PHYS_DATA[1][1][scene.CURRENT_ID] = RAYCAST

								COLLIDED_OBJECT = RAYCAST.CHECK_FOR_INTERSECTS(physics.BOUNDING_BOX_COLLISION, physics.RAY_TRI_INTERSECTION, PHYS_DATA)
								if type(COLLIDED_OBJECT) == INTERACTABLE:
									FLAG_STATES[COLLIDED_OBJECT.FLAG] = not FLAG_STATES[COLLIDED_OBJECT.FLAG]

							case PG.K_f:
								HEADLAMP_ENABLED = not HEADLAMP_ENABLED
								


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
						utils.CONSTANTS["DISPLAY_RESOLUTION"] = DISPLAY_RESOLUTION
						SCREEN = PG.display.set_mode(DISPLAY_RESOLUTION.TO_LIST(), PG.DOUBLEBUF | PG.OPENGL | PG.RESIZABLE)
						FBO_SCENE, TCB_SCENE, _, _, _ = render.CREATE_FBO(DISPLAY_RESOLUTION)
						glViewport(0, 0, int(DISPLAY_RESOLUTION.X), int(DISPLAY_RESOLUTION.Y))
						DISPLAY_CENTRE = DISPLAY_RESOLUTION / 2


				if (WINDOW_FOCUS == 1):
					#Mouse inputs for player view rotation only apply when window is focussed.
					if EVENT.type == PG.MOUSEMOTION:
						MOUSE_MOVE = (EVENT.pos[0] - (DISPLAY_RESOLUTION.X // 2), EVENT.pos[1] - (DISPLAY_RESOLUTION.Y // 2))
						PLAYER.ROTATION.X += MOUSE_MOVE[0] * PREFERENCES["PLAYER_SPEED_TURN_MOUSE"] * (FPS/PREFERENCES["FPS_LIMIT"]) * ZOOM_MULT
						PLAYER.ROTATION.Y -= MOUSE_MOVE[1] * PREFERENCES["PLAYER_SPEED_TURN_MOUSE"] * (FPS/PREFERENCES["FPS_LIMIT"]) * -ZOOM_MULT
					
					#Limit the camera"s vertical movement to ~±90*
					PLAYER.ROTATION = PLAYER.ROTATION.CLAMP(Y_BOUNDS=(-89.9, 89.9))



			if KEY_STATES[1] and PREFERENCES["DEV_TEST"]:
				current_frame += 1
				if current_frame > (0):
					current_frame=0
					RAYCAST = RAY(CAMERA_POSITION, "BULLET_RAY", RENDER_START_POINT=PLAYER.POSITION, ANGLE=VECTOR_2D(maths.radians(PLAYER.ROTATION.X), maths.radians(PLAYER.ROTATION.Y)))

					scene.CURRENT_ID += 1
					PHYS_DATA[1][1][scene.CURRENT_ID] = RAYCAST

					COLLIDED_OBJECT = RAYCAST.CHECK_FOR_INTERSECTS(physics.BOUNDING_BOX_COLLISION, physics.RAY_TRI_INTERSECTION, PHYS_DATA)


			
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


			PREVIOUS_FLAG_STATES = copy.copy(FLAG_STATES)
			for LOGIC_GATE in LOGIC_GATES:
				#Update the flags with any new logic changes.
				FLAG_STATES = LOGIC_GATE.UPDATE(PREVIOUS_FLAG_STATES)


			#Set player data, Calculate physics, Get player data.
			PHYS_DATA[0][PLAYER_ID] = PLAYER
			PHYS_DATA, FLAG_STATES = physics.UPDATE_PHYSICS(PHYS_DATA, FPS, KEY_STATES, FLAG_STATES)
			PLAYER = PHYS_DATA[0][PLAYER_ID]
			CAMERA_POSITION = PLAYER.POSITION + CAMERA_OFFSET


			#Give the VAO/VBO/EBO the data for any "dynamic" objects such as a sprite"s coordinates.
			#Applied over the top of other, environmental/static objects like Tris.
			(COPIED_VAO_VERTICES, COPIED_VAO_INDICES), PHYS_DATA = render.SCENE(PHYS_DATA, [ENV_VAO_VERTICES, ENV_VAO_INDICES], PLAYER)
			VBO_SCENE, EBO_SCENE = render.UPDATE_BUFFERS(COPIED_VAO_VERTICES, COPIED_VAO_INDICES, VBO_SCENE, EBO_SCENE)
			CAMERA_VIEW_MATRIX, CAMERA_LOOK_AT = render.CALC_VIEW_MATRIX(CAMERA_POSITION, PLAYER.ROTATION.RADIANS())

			
			#Render the current UI with the player"s data (Health, etc.)
			UI_TEXTURE_ID = ui.HUD(PLAYER, FPS)
			if PREFERENCES["DEBUG_UI"]:
				#Save map if DEBUG_UI is enabled.
				render.SAVE_MAP(CONSTANTS["UI_RESOLUTION"], UI_TEXTURE_ID, f"screenshots\\debug_maps\\colour_map_ui.png", "COLOUR")


			#Rendering the main scene.

			glLoadIdentity()

			#Bind FBO, set relevant OpenGL configs such as the void fog colour or the current texture.
			glBindFramebuffer(GL_FRAMEBUFFER, FBO_SCENE)
			glUseProgram(SCENE_SHADER)
			glClearColor(VOID_COLOUR.R, VOID_COLOUR.G, VOID_COLOUR.B, VOID_COLOUR.A)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			glClearDepth(1.0)
			glActiveTexture(GL_TEXTURE0)
			glBindTexture(GL_TEXTURE_2D, CURRENT_SHEET_ID)


			#Get locations for and provide data for the scene shader"s uniforms (such as CAMERA_POSITION).
			MODEL_LOC = glGetUniformLocation(SCENE_SHADER, "MODEL_MATRIX")
			VIEW_LOC = glGetUniformLocation(SCENE_SHADER, "VIEW_MATRIX")
			PROJECTION_LOC = glGetUniformLocation(SCENE_SHADER, "PROJECTION_MATRIX")
			TEXTURE_LOC = glGetUniformLocation(SCENE_SHADER, "TRI_TEXTURE")
			VIEW_DIST_LOC = glGetUniformLocation(SCENE_SHADER, "VIEW_MAX_DIST")
			CAMERA_POS_LOC = glGetUniformLocation(SCENE_SHADER, "CAMERA_POSITION")
			CAMERA_LA_LOC = glGetUniformLocation(SCENE_SHADER, "CAMERA_LOOK_AT")
			VOID_COLOUR_LOC = glGetUniformLocation(SCENE_SHADER, "VOID_COLOUR")
			LIGHT_COUNT_LOC = glGetUniformLocation(SCENE_SHADER, "LIGHT_COUNT")
			HEADLAMP_ENABLED_LOC = glGetUniformLocation(SCENE_SHADER, "HEADLAMP_ENABLED")
			NORMAL_DEBUG_LOC = glGetUniformLocation(SCENE_SHADER, "NORMAL_DEBUG")
			WIREFRAME_DEBUG_LOC = glGetUniformLocation(SCENE_SHADER, "WIREFRAME_DEBUG")

			glUniformMatrix4fv(MODEL_LOC, 1, GL_FALSE, MODEL_MATRIX)
			glUniformMatrix4fv(VIEW_LOC, 1, GL_FALSE, CAMERA_VIEW_MATRIX)
			glUniformMatrix4fv(PROJECTION_LOC, 1, GL_FALSE, PROJECTION_MATRIX)
			glUniform4fv(VOID_COLOUR_LOC, 1, GL_FALSE, glm.value_ptr(VOID_COLOUR.CONVERT_TO_GLM_VEC4()))
			glUniform1i(LIGHT_COUNT_LOC, len(LIGHTS))
			glUniform1f(VIEW_DIST_LOC, CONSTANTS["MAX_VIEW_DIST"])
			glUniform3fv(CAMERA_POS_LOC, 1, glm.value_ptr(CAMERA_POSITION.CONVERT_TO_GLM_VEC3()))
			glUniform3fv(CAMERA_LA_LOC, 1, CAMERA_LOOK_AT)
			glUniform1i(HEADLAMP_ENABLED_LOC, HEADLAMP_ENABLED)
			glUniform1i(NORMAL_DEBUG_LOC, PREFERENCES["DEBUG_NORMALS"])
			glUniform1i(WIREFRAME_DEBUG_LOC, PREFERENCES["DEBUG_WIREFRAME"])
			glUniform1i(TEXTURE_LOC, 0)


			for I, LIGHT in enumerate(LIGHTS):
				#Iterate through every light, to hand their data to the GLSL struct equivalent to the python class of the same name.
				LIGHT_POSITION_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].POSITION")
				LIGHT_LOOK_AT_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].LOOK_AT")
				LIGHT_COLOUR_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].COLOUR")
				LIGHT_INTENSITY_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].INTENSITY")
				LIGHT_FOV_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].FOV")
				LIGHT_MAX_DIST_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].MAX_DIST")
				LIGHT_SPACE_MATRIX_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].LIGHT_SPACE_MATRIX")
				SHADOW_MAP_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].SHADOW_MAP")
				ENABLED_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].ENABLED")

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
				glUniform1i(ENABLED_LOC, FLAG_STATES[LIGHT.FLAG])



			#Finally, instruct OpenGL to render the triangles of the scene with their assigned data, texture, etc.
			if PREFERENCES["DEBUG_WIREFRAME"]: glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
			glActiveTexture(GL_TEXTURE0)
			glBindVertexArray(VAO_SCENE)
			glBindTexture(GL_TEXTURE_2D, CURRENT_SHEET_ID)
			glDrawElements(GL_TRIANGLES, len(COPIED_VAO_INDICES), GL_UNSIGNED_INT, None)
			glBindTexture(GL_TEXTURE_2D, 0)
			glBindVertexArray(0)

			glBindFramebuffer(GL_FRAMEBUFFER, 0)
			if PREFERENCES["DEBUG_WIREFRAME"]: glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)


			#Reset values to align with the display size.
			#glViewport(0, 0, int(DISPLAY_RESOLUTION.X), int(DISPLAY_RESOLUTION.Y))
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			
			glUseProgram(QUAD_SHADER)

			SCREEN_TEXTURE_LOC = glGetUniformLocation(QUAD_SHADER, "SCREEN_TCB")
			glUniform1i(SCREEN_TEXTURE_LOC, 0)



			#Save the current frame, for a screenshot the next frame.
			PREVIOUS_FRAME = TCB_SCENE

			#Draw the current frame to a quad in the camera"s view to apply any effects to it.
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
		glDeleteTextures([CURRENT_SHEET_ID])
		if PREVIOUS_FRAME:
			glDeleteTextures([PREVIOUS_FRAME])

		PG.mouse.set_visible(True)
		PG.joystick.quit()
		PG.quit()
		sys.exit()

	#except Exception as E:
		#log.ERROR("Mainloop", E)



if __name__ == "__main__":
	MAIN()

else:
	#If this isn"t being run as __main__, something has gone very wrong and needs to be logged - it is not intended to ever occur.
	log.ERROR("main.py", "IsNotMain")
