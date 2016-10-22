# Author: Josh Kelly

# Import needed modules and components
import sys
import os
import urllib2

def isUserAdmin():
    import ctypes
    # WARNING: requires Windows XP SP2 or higher!
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        traceback.print_exc()
        print "Admin check failed, assuming not an admin."
        return False

def runAsAdmin(cmdLine=None, wait=True):

    import win32api, win32con, win32event, win32process
    from win32com.shell.shell import ShellExecuteEx
    from win32com.shell import shellcon

    python_exe = sys.executable

    if cmdLine is None:
        cmdLine = [python_exe] + sys.argv
    elif type(cmdLine) not in (types.TupleType,types.ListType):
        raise ValueError, "cmdLine is not a sequence."
    cmd = '"%s"' % (cmdLine[0],)
    # XXX TODO: isn't there a function or something we can call to massage command line params?
    params = " ".join(['"%s"' % (x,) for x in cmdLine[1:]])
    cmdDir = ''
    showCmd = win32con.SW_SHOWNORMAL
    #showCmd = win32con.SW_HIDE
    lpVerb = 'runas'  # causes UAC elevation prompt.

    # print "Running", cmd, params

    # ShellExecute() doesn't seem to allow us to fetch the PID or handle
    # of the process, so we can't get anything useful from it. Therefore
    # the more complex ShellExecuteEx() must be used.

    # procHandle = win32api.ShellExecute(0, lpVerb, cmd, params, cmdDir, showCmd)

    procInfo = ShellExecuteEx(nShow=showCmd,
                              fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                              lpVerb=lpVerb,
                              lpFile=cmd,
                              lpParameters=params)

    if wait:
        procHandle = procInfo['hProcess']
        obj = win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
        rc = win32process.GetExitCodeProcess(procHandle)
        #print "Process handle %s returned code %s" % (procHandle, rc)
    else:
        rc = None

    return rc

def test(command):
    rc = 0
    if not isUserAdmin():
        print "You're not an admin.", os.getpid(), "params: ", sys.argv
        #rc = runAsAdmin(["c:\\Windows\\notepad.exe"])
        rc = runAsAdmin()
    else:
        print "You are an admin!", os.getpid(), "params: ", sys.argv
        rc = 0
    x = raw_input('Press Enter to exit.')
    return rc

OSplatform = sys.platform
if OSplatform.startswith("win"):
    OSplatform = "windows"
    nukeDir = "C:\Program Files"
elif OSplatform.startswith("linux"):
    OSplatform = "linux"
    nukeDir = "/usr/local"
elif OSplatform.startswith("darwin"):
    OSplatform = "macosx"
    nukeDir = "/Applications"
    macExtraFolders = "Contents/MacOS/"

if OSplatform == "windows":
    pass
elif OSplatform == "linux":
    if os.getuid() == 0:
        pass
    else:
        print "User is not root! Rerun with sudo!"
        quit()
elif OSplatform == "macosx":
    if os.getuid() == 0:
        pass
    else:
        print "User is not root! Rerun with sudo!"
        quit()
else:
    print "Unsupported platform"
    quit()

folderStructure = {
    'user': os.path.join('plugins', 'user'),
    'python': os.path.join('plugins', os.path.join('user', 'python')),
    'icons': os.path.join('plugins', os.path.join('user', 'icons'))
}

fileStructure = {
    'init': os.path.join('plugins', os.path.join('user', 'init.py')),
    'menu': os.path.join('plugins', os.path.join('user', 'menu.py')),
    'nuke_submit_node': os.path.join('plugins', os.path.join('user', os.path.join('python', 'nuke_submit_node.py')))
}

pluginComponents = {
    'init': ['', ''],
    'menu': ['', ''],
    'nuke_submit_node': ['', 'https://raw.githubusercontent.com/SpaghettiBaguette/hqueue-renderScript/master/nuke_submit_node.py']
}

#for i in pluginComponents.keys():
#    response = urllib2.urlopen(i[2])
#    pluginComponents[i[1]] = response.read()

try:
    filePath = sys.argv[1]
except:
    filePath = nukeDir

nukeInstallDir = {}

for i in os.listdir(filePath):
    if "Nuke" in i:
        nukeInstallDir[i] = os.path.join(filePath, i)
    else:
        pass

print "########## Nuke Install Dir ##########"
print '\n'.join(nukeInstallDir)
print "######################################"

def createFilesAndDir(pathValues, type):
    for i in nukeInstallDir.values():
        for x in pathValues.values():
            if type == 'folder':
                if os.path.isdir(os.path.join(i, x)):
                    print os.path.join(i, x), "exists!"
                else:
                    print os.path.join(i, x), "does not exist! Creating!"
                    try:
                        os.makedirs(os.path.join(i, x))
                    except:
                        print "You're not an admin!"
            elif type == 'file':
                if os.path.isfile(os.path.join(i, x)):
                    print os.path.join(i, x), "exists!"
                    pass
                else:
                    print os.path.join(i, x), "does not exist! Creating!"

            else:
                raise ValueError('File type unsupported')

createFilesAndDir(folderStructure, 'folder')
createFilesAndDir(fileStructure, 'file')

#for i in nukeInstallDir.values():
#    for x in fileStructure.values():
#        if os.path.isfile(os.path.join(i, x)):
#            print os.path.join(i, x), "exists!"
#            pass
#        else:
#            print os.path.join(i, x), "does not exist! Creating!"

#if OSplatform == "linux":
#    command = "cp -rvn," +  + str(filePath)