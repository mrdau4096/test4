"""
[ui.py]
Creates the UI, based off of data such as player stats and current item.
Makes use of PyGame drawing/image manipulation functions.
______________________
Importing other files;
-texture_load.py
-log.py
"""
from exct import log
try:
	#Importing base python modules
	import sys, os
	import time as tm
	import math as maths
	import numpy as NP

	#Stop PyGame from giving that annoying welcome message
	os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

	sys.path.extend(("src", r"src\exct\data", r"src\exct\glsl"))
	import pygame as PG
	from pygame import time, joystick, display, image
	from OpenGL.GL import *
	from OpenGL.GLU import *
	from OpenGL.GL.shaders import compileProgram, compileShader

	#Import other sub-files.
	from imgs import texture_load
	from exct import log, utils, render
	from exct.utils import *

except Exception as E:
	log.ERROR("ui.py", E)


#log.REPORT_IMPORT("ui.py")

global IMAGE_CACHE, UI_SURFACE, COLOURED_VIGNETTE, VIGNETTE_COLOUR #For caching of images, so they are not loaded multiple times. Also UI_SURFACE for all UI drawing.
PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS
UI_SURFACE = PG.Surface(list(CONSTANTS["UI_RESOLUTION"]), PG.SRCALPHA)
VIGNETTE_FADEOUT_TIME, VIGNETTE_FADEOUT_CURRENT = 0.0, 0.0


IMAGE_CACHE = {}
#Dictionary of "standard" UI colours.
UI_COLOURS = {
	"SMOKY_BLACK": RGBA(20, 17, 15, 255),
	"DAVYS_GRAY": RGBA(72, 71, 74, 255),
	"SILVER": RGBA(186, 186, 186, 255),
	"WHITE_SMOKE": RGBA(245, 245, 245, 255),
	"MOSS_GREEN": RGBA(116, 142, 84, 255),
	"GOLD_TIPS": RGBA(229, 172, 43, 255),
}
OPTION_DISPLAY_NAMES = {
	"FPS_LIMIT": "Max FPS.",
	"FPS_DEFOCUS": "Lower BG. FPS",
	"PLAYER_SPEED_TURN_MOUSE": "Mouse Speed",
	"HARDER_HOSTILES": "Harder Enemies",
	"INF_AMMO": "Infinite Energy",
}
SKIPPED_PREFIXES = (
	"SCENE",
	"DEBUG",
	"DEV",
)

def UPDATE_CONFIG(CONFIG_NAME, EFFECT, BUTTON):
	CURRENT_VALUE = PREFERENCES[CONFIG_NAME]
	TYPE = type(CURRENT_VALUE)
	if TYPE == bool:
		PREFERENCES[CONFIG_NAME] = BUTTON.STATE
	elif TYPE == float:
		PREFERENCES[CONFIG_NAME] = round(PREFERENCES[CONFIG_NAME] + EFFECT, 1)
	elif TYPE == int:
		PREFERENCES[CONFIG_NAME] = CLAMP(PREFERENCES[CONFIG_NAME] + EFFECT, 0, float("inf"))
	else:
		log.ERROR("ui.py // UPDATE_CONFIG", f"Unknown type [{TYPE}] -> {CONFIG_NAME}: {CURRENT_VALUE}")
			

