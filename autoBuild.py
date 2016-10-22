# Author: Josh Kelly

# Import needed modules and components
import sys
import os
import urllib2

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
    'init': ['', 'https://raw.githubusercontent.com/SpaghettiBaguette/hqueue-renderScript/master/dependencies/init.py'],
    'menu': ['', 'https://raw.githubusercontent.com/SpaghettiBaguette/hqueue-renderScript/master/dependencies/menu.py'],
    'nuke_submit_node': ['', 'https://raw.githubusercontent.com/SpaghettiBaguette/hqueue-renderScript/master/nuke_submit_node.py']
}

for i in pluginComponents.keys():
    print pluginComponents[i][1]
    response = urllib2.urlopen(pluginComponents[i][1])
    pluginComponents[i][0] = response.read()

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
    for i in nukeInstallDir.keys():
        for x in pathValues.keys():
            if type == 'folder':
                if os.path.isdir(os.path.join(nukeInstallDir[i], pathValues[x])):
                    print os.path.join(nukeInstallDir[i], pathValues[x]), "exists!"
                else:
                    print os.path.join(nukeInstallDir[i], pathValues[x]), "does not exist! Creating!"
                    try:
                        os.makedirs(os.path.join(nukeInstallDir[i], pathValues[x]))
                    except:
                        print "You're not an admin!"
            elif type == 'file':
                if os.path.isfile(os.path.join(nukeInstallDir[i], pathValues[x])):
                    print os.path.join(nukeInstallDir[i], pathValues[x]), "exists!"
                    pass
                else:
                    print os.path.join(nukeInstallDir[i], pathValues[x]), "does not exist! Creating!"
                    file = open(os.path.join(nukeInstallDir[i], pathValues[x]), 'w')
                    file.write(pluginComponents[x][0])
                    file.close()
            else:
                raise ValueError('File type unsupported')

createFilesAndDir(folderStructure, 'folder')
createFilesAndDir(fileStructure, 'file')