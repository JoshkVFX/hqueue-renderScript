# Author: Josh Kelly

# Import needed modules and components
import os
import os.path
import sys
import xmlrpclib
import getpass
import io
import json
import nuke
import nukescripts

configLocation = os.path.join(os.environ['HOME'], ".hQueueConfig.dat")
defaultServerAddress = 'localhost:5000'

# This chunk of code is lifted from hqrop.py and rewritten as neccessary #######################################################################
def expandHQROOT(path, hq_server):
    """Return the given file path with instances of $HQROOT expanded
    out to the mount point for the HQueue shared folder root."""
    # Get the HQueue root path.
    hq_root = getHQROOT(hq_server)[0]
    if hq_root is None:
        return path

    expanded_path = {
        'windows': path.replace("$HQROOT", hq_root['windows']),
        'linux': path.replace("$HQROOT", hq_root['linux']),
        'macosx': path.replace("$HQROOT", hq_root['macosx'])
    }
    return expanded_path

def getHQROOT(hq_server):
    """Query the HQueue server and return the mount point path
    to the HQueue shared folder root.
    Return None if the path cannot be retrieved from the server.
    """
    # Identify this machine's platform.
    OSplatform = sys.platform
    if OSplatform.startswith("win"):
        OSplatform = "windows"
    elif OSplatform.startswith("linux"):
        OSplatform = "linux"
    elif OSplatform.startswith("darwin"):
        OSplatform = "macosx"

    # Connect to the HQueue server.
    s = hQServerConnect(hq_server)
    if s is None:
        return None

    try:
        # Get the HQ root for all platforms.
        hq_root = {
            'windows': s.getHQRoot('windows'),
            'linux': s.getHQRoot('linux'),
            'macosx': s.getHQRoot('macosx')
        }
    except:
        print("Could not retrieve $HQROOT from '" + hq_server + "'.")
        return None

    return [hq_root, OSplatform]

def hqServerProxySetup(hq_server):
    """Sets up a xmlrpclib server proxy to the given HQ server."""
    if not hq_server.startswith("http://"):
        full_hq_server_path = "http://%s" % hq_server
    else:
        full_hq_server_path = hq_server

    return xmlrpclib.ServerProxy(full_hq_server_path, allow_none=True)

def doesHQServerExists(hq_server):
    """Check that the given HQ server can be connected to.
    Returns True if the server exists and False if it does not. Furthermore,
    it will display an error message if it does not exists."""
    server = hqServerProxySetup(hq_server)
    return hQServerPing(server, hq_server)

def hQServerConnect(hq_server):
    """Connect to the HQueue server and return the proxy connection."""
    s = hqServerProxySetup(hq_server)

    if hQServerPing(s, hq_server):
        return s
    else:
        return None

def hQServerPing(server, hq_server):
    try:
        server.ping()
        return True
    except:
        print("Could not connect to '" + hq_server + "'.\n\n"
            + "Make sure that the HQueue server is running\n"
            + "or change the value of 'HQueue Server'.",
            TypeError("this is a type error"))

        return False

def getClients(hq_server):
    """Return a list of all the clients registered on the HQueue server.
    Return None if the client list could not be retrieved from the server.
    """
    s = hQServerConnect(hq_server)

    if s is None:
        return None

    try:
        client_ids = None
        attribs = ["id", "hostname"]
        clients = s.getClients(client_ids, attribs)
    except:
        print("Could not retrieve client list from '" + hq_server + "'.")
        return None

    return [client["hostname"] for client in clients]

def getClientGroups(hq_server):
    """Return a list of all the client groups on the HQueue server.
    Return None if the client group list could not be retrieved from the server.
    """
    s = hQServerConnect(hq_server)
    if s is None:
        return None

    try:
        client_groups = s.getClientGroups()
    except:
        print("Could not retrieve client group list from '"
                    + hq_server + "'.")
        return None

    return client_groups

def getBaseParameters(name, assigned_to, clientList, clientGroupList, installDir, serverAddress, priorityLevel):
    """Return a dictionary of the base parameters used in this nuke script"""
    parms = {
        "name": name,
        "assign_to": assigned_to,
        "clients": clientList,
        "client_groups": clientGroupList,
        "dirs_to_create": "",
        "environment": "",
        "hfs": installDir,
        "hq_server": serverAddress,
        "open_browser": "",
        "priority": priorityLevel,
        "hip_action": "",
        "autosave": "",
        "warn_unsaved_changes": "",
        "report_submitted_job_id": "",
    }

    addSubmittedByParm(parms)

    return parms