def CREATE_CONFIG_MENU():
	Y_INDEXES, Y_OFFSET = {bool:0,int:0,float:0}, 30
	MENU_DATA = []
	for KEY, VALUE in PREFERENCES.items():
		if any([KEY.startswith(OPTION) for OPTION in SKIPPED_PREFIXES]): continue #Continue if the option isnt to be shown in the menu.
		#Show a display name rather than the internal option name.
		NAME = KEY if KEY not in OPTION_DISPLAY_NAMES else OPTION_DISPLAY_NAMES[KEY]
		TYPE = type(VALUE)
		if TYPE == bool:
			Y_INDEXES[bool] += Y_OFFSET
			BUTTON_DATA = ({
				"X_POS": 555,
				"WIDTH": 70,
				"OFF_TEXT": "False",
				"ON_TEXT": "True",
				"EFFECT": bool,
				"TOGGLE": True,
				"STATE": VALUE,
			},)
		elif TYPE in (int, float):
			Y_INDEXES[int] += Y_OFFSET
			Y_INDEXES[float] += Y_OFFSET
			INCREMENT = 0.1 if type(VALUE) == float else 1
			BUTTON_DATA = ({
				"X_POS": 5,
				"WIDTH": 60,
				"OFF_TEXT": f"-{INCREMENT}",
				"ON_TEXT": f"-{INCREMENT}",
				"EFFECT": -INCREMENT,
				"TOGGLE": False,
				"STATE": None
			},{
				"X_POS": 290,
				"WIDTH": 60,
				"OFF_TEXT": f"+{INCREMENT}",
				"ON_TEXT": f"+{INCREMENT}",
				"EFFECT": INCREMENT,
				"TOGGLE": False,
				"STATE": None
			},)
		else:
			log.ERROR("ui.py // CREATE_CONFIG_MENU", f"Unknown type [{TYPE}] -> {KEY}: {VALUE}")



		MENU_BUTTON_DATA = [BUTTON(VECTOR_2D(ELEMENT["X_POS"], 25+Y_INDEXES[TYPE]), VECTOR_2D(ELEMENT["WIDTH"], 25), UPDATE_CONFIG, RGBA(25, 25, 25, 255), RGBA(50, 50, 50, 255), ELEMENT["OFF_TEXT"], ELEMENT["ON_TEXT"], TEXT_COLOUR=UI_COLOURS["GOLD_TIPS"], TOGGLE=ELEMENT["TOGGLE"], FUNCTION_VALUES=(KEY, ELEMENT["EFFECT"]), START_STATE=ELEMENT["STATE"]) for ELEMENT in BUTTON_DATA]

		MENU_DATA.extend(MENU_BUTTON_DATA)

	return MENU_DATA

def DRAW_OPTIONS_TEXT(UI_SURFACE):
	Y_INDEXES, Y_OFFSET = {bool:0,int:0,float:0}, 30
	for KEY, VALUE in PREFERENCES.items():
		if any([KEY.startswith(OPTION) for OPTION in SKIPPED_PREFIXES]): continue #Continue if the option isnt to be shown in the menu.
		#Show a display name rather than the internal option name.
		NAME = KEY if KEY not in OPTION_DISPLAY_NAMES else OPTION_DISPLAY_NAMES[KEY]
		TYPE = type(VALUE)
		if TYPE == bool:
			Y_INDEXES[bool] += Y_OFFSET
			TEXT_DATA = {
				"X_POS": 355,
				"WIDTH": 200,
				"TEXT": f"{NAME}:"
			}
		elif TYPE in (int, float):
			Y_INDEXES[int] += Y_OFFSET
			Y_INDEXES[float] += Y_OFFSET
			INCREMENT = 0.1 if type(VALUE) == float else 1
			TEXT_DATA = {
				"X_POS": 65,
				"WIDTH": 225,
				"TEXT": f"{NAME}: {PREFERENCES[KEY]}"
			}
		else:
			log.ERROR("ui.py // CREATE_CONFIG_MENU", f"Unknown type [{TYPE}] -> {KEY}: {VALUE}")

		CHAR_WIDTH = 12
		TEXT_RECT = PG.Rect(TEXT_DATA["X_POS"], 25+Y_INDEXES[TYPE], TEXT_DATA["WIDTH"], 25)
		PG.draw.rect(UI_SURFACE, (25, 25, 25, 255), TEXT_RECT)
		PG.draw.rect(UI_SURFACE, list(UI_COLOURS["GOLD_TIPS"]), TEXT_RECT, width=2)
		DRAW_TEXT(UI_SURFACE, TEXT_DATA["TEXT"], (TEXT_DATA["X_POS"]+(0.5*TEXT_DATA["WIDTH"])-(0.5*len(TEXT_DATA["TEXT"])*CHAR_WIDTH), 25+Y_INDEXES[TYPE]+5), 12, COLOUR=UI_COLOURS["GOLD_TIPS"])




#General UI related functions


