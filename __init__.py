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
    
    >>> import boViewGui.gui, boViewGui.view
    >>> 
    >>> class MyView(boViewGui.view.View):
    >>>     def bodyContent(self):
    >>>         self.viewItem(view='MyView')
    >>>         self.viewItem(view='MyView2')
    >>>         self.viewItem(view='MyView3')
    >>> 
    >>> gui = boViewGui.gui.Gui()
    >>> gui.views = {'MyView':MyView, 'MyView2':MyView, 'MyView3':MyView}
    >>> gui.create()
"""

import logging

__LOG_LEVEL__ = logging.DEBUG

def get_log(name=__name__):
    log = logging.getLogger(name)
    log.setLevel(__LOG_LEVEL__)
    return log

__VERSION__ = (0, 4, 1)

__version__ = '.'.join([str(n) for n in __VERSION__])
__author__ = 'Bohdon Sayre'