def addSubmittedByParm(parms):
    """Adds who submits the job to the base parameters."""
    try:
        parms["submittedBy"] = getpass.getuser()
    except (ImportError, KeyError):
        pass

def buildContainingJobSpec(job_name, parms, child_jobs, child_job,
                           apply_conditions_to_children=True):
    """Return a job spec that submits the child job and waits for it.
    The job containing the child job will not run any command.
    """
    job = {
        "name": job_name,
        "priority": parms['priority'],
#        "environment": {"HQCOMMANDS": hutil.json.utf8Dumps(hq_cmds)},
        "command": "",
        "children": child_jobs,
#        "emailTo": parms["emailTo"],
#        "emailReasons": parms["emailReasons"],
    }

    if "submittedBy" in parms:
        job["submittedBy"] = parms["submittedBy"]

    # Add job assignment conditions if any.
    conditions = {"clients": "host", "client_groups": "hostgroup"}
    for cond_type in conditions.keys():
        job_cond_keyword = conditions[cond_type]
        if parms["assign_to"] == cond_type:
            job[job_cond_keyword] = parms[cond_type]
            if apply_conditions_to_children:
                for child_job in job["children"]:
                    child_job[job_cond_keyword] = parms[cond_type]

    return job

def buildOSCommands(HFS, startFrame, endFrame, fileName):
    commands = {
        # Example: nuke.exe -F 1-100 -x myscript.nk
        "linux": HFS['linux']+" -F "+str(startFrame)+"-"+str(endFrame)+" -x "+fileName['linux'],
        "windows": HFS['windows']+" -F "+str(startFrame)+"-"+str(endFrame)+" -x "+fileName['windows'],
        "macosx": HFS['macosx']+" -F "+str(startFrame)+"-"+str(endFrame)+" -x "+fileName['macosx'],
    }

    return commands

def buildChildJobs(jobName, OSCommands, priority):
    job_spec = {
        "name": jobName,
        "command": OSCommands,
        "priority": priority,
        "tags": '',
#        "maxHosts": 1,
#        "minHosts": 1,
        "command": OSCommands,
    }
    return job_spec

def sendJob(hq_server, main_job):
    s = hQServerConnect(hq_server)
    if s is None:
        return False

    # We do this here as we need a server connection
    #_setupEmailReasons(s, main_job)

    # If we're running as an HQueue job, make that job our parent job.
    try:
        ids = s.newjob(main_job)
    except Exception, e:
        print "Could not submit job:", main_job['name'], "to", hq_server
        return False

#    jobId = ids[0]
    return ids

def getFrameWord(frames):
    if len(frames) == 1:
        return "Frame"
    else:
        return "Frames"

#def submitTestJob():
#    OSCommands = {
#        "linux": "echo Linux!",
#        "windows": "echo Windows!",
#        "macosx": "echo Mac!"
#    }
3    # Setup test job for testing submissions
#    job_spec = {
#        "name": "Test Job 1",
#        "command": OSCommands,
#        "tags": '',
##        "maxHosts": 1,
##        "minHosts": 1,
#    }
#    child_job = job_spec
#    job_spec = {
#        "name": "Test1",
#        "priority": 5,
#        "environment": "",
#        "command": "",
#        "children": [child_job],
##        "emailTo": parms["emailTo"],
##        "emailReasons": parms["emailReasons"],
#    }
#    s = hQServerConnect("localhost:5000")
#    jobId = s.newjob(job_spec)
#    print jobId

#################################################################################################################################################################################################

