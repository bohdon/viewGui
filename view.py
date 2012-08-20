#!/usr/bin/env mayapy
# encoding: utf-8
"""
viewGui.view

Created by Bohdon Sayre on 2010-01-01.
Copyright (c) 2012 Bohdon Sayre. All rights reserved.
"""

import pymel.core as pm
import logging
import os
import utils

__all__ = [
    'View',
    'IconCaptureView',
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
    onSelectionChange = None
    onSceneChange = None
    onUndo = None
    onRedo = None
    onWindowClosed = None
    
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
            with pm.formLayout() as self._layout:
                self.build()
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

    def build(self):
        """ Build the main header and body for this view. """
        with pm.frameLayout('%sHeadFrame' % self.viewName, mw=self._headMargins[0], mh=self._headMargins[1], lv=False, bv=False) as self._headFrame:
            self.buildHeader()
        with pm.frameLayout('%sFrame' % self.viewName, mw=self._bodyMargins[0], mh=self._bodyMargins[1], lv=False, bv=False) as self._bodyFrame:
            self.buildBody()
        utils.layoutForm(self._layout, (0, 1), spacing=2, vertical=True)
    
    def buildHeader(self):
        """
        Create buttons at the top of the view. These link to other views,
        and display the current view by highlighting it in white.
        
        If a custom header is desired, this can method should be overridden.
        """
        links = self.links()
        if links != []:
            with pm.frameLayout(lv=False, bs='out'):
                with pm.formLayout('{0}LinkForm'.format(self.viewName), bgc=self._linkBgc) as form:
                    last = None
                    for viewName in links:
                        name = None
                        if self.gui.hasView(viewName):
                            name = self.gui.getViewClass(viewName).displayName
                        if name is None:
                            name = viewName
                        btn = pm.button(l=name, c=pm.Callback(self.showView, viewName), h=18)
                        if viewName == self.viewName:
                            btn.setBackgroundColor([.86, .86, .86])
                        if last is None:
                            pm.formLayout(form, e=True, af=[(btn, 'left', 0)])
                        else:
                            pm.formLayout(form, e=True, ac=[(btn, 'left', 2, last)])
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
        btn = pm.button(l=l, c=pm.Callback(self.showView, viewName), ann=ann, h=self._viewItemHeight, bgc=bgc, en=en)
        return btn
    
    def frameItem(self, l='', c=None, ann='', bgc=None, en=True, mw=4, mh=4, bs='etchedIn'):
        """Create a small frame with no label and a button with a description"""
        with pm.frameLayout(lv=False, mw=mw, mh=mh, bs=bs) as frame:
            with pm.formLayout(en=en) as form:
                btn = pm.button(l=l, c=c, ann=ann, w=self._frameItemWidth)
                if bgc != None: btn.setBackgroundColor(bgc)
                if c != None: btn.setCommand(c)
                txt = pm.text(l=ann, al='center')
            utils.layoutForm(form, (0, 1), vertical=True)
        return frame, form, btn, txt
    
    def iconItem(self, l='', i=None, c=None, ann=None, bgc=None, en=True, mw=2, mh=2, bs='etchedIn', st='iconAndTextHorizontal'):
        """Create an icon button with a frame layout"""
        with pm.frameLayout(lv=False, mw=mw, mh=mh, bs=bs) as frame:
            btn = pm.iconTextButton(l=l, st=st, en=en)
            if bgc != None: btn.setBackgroundColor(bgc)
            if c != None: btn.setCommand(c)
            if i != None: btn.setImage(i)
            if ann != None: btn.setAnnotation(ann)
        return frame, btn




class IconCaptureView(View):
    @property
    def iconSize(self):
        return self._iconSize
    @iconSize.setter
    def iconSize(self, value):
        self._iconSize = value
        self.updateEditorFrame()

    def buildBody(self):
        self._iconSize = self.gui.iconSize
        self.minSize = 128
        self.maxSize = 512
        self.tempFileName = 'mayaIcon{0}.png'
        self.gui.window.setToolbox(True)
        self.camera = self.newCamera()
        with pm.formLayout() as form:
            with pm.columnLayout():
                kw = dict(w=128, h=128)
                with pm.frameLayout(lv=False, bv=False, **kw) as self.editorFrame:
                    self.panel = pm.modelPanel(cam=self.camera, mbv=False, l='Icon Capture View')
                    self.setupModelEditor(self.panel.getModelEditor())
                    bar = self.panel.getBarLayout()
                    pm.layout(bar, e=True, m=False)
            with pm.formLayout() as form2:
                self.buildFooter()
                utils.layoutForm(form2, 1)
            utils.layoutForm(form, (0, 1), vertical=True)
        self.updateEditorFrame()
        pm.refresh()

    def buildFooter(self):
        """ Override to build custom footer content for capturing icons """
        pm.button(l='Choose', c=pm.Callback(self.captureIcon))

    def updateEditorFrame(self):
        bigger = max(*self.iconSize)
        fit = min(max(self.minSize, bigger * 2), self.maxSize)
        scale = fit / float(bigger)
        size = [s * scale for s in self.iconSize]
        self.gui.window.setWidth(size[0])
        self.gui.window.setHeight(size[1])
        self.editorFrame.setWidth(size[0])
        self.editorFrame.setHeight(size[1])

    def newCamera(self):
        sel = pm.selected()
        c = pm.camera(n='iconCaptureCamera')[0]
        pm.viewSet(c, home=True)
        c.focalLength.set(150)
        pm.select(sel)
        pm.viewSet(c, fit=True)
        return c

    def setupModelEditor(self, me):
        """
        Setup the view style of the model editor, sometimes the model editor cant
        be found for some reason so we just have to accept it if we cant adjust it.
        """
        if me is None:
            return
        me = pm.ui.ModelEditor(me.split('|')[-1])
        try:
            pm.modelEditor(me, e=True, da='smoothShaded', dtx=True, allObjects=False, sel=False)
            pm.modelEditor(me, e=True, manipulators=False, grid=False, hud=False)
            pm.modelEditor(me, e=True, polymeshes=True, subdivSurfaces=True, nurbsSurfaces=True)
        except:
            pass

    def onWindowClosed(self):
        if pm.modelPanel(self.panel, q=True, ex=True):
            pm.deleteUI(self.panel, pnl=True)
        if self.camera.exists():
            pm.delete(self.camera)

    def captureIcon(self, filename=None, close=True):
        """
        Save an image with the current camera to the given filename.
        If no filename is given the image will be saved in a temp directory.
        Returns the path to the rendered image.
        """
        if filename is None:
            filename = self.getTempFile()
            if filename is None:
                self.log.warning('could not get a temporary file')
                return
        # check directory
        dir_ = os.path.dirname(filename)
        if not os.path.isdir(dir_):
            self.log.warning('cannot save image to missing directory: {0}'.format(dir_))
            return
        # render image
        self.renderIcon(filename)
        if close:
            self.closeWindow()
        return filename

    def renderIcon(self, filename):
        kw = dict(w=self.iconSize[0], h=self.iconSize[1], cam=self.panel.getCamera())
        utils.renderIcon(filename, **kw)
        self.log.info(filename)

    def getTempFile(self):
        import tempfile
        dir = tempfile.gettempdir()
        for i in range(1000):
            f = os.path.join(dir, self.tempFileName.format(i))
            if not os.path.isfile(f):
                return f

    def closeWindow(self):
        if pm.window(self.gui.window, ex=True):
            pm.deleteUI(self.gui.window)




