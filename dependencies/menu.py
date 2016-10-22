import sys
import nuke
import nuke_submit_node

print 'Loading Lab Tools...'
menubar = nuke.menu("Nuke")

# Custom Lab Tools
toolbar = nuke.toolbar("Nodes")
m = toolbar.addMenu("hQueue", icon="hQueue.png")

m.addCommand("Submit render", "nuke_submit_node.runGui()", icon="ICON.png")
