### Import needed modules and components
import os
import os.path
import sys
import xmlrpclib

### Window setup
class programCheck:
	
	### Initiate the job class by first building the window
	def __init__(self):
		self.gui = self.check()
	
	def check(self):
		### Try and initiate in a Nuke window or a Maya window and error if neither are found.
		try:
			import nuke
			import nukescripts
			return(nukeWindow)
		except:
			try:
				import maya.cmds as cmds
				return(mayaWindow)
			except:
				### Normally I'd run a raise RuntimeError but it's hard for non-programmers to debug so I'll print an error first then raise RuntimeError.
				print("No supported window manager available(Nuke, Maya)\n")
				raise RuntimeError("No supported window manager available(Nuke, Maya)\n")

class hqRop(object):

	### This chunk of code is lifted from hqrop.py and rewritten as neccessary #######################################################################
	def submitJob(parms, submit_function):
		"""Submits a job with the given parameters and function after checking to
		see if the project files need to be copied or not.
		submit_function will be passed parms
		"""
		if self.parms["hip_action"] == "copy_to_shared_folder":
			self.copyToSharedFolder(parms, submit_function)
		else:
			self.submit_function(self.parms)

	def expandHQROOT(self, path, hq_server):
		"""Return the given file path with instances of $HQROOT expanded
		out to the mount point for the HQueue shared folder root."""
		# Get the HQueue root path.
		self.hq_root = self.getHQROOT(hq_server)
		if self.hq_root is None:
			return path
	
		expanded_path = path.replace("$HQROOT", self.hq_root)
		return expanded_path


	def getHQROOT(self, hq_server):
		"""Query the HQueue server and return the mount point path 
		to the HQueue shared folder root.
		Return None if the path cannot be retrieved from the server.
		"""
		# Identify this machine's platform.
		platform = sys.platform
		if platform.startswith("win"):
			platform = "windows"
		elif platform.startswith("linux"):
			platform = "linux"
		elif platform.startswith("darwin"):
			platform = "macosx"
		
		# Connect to the HQueue server.
		s = self.hQServerConnect(hq_server)
		if s is None:
			return None
		
		try:
			# Get the HQ root.
			self.hq_root = s.getHQRoot(platform)
		except:
			print("Could not retrieve $HQROOT from '" + hq_server + "'.")
			return None
		
		return self.hq_root

	def getHQueueCommands(remote_hfs, num_cpus=0):
		"""Return the dictionary of commands to start hython, Python, and mantra.
		Return None if an error occurs when reading the commands
		from the HQueueCommands file.
		If `num_cpus` is greater than 0, then we add a -j option
		to each command so that the application is run with a maximum
		number of threads.
		"""
		import hou
		# HQueueCommands will exist in the Houdini path.
		cmd_file_path = hou.findFile(
			"soho/python%d.%d/HQueueCommands" % sys.version_info[:2])
	
		hq_cmds = {}
		cmd_file = open(cmd_file_path, "r")
		cmd_name = None
		cmds = None
		continue_cmd = False
		for line in cmd_file:
			line = line.strip()
	
			# Check if we need to continue the current command.
			if continue_cmd:
				# Add line to current command.
				cmds = _addLineToCommands(cmds, line)
				if line[-1] == "\\":
					continue_cmd = True
				else:
					cmds = _finalizeCommands(cmd_name, cmds, remote_hfs, num_cpus)
					if cmds is None:
						return None
					hq_cmds[cmd_name] = cmds
					continue_cmd = False
				continue
	
			# Ignore comments and empty lines.
			if line.startswith("#") or line.strip() == "":
				continue
	
			# Ignore lines with no command assignment.
			eq_op_loc = line.find("=")
			if eq_op_loc < 0:
				continue
	
			# Start a new command.
			cmd_name = line[0:eq_op_loc].strip()
			cmds = None
			line = line[eq_op_loc+1:]
	
			# Add line to current command.
			cmds = _addLineToCommands(cmds, line)
			if line[-1] == "\\":
				continue_cmd = True
			else:
				cmds = _finalizeCommands(cmd_name, cmds, remote_hfs, num_cpus)
				if cmds is None:
					return None
				hq_cmds[cmd_name] = cmds
				continue_cmd = False
	
		return hq_cmds


	def _addLineToCommands(cmds, line):
		"""Adds the given line to the command string.
		This is a helper function for getHQueueCommands.
		"""
		line = line.strip()
		if line[-1] == "\\":
			line = line[:-1].strip()
	
		if cmds is None:
			cmds = line
		else:
			cmds = cmds + " " + line
	
		return cmds


	def _finalizeCommands(cmd_name, cmds, remote_hfs, num_cpus):
		"""Perform final touches to the given commands.
		This is a helper function for getHQueueCommands.
		"""
		if cmd_name.endswith("Windows"):
			remote_hfs = hutil.file.convertToWinPath(remote_hfs, var_notation="!")
	
		# Replace HFS instances.
		cmds = cmds.replace("%(HFS)s", remote_hfs)
	
		# Attempt to replace other variable instances with
		# environment variables.
		try:
			cmds = cmds % os.environ
		except KeyError, e:
			print("Use of undefined variable in " + cmd_name + ".", e)
			return None
	
		# Strip out wrapper quotes, if any.
		# TODO: Is this needed still?
		if (cmds[0] == "\"" and cmds[-1] == "\"") \
			or (cmds[0] == "'" and cmds[-1] == "'"):
			cmds = cmds[1:]
			cmds = cmds[0:-1]
	
		# Add the -j option to hython and Mantra commands.
		if num_cpus > 0 and (
			cmd_name.startswith("hython") or cmd_name.startswith("mantra")):
			cmds += " -j" + str(num_cpus)
	
		return cmds

	def hqServerProxySetup(self, hq_server):
		"""Sets up a xmlrpclib server proxy to the given HQ server."""
		if not hq_server.startswith("http://"):
			full_hq_server_path = "http://%s" % hq_server
		else:
			full_hq_server_path = hq_server

		return xmlrpclib.ServerProxy(full_hq_server_path, allow_none=True)

	def doesHQServerExists(self, hq_server):
		"""Check that the given HQ server can be connected to.
		Returns True if the server exists and False if it does not. Furthermore,
		it will display an error message if it does not exists."""
		server = self.hqServerProxySetup(hq_server)
		return self.hQServerPing(server, hq_server)

	def hQServerConnect(self, hq_server):
		"""Connect to the HQueue server and return the proxy connection."""
		s = self.hqServerProxySetup(hq_server)

		if self.hQServerPing(s, hq_server):
			return s
		else:
			return None

	def hQServerPing(self, server, hq_server):
		try:
			server.ping()
			return True
		except:
			print("Could not connect to '" + hq_server + "'.\n\n"
				+ "Make sure that the HQueue server is running\n"
				+ "or change the value of 'HQueue Server'.",
				TypeError("this is a type error"))

			return False

	def getClients(self, hq_server):
		"""Return a list of all the clients registered on the HQueue server.
		Return None if the client list could not be retrieved from the server.
		"""
		s = self.hQServerConnect(hq_server)

		if s is None:
			return None

		try:
			self.client_ids = None
			self.attribs = ["id", "hostname"]
			self.clients = s.getClients(self.client_ids, self.attribs)
		except:
			print("Could not retrieve client list from '" + hq_server + "'.")
			return None
			
		return [self.client["hostname"] for self.client in self.clients]

	def getClientGroups(self, hq_server):
		"""Return a list of all the client groups on the HQueue server.
		Return None if the client group list could not be retrieved from the server.
		"""
		s = self.hQServerConnect(hq_server)
		if s is None:
			return None

		try:
			self.client_groups = s.getClientGroups()
		except:
			print("Could not retrieve client group list from '" 
						+ hq_server + "'.")
			return None
	
		return self.client_groups

	##################################################################################################################################################

