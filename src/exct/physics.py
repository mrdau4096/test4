"""
[physics.py]
Controls the physics of the game, such as gravity and collisions.
Basic systems, not too complex for performance and ease-of-use reasons.

______________________
Importing other sub-files;
-render.py
-physics.py
-texture_load.py
-load_scene.py
-log.py
-utils.py
"""

from exct import log
try:
	#Importing base python modules
	import sys, os
	import math as maths
	import numpy as NP
	from pyrr import Matrix44, Vector3, Vector4
	
	os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

	sys.path.extend(("src", r"src\exct\data", r"src\exct\glsl"))
	import pygame as PG
	from pygame import time, joystick, display, image

	#Import other sub-files.
	from exct import log, utils, render, pathfinding
	from scenes import scene
	from exct.utils import *

except ImportError:
	log.ERROR("physics.py", "Initial imports failed.")


log.REPORT_IMPORT("physics.py")
PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS



#General Physics Functions


def ACCELERATION_CALC(FORCE, MASS):
	"""
	F = ma
	Therefore a = F/m
	If Mass == 0 or Force == 0, then it will raise a zero-div-error.
	I account for this via presuming a "safe" return value is 0us^-2.
	"""
	try:
		return FORCE/MASS

	except ZeroDivisionError:
		return 0



def PLAYER_MOVEMENT(KEY_STATES, PLAYER):
	#Calculates player movement based on either keyboard or GamePad inputs.
	FINAL_MOVE_SPEED = CONSTANTS["PLAYER_SPEED_MOVE"]

	if KEY_STATES[PG.K_LCTRL]:
		#Crouching slows you down.
		FINAL_MOVE_SPEED *= CONSTANTS["MULT_CROUCH"]

	if KEY_STATES[PG.K_LSHIFT]:
		#Sprinting speeds you up.
		FINAL_MOVE_SPEED *= CONSTANTS["MULT_RUN"]

	elif KEY_STATES[PG.K_x]:
		#"Slow-walk" also slows you.
		FINAL_MOVE_SPEED *= CONSTANTS["MULT_SLOWWALK"]

	#Scale down the movement speed by how many physics iterations per frame there are.
	FINAL_MOVE_SPEED /= CONSTANTS["PHYSICS_ITERATIONS"]

	X_RADIANS = maths.radians(PLAYER.ROTATION.X)

	#Forward and left movement vectors.
	FORWARD = VECTOR_3D(
		-maths.cos(X_RADIANS),
		0,
		-maths.sin(X_RADIANS)
	).NORMALISE()
	
	LEFT = VECTOR_3D(
		maths.sin(X_RADIANS),
		0,
		-maths.cos(X_RADIANS)
	).NORMALISE()

	#Keyboard input affecting movement.
	if KEY_STATES[PG.K_w]:
		PLAYER.POSITION += FORWARD * FINAL_MOVE_SPEED
	if KEY_STATES[PG.K_s]:
		PLAYER.POSITION -= FORWARD * FINAL_MOVE_SPEED
	if KEY_STATES[PG.K_a]:
		PLAYER.POSITION += LEFT * -FINAL_MOVE_SPEED
	if KEY_STATES[PG.K_d]:
		PLAYER.POSITION -= LEFT * -FINAL_MOVE_SPEED


	#Return updated player data.
	return PLAYER



