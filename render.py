#These are just the imports for the neccessary components so this script can run
import os
import os.path
import sys
import time
import math
import random
import xmlrpclib
import subprocess
import getpass

os = sys.platform

#This is the hqserver class 
class hqserver(object):
	
	#Set the address for the hqueue server
	def __init__(self, address):
		#This formats the address so that it can be called properly
		self.serverAddress = address
		self.hq_server = xmlrpclib.ServerProxy("http://" + self.serverAddress + ":5000")
		self.test()
	
	#This tests whether the server is responding to pings on port 5000
	def test(self):
		try:
			self.hq_server.ping()
			self.status = 0
		except:
			self.status = 1
			raise RuntimeError("Server isn't responding on the specified port\n")

#This is where all the variables get set
class job(object):

	### TODO: Check fileDestinations "\\\"

	#This is where the static variables are set
	waitRandom = "ping 127.0.0.1 -n" + " " + "%RANDOM%" + " " + "> nul"
	#This variable is the random wait that gets placed at the beginning of the batch job
	
	def __init__(self, name):
		self.name = name
		self.program()
		self.file()
		self.location()
		self.local()
		self.destination()
		self.computers()
		self.numComp()
		self.processReservation()
		self.frameRange()
		self.frameSegmentation()
		self.programLineComposition()
		self.submitJob()
	
	#This is where the dynamic variable functions are gathered
	#Query the user on which program we're using
	def program(self):
		self.program = raw_input("What program are you rendering in? - Press m-(maya) or n-(nuke)\n")
		self.program = self.program.lower()
		if "m" in self.program:
			self.program = "maya"
		elif "n" in self.program:
			program = "nuke"
		else:
			raise RuntimeError("Incorrect spelling")

	#Query the user for the name of the file we're getting
	def file(self):
		self.file = raw_input("What is the files name?\n")
		while self.file.endswith(".ma") or self.file.endswith(".mb") or self.file.endswith(".nk"):
			self.file = self.file[:-3]
		else:
			pass

	#Query the user for where the scene file is
	def location(self):
		self.location = "P"
		if "maya" in self.program:
			self.location = raw_input("What folder is the file located in? (scenes folder)\n")
		else:
			self.location = raw_input("What folder is the file located in?\n")
			while self.location.endswith("\\") or self.location.endswith("/") or self.location.endswith(","):
				fileLocation = fileLocation[:-1]
			else:
				pass
				self.location = self.location + "\\"
				self.projLocation = self.location[:-7]
		  
	#Query the user for if the scene should be copied to the local machine before rendering
	def local(self):
		if "maya" in self.program:
				self.local = raw_input("Copy project locally before rendering?(Y/N)\n")
				self.local = self.local.lower()
				if "y" in self.local:
					self.directory = [i for i,x in enumerate(self.location) if x == "\\"]
					self.directoryLength = len(directory)
					if "\\" in self.location:
						self.proj = self.location.split("\\",self.directoryLength)
						self.projName = self.proj[self.directoryLength]
					elif "/" in self.location:
						self.proj = self.location.split("/",self.directoryLength)
						self.projName = self.proj[self.directoryLength]
					else:
						raise RuntimeError("There is no \\ or / in the file location, is it correct?(Y/N)\n")
				else:
					self.local = "n"
					self.imageCopy = ""
					self.localDelete = ""
					self.projName = ""
		else:
			self.local = "n"
			self.destination()
			 
	#Called to get the location for local render
	def destination(self):
		self.fileDestination = "P"
		if "y" in self.local:
			self.fileDestination = raw_input("Where would you like to copy to?\n")
		else:
			pass
		while self.fileDestination.endswith("\\\\") or self.fileDestination.endswith("/"):
			(self.fileDestination) = (self.fileDestination)[:-1]
		else:
			pass
		if ":" or "/" in self.fileDestination:
			fileLocationCheck = "OK"
		else:
			raise RuntimeError("There is no : or / in the file location, is it correct?(Y/N)\n")
		self.fileDestination = self.fileDestination + "\\"
		self.location = self.fileDestination + self.projName + "\\" + "scenes" + "\\"
		self.local = "xcopy /E /H" + " " + '"' + self.location + '"' + " " + '"' + self.fileDestination + self.projName + "\\" + '"' + " " + " " + "&&" + " "
		self.imageCopy = " " + "&&" + " " + "xcopy /E /H" + " " + self.fileDestination + self.projName + "\\images" + " " + '"' + self.location + "\\images\\" + '"' + " " + " " + "&&" + " "
		self.localDelete = "RD" + " " + self.fileDestination + self.projName + " " + "/S/Q" + " "
		self.location = self.fileDestination + self.projName

	def computers(self):
		self.computerRunType = raw_input("What computers should this run on? - Press a-(all) or s-(specified)\n")
		self.computerListType = computerListType.lower()
		self.computerSelectionType = computerListType
		
		if self.computerListType == "a":
			self.group = ("hostname","!=","")
		elif self.computerListType == "s":
			while self.computerRunCheck == "N":
				self.computerSelectionType = raw_input("Press c-(computers) or g-(groups)\n")
				self.computerSelectionType = computerSelectionType.lower()
				if "c" in self.computerSelectionType:
					self.computerSelectionType = "computers"
				elif "g" in self.computerSelectionType:
					self.computerSelectionType = "group"
				if self.computerSelectionType == "computers":
					self.groupType = "hostname"
					self.groupOp = "any"
					self.computerName = raw_input("Specify computer names - eg adlcgi-000941, adlcgi-000940\n")
					while self.computerName.endswith(",") or self.computerName.endswith(" "):
						self.computerName = self.computerName[:-1]
					else:
						self.pinging = subprocess.Popen(["ping",computerName,"-n","1"],stdout = subprocess.PIPE).communicate()[0]
						if ('Reply' in self.pinging):
							self.group = self.computerName
						else:
							print self.computerName + " was not available"
							group = ""
					self.computerGroupCheck = ""
					while self.computerGroupCheck == "" or group == "":
						self.computerName = raw_input("Any more computer names? - Press enter to continue\n")
						if self.computerName == "":
							self.computerGroupCheck = "pass"
						else:
							while self.computerName.endswith(",") or self.computerName.endswith(" "):
								self.computerName = self.computerName[:-1]
							else:
								self.pinging =  subprocess.Popen(["ping",computerName,"-n","1"],stdout = subprocess.PIPE).communicate()[0]
								if ('Reply' in self.pinging):
									if self.group == "":
										self.group = self.computerName
										self.computerRunCheck = "OK"
									else:
										self.group = self.group + ", " + self.computerName
								else:
									print self.computerName + " was not available"
					while self.group.endswith(",") or self.group.endswith(" "):
						self.group = self.group[:-1]
					else:
						self.group = self.group.translate(None, ' ')
						self.group = self.group.upper()
					print self.group
				elif self.computerSelectionType == "group":
					self.groupType = "group"
					self.groupOp = "=="
					self.group = raw_input("Specify group names - eg Example1, example2\n")
					if self.group == "":
						pass
					else:
						self.computerRunCheck = "OK"
				else:
					print "Incorrect Spelling"
		else:
			print "Please type a or s\n"
		
	def numComp(self):
		if self.computerSelectionType == "a":
			self.computers = int(raw_input("How many computers are you rendering on?\n"))
			self.messUp = "OK"
		elif self.groupType == "group":
			self.computers = int(raw_input("How many computers are you rendering on?\n"))
			self.messUp = "OK"
		elif self.computerSelectionType == "computers":
			self.groupNum = self.group.split(',')
			self.computers = len(self.groupNum)
			self.messUpCheck = raw_input("You have specified" + " " + str(self.computers) + " " + "computers, is this correct?(Y/N)\n")
			self.messUpCheck = self.messUpCheck.lower()
			if "y" in self.messUpCheck:
				self.messUp = "OK"
			else:
				self.computerRunCheck = "N"

		if self.computers == "":
			self.computers = 1
		else:
			pass

	def processReservation(self):
		if self.program == "maya":
			self.renderThreads = int(raw_input("How many render threads? (1-12)\n"))
			if self.renderThreads == "":
				self.renderThreads = 4
			else:
				pass
			self.renderer = raw_input("Select renderer? - Press m-(mentalRay) or a-(arnold) or h-(hardware)\n")
			self.renderer = self.renderer.lower()
			if "m" in self.renderer:
				self.renderer = "mentalRay"
			elif "a" in self.renderer:
				self.renderer = "arnold"
			elif "h" in self.renderer:
				self.renderer = "hardware"
			else:
				self.renderer = ""
				print "Renderer not defined, defaulting to scene file (May or may not work)"
		else:
			self.renderThreads = int(raw_input("How many render threads? (1-12)\n"))

	def frameRange(self):
		self.frameCheck = "N"
		while self.frameCheck == "N":
			self.frameStart = raw_input("What is the starting frame?\n")
			self.frameEnd = raw_input("What is the ending frame?\n")
			self.frameUserCheck = raw_input("You have specified " + frameStart + "-" + frameEnd + " is that correct?(Y/N)\n")
			self.frameUserCheck = self.frameUserCheck.lower()
			if "y" in self.frameUserCheck:
				self.frameCheck = "OK"
			else:
				pass
		else:
			pass
		self.frameRangeNum = ((int(self.frameStart)-1) - int(self.frameEnd))
		self.frameRange = self.frameStart + "-" + self.frameEnd
		self.frameAll = int(self.frameEnd) - (int(self.frameStart) - 1)
		self.renderStart = int(self.frameStart)
		self.renderRange = float(self.frameAll) / float(self.computers)
		self.renderRange = (math.ceil(self.renderRange))
		self.renderRange = str(self.renderRange)[:-2]
		self.renderRange = int(self.renderRange)
		self.renderEnd = (int(self.frameStart) + int(self.renderRange)) -1
		self.seqEnd = ((int(self.frameStart)-1) + int(self.computers))
		self.frameNum = self.renderStart
		self.compLen = len(str(self.computers))
		self.jobNum = 1
		self.jobNum = format(self.jobNum, str(self.compLen))
		self.jobNum = int(self.jobNum)

	def frameSegmentation(self):
		if self.program == "maya":
			self.renderType = raw_input("Do you want to render using tiles?(Y/N)\n")
			self.renderType = self.renderType.lower()
			if "y" in self.renderType:
				self.renderType = "t"
			else:
				self.renderType = raw_input("Press b-(batches) or s-(sequentially)\n")
				self.renderType = self.renderType.lower()
		else:
			self.renderType = raw_input("Press b-(batches) or s-(sequentially)\n")
			self.renderType = self.renderType.lower()
	
		if "t" in self.renderType:
				self.tileNum = int(raw_input("How many tiles?\n"))
				self.tilesWide = int(raw_input("How many tiles high?\n"))
				self.tilesHigh = tileNum/tilesWide
				self.dimensionCheck = "N"
				while self.dimensionCheck == "N":
					self.renderWidth = raw_input("What is the width of the image\n")
					self.renderHeight = raw_input("What is the height of the image\n")
					self.dimensionUserCheck = raw_input("You have specified " + renderWidth + "x" + renderHeight + " is that correct?(Y/N)\n")
					self.dimensionUserCheck = dimensionUserCheck.lower()
					if "y" in self.dimensionUserCheck:
						self.dimensionCheck = "OK"
					else:
						pass
				else:
					pass
				self.renderTileNum = 1
				self.renderWidthTileNum = 1
				self.renderHeightTileNum = 1

	def programLineComposition(self):
		if self.program == "nuke":
			self.programline = self.waitRandom + " " + "&&" + " " + self.localRender + "C: && cd C:\Program Files\Nuke9.0v6 && Nuke9.0 -ix "
			self.programExt = ".nk"
		elif self.program == "maya":
			self.programline = self.waitRandom + " " + "&&" + " " + self.localRender + "C: && set path=%PATH%;C:\Program Files\Autodesk\Maya2015\\bin; && render "
			if os.path.isfile(self.fileLoc + self.file + ".ma"):
				self.programExt = ".ma"
			else:
				self.programExt = ".mb"

	def userName(self):
		self.user = raw_input("Job submitted by?\n")
		if self.user == "":
			self.user == getpass.getuser()
		else:
			pass

	def submitJob(job_spec, jobNum):
		
		self.jobNum = jobNum
		
		#This sends the HQueue Job to the HQueue Server to run your render
		if "b" in self.renderType:
			#This checks if the frame range for the render command is below the final frame
			while int(self.renderStart) <= int(self.frameEnd):

				if self.renderEnd <= int(self.frameEnd):
					pass
				else:
					self.frameDif = abs(self.renderEnd - int(self.frameEnd))
					self.renderEnd = self.renderEnd - self.frameDif

				#This checks what program is rendering then compiles the command for the clients to run
				if self.program == "nuke":
					self.command = self.programline + "-F " + str(self.renderStart) + "-" + str(self.renderEnd) + " " + self.fileLoc + self.file + self.programExt
				elif self.program == "maya":
					self.renderLength = "-s " + str(self.renderStart) + " " + "-e " + str(self.renderEnd) + " "
					if "mentalRay" in self.renderer:
						self.renderSettings = "-mr:rt" + " " + str(self.renderThreads) + " " + "-mr:v 5" + " "
					elif "arnold" in self.renderer:
						self.renderSettings = "-r arnold" + " "
					elif "hardware" in self.renderer:
						self.renderSettings = "-r hw" + " "
					else:
						self.renderSettings = ""
					self.command = self.programline + self.renderLength + self.renderSettings + "-proj" + " " + self.fileLocation + " " + self.fileLoc + self.file + self.programExt + self.imageCopy + self.localDelete
				else:
					print "Error: unsupported program"
	
				#This is where the HQueue job is compiled
				job_spec = {
					"name" : self.file + " " + str(self.renderStart) + "-" + str(self.renderEnd),
					"command": self.command,
					"tags": [ "single" ],
					"maxHosts": 1,
					"minHosts": 1,
					"submittedBy": self.user,
					"conditions": [
						{ "type" : "client", "name":self.groupType, "op":self.groupOp, "value":self.group },
					]
				}
	
				#Calling the function to submit a job
				submitJob(job_spec, self.jobNum)
	
				#This checks if this is the last frame of the sequence and if it is adds a frame
				self.renderStart += self.renderRange
				self.renderEnd += self.renderRange
				self.jobNum += 1
		elif "t" in self.renderType:
			#This checks if the frame range for the render command is below the final frame
			while int(self.frameNum) <= int(self.frameEnd):
	
				if self.renderEnd <= int(self.frameEnd):
					pass
				else:
					self.frameDif = abs(self.renderEnd - int(self.frameEnd))
					self.renderEnd = self.renderEnd - self.frameDif
				self.renderLength = "-s " + str(self.frameNum) + " " + "-e " + str(self.frameNum) + " "
				if "mentalRay" in renderer:
					self.renderSettings = "-mr:rt" + " " + str(self.renderThreads) + " " + "-mr:v 5" + " "
				elif "arnold" in self.renderer:
					self.renderSettings = "-r arnold" + " "
				elif "hardware" in self.renderer:
					self.renderSettings = "-r hw"
				else:
					self.renderSettings = ""
				if self.renderTileNum <= self.tileNum:
					self.mayaTileRender = "-x" + " " + str(self.renderWidth) + " " + "-y" + " " + str(self.renderHeight) + " " + "-mr:reg" + " " + str(((int(self.renderWidth) / (int(self.tileNum)/self.tilesWide)) * (int(self.renderWidthTileNum) - 1))) + " " + str(((int(self.renderWidth) / (int(self.tileNum)/(self.tilesWide))) * int(self.renderWidthTileNum))) + " " + str(((int(self.renderHeight) / (int(self.tileNum)/self.tilesHigh)) * (int(self.renderHeightTileNum) - 1))) + " " + str(((int(self.renderHeight) / (int(self.tileNum)/self.tilesHigh)) * int(self.renderHeightTileNum))) + " "
				else:
					pass
				self.command = self.programline + self.renderLength + self.renderSettings + self.mayaTileRender + "-im" + " " + "part" + str(self.renderTileNum) + " " + "-proj " + self.fileLocation + " " + self.fileLoc + self.file + self.programExt + self.imageCopy + self.localDelete
	
				#This is where the HQueue job is compiled
				job_spec = {
					"name" : self.file + " " + "tile" + ":" + str(self.renderTileNum) + " " + "Frame" + ":" + str(self.frameNum),
					"command": self.command,
					"tags": [ "single" ],
					"maxHosts": 1,
					"minHosts": 1,
					"submittedBy": self.user,
					"conditions": [
						{ "type" : "client", "name":self.groupType, "op":self.groupOp, "value":self.group },
					]
				}
	
				#Calling the function to submit a job
				submitJob(job_spec, self.jobNum)
	
				#This checks if this is the last frame of the tile sequence and if it is adds a frame
				if self.frameNum <= self.renderEnd:
					if self.renderTileNum < self.tileNum:
						self.renderTileNum += 1
						if (self.renderTileNum-1) % self.tilesHigh == 0:
							self.renderWidthTileNum = 1
							self.renderHeightTileNum += 1
						else:
							self.renderWidthTileNum += 1
					else:
						self.frameNum += 1
						self.renderTileNum = 1
						self.renderWidthTileNum = 1
						self.renderHeightTileNum = 1
				else:
					self.renderStart += self.renderRange
					self.renderEnd += self.renderRange
					self.renderTileNum = 1
					self.renderWidthTileNum = 1
					self.renderHeightTileNum = 1
	
				self.jobNum += 1
		elif "s" in self.renderType:
			#This checks if the frame range for the render command is below the final frame
			while int(self.renderStart) <= int(self.seqEnd):
				#This checks what program is rendering then compiles the command for the clients to run
				if self.program == "nuke":
					self.command = self.programline + "-F " + str(self.renderStart) + "-" + str(self.frameEnd) + "x" + str(self.computers) + " " + self.fileLoc + self.file + self.programExt
				elif program == "maya":
					self.renderLength = "-s " + str(self.renderStart) + " " + "-e " + str(self.frameEnd) + " " + "-b " + str(self.computers)  + " "
					if "mentalRay" in self.renderer:
						self.renderSettings = "-mr:rt" + " " + str(self.renderThreads) + " " + "-mr:v 5" + " "
					elif "arnold" in self.renderer:
						self.renderSettings = "-r arnold "
					elif "hardware" in self.renderer:
						self.renderSettings = "-r hw"
					else:
						self.renderSettings = ""
					self.command = self.programline + self.renderLength + self.renderSettings + "-proj " + self.fileLocation + " " + self.fileLoc + self.file + self.programExt + self.imageCopy + self.localDelete
				else:
					print "Error: incorrect program"
	
				#This is where the HQueue job is compiled
				job_spec = {
					"name" : self.file + " " + str(self.renderStart) + "-" + str(self.frameEnd) + "x" + str(self.computers),
					"command": self.command,
					"tags": [ "single" ],
					"maxHosts": 1,
					"minHosts": 1,
					"submittedBy": self.user,
					"conditions": [
						{ "type" : "client", "name":self.groupType, "op":self.groupOp, "value":self.group },
					]
				}
	
				#Calling the function to submit a job
				submitJob(job_spec, self.jobNum)
	
				#This adds a value of something or other to render sequentially
				self.renderStart += 1
				
				self.jobNum += 1

serverAddress=raw_input("Server address?\n")
server=hqserver(serverAddress)
job1 = job("job1")
