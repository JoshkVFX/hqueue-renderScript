# hqueue-renderScript
A script designed to submit render jobs for Nuke and Maya using an installation of Houdini's render farm service, hQueue.

# Introduction
About a year ago I installed a version of Side FX's Houdini 14 Hqueue render farm job management system onto some of the networked computers of the University I was attending at the time. 
After using this for a few days, one of my peers offhandedly said that it would be useful if it could render Nuke and Maya scenes as well.
This was all I needed to hear and within a week I had a basic working version and a week after that I had a fully fleshed out commandline python script that could submit Nuke, Maya and Arnold jobs to Hqueue on windows.

# Where is it?
Long story short the "fully fleshed out script" I wrote worked, but was terribly written. I've chosen to rewrite it from scratch instead of fixing the previous version. 
I'm also improving it as I rewrite it, adding a GUI starting with Nuke then moving onto Maya then Pyqt for a standalone GUI. As I get more and more features rewritten I'll start writing how-to instructions but usage should be fairly straightforward.

# Links
http://SideFX.com - This is SideFX's website, creators of Houdini, Houdini FX and the Hqueue render server program. 