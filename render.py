#These are just the imports for the neccessary components so this script can run
import os
import sys
import time
import math
import random
import xmlrpclib

#This sets the server connection as a variable that can be called anytime
hq_server = xmlrpclib.ServerProxy("http://adlcgi-000941:5000")

#This checks if the server is accepting remote connections
try:
	hq_server.ping()
	Hqueue = "up"
except:
	Hqueue = "down"
print "HQueue Server is " + Hqueue + "\n"

#This is the main script
if Hqueue == "down":
	pass
else:
	#This is where the main variables are set, these are very sensitive so I don't recommend changing them
	file = raw_input("What is the files name?\n")

	if "sgtSpaghetti" in file:
		command = raw_input("What is the command?\n")
		compNum = raw_input("How many computers should this run on?\n")
		jobNum = 1
		while jobNum <= int(compNum):
		#This is where the HQueue job is compiled
			job_spec = {
				"name" : "Spaghetti command",
				"command": command,
				"tags": [ "sgtSpaghetti" ],
				"maxHosts": 1,
				"minHosts": 1,
			}
			job_ids = hq_server.newjob(job_spec)
			status = "Command" + " " + str(jobNum) + " " + "successfully submitted.\n"
			print status
			jobNum += 1
		sys.exit()
	else:
		pass

	program = raw_input("What program are you rendering in?\n")
	fileLocation = raw_input("What folder is the file located in?\n")
	fileLoc = fileLocation + "/"
	fileLocation = fileLocation[:-7]
	group = raw_input("What computers should this run on?(If all leave blank, if some computers write some, if you want to exclude any computers type their names)\n")
	group = group.lower()
	groupGroup = group

	if groupGroup == "":
		groupType = "hostname"
		groupOp = "!="
	elif groupGroup == "some":
		while group == "some":
			groupGroup = raw_input("Computers or Groups\n")
			groupGroup = groupGroup.lower()
			if groupGroup == "computers":
				groupType = "hostname"
				groupOp = "any"
				group = raw_input("Which computers\n")
				group = group.upper()
			elif groupGroup == "groups":
				groupType = "group"
				groupOp = "=="
				group = raw_input("Which groups?\n")
			else:
				print "Incorrect Spelling"
	else:
		groupType = "hostname"
		groupOp = "!="
		group = group.upper()

	if program == "maya":
		renderThreads = int(raw_input("How many render threads?\n"))
		renderer = raw_input("What renderer?\n")

		if "enta" in renderer:
			renderer = "mentalRay"
		elif "rnol" in renderer:
			renderer = "arnold"
		else:
			renderer = ""
			print "Renderer not defined, defaulting to scene file (May or may not work)"

	else:
		pass

	computers = int(raw_input("How many computers are you rendering on?\n"))
	frameStart = raw_input("What is the starting frame?\n")
	frameEnd = raw_input("What is the ending frame?\n")
	frameRange = frameStart + "-" + frameEnd
	frameAll = int(frameEnd) - (int(frameStart) - 1)
	renderStart = int(frameStart)
	renderRange = float(frameAll) / float(computers)
	renderRange = (math.ceil(renderRange))
	renderRange = str(renderRange)[:-2]
	renderRange = int(renderRange)
	renderEnd = (int(frameStart) + int(renderRange)) -1
	frameNum = renderStart
	compLen = len(str(computers))
	jobNum = 1
	jobNum = format(jobNum, str(compLen))
	jobNum = int(jobNum)

	if program == "maya":
		new = raw_input("Do you want to render batches, sequentially or using tiles?\n")
	else:
		new = raw_input("Do you want to render batches or sequentially\n")

	if "tile" in new:
			tileNum = int(raw_input("How many tiles?\n"))
			renderWidth = raw_input("What is the width of the image\n")
			renderHeight = raw_input("What is the height of the image\n")
			renderTileNum = 1
			renderWidthTileNum = 1
			renderHeightTileNum = 1
	waitRandom = "ping 127.0.0.1 -n" + " " + str(random.randrange(0,120)) + " " + "> nul"
	user = raw_input("Who are you?\n")

	def submitJob(job_spec, jobNum):
		#This sends the HQueue Job to the HQueue Server to run your render
		job_ids = hq_server.newjob(job_spec)
		print "Job" + " " + str(jobNum) + "/" + str(computers) + " " + "successfully submitted.\n"

	#This is the main beast that evaluates all the inputs and formulates commands for rendering on clients
	if "bat" in new:
		#This checks if the frame range for the render command is below the final frame
		while int(renderStart) <= int(frameEnd):

			if renderEnd <= int(frameEnd):
				pass
			else:
				frameDif = abs(renderEnd - int(frameEnd))
				renderEnd = renderEnd - frameDif

			#This checks what program is rendering then compiles the command for the clients to run
			if program == "nuke":
				programline = waitRandom + " " + "&&" + " " + "C: && cd C:\Program Files\Nuke9.0v6 && Nuke9.0 -ix "
				programExt = ".nk"
				command = programline + "-F " + str(renderStart) + "-" + str(renderEnd) + " " + fileLoc + file + programExt
			elif program == "maya":
				programline = waitRandom + " " + "&&" + " " + "C: && set path=%PATH%;C:\Program Files\Autodesk\Maya2015\\bin; && render "
				programExt = ".mb"
				renderLength = "-s " + str(renderStart) + " " + "-e " + str(renderEnd) + " "
				if "mentalRay" in renderer:
					rendererSettings = "-mr:rt" + " " + str(renderThreads) + " " + "-mr:v 5" + " "
				elif "arnold" in renderer:
					rendererSettings = "-r arnold" + " "
				else:
					renderSettings = ""
				command = programline + renderLength + rendererSettings + "-proj" + " " + fileLocation + " " + fileLoc + file + programExt
			else:
				print "Error: unsupported program"

			#This is where the HQueue job is compiled
			job_spec = {
				"name" : file + " " + str(renderStart) + "-" + str(renderEnd),
				"command": command,
				"tags": [ "single" ],
				"maxHosts": 1,
				"minHosts": 1,
				"submittedBy": user,
				"conditions": [
					{ "type" : "client", "name":groupType, "op":groupOp, "value":group },
				]
			}
			
			#Calling the function to submit a job
			submitJob(job_spec, jobNum)

			#This checks if this is the last frame of the sequence and if it is adds a frame
			renderStart += renderRange
			renderEnd += renderRange
			jobNum += 1
	elif "tile" in new:
		#This checks if the frame range for the render command is below the final frame
		while int(frameNum) <= int(frameEnd):

			if renderEnd <= int(frameEnd):
				pass
			else:
				frameDif = abs(renderEnd - int(frameEnd))
				renderEnd = renderEnd - frameDif
			programline = waitRandom + " " + "&&" + " " + "C: && set path=%PATH%;C:\Program Files\Autodesk\Maya2015\\bin; && render "
			programExt = ".mb"
			renderLength = "-s " + str(frameNum) + " " + "-e " + str(frameNum) + " "
			if "mentalRay" in renderer:
				rendererSettings = "-mr:rt" + " " + str(renderThreads) + " " + "-mr:v 5" + " "
			elif "arnold" in renderer:
				rendererSettings = "-r arnold" + " "
			else:
				renderSettings = ""
			if renderTileNum <= tileNum:
				mayaTileRender = "-x" + " " + str(renderWidth) + " " + "-y" + " " + str(renderHeight) + " " + "-mr:reg" + " " + str(((int(renderWidth) / (int(tileNum)/2)) * (int(renderWidthTileNum) - 1))) + " " + str(((int(renderWidth) / (int(tileNum)/2)) * int(renderWidthTileNum))) + " " + str(((int(renderHeight) / (int(tileNum)/4)) * (int(renderHeightTileNum) - 1))) + " " + str(((int(renderHeight) / (int(tileNum)/4)) * int(renderHeightTileNum))) + " "
			else:
				pass
			command = programline + renderLength + renderSettings + mayaTileRender + "-im" + " " + str(frameNum) + "-" + "part" + str(renderTileNum) + " " + "-proj " + fileLocation + " " + fileLoc + file + programExt

			#This is where the HQueue job is compiled
			job_spec = {
				"name" : file + " " + "tile" + str(renderTileNum) + "Frame" + str(frameNum),
				"command": command,
				"tags": [ "single" ],
				"maxHosts": 1,
				"minHosts": 1,
				"submittedBy": user,
				"conditions": [
					{ "type" : "client", "name":groupType, "op":groupOp, "value":group },
				]
			}

			#Calling the function to submit a job
			submitJob(job_spec, jobNum)

			#This checks if this is the last frame of the tile sequence and if it is adds a frame
			if frameNum <= renderEnd:
				if renderTileNum < tileNum:
					renderTileNum += 1
					if renderTileNum <> ((int(tileNum)/2)+1):
						renderWidthTileNum += 1
					else:
						renderWidthTileNum = 1
						renderHeightTileNum += 1
				else:
					frameNum += 1
					renderTileNum = 1
					renderWidthTileNum = 1
					renderHeightTileNum = 1
			else:
				renderStart += renderRange
				renderEnd += renderRange
				renderTileNum = 1
				renderWidthTileNum = 1
				renderHeightTileNum = 1

			jobNum += 1
	else:
		#This checks if the frame range for the render command is below the final frame
		while int(renderStart) <= int(frameEnd):

			#This checks what program is rendering then compiles the command for the clients to run
			if program == "nuke":
				programline = waitRandom + " " + "&&" + " " + "C: && cd C:\Program Files\Nuke9.0v6 && Nuke9.0 -ix "
				programExt = ".nk"
				command = programline + "-F " + str(renderStart) + "-" + str(frameEnd) + "x" + str(computers) + " " + fileLoc + file + programExt
			elif program == "maya":
				programline = waitRandom + " " + "&&" + " " + "C: && set path=%PATH%;C:\Program Files\Autodesk\Maya2015\\bin; && render "
				programExt = ".mb"
				renderLength = "-s " + str(renderStart) + " " + "-e " + str(renderEnd) + " " + "-b " + str(renderRange)  + " "
				if "mentalRay" in renderer:
					rendererSettings = "-mr:rt" + " " + str(renderThreads) + " " + "-mr:v 5" + " "
				elif "arnold" in renderer:
					rendererSettings = "-r arnold "
				else:
					renderSettings = ""
				command = programline + renderSettings + "-proj " + fileLocation + " " + fileLoc + file + programExt
			else:
				print "Error: incorrect program"

			#This is where the HQueue job is compiled
			job_spec = {
				"name" : file + " " + str(renderStart) +  "x" + str(renderRange) + "-" + str(frameEnd),
				"command": command,
				"tags": [ "single" ],
				"maxHosts": 1,
				"minHosts": 1,
				"submittedBy": user,
				"conditions": [
					{ "type" : "client", "name":groupType, "op":groupOp, "value":group },
				]
			}

			#Calling the function to submit a job
			submitJob(job_spec, jobNum)

			#This adds a value of 1 to render sequentially 
			renderStart += int(computers)
			
			jobNum += 1