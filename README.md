########################################################################
#                        Description                                   #
########################################################################
This is a python GUI that plot in realtime the output of a camera.

And should have some analysis options.




github package at: https://github.com/Clemgou/



########################################################################
#                      Used packages                                   #
########################################################################
- os
- sys
- numpy
- PyQt5
- pyqtgraph
- pyqtgraph.opengl, pyqtgraph.Qt, pyqtgraph.opengl.GLGraphicsItem
- itertools
- functools
- pyueye (for the camera EO)
- PIL (for saving images)
-  	




########################################################################
#                            Remarks                                   #
########################################################################

1) I had to change the ImageItem.py file because of some issue with the
getHistogram method. I used the newest version (Jun 17, 2019) available
in the git repository of pyqtgraph:
https://github.com/pyqtgraph/pyqtgraph.git

The working file can be found in the Miscellaneous directory.

2)
