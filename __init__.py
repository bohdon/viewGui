#!/usr/bin/env mayapy
# encoding: utf-8
"""
viewGui

Created by Bohdon Sayre on 2010-01-01.
Copyright (c) 2012 Bohdon Sayre. All rights reserved.
    
The View GUI provides a way to easily create
a window in maya based on using pages or 'views.'

All views should be subclasses of viewGui.View.
All views should be passed to the Gui as a dictionary
of {<class name>:<class>}. Views can then be displayed
by using the showView method. This method can be accessed
through direct access to the Gui, but is also available
to all viewGui.View subclasses.

>>> import viewGui
>>> 
>>> class MyView(viewGui.View):
>>>     def buildBody(self):
>>>         self.viewItem(view='MyView')
>>>         self.viewItem(view='MyView2')
>>>         self.viewItem(view='MyView3')
>>> 
>>> gui = viewGui.Gui(viewClasses = [MyView, MyView, MyView])
>>> gui.create()
"""

import logging
import os
from gui import *
from view import *
from utils import *

__version__ = '0.5.1'
gui.VERSION = __version__

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)

