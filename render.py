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

	def getBaseParameters():
		"""Return a dictionary of the base parameters used by all HQueue ROPs."""
		parms = {
			"name" : hou.ch("hq_job_name").strip(),
			"assign_to" : hou.parm("hq_assign_to").evalAsString(),
			"clients": hou.ch("hq_clients").strip(),
			"client_groups" : hou.ch("hq_client_groups").strip(),
			"dirs_to_create": getDirectoriesToCreate(hou.pwd(), expand=False),
			"environment" : getEnvVariablesToSet(hou.pwd()),
			"hfs": getUnexpandedStringParmVal(hou.parm("hq_hfs")),
			"hq_server": hou.ch("hq_server").strip(),
			"open_browser": hou.ch("hq_openbrowser"),
			"priority": hou.ch("hq_priority"),
			"hip_action": hou.ch("hq_hip_action"),
			"autosave": hou.ch("hq_autosave"),
			"warn_unsaved_changes": hou.ch("hq_warn_unsaved_changes"),
			"report_submitted_job_id": hou.ch("hq_report_submitted_job_id"),
		}
    
		addSubmittedByParm(parms)

		# Get the .hip file path.
		if parms["hip_action"] == "use_current_hip":
		    parms["hip_file"] = hou.hipFile.path()
		elif parms["hip_action"] == "use_target_hip":
		    parms["hip_file"] = getUnexpandedStringParmVal(hou.parm("hq_hip"))
		elif parms["hip_action"] == "copy_to_shared_folder": 
			# Get the target project directory from the project path parameter.
			# We need to resolve $HQROOT if it exists in the parameter value.
			# To do that, we temporarily set $HQROOT, evaluate the parameter,
			# and then unset $HQROOT.
			old_hq_root = hou.hscript("echo $HQROOT")[0].strip()
			hq_root = expandHQROOT("$HQROOT", parms["hq_server"])
			hou.hscript("set HQROOT=%s" % hq_root)
			target_dir = hou.parm("hq_project_path").eval().strip()
			if old_hq_root != "":
				hou.hscript("set HQROOT=%s" % old_hq_root)
			else:
				hou.hscript("set -u HQROOT")
			if target_dir[-1] != "/":
				target_dir = target_dir + "/"

			# Set the target .hip file path.
			parms["hip_file"] = target_dir + os.path.basename(hou.hipFile.name())

			# When copying to the shared folder,
			# we always create a new .hip file.
			parms["hip_file"] = _getNewHipFilePath(parms["hip_file"])
		else:
			pass

		# Setup email parameters
		if hou.ch("hq_will_email"):
			# We remove the whitespace around each email entry
			parms["emailTo"] = ",".join([email.strip() for email in 
										 hou.ch("hq_emailTo").split(',')])

			# The values added to parms for why emails should be sent are 
			# place holders.
			# When jobSend is ran they are updated as we need a server connection
			# to add the values we want.
			email_reasons = []

			if hou.ch("hq_email_on_start"):
				email_reasons.append("start")

			if hou.ch("hq_email_on_success"):
				email_reasons.append("success")

			if hou.ch("hq_email_on_failure"):
				email_reasons.append("failure")

			if hou.ch("hq_email_on_pause"):
				email_reasons.append("pause")

			if hou.ch("hq_email_on_resume"):
				email_reasons.append("resume")

			if hou.ch("hq_email_on_reschedule"):
				email_reasons.append("reschedule")

			if hou.ch("hq_email_on_priority_change"):
				email_reasons.append("priority change")

			parms["emailReasons"] = email_reasons
		else:
			parms["emailTo"] = ""
			# An empty list for emailReasons means no email will be sent
			parms["emailReasons"] = []


		return parms

	def addSubmittedByParm(parms):
		"""Adds who submits the job to the base parameters."""
		try:
			parms["submittedBy"] = getpass.getuser()
		except (ImportError, KeyError):
			pass

	def setupEmailReasons(server_connection, job_spec):
		"""Changes the placeholder string in the emailReasons part of the job
		spec with the actual string that will be sent.
		Gives a warning message if any of the options do not exist on the 
		server side.
		"""
		placeholder_reasons = job_spec["emailReasons"]
		new_reasons = []
		failure_messages = []


		for reason in placeholder_reasons:
			try:
				if reason == "start":
					new_reasons.extend(
						server_connection.getStartedJobEventNames())
				elif reason == "success":
					new_reasons.extend(server_connection.getSucceededStatusNames())
				elif reason == "failure":
					new_reasons.extend(server_connection.getFailedJobStatusNames())
				elif reason == "pause":
					new_reasons.extend(server_connection.getPausedJobStatusNames())
				elif reason == "resume":
					new_reasons.extend(server_connection.getResumedEventNames())
				elif reason == "reschedule":
					new_reasons.extend(
					server_connection.getRescheduledEventNames())
				elif reason == "priority change":
					new_reasons.extend(
					server_connection.getPriorityChangedEventNames())
				else:
					raise Exception("Did not recieve valid placeholder reason " + 
									reason + ".")
			except xmlrpclib.Fault:
				failure_messages.append(string.capwords(reason))


		if failure_messages:
			if hou.isUIAvailable():
				base_failure_message = ("The server does not support sending "
				+ "email for the following reasons:")
				failure_message = "\n".join(failure_messages)
				failure_message = "\n".join([base_failure_message, failure_message])
				hou.ui.displayMessage(failure_message, 
									  severity = hou.severityType.Warning) 


		job_spec["emailReasons"] = ",".join(new_reasons)

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

	def buildContainingJobSpec(job_name, hq_cmds, parms, child_job,
							   apply_conditions_to_children=True):
		"""Return a job spec that submits the child job and waits for it.
		The job containing the child job will not run any command.
		"""
		job = {
			"name": job_name,
			"priority": child_job["priority"],
			"environment": {"HQCOMMANDS": hutil.json.utf8Dumps(hq_cmds)},
			"command": "",
			"children": [child_job],
			"emailTo": parms["emailTo"],
			"emailReasons": parms["emailReasons"],
		}

		if "submittedBy" in parms:
			job["submittedBy"] = parms["submittedBy"]

		# Add job assignment conditions if any.
		conditions = { "clients":"host", "client_groups":"hostgroup" }
		for cond_type in conditions.keys():
			job_cond_keyword = conditions[cond_type]
			if parms["assign_to"] == cond_type:
				job[job_cond_keyword] = parms[cond_type]
				if apply_conditions_to_children:
					for child_job in job["children"]:
						child_job[job_cond_keyword] = parms[cond_type]

		return job


	def getHQueueCommands(remote_hfs, num_cpus=0):
		"""Return the dictionary of commands to start hython, Python, and mantra.
		Return None if an error occurs when reading the commands
		from the HQueueCommands file.
		If `num_cpus` is greater than 0, then we add a -j option
		to each command so that the application is run with a maximum
		number of threads.
		"""
	
		self.hq_cmds = {}
		self.cmd_file = open(cmd_file_path, "r")
		self.cmd_name = None
		self.cmds = None
		self.continue_cmd = False
		for line in self.cmd_file:
			line = line.strip()
	
			# Check if we need to continue the current command.
			if self.continue_cmd:
				# Add line to current command.
				self.cmds = self.addLineToCommands(cmds, line)
				if line[-1] == "\\":
					self.continue_cmd = True
				else:
					self.cmds = self.finalizeCommands(cmd_name, cmds, remote_hfs, num_cpus)
					if self.cmds is None:
						return None
					self.hq_cmds[cmd_name] = self.cmds
					self.continue_cmd = False
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
			cmds = addLineToCommands(cmds, line)
			if line[-1] == "\\":
				continue_cmd = True
			else:
				cmds = _finalizeCommands(cmd_name, cmds, remote_hfs, num_cpus)
				if cmds is None:
					return None
				hq_cmds[cmd_name] = cmds
				continue_cmd = False
	
		return hq_cmds

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


	def addLineToCommands(cmds, line):
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


	def finalizeCommands(cmd_name, cmds, remote_hfs, num_cpus):
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

	def sendJob(hq_server, main_job, open_browser, report_submitted_job_id):
		"""Send the given job to the HQ server.
		If the ui is available, either display the HQ web interface or display the
		id of the submitted job depending on the value of `open_browser` and 
		'report_submitted_job_id'.
		"""
		import hou
		s = _connectToHQServer(hq_server)
		if s is None:
			return False

		# We do this here as we need a server connection
		setupEmailReasons(s, main_job)

		# If we're running as an HQueue job, make that job our parent job.
		try:
			ids = s.newjob(main_job, os.environ.get("JOBID"))
		except Exception, e:
			displayError("Could not submit job to '" + hq_server + "'.", e)
			return False
       
		# Don't open a browser window or try to display a popup message if we're
		# running from Houdini Batch.
		if not hou.isUIAvailable():
			return True

		jobId = ids[0]
		if not open_browser and report_submitted_job_id:
			buttonindex = hou.ui.displayMessage("Your job has been submitted (Job %i)." % jobId, buttons=("Open HQueue", "Ok"), default_choice=1 )

		if buttonindex == 0:
			open_browser = True

		if open_browser:
			url = "%(hq_server)s" % locals()
			webbrowser.open(url)

		return True

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
			### Take the output of self.response and make it into a hqFilePath for submission to the server
			self.hqFilePath = self.response
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