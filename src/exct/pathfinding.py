from exct import log
try:
	#Importing base python modules
	import sys, os
	import math as maths
	import copy
	
	os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

	sys.path.extend(("src", r"src\exct\data", r"src\exct\glsl"))

	#Import other sub-files.
	from exct import utils
	from exct.utils import *

except ImportError:
	log.ERROR("pathfinding.py", "Initial imports failed.")


log.REPORT_IMPORT("pathfinding.py")
PREFERENCES, CONSTANTS = utils.PREFERENCES, utils.CONSTANTS
NPC_NODE_GRAPH = None



class GRAPH:
	def __init__(self, NODES, INITIALISE_NODES=False):
		if INITIALISE_NODES:
			NODES = INITIALISE_NODE_LIST(NODES)

		self.INITIAL_NODES = {NODE.FLAG: NODE for NODE in NODES.values()}
		self.CURRENT_NODES = copy.copy(self.INITIAL_NODES)
		self.EMPTY = (len(NODES) == 0)



	def ADD_ENTITY_NODE(self, ENTITY, ENTITY_NAME):
		self.CURRENT_NODES = self.CLOSEST_TO_ENTITY(ENTITY, self.CURRENT_NODES, ENTITY_NAME)
		self.EMPTY = (len(self.CURRENT_NODES) == 0)



	def CLEAR_NEW_NODES(self):
		self.CURRENT_NODES = copy.copy(self.INITIAL_NODES)
		self.EMPTY = (len(self.CURRENT_NODES) == 0)



	def FIND_LOWEST_UNVISITED(self, VISITED, DISTANCES):
		LOWEST_DISTANCE_FLAG = None
		LOWEST_DISTANCE = float("inf")

		for FLAG, DISTANCE in DISTANCES.items():
			if not VISITED[FLAG] and DISTANCE < LOWEST_DISTANCE:
				LOWEST_DISTANCE = DISTANCE
				LOWEST_DISTANCE_FLAG = FLAG
				
		return LOWEST_DISTANCE_FLAG



	def DIJKSTRA(self, ORIGIN_ENTITY, TARGET_ENTITY):
		self.CLEAR_NEW_NODES()

		ORIGIN_FLAG, TARGET_FLAG = "<ORIGIN>", "<TARGET_ENTITY>"
		self.ADD_ENTITY_NODE(ORIGIN_ENTITY, ORIGIN_FLAG)
		self.ADD_ENTITY_NODE(TARGET_ENTITY, TARGET_FLAG)
		

		if ORIGIN_FLAG not in self.CURRENT_NODES or TARGET_FLAG not in self.CURRENT_NODES:
			return None


		for NODE in self.CURRENT_NODES.values():
			NODE.PREDECESSOR = None


		VISITED = {FLAG: False for FLAG in self.CURRENT_NODES}
		DISTANCES = {FLAG: float("inf") for FLAG in self.CURRENT_NODES}
		DISTANCES[ORIGIN_FLAG] = 0.0


		CURRENT_FLAG = ORIGIN_FLAG

		while CURRENT_FLAG is not None:
			CURRENT_NODE = self.CURRENT_NODES[CURRENT_FLAG]


			if CURRENT_FLAG == TARGET_FLAG:
				return self.RECONSTRUCT_PATH(TARGET_FLAG)


			for NEIGHBOUR, DISTANCE in CURRENT_NODE.CONNECTIONS.items():
				if not VISITED[NEIGHBOUR]:
					NEW_TOTAL_DISTANCE = DISTANCES[CURRENT_FLAG] + DISTANCE
					if NEW_TOTAL_DISTANCE < DISTANCES[NEIGHBOUR]:
						DISTANCES[NEIGHBOUR] = NEW_TOTAL_DISTANCE
						self.CURRENT_NODES[NEIGHBOUR].PREDECESSOR = CURRENT_FLAG


			VISITED[CURRENT_FLAG] = True


			CURRENT_FLAG = self.FIND_LOWEST_UNVISITED(VISITED, DISTANCES)


		return None



	def RECONSTRUCT_PATH(self, TARGET_FLAG):
		PATH = []
		CURRENT_FLAG = TARGET_FLAG
		
		while CURRENT_FLAG is not None:
			PATH.append(CURRENT_FLAG)
			CURRENT_FLAG = self.CURRENT_NODES[CURRENT_FLAG].PREDECESSOR
	   
		PATH.reverse()
		NODE_LIST = [self.CURRENT_NODES[FLAG] for FLAG in PATH]
		return NODE_LIST


	
	def CLOSEST_TO_ENTITY(self, ENTITY, NODE_LIST, ENTITY_NAME):
		NODE_FLAGS = [FLAG for FLAG in NODE_LIST.keys()]
		DISTANCES = [abs(ENTITY.POSITION - NODE.POSITION) for NODE in NODE_LIST.values()]

		if not self.EMPTY:
			MIN_DISTANCE = min(DISTANCES)
			INDEX = DISTANCES.index(MIN_DISTANCE)
			CLOSEST_FLAG = NODE_FLAGS[INDEX]
			NODE_LIST[CLOSEST_FLAG].CONNECTIONS[ENTITY_NAME] = MIN_DISTANCE

			CONNECTION = {CLOSEST_FLAG: MIN_DISTANCE,}

		else:
			CONNECTION = {}


		NODE_LIST[ENTITY_NAME] = NPC_PATH_NODE(
			ENTITY_NAME,
			ENTITY.POSITION,
			CONNECTION,
		)

		return NODE_LIST



	def __repr__(self):
		return f"<GRAPH: [INITIAL_NODES: {self.INITIAL_NODES}, CURRENT_NODES: {self.CURRENT_NODES}, EMPTY: {self.EMPTY}]>"



def INITIALISE_NODE_LIST(NODE_LIST):
	for NODE in NODE_LIST.values():
		CONNECTION_NAMES = NODE.CONNECTIONS
		if CONNECTION_NAMES is not None:
			NODE.CONNECTIONS = {NODE_FLAG: abs(NODE.POSITION - NODE_LIST[NODE_FLAG].POSITION) for NODE_FLAG in CONNECTION_NAMES}

	return NODE_LIST



