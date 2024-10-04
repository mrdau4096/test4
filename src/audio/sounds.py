"""
[audio.py]
Loads audio files and sounds in the .wav format from /audio/

______________________
Importing other files;
-log.py
"""

from exct import log
try:
	#Importing base python modules
	import sys, os
	import math as maths
	import numpy as NP

	#Stop PyGame from giving that annoying welcome message
	os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

	sys.path.extend(("src", r"src\exct\data", r"src\exct\glsl"))
	import pygame as PG
	from pygame import time, joystick, display, image

	#Import other sub-files.
	from exct import utils
	from exct.utils import *

except Exception as E:
	log.ERROR("audio.py", E)

log.REPORT_IMPORT("audio.py")



#Implement actual sounds later.


def LOAD_AUDIO(FILE_NAME):
	#Loads a given audio WAV file.
	return None


def PLAY_SOUND(SOUND_NAME):
	#Plays a sound using the name of a previously loaded file.
	pass