def UPDATE_PHYSICS(PHYS_DATA, FPS, KEY_STATES, FLAG_STATES):
	#Updates the physics with as many iterations as CONSTANTS["PHYSICS_ITERATIONS"] defines.
	#try:
		KINETICs_LIST, STATICs_LIST = PHYS_DATA
		REMOVED_OBJECTS = []

		for _ in range(CONSTANTS["PHYSICS_ITERATIONS"]):
			for PHYS_OBJECT_ID, PHYS_OBJECT in KINETICs_LIST.items():
				#Check every physics object (PLAYER, CUBE_PHYSICS, etc.)
				OBJECT_TYPE = type(PHYS_OBJECT)

				if PHYS_OBJECT_ID in REMOVED_OBJECTS:
					continue

				if OBJECT_TYPE == PROJECTILE:
					PHYS_OBJECT.LIFETIME += 1
					if PHYS_OBJECT.LIFETIME >= CONSTANTS["MAX_PROJECTILE_LIFESPAN"]:
						REMOVED_OBJECTS.append(PHYS_OBJECT_ID)
						continue

				elif OBJECT_TYPE == ENEMY:
					MOVEMENT_DIRECTION = (PHYS_OBJECT.TARGET.POSITION - PHYS_OBJECT.POSITION)
					if abs(MOVEMENT_DIRECTION) > CONSTANTS["PATHFINDING_THRESHOLD"]:
						MOVEMENT_VECTOR = MOVEMENT_DIRECTION.NORMALISE() * (PHYS_OBJECT.SPEED / CONSTANTS["PHYSICS_ITERATIONS"])
						PHYS_OBJECT.POSITION += MOVEMENT_VECTOR
			
						MOVEMENT_DIRECTION = MOVEMENT_DIRECTION.NORMALISE()
						YAW = maths.atan2(MOVEMENT_DIRECTION.X, MOVEMENT_DIRECTION.Z)
						
						PHYS_OBJECT.ROTATION = VECTOR_3D(YAW, 0.0, 0.0).DEGREES()



				if OBJECT_TYPE == CUBE_PATH:
					#CUBE_PATH has to be treated seperately, as it has its own unique physics requirements.
					#This will move the cube if its flag-state is true, handled within the utils.py class attribute ADVANCE().
					PHYS_OBJECT.ADVANCE(FLAG_STATES)

				else:
					#Any other physics object.
					COLLIDING, DISPLACEMENT_VECTOR, TOUCHING = False, VECTOR_3D(0, 0, 0), False

						
					if OBJECT_TYPE == PLAYER:
						#If player, apply movement first.
						PHYS_OBJECT = PLAYER_MOVEMENT(KEY_STATES, PHYS_OBJECT)
						PHYS_OBJECT.POINTS = utils.FIND_CUBOID_POINTS(PHYS_OBJECT.DIMENTIONS, PHYS_OBJECT.POSITION)


					#Collisions between physics-bodies (not with itself, hence the comparing of IDs)
					for BODY_ID, BODY in KINETICs_LIST.items():
						if BODY_ID != PHYS_OBJECT_ID: #Stops self collisions.
							BODY_TYPE = type(BODY)
							if BOUNDING_BOX_COLLISION(PHYS_OBJECT.BOUNDING_BOX, BODY.BOUNDING_BOX): #Axis-aligned bounding-box collision check for computational efficiency
								COLLISION_DATA = COLLISION_CHECK(PHYS_OBJECT, BODY)
								if COLLISION_DATA[2]:
									TOUCHING = True

								if COLLISION_DATA[0]:
									COLLIDING = True
									DISPLACEMENT = COLLISION_DATA[1]
									DISPLACEMENT.Y = 0.0


									if OBJECT_TYPE == PROJECTILE:
										if BODY.ID != PHYS_OBJECT.OWNER and not PHYS_OBJECT.CREATE_EXPLOSION:
											REMOVED_OBJECTS.append(PHYS_OBJECT_ID)
											if BODY_TYPE in (PLAYER, ENEMY,):
												BODY.HURT(PHYS_OBJECT.DAMAGE_STRENGH)
											continue
									
									elif BODY_TYPE == PROJECTILE:
										if PHYS_OBJECT.ID != BODY.OWNER and not BODY.CREATE_EXPLOSION:
											REMOVED_OBJECTS.append(BODY.ID)
											if BODY_TYPE in (PLAYER, ENEMY,):
												PHYS_OBJECT.HURT(BODY.DAMAGE_STRENGH)
											continue

									else:
										#Moves each proportional to their mass (i.e. pushing)
										#If the BODY is a CUBE_PATH, do not push. CUBE_PATH has unique requirements and cannot be pushed by another phys object.
										PHYS_OBJECT_PROPORTION = (BODY.MASS / (PHYS_OBJECT.MASS + BODY.MASS)) if (BODY_TYPE != CUBE_PATH) else 1.0
										BODY_PROPORTION = (PHYS_OBJECT.MASS / (PHYS_OBJECT.MASS + BODY.MASS)) if (BODY_TYPE != CUBE_PATH) else 0.0


										DISPLACEMENT_VECTOR += DISPLACEMENT * PHYS_OBJECT_PROPORTION
										BODY.POSITION -= DISPLACEMENT * BODY_PROPORTION



										if OBJECT_TYPE in (ENEMY, ITEM, PLAYER,):
											#Calculate new points data (Axis aligned)
											PHYS_OBJECT.POINTS = utils.FIND_CUBOID_POINTS(PHYS_OBJECT.DIMENTIONS, PHYS_OBJECT.POSITION)
										elif OBJECT_TYPE in (CUBE_PHYSICS,):
											#Calculate new points data (Rotated)
											PHYS_OBJECT.POINTS = utils.ROTATE_POINTS(utils.FIND_CUBOID_POINTS(PHYS_OBJECT.DIMENTIONS, PHYS_OBJECT.POSITION), PHYS_OBJECT.POSITION, PHYS_OBJECT.ROTATION)


					#Collisions between phys-body and environmental objects
					for STATIC_ID, STATIC in STATICs_LIST[0].items(): #Check the statics (environmental objects) with collision only.
						if BOUNDING_BOX_COLLISION(PHYS_OBJECT.BOUNDING_BOX, STATIC.BOUNDING_BOX): #Axis-aligned bounding-box collision check for computational efficiency
							COLLISION_DATA = COLLISION_CHECK(PHYS_OBJECT, STATIC)
							if COLLISION_DATA[2]:
								TOUCHING = True

							if COLLISION_DATA[0]:
								if (type(STATIC) == TRIGGER) and (OBJECT_TYPE == PLAYER):
									FLAG_STATES[STATIC.FLAG] = True

								else:
									COLLIDING = True
									"""
									Stops bouncing from perfect displacement outside of the surface.
									If it were perfect, it would be outside and so not colliding; thus would be subject to gravity.
									Then the next frame, it is inside the object again, and is perfectly displaced.
									Repeat every 2nd frame, causes vibration.
									"""
									DISPLACEMENT_VECTOR += COLLISION_DATA[1] * 0.975

									if OBJECT_TYPE == PROJECTILE:
										REMOVED_OBJECTS.append(PHYS_OBJECT_ID)
					


					if PHYS_OBJECT.POSITION.Y <= -256.0:
						if OBJECT_TYPE in (ENEMY, ITEM, PROJECTILE, CUBE_PHYSICS):
							REMOVED_OBJECTS.append(PHYS_OBJECT_ID)
						else:
							#If the object falls outside of the scene boundaries, return to the player's initial position.
							PHYS_OBJECT.POSITION = CONSTANTS["PLAYER_INITIAL_POS"]
							PHYS_OBJECT.LATERAL_VELOCITY.Y = 0.0


					elif COLLIDING:
						#If colliding; apply displacement vectors, allow for jumping, etc.
						if OBJECT_TYPE == PLAYER:
							KEY_STATES["JUMP_GRACE"] = 0
						PHYS_OBJECT.POSITION += DISPLACEMENT_VECTOR
						PHYS_OBJECT.LATERAL_VELOCITY.Y = 0.0

						if TOUCHING:
							#Slide along surfaces, but not forever.
							PHYS_OBJECT.LATERAL_VELOCITY *= CONSTANTS["MULT_FRICTION"]


					else:
						#You can still jump if you do it within 10 frames of falling off of an edge.
						if KEY_STATES["JUMP_GRACE"] <= 10:
							KEY_STATES["JUMP_GRACE"] += 1/CONSTANTS["PHYSICS_ITERATIONS"]

						GRAVITY_ACCEL = ACCELERATION_CALC(CONSTANTS["ACCEL_GRAV"]/FPS, PHYS_OBJECT.MASS) / CONSTANTS["PHYSICS_ITERATIONS"]
						OBJECT_ACCELERATION = VECTOR_3D(0, GRAVITY_ACCEL, 0)
						PHYS_OBJECT.LATERAL_VELOCITY += OBJECT_ACCELERATION
						PHYS_OBJECT.POSITION += PHYS_OBJECT.LATERAL_VELOCITY / CONSTANTS["PHYSICS_ITERATIONS"]


					if KEY_STATES[PG.K_SPACE] and OBJECT_TYPE == PLAYER and KEY_STATES["JUMP_GRACE"] <= 10:
						#If the player presses SPACE and its within 10 frames of starting to fall/are on a surface, jump.
						KEY_STATES[PG.K_SPACE] = False
						PHYS_OBJECT.LATERAL_VELOCITY.Y += CONSTANTS["JUMP_VELOCITY"]
						PHYS_OBJECT.POSITION += (PHYS_OBJECT.LATERAL_VELOCITY * (1 - (CONSTANTS["MULT_AIR_RES"] / CONSTANTS["PHYSICS_ITERATIONS"])))


				OBJECT_TYPE = type(PHYS_OBJECT)
				if OBJECT_TYPE in (ENEMY, ITEM, PLAYER, CUBE_PATH, PROJECTILE,):
					#Calculate new points data (Axis aligned)
					PHYS_OBJECT.POINTS = utils.FIND_CUBOID_POINTS(PHYS_OBJECT.DIMENTIONS, PHYS_OBJECT.POSITION)
				
				elif OBJECT_TYPE in (CUBE_PHYSICS,):
					#Calculate new points data (Rotated)
					PHYS_OBJECT.POINTS = utils.ROTATE_POINTS(utils.FIND_CUBOID_POINTS(PHYS_OBJECT.DIMENTIONS, PHYS_OBJECT.POSITION), PHYS_OBJECT.POSITION, PHYS_OBJECT.ROTATION)
				

				#Update object's bounding box for this iteration, and re-assign in the dictionary of phys-bodies. Move onto next object.
				PHYS_OBJECT.BOUNDING_BOX.UPDATE(PHYS_OBJECT.POSITION, PHYS_OBJECT.POINTS)
				KINETICs_LIST[PHYS_OBJECT_ID] = PHYS_OBJECT


		for OBJECT_ID in REMOVED_OBJECTS:
			if OBJECT_ID  in KINETICs_LIST:
				del KINETICs_LIST[OBJECT_ID]

		PHYS_DATA = (KINETICs_LIST, STATICs_LIST)
		return PHYS_DATA, FLAG_STATES
	
	#except Exception as E:
		#log.ERROR("physics.UPDATE_PHYSICS", E)




