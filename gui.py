


import logging
from pymel.core import *
from view import View

LOG = logging.getLogger('ViewGui : Gui')
LOG.setLevel(logging.DEBUG)


class Gui(object):
    
    _win = None
    winName = 'viewGuiWin'
    title = 'View Gui'
    _options = {}
    _views = {}
    mainView = None
    _curView = None
    _mainForm = None
    _metricOpts = ['w', 'h', 'tlc']
    _windowOpts = ['tlb', 'mnb', 'mxb', 's', 'tb']
    
    
    def __del__(self):
        LOG.info('Gui has died...')
    
    @property
    def views(self):
        """All available views of the View Gui"""
        return self._views
    @views.setter
    def views(self, views):
        self.updateViews(views)
    
    def curView(self):
        """The currently displayed view"""
        return self._curView
    
    @property
    def options(self):
        """Options to control how the window is displayed.
        Only expected options are allowed:
        w: width
        h: height
        tlc: topLeftCorner
        tlb: toolBox
        mnb: minimizeButton
        mxb: maximizeButton
        s: scaleable
        tb: toolBar"""
        return self._options
    @options.setter
    def setoptions(self, options):
        for key in options:
            if key in self._settingOpts or key in self._metricOpts:
                self._options[key] = options[key]
    
    @property
    def window(self): return self._win
    
    def create(self):
        """Build the window"""
        self.resetViews()
        
        LOG.debug('Creating Gui...')
        if window(self.winName, ex=True):
            deleteUI(self.winName)
        
        self.applyMetricOpts()
        with window(self.winName, title=self.title) as self._win:
            self.applyWindowOpts()
            with formLayout('mainForm', nd=100) as self._mainForm:
                self.showView(self.mainView)
        
    
    def applyMetricOpts(self):
        """Set window size by editing the window prefs if they exist"""
        if not windowPref(self.winName, ex=True):
            windowPref(self.winName, tlc=(200, 200), w=240, h=240)
        if hasattr(self, 'w'):
            windowPref(self.winName, e=True, w=self.w)
        if hasattr(self, 'h'):
            windowPref(self.winName, e=True, w=self.h)
        if hasattr(self, 'tlc'):
            windowPref(self.winName, e=True, tlc=self.tlc)
    
    def applyWindowOpts(self):
        """Apply special window settings"""
        if hasattr(self, 'tlb'):
            window(self.winName, e=True, tlb=self.tlb)
        if hasattr(self, 'mnb'):
            window(self.winName, e=True, mnb=self.mnb)
        if hasattr(self, 'mxb'):
            window(self.winName, e=True, mxb=self.mxb)
        if hasattr(self, 's'):
            window(self.winName, e=True, s=self.s)
        if hasattr(self, 'tb'):
            window(self.winName, e=True, tb=self.tb)
    
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
                LOG.debug('deleted view : %s' % view)
        
        #add views that do not exist yet
        for view in views.keys():
            if not self._views.has_key(view):
                cls = views[view]
                if issubclass(cls, View):
                    self._views[view] = {'cls':cls, 'inst':None}
                    LOG.debug('added view : %s' % view)
                else:
                    LOG.debug('%s is not a subclass of View (%s, %s)' % (view, id(cls.__bases__[0]), id(View)))
        
        if self.mainView is None and self._views != {}:
            self.mainView = self._views.keys()[0]
        if self._curView not in self._views.keys():
            self._curView = None
        
        LOG.debug('mainView is %s' % self.mainView)
        LOG.debug('curView is %s' % self._curView)
    
    
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
    
    """def hideView(self, view):
        \"\"\"
        Hide the specified view if it is intended to be
        persistent, otherwise delete the instance
        \"\"\"
        viewInst = self._views[view]['inst']
        if viewInst.isPersistent"""
        
    
    def initView(self, view):
        """
        Init a view if it hasn't been already.
        """
        if self._views[view]['inst'] is None:
            cls = self._views[view]['cls']
            self._views[view]['inst'] = cls(self._mainForm, self)
            self._views[view]['inst'].create()
    
    
    def hideCurView(self):
        """
        Hide the current view if it exists
        """
        if self._views.has_key(self._curView):
            self._views[self._curView]['inst'].hide()



