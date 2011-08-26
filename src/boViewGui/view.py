


import boViewGui
from pymel.core import *


__version__ = '0.3.5'


class View(object):
    """
    Template class for a ViewGui View.
    
    Views mainly consist of a frameLayout containing any controls
    and their corresponding methods.
    
    Common control layouts can be created using special methods:
        viewItem -> create a button that can link to another view
        frameItem -> create a framed button with text
    """
    
    _displayName = 'View'
    
    _visible = False
    
    _layout = None
    _nullLayout = None
    _headFrame = None
    _bodyFrame = None
    _headMargins = [0, 0]
    _bodyMargins = [4, 4]
    _linkBgc = [0.2, 0.2, 0.2]
    _attachMargin = 0
    
    _viewItemHeight = 34
    _frameItemWidth = 90
    
    def __init__(self, parent, gui):
        self._parent = parent
        self.gui = gui
        self.showView = gui.showView
        self.viewName = self.__class__.__name__
        self.log = boViewGui.get_log('View ({0})'.format(self.viewName))
    
    def __del__(self):
        self.destroy()
        self.log.info('%s has died...' % self.viewName)
    
    def destroy(self):
        """Delete the main layout and reset attributes"""
        try: self._layout.delete()
        except: pass
    
    def recreate(self):
        self.destroy()
        self.create()
    
    def create(self):
        """Create the layout."""
        self.log.debug('    Creating View : %s' % self.viewName)
        with self._parent:
            with formLayout() as self._layout:
                self.allContent()
        self.detachView()
    
    
    def allContent(self):
        """
        Create two frame layouts as a header and body.
        """
        with frameLayout('%sHeadFrame' % self.viewName, mw=self._headMargins[0], mh=self._headMargins[1], lv=False, bs='out') as self._headFrame:
            self.headContent()
        with frameLayout('%sFrame' % self.viewName, mw=self._bodyMargins[0], mh=self._bodyMargins[1], lv=False, bv=False) as self._bodyFrame:
            self.bodyContent()
        formLayout(self._layout, e=True,
            af=[(self._headFrame, 'top', 0), (self._headFrame, 'left', 0), (self._headFrame, 'right', 0),
                (self._bodyFrame, 'left', 0), (self._bodyFrame, 'right', 0), (self._bodyFrame, 'bottom', 0)],
            ac=[(self._bodyFrame, 'top', 2, self._headFrame)])
    
    def headContent(self):
        """
        Create buttons at the top of the view. These are designed
        to link to other views, and are often used to display the 
        hierarchy of views in relation to each other.
        
        If a custom header is desired, this can method should be overrided.
        """
        links = self.links()
        if links != []:
            self.log.debug('        building links: %s' % links)
            with formLayout('%sLinkForm' % self.viewName, bgc=self._linkBgc) as form:
                btns = []
                for i in range(len(links)):
                    viewName = links[i]
                    if self.gui._views.has_key(viewName):
                        name = self.gui._views[viewName]['cls']._displayName
                    else:
                        name = viewName
                    btns.append( button(l=name, c=Callback(self.showView, viewName), h=18) )
                    if viewName == self.viewName:
                        button(btns[i], e=True, bgc=[.86, .86, .86])
                    if i == 0:
                        formLayout(form, e=True, af=[(btns[i], 'left', 0)])
                    else:
                        formLayout(form, e=True, ac=[(btns[i], 'left', 2, btns[i-1])])
            self._headFrame.setVisible(True)
        else:
            self._headFrame.setVisible(False)
    
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
        
        ex. ['MainView, 'SecondPageView', 'ThirdPageView', self.viewName]
        """
        return []
    
    def hide(self):
        """Hide the view"""
        self._visible = False
        self.detachView()
        self.updateVisible()
                             
    def show(self):
        """Show the view"""
        self._visible = True
        self.attachView()
        self.updateVisible()
    
    
    def attachView(self):
        formLayout(self._parent, e=True,
            af=[(self._layout, 'top', self._attachMargin),
                (self._layout, 'left', self._attachMargin),
                (self._layout, 'right', self._attachMargin),
                (self._layout, 'bottom', self._attachMargin) ]
        )
    
    def detachView(self):
        formLayout(self._parent, e=True,
            ap=[(self._layout, 'left', 0, 100)]
        )
    
    def updateVisible(self):
        """The visible switch has a glitch, therefore
        it has been swapped with attaching hidden views
        to the gui form in a way that makes them
        invisible"""
        if not self._layout is None:
            self._layout.setVisible(self._visible)
            self.log.debug('    %s -> %s' % (self.viewName, self._visible and 'visible' or 'hidden'))
        else:
            self.log.error('    %s has not been created yet' % self._layout)
        setParent('..')
    
    def viewItem(self, viewName, l=None, ann='', bgc=[.25, .25, .25], en=True):
        """Create a button used to link to another view"""
        if l is None: l = viewName
        btn = button(l=l, c=Callback(self.showView, viewName), ann=ann, h=self._viewItemHeight, bgc=bgc, en=en)
        return btn
    
    def frameItem(self, l='', c=None, ann='', bgc=None, en=True, mw=4, mh=4, bs='etchedIn'):
        """Create a small frame with no label and a button with a description"""
        with frameLayout(lv=False, mw=mw, mh=mh, bs=bs) as frame:
            with formLayout(en=en) as form:
                btn = button(l=l, c=c, ann=ann, w=self._frameItemWidth)
                if bgc != None: btn.setBackgroundColor(bgc)
                if c != None: btn.setCommand(c)
                txt = text(l=ann, al='center')
            formLayout(form, e=True, af=[(btn, 'top', 0), (btn, 'left', 0), (btn, 'right', 0), (txt, 'left', 0), (txt, 'right', 0), (txt, 'bottom', 0)], ac=[(txt, 'top', 4, btn)])
        return frame, form, btn, txt
    
    def iconItem(self, l='', i=None, c=None, ann=None, bgc=None, en=True, mw=2, mh=2, bs='etchedIn', st='iconAndTextHorizontal'):
        """Create an icon button with a frame layout"""
        with frameLayout(lv=False, mw=mw, mh=mh, bs=bs) as frame:
            btn = iconTextButton(l=l, st=st, en=en)
            if bgc != None: btn.setBackgroundColor(bgc)
            if c != None: btn.setCommand(c)
            if i != None: btn.setImage(i)
            if ann != None: btn.setAnnotation(ann)
        return frame, btn