#Collision-checking functions



def BOUNDING_BOX_COLLISION(BOX_A, BOX_B, OFFSET=0.0):
	#Calculates axis-aligned bounding box collisions.
	if ((BOX_A.MIN_X - OFFSET > BOX_B.MAX_X + OFFSET) or (BOX_A.MAX_X + OFFSET < BOX_B.MIN_X - OFFSET)
	  or (BOX_A.MIN_Y - OFFSET > BOX_B.MAX_Y + OFFSET) or (BOX_A.MAX_Y + OFFSET < BOX_B.MIN_Y - OFFSET)
	   or (BOX_A.MIN_Z - OFFSET > BOX_B.MAX_Z + OFFSET) or (BOX_A.MAX_Z + OFFSET < BOX_B.MIN_Z - OFFSET)):
		return False

	return True



def RAY_TRI_INTERSECTION(RAY, TRIANGLE):
	VERTEX_A, VERTEX_B, VERTEX_C = TRIANGLE
	EPSILON = 1e-8

	#Edge vectors from vertex0
	EDGE_1 = VERTEX_B - VERTEX_A
	EDGE_2 = VERTEX_C - VERTEX_A

	#Begin calculating determinant - also used to calculate u parameter
	RAY_CROSS_EDGE = RAY.DIRECTION_VECTOR.CROSS(EDGE_2)
	DETERMINANT = EDGE_1.DOT(RAY_CROSS_EDGE)

	if abs(DETERMINANT) < EPSILON:
		return None #No intersection, ray is parallel to the triangle

	INVERSE_DETERMINANT = 1/DETERMINANT

	#Calculate the vector from vertex0 to the ray origin
	RAY_ORIGIN_TO_TRI_VERTEX_A = RAY.START_POINT - VERTEX_A


	#Calculate barycentric U parameter and test bound
	BARYCENTRIC_COORDINATE_U = RAY_ORIGIN_TO_TRI_VERTEX_A.DOT(RAY_CROSS_EDGE) * INVERSE_DETERMINANT
	
	if not (0.0 <= BARYCENTRIC_COORDINATE_U <= 1.0):
		return None #No intersection found


	#Calculate barycentric V parameter and test bound
	RAY_ORIGIN_TO_TRI_VERTEX_A_CROSS_EDGE_1 = RAY_ORIGIN_TO_TRI_VERTEX_A.CROSS(EDGE_1)
	BARYCENTRIC_COORDINATE_V = RAY.DIRECTION_VECTOR.DOT(RAY_ORIGIN_TO_TRI_VERTEX_A_CROSS_EDGE_1) * INVERSE_DETERMINANT
	
	if not (0.0 <= BARYCENTRIC_COORDINATE_V <= 1.0) or (BARYCENTRIC_COORDINATE_U + BARYCENTRIC_COORDINATE_V > 1.0):
		return None #No intersection found

	#Calculate INTERSECTION_DISTANCE to find out where the intersection point is on the line
	INTERSECTION_DISTANCE = EDGE_2.DOT(RAY_ORIGIN_TO_TRI_VERTEX_A_CROSS_EDGE_1) * INVERSE_DETERMINANT


	if INTERSECTION_DISTANCE > EPSILON:
		#INTERSECTION_POINT is unused currently, but may be needed in the future, so has been retained.
		#INTERSECTION_POINT = RAY.START_POINT + (INTERSECTION_DISTANCE * RAY.DIRECTION_VECTOR)
		return INTERSECTION_DISTANCE

	else:
		return None #No intersection found