def DRAW_TEXT(SCREEN, TEXT, POSITION, FONT_SIZE, COLOUR=RGBA(255, 255, 255, 255)):
	#Draws text on a given surface, with colour, size and position.
	FONT = PG.font.Font('src\\exct\\fonts\\PressStart2P-Regular.ttf', FONT_SIZE)
	text_surface = FONT.render(str(TEXT), True, list(COLOUR))
	SCREEN.blit(text_surface, POSITION)

def LOAD_IMG(IMAGE_NAME):
	if IMAGE_NAME in IMAGE_CACHE:
		return IMAGE_CACHE[IMAGE_NAME]
	else:
		IMAGE = PG.image.load(f"{IMAGE_NAME}.png")
		IMAGE_CACHE[IMAGE_NAME] = IMAGE
		return IMAGE

def DRAW_IMG(SCREEN, IMG_NAME, POSITION, SCALE):
	#Draws an image loaded from the file structure (in \src\imgs\) to a position and with scale.
	try:
		IMAGE = LOAD_IMG(f"src\\imgs\\{IMG_NAME}")
	except FileNotFoundError:
		IMAGE = LOAD_IMG(f"src\\imgs\\{texture_load.FALLBACK_TEXTURE}")
	SCALED_IMAGE = PG.transform.scale(IMAGE, SCALE)
	SCREEN.blit(SCALED_IMAGE, POSITION)



#UI screens & HUD


def UPDATE_VIGNETTE(NEW_VIGNETTE_COLOUR, FPS, FADEOUT=None):
	global VIGNETTE_COLOUR, VIGNETTE_FADEOUT_TIME, VIGNETTE_FADEOUT_CURRENT
	if FADEOUT is not None:
		VIGNETTE_FADEOUT_TIME, VIGNETTE_FADEOUT_CURRENT = FADEOUT, 0.0
	VIGNETTE_FADEOUT_CURRENT += 1/FPS
	if VIGNETTE_FADEOUT_CURRENT < VIGNETTE_FADEOUT_TIME:
		VIGNETTE_COLOUR = NEW_VIGNETTE_COLOUR
		FADE = 1.0 - (VIGNETTE_FADEOUT_CURRENT/VIGNETTE_FADEOUT_TIME)
		FADE_COLOUR = RGBA(
			VIGNETTE_COLOUR.R,
			VIGNETTE_COLOUR.G,
			VIGNETTE_COLOUR.B,
			FADE * 255,
		)
		VIGNETTE_IMAGE = LOAD_IMG("src\\imgs\\ui-vignette")
		COLOURED_VIGNETTE = PG.Surface(list(CONSTANTS["UI_RESOLUTION"]), PG.SRCALPHA)
		COLOURED_VIGNETTE.fill(list(FADE_COLOUR))
		COLOURED_VIGNETTE.blit(VIGNETTE_IMAGE, (0, 0), special_flags=PG.BLEND_RGBA_MULT)
		return COLOURED_VIGNETTE



