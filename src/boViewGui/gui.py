


import boViewGui
from boViewGui import view
from pymel.core import *

__version__ = '0.3.4'


class Gui(object):
    
    def __init__(self):
        self._win = None #the window itself, once created
        self.winName = 'viewGuiWin' #maya id of the window
        self.title = 'View Gui' #title of the window
        self.metrics = {} #window width, height and top left corner (w, h, tlc)
        self._views = {} #REPLACE WITH _viewsList, and keep _views as a simple index list, this will also help maintain order
        self.defaultView = None #default view to show on create
        self._curView = None #currently displayed view
        self._mainForm = None #form for views to be attached to when visible
        self._invisForm = None #form for all hidden views to be attached to
        self.log = boViewGui.get_log('Gui ({0})'.format(id(self)))
    
    
    @property
    def views(self):
        """All available views
        {'<view name>': {'cls':<view class>, 'inst':<view instance>}}
        """
        return self._views
    @views.setter
    def views(self, views):
        """REPLACES WITH setViews and getViews"""
        self.updateViews(views)
    
    def setViews(self, views):
        self.updateViews(views)
    def getViews(self):
        return self._views
    
    @property
    def curView(self): return self._curView
    
    @property
    def window(self): return self._win
    
    def create(self):
        """Build the window and show the default view."""
        self.resetViews()
        
        self.log.debug('Creating Gui...')
        self.log.debug('    gui vers: %s' % __version__)
        self.log.debug('    view vers: %s' % view.__version__)
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
        if self.metrics.has_key('w'):
            windowPref(self.winName, e=True, w=self.metrics['w'])
        if self.metrics.has_key('h'):
            windowPref(self.winName, e=True, h=self.metrics['h'])
        if self.metrics.has_key('tlc'):
            windowPref(self.winName, e=True, tlc=self.metrics['tlc'])
    
    def winClosed(self):
        self.log.debug('Gui has been closed.')
        self.resetViews()
    
    
    def resetViews(self):
        """Delete all view instances"""
        for viewName in self._views.keys():
            self._views[viewName]['inst'] = None
        self._curView = None
    
    def updateViews(self, views):
        self.log.debug('Updating views...')
        #delete views that may have been removed
        viewsDict = {}
        for viewCls in views:
            viewsDict[viewCls.__name__] = viewCls
        self.log.debug('    views: %s' % viewsDict)
        
        for viewName in self._views.keys():
            if not views.has_key(viewName):
                del self._views[viewName]
                self.log.debug('    deleted view : %s' % viewName)
        
        #add views that do not exist yet
        for viewName in viewsDict.keys():
            if not self._views.has_key(viewName):
                cls = viewsDict[viewName]
                if issubclass(cls, view.View):
                    self._views[viewName] = {'cls':cls, 'inst':None}
                    self.log.debug('    added view : %s' % viewName)
                    #self.log.debug('      (%s, %s)' % (id(cls.__bases__[0]), id(view.View)))
                else:
                    self.log.debug('    %s is not a subclass of View (%s, %s)' % (viewName, id(cls.__bases__[0]), id(view.View)))
        
        if self.defaultView is None and self._views != {}:
            self.defaultView = self._views.keys()[0]
        if self._curView not in self._views.keys():
            self._curView = None
        
        self.log.debug('    defaultView is %s' % self.defaultView)
        self.log.debug('    curView is %s' % self._curView)
    
    
    def showView(self, viewName):
        if self._views.has_key(viewName):
            if viewName != self._curView:
                self.log.debug('Showing view %s' % viewName)
                self.hideCurView()
                self.initView(viewName)
                self._views[viewName]['inst'].show()
                self._curView = viewName
                
        elif viewName is None:
            if self._curView != None:
                if self._views.has_key(self._curView):
                    self._views[viewName]['inst'].hide()
                self._curView = viewName
        
        self.log.debug('  curView is %s' % self._curView)
    
    def initView(self, viewName):
        """Init a view if it hasn't been already."""
        if self._views[viewName]['inst'] is None:
            cls = self._views[viewName]['cls']
            self._views[viewName]['inst'] = cls(self._mainForm, self)
            self._views[viewName]['inst'].create()
            if self._curView is None and self.defaultView == viewName:
                self._views[viewName]['inst'].show()
    
    def hideCurView(self):
        """Hide the current view if it exists"""
        if self._views.has_key(self._curView):
            self._views[self._curView]['inst'].hide()



