"""
[log.py]
Used within other file's try: except: loops to print error info with time, and log it too.
Probably most-referenced subroutine in terms of hardcoded number.

________________
Imports modules;
-OS
-Sys
-DateTime
"""
#Importing External modules
import os, sys, datetime

print("Imported Sub-file // log.py")



def GET_TIME(): #Gets current date/time, gives back as a string.
	FULL_TIME = str(datetime.datetime.now())
	UNFORMATTED_DATE, TIME = FULL_TIME[:10], FULL_TIME[11:-7]
	DATE = f"{UNFORMATTED_DATE[8:]}-{UNFORMATTED_DATE[5:7]}-{UNFORMATTED_DATE[:4]}"
	return f"{TIME}, {DATE}"



def ERROR(LOCATION, ISSUE):
	"""
	Getting the log file, and writing to it etc.
	"""
	CURRENT_DIR = os.path.dirname(__file__)
	PARENT_DIR = os.path.dirname(CURRENT_DIR)
	sys.path.append(PARENT_DIR)

	FORMATTED_TIME = GET_TIME()
	MESSAGE = (f"{FORMATTED_TIME} / ERROR in {LOCATION} / {ISSUE}")

	try:
		LOG_FILE = open("error-log.txt", "a")
		LOG_TEST = open("error-log.txt", "r")
		
		if len(LOG_TEST.readlines()) < 1:
			OPTIONAL_EXTRA_MESSAGE = "/Log file for any reported errors. Any errors will appear below;"
		
		else:
			OPTIONAL_EXTRA_MESSAGE = ""

		LOG_FILE.write(f"{OPTIONAL_EXTRA_MESSAGE}\n{MESSAGE}")
		LOG_FILE.close()

		input(f"{MESSAGE}\nPress ENTER or close terminal to exit.\n> ")

	except Exception as e:
		print(f"{FORMATTED_TIME} / ERROR @ log.py / {e} WHILE REPORTING / {LOCATION}, {ISSUE}")

	sys.exit()