def HUD(PLAYER, FPS):
	#Draws the heads-up display (HUD) user-interface (UI) onto a PyGame surface, which is then returned as an OpenGL texture.
	#Uses data about the player, such as Health and Energy.
	#try:
		#Fill the UI surface with transparent pixels first.
		UI_SURFACE.fill([0, 0, 0, 0])

		#Draw the Vignette, if necessary.
		if VIGNETTE_COLOUR != RGBA(0, 0, 0, 0):
			#If not the default, starting value;
			COLOURED_VIGNETTE = UPDATE_VIGNETTE(VIGNETTE_COLOUR, FPS)
			if COLOURED_VIGNETTE is not None:
				UI_SURFACE.blit(COLOURED_VIGNETTE, (0, 0))

		#Draw the "Crosshair" cross.
		PG.draw.line(UI_SURFACE, list(UI_COLOURS["SMOKY_BLACK"]), (320, 177), (320, 183.5), 3)
		PG.draw.line(UI_SURFACE, list(UI_COLOURS["SMOKY_BLACK"]), (317, 180), (323.5, 180), 3)
		PG.draw.line(UI_SURFACE, list(UI_COLOURS["SILVER"]), (320, 177.5), (320, 183.5), 1)
		PG.draw.line(UI_SURFACE, list(UI_COLOURS["SILVER"]), (317.5, 180), (323.5, 180), 1)

		#Draw the lower-left info panel.
		DRAW_TEXT(UI_SURFACE, str(PLAYER.ENERGY).zfill(3), (105, 322), 16, COLOUR=UI_COLOURS["GOLD_TIPS"])
		DRAW_TEXT(UI_SURFACE, str(PLAYER.HEALTH).zfill(3), (105, 343), 16, COLOUR=UI_COLOURS["GOLD_TIPS"])
		DRAW_IMG(UI_SURFACE, "ui-energy", (5, 322), (94, 16))
		DRAW_IMG(UI_SURFACE, "ui-health", (5, 343), (88, 16))

		#Top-Right corner's FPS counter.
		DRAW_TEXT(UI_SURFACE, f"FPS: {str(maths.floor(FPS)).zfill(2)}", (583, 2), 8, COLOUR=UI_COLOURS["GOLD_TIPS"])

		#Held Item, using player's held item.
		ITEM_TEXTURE = PLAYER.ITEMS[PLAYER.HELD_ITEM][9]
		if ITEM_TEXTURE is not None:
			DRAW_IMG(UI_SURFACE, f"item-{str(ITEM_TEXTURE)}", (384, 104), (256, 256))


		#Top-Left debug notices.
		DEBUG_TYPES = {
			"DEBUG_MAPS": PREFERENCES["DEBUG_MAPS"],
			"DEBUG_UI": PREFERENCES["DEBUG_UI"],
			"DEBUG_NORMALS": PREFERENCES["DEBUG_NORMALS"],
			"DEBUG_PROFILER": PREFERENCES["DEBUG_PROFILER"],
			"DEBUG_RAYS": PREFERENCES["DEBUG_RAYS"],
			"DEBUG_WIREFRAME": PREFERENCES["DEBUG_WIREFRAME"],
			"DEV_TEST": PREFERENCES["DEV_TEST"],
		}
		
		for I, (DEBUG_TYPE, ENABLED) in enumerate(DEBUG_TYPES.items()):
			if ENABLED:
				DRAW_TEXT(UI_SURFACE, DEBUG_TYPE, (5, (10*I) + 2), 8, COLOUR=UI_COLOURS["GOLD_TIPS"])

		if PREFERENCES["DEV_TEST"]:
			PLAYER_POS_TEXT = f"({round(PLAYER.POSITION.X, 2)}, {round(PLAYER.POSITION.Y, 2)}, {round(PLAYER.POSITION.Z, 2)})"
			PLAYER_ROT_TEXT = f"({round(PLAYER.ROTATION.X, 2)}, {round(PLAYER.ROTATION.Y, 2)})"
			DRAW_TEXT(UI_SURFACE, PLAYER_POS_TEXT, (320-(8*(len(PLAYER_POS_TEXT)/2)), 5), 8, COLOUR=UI_COLOURS["GOLD_TIPS"])
			DRAW_TEXT(UI_SURFACE, PLAYER_ROT_TEXT, (320-(8*(len(PLAYER_ROT_TEXT)/2)), 15), 8, COLOUR=UI_COLOURS["GOLD_TIPS"])
			

		#Convert to an OpenGL texture.
		UI_SURFACE_ID = render.SURFACE_TO_TEXTURE(UI_SURFACE, CONSTANTS["UI_RESOLUTION"].TO_INT())

		return UI_SURFACE_ID

	#except Exception as E:
		#log.ERROR("ui.HUD", E)


