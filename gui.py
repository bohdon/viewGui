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
import time
from utils import Callback

__all__ = [
    'Gui',
    'ViewGui',
    'IconCaptureGui',
    'DockControl',
    'ScriptedPanelTypes',
    'ScriptedPanel',
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
        self.name = name
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
    def winName(self):
        return self.name
    
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
            self.mainControl = self._win
            with pm.frameLayout('mainForm', lv=False, bv=False) as self._mainLayout:
                self.showDefaultView()
        
        pm.scriptJob(uid=(self._win, Callback(self.winClosed)))

    def setupScriptJob(self, event):
        if not self._scriptJobs.has_key(event):
            # setup script job
            eventmap = dict(
                onSelectionChange=['SelectionChanged'],
                onSceneChange=['SceneOpened', 'NewSceneOpened', 'PostSceneRead'],
                onUndo=['Undo'],
                onRedo=['Redo'],
            )
            self._scriptJobs[event] = []
            if eventmap.has_key(event):
                for key in eventmap[event]:
                    j = pm.scriptJob(e=(key, Callback(self.scriptJobUpdate, event)), p=self.mainControl)
                    self._scriptJobs[event].append(j)
            elif event == 'onWindowClosed':
                j = pm.scriptJob(uid=(self.window, Callback(self.scriptJobUpdate, event)), runOnce=True)
                self._scriptJobs[event].append(j)

    def scriptJobUpdate(self, event):
        print "event: %s" % event # TESTING
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
            v = c(self)
            with self._mainLayout:
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

class DockControl(Gui):
    """
    Display gui in a dockControl instead of a separate window.
    These appear on the left and right sides of the viewport.
    """
    """
    The main View Gui class. Contains a list of View subclasses that can be shown by name.
    
    The window has metrics, but Views may also have metrics that will be applied when
    the View is shown.  The gui can ignore View metrics by setting ignoreViewMetrics to True.
    """
    _dockControl = None
    def __init__(self, *args, **kwargs):
        """
        dockName - name of the dock dockControl
        floating - True/False if dock is floating or docked
        area - default area for the dock
        """
        self.dockName = kwargs.pop('dockName', None)
        if not self.dockName and len(args) > 2:
            self.dockName = "%sDock" % args[1]
        self.floating = kwargs.pop('floating', False)
        self.area = kwargs.pop('area', "left")
        super(DockControl, self).__init__(*args, **kwargs)
        self.register()

    @property
    def dockControl(self):
        return self._dockControl
    
    def dockVisibleChanged(self):
        if pm.dockControl(self._dockControl, ex=True):
            if not pm.dockControl(self._dockControl, q=True, vis=True):
                self.mainLayout.clear()
            else:
                self._updateViews()

    def register(self):
        """ Register the dock in maya """
        self.deleteViews()
        
        # Dock
        if pm.dockControl(self.dockName, ex=True):
            pm.deleteUI(self.dockName)

        # Window
        if pm.window(self.winName, ex=True):
            pm.deleteUI(self.winName)
        
        self._win = None
        self.applyMetrics()

        # For a dockControl, we've got to go create the ui this way
        # otherwise when we create the dockControl it doesn't see the main layout
        self._win = pm.window(self.winName, title=self.title)
        with pm.frameLayout('mainForm', lv=False, bv=False, p=self._win) as self._mainLayout:
            self.mainControl = self._mainLayout
            self.showDefaultView()

            # Create the dockControl
            self._dockControl = pm.dockControl(self.winName+"Dock",
                con=self._win, aa=['left', 'right'], a=self.area, fl=int(self.floating), l=self.title,
                vcc=Callback(self.dockVisibleChanged), vis=False,
            )

        pm.scriptJob(uid=(self._win, Callback(self.winClosed)))

    def create(self):
        """ Show the dock control """
        self.showDock()

    def showDock(self):
        pm.dockControl(self.dockControl, e=True, vis=True)

    def hideDock(self):
        pm.dockControl(self.dockControl, e=True, vis=False)

    def toggleDock(self):
        if pm.dockControl(self.dockControl, q=True, vis=True):
            self.hideDock()
        else:
            self.showDock()

    def dockVisibleChanged(self):
        pass



PANEL_MELCALLBACK = """
proc viewGuiPanelCallback(string $panelName) {{
    python("import maya.mel; from viewGui.gui import ScriptedPanelTypes");
    python("ScriptedPanelTypes.callback({0!r}, {1!r}, '" + $panelName + "')");
}}
viewGuiPanelCallback
"""
PANEL_MELCOPYSTATECALLBACK = """
proc viewGuiPanelCopyCallback(string $panelName, string $newPanelName) {{
    python("import maya.mel; from viewGui.gui import ScriptedPanelTypes");
    python("ScriptedPanelTypes.callback({0!r}, {1!r}, '" + $panelName + "', '" + $newPanelName + "')");
}}
viewGuiPanelCopyCallback
"""
PANEL_MELSTATECOMMAND = ''


class ScriptedPanelTypes(object):
    """
    Manages existing custom scripted panel types and their instances.
    """

    INSTANCES = {}
    INIT_KWARGS = {}

    @staticmethod
    def callback(panelType, callback, name, newName=None):
        # create panel
        if callback == 'createCallback':
            return ScriptedPanelTypes.createCallback(panelType, name)
        # handle copy state extra args
        if callback == 'copyStateCallback':
            kw = dict(newPanel=ScriptedPanelTypes.getInstance(panelType, newName))
        else:
            kw = {}
        # send callback to existing panel
        inst = ScriptedPanelTypes.getInstance(panelType, name)
        result = None
        if not inst:
            LOG.error('missing scripted panel instance: type: {0}, name: {1}, callback: {2}'.format(panelType, name, callback))
        else:
            method = getattr(inst, callback)
            LOG.debug('calling {0} on {1}'.format(method.__name__, name))
            result = method(**kw)
            if callback == 'deleteCallback':
                ScriptedPanelTypes.removeInstance(inst)
        if not result:
            result = ''
        return result

    @staticmethod
    def addInstance(inst):
        if not isinstance(inst, ScriptedPanel):
            raise TypeError('excpted ScriptedPanel, got {0}'.format(type(inst).__name__))
        typ = inst.panelType
        if not ScriptedPanelTypes.INSTANCES.has_key(typ):
            ScriptedPanelTypes.INSTANCES[typ] = []
        ScriptedPanelTypes.INSTANCES[typ].append(inst)
        LOG.debug('registered scripted panel instance: {0}, name: {1}'.format(inst, inst.panelName))

    @staticmethod
    def removeInstance(inst):
        for k in ScriptedPanelTypes.INSTANCES.keys():
            if inst in ScriptedPanelTypes.INSTANCES[k]:
                ScriptedPanelTypes.INSTANCES[k].remove(inst)

    @staticmethod
    def getInstance(typ, name):
        """ Currently using instance id instead of name """
        if ScriptedPanelTypes.INSTANCES.has_key(typ):
            for inst in ScriptedPanelTypes.INSTANCES[typ]:
                if inst.panelName == name:
                    return inst

    @staticmethod
    def allPanels(panelType):
        """ Return all panel instances of the given type """
        return ScriptedPanelTypes.INSTANCES.get(panelType, [])

    @staticmethod
    def deleteAllPanels(panelType):
        """ Delete all panels of the given type """
        for p in ScriptedPanelTypes.INSTANCES.get(panelType, []):
            if p.exists:
                pm.deleteUI(p.panel, pnl=True)

    @staticmethod
    def newType(typeName, unique=False, **kwargs):
        """
        Create and a new scripted panel type.
        The given kwargs will be used to initialize new panels of this type,
        so this is where viewClasses, defaultView, etc should be given.
        """
        # create new panel type if it doesnt exist
        if not pm.scriptedPanelType(typeName, query=True, exists=True):
            newType = pm.scriptedPanelType(typeName)
            LOG.info('created new scripted panel type: {0}'.format(newType))
        # edit panel type
        kw = {}
        for cb in ('create', 'init', 'add', 'remove', 'delete', 'saveState', 'copyState'):
            cbname = '{0}Callback'.format(cb)
            fmt = PANEL_MELCOPYSTATECALLBACK if cb == 'copyState' else PANEL_MELCALLBACK
            kw[cbname] = fmt.format(typeName, cbname)
        newType = pm.scriptedPanelType(typeName, edit=True, unique=unique, **kw)
        # register init kwargs for this type
        ScriptedPanelTypes.INIT_KWARGS[newType] = kwargs
        return newType

    @staticmethod
    def newPanel(typ, title, name):
        """
        Create and return a new panel of the given type.
        """
        pm.scriptedPanel(name, unParent=True, type=typ, label=title)
        return ScriptedPanelTypes.getInstance(typ, name)

    @staticmethod
    def createCallback(panelType, name):
        """ Create a viewGui ScriptedPanel instance from the newly created maya ScriptedPanel """
        pnl = pm.ui.ScriptedPanel(name)
        try:
            inst = ScriptedPanel(pnl, **ScriptedPanelTypes.INIT_KWARGS.get(panelType, {}))
        except Exception as e:
            LOG.error(e)
            # abort panel creation
            try:
                pm.deleteUI(pnl)
            except Exception as e:
                LOG.error(e)
        else:
            LOG.debug('created new ScriptedPanel instance from {0!r}: {1}'.format(pnl, inst))
            ScriptedPanelTypes.addInstance(inst)



class ScriptedPanel(Gui):
    @staticmethod
    def newPanel(typ, title, name):
        """
        Create and return a new panel of the given type.
        The scripted panel type must be created before a new panel can be made.
        """
        return ScriptedPanelTypes.newPanel(typ, title, name)

    @staticmethod
    def fromPanel(pnl):
        return ScriptedPanelTypes.getInstance(pnl.getType(), pnl.name())

    def __init__(self, panel, *args, **kwargs):
        super(ScriptedPanel, self).__init__(*args, **kwargs)
        self.panel = panel
        self.name = self.panel.name()

    def __repr__(self):
        return '<ScriptedPanel | {0.panelType} | {0.panelName} | {0.panelTitle}>'.format(self)

    @property
    def exists(self):
        return pm.scriptedPanel(self.panel, q=True, ex=True)

    @property
    def panelName(self):
        if self.exists:
            self.name = self.panel.name()
        return self.name

    @property
    def panelTitle(self):
        if self.exists:
            return self.panel.getLabel()
    @panelTitle.setter
    def panelTitle(self, value):
        if self.exists:
            self.panel.setLabel(value)

    @property
    def panelType(self):
        if self.exists:
            return self.panel.getType()

    @property
    def menuBar(self):
        if self.panelName:
            return pm.scriptedPanel(self.panelName, q=True, control=True)

    def create(self):
        """ Create an instance of this ScriptedPanel's panel type. """
        raise Exception('ScriptedPanels must be created via ScriptedPanelTypes.newPanel')

    def saveStateCallback(self):
        """ Save the state of the panel """
        return 'print("this is a state string");'

    def createCallback(self):
        """ Create any editors unparented here and do any other initialization required. """
        pass

    def initCallback(self):
        """ Re-initialize the panel on file new or file open. """
        pass

    def addCallback(self):
        """ Create UI and parent any editors. """
        # delete window
        if pm.window(self.winName, ex=True):
            pm.deleteUI(self.winName)
        
        self._win = None
        self.applyMetrics()
        
        p = pm.currentParent()

        self.deleteViews()
        with pm.window(title=self.title) as self._win:
            self._mainLayout = pm.verticalLayout()
        pm.verticalLayout(self._mainLayout, e=True, p=p)

        self._win = self._mainLayout
        self.mainControl = self._mainLayout
        self.showDefaultView()
        pm.evalDeferred(self.refreshScriptJobs)

    def refreshScriptJobs(self):
        recreate = []
        for event in self._scriptJobs:
            for j in self._scriptJobs[event]:
                if not pm.scriptJob(ex=j):
                    recreate.append(event)
                    break
        for event in recreate:
            del self._scriptJobs[event]
            self.setupScriptJob(event)

    def removeCallback(self):
        """ Unparent any editors and save state if required. """
        self.winClosed()
        # delete this panel
        pm.evalDeferred(self._removeDeferred)

    def _removeDeferred(self):
        if self.exists:
            # panel is registered as torn off when it was previously not
            # only delete when it was torn off and will not be any more (getTearOff == False)
            if self.panel.getTearOff():
                return
            # only delete if not the last one
            if len(ScriptedPanelTypes.allPanels(self.panelType)) < 2:
                return
            try:
                pm.deleteUI(self.panel, pnl=True)
            except Exception as e:
                LOG.error(e)

    def deleteCallback(self):
        """ Delete any editors and do any other cleanup required. """
        pass

    def saveStateCallback(self):
        """ Return a string that will restore the state of a panel on create to this panels current state """
        return ''

    def copyStateCallback(self, newPanel):
        """ Copy the state of one panel to another """
        if newPanel:
            pm.evalDeferred(Callback(self._copyStateDeferred, newPanel))

    def _copyStateDeferred(self, newPanel):
        newPanel.panelTitle = self.panelTitle