def COLLISION_CHECK(PHYS_BODY, STATIC):
	#Check if 2 objects are colliding by splitting them into triangles and using S.A.T. OR comparing cube-like properties (AABB_COLLISION_RESPONSE())
	COLLIDING, TOUCHING = False, False
	APPLIED_VECTOR, PEN_DEPTH = VECTOR_3D(0.0, 0.0, 0.0), float("inf")
	STATIC_TYPE = type(STATIC)
	
	if STATIC_TYPE in (CUBE_STATIC, CUBE_PHYSICS, CUBE_PATH, TRIGGER, PROJECTILE,): #Cube-like objects
		APPLIED_VECTOR = AABB_COLLISION_RESPONSE(PHYS_BODY, STATIC)	

		if APPLIED_VECTOR is not None: return (True, APPLIED_VECTOR, False)
	

	elif STATIC_TYPE in (QUAD, INTERACTABLE,): #Quad-like Objects
		QUAD_POINTS = STATIC.POINTS
		TRI_LIST = (
			[QUAD_POINTS[0], QUAD_POINTS[1], QUAD_POINTS[2]],
			[QUAD_POINTS[0], QUAD_POINTS[3], QUAD_POINTS[2]]
		)
		
		for I, TRIANGLE in enumerate(TRI_LIST):
			#Use SAT on the current triangle and the phys-body.
			QUAD_COLLISION = AABB_TRI_COLLISION_RESPONSE(PHYS_BODY.POINTS, TRIANGLE, STATIC.NORMALS[I])
			if QUAD_COLLISION[0] or QUAD_COLLISION[2]:
				PEN_DEPTH = min(QUAD_COLLISION[1], PEN_DEPTH)
				APPLIED_VECTOR += PEN_DEPTH * STATIC.NORMALS[0]
				COLLIDING, TOUCHING = QUAD_COLLISION[0], QUAD_COLLISION[2]
		
		if COLLIDING: return (COLLIDING, APPLIED_VECTOR, TOUCHING)
	

	elif STATIC_TYPE == TRI: #Only Tris are singular triangles.
		#Use SAT on the current triangle and the phys-body.
		TRI_COLLISION = AABB_TRI_COLLISION_RESPONSE(PHYS_BODY.POINTS, STATIC.POINTS, STATIC.NORMALS[0])
		
		if TRI_COLLISION[0] or TRI_COLLISION[2]:
			APPLIED_VECTOR = TRI_COLLISION[1] * STATIC.NORMALS[0]
			COLLIDING, TOUCHING = TRI_COLLISION[0], TRI_COLLISION[2]
		
		if COLLIDING: return (COLLIDING, APPLIED_VECTOR, TOUCHING)
	

	#If no collision found, return False.
	return (False, APPLIED_VECTOR, False)


