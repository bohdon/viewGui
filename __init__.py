"""
    View Gui
    
    Copyright (C) 2010 Bohdon Sayre
    All Rights Reserved
    bo@bohdon.com
    
    The View GUI provides a way to easily create
    a window in maya based on using pages or 'views.'
    
    All views should be subclasses of boViewGui.view.View.
    All views should be passed to the Gui as a dictionary
    of {<class name>:<class>}. Views can then be displayed
    by using the showView method. This method can be accessed
    through direct access to the Gui, but is also available
    to all boViewGui.view.View subclasses.
    
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

__LOG_LEVEL__ = logging.WARNING

def get_log(name=__name__):
    log = logging.getLogger('ViewGui : %s' % name)
    log.setLevel(__LOG_LEVEL__)
    return log

__VERSION__ = (0, 4, 23)

__version__ = '.'.join([str(n) for n in __VERSION__])
__author__ = 'Bohdon Sayre'