def PROCESS_UI_STATE(SCREEN, UI_TYPE, KEY_STATES, VAOs, QUAD_SHADER, BACKGROUND=None, BACKGROUND_SHADE=True, UI_DATA=None):
		"""
		Handles the current UI screen (UI_TYPE) and acts as its own loop to control the context.
		Swapping the PG screen resolution
		"""
	#try:
		if UI_TYPE == OPTIONS_MENU:
			UI_DATA = CREATE_CONFIG_MENU()

		PG.mouse.set_visible(True)
		VAO_QUAD, VAO_UI = VAOs
		MOUSE_POSITION = VECTOR_2D(0, 0)
		UI_RESOLUTION = utils.CONSTANTS["UI_RESOLUTION"]
		DISPLAY_RESOLUTION = utils.CONSTANTS["DISPLAY_RESOLUTION"]
		WINDOW_FOCUS = 0
		UI_ACTIVE, RUN = True, True
		while UI_ACTIVE:
			EVENTS = PG.event.get()
			for EVENT in EVENTS:
				match EVENT.type:
					case PG.QUIT:
						PG.mouse.set_visible(True)
						PG.joystick.quit()
						PG.quit()
						sys.exit()

					case PG.VIDEORESIZE:
						#Display size changes handled
						DISPLAY_RESOLUTION = VECTOR_2D(EVENT.w, EVENT.h)
						utils.CONSTANTS["DISPLAY_RESOLUTION"] = DISPLAY_RESOLUTION
						SCREEN = PG.display.set_mode(list(DISPLAY_RESOLUTION), PG.DOUBLEBUF | PG.OPENGL | PG.RESIZABLE)
						FBO_SCENE, TCB_SCENE, _, _, _ = render.CREATE_FBO(DISPLAY_RESOLUTION)
						glViewport(0, 0, int(DISPLAY_RESOLUTION.X), int(DISPLAY_RESOLUTION.Y))
						DISPLAY_CENTRE = DISPLAY_RESOLUTION / 2

					case PG.KEYDOWN:
						if EVENT.key in KEY_STATES:
							KEY_STATES[EVENT.key] = True
						match EVENT.key:
							case PG.K_BACKSPACE:
								PG.mouse.set_visible(True)
								PG.joystick.quit()
								PG.quit()
								sys.exit()
							case PG.K_ESCAPE:
								return True, SCREEN, 1

					case PG.KEYUP:
						if EVENT.key in KEY_STATES:
							KEY_STATES[EVENT.key] = False

					case PG.MOUSEBUTTONDOWN:
						if EVENT.button in KEY_STATES:
							KEY_STATES[EVENT.button] = True

					case PG.MOUSEBUTTONUP:
						if EVENT.button in KEY_STATES:
							KEY_STATES[EVENT.button] = False

					case PG.ACTIVEEVENT:
						if EVENT.state == 2:
							WINDOW_FOCUS = EVENT.gain

					case PG.MOUSEMOTION:
						MOUSE_POSITION = VECTOR_2D(EVENT.pos[0]*UI_RESOLUTION.X/DISPLAY_RESOLUTION.X, EVENT.pos[1]*UI_RESOLUTION.Y/DISPLAY_RESOLUTION.Y)


			DEFAULT_DATA = (MOUSE_POSITION, BACKGROUND_SHADE, KEY_STATES, any([EVENT.type == PG.MOUSEBUTTONUP for EVENT in EVENTS]))
			if UI_DATA is not None:
				UI_SURFACE, EXTRA_DATA, UI_ACTIVE = UI_TYPE(DEFAULT_DATA, UI_DATA) #Call one of the UI functions with data
			else:
				UI_SURFACE, EXTRA_DATA, UI_ACTIVE = UI_TYPE(DEFAULT_DATA) #Call one of the UI functions without data
			UI_SURFACE_ID = render.SURFACE_TO_TEXTURE(UI_SURFACE, CONSTANTS["UI_RESOLUTION"].TO_INT())
			if PREFERENCES["DEBUG_UI"]: render.SAVE_MAP(CONSTANTS["UI_RESOLUTION"], UI_SURFACE_ID, f"src\\debug_maps\\colour_map_UI.png", "COLOUR")


			if "QUIT" in EXTRA_DATA:
				if EXTRA_DATA["QUIT"]:
					return False, SCREEN, 0

			
			glViewport(0, 0, int(DISPLAY_RESOLUTION.X), int(DISPLAY_RESOLUTION.Y))
			glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
			glUseProgram(QUAD_SHADER)

			SCREEN_TEXTURE_LOC = glGetUniformLocation(QUAD_SHADER, "SCREEN_TCB")
			glUniform1i(SCREEN_TEXTURE_LOC, 0)

			#Draw background layer if BACKGROUND is not None
			if BACKGROUND is not None:
				glBindVertexArray(VAO_QUAD)
				glActiveTexture(GL_TEXTURE0)
				glBindTexture(GL_TEXTURE_2D, BACKGROUND)
				glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
				glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
				glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
				glBindTexture(GL_TEXTURE_2D, 0)
				glBindVertexArray(0)

			#Draw UI layer
			glBindVertexArray(VAO_UI)
			glActiveTexture(GL_TEXTURE0)
			glBindTexture(GL_TEXTURE_2D, UI_SURFACE_ID)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
			glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
			glBindTexture(GL_TEXTURE_2D, 0)
			glBindVertexArray(0)



			#Show UI screen to user.
			glDeleteTextures([UI_SURFACE_ID])
			PG.display.flip()


		return RUN, SCREEN, 1

	#except Exception as E:
		#log.ERROR("ui.py // PROCESS_UI_STATE", E)