### Run to open a window in Nuke
class nukeWindow(nukescripts.PythonPanel):
	
	### Initialise the hqRop to be callable
	serverRop = hqRop()

	def __init__(self):
		### Init the panel with a name
		nukescripts.PythonPanel.__init__(self, "hQueue Nuke render submission panel")
		### Gets the absolute file path for the currently open Nuke script, if nothing open then defaults to install directory
		self.absoluteFilePath = os.path.abspath(nuke.value("root.name"))
		### Setup a text box for the server address to be input into
		self.serverAddress = nuke.String_Knob('serverAddress', 'Server Address: ')
		self.addKnob(self.serverAddress)
		### Setup a button to test the server address which will reveal the Connection Successful text
		self.addressTest = nuke.PyScript_Knob("addressTest", "Test the server address", "")
		self.addKnob(self.addressTest)
		### Create addressSuccessFlag flag that is hidden until the server is successfully pinged
		self.addressSuccessFlag = nuke.Text_Knob('addressSuccessFlag', '', '<span style="color:green">Connection Successful</span>')
		self.addressSuccessFlag.setFlag(nuke.STARTLINE)
        self.addressSuccessFlag.setVisible(False)
        self.addKnob(self.addressSuccessFlag)
		### Get the filepath from self.absoluteFilePath and put it into a text box
		self.filePath = nuke.String_Knob('filePath', 'File Path: ', self.absoluteFilePath)
		self.addKnob(self.filePath)
		### Create a button that will test the file path for an nuke script
		self.filePathCheck = nuke.PyScript_Knob("filePathCheck", "Test the File Path", "")
        self.addKnob(self.filePathCheck)
        ### Create pathSuccessFlag flag that is hidden until the file path is verified
		self.pathSuccessFlag = nuke.Text_Knob('pathSuccessFlag', '', '<span style="color:green">Connection Successful</span>')
		self.pathSuccessFlag.setFlag(nuke.STARTLINE)
        self.pathSuccessFlag.setVisible(False)
        self.addKnob(self.pathSuccessFlag)
		### Setup the get client list button, which will use hqrop functions
		self.clientGet = nuke.PyScript_Knob("clientGet", "Get client list", "")
		self.addKnob(self.clientGet)
		### Setup the get client groups button, which will use hqrop functions
		self.clientGroupGet = nuke.PyScript_Knob("clientGroupGet", "Get client groups", "")
		self.addKnob(self.clientGroupGet)
		### Setup a save client selection button, this hides the client list and itself
		self.clientSelect = nuke.PyScript_Knob("clientSelect", "Save client selection", "")
		self.clientSelect.setVisible(False)
		self.addKnob(self.clientSelect)
		### Setup a multiline client list that appears when clientGet is run
		self.clientList = nuke.Multiline_Eval_String_Knob('clientList', 'Client List: ')
		self.clientList.setFlag(nuke.STARTLINE)
		self.clientList.setVisible(False)
		self.addKnob(self.clientList)
		### Setup a frame range with the default frame range of the scene
		self.fRange = nuke.String_Knob('fRange', 'Track Range', '%s-%s' % (nuke.root().firstFrame(), nuke.root().lastFrame()))
		self.addKnob(self.fRange)
		
		### Set the minimum size of the python panel
		self.setMinimumSize(500, 600)

	def knobChanged(self, knob):
		### When you press a button run the command attached to that button
		self.response = ""
		### Figure out which knob was changed
		if knob is self.filePathCheck:
			### See if the file path has $HQROOT in it
			if "$HQROOT" in self.filePath.value():
				### Get a response from the function of the button that was pressed
				self.cleanPath = self.serverRop.expandHQROOT(self.filePath.value(), self.serverAddress.value())
				self.response = self.filePath.value()
				### Clean the file path before checking it exists
				if os.path.isfile(self.response):
					### Set the value of pathSuccessFlag to green text Connection Successful 
					self.pathSuccessFlag.setValue('<span style="color:green">File found</span>')
				else:
					### Set the value of pathSuccessFlag to green text Connection failed
					self.pathSuccessFlag.setValue('<span style="color:red">File not found</span>')
				### Set the address success text flag to visible
				self.pathSuccessFlag.setVisible(True)
			elif self.serverRop.getHQROOT(self.serverAddress.value()) in self.filePath.value():
				self.hqroot = self.serverRop.getHQROOT(self.serverAddress.value())
				self.response = self.filePath.value().replace(self.hqroot, "$HQROOT")
				### Check whether file exists
				if os.path.isfile(self.filePath.value()):
					### Set the value of pathSuccessFlag to green text Connection Successful 
					self.pathSuccessFlag.setValue('<span style="color:green">File found</span>')
				else:
					### Set the value of pathSuccessFlag to green text Connection failed
					self.pathSuccessFlag.setValue('<span style="color:red">File not found</span>')
			else:
				### Check whether file exists
				if os.path.isfile(self.filePath.value()):
					### Set the value of pathSuccessFlag to green text Connection Successful 
					self.pathSuccessFlag.setValue('<span style="color:green">File found but not in shared folder, might not work for all OS</span>')
				else:
					### Set the value of pathSuccessFlag to green text Connection failed
					self.pathSuccessFlag.setValue('<span style="color:red">File not found</span>')
			self.pathSuccessFlag.setVisible(True)
			### Take the output of self.response and make it into a hqPath for submission to the server
			self.hqFilePath = self.response
			print(self.hqPath)
		elif knob is self.addressTest:
			### Get a response from the function of the button that was pressed
			self.response = self.serverRop.doesHQServerExists(self.serverAddress.value())
			### If there is a response do thing
			if self.response == True:
				### Set the value of addressSuccessFlag to green text Connection Successful 
				self.addressSuccessFlag.setValue('<span style="color:green">Connection Successful</span>')
			else:
				### Set the value of addressSuccessFlag to green text Connection failed
				self.addressSuccessFlag.setValue('<span style="color:red">Connection failed</span>')
			### Set the address success text flag to visible
			self.addressSuccessFlag.setVisible(True)
		elif knob is self.clientGet:
			### Get a response from the function of the button that was pressed
			self.response = self.serverRop.getClients(self.serverAddress.value())
			### If there is a response do thing
			if self.response:
				### reveal the client list and the client select button
				self.clientList.setVisible(True)
				self.clientSelect.setVisible(True)
				### Generate a interrum string for future use
				self.clientGetInterrum = ""
				### For loop to extract the computer names into a string with newlines
				for x in range(len(self.response)):
					self.clientGetInterrum+=str(self.response[x]+"\n")
				### set the value of clientList to the interrum string generated from the array for loop and remove the last newline for neatness
				self.clientList.setValue(self.clientGetInterrum[:-1])
		elif knob is self.clientGroupGet:
			### Get a response from the function of the button that was pressed
			self.response = self.serverRop.getClientGroups(self.serverAddress.value())
			### If there is a response do thing
			if self.response:
				### reveal the client list and the client select button
				self.clientList.setVisible(True)
				self.clientSelect.setVisible(True)
				### Generate a interrum string for future use
				self.clientGetGroupInterrum = ""
				### For loop to extract the computer names into a string with newlines
				for x in self.response:
					self.clientGetGroupInterrum+=str(x["name"]+"\n")
				### set the value of clientList to the interrum string generated from the array for loop and remove the last newline for neatness
				self.clientList.setValue(self.clientGetGroupInterrum[:-1])
		elif knob is self.clientSelect:
			### Hide the client selection button and the client list
			self.clientSelect.setVisible(False)
			self.clientList.setVisible(False)
			self.clientSelectInterrum = self.clientList.value().replace("\n", " ")

### Run to open a window in Maya
class mayaWindow(object):
		
	### Create a window in the maya gui
	def __init__(self):
		print("Not currently supported")
		sys.exit

class nativeWindow(object):
		
	### Create a window in the native gui
	def __init__(self):
		print("Not currently supported")
		sys.exit

########################################################################################################################################################################################################
############################################ Main code
########################################################################################################################################################################################################

### Run the programCheck class method
guiProgram = programCheck()

### Not sure if I want to just call guiProgram.gui().showModal() or assign it to a variable then call that. Will go with the assign variable for now
### Attempt to initiate the current window
#guiProgram.gui().showModal()
currentWindow = guiProgram.gui()
currentWindow.showModal()