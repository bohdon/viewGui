


import logging
from pymel.core import *
from view import View


LOG = logging.getLogger('ViewGui : Gui')
LOG.setLevel(logging.DEBUG)


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
        for view in self._views.keys():
            self._views[view]['inst'] = None
        self._curView = None
    
    def updateViews(self, views):
        LOG.debug('updating views...')
        #delete views that may have been removed
        for view in self._views.keys():
            if not views.has_key(view):
                del self._views[view]
                LOG.debug('  deleted view : %s' % view)
        
        #add views that do not exist yet
        for view in views.keys():
            if not self._views.has_key(view):
                cls = views[view]
                if issubclass(cls, View):
                    self._views[view] = {'cls':cls, 'inst':None}
                    LOG.debug('  added view : %s' % view)
                else:
                    LOG.debug('  %s is not a subclass of View (%s, %s)' % (view, id(cls.__bases__[0]), id(View)))
        
        if self.defaultView is None and self._views != {}:
            self.defaultView = self._views.keys()[0]
        if self._curView not in self._views.keys():
            self._curView = None
        
        LOG.debug(' defaultView is %s' % self.defaultView)
        LOG.debug(' curView is %s' % self._curView)
    
    
    def showView(self, view):
        if self._views.has_key(view):
            if view != self._curView:
                self.hideCurView()
                #init the view if it hasnt been already
                self.initView(view)
                self._views[view]['inst'].show()
                self._curView = view
        elif view is None:
            if self._curView != None:
                if self._views.has_key(self._curView):
                    self._views[self._curView]['inst'].hide()
                self._curView = view
        LOG.debug('curView is %s' % self._curView)
    
    def hideView(self, view):
        """
        Hide the specified view if it is intended to be
        persistent, otherwise delete the instance
        """
        if self._views[view]['inst'].persistent:
            self._views[view]['inst'].hide()
        else:
            self._views[view]['inst'] = None
        
    
    def initView(self, view):
        """Init a view if it hasn't been already."""
        if self._views[view]['inst'] is None:
            cls = self._views[view]['cls']
            self._views[view]['inst'] = cls(self._mainForm, self.showView)
            self._views[view]['inst'].create()
    
    
    def hideCurView(self):
        """Hide the current view if it exists"""
        if self._views.has_key(self._curView):
            self._views[self._curView]['inst'].hide()



