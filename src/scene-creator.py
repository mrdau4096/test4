import os, sys
import math as maths
from imgs import texture_load
from exct import utils, log
from scenes import scene
from exct.utils import *

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
sys.path.append("modules.zip")
import pygame as PG
from pygame.locals import *
import numpy as NP
import copy

global DISPLAY_RESOLUTION
global scale
global offset
global in_box
scale = 20
offset = VECTOR_3D(0.0, 0.0, 0.0)
in_box = False

def draw_grid(screen, rect, viewport_name):
	# Draw a simple grid in the given rect
	grid_color = (100, 100, 100)

	match viewport_name:
		case "XY (A/D, E/Q)":
			gridoffset_a = ((offset.X) % scale) - (0.5 * scale)
			gridoffset_b = (offset.Y * -1) % scale
			right = rect.right - scale
		case "ZY (W/S, E/Q)":
			gridoffset_a = offset.Z % scale
			gridoffset_b = (offset.Y * -1) % scale
			right = rect.right
		case "XZ (A/D, W/S)":
			gridoffset_a = offset.X % scale
			gridoffset_b = offset.Z % scale
			right = rect.right


	for x in range(rect.left, round(right), round(scale)):
		PG.draw.line(screen, grid_color, (x + gridoffset_a, rect.top), (x + gridoffset_a, rect.bottom))
	for y in range(rect.top, rect.bottom, round(scale)):
		PG.draw.line(screen, grid_color, (rect.left, y + gridoffset_b), (rect.right, y + gridoffset_b))

def clip_line(line, rect):
	""" Clip the line to ensure it stays within the rectangle """
	x1, y1 = line[0]
	x2, y2 = line[1]
	xmin, ymin = rect.topleft
	xmax, ymax = rect.bottomright

	def clip(p, q, u1, u2):
		if p < 0:
			r = q / p
			if r > u2:
				return False, u1, u2
			if r > u1:
				u1 = r
		elif p > 0:
			r = q / p
			if r < u1:
				return False, u1, u2
			if r < u2:
				u2 = r
		elif q < 0:
			return False, u1, u2
		return True, u1, u2

	dx = x2 - x1
	dy = y2 - y1
	u1, u2 = 0.0, 1.0

	accept, u1, u2 = clip(-dx, x1 - xmin, u1, u2)
	if not accept:
		return None
	accept, u1, u2 = clip(dx, xmax - x1, u1, u2)
	if not accept:
		return None
	accept, u1, u2 = clip(-dy, y1 - ymin, u1, u2)
	if not accept:
		return None
	accept, u1, u2 = clip(dy, ymax - y1, u1, u2)
	if not accept:
		return None

	if u2 < 1.0:
		x2 = x1 + u2 * dx
		y2 = y1 + u2 * dy
	if u1 > 0.0:
		x1 = x1 + u1 * dx
		y1 = y1 + u1 * dy

	return (x1, y1), (x2, y2)

def draw_lines(screen, lines, rect, viewport_name):
	# Draw the lines in the given rect
	for line in lines:
		for ln in line[1:]:
			if ln[0] == viewport_name:
				clipped_line = clip_line(
					((rect.left + ln[1].X, rect.top + ln[1].Y), 
					 (rect.left + ln[2].X, rect.top + ln[2].Y)), rect)
				if clipped_line:
					if line[0] == "P":
						PG.draw.circle(screen, (255, 128, 255), clipped_line[0], 2)

					else:
						match line[0]:
							case"E": 
								colour = (200, 200, 200)
								thickness = 2
							case "N": 
								colour = (255, 0, 255)
								thickness = 1
							case "L":
								colour = (255, 128, 128)
								thickness = 1

						PG.draw.line(screen, colour, clipped_line[0], clipped_line[1], thickness)

def CONVERT_TO_2D(DATA_3D):
	DATA_2D = []
	for ln in DATA_3D:
		DATA_2D.append((
			ln[0],
			("XY (A/D, E/Q)", VECTOR_2D(ln[1].X, -1 * ln[1].Y), VECTOR_2D(ln[2].X, -1 * ln[2].Y)),
			("ZY (W/S, E/Q)", VECTOR_2D(ln[1].Z, -1 * ln[1].Y), VECTOR_2D(ln[2].Z, -1 * ln[2].Y)),
			("XZ (A/D, W/S)", VECTOR_2D(ln[1].X, ln[1].Z), VECTOR_2D(ln[2].X, ln[2].Z))
		))
	return DATA_2D

def IS_IN_RECTANGLE(POSITION, RECTANGLE):
	if (POSITION.X < RECTANGLE[0] or POSITION.X > (RECTANGLE[0] + RECTANGLE[2])) or (POSITION.Y < RECTANGLE[1] or POSITION.Y > (RECTANGLE[1] + RECTANGLE[3])):
		return False
	return True

def calculate_frustum_lines(LIGHT):
	# Example light properties
	aspect_ratio = 1.0  # Aspect ratio of the frustum, if needed use LIGHT.ASPECT_RATIO

	# Compute direction
	direction = (LIGHT.LOOK_AT - LIGHT.POSITION).NORMALISE()

	# Calculate frustum dimensions
	near_height = 2 * NP.tan(NP.radians(LIGHT.FOV) / 2) * LIGHT.MIN_DISTANCE
	near_width = near_height * aspect_ratio
	far_height = 2 * NP.tan(NP.radians(LIGHT.FOV) / 2) * LIGHT.MAX_DISTANCE
	far_width = far_height * aspect_ratio

	# Compute right and up vectors
	right = direction.CROSS(VECTOR_3D(0, 1, 0))
	right = right.NORMALISE()
	up = right.CROSS(direction)

	# Compute centers of near and far planes
	near_center = LIGHT.POSITION + direction * LIGHT.MIN_DISTANCE
	far_center = LIGHT.POSITION + direction * LIGHT.MAX_DISTANCE

	# Compute corners of the near and far planes
	near_top_left = near_center + (up * near_height / 2) - (right * near_width / 2)
	near_top_right = near_center + (up * near_height / 2) + (right * near_width / 2)
	near_bottom_left = near_center - (up * near_height / 2) - (right * near_width / 2)
	near_bottom_right = near_center - (up * near_height / 2) + (right * near_width / 2)

	far_top_left = far_center + (up * far_height / 2) - (right * far_width / 2)
	far_top_right = far_center + (up * far_height / 2) + (right * far_width / 2)
	far_bottom_left = far_center - (up * far_height / 2) - (right * far_width / 2)
	far_bottom_right = far_center - (up * far_height / 2) + (right * far_width / 2)

	# Create a list of lines representing the frustum
	lines_list = [
		# Near plane edges
		("L", (near_top_left * scale) + offset, (near_top_right * scale) + offset),
		("L", (near_top_right * scale) + offset, (near_bottom_right * scale) + offset),
		("L", (near_bottom_right * scale) + offset, (near_bottom_left * scale) + offset),
		("L", (near_bottom_left * scale) + offset, (near_top_left * scale) + offset),

		# Far plane edges
		("L", (far_top_left * scale) + offset, (far_top_right * scale) + offset),
		("L", (far_top_right * scale) + offset, (far_bottom_right * scale) + offset),
		("L", (far_bottom_right * scale) + offset, (far_bottom_left * scale) + offset),
		("L", (far_bottom_left * scale) + offset, (far_top_left * scale) + offset),

		# Connecting edges between near and far planes
		("L", (near_top_left * scale) + offset, (far_top_left * scale) + offset),
		("L", (near_top_right * scale) + offset, (far_top_right * scale) + offset),
		("L", (near_bottom_left * scale) + offset, (far_bottom_left * scale) + offset),
		("L", (near_bottom_right * scale) + offset, (far_bottom_right * scale) + offset)
	]

	return lines_list


