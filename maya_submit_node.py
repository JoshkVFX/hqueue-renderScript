# Author: Josh Kelly

# Import needed modules and components
import os
import os.path
import sys
import xmlrpclib
import getpass
import json
import posixpath
import maya.cmds as cmds

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

def buildContainingJobSpec(job_name, parms, child_jobs,
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
#            job[job_cond_keyword] = 'josh-laptop'
            job[job_cond_keyword] = parms[cond_type]
            if apply_conditions_to_children:
                for child_job in job["children"]:
                    child_job[job_cond_keyword] = parms[cond_type]

    return job

def buildOSCommands(MFS, startFrame, endFrame, fileName):
    commands = {
        # Example: nuke.exe -F 1-100 -x myscript.nk
        "linux": MFS['linux']+" -r "+cmds.optionMenuGrp('renderChoice', q=True, value=True)+" -s "+str(startFrame)+" -e "+str(endFrame)+" -b 1 -proj "+'"'+'/'.join(fileName['linux'].strip('"').split('/')[:-2])+'" '+fileName['linux'],
        "windows": MFS['windows']+" -r "+cmds.optionMenuGrp('renderChoice', q=True, value=True)+" -s "+str(startFrame)+" -e "+str(endFrame)+" -b 1 -proj "+'"'+'\\'.join(fileName['windows'].strip('"').split('\\')[:-2])+'" '+fileName['windows'],
        "macosx": MFS['macosx']+" -r "+cmds.optionMenuGrp('renderChoice', q=True, value=True)+" -s "+str(startFrame)+" -e "+str(endFrame)+" -b 1 -proj "+'"'+'/'.join(fileName['windows'].strip('"').split('/')[:-2])+'" '+fileName['macosx']
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

    return ids

def getFrameWord(frames):
    if len(frames) == 1:
        return "Frame"
    else:
        return "Frames"

#################################################################################################################################################################################################
#### CONFIG FUNCTIONS

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
    return True

def getMayaRenderers():
    return cmds.renderer(q=1, namesOfAvailableRenderers=1),cmds.getAttr("defaultRenderGlobals.currentRenderer")

#################################################################################################################################################################################################

### C:/Program Files/Autodesk/Maya2011/devkit/plug-ins/scripted


class createMyLayoutCls(object):
    def __init__(self, *args):
        pass

    def show(self):
        self.createMyLayout()

    def createMyLayout(self):

        # check to see if our window exists
        if cmds.window('hQueueSubmit', exists=True):
            cmds.deleteUI('hQueueSubmit')

        self.window = cmds.window('hQueueSubmit', widthHeight=(500, 600), title="hQueue Maya render submission panel",
                                  resizeToFitChildren=1)

        cmds.columnLayout('hQueueWindowLayout', adjustableColumn=True, columnAlign="center") #, rowSpacing=10)

        self.jobName = cmds.textFieldGrp('jobName', label="Job name: ", text="<default>")

        self.serverAddress = cmds.textFieldButtonGrp('serverAddress', label="Server Address: ",
                                                     text=retrieveConfigCache(),
                                                     buttonLabel="Test the server Address",
                                                     buttonCommand=self.serverAddressConnect)

        self.filePath = cmds.textFieldButtonGrp('filePath', label="File path: ",
                                                text=cmds.file(q=True, location=True),
                                                buttonLabel="Test the file path",
                                                buttonCommand=self.filePathCheck)

        self.installDirectoryChoicesKey = {'HQRoot install directory': '$HQROOT/maya_distros/$OS-Maya' + str(cmds.about(version=True)),
                                           'Default install directory': os.environ['MAYA_LOCATION'],
                                           'Custom install directory': ''}
        self.installDirectoryChoices = ['HQRoot install directory', 'Default install directory', 'Custom install directory']
        self.installDirectoryCurrent = cmds.optionMenuGrp('installDirectoryCurrent', label="NFS Directory: ",
                                                          changeCommand=self.installDirectoryChoicesChange)
        for i in self.installDirectoryChoices:
            cmds.menuItem(label=i)

        self.installDirectory = cmds.textFieldGrp('installDirectory', label="Maya Install Directory: ",
                                                   text=self.installDirectoryChoicesKey[cmds.optionMenuGrp(
                                                       self.installDirectoryCurrent, q=True, value=True)])

        self.priorityLevels = ['1 (Lowest)', '2', '3', '4', '5 (Medium)', '6', '7', '8', '9', '10 (Highest)']
        self.priority = cmds.optionMenuGrp('priority', label="Priority: ")
        for i in self.priorityLevels:
            cmds.menuItem(label=i)
        cmds.optionMenuGrp(self.priority, edit=True, select=5)

        self.clientSelectionTypes = {'Any Client': 'any', 'Selected Clients': 'clients', 'Clients from Listed Groups': 'client_groups'}
        self.clientTypes = ['Any Client', 'Selected Clients', 'Clients from Listed Groups']
        self.assign_to = cmds.optionMenuGrp('assign_to', label="Assigned nodes: ", changeCommand=self.assignedToChange)
        for i in self.clientTypes:
            cmds.menuItem(label=i)

        self.clientGet = cmds.textFieldButtonGrp('clientGet', label="Clients: ", buttonLabel="Get client list",
                                                 buttonCommand=self.getClientList, visible=False)

        self.clientGroupGet = cmds.textFieldButtonGrp('clientGroupGet', label="Client groups: ",
                                                      buttonLabel="Get client groups",
                                                      buttonCommand=self.getClientGroupList, visible=False)

        self.trackRange = cmds.textFieldGrp('trackRange', label="Track Range: ", text=str(int(cmds.getAttr('defaultRenderGlobals.startFrame'))) + '-' + str(int(cmds.getAttr('defaultRenderGlobals.endFrame'))))

        (self.renderOptions,self.currentRenderer) = getMayaRenderers()
        self.renderChoice = cmds.optionMenuGrp('renderChoice', label="Renderer: ")
        for i in self.renderOptions:
            cmds.menuItem(label=i)

        cmds.optionMenuGrp('renderChoice', edit=True, value=self.currentRenderer)

        self.submitJob = cmds.button(label="Submit job to farm", recomputeSize=True, command=self.submitJobToFarm)

        cmds.setParent(menu=True)

        cmds.showWindow(self.window)

    def assignedToChange(self, *args):
        if args[0] == 'Any Client':
            cmds.textFieldButtonGrp(self.clientGet, edit=True, visible=False)
            cmds.textFieldButtonGrp(self.clientGroupGet, edit=True, visible=False)
        elif args[0] == 'Selected Clients':
            cmds.textFieldButtonGrp(self.clientGroupGet, edit=True, visible=False)
            cmds.textFieldButtonGrp(self.clientGet, edit=True, visible=True)
        elif args[0] == 'Clients from Listed Groups':
            cmds.textFieldButtonGrp(self.clientGet, edit=True, visible=False)
            cmds.textFieldButtonGrp(self.clientGroupGet, edit=True, visible=True)
        else:
            print "Unknown type:", args[0]
            raise ValueError

    def getClientList(self, *args):
        # Get a response from the function of the button that was pressed
        self.clientResponse = getClients(cmds.textFieldButtonGrp(self.serverAddress, q=True, text=True))

        self.clientListType = 'clientGet'

        self.cleanList = self.clientResponse

        # Call the function for popping up the popup
        self.popUpPanel(self)

    def getClientGroupList(self, *args):
        # Get a response from the function of the button that was pressed
        self.clientGroupResponse = getClientGroups(cmds.textFieldButtonGrp(self.serverAddress, q=True, text=True))
        self.cleanList = []

        self.clientListType = 'clientGroupGet'

        for i in range(0, len(self.clientGroupResponse)):
            self.cleanList.append(self.clientGroupResponse[i]['name'])

        # Call the function for popping up the popup
        self.popUpPanel(self)

    def popUpPanel(self, *args):
        # check to see if our window exists
        if cmds.window('clientList', exists=True):
            cmds.deleteUI('clientList')
        cmds.window('clientList', width=200, height=200, resizeToFitChildren=1)
        cmds.columnLayout(adjustableColumn=True, columnAlign="center")
        for i in self.cleanList:
            cmds.checkBox(i.replace('-', ''))
        cmds.button('acceptClientListButton', label='Accept', command=self.clientListAccept)
        cmds.popupMenu(alt=True, ctl=True)
        cmds.showWindow()

    def clientListAccept(self, *args):
        self.clientInterrumList = []
        for i in self.cleanList:
            if cmds.checkBox(i.replace('-', ''), q=True, value=True) is True:
                self.clientInterrumList.append(i)
        cmds.textFieldButtonGrp(self.clientListType, edit=True, text=', '.join(self.clientInterrumList))
        return True

    def cleanInstallEXE(self, unusableDir):
        if cmds.optionMenuGrp('installDirectoryCurrent', q=True, value=True) == "HQRoot install directory":
            usableDir = {
                'linux': posixpath.join(posixpath.join(unusableDir.replace("$HQROOT", '"'+self.hqRoot['linux']).replace("$OS", 'linux'), 'bin'), 'Render"'),
                'windows': posixpath.join(posixpath.join(unusableDir.replace("$HQROOT", '"'+self.hqRoot['windows']).replace("$OS", 'windows'), 'bin'), 'Render.exe"').replace('/', '\\'),
                'macosx': posixpath.join(posixpath.join(unusableDir.replace("$HQROOT", '"'+self.hqRoot['macosx']).replace("$OS", 'macosx'), 'bin'), 'Render"')
            }
        elif cmds.optionMenuGrp('installDirectory', q=True, value=True) == "Default install directory":
            mayaDirName = 'maya' + str(cmds.about(version=True))
            usableDir = {
                'linux': posixpath.join(posixpath.join(posixpath.join('"/usr/autodesk', mayaDirName), 'bin'), 'Render"'),
                'windows': posixpath.join(posixpath.join(posixpath.join('"C:\Program Files\Autodesk', mayaDirName), 'bin'), 'Render.exe"').replace('/', '\\'),
                'macosx': posixpath.join(posixpath.join(posixpath.join('"/Applications/Autodesk/', mayaDirName), '/Maya.app/Contents/bin'), 'Render"')
            }
        return usableDir

    def installDirectoryChoicesChange(self, *args):
        cmds.textFieldGrp('installDirectory', edit=True, text=self.installDirectoryChoicesKey[args[0]])

    def filePathCheck(self, *args):
        self.hQRootFilePathCheck()

        # Check if the file can be found at either of the possible file paths
        if os.path.isfile(self.fileResponse[self.platform].strip('"')) or os.path.isfile(self.fileResponse['hq'].strip('"')):
            # Set the background of filePath's text box to green if File found
            cmds.textFieldButtonGrp('filePath', edit=True, backgroundColor=(0, 0.8, 0))
            self.filePathSuccess=True
        else:
            # Set the background of filePath's text box to red if File not found
            cmds.textFieldButtonGrp('filePath', edit=True, backgroundColor=(0.8, 0, 0))
            self.filePathSuccess=None

    def hQRootFilePathCheck(self):
        (self.hqRoot, self.platform) = getHQROOT(cmds.textFieldButtonGrp(self.serverAddress, q=True, text=True))
        self.filePathValue = cmds.textFieldButtonGrp(self.filePath, q=True, text=True)
        # See if the file path has $HQROOT in it
        if "$HQROOT" in self.filePathValue:
            # Set the platforms file value to the resolved path
            self.fileResponse = {
                'windows': self.filePathValue.replace("$HQROOT", '"'+self.hqRoot['windows']).replace('/', '\\')+'"',
                'macosx': self.filePathValue.replace("$HQROOT", '"'+self.hqRoot['macosx']).replace('\\', '/')+'"',
                'linux': self.filePathValue.replace("$HQROOT", '"'+self.hqRoot['linux']).replace('\\', '/')+'"',
                'hq': '"'+self.filePathValue+'"'
            }
        elif self.hqRoot['linux'] in self.filePathValue or self.hqRoot['macosx'] in self.filePathValue or self.hqRoot['windows'].replace('\\', '/') in self.filePathValue:
            self.fileResponse = {
                'windows': self.filePathValue.replace(self.hqRoot[self.platform].replace('\\', '/'), '"'+self.hqRoot['windows']).replace('/',
                                                                                                                  '\\')+'"',
                'macosx': self.filePathValue.replace(self.hqRoot[self.platform].replace('\\', '/'), '"'+self.hqRoot['macosx']).replace('\\',
                                                                                                                '/')+'"',
                'linux': self.filePathValue.replace(self.hqRoot[self.platform].replace('\\', '/'), '"'+self.hqRoot['linux']).replace('\\',
                                                                                                              '/')+'"',
                'hq': self.filePathValue.replace(self.hqRoot['linux'], '"'+"$HQROOT").replace(self.hqRoot['macosx'], '"'+"$HQROOT").replace(self.hqRoot['windows'], '"'+"$HQROOT")+'"'
            }
        else:
            self.fileResponse = {
                'windows': '"'+self.filePathValue.replace('/', '\\')+'"',
                'macosx': '"'+self.filePathValue.replace('\\', '/')+'"',
                'linux': '"'+self.filePathValue.replace('\\', '/')+'"',
                'hq': '"'+self.filePathValue+'"'
            }

    def jobNameSet(self, jobName, FilePath):
        if jobName == "<default>":
            return "Render -> NK: "+FilePath
        else:
            return jobName

    def finaliseClientList(self):
        self.clientGroupFullList = ''
        self.clientFullList = ''
        self.assigned_to_value = cmds.optionMenuGrp('assign_to', q=True, value=True)
        if self.assigned_to_value == "Any Client":
            self.assigned_to = self.clientSelectionTypes["Any Client"]
        elif self.assigned_to_value == "Selected Clients":
            self.assigned_to = self.clientSelectionTypes["Selected Clients"]
            # Create a string using the clientList names that can be sent with the job
            self.clientFullList = cmds.textFieldButtonGrp('clientGet', q=True, text=True)
        elif self.assigned_to_value == "Clients from Listed Groups":
            self.assigned_to = self.clientSelectionTypes["Clients from Listed Groups"]
            # Create a list using the clientList names to generate a list that can be sent with the job
            self.clientGroupFullList = cmds.textFieldButtonGrp('clientGroupGet', q=True, text=True)

    def finaliseJobSpecs(self):
        self.finaliseClientList()
        try:
            if self.hqRoot:
                pass
        except:
            self.filePathCheck()
        if self.filePathSuccess is True:
            return getBaseParameters(self.jobNameSet(cmds.textFieldGrp('jobName', q=True, text=True), self.fileResponse['hq']), self.assigned_to_value,
                                     self.clientFullList, self.clientGroupFullList,
                                     self.cleanInstallEXE(cmds.textFieldGrp('installDirectory', q=True, text=True)), cmds.textFieldButtonGrp('serverAddress', q=True, text=True), cmds.optionMenuGrp('priority', q=True, value=True))
        else:
            raise ValueError("File Path not found")

    def submitJobToFarm(self, *args):
        self.parms = self.finaliseJobSpecs()
        self.childJobs = []
        for i in range(int(cmds.textFieldGrp('trackRange', q=True, text=True).split('-')[0]), int(cmds.textFieldGrp('trackRange', q=True, text=True).split('-')[1]) + 1, 10):
            self.childJobs.append(buildChildJobs("Frame Range_" + str(i) + "-" + str(i + 9),
                                                 buildOSCommands(self.parms['hfs'], i, i + 9, self.fileResponse),
                                                 self.parms['priority']))
        try:
            self.mainJob = buildContainingJobSpec(self.parms['name'], self.parms, self.childJobs)
        except:
            raise ValueError("Frame range is invalid")
        self.jobResponse = sendJob(self.parms['hq_server'], self.mainJob)
        if self.jobResponse:
            print "Job submission successful"
        else:
            print "Failed"

    def serverAddressWrite(self, *args):
        self.response = writeConfigCache(cmds.textFieldButtonGrp(self.serverAddress, q=True, text=True))
        return self.response

    def serverAddressConnect(self, *args):
        self.response = doesHQServerExists(cmds.textFieldButtonGrp(self.serverAddress, q=True, text=True))
        if self.response is True:
            self.serverAddressWrite()
            cmds.textFieldButtonGrp('serverAddress', edit=True, backgroundColor=(0, 0.8, 0))
        else:
            cmds.textFieldButtonGrp('serverAddress', edit=True, backgroundColor=(0.8, 0, 0))

b_cls = createMyLayoutCls()
b_cls.show()