# Author: Josh Kelly

# Import needed modules and components
import os
import os.path
import sys
import xmlrpclib
import getpass
import io
import nuke
import nukescripts

# This chunk of code is lifted from hqrop.py and rewritten as neccessary #######################################################################
def expandHQROOT(path, hq_server):
    """Return the given file path with instances of $HQROOT expanded
    out to the mount point for the HQueue shared folder root."""
    # Get the HQueue root path.
    hq_root = getHQROOT(hq_server)
    if hq_root is None:
        return path

    expanded_path = path.replace("$HQROOT", hq_root)
    return expanded_path


def getHQROOT(hq_server):
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
    s = hQServerConnect(hq_server)
    if s is None:
        return None

    try:
        # Get the HQ root.
        hq_root = s.getHQRoot(platform)
    except:
        print("Could not retrieve $HQROOT from '" + hq_server + "'.")
        return None

    return hq_root

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

    print parms

def addSubmittedByParm(parms):
    """Adds who submits the job to the base parameters."""
    try:
        parms["submittedBy"] = getpass.getuser()
    except (ImportError, KeyError):
        pass

def getJobCommands(hq_cmds, cmd_key, script=None):
    """Return platform-specific job commands defined by `cmd_key` and `script`.

    Return a dictionary where the keys are the supported platforms
    (i.e. linux, windows, macosx) and the values are the shell commands to be
    executed for the job.  `cmd_key` is a key into the `hq_cmds` dictionary and
    should be either "hythonComands", "pythonCommands" or "mantraCommands".

    The optional `script` argument indicates whether the job should
    execute a script file.  If `script` is None, then the job should run
    the commands from hq_cmds[cmd_key] as-is.
    """
    linux_cmd_key = cmd_key + "Linux"
    win_cmd_key = cmd_key + "Windows"
    macosx_cmd_key = cmd_key + "Macosx"

    # Get Linux commands.  Default to platform-independent commands
    # if Linux commands do not exist.
    linux_cmds = hq_cmds[linux_cmd_key] if hq_cmds.has_key(linux_cmd_key) \
        else hq_cmds[cmd_key]

    # Get Windows commands.  Default to platform-independent commands
    # if Windows commands do no exist.
    win_cmds = hq_cmds[win_cmd_key] if hq_cmds.has_key(win_cmd_key) \
        else hq_cmds[cmd_key]

    # Get MacOSX commands.  Default to platform-independent commands
    # if MacOSX commands do no exist.
    macosx_cmds = hq_cmds[macosx_cmd_key] if hq_cmds.has_key(macosx_cmd_key) \
        else hq_cmds[cmd_key]

    if script is not None:
        # Get the HQueue scripts directory.
        linux_hq_scripts_dir = hqScriptsDirectory()
        macosx_hq_scripts_dir = hqScriptsDirectory()
        win_hq_scripts_dir = hutil.file.convertToWinPath(linux_hq_scripts_dir,
                                                         var_notation="!")

        linux_cmds = "%s %s/%s" % (linux_cmds, linux_hq_scripts_dir, script)
        macosx_cmds = "%s %s/%s" % (macosx_cmds, macosx_hq_scripts_dir, script)
        win_cmds = "%s \"%s\\%s\"" % (win_cmds, win_hq_scripts_dir, script)

    commands = {
        "linux": linux_cmds,
        "windows": win_cmds,
        "macosx": macosx_cmds
    }

    return commands


#################################################################################################################################################################################################

# Run to open a window in Nuke
class nukeWindow(nukescripts.PythonPanel):

    def __init__(self):
        # Init the panel with a name
        nukescripts.PythonPanel.__init__(self, "hQueue Nuke render submission panel")

        # Setup a text box for the job name
        self.jobName = nuke.String_Knob('jobName', 'Job Name: ')
        self.addKnob(self.jobName)

        # Gets the absolute file path for the currently open Nuke script, if nothing open then defaults to install directory
        self.absoluteFilePath = os.path.abspath(nuke.value("root.name"))

        # Setup a text box for the server address to be input into
        self.serverAddress = nuke.String_Knob('serverAddress', 'Server Address: ')
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
        self.installDirectory.setValue('$HQROOT/nuke_distros/hfs.$HQCLIENTARCH')
