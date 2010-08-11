


import logging
from pymel.core import *



LOG = logging.getLogger('ViewGui : View')
LOG.setLevel(logging.DEBUG)


class View(object):
    """
    Template class for a ViewGui View.
    
    Views mainly consist of a frameLayout containing any controls
    and their corresponding methods.
    
    Common control layouts can be created using special methods:
        viewItem -> create a button that can link to another view
        frameItem -> create a framed button with text
    """
    
    #whether or not the view remains existant if it is not visible
    persistent = True
    
    _visible = False
    
    _layout = None
    _headFrame = None
    _bodyFrame = None
    _headMargins = [0, 0]
    _bodyMargins = [4, 4]
    _linkBgc = [0.2, 0.2, 0.2]
    _attachMargin = 0
    
    _viewItemHeight = 34
    _frameItemWidth = 90
    
    def __init__(self, parent, showView):
        self._parent = parent
        self.showView = showView
        self.viewName = self.__class__.__name__
    
    def __del__(self):
        self.destroy()
        LOG.info('%s has died...' % self.viewName)
    
    def destroy(self):
        """Delete the main layout and reset attributes"""
        try: self._layout.delete()
        except: pass
    
    def recreate(self):
        self.destroy()
        self.create()
    
    def create(self):
        """Create the layout."""
        LOG.debug('Creating View : %s' % self.viewName)
        with self._parent:
            with formLayout() as self._layout:
                self._layout.setVisible(self._visible)
                self.allContent()
        
        formLayout(self._parent, e=True,
            af=[(self._layout, 'top', self._attachMargin), (self._layout, 'left', self._attachMargin),
                (self._layout, 'right', self._attachMargin), (self._layout, 'bottom', self._attachMargin)])
    
    
    def allContent(self):
        """
        Create two frame layouts as a header and body.
        This is the default style for a ViewGui view.
        If an alternate style is desired, this method
        should be overriden.
        """
        with frameLayout('%sHeadFrame' % self.viewName, mw=self._headMargins[0], mh=self._headMargins[1], lv=False, bs='out') as self._headFrame:
            self.headContent()
        with frameLayout('%sFrame' % self.viewName, mw=self._bodyMargins[0], mh=self._bodyMargins[1], lv=False, bs='out') as self._bodyFrame:
            self.bodyContent()
        formLayout(self._layout, e=True,
            af=[(self._headFrame, 'top', 0), (self._headFrame, 'left', 0), (self._headFrame, 'right', 0),
                (self._bodyFrame, 'left', 0), (self._bodyFrame, 'right', 0), (self._bodyFrame, 'bottom', 0)],
            ac=[(self._bodyFrame, 'top', self._attachMargin, self._headFrame)])
    
    def headContent(self):
        """
        Create buttons at the top of the view. These are designed
        to link to other views, and are often used to display the 
        hierarchy of views in relation to each other.
        
        If a custom header is desired, this can method should be overrided.
        """
        with formLayout('%sLinkForm' % self.viewName, bgc=self._linkBgc):
            btns = []
            path = self.links()
            for i in range(0, len(path)):
                name, view = path[i]
                btns.append( button(l=name, c=Callback(self.showView, view), h=18) )
                if view == self.viewName:
                    button(btns[i], e=True, bgc=[.86, .86, .86])
                if i == 0:
                    formLayout(self._headFrame, e=True, af=[(btns[i], 'left', 0)])
                else:
                    formLayout(self._headFrame, e=True, ac=[(btns[i], 'left', 2, btns[i-1])]) 
    
    def bodyContent(self):
        """Create the main content of the view.
        This method should always be overrided."""
        pass
    
    def links(self):
        """
        Return a tuple list of the view names and classes.
        This is usually the view's hierarchy, with the current
        view being listed last, and the highest view first.
        This method should always be overriden.
        
        ex. [('Main', 'Main'), ('Second Page', 'SecondPage'), ('Third Page', self.viewName)]
        """
        return []
    
    def hide(self):
        """Hide the view"""
        self._visible = False
        if not self._layout is None:
            self._layout.setVisible(self._visible)
            LOG.debug('%s hidden' % self.viewName)
        else:
            LOG.error('%s has not been created yet' % self._layout)
    
    def show(self):
        """Show the view"""
        self._visible = True
        if not self._layout is None:
            self._layout.setVisible(self._visible)
            LOG.debug('%s visible' % self.viewName)
        else:
            LOG.error('%s has not been created yet' % self._layout)
    
    def viewItem(self, view, l=None, ann='', bgc=[.25, .25, .25], en=True):
        """Create a button used to link to another view"""
        if l is None: l = view
        btn = button(l=l, c=Callback(self.showView, view), ann=ann, h=self._viewItemHeight, bgc=bgc, en=en)
        return btn
    
    def frameItem(self, l, c, ann='', bgc=None, en=True, mw=4, mh=4, bs='etchedIn'):
        """Create a small frame with no label and a button with a description"""
        with frameLayout(lv=False, mw=mw, mh=mh, bs=bs) as frame:
            with formLayout(en=en) as form:
                btn = button(l=l, c=c, ann=ann, w=self._frameItemWidth)
                if bgc != None:
                    button(btn, e=True, bgc=bgc)
                txt = text(l=ann, al='center')
            formLayout(form, e=True, af=[(btn, 'top', 0), (btn, 'left', 0), (btn, 'right', 0), (txt, 'left', 0), (txt, 'right', 0), (txt, 'bottom', 0)], ac=[(txt, 'top', 4, btn)])
        return frame, form, btn, txt




