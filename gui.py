


import boViewGui
from boViewGui import view

from pymel.core import *


LOG = boViewGui.get_log('Gui')


class Gui(object):
    
    _win = None #the window itself, once created
    winName = 'viewGuiWin' #maya id of the window
    title = 'View Gui' #title of the window
    metrics = {} #window width, height and top left corner
    _views = {}
    defaultView = None #default view to show on create
    _curView = None #currently displayed view
    _mainForm = None #form for all views to be attached to
    
    
    @property
    def views(self):
        """All available views
        {'<view name>': {'cls':<view class>, 'inst':<view instance>}}
        """
        return self._views
    @views.setter
    def views(self, views):
        self.updateViews(views)
    
    @property
    def curView(self): return self._curView
    
    @property
    def window(self): return self._win
    
    def create(self):
        """Build the window and show the default view."""
        self.resetViews()
        
        LOG.debug('Creating Gui...')
        if window(self.winName, ex=True):
            deleteUI(self.winName)
        
        self.applyMetricOpts()
        with window(self.winName, title=self.title) as self._win:
            with formLayout('mainForm', nd=100) as self._mainForm:
                self.showView(self.defaultView)
        
        scriptJob( uid=(self._win, Callback(self.winClosed)) )
    
    def applyMetricOpts(self):
        """Set window size and position by editing the window prefs"""
        if not windowPref(self.winName, ex=True):
            windowPref(self.winName, tlc=(200, 200), w=240, h=240)
        if hasattr(self.metrics, 'w'):
            windowPref(self.winName, e=True, w=self.metrics['w'])
        if hasattr(self.metrics, 'h'):
            windowPref(self.winName, e=True, w=self.metrics['h'])
        if hasattr(self.metrics, 'tlc'):
            windowPref(self.winName, e=True, tlc=self.metrics['tlc'])
    
    def winClosed(self):
        LOG.debug('Gui has been closed.')
        self.resetViews()
    
    
    def resetViews(self):
        """Delete all view instances"""
        for viewName in self._views.keys():
            self._views[viewName]['inst'] = None
        self._curView = None
    
    def updateViews(self, views):
        LOG.debug('updating views...')
        #delete views that may have been removed
        for viewName in self._views.keys():
            if not views.has_key(viewName):
                del self._views[viewName]
                LOG.debug('  deleted view : %s' % viewName)
        
        #add views that do not exist yet
        for viewName in views.keys():
            if not self._views.has_key(viewName):
                cls = views[viewName]
                if issubclass(cls, view.View):
                    self._views[viewName] = {'cls':cls, 'inst':None}
                    LOG.debug('  added view : %s' % viewName)
                else:
                    LOG.debug('  %s is not a subclass of View (%s, %s)' % (viewName, id(cls.__bases__[0]), id(view.View)))
        
        if self.defaultView is None and self._views != {}:
            self.defaultView = self._views.keys()[0]
        if self._curView not in self._views.keys():
            self._curView = None
        
        LOG.debug(' defaultView is %s' % self.defaultView)
        LOG.debug(' curView is %s' % self._curView)
    
    
    def showView(self, viewName):
        if self._views.has_key(viewName):
            if viewName != self._curView:
                self.hideCurView()
                #init the view if it hasnt been already
                self.initView(viewName)
                self._views[viewName]['inst'].show()
                self._curView = viewName
        elif viewName is None:
            if self._curView != None:
                if self._views.has_key(self._curView):
                    self._views[self._curView]['inst'].hide()
                self._curView = viewName
        LOG.debug('curView is %s' % self._curView)
    
    def hideView(self, viewName):
        """
        Hide the specified view if it is intended to be
        persistent, otherwise delete the instance
        """
        if self._views[viewName]['inst'].persistent:
            self._views[viewName]['inst'].hide()
        else:
            self._views[viewName]['inst'] = None
        
    
    def initView(self, viewName):
        """Init a view if it hasn't been already."""
        if self._views[viewName]['inst'] is None:
            cls = self._views[viewName]['cls']
            self._views[viewName]['inst'] = cls(self._mainForm, self.showView)
            self._views[viewName]['inst'].create()
    
    
    def hideCurView(self):
        """Hide the current view if it exists"""
        if self._views.has_key(self._curView):
            self._views[self._curView]['inst'].hide()



