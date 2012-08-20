#!/usr/bin/env mayapy
# encoding: utf-8
"""
viewGui.gui

Created by Bohdon Sayre on 2010-01-01.
Copyright (c) 2012 Bohdon Sayre. All rights reserved.
"""

import pymel.core as pm
import logging
import view

__all__ = [
    'Gui',
    'ViewGui',
    'IconCaptureGui',
]

LOG = logging.getLogger(__name__)
VERSION = '0.0'
DEFAULT_SIZE = (200, 200)
DEFAULT_TLC = (200, 200)

class Gui(object):
    """
    The main View Gui class. Contains a list of View subclasses that can be shown by name.
    
    The window has metrics, but Views may also have metrics that will be applied when
    the View is shown.  The gui can ignore View metrics by setting ignoreViewMetrics to True.
    """
    def __init__(self, title='View Gui', name='viewGuiWin', viewClasses=None, defaultView=None, w=None, h=None):
        """
        `title` -- the title for the window
        `name` -- the maya name for the window, should be as unique as possible
        `viewClasses` -- the list of view classes available for this window
        `defaultView` -- the name of the view to use as the default when showing
        `w` -- width of the window
        `h` -- heigth of the window
        """
        self.title = title
        self.winName = name
        self.metrics = {'w':w, 'h':h, 'tlc':None}
        
        self._win = None
        self._viewClasses = []
        self._viewInst = {}
        self._viewMetrics = {}
        self._defaultView = None
        self._curViewName = None
        self._mainLayout = None
        self._scriptJobs = {}
        
        if viewClasses is not None:
            if not isinstance(viewClasses, (list, tuple)):
                viewClasses = [viewClasses]
            self.viewClasses = viewClasses
        
        self.defaultView = defaultView
        
        LOG.debug('viewGui version: {0}'.format(VERSION))
    
    @property
    def viewClasses(self):
        """ Return all available view classes """
        return self._viewClasses
    @viewClasses.setter
    def viewClasses(self, views):
        """ Set the available view classes """
        self._viewClasses = [v for v in views if isinstance(v, type) and issubclass(v, view.View)]
        self._updateViews()
    
    def getViewClass(self, viewName):
        """ Return the class for the given view name """
        for c in self.viewClasses:
            if c.__name__ == viewName:
                return c
    
    @property
    def viewNames(self):
        """ Return all available view class names """
        return [v.__name__ for v in self.viewClasses]
    
    @property
    def views(self):
        """ Return all view instances in a dictionary by name """
        return self._viewInst.copy()
    
    def hasView(self, viewName):
        """ Return True if this gui has the given viewName """
        return viewName in self.viewNames
    
    def getView(self, viewName):
        if self.hasView(viewName):
            return self._viewInst[viewName]
    
    @property
    def curViewName(self):
        return self._curViewName
    
    @property
    def curView(self):
        return self.getView(self.curViewName)
    
    @property
    def defaultView(self):
        if self._defaultView is None:
            if len(self.viewClasses) > 0:
                return self.viewNames[0]
        else:
            return self._defaultView
    @defaultView.setter
    def defaultView(self, value):
        if self.hasView(value):
            self._defaultView = value
    
    @property
    def window(self):
        return self._win
    
    def _updateViews(self):
        """
        Update current views. Removes views whose classes are no longer
        registered and adds entries for instances of new classes.
        """
        for n in self.viewNames:
            if not self._viewInst.has_key(n):
                self._viewInst[n] = None
                LOG.debug('new view: {0}'.format(n))
        
        for n in self._viewInst.keys():
            if not self.hasView(n):
                del self._viewInst[n]
                LOG.debug('removed view: {0}'.format(n))
        
        for n in self._viewMetrics.keys():
            if not self.hasView(n):
                del self._viewMetrics[n]
        
        if self.defaultView is None and len(self.viewClasses) > 0:
            self.defaultView = self.viewNames[0]
        if self.curViewName not in self.viewNames:
            self._curViewName = self.defaultView
        self.showView(self.curViewName)
        
        LOG.debug('defaultView is {0}'.format(self.defaultView))
        LOG.debug('curView is {0}'.format(self._curViewName))
    
    def create(self):
        """ Build the window and show the default view """
        self.deleteViews()
        
        if pm.window(self.winName, ex=True):
            pm.deleteUI(self.winName)
        
        self._win = None
        self.applyMetrics()
        with pm.window(self.winName, title=self.title) as self._win:
            with pm.frameLayout('mainForm', lv=False, bv=False) as self._mainLayout:
                self.showDefaultView()
        
        pm.scriptJob(uid=(self._win, pm.Callback(self.winClosed)))

    def setupScriptJob(self, event):
        if not self._scriptJobs.has_key(event):
            # setup script job
            eventmap = dict(
                onSelectionChange=['SelectionChanged'],
                onSceneChange=['SceneOpened', 'NewSceneOpened'],
                onUndo=['Undo'],
                onRedo=['Redo'],
            )
            self._scriptJobs[event] = []
            if eventmap.has_key(event):
                for key in eventmap[event]:
                    j = pm.scriptJob(e=(key, pm.Callback(self.scriptJobUpdate, event)), p=self.window)
                    self._scriptJobs[event].append(j)
            elif event == 'onWindowClosed':
                j = pm.scriptJob(uid=(self.window, pm.Callback(self.scriptJobUpdate, event)), runOnce=True)
                self._scriptJobs[event].append(j)

    def scriptJobUpdate(self, event):
        v = self.curView
        if v is not None:
            fnc = getattr(v, event)
            if hasattr(fnc, '__call__'):
                fnc()
    
    def applyMetrics(self, m=None):
        """Set window size and position by editing the window prefs"""
        if m is None:
            m = self.metrics
        if not pm.windowPref(self.winName, ex=True):
            pm.windowPref(self.winName, tlc=DEFAULT_TLC, w=DEFAULT_SIZE[0], h=DEFAULT_SIZE[1])
        if m.has_key('w') and m['w'] is not None:
            pm.windowPref(self.winName, e=True, w=m['w'])
            if self._win is not None:
                self._win.setWidth(m['w'])
        if m.has_key('h') and m['h'] is not None:
            pm.windowPref(self.winName, e=True, h=m['h'])
            if self._win is not None:
                self._win.setHeight(m['h'])
        if m.has_key('tlc') and m['tlc'] is not None:
            pm.windowPref(self.winName, e=True, tlc=m['tlc'])
    
    def winClosed(self):
        LOG.debug('gui closed')
        self.deleteViews()
    
    def deleteViews(self):
        """ Delete all view instances """
        for viewName in self._viewInst.keys():
            self._viewInst[viewName] = None
        self._curViewName = None
    
    def deleteView(self, viewName):
        if self.hasView(viewName):
            self._viewInst[viewName] = None
    
    def resetView(self, viewName):
        if self.hasView(viewName):
            self.deleteView(viewName)
            if viewName == self.curViewName:
                self.showView(viewName)
    
    def showDefaultView(self):
        self.showView(self.defaultView)
    
    def showView(self, viewName):
        if not self.hasView(viewName):
            return
        if viewName == self.curViewName:
            return
        self.hideCurView()
        # create and show
        v = self.getView(viewName)
        # check persistence
        if v is not None and not v.persistent:
            self.deleteView(viewName)
            v = None
        if v is None:
            self._createView(viewName)
            v = self.getView(viewName)
        v.show()
        # apply metrics
        if v.rememberMetrics and self._viewMetrics.has_key(viewName):
            self.applyMetrics(self._viewMetrics[viewName])
        self._curViewName = viewName
        LOG.debug('showed view {0}'.format(viewName))
    
    def _createView(self, viewName):
        """ Create the view for the given name if it doesn't already exist. """
        if not self.hasView(viewName):
            return
        if self.getView(viewName) is None:
            c = self.getViewClass(viewName)
            v = c(self._mainLayout, self)
            v.create()
            self._viewInst[viewName] = v
            if v.metrics is not None:
                self._viewMetrics[viewName] = v.metrics.copy()
            # check if requires script jobs
            for e in ('onSelectionChange', 'onSceneChange', 'onUndo', 'onRedo', 'onWindowClosed'):
                if hasattr(getattr(v, e), '__call__'):
                    self.setupScriptJob(e)
            LOG.debug('created view {0}'.format(viewName))
    
    def hideCurView(self):
        """ Hide the current view if it exists """
        v = self.curView
        if v is not None:
            if v.rememberMetrics:
                self._viewMetrics[self.curViewName] = dict(
                    w = self._win.getWidth(),
                    h = self._win.getHeight()
                )
            v.hide()

ViewGui = Gui


def IconCaptureGui(name='viewGuiIconCaptureWin', title='Capture Icon', size=(128, 128), cls=None):
    if cls is None:
        cls = view.IconCaptureView
    g = ViewGui(title, name, [cls], w=100, h=100)
    g.iconSize = size
    g.create()
    return g.curView