# Run to open a window in Nuke
class nukeWindow(nukescripts.PythonPanel):

    def __init__(self):
        # Init the panel with a name
        nukescripts.PythonPanel.__init__(self, "hQueue Nuke render submission panel")

        # Setup a text box for the job name
        self.jobName = nuke.String_Knob('jobName', 'Job Name: ', '<default>')
        self.addKnob(self.jobName)

        # Gets the absolute file path for the currently open Nuke script, if nothing open then defaults to install directory
        self.absoluteFilePath = os.path.abspath(nuke.value("root.name"))

        # Setup a text box for the server address to be input into
        self.serverAddress = nuke.String_Knob('serverAddress', 'Server Address: ')
        self.serverAddress.setValue(retrieveConfigCache())
        self.addKnob(self.serverAddress)

        # Setup a button to test the server address which will reveal the Connection Successful text
        self.addressTest = nuke.PyScript_Knob("addressTest", "Test the server address", "")
        self.addKnob(self.addressTest)

        # Create addressSuccessFlag flag that is hidden until the server is successfully pinged
        self.addressSuccessFlag = nuke.Text_Knob('addressSuccessFlag', '', '<span style="color:green">Connection Successful</span>')
        self.addressSuccessFlag.setFlag(nuke.STARTLINE)
        self.addressSuccessFlag.setVisible(False)
        self.addKnob(self.addressSuccessFlag)

        # Get the filepath from self.absoluteFilePath and put it into a text box
        self.filePath = nuke.String_Knob('filePath', 'File Path: ', self.absoluteFilePath)
        self.addKnob(self.filePath)

        # Create a button that will test the file path for an nuke script
        self.filePathCheck = nuke.PyScript_Knob("filePathCheck", "Test the File Path", "")
        self.addKnob(self.filePathCheck)

        # Create pathSuccessFlag flag that is hidden until the file path is verified
        self.pathSuccessFlag = nuke.Text_Knob('pathSuccessFlag', '', '<span style="color:green">Connection Successful</span>')
        self.pathSuccessFlag.setFlag(nuke.STARTLINE)
        self.pathSuccessFlag.setVisible(False)
        self.addKnob(self.pathSuccessFlag)

        # Setup a text box for the server address to be input into
        self.installDirectory = nuke.String_Knob('installDirectory', 'Nuke Install Directory: ')
        self.installDirectory.setValue('$HQROOT/nuke_distros/$OS-Nuke'+str(nuke.NUKE_VERSION_STRING))
        self.addKnob(self.installDirectory)

        # Setup a button to test the server address which will reveal the Connection Successful text
        self.installDirectoryCurrent = nuke.PyScript_Knob("installDirectoryCurrent", "Own install directory", "")
        self.addKnob(self.installDirectoryCurrent)

        # Setup the Client selection box as a drop down menu
        self.priorityLevels = ['1 (Lowest)', '2', '3', '4', '5 (Medium)', '6', '7', '8', '9', '10 (Highest)']
        self.priority = nuke.Enumeration_Knob('priority', 'Priority: ', self.priorityLevels)
        self.priority.setValue(self.priorityLevels[4])
        self.addKnob(self.priority)

        # Setup the Client selection box as a drop down menu
        self.clientSelectionTypes = {'Any Client': 'any', 'Selected Clients': 'clients', 'Clients from Listed Groups': 'client_groups'}
        self.clientTypes = ['Any Client'] #, 'Selected Clients', 'Clients from Listed Groups']
        self.assign_to = nuke.Enumeration_Knob('nodes', 'Assigned nodes', self.clientTypes)
        self.addKnob(self.assign_to)

        # Setup the box that will display the chosen clients
        self.clientList = nuke.String_Knob('clientList', 'Clients: ', '')
        self.clientList.setFlag(nuke.STARTLINE)
        self.clientList.setVisible(False)
        self.addKnob(self.clientList)

        # Setup the get client list button, which will use hqrop functions
        self.clientGet = nuke.PyScript_Knob("clientGet", "Get client list", "")
        self.clientGet.setVisible(False)
        self.addKnob(self.clientGet)

        # Setup the get client groups button, which will use hqrop functions
        self.clientGroupGet = nuke.PyScript_Knob("clientGroupGet", "Get client groups", "")
        self.clientGroupGet.setVisible(False)
        self.addKnob(self.clientGroupGet)

        # Setup a frame range with the default frame range of the scene
        self.fRange = nuke.String_Knob('fRange', 'Track Range', '%s-%s' % (nuke.root().firstFrame(), nuke.root().lastFrame()))
        self.addKnob(self.fRange)

        # Setup a button to test the server address which will reveal the Connection Successful text
        self.submitJob = nuke.PyScript_Knob("submitJob", "Submit job to farm", "")
        self.submitJob.setFlag(nuke.STARTLINE)
        self.addKnob(self.submitJob)

        # Set the minimum size of the python panel
        self.setMinimumSize(500, 600)

    def knobChanged(self, knob):
        # When you press a button run the command attached to that button
        self.response = ""

        # Figure out which knob was changed
        if knob is self.addressTest:
            # Get a response from the function of the button that was pressed
            self.response = doesHQServerExists(self.serverAddress.value())

            # If there is a response do thing
            if self.response == True:
                # Write out the server address to a a hidden file
                writeConfigCache(self.serverAddress.value())
                # Set the value of addressSuccessFlag to green text Connection Successful
                self.addressSuccessFlag.setValue('<span style="color:green">Connection Successful</span>')
            else:
                # Set the value of addressSuccessFlag to green text Connection failed
                self.addressSuccessFlag.setValue('<span style="color:red">Connection failed</span>')

            # Set the address success text flag to visible
            self.addressSuccessFlag.setVisible(True)

        elif knob is self.filePathCheck:
            self.sysHQInfo = getHQROOT(self.serverAddress.value())
            self.hqRoot = self.sysHQInfo[0]
            self.platform = self.sysHQInfo[1]
            # See if the file path has $HQROOT in it
            if "$HQROOT" in self.filePath.value():
                # Set the platforms file value to the resolved path
                self.fileResponse = {
                    'windows': self.filePath.value().replace("$HQROOT", self.hqRoot['windows']),
                    'macosx': self.filePath.value().replace("$HQROOT", self.hqRoot['macosx']),
                    'linux': self.filePath.value().replace("$HQROOT", self.hqRoot['linux']),
                    'hq': self.filePath.value()
                }
            elif self.hqRoot['linux'] in self.filePath.value() or self.hqRoot['macosx'] in self.filePath.value() or self.hqRoot['windows'] in self.filePath.value():
                self.fileResponse = {
                    'windows': self.filePath.value().replace(self.hqRoot[self.platform], self.hqRoot['windows']),
                    'macosx': self.filePath.value().replace(self.hqRoot[self.platform], self.hqRoot['macosx']),
                    'linux': self.filePath.value().replace(self.hqRoot[self.platform], self.hqRoot['linux']),
                    'hq': self.filePath.value().replace(self.hqRoot['linux'], "$HQROOT").replace(self.hqRoot['macosx'], "$HQROOT").replace(self.hqRoot['windows'], "$HQROOT")
                }
            else:
                self.fileResponse = {
                    'windows': self.filePath.value(),
                    'macosx': self.filePath.value(),
                    'linux': self.filePath.value(),
                    'hq': self.filePath.value()
                }

            # Check if the file path exists
            if os.path.isfile(self.fileResponse[self.platform]) or os.path.isfile(self.fileResponse['hq']):
                # Set the value of pathSuccessFlag to green text File found
                self.pathSuccessFlag.setValue('<span style="color:green">File found</span>')
            else:
                # Set the value of pathSuccessFlag to green text File not found
                self.pathSuccessFlag.setValue('<span style="color:red">File not found</span>')
            # Reveal the file result flag
            self.pathSuccessFlag.setVisible(True)

        elif knob is self.installDirectoryCurrent:
            self.installDirectory.setValue(nuke.EXE_PATH)

        elif knob is self.assign_to:
            if self.assign_to.value() == "Selected Clients":
                self.clientList.setVisible(True)
                self.clientGet.setVisible(True)
                self.clientGroupGet.setVisible(False)
            elif self.assign_to.value() == "Clients from Listed Groups":
                self.clientList.setVisible(True)
                self.clientGet.setVisible(False)
                self.clientGroupGet.setVisible(True)
            elif self.assign_to.value() == "Any Client":
                self.clientList.setVisible(False)
                self.clientGet.setVisible(False)
                self.clientGroupGet.setVisible(False)

        elif knob is self.clientGet:
            # Get a response from the function of the button that was pressed
            self.clientResponse = getClients(self.serverAddress.value())
            self.cleanList = {}

            for i in range(0, len(self.clientResponse)):
                self.cleanList[self.clientResponse[i]] = self.clientResponse[i]

            # Call the function for popping up the popup
            self.clientInterrumList = self.popUpPanel(self.clientResponse)

        elif knob is self.clientGroupGet:
            # Get a response from the function of the button that was pressed
            self.clientGroupResponse = getClientGroups(self.serverAddress.value())
            self.cleanList = {}

            for i in range(0, len(self.clientGroupResponse)):
                self.cleanList[self.clientGroupResponse[i]['name']] = self.clientGroupResponse[i]

            # Call the function for popping up the popup
            self.clientInterrumList = self.popUpPanel(self.clientGroupResponse)

        elif knob is self.submitJob:
            self.parms = self.finaliseJobSpecs()
            self.childJobs = []
            for i in range(int(self.fRange.value().split('-')[0]), int(self.fRange.value().split('-')[1])+1):
                self.childJobs.append(buildChildJobs("Frame Range_"+str(i)+"-"+str(i), buildOSCommands(self.parms['hfs'], i, i, self.fileResponse), self.parms['priority']))
            try:
                self.mainJob = buildContainingJobSpec(self.parms['name'], self.parms, self.childJobs, self.childJobs[0])
            except:
                raise ValueError("Frame range is invalid")
            self.jobResponse = sendJob(self.parms['hq_server'], self.mainJob)
            if self.jobResponse:
                print "Successful"
            else:
                print "Failed"

    def finaliseJobSpecs(self):
        self.finaliseClientList()
        try:
            if self.hqRoot:
                pass
        except:
            self.knobChanged(self.filePathCheck)
        return getBaseParameters(self.jobNameSet(self.jobName.value(), self.fileResponse['hq']), self.assigned_to, \
                                 self.clientFullList, self.clientGroupFullList, \
                                 self.cleanInstallEXE(self.installDirectory.value()), self.serverAddress.value(), self.priority.value())

    def cleanInstallEXE(self, unusableDir):
        usableDir = {
            'linux': os.path.join(unusableDir.replace("$HQROOT", self.hqRoot['linux']).replace("$OS", self.platform), os.path.split(nuke.EXE_PATH)[1]),
            'windows': os.path.join(unusableDir.replace("$HQROOT", self.hqRoot['windows']).replace("$OS", self.platform), os.path.split(nuke.EXE_PATH)[1]+'.exe'),
            'macosx': os.path.join(unusableDir.replace("$HQROOT", self.hqRoot['macosx']).replace("$OS", self.platform), os.path.split(nuke.EXE_PATH)[1])
        }
        return usableDir

    def jobNameSet(self, jobName, FilePath):
        if jobName == "<default>":
            return "Render -> NK: "+FilePath
        else:
            return jobName

    def finaliseClientList(self):
        if self.assign_to.value() == "Any Client":
            self.assigned_to = self.clientSelectionTypes["Any Client"]
            self.clientFullList = []
            self.clientGroupFullList = []
        elif self.assign_to.value() == "Selected Clients":
            self.assigned_to = self.clientSelectionTypes["Selected Clients"]
            # Create a list using the clientList names to generate a list that can be sent with the job
            self.clientFullList = []
            self.clientGroupFullList = []
            for i in self.clientList.value():
                print i
                print self.cleanList[i]
                self.clientFullList.append(self.cleanList[i])
            print self.clientFullList
        elif self.assign_to.value() == "Clients from Listed Groups":
            # Create a list using the clientList names to generate a list that can be sent with the job
            self.clientFullList = []
            self.clientGroupFullList = []
            for i in self.clientList.value():
                print i
                print self.cleanList[i]
                self.clientGroupFullList.append(self.cleanList[i])
            print self.clientGroupFullList

    def popUpPanel(self, response):
        # If there is a response do thing
        if response:

            # reveal the client list and the client select button
            self.clientSelectPopUp = clientSelectionPanel()
            self.clientSelectPopUp.clientInterrumList.setValue(', '.join(self.cleanList.keys()))
            self.clientSelectPopUp.showModal()

            # set the value of clientList to the interrum string generated from the array for loop
            self.clientList.setValue(self.clientSelectPopUp.clientInterrumList.value())