def AABB_COLLISION_RESPONSE(AABB_1, AABB_2):
	#Compares 2 axis-aligned bounding boxes to determine collisions and their response.
	if BOUNDING_BOX_COLLISION(AABB_1.BOUNDING_BOX, AABB_2.BOUNDING_BOX, OFFSET=-1.0):
		NORMALS = [VECTOR_3D(1.0, 0.0, 0.0), VECTOR_3D(0.0, 1.0, 0.0), VECTOR_3D(0.0, 0.0, 1.0)]
		X_AXIS = min(
			(AABB_1.POSITION.X + (AABB_1.DIMENTIONS.X / 2)) - (AABB_2.POSITION.X - (AABB_2.DIMENTIONS.X / 2)),
			(AABB_2.POSITION.X + (AABB_2.DIMENTIONS.X / 2)) - (AABB_1.POSITION.X - (AABB_1.DIMENTIONS.X / 2))
		) #Minimums in the X axis.
		Y_AXIS = min(
			(AABB_1.POSITION.Y + (AABB_1.DIMENTIONS.Y / 2)) - (AABB_2.POSITION.Y - (AABB_2.DIMENTIONS.Y / 2)),
			(AABB_2.POSITION.Y + (AABB_2.DIMENTIONS.Y / 2)) - (AABB_1.POSITION.Y - (AABB_1.DIMENTIONS.Y / 2))
		) #Minimums in the Y axis.
		Z_AXIS = min(
			(AABB_1.POSITION.Z + (AABB_1.DIMENTIONS.Z / 2)) - (AABB_2.POSITION.Z - (AABB_2.DIMENTIONS.Z / 2)),
			(AABB_2.POSITION.Z + (AABB_2.DIMENTIONS.Z / 2)) - (AABB_1.POSITION.Z - (AABB_1.DIMENTIONS.Z / 2))
		) #Minimums in the Z axis.
		
		INTERSECTS = (X_AXIS, Y_AXIS, Z_AXIS)
		SMALLEST_INTERSECT = min(INTERSECTS)
		PEN_DIR = INTERSECTS.index(SMALLEST_INTERSECT)
		DISPLACEMENT_VECTOR = NORMALS[PEN_DIR] * abs(SMALLEST_INTERSECT)
		CENTRE_DIRECTION = list((AABB_1.POSITION - AABB_2.POSITION).SIGN())
		DISPLACEMENT_VECTOR *= CENTRE_DIRECTION[PEN_DIR]

		return DISPLACEMENT_VECTOR


	#If no collision, return None.
	return None



