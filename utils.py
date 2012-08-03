#!/usr/bin/env python
# encoding: utf-8
"""
viewGui.utils

Created by Bohdon Sayre on 2012-06-21.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

import pymel.core as pm
import math
import os
import re
import subprocess
import sys


def asList(value):
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        return [value]
    return value

def getAttrTitle(attr):
    n = attr.longName()
    return re.sub('([A-Z])', ' \\1', n).title()

def getRadialMenuPositions(count):
    """ Return a list of radial positions for the given number of items """
    if count < 0:
        raise ValueError('count cannot be negative')
    defaults = [
        [], ['N'], ['N', 'S'], ['N', 'SE', 'SW'], ['N', 'E', 'S', 'W'],
    ]
    ordered = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    if count < len(defaults):
        return defaults[count]
    else:
        results = []
        for i in range(count):
            if i < len(ordered):
                results.append(ordered[i])
            else:
                results.append(None)
        return results

def title(bs='out', *args, **kwargs):
    """
    Creates a frame layout with a text item inside. Only exposed control is the
    border style of the frame layout.

    Returns frame layout and text item.
    """
    with pm.frameLayout(lv=False, bs=bs) as frame:
        txt = pm.text(*args, **kwargs)
    return frame, txt


def attrControl(attr, cw=200, lw=100, ls=4, al='right', **kwargs):
    """
    Automatically create a control for the given node attribute.
    This returns a attrControlGrp but sets it up with more configurability.

    `cw` -- the content width
    `lw` -- the label width
    `ls` -- the spacing between the label and content
    `al` -- the label alignment
    """
    ctl = pm.attrControlGrp(a=attr, **kwargs)
    children = ctl.getChildren()
    count = len(children)
    label, child1 = children[0:2]
    label = pm.ui.Text(label)
    row = label.parent()
    # increase label padding
    row.columnAttach((1, 'right', ls))
    row.columnAlign((1, al))
    label.setWidth(lw)
    label.setAlign(al)
    # resize contents
    row.columnWidth((1, lw))
    for i in range(1, count):
        w = cw / float(count - 1)
        row.columnWidth((i+1, w))
    # handle check box labels
    if isinstance(child1, pm.ui.CheckBox):
        label.setLabel(child1.getLabel())
        child1.setLabel('')
        if kwargs.has_key('h'):
            h = kwargs['h']
        else:
            h = 20
        row.setHeight(h)
    # handle single number fields
    if attr.type() in ('long', 'int', 'double', 'float'):
        row.columnWidth((2, cw / 3.0))
    # handle sliders with nav button
    if count == 4 and isinstance(children[2], pm.ui.FloatSlider):
        row.columnWidth((3, cw / 3.0 * 2))
    return ctl

def layoutForm(form, ratios, spacing=2, offset=0, vertical=False, fullAttach=True, flip=False):
    """
    Layout the given form with the given list of ratios.
    Currently only supports fixed sized controls on the outer edges,
    eg. ratios of 0 cannot be within two higher ratios.

    `form` -- the formLayout to adjust
    `ratios` -- a list ratios for each child of the form
    `spacing` -- the space between controls
    `offset` -- the space between controls and the edge of the form
    `vertical` -- whether we should lay out the form veritcally or horizontally
    `fullAttach` -- whether the sides for each control should also be attached or left alone
    `flip` -- attach the bottom or right sides first
    """
    return layoutFormChildren(form, form.getChildren(), ratios, spacing, offset, vertical, fullAttach, flip)


def layoutFormChildren(form, children, ratios, spacing=2, offset=0, vertical=False, fullAttach=True, flip=False):
    """
    Layout the given form and specified children with the given ratios.

    `form` -- the formLayout to adjust
    `children` -- the list of children associated with the list of ratios
    `ratios` -- a list ratios for each child of the form
    `spacing` -- the space between controls
    `offset` -- the space between controls and the edge of the form
    `vertical` -- whether we should lay out the form veritcally or horizontally
    `fullAttach` -- whether the sides for each control should also be attached or left alone
    `flip` -- attach the bottom or right sides first
    """
    children = asList(children)
    ratios = asList(ratios)
    if len(ratios) != len(children):
        raise ValueError('the list of ratios must match the list of children in the form')
    divs = form.getNumberOfDivisions()
    total = sum(ratios)
    attached = []
    pairs = zip(children, ratios)
    akey = 'top' if vertical else 'left'
    bkey = 'bottom' if vertical else 'right'
    fixedEnds = []
    # attach all fixed-width
    fixedGrps = ((pairs, akey), (reversed(pairs), bkey))
    if flip:
        fixedGrps = reversed(fixedGrps)
    for loop, key in fixedGrps:
        prev = None
        for child, r in loop:
            if r is not 0 or child in attached:
                fixedEnds.append(prev)
                break
            if prev is None:
                kw = dict(af=[(child, key, offset)])
            else:
                kw = dict(ac=[(child, key, spacing, prev)])
            pm.formLayout(form, e=True, **kw)
            prev = child
            attached.append(child)
    # attach all expanding
    expand = [p for p in pairs if p[0] not in attached]
    curUnit = 0
    lastPos = None
    for i in range(len(expand)):
        child, r = expand[i]
        aused = False
        if i == 0:
            aused = True
            # attach to first fixed group
            if fixedEnds[0] is None:
                pm.formLayout(form, e=True, af=[(child, akey, offset)])
            else:
                pm.formLayout(form, e=True, ac=[(child, akey, spacing, fixedEnds[0])])
        bused = False
        if i == len(expand) - 1:
            bused = True
            # attach to second fixed group
            if fixedEnds[1] is None:
                pm.formLayout(form, e=True, af=[(child, bkey, offset)])
            else:
                pm.formLayout(form, e=True, ac=[(child, bkey, spacing, fixedEnds[1])])
        # attach to position
        pos = (float(r+curUnit) / total) * divs
        curUnit += r
        if not aused:
            pm.formLayout(form, e=True, ap=[(child, akey, spacing, lastPos)])
        if not bused:
            pm.formLayout(form, e=True, ap=[(child, bkey, spacing, pos)])
        lastPos = pos
    # full attach
    if fullAttach:
        aokey = 'left' if vertical else 'top'
        bokey = 'right' if vertical else 'bottom'
        for c in children:
            af = [(c, k, offset) for k in (aokey, bokey)]
            pm.formLayout(form, e=True, af=af)


def attachFormChildren(form, children, terms, offset=2, ctl=None, pos=None):
    """
    Macro way to attach multiple children to a control, side, or position.
    """
    children = asList(children)
    terms = asList(terms)
    if ctl is not None:
        key = 'ac'
        format = [offset, ctl]
    elif pos is not None:
        key = 'ap'
        format = [offset, pos]
    else:
        key = 'af'
        format = [offset]
    items = [[c, t] + format for c in children for t in terms]
    kw = {key:items}
    pm.formLayout(form, e=True, **kw)



def gridFormLayout(numberOfRows=None, numberOfColumns=None, spacing=2, **kwargs):
    return GridFormLayout(numberOfRows, numberOfColumns, spacing, **kwargs)


class GridFormLayout(object):
    def __init__(self, numberOfRows=None, numberOfColumns=None, spacing=2, **kwargs):
        self.numberOfRows = numberOfRows
        self.numberOfColumns = numberOfColumns
        self.spacing = spacing
        self.form = pm.formLayout(**kwargs)

    def __enter__(self):
        self.form.__enter__()
        return self

    def __exit__(self, type, value, traceback):
        self.form.__exit__(type, value, traceback)
        self.buildFormGrid()

    def buildFormGrid(self):
        elements = self.form.children()
        nc = self.numberOfColumns
        nr = self.numberOfRows
        attaches = []
        # get the number of rows and columns
        if nr is None and nc is None:
            nr = math.floor(math.sqrt(len(elements)))
            while len(elements) % nr != 0:
                nr -= 1
            nc = math.ceil(len(elements) / nr)
        if nc is None:
            nc = math.ceil(len(elements) / float(nr))
        if nr is None:
            nr = math.ceil(len(elements) / float(nc))
        # build the attachPosition list
        for n, element in enumerate(elements):
            j = math.floor(n / nc)
            i = n - (j * nc)
            attaches.append((element, 'left', self.spacing, 100 * i / nc))
            attaches.append((element, 'top', self.spacing, 100 * j / nr))
            attaches.append((element, 'right', self.spacing, 100 * (i + 1) / nc))
            attaches.append((element, 'bottom', self.spacing, 100 * (j + 1) / nr))
        pm.formLayout(self.form, e=True, ap=attaches)


class ItemList(object):
    """
    ItemList wraps a textScrollList control allowing you to
    easily list and retrieve more complex objects.

    The displayed names for each item are determined by
    the encode method, which can be overridden.
    """
    def __init__(self, items=None, format='{name}', encode=None, **kwargs):
        self._format = format
        self._customEncode = encode
        self.build(**kwargs)
        self.items = items

    @property
    def items(self):
        return self._items
    @items.setter
    def items(self, value):
        value = asList(value)
        self._items = value
        self.update()

    @property
    def encode(self):
        return self._customEncode
    @encode.setter
    def encode(self, value):
        if hasattr(value, '__call__') or value is None:
            self._customEncode = value
            self.update()

    @property
    def format(self):
        return self._format
    @format.setter
    def format(self, value):
        self._format = str(value)
        self.update()

    @property
    def selected(self):
        return [self.items[i] for i in self.selectedIndeces]
    @selected.setter
    def selected(self, value):
        value = asList(value)
        indeces = [i for i in range(len(self.items)) if self.items[i] in value]
        self.selectedIndeces = indeces

    @property
    def selectedNames(self):
        return [self._encode(i) for i in self.selected]
    @selectedNames.setter
    def selectedNames(self, value):
        value = asList(value)
        indeces = [i for i in range(len(self.items)) if self._encode(self.items[i]) in value]
        self.selectedIndeces = indeces

    @property
    def selectedIndeces(self):
        return [i-1 for i in self.control.getSelectIndexedItem()]
    @selectedIndeces.setter
    def selectedIndeces(self, value):
        value = asList(value)
        indeces = [i+1 for i in value if i in range(len(self.items))]
        self.control.deselectAll()
        self.control.setSelectIndexedItem(indeces)

    def build(self, **kwargs):
        self.control = pm.textScrollList(**kwargs)

    def _encode(self, item):
        val = item
        if self._customEncode is not None:
            val = self._customEncode(item)
        return str(val)

    def update(self):
        """ Update the list to represent the current items """
        names = [self._encode(i) for i in self.items]
        self.control.removeAll()
        for i, n in enumerate(names):
            # format encoded name
            n = self.format.format(index=i+1, name=n)
            self.control.append(n)


class ManageableList(ItemList):
    def __init__(self, *args, **kwargs):
        super(ManageableList, self).__init__(*args, **kwargs)
        self.addCommand = None
        self.removeCommand = None
        self.clearCommand = None

    def build(self, **kwargs):
        fkw = {}
        for k in ('h', 'bgc'):
            if kwargs.has_key(k):
                fkw[k] = kwargs[k]
        with pm.formLayout(**fkw) as form:
            lst = self.control = pm.textScrollList(**kwargs)
            add = pm.button(l='+', w=20, h=20, ann='Add', c=pm.Callback(self.onAdd))
            rem = pm.button(l='-', w=20, h=20, ann='Remove', c=pm.Callback(self.onRemove))
            clr = pm.button(l='x', w=20, h=20, ann='Clear', c=pm.Callback(self.onClear))
            pm.formLayout(form, e=True,
                af=[(lst, 'left', 0), (lst, 'top', 0), (lst, 'bottom', 0), (clr, 'right', 0),
                    (add, 'bottom', 0), (rem, 'bottom', 0), (clr, 'bottom', 0)],
                ac=[(rem, 'right', 4, clr), (add, 'right', 4, rem), (lst, 'right', 4, add)],
            )
        self.layout = form

    def setHeight(self, value):
        self.layout.setHeight(value)
    def getHeight(self):
        return self.layout.getHeight()

    def onAdd(self):
        if self.addCommand is not None:
            self.addCommand(self)

    def onRemove(self):
        self.items = [i for i in self.items if i not in self.selected]
        if self.removeCommand is not None:
            self.removeCommand(self)

    def onClear(self):
        self.items = None
        if self.clearCommand is not None:
            self.clearCommand(self)


class NodeList(ItemList):
    def __init__(self, *args, **kwargs):
        kwargs['sc'] = pm.Callback(self.onSelect)
        super(NodeList, self).__init__(*args, **kwargs)
        self.selectCommand = None

    @property
    def items(self):
        return self._items
    @items.setter
    def items(self, value):
        value = asList(value)
        value = [v for v in value if hasattr(v, 'select') or isinstance(v, pm.Attribute)]
        self._items = value
        self.update()
    
    def onSelect(self):
        pm.select(self.selected)
        if hasattr(self.selectCommand, '__call__'):
            self.selectedCommand(self.selected)


class BrowsePathForm(object):
    """
    Creates a form with a path text field and a button
    to browse for an existing file or folder.
    """
    def __init__(self, label=None, files=True, labelWidth=50):
        self.labelWidth = labelWidth
        self.build()
        self.label = label
        self.browseCaption = 'Choose a {itemTerm}'
        self.browseOkCaption = 'Choose'
        self.files = files
        self.changeCommand = None

    @property
    def path(self):
        return self.pathField.getText()
    @path.setter
    def path(self, value):
        self.pathField.setText(value)

    @property
    def directory(self):
        if os.path.exists(self.path):
            if os.path.isdir(self.path):
                return self.path
            else:
                return os.path.dirname(self.path)

    @property
    def label(self):
        return self.labelText.getLabel()
    @label.setter
    def label(self, value):
        self.labelText.setManage(value is not None)
        self.labelText.setLabel(value)

    @property
    def fileMode(self):
        return 1 if self.files else 2

    @property
    def itemTerm(self):
        return 'File' if self.files else 'Directory'

    def build(self):
        with pm.formLayout() as form:
            lbl = self.labelText = pm.text(l='', al='right', w=self.labelWidth)
            pth = self.pathField = pm.textField(tx='', cc=pm.Callback(self.onChange))
            self.buildShowMenu(self.pathField)
            brs = self.browseBtn = pm.button(l='Browse', h=20, c=pm.Callback(self.browse))
            pm.formLayout(form, e=True,
                af=[(lbl, 'top', 4), (lbl, 'left', 0), (brs, 'right', 0)],
                ac=[(pth, 'left', 4, lbl), (pth, 'right', 4, brs)],
            )
        self.layout = form
        return form

    def buildShowMenu(self, parent):
        pm.popupMenu(p=parent)
        pm.menuItem(l='Show...', c=pm.Callback(self.show))

    def onChange(self):
        if self.changeCommand is not None:
            self.changeCommand(self.path)

    def show(self):
        if os.path.exists(self.path):
            if os.path.isdir(self.path):
                path = self.path
            else:
                path = os.path.dirname(self.path)
        if sys.platform == 'win32':
            cmd = ['explorer.exe']
        else:
            cmd = ['open']
        cmd.append(os.path.normpath(path))
        subprocess.Popen(cmd)

    def browse(self):
        kw = dict(
            cap=self.browseCaption.format(itemTerm=self.itemTerm),
            okc=self.browseOkCaption,
            fm=self.fileMode
        )
        dir_ = self.directory
        if dir_ is not None:
            kw['dir'] = dir_
        path = pm.fileDialog2(**kw)
        if path is not None:
            self.path = path[0]
            self.onChange()


class PathButtonForm(object):
    """
    Creates a row of buttons that represent each item of
    a path. Clicking on a button returns the path to that item.
    """
    ROOT_REGEX = re.compile('^(/|//|[a-zA-Z]+:)[^/]*$')

    def __init__(self, path=None, command=None):
        self._path = path
        self.command = command
        self.build()

    @property
    def path(self):
        return self._path
    @path.setter
    def path(self, value):
        if value is not None:
            value = value.replace('\\', '/')
        self._path = value
        self.update()

    @property
    def pathItems(self):
        items = []
        if self.path is None:
            return items
        pth = self.path
        while True:
            items.append(pth)
            if self.ROOT_REGEX.match(pth):
                break
            pth, base = os.path.split(pth)
            if not len(pth) or not len(base):
                # failsafe
                break
        return list(reversed(items))

    def build(self):
        with pm.columnLayout() as self.layout:
            self.buildPathForm()

    def buildPathForm(self):
        with pm.formLayout() as form:
            paths = self.pathItems
            seps = 0
            for i, path in enumerate(paths):
                if i != 0:
                    seps += 1
                    pm.text(l='/')
                elif self.ROOT_REGEX.match(path):
                    if path.startswith('/'):
                        seps += 1
                        pm.text(l=re.search('/+', path).group())
                pm.button(l=os.path.basename(path), h=18, bgc=(0.3, 0.3, 0.3), c=pm.Callback(self._command, path))
            layoutForm(form, [0] * (len(paths) + seps))

    def _command(self, path):
        if hasattr(self.command, '__call__'):
            pm.evalDeferred(pm.Callback(self.command, path))

    def update(self):
        # TODO: update buttons in a relative fashion
        # so that clicked buttons dont get deleted and recreated
        self.layout.clear()
        with self.layout:
            self.buildPathForm()