class clientSelectionPanel(nukescripts.PythonPanel):
    def __init__(self):
        nukescripts.PythonPanel.__init__(self, 'Client select')

        # Setup a multiline client list that appears when clientGet is run
        self.clientInterrumList = nuke.Multiline_Eval_String_Knob('clientInterrumList', 'Client List: ')
        self.addKnob(self.clientInterrumList)

    def knobChanged(self, knob):
        if knob == "OK":
            print "OK"
        else:
            print knob
            print "KNOB ^^^"
            return self.clientInterrumList

def retrieveConfigCache():
    if os.path.isfile(configLocation):
        with open(configLocation, 'r') as f:
            config = json.load(f)
        return config['Server Address']
    else:
        return defaultServerAddress

def writeConfigCache(serverAddress):
    config = {'Server Address': serverAddress}
    with open(configLocation, 'w') as f:
        json.dump(config, f)

#class nukeAdvancedWindow(nukescripts.PythonPanel):
#    def __init__(self):
#        # Init the panel with a name
#        nukescripts.PythonPanel.__init__(self, "hQueue Advanced Nuke render submission panel")

##################################################################################################################################################################################################
############################################ Main code
##################################################################################################################################################################################################

def runGui():
    currentWindow = nukeWindow()
    currentWindow.showModal()