def AABB_TRI_COLLISION_RESPONSE(CUBOID, TRI, TRI_NORMAL):
	"""
	Uses S.A.T. (Separating Axis Theorem)
	Check a few axis shared between the cuboid and triangle.
	Project onto a singular line, check for overlap.
	If any have no overlap, there exists a direction of separation and so are not touching.
	"""
	SEPARATING_AXIS = (
		(CUBOID[1] - CUBOID[0]).NORMALISE(),
		(CUBOID[2] - CUBOID[0]).NORMALISE(),
		(CUBOID[4] - CUBOID[0]).NORMALISE(),
	
		(TRI[0] - TRI[1]).NORMALISE(),
		(TRI[0] - TRI[2]).NORMALISE(),
		TRI_NORMAL
	)

	MIN_PEN_DEPTH = float('inf')

	for CURRENT_AXIS in SEPARATING_AXIS:
		CUBOID_MIN_MAX = CURRENT_AXIS.PROJECT(CUBOID)
		TRI_MIN_MAX = CURRENT_AXIS.PROJECT(TRI)

		if CUBOID_MIN_MAX[1] < TRI_MIN_MAX[0] or CUBOID_MIN_MAX[0] > TRI_MIN_MAX[1]:
			del SEPARATING_AXIS, CUBOID_MIN_MAX, TRI_MIN_MAX, CURRENT_AXIS
			#Must not be touching, as a seperating axis has been found.
			return (False, 0, False)
		
		#Calculate penetration depth for the current axis
		PEN_DEPTH = min(abs(CUBOID_MIN_MAX[1] - TRI_MIN_MAX[0]), abs(TRI_MIN_MAX[1] - CUBOID_MIN_MAX[0]))
		MIN_PEN_DEPTH = min(MIN_PEN_DEPTH, PEN_DEPTH)

	OFFSET = -0.01 if MIN_PEN_DEPTH > 0.0 else 0.01 if MIN_PEN_DEPTH < 0.0 else 0.0
	del SEPARATING_AXIS, CUBOID_MIN_MAX, TRI_MIN_MAX, CURRENT_AXIS


	#If colliding, round the distance to 8 decimals and if its smaller than 0.01 treat as "TOUCHING".
	PEN_DEPTH = round(MIN_PEN_DEPTH + OFFSET, 8)
	return (True, PEN_DEPTH, False) if abs(PEN_DEPTH) > 0.001 else (False, PEN_DEPTH, True)