def DISPLAY_BUTTONS(UI_SURFACE, BUTTONS, MOUSE_POSITION, KEY_STATES, MOUSEBUTTONUP):
	RESULTS_DICT = {}
	for ELEMENT in BUTTONS:
		RESULTS_DICT[ELEMENT.OFF_TEXT] = ELEMENT.EVALUATE_STATE(MOUSE_POSITION, KEY_STATES, MOUSEBUTTONUP)
		ELEMENT.DRAW(UI_SURFACE)
	return RESULTS_DICT



def PAUSE_MENU(DEFAULT_DATA, OPTIONS_DATA):
	MOUSE_POSITION, BACKGROUND_SHADE, KEY_STATES, MOUSEBUTTONUP = DEFAULT_DATA
	UI_SURFACE.fill([25, 25, 25, 200] if BACKGROUND_SHADE else [0, 0, 0, 0])
	BUTTONS = (
		BUTTON(VECTOR_2D(25, 25), VECTOR_2D(250, 25), TRUE, RGBA(25, 25, 25, 255), RGBA(50, 50, 50, 255), "RESUME", "RESUME", TEXT_COLOUR=UI_COLOURS["GOLD_TIPS"]),
		BUTTON(VECTOR_2D(25, 75), VECTOR_2D(250, 25), PROCESS_UI_STATE, RGBA(25, 25, 25, 255), RGBA(50, 50, 50, 255), "OPTIONS", "OPTIONS", FUNCTION_VALUES=OPTIONS_DATA, TEXT_COLOUR=UI_COLOURS["GOLD_TIPS"]),
		BUTTON(VECTOR_2D(25, 125), VECTOR_2D(250, 25), TRUE, RGBA(25, 25, 25, 255), RGBA(50, 50, 50, 255), "QUIT", "QUIT", TEXT_COLOUR=UI_COLOURS["GOLD_TIPS"]),
	)

	RESULTS_DICT = DISPLAY_BUTTONS(UI_SURFACE, BUTTONS, MOUSE_POSITION, KEY_STATES, MOUSEBUTTONUP)
	

	if RESULTS_DICT["RESUME"]:
		return UI_SURFACE, RESULTS_DICT, False
	return UI_SURFACE, RESULTS_DICT, True



def MAIN_MENU(DEFAULT_DATA, OPTIONS_DATA):
	MOUSE_POSITION, BACKGROUND_SHADE, KEY_STATES, MOUSEBUTTONUP = DEFAULT_DATA
	UI_SURFACE.fill([25, 25, 25, 200] if BACKGROUND_SHADE else [0, 0, 0, 0])
	BUTTONS = (
		BUTTON(VECTOR_2D(25, 225), VECTOR_2D(250, 25), TRUE, RGBA(25, 25, 25, 255), RGBA(50, 50, 50, 255), "CONTINUE", "CONTINUE", TEXT_COLOUR=UI_COLOURS["GOLD_TIPS"]),
		BUTTON(VECTOR_2D(25, 275), VECTOR_2D(250, 25), PROCESS_UI_STATE, RGBA(25, 25, 25, 255), RGBA(50, 50, 50, 255), "OPTIONS", "OPTIONS", FUNCTION_VALUES=OPTIONS_DATA, TEXT_COLOUR=UI_COLOURS["GOLD_TIPS"]),
		BUTTON(VECTOR_2D(25, 325), VECTOR_2D(250, 25), TRUE, RGBA(25, 25, 25, 255), RGBA(50, 50, 50, 255), "QUIT", "QUIT", TEXT_COLOUR=UI_COLOURS["GOLD_TIPS"]),
	)

	DRAW_IMG(UI_SURFACE, "ui-title", (275, 20), (360, 144))

	RESULTS_DICT = DISPLAY_BUTTONS(UI_SURFACE, BUTTONS, MOUSE_POSITION, KEY_STATES, MOUSEBUTTONUP)
	if RESULTS_DICT["CONTINUE"] or RESULTS_DICT["QUIT"]:
		return UI_SURFACE, RESULTS_DICT, False
	return UI_SURFACE, RESULTS_DICT, True



