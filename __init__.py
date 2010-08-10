"""
    View Gui
    
    Copyright (C) 2010 Bohdon Sayre
    All Rights Reserved
    bo@bohdon.com
    
    The View GUI provides a way to easily create
    a window in maya based on using pages or 'views.'
    
    All views should be subclasses of boViewGui.View.
    All views should be passed to the Gui as a dictionary
    of {<class name>:<class>}. Views can then be displayed
    by using the showView method. This method can be accessed
    through direct access to the Gui, but is also available
    to all boViewGui.View subclasses.
    
"""

__version__ = '0.4.0'
__author__ = 'Bohdon Sayre'


from gui import Gui
from view import View

"""
import boViewGui
reload(boViewGui)
reload(boViewGui.gui)
reload(boViewGui.view)

class MyView(boViewGui.View):
    _displayName = 'My View'
    def bodyContent(self):
        with columnLayout(adj=True):
            button(l='Hi')
            button(l='Hello')

g = boViewGui.Gui()
g.views = {'MyView':MyView}
g.showView('MyView')
g.create()
g.mainView
g.views = {}
del g


setParent()
for item in lsUI(cl=True):
    if 'MyViewHeadFrame' in item.name():
        print item
"""

