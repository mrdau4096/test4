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
	import random

	#Stops PyGame from giving the welcome message.
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
	from exct import render, physics, utils, ui, pathfinding
	from scenes import scene
	from exct.utils import *
	
except Exception as E:
	log.ERROR("main.py", E)

#Formatting for the terminal output.
print("--\n")


from OpenGL.GL import *
import numpy as np
from PIL import Image



try:
	#Import the memory-profiler I used in testing.
	from memory_profiler import profile

except ImportError:
	#If it fails, then this is not an issue
	#It is only used for the sake of testing anyhow, and is non-essential in actual program.
	pass



def MAIN():
	try:
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
		PLAYER_PREV_FRAME = None
		FPS_CAP = PREFERENCES["FPS_LIMIT"]
		SECONDS_SINCE_LAST_FIRE = 5
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
		
		RENDER_DATA, PHYS_DATA, FLAG_DATA, PLAYER_ID, SHEETS_USED, CURRENT_ID = scene.LOAD_FILE(PREFERENCES["SCENE"])
		scene.CURRENT_ID = CURRENT_ID
		SHEET_ARRAY = texture_load.CREATE_SHEET_ARRAY(scene.SHEETS_USED, FROM_FILE=True)
		(ENV_VAO_VERTICES, ENV_VAO_INDICES), LIGHTS = RENDER_DATA
		FLAG_STATES, LOGIC_GATES = FLAG_DATA


		#Mid-loading Shadow-Mapping
		SHADOWMAP_RESOLUTION = CONSTANTS["SHADOW_MAP_RESOLUTION"]
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
			SURFACE = glfw.create_window(int(SHADOWMAP_RESOLUTION.X), int(SHADOWMAP_RESOLUTION.Y), f"Shadowmap; {I} of {len(LIGHTS)}", None, None)
			if not SURFACE:
				glfw.terminate()
				raise Exception("GLFW could not create window.")
			glfw.make_context_current(SURFACE)

			LIGHTS[I] = render.CREATE_SHADOW_MAPS(SURFACE, I, LIGHT, (NP.array(ENV_VAO_VERTICES, dtype=NP.float32), NP.array(ENV_VAO_INDICES, dtype=NP.uint32)), SHEETS_USED)
			glfw.terminate()

		SHADOW_MAP_DATA_ARRAY = NP.array([LIGHT.SHADOW_MAP_DATA for LIGHT in LIGHTS], dtype=NP.float32)

		#Set the context back as the main PG window, and convert any shadow map data.
		PG.display.set_caption("test4.2.7//main.py")
		PG.display.set_icon(PG.image.load("src\\imgs\\main.ico"))
		SCREEN = PG.display.set_mode(list(DISPLAY_RESOLUTION), PG.DOUBLEBUF | PG.OPENGL | PG.RESIZABLE)

		(
			(SCENE_SHADER, QUAD_SHADER),
			(VAO_QUAD, VAO_UI, FBO_SCENE, TCB_SCENE),
			(VAO_SCENE, VBO_SCENE, EBO_SCENE),
			(MODEL_MATRIX, PROJECTION_MATRIX)
		) = render.SET_PYGAME_CONTEXT()

		HOSTILES, SUPPLIES, PROJECTILES, ITEMS, (SHEETS_USED, SHEET_LIST) = GET_GAME_DATA(SHEETS_USED, PROCESS_SHEETS_USED=False)
		SHEETS_USED.extend(SHEET_LIST)
		SHEETS_USED = utils.REMOVE_INDEXED_DUPLICATES(SHEETS_USED)
		SHEET_ARRAY = texture_load.CREATE_SHEET_ARRAY(SHEETS_USED, FROM_FILE=True)


		SHADOW_ARRAY = texture_load.CREATE_SHEET_ARRAY(SHADOW_MAP_DATA_ARRAY, DIMENTIONS=SHADOWMAP_RESOLUTION, GL_TYPE=GL_RGB, DATA_TYPE=GL_FLOAT)

		ui.VIGNETTE_COLOUR = RGBA(0, 0, 0, 0)
		ui.COLOURED_VIGNETTE = ui.UPDATE_VIGNETTE(RGBA(0, 0, 0, 0), FPS_CAP, FADEOUT=float("inf"))
		PLAYER = PHYS_DATA[0][PLAYER_ID]
		
	except Exception as E:
		log.ERROR("Main.py Value initialisation", E)

	try:
		OPTIONS_DATA = (
			SCREEN,
			ui.OPTIONS_MENU,
			KEY_STATES,
			(VAO_QUAD, VAO_UI),
			QUAD_SHADER
		)
		

		RUN, SCREEN, WINDOW_FOCUS = ui.PROCESS_UI_STATE(
			SCREEN,
			ui.MAIN_MENU,
			KEY_STATES,
			(VAO_QUAD, VAO_UI),
			QUAD_SHADER,
			BACKGROUND=texture_load.LOAD_IMG("ui-menu_background", OPENGL=True),
			BACKGROUND_SHADE=False,
			UI_DATA=OPTIONS_DATA
		)

		DISPLAY_RESOLUTION = utils.CONSTANTS["DISPLAY_RESOLUTION"]
		FBO_SCENE, TCB_SCENE, _, _, _ = render.CREATE_FBO(DISPLAY_RESOLUTION)
		DISPLAY_CENTRE = DISPLAY_RESOLUTION/2


		#Main game loop.
		while RUN:
			MOUSE_MOVE = [0, 0]
			FPS = utils.CLAMP(CLOCK.get_fps(), 1, FPS_CAP)
			PLAYER_PREV_FRAME = copy.copy(PLAYER)
			if SECONDS_SINCE_LAST_FIRE < 5:
				#Only count for 5s of no item use to prevent infinite increase.
				SECONDS_SINCE_LAST_FIRE += 1/FPS
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
								if PLAYER.HELD_ITEM is not None:
									ITEM = PLAYER.ITEMS[PLAYER.HELD_ITEM]

									if SECONDS_SINCE_LAST_FIRE >= ITEM[8] and PLAYER.ENERGY >= ITEM[4]:
										SECONDS_SINCE_LAST_FIRE = 0

										if ITEM[5]: #If raycast...
											if ITEM[7] > 0: #For raycasts, this means multiple rays with spread or if 0.0, 1 ray.
												SPREAD_MAX = CONSTANTS["MAX_RAY_SPREAD"]
												for _ in range(int(round(ITEM[7]))-1):
													SPREAD = VECTOR_2D(random.randint(-SPREAD_MAX, SPREAD_MAX), random.randint(-SPREAD_MAX, SPREAD_MAX))
													ANGLE = (VECTOR_2D(PLAYER.ROTATION.X, PLAYER.ROTATION.Y) + SPREAD).RADIANS()
													RAYCAST = RAY(
														CAMERA_POSITION,
														"BULLET_RAY",
														RENDER_START_POINT=PLAYER.POSITION + (0.5 * CAMERA_OFFSET),
														ANGLE=ANGLE,
														MAX_DISTANCE=64.0,
														OWNER=PLAYER.ID,
													)
													scene.CURRENT_ID += 1
													PHYS_DATA[1][1][scene.CURRENT_ID] = RAYCAST

													COLLIDED_OBJECT = RAYCAST.CHECK_FOR_INTERSECTS(
														physics.BOUNDING_BOX_COLLISION,
														physics.RAY_TRI_INTERSECTION,
														PHYS_DATA
													)

													if type(COLLIDED_OBJECT) in (PLAYER, ENEMY,):
														PHYS_DATA = COLLIDED_OBJECT.HURT(ITEM[5], PHYS_DATA, scene.CURRENT_ID)


											#Always do 1 perfectly aimed ray.
											RAYCAST = RAY(
												CAMERA_POSITION,
												"BULLET_RAY",
												RENDER_START_POINT=PLAYER.POSITION + (0.5 * CAMERA_OFFSET),
												ANGLE=VECTOR_2D(maths.radians(PLAYER.ROTATION.X), maths.radians(PLAYER.ROTATION.Y)),
												MAX_DISTANCE=64.0,
												OWNER=PLAYER.ID,
											)
											scene.CURRENT_ID += 1
											PHYS_DATA[1][1][scene.CURRENT_ID] = RAYCAST

											COLLIDED_OBJECT = RAYCAST.CHECK_FOR_INTERSECTS(
												physics.BOUNDING_BOX_COLLISION,
												physics.RAY_TRI_INTERSECTION,
												PHYS_DATA
											)

											if type(COLLIDED_OBJECT) in (PLAYER, ENEMY,):
												PHYS_DATA = COLLIDED_OBJECT.HURT(ITEM[5], PHYS_DATA, scene.CURRENT_ID)

										
										else:
											DIRECTION_VECTOR = VECTOR_3D(
												 maths.cos(maths.radians(-PLAYER.ROTATION.Y)) * maths.sin(maths.radians(PLAYER.ROTATION.X) - utils.piDIV2),
												 maths.sin(maths.radians(-PLAYER.ROTATION.Y)),
												-maths.cos(maths.radians(-PLAYER.ROTATION.Y)) * maths.cos(maths.radians(PLAYER.ROTATION.X) - utils.piDIV2)
											)

											PROJ_DATA = PROJECTILES[ITEM[6]]
											PROJ_TEXTURE_SHEETS_USED, PROJ_TEXTURE = PROJ_DATA[2][0]
											PROJ_TEXTURE = texture_load.UV_CACHE_MANAGER(PROJ_TEXTURE)
											scene.CURRENT_ID += 1

											#Would use "PROJECTILE" as the variable name, but the class already uses that.
											PROJ = PROJECTILE(
												scene.CURRENT_ID,
												CAMERA_POSITION + (DIRECTION_VECTOR * 0.25),#0.25u offset infront of the camera.
												DIRECTION_VECTOR * ITEM[7],					#Firing velocity is stored within the item's data.
												ITEM[6],									#Projectile Type.
												PROJ_TEXTURE,								#Texture used by the projectile.
												PROJ_TEXTURE_SHEETS_USED,					#The sheet the texture was on.
												PLAYER.ID,									#"Owner" is player.
											)

											#Add to PHYS_DATA\KINETICs
											PHYS_DATA[0][scene.CURRENT_ID] = PROJ

										#Remove ENERGY from PLAYER, if INF_ENERGY is not True.
										PLAYER.ENERGY -= 0 if PREFERENCES["INF_ENERGY"] else ITEM[4]



					case PG.MOUSEWHEEL:
						SECONDS_SINCE_LAST_FIRE = 5
						ITEM_LIST = list(PLAYER.ITEMS.keys())
						CURRENT_ITEM_INDEX = ITEM_LIST.index(PLAYER.HELD_ITEM)
						if EVENT.y > 0:
							CURRENT_ITEM_INDEX += 1
						elif EVENT.y < 0:
							CURRENT_ITEM_INDEX -= 1

						if CURRENT_ITEM_INDEX < 0:
							CURRENT_ITEM_INDEX = len(ITEM_LIST)-1
						CURRENT_ITEM_INDEX %= len(ITEM_LIST)

						PLAYER.HELD_ITEM = ITEM_LIST[CURRENT_ITEM_INDEX]


					case PG.MOUSEBUTTONUP:
						if EVENT.button in KEY_STATES:
							KEY_STATES[EVENT.button] = False


					case PG.KEYDOWN:
						if EVENT.key in KEY_STATES:
							KEY_STATES[EVENT.key] = True
						
						match EVENT.key:
							case PG.K_BACKSPACE:
								if PREFERENCES["DEV_TEST"]:
									#Only allow if DEV_TEST to stop accidental usage.
									PG.mouse.set_visible(True)
									PG.quit()
									sys.exit()


							case PG.K_ESCAPE:
								RUN, SCREEN, WINDOW_FOCUS = ui.PROCESS_UI_STATE(
									SCREEN,
									ui.PAUSE_MENU, KEY_STATES,
									(VAO_QUAD, VAO_UI),
									QUAD_SHADER,
									BACKGROUND=PREVIOUS_FRAME,
									UI_DATA=OPTIONS_DATA
								)
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
								RAYCAST = RAY(
									CAMERA_POSITION,
									"INTERACT_RAY",
									RENDER_START_POINT=PLAYER.POSITION,
									ANGLE=VECTOR_2D(maths.radians(PLAYER.ROTATION.X), maths.radians(PLAYER.ROTATION.Y)),
									MAX_DISTANCE=1.25
								)

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


							case PG.K_F2:
								PREFERENCES["HIDE_HUD"] = not PREFERENCES["HIDE_HUD"]

					
					case PG.VIDEORESIZE:
						#Display size changes handled
						DISPLAY_RESOLUTION = VECTOR_2D(EVENT.w, EVENT.h)
						utils.CONSTANTS["DISPLAY_RESOLUTION"] = DISPLAY_RESOLUTION
						SCREEN = PG.display.set_mode(list(DISPLAY_RESOLUTION), PG.DOUBLEBUF | PG.OPENGL | PG.RESIZABLE)
						FBO_SCENE, TCB_SCENE, _, _, _ = render.CREATE_FBO(DISPLAY_RESOLUTION)
						glViewport(0, 0, int(DISPLAY_RESOLUTION.X), int(DISPLAY_RESOLUTION.Y))
						DISPLAY_CENTRE = DISPLAY_RESOLUTION / 2


				if (WINDOW_FOCUS == 1) and (PLAYER.ALIVE):
					#Mouse inputs for player view rotation only apply when window is focussed.
					ZOOM_MULT = 0.3333333 if KEY_STATES[PG.K_c] else 1.0 #Zoom changes sensitivity
					if EVENT.type == PG.MOUSEMOTION:
						MOUSE_MOVE = (EVENT.pos[0] - (DISPLAY_RESOLUTION.X // 2), EVENT.pos[1] - (DISPLAY_RESOLUTION.Y // 2))
						PLAYER.ROTATION.X += MOUSE_MOVE[0] * PREFERENCES["PLAYER_SPEED_TURN_MOUSE"] * (FPS/PREFERENCES["FPS_LIMIT"]) * ZOOM_MULT
						PLAYER.ROTATION.Y -= MOUSE_MOVE[1] * PREFERENCES["PLAYER_SPEED_TURN_MOUSE"] * (FPS/PREFERENCES["FPS_LIMIT"]) * -ZOOM_MULT
					
					#Limit the camera"s vertical movement to ~±90*
					PLAYER.ROTATION = PLAYER.ROTATION.CLAMP(Y_BOUNDS=(-89.9, 89.9))



			
			if WINDOW_FOCUS == 0:
				#If window is not in focus, set the FPS to the "idle", lower value and show the mouse.
				PG.mouse.set_visible(True)
				FPS_CAP = CONSTANTS["FPS_LOW"] if PREFERENCES["FPS_DEFOCUS"] else PREFERENCES["FPS_LIMIT"]
			else:
				#Otherwise move mouse to centre of screen (hidden) and use the "active", higher FPS.
				PG.mouse.set_pos(list(DISPLAY_CENTRE))
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
			(COPIED_VAO_VERTICES, COPIED_VAO_INDICES), PHYS_DATA, scene.CURRENT_ID = render.SCENE(
				PHYS_DATA,
				[ENV_VAO_VERTICES, ENV_VAO_INDICES],
				PLAYER,
				SHEETS_USED,
				scene.CURRENT_ID,
				FPS,
			)
			VBO_SCENE, EBO_SCENE = render.UPDATE_BUFFERS(
				COPIED_VAO_VERTICES,
				COPIED_VAO_INDICES,
				VBO_SCENE,
				EBO_SCENE
			)
			CAMERA_VIEW_MATRIX, CAMERA_LOOK_AT = render.CALC_VIEW_MATRIX(CAMERA_POSITION, PLAYER.ROTATION.RADIANS())

			
			#Render the current UI with the player"s data (Health, etc.)

			if PLAYER_PREV_FRAME is not None:
				#print(PLAYER.HEALTH, PLAYER_PREV_FRAME.HEALTH)
				if PLAYER.HEALTH > PLAYER_PREV_FRAME.HEALTH:
					ui.COLOURED_VIGNETTE = ui.UPDATE_VIGNETTE(CONSTANTS["HEAL_COLOUR"], FPS, FADEOUT=1.0)
				elif PLAYER.HEALTH < PLAYER_PREV_FRAME.HEALTH:
					ui.COLOURED_VIGNETTE = ui.UPDATE_VIGNETTE(CONSTANTS["HURT_COLOUR"], FPS, FADEOUT=1.0)
				elif PLAYER.ENERGY > PLAYER_PREV_FRAME.ENERGY:
					ui.COLOURED_VIGNETTE = ui.UPDATE_VIGNETTE(CONSTANTS["RECHARGE_COLOUR"], FPS, FADEOUT=1.0)


			UI_TEXTURE_ID = ui.HUD(PLAYER, FPS)
			if PREFERENCES["DEBUG_UI"]:
				#Save map if DEBUG_UI is enabled.
				render.SAVE_MAP(CONSTANTS["UI_RESOLUTION"], UI_TEXTURE_ID, f"src\\debug_maps\\colour_map_ui.png", "COLOUR")


			#Rendering the main scene.

			glLoadIdentity()

			#Bind FBO, set relevant OpenGL configs such as the void fog colour or the current texture.
			glBindFramebuffer(GL_FRAMEBUFFER, FBO_SCENE)
			glUseProgram(SCENE_SHADER)
			glClearColor(VOID_COLOUR.R, VOID_COLOUR.G, VOID_COLOUR.B, VOID_COLOUR.A)
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			glClearDepth(1.0)


			#Get locations for and provide data for the scene shader"s uniforms (such as CAMERA_POSITION).
			MODEL_LOC = glGetUniformLocation(SCENE_SHADER, "MODEL_MATRIX")
			VIEW_LOC = glGetUniformLocation(SCENE_SHADER, "VIEW_MATRIX")
			PROJECTION_LOC = glGetUniformLocation(SCENE_SHADER, "PROJECTION_MATRIX")
			VIEW_DIST_LOC = glGetUniformLocation(SCENE_SHADER, "VIEW_MAX_DIST")
			CAMERA_POS_LOC = glGetUniformLocation(SCENE_SHADER, "CAMERA_POSITION")
			CAMERA_LA_LOC = glGetUniformLocation(SCENE_SHADER, "CAMERA_LOOK_AT")
			VOID_COLOUR_LOC = glGetUniformLocation(SCENE_SHADER, "VOID_COLOUR")
			LIGHT_COUNT_LOC = glGetUniformLocation(SCENE_SHADER, "LIGHT_COUNT")
			HEADLAMP_ENABLED_LOC = glGetUniformLocation(SCENE_SHADER, "HEADLAMP_ENABLED")
			NORMAL_DEBUG_LOC = glGetUniformLocation(SCENE_SHADER, "NORMAL_DEBUG")
			WIREFRAME_DEBUG_LOC = glGetUniformLocation(SCENE_SHADER, "WIREFRAME_DEBUG")
			RAY_PERSIST_FRAMES_LOC = glGetUniformLocation(SCENE_SHADER, "MAX_RAY_PERSIST_SECONDS")
			SHEETS_ARRAY_LOC = glGetUniformLocation(SCENE_SHADER, "SHEETS")
			SHADOWS_ARRAY_LOC = glGetUniformLocation(SCENE_SHADER, "SHADOW_MAPS")

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
			glUniform1f(RAY_PERSIST_FRAMES_LOC, CONSTANTS["MAX_RAY_PERSIST_SECONDS"])
			glUniform1i(SHEETS_ARRAY_LOC, 0)
			glUniform1i(SHADOWS_ARRAY_LOC, 1)


			for I, LIGHT in enumerate(LIGHTS):
				#Iterate through every light, to hand their data to the GLSL struct equivalent to the python class of the same name.
				LIGHT_POSITION_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].POSITION")
				LIGHT_LOOK_AT_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].LOOK_AT")
				LIGHT_COLOUR_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].COLOUR")
				LIGHT_INTENSITY_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].INTENSITY")
				LIGHT_FOV_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].FOV")
				LIGHT_MAX_DIST_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].MAX_DIST")
				LIGHT_SPACE_MATRIX_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].LIGHT_SPACE_MATRIX")
				ENABLED_LOC = glGetUniformLocation(SCENE_SHADER, f"LIGHTS[{I}].ENABLED")

				glUniform3fv(LIGHT_POSITION_LOC, 1, glm.value_ptr(LIGHT.POSITION.CONVERT_TO_GLM_VEC3()))
				glUniform3fv(LIGHT_LOOK_AT_LOC, 1, glm.value_ptr(LIGHT.LOOK_AT.CONVERT_TO_GLM_VEC3()))
				glUniform3fv(LIGHT_COLOUR_LOC, 1, glm.value_ptr(LIGHT.COLOUR.CONVERT_TO_GLM_VEC4()))
				glUniform1f(LIGHT_INTENSITY_LOC, LIGHT.INTENSITY)
				glUniform1f(LIGHT_FOV_LOC, LIGHT.FOV)
				glUniform1f(LIGHT_MAX_DIST_LOC, LIGHT.MAX_DISTANCE)
				glUniformMatrix4fv(LIGHT_SPACE_MATRIX_LOC, 1, GL_FALSE, glm.value_ptr(LIGHT.SPACE_MATRIX))
				glUniform1i(ENABLED_LOC, FLAG_STATES[LIGHT.FLAG])



			#Finally, instruct OpenGL to render the triangles of the scene with their assigned data, texture, etc.
			if PREFERENCES["DEBUG_WIREFRAME"]: glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
			glBindVertexArray(VAO_SCENE)
			glBindTextureUnit(0, SHEET_ARRAY)
			glBindTextureUnit(1, SHADOW_ARRAY)
			glBindVertexArray(VAO_SCENE)
			
			glDrawElements(GL_TRIANGLES, len(COPIED_VAO_INDICES), GL_UNSIGNED_INT, None)
			glBindVertexArray(0)

			glBindFramebuffer(GL_FRAMEBUFFER, 0)
			if PREFERENCES["DEBUG_WIREFRAME"]: glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)


			#Reset values to align with the display size.
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			PREVIOUS_FRAME = TCB_SCENE
			
			glUseProgram(QUAD_SHADER)

			TEXTURE_LOC = glGetUniformLocation(QUAD_SHADER, "TEXTURE")
			glUniform1i(TEXTURE_LOC, 0)


			#Draw the current frame to a quad in the camera's view to apply any effects to it.
			glBindVertexArray(VAO_QUAD)
			glBindTextureUnit(0, TCB_SCENE)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
			glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
			glBindVertexArray(0)
			

			#Draw UI on a quad slightly closer to the camera to overlay on the scene.			
			glBindVertexArray(VAO_UI)
			glBindTextureUnit(0, UI_TEXTURE_ID)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
			glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
			glBindVertexArray(0)


			#Finally delete the current UI data to prevent a memory overflow
			#Display current frame to user.
			glDeleteTextures([UI_TEXTURE_ID])
			PG.display.flip()

			pathfinding.NPC_NODE_GRAPH.CLEAR_NEW_NODES()


			if not PLAYER.ALIVE:
				ui.UPDATE_VIGNETTE(CONSTANTS["HURT_COLOUR"], FPS, FADEOUT=float("inf"))
				RUN, SCREEN, WINDOW_FOCUS = ui.PROCESS_UI_STATE(
					SCREEN,
					ui.REVIVE_SCREEN, KEY_STATES,
					(VAO_QUAD, VAO_UI),
					QUAD_SHADER,
					BACKGROUND=PREVIOUS_FRAME,
					UI_DATA=PLAYER,
				)



		#Quitting/Deleting all that needs to be done, when RUN == False
		FRAME_BUFFERS = [FBO_SCENE,]
		VERTEX_BUFFERS = [VAO_SCENE, VAO_QUAD, VAO_UI]
		DATA_BUFFERS = [VBO_SCENE, EBO_SCENE, TCB_SCENE]

		glDeleteFramebuffers(len(FRAME_BUFFERS), FRAME_BUFFERS)
		glDeleteVertexArrays(len(VERTEX_BUFFERS), VERTEX_BUFFERS)
		glDeleteBuffers(len(DATA_BUFFERS), DATA_BUFFERS)

		PG.mouse.set_visible(True)
		PG.joystick.quit()
		PG.quit()
		sys.exit()

	except Exception as E:
		log.ERROR("Mainloop", E)



if __name__ == "__main__":
	MAIN()

else:
	#If this isn"t being run as __main__, something has gone very wrong and needs to be logged - it is not intended to ever occur.
	log.ERROR("main.py", "IsNotMain")