def OPTIONS_MENU(DEFAULT_DATA, OPTIONS_MENU_BUTTONS):
	MOUSE_POSITION, BACKGROUND_SHADE, KEY_STATES, MOUSEBUTTONUP = DEFAULT_DATA
	UI_SURFACE.fill([25, 25, 25, 200] if BACKGROUND_SHADE else [0, 0, 0, 0])
	BUTTONS = [
		BUTTON(VECTOR_2D(25, 325), VECTOR_2D(250, 25), TRUE, RGBA(25, 25, 25, 255), RGBA(50, 50, 50, 255), "BACK", "BACK", TEXT_COLOUR=UI_COLOURS["GOLD_TIPS"]),
		BUTTON(VECTOR_2D(275, 325), VECTOR_2D(250, 25), utils.SAVE_CONFIGS, RGBA(25, 25, 25, 255), RGBA(50, 50, 50, 255), "APPLY", "APPLY", TEXT_COLOUR=UI_COLOURS["GOLD_TIPS"], FUNCTION_VALUES=(PREFERENCES, CONSTANTS)),
	]

	BUTTONS.extend(OPTIONS_MENU_BUTTONS)


	DRAW_TEXT(UI_SURFACE, "Change options;", (5,5), 25, COLOUR=UI_COLOURS["GOLD_TIPS"])
	DRAW_TEXT(UI_SURFACE, "Restart after applying to ensure options are used.", (5,35), 12, COLOUR=UI_COLOURS["GOLD_TIPS"])
	RESULTS_DICT = DISPLAY_BUTTONS(UI_SURFACE, BUTTONS, MOUSE_POSITION, KEY_STATES, MOUSEBUTTONUP)


	DRAW_OPTIONS_TEXT(UI_SURFACE)

	if RESULTS_DICT["BACK"]:
		return UI_SURFACE, RESULTS_DICT, False
	return UI_SURFACE, RESULTS_DICT, True



def REVIVE_SCREEN(DEFAULT_DATA, REVIVE_DATA):
	MOUSE_POSITION, BACKGROUND_SHADE, KEY_STATES, MOUSEBUTTONUP = DEFAULT_DATA
	UI_SURFACE.fill([25, 25, 25, 200] if BACKGROUND_SHADE else [0, 0, 0, 0])
	UI_SURFACE.blit(COLOURED_VIGNETTE, (0, 0))
	BUTTONS = [
		BUTTON(VECTOR_2D(25, 325), VECTOR_2D(250, 25), TRUE, RGBA(25, 25, 25, 255), RGBA(50, 50, 50, 255), "QUIT", "QUIT", TEXT_COLOUR=UI_COLOURS["GOLD_TIPS"]),
		BUTTON(VECTOR_2D(365, 325), VECTOR_2D(250, 25), utils.RESET_PLAYER, RGBA(25, 25, 25, 255), RGBA(50, 50, 50, 255), "REVIVE", "REVIVE", TEXT_COLOUR=UI_COLOURS["GOLD_TIPS"], FUNCTION_VALUES=REVIVE_DATA),
	]

	RESULTS_DICT = DISPLAY_BUTTONS(UI_SURFACE, BUTTONS, MOUSE_POSITION, KEY_STATES, MOUSEBUTTONUP)
	if RESULTS_DICT["REVIVE"] or RESULTS_DICT["QUIT"]:
		return UI_SURFACE, RESULTS_DICT, False
	return UI_SURFACE, RESULTS_DICT, True



def TRUE():
	return True

def FALSE():
	return True