def LOAD_BOXES(TEXTINPUTS, TEXTBOXES, DROPDOWNS, type_name):
	TEXTINPUTS_COPY, TEXTBOXES_COPY, DROPDOWNS_COPY = TEXTINPUTS.copy(), TEXTBOXES.copy(), DROPDOWNS.copy()
	match type_name:
		case "PLAYER":
			TEXTINPUTS_COPY.append(TextInputBox("V1X", 0.775, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.X))
			TEXTINPUTS_COPY.append(TextInputBox("V1Y", 0.825, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.Y))
			TEXTINPUTS_COPY.append(TextInputBox("V1Z", 0.875, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.Z))
			TEXTINPUTS_COPY.append(TextInputBox("COL", 0.825, 0.125, 0.1, 0.025, 15, text=current_object.COLLISION))
			
			TEXTBOXES_COPY.append([["Pos:", 15], 0.725, 0.1, 0.05, 0.025])
			TEXTBOXES_COPY.append([["", 15], 0.725, 0.075, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Collision:", 15], 0.725, 0.125, 0.1, 0.025])
			TEXTBOXES_COPY.append([["Player Items:", 15], 0.725, 0.15, 0.2, 0.025])
		
			DROPDOWNS_COPY.append([0.725, 0.175, 0.05, 0.025, 2, "Slot0", current_object.ITEMS, False])
			DROPDOWNS_COPY.append([0.775, 0.175, 0.05, 0.025, 2, "Slot1", current_object.ITEMS, False])
			DROPDOWNS_COPY.append([0.825, 0.175, 0.05, 0.025, 2, "Slot2", current_object.ITEMS, False])
			DROPDOWNS_COPY.append([0.875, 0.175, 0.05, 0.025, 2, "Slot3", current_object.ITEMS, False])

		case "CUBE_STATIC" | "CUBE_PHYSICS":
			textures = CONV_TEXTURES(current_object.TEXTURE_INFO[0])
			TEXTINPUTS_COPY.append(TextInputBox("V1X", 0.775, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.X))
			TEXTINPUTS_COPY.append(TextInputBox("V1Y", 0.825, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.Y))
			TEXTINPUTS_COPY.append(TextInputBox("V1Z", 0.875, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.Z))
			TEXTINPUTS_COPY.append(TextInputBox("DMX", 0.775, 0.125, 0.05, 0.025, 15, text=current_object.DIMENTIONS.X))
			TEXTINPUTS_COPY.append(TextInputBox("DMY", 0.825, 0.125, 0.05, 0.025, 15, text=current_object.DIMENTIONS.Y))
			TEXTINPUTS_COPY.append(TextInputBox("DMZ", 0.875, 0.125, 0.05, 0.025, 15, text=current_object.DIMENTIONS.Z))
			TEXTINPUTS_COPY.append(TextInputBox("TX1", 0.775, 0.15, 0.05, 0.025, 15, text=textures[0]))
			TEXTINPUTS_COPY.append(TextInputBox("TX2", 0.825, 0.15, 0.05, 0.025, 15, text=textures[1]))
			TEXTINPUTS_COPY.append(TextInputBox("TX3", 0.875, 0.15, 0.05, 0.025, 15, text=textures[2]))
			TEXTINPUTS_COPY.append(TextInputBox("COL", 0.825, 0.175, 0.1, 0.025, 15, text=current_object.COLLISION))
			
			TEXTBOXES_COPY.append([["Pos:", 15], 0.725, 0.1, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Dim:", 15], 0.725, 0.125, 0.05, 0.025])
			TEXTBOXES_COPY.append([["", 15], 0.725, 0.075, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Texture:", 15], 0.725, 0.15, 0.1, 0.025])
			TEXTBOXES_COPY.append([["Collision:", 15], 0.725, 0.175, 0.1, 0.025])

		case "QUAD":
			TEXTINPUTS_COPY.append(TextInputBox("V1X", 0.775, 0.1, 0.05, 0.025, 15, text=current_object.POINTS[0].X))
			TEXTINPUTS_COPY.append(TextInputBox("X1Y", 0.825, 0.1, 0.05, 0.025, 15, text=current_object.POINTS[0].Y))
			TEXTINPUTS_COPY.append(TextInputBox("V1Z", 0.875, 0.1, 0.05, 0.025, 15, text=current_object.POINTS[0].Z))
			TEXTINPUTS_COPY.append(TextInputBox("V2X", 0.775, 0.125, 0.05, 0.025, 15, text=current_object.POINTS[1].X))
			TEXTINPUTS_COPY.append(TextInputBox("X2Y", 0.825, 0.125, 0.05, 0.025, 15, text=current_object.POINTS[1].Y))
			TEXTINPUTS_COPY.append(TextInputBox("V2Z", 0.875, 0.125, 0.05, 0.025, 15, text=current_object.POINTS[1].Z))
			TEXTINPUTS_COPY.append(TextInputBox("V3X", 0.775, 0.15, 0.05, 0.025, 15, text=current_object.POINTS[2].X))
			TEXTINPUTS_COPY.append(TextInputBox("X3Y", 0.825, 0.15, 0.05, 0.025, 15, text=current_object.POINTS[2].Y))
			TEXTINPUTS_COPY.append(TextInputBox("V3Z", 0.875, 0.15, 0.05, 0.025, 15, text=current_object.POINTS[2].Z))
			TEXTINPUTS_COPY.append(TextInputBox("V4X", 0.775, 0.175, 0.05, 0.025, 15, text=current_object.POINTS[3].X))
			TEXTINPUTS_COPY.append(TextInputBox("X4Y", 0.825, 0.175, 0.05, 0.025, 15, text=current_object.POINTS[3].Y))
			TEXTINPUTS_COPY.append(TextInputBox("V4Z", 0.875, 0.175, 0.05, 0.025, 15, text=current_object.POINTS[3].Z))
			TEXTINPUTS_COPY.append(TextInputBox("COL", 0.825, 0.1975, 0.1, 0.025, 15, text=current_object.COLLISION))
			TEXTINPUTS_COPY.append(TextInputBox("TX1", 0.825, 0.22, 0.1, 0.025, 15, text=CONV_TEXTURES(current_object.TEXTURE_INFO)[0]))

			TEXTBOXES_COPY.append([["V1:", 15], 0.725, 0.1, 0.05, 0.025])
			TEXTBOXES_COPY.append([["V2:", 15], 0.725, 0.125, 0.05, 0.025])
			TEXTBOXES_COPY.append([["V3:", 15], 0.725, 0.15, 0.05, 0.025])
			TEXTBOXES_COPY.append([["V4:", 15], 0.725, 0.175, 0.05, 0.025])
			TEXTBOXES_COPY.append([["", 15], 0.725, 0.075, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Collision:", 15], 0.725, 0.1975, 0.1, 0.025])
			TEXTBOXES_COPY.append([["Texture:", 15], 0.725, 0.22, 0.1, 0.025])

		case "TRI":
			TEXTINPUTS_COPY.append(TextInputBox("V1X", 0.775, 0.1, 0.05, 0.025, 15, text=current_object.POINTS[0].X))
			TEXTINPUTS_COPY.append(TextInputBox("V1Y", 0.825, 0.1, 0.05, 0.025, 15, text=current_object.POINTS[0].Y))
			TEXTINPUTS_COPY.append(TextInputBox("V1Z", 0.875, 0.1, 0.05, 0.025, 15, text=current_object.POINTS[0].Z))
			TEXTINPUTS_COPY.append(TextInputBox("V2X", 0.775, 0.125, 0.05, 0.025, 15, text=current_object.POINTS[1].X))
			TEXTINPUTS_COPY.append(TextInputBox("V2Y", 0.825, 0.125, 0.05, 0.025, 15, text=current_object.POINTS[1].Y))
			TEXTINPUTS_COPY.append(TextInputBox("V2Z", 0.875, 0.125, 0.05, 0.025, 15, text=current_object.POINTS[1].Z))
			TEXTINPUTS_COPY.append(TextInputBox("V3X", 0.775, 0.15, 0.05, 0.025, 15, text=current_object.POINTS[2].X))
			TEXTINPUTS_COPY.append(TextInputBox("V3Y", 0.825, 0.15, 0.05, 0.025, 15, text=current_object.POINTS[2].Y))
			TEXTINPUTS_COPY.append(TextInputBox("V3Z", 0.875, 0.15, 0.05, 0.025, 15, text=current_object.POINTS[2].Z))
			TEXTINPUTS_COPY.append(TextInputBox("COL", 0.825, 0.175, 0.1, 0.025, 15, text=current_object.COLLISION))
			TEXTINPUTS_COPY.append(TextInputBox("TX1", 0.825, 0.1975, 0.1, 0.025, 15, text=CONV_TEXTURES(current_object.TEXTURE_INFO)[0]))

			TEXTBOXES_COPY.append([["V1:", 15], 0.725, 0.1, 0.05, 0.025])
			TEXTBOXES_COPY.append([["V2:", 15], 0.725, 0.125, 0.05, 0.025])
			TEXTBOXES_COPY.append([["V3:", 15], 0.725, 0.15, 0.05, 0.025])
			TEXTBOXES_COPY.append([["", 15], 0.725, 0.075, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Collision:", 15], 0.725, 0.175, 0.1, 0.025])
			TEXTBOXES_COPY.append([["Texture:", 15], 0.725, 0.1975, 0.1, 0.025])

		case "SPRITE_STATIC":
			TEXTINPUTS_COPY.append(TextInputBox("V1X", 0.775, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.X))
			TEXTINPUTS_COPY.append(TextInputBox("V1Y", 0.825, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.Y))
			TEXTINPUTS_COPY.append(TextInputBox("V1Z", 0.875, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.Z))
			TEXTINPUTS_COPY.append(TextInputBox("TX1", 0.825, 0.125, 0.1, 0.025, 15, text=CONV_TEXTURES(current_object.TEXTURE_INFO)[0]))

			TEXTBOXES_COPY.append([["Pos:", 15], 0.725, 0.1, 0.05, 0.025])
			TEXTBOXES_COPY.append([["", 15], 0.725, 0.075, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Texture:", 15], 0.725, 0.125, 0.1, 0.025])

		case "ITEM":
			TEXTINPUTS_COPY.append(TextInputBox("V1X", 0.775, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.X))
			TEXTINPUTS_COPY.append(TextInputBox("V1Y", 0.825, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.Y))
			TEXTINPUTS_COPY.append(TextInputBox("V1Z", 0.875, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.Z))
			TEXTINPUTS_COPY.append(TextInputBox("TYP", 0.825, 0.125, 0.1, 0.025, 15, text=current_object.TYPE))
			
			TEXTBOXES_COPY.append([["Pos:", 15], 0.725, 0.1, 0.05, 0.025])
			TEXTBOXES_COPY.append([["", 15], 0.725, 0.075, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Type:", 15], 0.725, 0.125, 0.1, 0.025])

		case "INTERACTABLE":
			TEXTINPUTS_COPY.append(TextInputBox("V1X", 0.775, 0.1, 0.05, 0.025, 15, text=round(current_object.POINTS[0].X, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V1Y", 0.825, 0.1, 0.05, 0.025, 15, text=round(current_object.POINTS[0].Y, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V1Z", 0.875, 0.1, 0.05, 0.025, 15, text=round(current_object.POINTS[0].Z, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V2X", 0.775, 0.125, 0.05, 0.025, 15, text=round(current_object.POINTS[1].X, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V2Y", 0.825, 0.125, 0.05, 0.025, 15, text=round(current_object.POINTS[1].Y, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V2Z", 0.875, 0.125, 0.05, 0.025, 15, text=round(current_object.POINTS[1].Z, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V3X", 0.775, 0.15, 0.05, 0.025, 15, text=round(current_object.POINTS[2].X, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V3Y", 0.825, 0.15, 0.05, 0.025, 15, text=round(current_object.POINTS[2].Y, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V3Z", 0.875, 0.15, 0.05, 0.025, 15, text=round(current_object.POINTS[2].Z, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V4X", 0.775, 0.175, 0.05, 0.025, 15, text=round(current_object.POINTS[3].X, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V4Y", 0.825, 0.175, 0.05, 0.025, 15, text=round(current_object.POINTS[3].Y, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V4Z", 0.875, 0.175, 0.05, 0.025, 15, text=round(current_object.POINTS[3].Z, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("COL", 0.825, 0.1975, 0.1, 0.025, 15, text=current_object.COLLISION))
			TEXTINPUTS_COPY.append(TextInputBox("TX1", 0.825, 0.22, 0.1, 0.025, 15, text=CONV_TEXTURES(current_object.TEXTURE_INFO)[0]))
			TEXTINPUTS_COPY.append(TextInputBox("FLG", 0.825, 0.2425, 0.1, 0.025, 15, text=current_object.FLAG[0]))

			TEXTBOXES_COPY.append([["V1:", 15], 0.725, 0.1, 0.05, 0.025])
			TEXTBOXES_COPY.append([["V2:", 15], 0.725, 0.125, 0.05, 0.025])
			TEXTBOXES_COPY.append([["V3:", 15], 0.725, 0.15, 0.05, 0.025])
			TEXTBOXES_COPY.append([["V4:", 15], 0.725, 0.175, 0.05, 0.025])
			TEXTBOXES_COPY.append([["", 15], 0.725, 0.075, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Collision:", 15], 0.725, 0.1975, 0.1, 0.025])
			TEXTBOXES_COPY.append([["Texture:", 15], 0.725, 0.22, 0.1, 0.025])
			TEXTBOXES_COPY.append([["Flag:", 15], 0.725, 0.2425, 0.1, 0.025])

		case "CUBE_PATH":
			textures = CONV_TEXTURES(current_object.TEXTURE_INFO[0])
			TEXTINPUTS_COPY.append(TextInputBox("V1X", 0.775, 0.1, 0.05, 0.025, 15, text=round(current_object.POSITION.X, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V1Y", 0.825, 0.1, 0.05, 0.025, 15, text=round(current_object.POSITION.Y, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V1Z", 0.875, 0.1, 0.05, 0.025, 15, text=round(current_object.POSITION.Z, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("DMX", 0.775, 0.125, 0.05, 0.025, 15, text=round(current_object.DIMENTIONS.X, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("DMY", 0.825, 0.125, 0.05, 0.025, 15, text=round(current_object.DIMENTIONS.Y, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("DMZ", 0.875, 0.125, 0.05, 0.025, 15, text=round(current_object.DIMENTIONS.Z, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("MVX", 0.775, 0.15, 0.05, 0.025, 15, text=round(current_object.MOVEMENT.X, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("MVY", 0.825, 0.15, 0.05, 0.025, 15, text=round(current_object.MOVEMENT.Y, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("MVZ", 0.875, 0.15, 0.05, 0.025, 15, text=round(current_object.MOVEMENT.Z, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("TX1", 0.775, 0.175, 0.05, 0.025, 15, text=textures[0]))
			TEXTINPUTS_COPY.append(TextInputBox("TX2", 0.825, 0.175, 0.05, 0.025, 15, text=textures[1]))
			TEXTINPUTS_COPY.append(TextInputBox("TX3", 0.875, 0.175, 0.05, 0.025, 15, text=textures[2]))
			TEXTINPUTS_COPY.append(TextInputBox("COL", 0.825, 0.1975, 0.1, 0.025, 15, text=current_object.COLLISION))
			TEXTINPUTS_COPY.append(TextInputBox("SPD", 0.825, 0.22, 0.1, 0.025, 15, text=current_object.SPEED))
			
			TEXTBOXES_COPY.append([["Pos:", 15], 0.725, 0.1, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Dim:", 15], 0.725, 0.125, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Move:", 15], 0.725, 0.15, 0.05, 0.025])
			TEXTBOXES_COPY.append([["", 15], 0.725, 0.075, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Texture:", 15], 0.725, 0.175, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Collision:", 15], 0.725, 0.1975, 0.1, 0.025])
			TEXTBOXES_COPY.append([["Mov. Speed:", 15], 0.725, 0.22, 0.1, 0.025])

		case "ENEMY":
			TEXTINPUTS_COPY.append(TextInputBox("V1X", 0.775, 0.1, 0.05, 0.025, 15, text=round(current_object.POSITION.X, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V1Y", 0.825, 0.1, 0.05, 0.025, 15, text=round(current_object.POSITION.Y, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V1Z", 0.875, 0.1, 0.05, 0.025, 15, text=round(current_object.POSITION.Z, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("RTX", 0.775, 0.125, 0.05, 0.025, 15, text=round(current_object.ROTATION.X, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("RTY", 0.825, 0.125, 0.05, 0.025, 15, text=round(current_object.ROTATION.Y, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("RTZ", 0.875, 0.125, 0.05, 0.025, 15, text=round(current_object.ROTATION.Z, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("TYP", 0.825, 0.15, 0.1, 0.025, 15, text=current_object.TYPE))
			
			TEXTBOXES_COPY.append([["Pos:", 15], 0.725, 0.1, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Dir:", 15], 0.725, 0.125, 0.05, 0.025])
			TEXTBOXES_COPY.append([["", 15], 0.725, 0.075, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Type:", 15], 0.725, 0.15, 0.1, 0.025])

		case "LIGHT":
			TEXTINPUTS_COPY.append(TextInputBox("V1X", 0.775, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.X))
			TEXTINPUTS_COPY.append(TextInputBox("V1Y", 0.825, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.Y))
			TEXTINPUTS_COPY.append(TextInputBox("V1Z", 0.875, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.Z))
			TEXTINPUTS_COPY.append(TextInputBox("LAX", 0.775, 0.125, 0.05, 0.025, 15, text=round(current_object.LOOK_AT.X, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("LAY", 0.825, 0.125, 0.05, 0.025, 15, text=round(current_object.LOOK_AT.Y, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("LAX", 0.875, 0.125, 0.05, 0.025, 15, text=round(current_object.LOOK_AT.Z, 4)))
			TEXTINPUTS_COPY.append(TextInputBox("V3X", 0.775, 0.15, 0.05, 0.025, 15, text=current_object.COLOUR.R))
			TEXTINPUTS_COPY.append(TextInputBox("V3Y", 0.825, 0.15, 0.05, 0.025, 15, text=current_object.COLOUR.G))
			TEXTINPUTS_COPY.append(TextInputBox("V3Z", 0.875, 0.15, 0.05, 0.025, 15, text=current_object.COLOUR.B))
			TEXTINPUTS_COPY.append(TextInputBox("FOV", 0.825, 0.175, 0.1, 0.025, 15, text=current_object.FOV))
			TEXTINPUTS_COPY.append(TextInputBox("DST", 0.825, 0.1975, 0.1, 0.025, 15, text=current_object.MAX_DISTANCE))
			TEXTINPUTS_COPY.append(TextInputBox("INT", 0.825, 0.22, 0.1, 0.025, 15, text=current_object.INTENSITY))
			
			TEXTBOXES_COPY.append([["Pos:", 15], 0.725, 0.1, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Look-at:", 15], 0.725, 0.125, 0.05, 0.025])
			TEXTBOXES_COPY.append([["RGB:", 15], 0.725, 0.15, 0.05, 0.025])
			TEXTBOXES_COPY.append([["", 15], 0.725, 0.075, 0.05, 0.025])
			TEXTBOXES_COPY.append([["FOV:", 15], 0.725, 0.175, 0.1, 0.025])
			TEXTBOXES_COPY.append([["MaxDist:", 15], 0.725, 0.1975, 0.1, 0.025])
			TEXTBOXES_COPY.append([["Intensity:", 15], 0.725, 0.22, 0.1, 0.025])

		case "NPC_PATH_NODE":
			TEXTINPUTS_COPY.append(TextInputBox("V1X", 0.775, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.X))
			TEXTINPUTS_COPY.append(TextInputBox("V1Y", 0.825, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.Y))
			TEXTINPUTS_COPY.append(TextInputBox("V1Z", 0.875, 0.1, 0.05, 0.025, 15, text=current_object.POSITION.Z))
			TEXTINPUTS_COPY.append(TextInputBox("FLG", 0.825, 0.125, 0.1, 0.025, 15, text=current_object.FLAG[2:].upper()))

			
			TEXTBOXES_COPY.append([["Pos:", 15], 0.725, 0.1, 0.05, 0.025])
			TEXTBOXES_COPY.append([["", 15], 0.725, 0.075, 0.05, 0.025])
			TEXTBOXES_COPY.append([["Flag:", 15], 0.725, 0.125, 0.1, 0.025])
			TEXTBOXES_COPY.append([["Node Connections:", 15], 0.725, 0.15, 0.2, 0.025])
		
			DROPDOWNS_COPY.append([0.725, 0.175, 0.05, 0.025, 2, "Node0", "Placeholder", False])
			DROPDOWNS_COPY.append([0.775, 0.175, 0.05, 0.025, 2, "Node1", "Placeholder", False])
			DROPDOWNS_COPY.append([0.825, 0.175, 0.05, 0.025, 2, "Node2", "Placeholder", False])
			DROPDOWNS_COPY.append([0.875, 0.175, 0.05, 0.025, 2, "Node3", "Placeholder", False])
			DROPDOWNS_COPY.append([0.725, 0.2, 0.05, 0.025, 2, "Node4", "Placeholder", False])
			DROPDOWNS_COPY.append([0.775, 0.2, 0.05, 0.025, 2, "Node5", "Placeholder", False])
			DROPDOWNS_COPY.append([0.825, 0.2, 0.05, 0.025, 2, "Node6", "Placeholder", False])
			DROPDOWNS_COPY.append([0.875, 0.2, 0.05, 0.025, 2, "Node7", "Placeholder", False])

	return TEXTINPUTS_COPY, TEXTBOXES_COPY, DROPDOWNS_COPY


def REFORMAT(OBJECT, DATA_3D):
	object_type = type(OBJECT)
	if object_type in (PLAYER, NPC_PATH_NODE):
		return DATA_3D
	lines_list = []
	if object_type in (CUBE_STATIC, CUBE_PHYSICS):
		pts = OBJECT.POINTS
		centres = (
			utils.FIND_CENTROID((pts[0], pts[1], pts[2], pts[3])),
			utils.FIND_CENTROID((pts[0], pts[1], pts[4], pts[6])),
			utils.FIND_CENTROID((pts[0], pts[1], pts[4], pts[5])),
			utils.FIND_CENTROID((pts[1], pts[3], pts[7], pts[5])),
			utils.FIND_CENTROID((pts[2], pts[3], pts[6], pts[7])),
			utils.FIND_CENTROID((pts[4], pts[5], pts[6], pts[7]))
		)
		lines_list = [ #E == Edge
			("E", (pts[0] * scale) + offset, (pts[1] * scale) + offset),
			("E", (pts[0] * scale) + offset, (pts[2] * scale) + offset),
			("E", (pts[0] * scale) + offset, (pts[3] * scale) + offset),
			("E", (pts[0] * scale) + offset, (pts[4] * scale) + offset),
			("E", (pts[1] * scale) + offset, (pts[3] * scale) + offset),
			("E", (pts[1] * scale) + offset, (pts[5] * scale) + offset),
			("E", (pts[1] * scale) + offset, (pts[4] * scale) + offset),
			("E", (pts[1] * scale) + offset, (pts[7] * scale) + offset),
			("E", (pts[2] * scale) + offset, (pts[3] * scale) + offset),
			("E", (pts[2] * scale) + offset, (pts[6] * scale) + offset),
			("E", (pts[3] * scale) + offset, (pts[6] * scale) + offset),
			("E", (pts[3] * scale) + offset, (pts[7] * scale) + offset),
			("E", (pts[4] * scale) + offset, (pts[5] * scale) + offset),
			("E", (pts[4] * scale) + offset, (pts[6] * scale) + offset),
			("E", (pts[4] * scale) + offset, (pts[7] * scale) + offset),
			("E", (pts[5] * scale) + offset, (pts[7] * scale) + offset),
			("E", (pts[6] * scale) + offset, (pts[7] * scale) + offset)
		]

		if OBJECT.COLLISION:
			for centre, norm in zip(centres, OBJECT.NORMALS):
				normal_end = centre + norm
				lines_list.append(("P", ((centre) * scale) + offset, ((centre) * scale) + offset))
				lines_list.append(("N", ((centre) * scale) + offset, ((normal_end) * scale) + offset)) #N == Normal


	elif object_type in (QUAD, INTERACTABLE):
		pts = OBJECT.POINTS
		lines_list =[ 
			("E", (pts[0] * scale) + offset, (pts[1] * scale) + offset),
			("E", (pts[1] * scale) + offset, (pts[2] * scale) + offset),
			("E", (pts[2] * scale) + offset, (pts[3] * scale) + offset),
			("E", (pts[3] * scale) + offset, (pts[0] * scale) + offset),
			("E", (pts[0] * scale) + offset, (pts[2] * scale) + offset)
		]
		
		if OBJECT.COLLISION:
			tri_1_centre = utils.FIND_CENTROID((pts[0], pts[1], pts[2]))
			tri_2_centre = utils.FIND_CENTROID((pts[0], pts[3], pts[2]))
			lines_list.append(("P", ((tri_1_centre) * scale) + offset, ((tri_1_centre) * scale) + offset))
			lines_list.append(("N", ((tri_1_centre) * scale) + offset, ((tri_1_centre + OBJECT.NORMALS[0]) * scale) + offset))
			lines_list.append(("P", ((tri_2_centre) * scale) + offset, ((tri_2_centre) * scale) + offset))
			lines_list.append(("N", ((tri_2_centre) * scale) + offset, ((tri_2_centre + OBJECT.NORMALS[1]) * scale) + offset))

	elif object_type in (TRI,):
		pts = OBJECT.POINTS
		lines_list = [
			("E", (pts[0] * scale) + offset, (pts[1] * scale) + offset),
			("E", (pts[1] * scale) + offset, (pts[2] * scale) + offset),
			("E", (pts[2] * scale) + offset, (pts[0] * scale) + offset),
		]

		if OBJECT.COLLISION:
			tri_centre = utils.FIND_CENTROID((pts[0], pts[1], pts[2]))
			lines_list.append(("P", ((tri_centre) * scale) + offset, ((tri_centre) * scale) + offset))
			lines_list.append(("N", ((tri_centre) * scale) + offset, ((tri_centre + OBJECT.NORMALS[0]) * scale) + offset))

	DATA_3D.extend(lines_list)
	return DATA_3D

def TO_VECTOR_3D(numpy):
	return VECTOR_3D(numpy[0], numpy[1], numpy[2])

def align_parts(DISPLAY_RESOLUTION):
	VIEWPORTS = {
		'XZ (A/D, W/S)': PG.Rect(DISPLAY_RESOLUTION.X*0.01, DISPLAY_RESOLUTION.Y*0.01, DISPLAY_RESOLUTION.X*0.6375, DISPLAY_RESOLUTION.Y*0.5),
		'XY (A/D, E/Q)': PG.Rect(DISPLAY_RESOLUTION.X*0.01, DISPLAY_RESOLUTION.Y*0.55, DISPLAY_RESOLUTION.X*0.3, DISPLAY_RESOLUTION.Y*0.3),
		'ZY (W/S, E/Q)': PG.Rect(DISPLAY_RESOLUTION.X*0.35, DISPLAY_RESOLUTION.Y*0.55, DISPLAY_RESOLUTION.X*0.3, DISPLAY_RESOLUTION.Y*0.3)
	}

	BUTTONS = {
		"Previous": (0.725, 0.025, 0.05, 0.025, True),
		"Next": (0.875, 0.025, 0.05, 0.025, True),
	}

	TYPE_LIST = ["PLAYER", "CUBE_STATIC", "QUAD", "TRI", "SPRITE_STATIC", "ITEM", "TRIGGER", "INTERACTABLE", "CUBE_PATH", "ENEMY", "CUBE_PHYSICS", "LIGHT", "NPC_PATH_NODE"]

	DROPDOWNS = [
		[0.725, 0.5, 0.125, 0.025, 5, TYPE_LIST[0], TYPE_LIST, False]
	]

	TEXTBOXES = [
		[["ID:", 15], 0.765, 0.025, 0.125, 0.025],
		[["", 15], 0.725, 0.05, 0.2, 0.025],
		[["", 22], 0.01, 0.925, 0.6375, 0.0375],
		[["X Axis", 15], 0.775, 0.075, 0.05, 0.025],
		[["Y Axis", 15], 0.825, 0.075, 0.05, 0.025],
		[["Z Axis", 15], 0.875, 0.075, 0.05, 0.025],
	]

	TEXTINPUTS = [
	]

	return VIEWPORTS, BUTTONS, DROPDOWNS, TEXTINPUTS, TEXTBOXES

def draw_text(screen, text, position, fontsize, colour=(255, 255, 255)):
	font = PG.font.SysFont('Arial', fontsize)
	text_surface = font.render(str(text), True, colour)
	screen.blit(text_surface, position)

class TextInputBox:
	def __init__(self, name, x, y, w, h, fontsize, text=""):
		self.position = VECTOR_2D(DISPLAY_RESOLUTION.X * x, DISPLAY_RESOLUTION.Y * y)
		self.dimentions = VECTOR_2D(DISPLAY_RESOLUTION.X * w, DISPLAY_RESOLUTION.Y * h)
		self.colour_inactive = (175, 175, 175)
		self.colour_active = (225, 225, 225)
		self.colour = self.colour_inactive
		self.text = str(text)
		self.name = str(name)
		self.fontsize = fontsize
		self.active = False

	def handle_event(self, event, screen):
		if event.type == PG.MOUSEBUTTONDOWN:
			if IS_IN_RECTANGLE(VECTOR_2D(event.pos[0], event.pos[1]), (self.position.X, self.position.Y, self.dimentions.X, self.dimentions.Y)):
				self.active = not self.active
				self.colour = self.colour_active
			else:
				self.active = False
				self.colour = self.colour_inactive

		if event.type == PG.KEYDOWN:
			if self.active:
				if event.key == PG.K_RETURN:
					value_list[self.name] = self.text
				elif event.key == PG.K_BACKSPACE:
					self.text = self.text[:-1]
					value_list[self.name] = None
				else:
					self.text += event.unicode
					value_list[self.name] = None
				self.draw(screen)

	def draw(self, screen):
		rect = PG.Rect(self.position.X, self.position.Y, self.dimentions.X, self.dimentions.Y)
		PG.draw.rect(screen, self.colour, rect)
		PG.draw.rect(screen, (200, 200, 200), rect, 2)
		draw_text(screen, self.text, (self.position.X + 2, self.position.Y), self.fontsize, colour=(0, 0, 0))

def CONV_TEXTURES(textures):
	if type(textures) in (tuple, list):
		out = []
		for tx in textures:
			out.append((str(hex(round((1 - tx[3].Y) * 16)))[2:] + str(hex(round(tx[0].X * 16)))[2:]).upper())

	else:
		out = (str(hex(round((1 - tx[3].Y) * 16)))[2:] + str(hex(round(tx[0].X * 16)))[2:]).upper()

	return out


if __name__ == "__main__":
	_, CONSTANTS = utils.GET_CONFIGS()
	CONSTANTS["FPS_CAP"] = 60
	CONSTANTS["BG_FPS"] = 15
	print("\n\nCurrent user configs;")
	for OPTION in CONSTANTS:
		print(f"{OPTION}: {CONSTANTS[OPTION]}")
	print("\n")

	DISPLAY_RESOLUTION = VECTOR_2D(1280, 720)

	CLOCK = PG.time.Clock()
	PG.font.init()
	PG.init()
	SCREEN = PG.display.set_mode(DISPLAY_RESOLUTION.TO_LIST(), RESIZABLE)
	PG.display.set_caption("test4//src//scene-creator.py")
	PG.display.set_icon(PG.image.load("imgs/editor.ico"))

	FILE_DATA = scene.LOAD_FILE("test")[0]
	RENDER_DATASET = FILE_DATA[0]
	LIGHTS = FILE_DATA[2]

	type_list = {
		SCENE: "SCENE",
		CUBE_STATIC: "CUBE_STATIC",
		QUAD: "QUAD",
		TRI: "TRI",
		SPRITE_STATIC: "SPRITE_STATIC",
		CUBE_PATH: "CUBE_PATH",
		TRIGGER: "TRIGGER",
		INTERACTABLE: "INTERACTABLE",
		LIGHT: "LIGHT",
		NPC_PATH_NODE: "NPC_PATH_NODE",
		CUBE_PHYSICS: "CUBE_PHYSICS",
		ITEM: "ITEM",
		ENEMY: "ENEMY",
		PLAYER: "PLAYER"
	}

	VIEWPORTS, BUTTONS, DROPDOWNS, TEXTINPUTS, TEXTBOXES = align_parts(DISPLAY_RESOLUTION)
	KEY_STATES = {PG.K_w: False, PG.K_a: False, PG.K_s: False, PG.K_d: False, PG.K_e: False, PG.K_q: False, PG.K_LSHIFT: False}

	object_id = 0
	current_object = RENDER_DATASET[object_id]
	object_type = type(current_object)
	TEXTBOXES[0][0][0] = f"ID: {object_id}"
	type_name = type_list[object_type]
	TEXTBOXES[1][0][0] = type_name
	TEXTINPUTS_COPY, TEXTBOXES_COPY, DROPDOWNS_COPY = LOAD_BOXES(TEXTINPUTS, TEXTBOXES, DROPDOWNS, type_name)

	value_list = {
		"V1X": None, "V1Y": None, "V1Z": None,
		"V2X": None, "V2Y": None, "V2Z": None,
		"V3X": None, "V3Y": None, "V3Z": None,
		"V4X": None, "V4Y": None, "V4Z": None,
		"TX1": None, "TX2": None, "TX3": None,
		"RTX": None, "RTY": None, "RTZ": None,
		"LAX": None, "LAY": None, "LAZ": None,
		"MVX": None, "MVY": None, "MVZ": None,
		"DMX": None, "DMY": None, "DMZ": None,
		"COL": None,
		"FLG": None,
		"DST": None,
		"FOV": None,
		"DST": None,
		"INT": None,
		"SPD": None
	}

	WINDOW_FOCUS = 0
	previous_press = False
	RUN = True
	while RUN:
		in_box = False
		for EVENT in PG.event.get():
			match EVENT.type:
				case PG.QUIT:
					RUN = False

				case PG.MOUSEWHEEL:
					if EVENT.y > 0:
						scale = CLAMP(scale * 1.1, 0.51, 1000)
					elif EVENT.y < 0:
						scale = CLAMP(scale / 1.1, 0.51, 1000)

				case PG.ACTIVEEVENT:
					if EVENT.state == 2:
						WINDOW_FOCUS = EVENT.gain

				case PG.KEYDOWN:
					if EVENT.key in KEY_STATES:
						KEY_STATES[EVENT.key] = True

					match EVENT.key:
						case PG.K_ESCAPE:
							RUN = False



				case PG.KEYUP:
					if EVENT.key in KEY_STATES:
						KEY_STATES[EVENT.key] = False

				case PG.VIDEORESIZE:
					DISPLAY_RESOLUTION = VECTOR_2D(EVENT.w, EVENT.h)
					SCREEN = PG.display.set_mode(DISPLAY_RESOLUTION.TO_LIST(), RESIZABLE)
					VIEWPORTS, BUTTONS, TEXTINPUTS, TEXTBOXES = align_parts(DISPLAY_RESOLUTION)
					DATA_2D = CONVERT_TO_2D(DATA_3D)

				case PG.MOUSEBUTTONDOWN:
					CURSOR_POSITION = VECTOR_2D(PG.mouse.get_pos()[0], PG.mouse.get_pos()[1])
					for button_name, button_data in BUTTONS.items():
						if IS_IN_RECTANGLE(CURSOR_POSITION, (button_data[0]*DISPLAY_RESOLUTION.X, button_data[1]*DISPLAY_RESOLUTION.Y, button_data[2]*DISPLAY_RESOLUTION.X, button_data[3]*DISPLAY_RESOLUTION.Y)) and PG.mouse.get_pressed()[0]:
							if button_name == "Next" and object_id < len(RENDER_DATASET) -1:
								object_id += 1
							elif button_name == "Previous" and object_id > 0:
								object_id -= 1
							
							VIEWPORTS, BUTTONS, DROPDOWNS, TEXTINPUTS, TEXTBOXES = align_parts(DISPLAY_RESOLUTION)
							current_object = RENDER_DATASET[object_id]
							object_type = type(current_object)
							TEXTBOXES[0][0][0] = f"ID: {object_id}"
							type_name = type_list[object_type]
							TEXTBOXES[1][0][0] = type_name

							TEXTINPUTS_COPY, TEXTBOXES_COPY, DROPDOWNS_COPY = LOAD_BOXES(TEXTINPUTS, TEXTBOXES, DROPDOWNS, type_name)

			for box in TEXTINPUTS_COPY:
				box.handle_event(EVENT, SCREEN)

		if WINDOW_FOCUS != 1:
			CLOCK.tick(CONSTANTS["BG_FPS"])
			continue

		CLOCK.tick(CONSTANTS["FPS_CAP"])
		FPS = utils.CLAMP(CLOCK.get_fps(), 0, CONSTANTS["FPS_CAP"])
		#print(FPS)


		CURSOR_POSITION = VECTOR_2D(PG.mouse.get_pos()[0], PG.mouse.get_pos()[1])
		CURSOR_INPUT = PG.mouse.get_pressed()


		if not in_box:
			final_scroll_speed = 2 if KEY_STATES[PG.K_LSHIFT] else 1
			X = VECTOR_3D(final_scroll_speed, 0, 0)
			Y = VECTOR_3D(0, final_scroll_speed, 0)
			Z = VECTOR_3D(0, 0, final_scroll_speed)
			if KEY_STATES[PG.K_w]:
				offset += Z
			if KEY_STATES[PG.K_s]:
				offset -= Z
			if KEY_STATES[PG.K_a]:
				offset += X
			if KEY_STATES[PG.K_d]:
				offset -= X
			if KEY_STATES[PG.K_e]:
				offset -= Y
			if KEY_STATES[PG.K_q]:
				offset += Y

		DATA_3D = []
		for OBJECT in RENDER_DATASET:
			DATA_3D = REFORMAT(OBJECT, DATA_3D)

		DATA_2D = CONVERT_TO_2D(DATA_3D)

		for light in LIGHTS:
			light_lines = calculate_frustum_lines(light)
			DATA_2D.extend(CONVERT_TO_2D(light_lines))

		SCREEN.fill((50, 50, 50))  # Clear the screen with a gray background

		# Draw the viewports
		fontsize = 20  # round((DISPLAY_RESOLUTION.X + DISPLAY_RESOLUTION.Y) / 2)*15
		for viewport_name, rect in VIEWPORTS.items():
			draw_text(SCREEN, viewport_name, ((rect[0] + (0.5 * rect[2]) - (0.25 * len(viewport_name) * fontsize)), (rect[1] + rect[3] + (0.25 * fontsize))), fontsize)
			draw_grid(SCREEN, rect, viewport_name)  # Draw the grid
			draw_lines(SCREEN, DATA_2D, rect, viewport_name)  # Draw the lines
			PG.draw.rect(SCREEN, (200, 200, 200), rect, 2)  # Draw the border

		PG.draw.rect(SCREEN, (128, 128, 128), PG.Rect(DISPLAY_RESOLUTION.X * 0.675, DISPLAY_RESOLUTION.Y * 0.01, DISPLAY_RESOLUTION.X * 0.32, DISPLAY_RESOLUTION.Y * 0.95,))
		PG.draw.rect(SCREEN, (200, 200, 200), PG.Rect(DISPLAY_RESOLUTION.X * 0.675, DISPLAY_RESOLUTION.Y * 0.01, DISPLAY_RESOLUTION.X * 0.32, DISPLAY_RESOLUTION.Y * 0.95,), 5)  # Draw the border

		fontsize = 15
		for box in TEXTINPUTS_COPY:
			box.draw(SCREEN)

		for name, value in value_list.items():
			if value is not None:
				try:
					match name:
						case "V1X":
							if type_name not in [QUAD, TRI, INTERACTABLE]:
								current_object.POSITION.X = float(value)
							else:
								current_object.POINTS[0].X = float(value)
						case "V1Y":
							if type_name not in [QUAD, TRI, INTERACTABLE]:
								current_object.POSITION.Y = float(value)
							else:
								current_object.POINTS[0].Y = float(value)
						case "V1Z":
							if type_name not in [QUAD, TRI, INTERACTABLE]:
								current_object.POSITION.Z = float(value)
							else:
								current_object.POINTS[0].Z = float(value)
						case "V2X":
							current_object.POINTS[1].X = float(value)
						case "V2Y":
							current_object.POINTS[1].Y = float(value)
						case "V2Z":
							current_object.POINTS[1].Z = float(value)
						case "V3X":
							current_object.POINTS[2].X = float(value)
						case "V3Y":
							current_object.POINTS[2].Y = float(value)
						case "V3Z":
							current_object.POINTS[2].Z = float(value)
						case "V4X":
							current_object.POINTS[3].X = float(value)
						case "V4Y":
							current_object.POINTS[3].Y = float(value)
						case "V4Z":
							current_object.POINTS[3].Z = float(value)
						case "DMX":
							current_object.DIMENTIONS.X = float(value)
						case "DMY":
							current_object.DIMENTIONS.Y = float(value)
						case "DMZ":
							current_object.DIMENTIONS.Z = float(value)
						case "RTX":
							current_object.ROTATION.X = float(value)
						case "RTY":
							current_object.ROTATION.Y = float(value)
						case "RTZ":
							current_object.ROTATION.Z = float(value)
						case "TX1":
							current_object.TEXTURE_DATA[0] = str(value)
						case "TX2":
							current_object.TEXTURE_DATA[1] = str(value)
						case "TX3":
							current_object.TEXTURE_DATA[2] = str(value)
						case "COL":
							current_object.COLLISION = bool(value)
						case "FLG":
							current_object.FLAG = str(value)
						case "DST":
							current_object.MAX_DISTANCE = float(value)
						case "LAX":
							current_object.ROTATION.X = float(value)
						case "LTY":
							current_object.ROTATION.Y = float(value)
						case "LTZ":
							current_object.ROTATION.Z = float(value)
				except ValueError as E:
					TEXTBOXES_COPY[2][0][0] = f"Exception: {E}"


		for textbox in TEXTBOXES_COPY:
			if textbox[0][0][:11] == "Exception: ": colour = (200, 0, 0)
			else: colour = (255, 255, 255)
			PG.draw.rect(SCREEN, (128, 128, 128), PG.Rect(DISPLAY_RESOLUTION.X * textbox[1], DISPLAY_RESOLUTION.Y * textbox[2], DISPLAY_RESOLUTION.X * textbox[3], DISPLAY_RESOLUTION.Y * textbox[4]))
			PG.draw.rect(SCREEN, (200, 200, 200), PG.Rect(DISPLAY_RESOLUTION.X * textbox[1], DISPLAY_RESOLUTION.Y * textbox[2], DISPLAY_RESOLUTION.X * textbox[3], DISPLAY_RESOLUTION.Y * textbox[4]), 2)
			draw_text(SCREEN, textbox[0][0], (((textbox[1] * DISPLAY_RESOLUTION.X) + (0.5 * (textbox[3] * DISPLAY_RESOLUTION.X))) - (0.25 * len(textbox[0][0]) * textbox[0][1]), (textbox[2] * DISPLAY_RESOLUTION.Y)), textbox[0][1], colour=colour)

		fontsize = 15
		for button_name, button_data in BUTTONS.items():
			pg_rect = PG.Rect(DISPLAY_RESOLUTION.X * button_data[0], DISPLAY_RESOLUTION.Y * button_data[1], DISPLAY_RESOLUTION.X * button_data[2], DISPLAY_RESOLUTION.Y * button_data[3])
			button_colour = (128, 128, 128)
			if IS_IN_RECTANGLE(CURSOR_POSITION, (button_data[0]*DISPLAY_RESOLUTION.X, button_data[1]*DISPLAY_RESOLUTION.Y, button_data[2]*DISPLAY_RESOLUTION.X, button_data[3]*DISPLAY_RESOLUTION.Y)) and CURSOR_INPUT[0]:
				button_colour = (200, 200, 200)
			PG.draw.rect(SCREEN, button_colour, pg_rect)
			PG.draw.rect(SCREEN, (200, 200, 200), pg_rect, 2)
			draw_text(SCREEN, button_name, (((button_data[0] * DISPLAY_RESOLUTION.X) + (0.5 * (button_data[2] * DISPLAY_RESOLUTION.X))) - (0.25 * len(button_name) * fontsize), (button_data[1] * DISPLAY_RESOLUTION.Y)), fontsize)

		for ID, dropdown_data in enumerate(DROPDOWNS_COPY):
			dropdown_name = dropdown_data[-3]
			pg_rect = PG.Rect(DISPLAY_RESOLUTION.X * dropdown_data[0], DISPLAY_RESOLUTION.Y * dropdown_data[1], DISPLAY_RESOLUTION.X * dropdown_data[2], DISPLAY_RESOLUTION.Y * dropdown_data[3])
			dropdown_colour = (128, 128, 128)
			if CURSOR_INPUT[0]: #Somehow selecting an option from the dropdown with LMB, while this is ALSO LMB, means the option is not selected. How? I dont know.
				if IS_IN_RECTANGLE(CURSOR_POSITION, (dropdown_data[0] * DISPLAY_RESOLUTION.X, dropdown_data[1] * DISPLAY_RESOLUTION.Y, dropdown_data[2] * DISPLAY_RESOLUTION.X, dropdown_data[3] * DISPLAY_RESOLUTION.Y)):
					dropdown_colour = (200, 200, 200)
					DROPDOWNS_COPY[ID][-1] = True
					previous_press = True
				else:
					previous_press = False
					DROPDOWNS_COPY[ID][-1] = False
			PG.draw.rect(SCREEN, dropdown_colour, pg_rect)
			PG.draw.rect(SCREEN, (200, 200, 200), pg_rect, 2)
			draw_text(SCREEN, dropdown_name, (((dropdown_data[0] * DISPLAY_RESOLUTION.X) + (0.5 * (dropdown_data[2] * DISPLAY_RESOLUTION.X))) - (dropdown_data[-4] * fontsize), (dropdown_data[1] * DISPLAY_RESOLUTION.Y)), fontsize)

		for ID, dropdown_data in enumerate(DROPDOWNS_COPY):
			dropdown_name = dropdown_data[-3]
			if DROPDOWNS_COPY[ID][-1]:
				for I, item in enumerate(dropdown_data[-2]):
					if IS_IN_RECTANGLE(CURSOR_POSITION, (dropdown_data[0] * DISPLAY_RESOLUTION.X, ((I + 1) * 15) + (dropdown_data[1] * DISPLAY_RESOLUTION.Y), dropdown_data[2] * DISPLAY_RESOLUTION.X, dropdown_data[3] * DISPLAY_RESOLUTION.Y)):
						item_colour = (200, 200, 200)
						if PG.mouse.get_pressed()[0]:
							dropdown_data[-1] = False
							dropdown_data[-3] = item
							DROPDOWNS_COPY[ID] = dropdown_data
					else:
						item_colour = (164, 164, 164)
					item_rect = PG.Rect(DISPLAY_RESOLUTION.X * dropdown_data[0], ((I + 1) * 15) + (DISPLAY_RESOLUTION.Y * dropdown_data[1]), DISPLAY_RESOLUTION.X * dropdown_data[2], DISPLAY_RESOLUTION.Y * dropdown_data[3])
					PG.draw.rect(SCREEN, item_colour, item_rect)
					PG.draw.rect(SCREEN, (200, 200, 200), item_rect, 2)
					draw_text(SCREEN, item, (((dropdown_data[0] * DISPLAY_RESOLUTION.X) + (0.5 * (dropdown_data[2] * DISPLAY_RESOLUTION.X))) - (dropdown_data[-4] * fontsize), ((I + 1) * 15) + (dropdown_data[1] * DISPLAY_RESOLUTION.Y)), fontsize)


		PG.display.flip()

	PG.quit()
	quit()

