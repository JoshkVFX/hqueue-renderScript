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
        print "########## Nuke Install Dir ##########"
        print nukeInstallDir[i]
        print "######################################"

    else:
        pass

for i in nukeInstallDir.values():
    for x in folderStructure.values():
        if os.path.isdir(os.path.join(i, x)):
            print os.path.join(i, x), "exists!"
            pass
        else:
            print os.path.join(i, x), "does not exist! Creating!"

for i in nukeInstallDir.values():
    for x in fileStructure.values():
        if os.path.isfile(os.path.join(i, x)):
            print os.path.join(i, x), "exists!"
            pass
        else:
            print os.path.join(i, x), "does not exist! Creating!"

#if OSplatform == "linux":
#    command = "cp -rvn," +  + str(filePath)
