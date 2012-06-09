#!/usr/bin/env mayapy
# encoding: utf-8
"""
viewGui.view

Created by Bohdon Sayre on 2010-01-01.
Copyright (c) 2012 Bohdon Sayre. All rights reserved.
"""


from pymel.core import *
import logging

__all__ = [
    'View',
]

class View(object):
    """
    Template class for a ViewGui View.
    
    Views mainly consist of a frameLayout containing any controls
    and their corresponding methods.
    
    Subclasses of View should override buildBody or buildHeader to build
    custom content in the view. This content is only built once, unless
    persistent is set to False, in which case the View is recreated
    each time that it is shown.
    
    The view's metrics can be controlled by setting the width or height
    attributes, though the Gui can choose to ignore these.  The gui will
    also remember and restore the last size of the window when it was
    visible if rememberMetrics is set to True.
    """
    
    displayName = None
    rememberMetrics = False
    metrics = None
    persistent = True
    
    _layout = None
    _headFrame = None
    _bodyFrame = None
    _headMargins = [0, 0]
    _bodyMargins = [4, 4]
    _linkBgc = [0.2, 0.2, 0.2]
    
    _viewItemHeight = 34
    _frameItemWidth = 90
    
    def __init__(self, parent, gui):
        self._parent = parent
        self.gui = gui
        self.showView = gui.showView
        self.viewName = self.__class__.__name__
        self.log = logging.getLogger('viewGui.view.{0}'.format(self.viewName))
    
    def __del__(self):
        self.log.debug('destroyed')
        self.destroy()
    
    @property
    def visible(self):
        return self._layout.getManage()
    @visible.setter
    def visible(self, value):
        self._layout.setManage(value)
    
    def destroy(self):
        """ Delete the layout of this view"""
        try:
            self._layout.delete()
        except:
            pass
    
    def create(self):
        self.log.debug('building')
        with self._parent:
            with formLayout() as self._layout:
                self.allContent()
        self.hide()
    
    def hide(self):
        self.visible = False
        self.onHide()
    
    def show(self):
        self.visible = True
        self.onShow()
    
    def onHide(self):
        pass
    
    def onShow(self):
        pass
    
    def allContent(self):
        """
        Create two frame layouts as a header and body.
        """
        with frameLayout('%sHeadFrame' % self.viewName, mw=self._headMargins[0], mh=self._headMargins[1], lv=False, bv=False) as self._headFrame:
            self.buildHeader()
        with frameLayout('%sFrame' % self.viewName, mw=self._bodyMargins[0], mh=self._bodyMargins[1], lv=False, bv=False) as self._bodyFrame:
            self.buildBody()
        formLayout(self._layout, e=True,
            af=[(self._headFrame, 'top', 0), (self._headFrame, 'left', 0), (self._headFrame, 'right', 0),
                (self._bodyFrame, 'left', 0), (self._bodyFrame, 'right', 0), (self._bodyFrame, 'bottom', 0)],
            ac=[(self._bodyFrame, 'top', 2, self._headFrame)])
    
    def buildHeader(self):
        """
        Create buttons at the top of the view. These link to other views,
        and display the current view by highlighting it in white.
        
        If a custom header is desired, this can method should be overridden.
        """
        links = self.links()
        if links != []:
            with frameLayout(lv=False, bs='out'):
                with formLayout('{0}LinkForm'.format(self.viewName), bgc=self._linkBgc) as form:
                    last = None
                    for viewName in links:
                        name = None
                        if self.gui.hasView(viewName):
                            name = self.gui.getViewClass(viewName).displayName
                        if name is None:
                            name = viewName
                        btn = button(l=name, c=Callback(self.showView, viewName), h=18)
                        if viewName == self.viewName:
                            btn.setBackgroundColor([.86, .86, .86])
                        if last is None:
                            formLayout(form, e=True, af=[(btn, 'left', 0)])
                        else:
                            formLayout(form, e=True, ac=[(btn, 'left', 2, last)])
                        last = btn
        self._headFrame.setManage(len(links) > 0)

    def buildBody(self):
        """Create the main content of the view.
        This method should always be overrided."""
        self.log.warning('buildBody was not overridden')
        pass
    
    def links(self):
        """
        Return a list of the view names for this view's header.
        This is usually the view's hierarchy, with the current
        view being listed last, and the highest view first.
        This method should always be overriden.
        
        ex. ['MainView, 'SecondPageView', 'ThirdPageView', self.viewName]
        """
        return []
    
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