#        if nuke.EXE_PATH:
#            self.installDirectory.setValue(nuke.EXE_PATH)
        self.addKnob(self.installDirectory)

        # Setup a button to test the server address which will reveal the Connection Successful text
        self.installDirectoryCurrent = nuke.PyScript_Knob("installDirectoryCurrent", "Own install directory", "")
        self.addKnob(self.installDirectoryCurrent)

        # Setup the Client selection box as a drop down menu
        self.priorityLevels = ['1 (Lowest)', '2', '3', '4', '5 (Medium)', '6', '7', '8', '9', '10 (Highest)']
        self.priority = nuke.Enumeration_Knob('priority', 'Priority: ', self.priorityLevels)
        self.addKnob(self.priority)

        # Setup the Client selection box as a drop down menu
        self.clientSelectionTypes = {'Any Client': 'any', 'Selected Clients': 'clients', 'Clients from Listed Groups': 'client_groups'}
        self.clientTypes = ['Any Client', 'Selected Clients', 'Clients from Listed Groups']
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
                # Set the value of addressSuccessFlag to green text Connection Successful
                self.addressSuccessFlag.setValue('<span style="color:green">Connection Successful</span>')
            else:
                # Set the value of addressSuccessFlag to green text Connection failed
                self.addressSuccessFlag.setValue('<span style="color:red">Connection failed</span>')

            # Set the address success text flag to visible
            self.addressSuccessFlag.setVisible(True)

        elif knob is self.filePathCheck:
            # See if the file path has $HQROOT in it
            if "$HQROOT" in self.filePath.value():
                # Get a response from the function of the button that was pressed
                self.cleanPath = expandHQROOT(self.filePath.value(), self.serverAddress.value())
                self.response = self.cleanPath
                # Set the address success text flag to visible
                self.pathSuccessFlag.setVisible(True)
            elif getHQROOT(self.serverAddress.value()) in self.filePath.value():
                self.hqroot = getHQROOT(self.serverAddress.value())
                self.response = self.filePath.value().replace(self.hqroot, "$HQROOT")
            else:
                self.response = self.filePath.value()
            # Check if the file path exists
            if os.path.isfile(self.response):
                # Set the value of pathSuccessFlag to green text File found
                self.pathSuccessFlag.setValue('<span style="color:green">File found</span>')
            else:
                # Set the value of pathSuccessFlag to green text File not found
                self.pathSuccessFlag.setValue('<span style="color:red">File not found</span>')

            # Reveal the file result flag
            self.pathSuccessFlag.setVisible(True)
            # Take the output of self.response and make it into a hqFilePath for submission to the server
            self.hqFilePath = self.response

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
            self.response = getClients(self.serverAddress.value())
            self.cleanList = {}

            for i in range(0, len(self.response)):
                self.cleanList[self.response[i]] = self.response[i]

            # Call the function for popping up the popup
            self.clientInterrumList = self.popUpPanel()

        elif knob is self.clientGroupGet:
            # Get a response from the function of the button that was pressed
            self.response = getClientGroups(self.serverAddress.value())
            self.cleanList = {}

            for i in range(0, len(self.response)):
                self.cleanList[self.response[i]['name']] = self.response[i]

            # Call the function for popping up the popup
            self.clientInterrumList = self.popUpPanel()

        elif knob is self.submitJob:
            self.finaliseClientList()
            getBaseParameters(self.jobName.value(), self.assign_to.value(), self.clientFullList, self.clientGroupFullList, self.installDirectory.value(), self.serverAddress.value(), self.priority.value())

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

    def popUpPanel(self):
        # If there is a response do thing
        if self.response:

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