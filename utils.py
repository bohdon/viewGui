#!/usr/bin/env python
# encoding: utf-8
"""
viewGui.utils

Created by Bohdon Sayre on 2012-06-21.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

import pymel.core as pm
import logging
import math
import os
import re
import shutil
import subprocess
import sys

LOG = logging.getLogger(__name__)

SHOW_MSG = 'Show in ' + ('Finder' if sys.platform == 'darwin' else 'Explorer')


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



def autoAttrControl(attr, attrKwargs={}, compoundKwargs={}, multiKwargs={}, customBuilder=None, customKwargs={}):
    """
    Create a control layout automatically for the given attribute.
    Determines whether to create a normal control form, a compound or multi layout.

    `attrKwargs` -- kwargs to pass to attrControl
    `compoundKwargs` -- kwargs to pass to CompoundAttrLayout
    `multiKwargs` -- kwargs to pass to MultiAttrLayout
    `customBuilder` -- if given, will use this function to build message attribute forms
    `customKwargs` -- kwargs to pass to the given customBuilder
    """
    autoKwargs = locals()
    del autoKwargs['attr']
    # custom
    if hasattr(customBuilder, '__call__'):
        result = customBuilder(attr, **customKwargs)
        if result:
            return result
    # multi
    if attr.isMulti():
        return MultiAttrLayout(attr, autoKwargs=autoKwargs, **multiKwargs)
    # compound
    if attr.isCompound() and attr.type() not in CompoundAttrLayout.compoundTypes:
        return CompoundAttrLayout(attr, autoKwargs=autoKwargs, **compoundKwargs)
    # normal attribute
    try:
        result = attrControl(attr, **attrKwargs)
    except:
        result = unknownAttrControl(attr, **attrKwargs)
    return result


def attrControl(attr, cw=200, lw=100, ls=4, al='right', labelfnc=None, **kwargs):
    """
    Automatically create a control for the given node attribute.
    This returns a attrControlGrp but sets it up with more configurability.

    `cw` -- the content width
    `lw` -- the label width
    `ls` -- the spacing between the label and content
    `al` -- the label alignment
    """
    if hasattr(labelfnc, '__call__'):
        kwargs['l'] = labelfnc(attr)
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


def unknownAttrControl(attr, lw=100, cw=200, ls=4, al='right', labelfnc=None, **kwargs):
    with pm.formLayout(h=20) as form:
        if hasattr(labelfnc, '__call__'):
            kwargs['l'] = labelfnc(attr)
        else:
            kwargs['l'] = getAttrTitle(attr)
        pm.text(en=False, w=lw, al=al, **kwargs)
        pm.separator(st='none')
        layoutForm(form, (0, 1))
    return form



class CompoundAttrLayout(object):
    compoundTypes = ['float2', 'float3', 'double2', 'double3', 'long2', 'long3', 'short2', 'short3']

    def __init__(self, attr, autoKwargs={}, w=300, labelfnc=None, **kwargs):
        if not attr.isCompound():
            raise ValueError('{0} is not a compound attribute'.format(attr))
        self.attr = attr
        self.autoKwargs = autoKwargs
        self.labelfnc = labelfnc
        self.build(w=w, **kwargs)

    def __str__(self):
        return str(self.layout)

    @property
    def label(self):
        if hasattr(self.labelfnc, '__call__'):
            return self.labelfnc(self.attr)
        return getAttrTitle(self.attr)

    def build(self, w=300, **kwargs):
        kw = dict(l=self.label, bs='etchedIn', mw=4, mh=4, w=w)
        kw.update(kwargs)
        with pm.frameLayout(**kw) as self.layout:
            self.buildContent()

    def buildContent(self):
        with pm.columnLayout(adj=True, rs=2):
            for a in self.attr.children():
                autoAttrControl(a, **self.autoKwargs)

    def update(self):
        self.layout.clear()
        with self.layout:
            self.buildContent()


def addMultiItem(attr, insert=False):
    """
    Add an item to the given multi attribute.
    `insert` -- insert into the first available index, otherwise adds to the end
    """
    if not attr.isMulti():
        raise ValueError('{0} is not a multi attribute'.format(attr))
    indices = attr.getArrayIndices()
    max = -1
    if len(indices):
        max = sorted(indices)[-1]
    index = None
    if insert:
        for i in range(max+1):
            if i not in indices:
                index = i
                break
    if index is None:
        index = max + 1
    attr[index].get()
    return attr[index]

def removeMultiItem(attr, index):
    """
    Remove the given index from the given multi attribute.
    This will not work if an attrControl exists for the attribute.
    """
    if not attr.isMulti():
        raise ValueError('{0} is not a multi attribute'.format(attr))
    pm.removeMultiInstance(attr[index], b=True)


class MultiAttrLayout(object):
    def __init__(self, attr, autoKwargs={}, w=300, labelfnc=None, **kwargs):
        if not attr.isMulti():
            raise ValueError('{0} is not a multi attribute'.format(attr))
        self.attr = attr
        self.autoKwargs = autoKwargs
        self.labelfnc = labelfnc
        self.build(w=w, **kwargs)

    def __str__(self):
        return str(self.layout)

    @property
    def label(self):
        if hasattr(self.labelfnc, '__call__'):
            return self.labelfnc(self.attr)
        l = getAttrTitle(self.attr)
        l = '{0} ({1})'.format(l, self.attr.numElements())
        return l

    def build(self, w=300, **kwargs):
        kw = dict(l=self.label, bs='etchedIn', mw=4, mh=4, w=w)
        kw.update(kwargs)
        with pm.frameLayout(**kw) as self.layout:
            self.buildContent()

    def buildContent(self):
        with pm.columnLayout(adj=True, rs=2) as self.column:
            pm.button(l='Add Item', c=pm.Callback(self.addItem))
            for i in self.attr.getArrayIndices():
                self.buildItem(i)

    def buildItem(self, index):
        with pm.formLayout() as form:
            autoAttrControl(self.attr[index], **self.autoKwargs)
            pm.iconTextButton(i='removeRenderable.png', st='iconOnly', c=pm.Callback(self.removeItem, index, form))
            layoutForm(form, (1, 0))

    def update(self):
        self.layout.clear()
        with self.layout:
            self.buildContent()

    def addItem(self):
        new = addMultiItem(self.attr)
        with self.column:
            self.buildItem(new.index())
        self.layout.setLabel(self.label)

    def removeItem(self, index, form):
        pm.deleteUI(form)
        removeMultiItem(self.attr, index)
        self.layout.setLabel(self.label)


class AttrIconTextCheckBox(object):
    """
    Creates an iconTextCheckBox that controls one or more attributes.
    """
    def __init__(self, attrs, l=None, **kwargs):
        self.attrs = attrs
        self.build(l=l, **kwargs)
        self.changeCallback = None

    def __str__(self):
        return str(self.control)

    @property
    def attrs(self):
        return self._attrs
    @attrs.setter
    def attrs(self, value):
        value = asList(value)
        value = [a for a in value if isinstance(a, pm.Attribute) and a.isSettable()]
        self._attrs = asList(value)


    def build(self, l=None, **kwargs):
        if l is None:
            if len(self.attrs):
                l = getAttrTitle(self.attrs[0])
            else:
                l = 'Attr Check Box'
        kw = dict(l=l, v=self.getAttrsValue(), st='textOnly', cc=pm.Callback(self.toggleAttrs))
        kw.update(kwargs)
        self.control = pm.iconTextCheckBox(**kw)

    def update(self):
        self.control.setValue(self.getAttrsValue())

    def getAttrsValue(self):
        """ Return the all value of all attributes """
        if not len(self.attrs):
            return False
        return all([a.get() for a in self.attrs])

    def toggleAttrs(self):
        off = [a for a in self.attrs if not a.get()]
        if len(off) == len(self.attrs):
            self.set(True)
            self.control.setValue(True)
        elif len(off):
            self.set(True, off)
            self.control.setValue(True)
        else:
            self.set(False)
            self.control.setValue(False)
        if hasattr(self.changeCallback, '__call__'):
            self.changeCallback()

    def set(self, value, attrs=None):
        if attrs is None:
            attrs = self.attrs
        for a in attrs:
            try:
                a.set(value)
            except:
                pass


class NodeSelectionCheckBox(object):
    """
    Creates an icon text check box that represents the selection of a set of nodes.
    Clicking the button toggles the selection of the nodes and the 'update'
    method can be used to change the state of the button to reflect whether or not
    all of the nodes are selected.
    """
    def __init__(self, nodes, **kwargs):
        self.build(**kwargs)
        self.nodes = nodes
        self.changeCallback = None

    def __str__(self):
        return str(self.control)

    @property
    def nodes(self):
        return self._nodes
    @nodes.setter
    def nodes(self, value):
        self._nodes = asList(value)
        self.update()

    def build(self, **kwargs):
        kw = dict(st='iconOnly', i='edit.png', cc=pm.Callback(self.toggleSelection))
        kw.update(kwargs)
        self.control = pm.iconTextCheckBox(**kw)

    def update(self):
        self.control.setValue(self.areNodesSelected())

    def areNodesSelected(self):
        if not len(self.nodes):
            return False
        sel = pm.selected()
        return all([n in sel for n in self.nodes])

    def toggleSelection(self):
        """
        Toggle the selection of the nodes.
        If none are selected, adds all, if some are selected, adds the remaining,
        if all are selected, removes all.
        """
        sel = pm.selected()
        missing = [n for n in self.nodes if n not in sel]
        if len(missing) == len(self.nodes):
            pm.select(self.nodes, add=True)
            self.control.setValue(True)
        elif len(missing):
            pm.select(missing, add=True)
            self.control.setValue(True)
        else:
            pm.select(self.nodes, d=True)
        if hasattr(self.changeCallback, '__call__'):
            self.changeCallback()



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

    def __str__(self):
        return str(self.form)

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

    def __str__(self):
        return str(self.control)

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
        if val is None:
            return ''
        return str(val)

    def update(self):
        """ Update the list to represent the current items """
        names = [self._encode(i) for i in self.items]
        self.control.removeAll()
        for i, n in enumerate(names):
            # format encoded name
            n = self.format.format(index=i+1, name=n)
            self.control.append(n)



class FilterList(ItemList):
    """
    FilterList provides an easy way to create a collection of textScrollLists
    whos contents represent parent-child relationships. A FilterList's selection
    will determine the contents of it's child FilterList, if any. FilterLists
    can be chained together to form any number of list collections.
    """
    def __init__(self, parent=None, child=None, items={}, *args, **kwargs):
        self.allItems = items
        self._searchFilter = None
        if kwargs.has_key('searchFilter'):
            self._searchFilter = kwargs['searchFilter']
            del kwargs['searchFilter']
        items = None
        self.parent = parent
        self.child = child
        self._findOverride = False
        self.selectCommand = None
        self.doubleClickCommand = None
        kwargs['selectCommand'] = pm.Callback(self._selectCommand)
        kwargs['doubleClickCommand'] = pm.Callback(self._doubleClickCommand)
        super(FilterList, self).__init__(*args, **kwargs)

    @property
    def searchFilter(self):
        return self._searchFilter
    @searchFilter.setter
    def searchFilter(self, value):
        self._searchFilter = value
        self.update()

    def update(self):
        # maintain the current selection
        sel = self.selectedNames
        self._items = self._getFilteredItems()
        super(FilterList, self).update()
        if isinstance(self.child, FilterList):
            self.child.update()
        # Reapply the selection
        # self.selectedNames(sel) #TODO

    def _filterDict(self, dictionary, keys=None):
        '''
        Filter the items from the supplied dictionary
        based on the supplied keys (Top-Level Only)
        '''
        result = {}
        for k, v in dictionary.items():
            v = self._validate(v)
            add = False
            if keys:
                if k in keys:
                    add = True
            else:
                add = True
            if add:
                if not result.has_key(k):
                    result[k] = []
                result[k].extend(v)
        return result

    def _getFilteredItems(self):
        ''' Filter the supplied items '''
        parentSel = None
        if isinstance(self.parent, FilterList):
            parentSel = self.parent.selected
        # compile the items based on the parent
        items = self._filterDict(self.allItems, parentSel)
        
        result = []
        allValues = []
        for item in items.values():
            allValues.extend(item)
        if self._searchFilter and self.child is None:
            for item in allValues:
                searches = re.split('[; |,]',self._searchFilter)
                found = False
                for search in searches:
                    if search in item:
                        found = True
                if found: result.append(item)
        else:
            result.extend(allValues)
        result.sort()

        return result

    def _validate(self, value):
        ''' Validate the given value from self.data '''
        if value is None:
            return []
        if not isinstance(value, list):
            value = [value]
        # ensure value items are strings
        value = [str(x) for x in value]
        return value

    def _selectCommand(self):
        if self.selectCommand is not None:
            self.selectCommand()
        if isinstance(self.child, FilterList):
            self.child.update()

    def _doubleClickCommand(self):
        if self.doubleClickCommand is not None:
            self._doubleClickCommand()
        if isinstance(self.child, FilterList):
            self.child.update()



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
        self._items = value
        self.update()
    
    def onSelect(self):
        nodes = [n for n in self.selected if hasattr(n, 'select') or isinstance(n, pm.Attribute)]
        pm.select(nodes)
        if hasattr(self.selectCommand, '__call__'):
            self.selectCommand(nodes)



class DataLayout(object):
    """
    Creates a layout for representing simple data. The data property
    can be supplied with any dictionary like information and will be used
    to automatically populate text objects.

    Linewrapping and truncation can be used to organize how the data is displayed.
    Functions that return custom controls can be added as values
    """
    def __init__(self, data=None, ratio=(1, 3), scroll=False, linewrap=None, truncate=None, sortedKeys=None):
        self.sortedKeys = sortedKeys
        self.build()
        self._ratio = ratio
        self._scroll = scroll
        self._linewrap = linewrap
        self._truncate = truncate
        self.offset = 2
        self.data = data

    def __str__(self):
        return str(self.layout)

    @property
    def data(self):
        return self._data
    @data.setter
    def data(self, value):
        self._data = value
        self.update()

    @property
    def ratio(self):
        return self._ratio
    @ratio.setter
    def ratio(self, value):
        self._ratio = value
        self.update()

    @property
    def scroll(self):
        return self._scroll
    @scroll.setter
    def scroll(self, value):
        self._scroll = value
        self.update()

    @property
    def linewrap(self):
        return self._linewrap
    @linewrap.setter
    def linewrap(self, value):
        self._linewrap = value
        self.update()

    @property
    def truncate(self):
        return self._truncate
    @truncate.setter
    def truncate(self, value):
        self._truncate = value
        self.update()

    def encode(self, value):
        value = str(value)
        if self.truncate is not None and len(value) > self.truncate:
            value = value[:self.truncate] + '...'
        return value

    def build(self):
        with pm.formLayout() as self.layout:
            pass

    def buildContent(self):
        if self.scroll:
            with pm.scrollLayout(cr=True, h=10):
                self.buildDataContent()
        else:
            self.buildDataContent()

    def buildDataContent(self):
        with pm.formLayout() as form:
            if not hasattr(self.data, 'items'):
                return
            last = None

            allItems = self.data.items()
            sortedItems = []
            if self.sortedKeys:
                # First remove each sorted key in order
                for key in self.sortedKeys:
                    for i, item in enumerate(allItems):
                        if key == item[0]:
                            sortedItems.append(allItems.pop(i))
            # Then add the rest
            sortedItems.extend(allItems)

            for item in sortedItems:
                k, v = item
                lbl = pm.text(l=self.encode(k), al='right', en=False)
                kw = dict(ww=self.linewrap) if self.linewrap is not None else {}
                if hasattr(v, '__call__'):
                    try:
                        val = v()
                    except:
                        LOG.error("Invalid control for key: {0}".format(k))
                else:
                    val = pm.text(l=self.encode(v), al='left', **kw)
                layoutFormChildren(form, (lbl, val), self.ratio, fullAttach=False)
                if last is not None:
                    attachFormChildren(form, (lbl, val), 'top', offset=self.offset, ctl=last)
                last = val

    def update(self):
        self.layout.clear()
        with self.layout:
            self.buildContent()
            layoutForm(self.layout, 1)
    
    def buildMetaDataForm(self):
        with pm.formLayout() as form:
            lastCtl = None
            for k, v in self.metaDataItems:
                label = pm.text(l=k, al='right', en=False)
                value = pm.text(l=v, al='left')
                pm.formLayout(form, e=True,
                    af=[(label, 'left', 0), (value, 'right', 0)],
                    ap=[(label, 'right', 2, 35), (value, 'left', 2, 35)],
                )
                if lastCtl is not None:
                    pm.formLayout(form, e=True,
                        ac=[(label, 'top', 4, lastCtl), (value, 'top', 4, lastCtl)],
                    )
                lastCtl = value
        return form



class ModeForm(object):
    """
    Creates a form with controls that operate under one of a given
    list of modes. Primarily creates a collection of icon text
    radio buttons with each modes title as the label, and provides
    an interface for getting or setting the mode easily.
    Set the `modeChangedCommand` property to get callbacks when
    the mode is changed in the ui.
    """
    def __init__(self, modes, annotations=None, modeChangedCommand=None, encode=None, multiple=False, allowNone=False, **kwargs):
        self._mode = []
        self.modes = pm.util.enum.Enum(self.__class__.__name__, modes)
        self.annotations = annotations
        self.buttons = []
        self.encodeData = {}
        self._customEncode = encode
        self.multiple = multiple
        self.allowNone = allowNone
        self.build(**kwargs)
        self.modeChangedCommand = modeChangedCommand
        if not self.allowNone:
            self._mode = [self.modes[0]]
            self.updateSelected()

    def __str__(self):
        return str(self.layout)

    @property
    def mode(self):
        if not self.multiple:
            if self._mode:
                return self._mode[0]
            else:
                return None
        else:
            return self._mode
    @mode.setter
    def mode(self, value):
        self._mode = None
        if value is not None:
            result = []
            values = asList(value)
            if not self.multiple and len(values) > 1:
                raise ValueError('mode must be a single value')
            result.extend([self.modes[self.modes.getIndex(v)] for v in values])
            if len(result):
                self._mode = result
        self.updateSelected()

    @property
    def encode(self):
        return self._customEncode
    @encode.setter
    def encode(self, value):
        if hasattr(value, '__call__') or value is None:
            self._customEncode = value
            self.update()

    def build(self, ratios=None, spacing=0, **kwargs):
        self.buttons = []
        if ratios is None:
            ratios = [1] * len(self.modes)
        with pm.formLayout() as self.layout:
            for i, m in enumerate(self.modes):
                label = self._encode(m.key)
                self.encodeData[str(label)] = m.key.title()
                kw = dict(
                    l=label,
                    st='textOnly',
                    onc=pm.Callback(self.modeChanged, m, True),
                    ofc=pm.Callback(self.modeChanged, m, False),
                )
                if self.annotations is not None and len(self.annotations) > i:
                    kw['ann'] = self.annotations[i]
                kw.update(kwargs)
                btn = pm.iconTextCheckBox(**kw)
                self.buttons.append(btn)
            layoutForm(self.layout, ratios, spacing=spacing)

    def _defaultEncode(self, value):
        return value.title()

    def _encode(self, item):
        val = item
        if hasattr(self._customEncode, '__call__'):
            val = self._customEncode(item)
        else:
            val = self._defaultEncode(item)
        if val is None:
            return ''
        return str(val)

    def _deselectMode(self, value):
        if value in self._mode:
            self._mode.remove(value)
        self.updateSelected()

    def _selectMode(self, value):
        if self.multiple:
            if value not in self._mode:
                self._mode.append(value)
        else:
            self.mode = value
        self.updateSelected()

    def selectAll(self):
        if self.multiple:
            self.mode = [str(v) for v in self.modes]

    def updateSelected(self):
        """
        Update the selected items to reflect the current mode(s)
        """
        for i, b in enumerate(self.buttons):
            en = i in asList(self.mode)
            b.setValue(en)

    def updateLabels(self):
        for button in self.buttons:
            currLabel = button.getLabel()
            mode = self.encodeData[currLabel]
            newLabel = self._encode(mode)
            del self.encodeData[currLabel]
            self.encodeData[newLabel] = mode
            button.setLabel(newLabel)

    def modeChanged(self, mode=None, on=True):
        #if mode is none and radioMode = true, dont change mode
        if on:
            self._selectMode(mode)
        elif self.allowNone:
            self._deselectMode(mode)
        else:
            self.updateSelected()
        if hasattr(self.modeChangedCommand, '__call__'):
            self.modeChangedCommand(mode)



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

    def __str__(self):
        return str(self.layout)

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
        pm.menuItem(l=SHOW_MSG, c=pm.Callback(self.show))

    def onChange(self):
        if self.changeCommand is not None:
            self.changeCommand(self.path)

    def show(self):
        if os.path.exists(self.path):
            if os.path.isdir(self.path):
                path = self.path
            else:
                path = os.path.dirname(self.path)
        show(path)

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





ROOT_REGEX = re.compile('^(/|//|[a-zA-Z]+:)[^/]*$')

def getPathItems(path):
    items = []
    if path is None or not len(path.strip()):
        return items
    pth = path
    while True:
        items.append(pth)
        if ROOT_REGEX.match(pth):
            break
        pth, base = os.path.split(pth)
        if not len(pth) or not len(base):
            # failsafe
            break
    return list(reversed(items))


class PathButtonForm(object):
    """
    Creates a row of buttons that represent each item of
    a path. Clicking on a button returns the path to that item.

    By setting the `rootPath` property, only the relative path
    to the root path will actually appear as buttons.

    Setting `browse` to True will cause option menus to appear
    as the last path item.  `browseDepth` controls how many
    path items of the current path will also be option menus.

    Directories can be excluded from browse option menus by setting
    the `browseExcludes` list to the desired exclude regexes.
    """

    def __init__(self, path=None, browse=False, command=None, bgc=(0.3, 0.3, 0.3)):
        self._path = path
        self._rootPath = None
        self._browse = browse
        self.bgc = bgc
        self.browseDepth = 1
        self.browseExcludes = ['\..*']
        self.command = command
        self.build()

    def __str__(self):
        return str(self.layout)

    @property
    def rootPath(self):
        return self._rootPath
    @rootPath.setter
    def rootPath(self, value):
        if value is not None:
            value = value.replace('\\', '/')
            if not len(value.strip()):
                value = None
        if self._rootPath != value:
            self._rootPath = value
            self.update()

    @property
    def path(self):
        return self._path
    @path.setter
    def path(self, value):
        if value is not None:
            value = value.replace('\\', '/')
            if not len(value.strip()):
                value = None
        if self._path != value:
            self._path = value
            self.update()

    @property
    def relPath(self):
        if None not in (self.rootPath, self.path) and self.rootPath in self.path:
            return os.path.relpath(self.path, self.rootPath)
        return self.path

    @property
    def pathItems(self):
        return getPathItems(self.path)

    def _numRelItems(self):
        """
        Return the number of items in the path that are
        part of the root path and should not be displayed.
        """
        if None not in (self.rootPath, self.path) and self.rootPath in self.path:
            rootItems = getPathItems(self.rootPath)
            return len(rootItems)
        return -1

    @property
    def browse(self):
        return self._browse
    @browse.setter
    def browse(self, value):
        self._browse = value
        self.update()

    def getBrowseDirs(self, path):
        return getSubDirs(path, self.browseExcludes)

    def build(self):
        with pm.columnLayout() as self.layout:
            self.buildPathForm()

    def buildPathForm(self):
        with pm.formLayout(h=20) as form:
            paths = self.pathItems
            skipCount = self._numRelItems()
            children = 0
            for i, path in enumerate(paths):
                if i < (skipCount-1):
                    continue
                # insert root prefix if necessary
                if ROOT_REGEX.match(path):
                    if path.startswith('/'):
                        pm.text(l=re.search('/+', path).group())
                        children += 1
                # insert button or browse menu
                if self.browse and i >= len(paths) - self.browseDepth and i > (skipCount-1):
                    dir_ = os.path.dirname(path)
                    subPaths = self.getBrowseDirs(dir_)
                    mnu = self.buildPathsMenu(dir_, subPaths, current=path)
                    buildShowMenu(mnu, path)
                else:
                    btn = pm.button(l=os.path.basename(path), h=20, c=pm.Callback(self._command, path))
                    buildShowMenu(btn, path)
                    if self.bgc is not None:
                        btn.setBackgroundColor(self.bgc)
                children += 1
                # insert path separators and final browse menu
                if i != len(paths) - 1:
                    pm.text(l='/')
                    children += 1
                elif self.browse:
                    subPaths = self.getBrowseDirs(path)
                    if len(subPaths):
                        pm.text(l='/')
                        self.buildPathsMenu(self.path, subPaths)
                        children += 2
            layoutForm(form, [0] * children, fullAttach=False)

    def buildPathsMenu(self, root, paths, current=None):
        menu = pm.optionMenu(h=20)
        if self.bgc is not None:
            menu.setBackgroundColor(self.bgc)
        menu.changeCommand(pm.Callback(self._browseCommand, root, menu))
        if current is None:
            pm.menuItem(l='')
        values = []
        for path in paths:
            values.append(os.path.basename(path))
            pm.menuItem(l=values[-1])
        if current is not None:
            curval = os.path.basename(current)
            if curval in values:
                menu.setValue(curval)
        return menu

    def _browseCommand(self, root, menu):
        relPath = menu.getValue()
        if len(relPath):
            path = os.path.join(root, relPath).replace('\\', '/')
            self._command(path)

    def _command(self, path):
        if hasattr(self.command, '__call__'):
            pm.evalDeferred(pm.Callback(self.command, path))

    def update(self):
        # TODO: update buttons in a relative fashion
        # so that clicked buttons dont get deleted and recreated
        self.layout.clear()
        with self.layout:
            self.buildPathForm()


def buildShowMenu(ctl, path=None, obj=None, attr=None, l=None):
    """
    Build a show in finder/explorer menu on the given control.
    The path can be given outright, or be provided as an object,
    attribute pair that will be retrieved on command.
    """
    pm.popupMenu(p=ctl)
    return buildShowMenuItem(path, obj, attr, l)

def buildShowMenuItem(path=None, obj=None, attr=None, l=None):
    if l is None:
        l = SHOW_MSG
    return pm.menuItem(l=l, c=getShowCommand(path, obj, attr))

def getShowCommand(path=None, obj=None, attr=None):
    """
    Get a command that will show the given path or obj.attr in finder/explorer.
    """
    def _show():
        show(getattr(obj, attr))
    # resolve path command
    if path is None:
        if obj is None or attr is None:
            raise ValueError('must provide atleast a path or object and attribute')
        cmd = pm.Callback(_show)
    else:
        cmd = pm.Callback(show, path)
    return cmd


def show(path):
    if path is None or not os.path.isdir(path):
        return
    if sys.platform == 'win32':
        subprocess.Popen(['explorer.exe', os.path.normpath(path)])
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', path])


def getSubDirs(path, excludes=None):
    if os.path.isdir(path):
        items = [os.path.join(path, f).replace('\\', '/') for f in os.listdir(path)]
        dirs = [d for d in items if os.path.isdir(d)]
        filtered = dirs
        if excludes is not None:
            filtered = []
            for d in dirs:
                if not any([re.match(f, os.path.basename(d)) for f in excludes]):
                    filtered.append(d)
        return sorted(filtered)
    return []


def browse(files=True, existing=True, cap='Choose {item}', okc='Choose', dir=None):
    fm = (1 if existing else 0) if files else 2
    item = 'File' if files else 'Directory'
    cap.format(item=item)
    kw = dict(fm=fm, cap=cap, okc=okc)
    if dir is not None and os.path.isdir(dir):
        kw['dir'] = dir
    result = pm.fileDialog2(**kw)
    if result is not None and len(result):
        return result[0]





class LibraryLayout(object):
    """
    Create a layout that shows icon items for files
    within one or more paths.
    """
    def __init__(self, itemClasses=None, editable=True):
        if itemClasses is None:
            itemClasses = [LibraryIconItem]
        self.bgc = (0.18, 0.18, 0.18)
        self.pathbgc = (0.2, 0.2, 0.2)
        self._editable = editable
        self._multipleSelection = False
        self._columns = 6
        self._itemSize = 75
        self._dragItem = None
        self._itemClasses = itemClasses
        self._items = {}
        self._paths = []
        self.dialogParent = None
        self.pathFilter = None
        self.itemFilter = None
        self.selectCallback = None
        self.deselectCallback = None
        self.renameCallback = None
        self.deleteCallback = None
        self.build()

    def __str__(self):
        return str(self.layout)

    @property
    def paths(self):
        return self._paths
    @paths.setter
    def paths(self, value):
        value = asList(value)
        if self._paths != value:
            self._paths = value
            self.update()

    def setPath(self, value):
        self.paths = value

    @property
    def itemClasses(self):
        return self._itemClasses
    @itemClasses.setter
    def itemClasses(self, value):
        self._itemClasses = [x for x in asList(value) if isinstance(x, LibraryItem)]
        self.update()

    @property
    def itemSize(self):
        return self._itemSize
    @itemSize.setter
    def itemSize(self, value):
        self._itemSize = value
        self.updateItemSizes()

    @property
    def columns(self):
        return self._columns
    @columns.setter
    def columns(self, value):
        self._columns = value
        self.updateContent()

    @property
    def multipleSelection(self):
        return self._multipleSelection
    @multipleSelection.setter
    def multipleSelection(self, value):
        self._multipleSelection = value
        self.updateItemSelection()

    @property
    def editable(self):
        return self._editable
    @editable.setter
    def editable(self, value):
        self._editable = value
        self.update()
    
    def items(self, path=None):
        """
        Return the current items for the given path, or
        as a dictionary with all paths.
        """
        if path is not None:
            if self._items.has_key(path):
                return self._items[path]
        else:
            return self._items.copy()

    def allItems(self):
        """ Return all items in a flat list """
        return [v for itms in self.items().values() for v in itms]

    def selectedItem(self, path=None):
        sel = self.selectedItems(path)
        if len(sel):
            return sel[0]

    def selectedItems(self, path=None):
        items = []
        if path is not None:
            if self._items.has_key(path):
                items = self._items[path]
        else:
            items = self.allItems()
        return [i for i in items if i.selected]
    
    def build(self):
        """ Build the contents of the grid-view containing all animation poses/clips """
        with pm.scrollLayout('libraryLayout', cr=True, bgc=(0.18, 0.18, 0.18)) as self.scrollLayout:
            with pm.frameLayout('libraryFrame', lv=False, bv=False, mw=8, mh=8) as self.contentLayout:
                self.buildLibraryContent()
        self.layout = self.scrollLayout
    
    def buildLibraryContent(self):
        """ Build a path header and item grid for each of the current item lists """
        with pm.columnLayout(adj=True, rs=8) as col:
            for p in self.paths:
                if self.pathFilter is not None:
                    if not self.pathFilter(p):
                        continue
                if self._items.has_key(p):
                    itms = self._items[p]
                    if self.itemFilter is not None:
                        itms = [i for i in itms if self.itemFilter(i)]
                    self.buildItemLayout(itms, p)
        return col

    def buildItemLayout(self, items, path=None):
        rows = []
        i = 0
        while i < len(items):
            end = min(len(items), i+self.columns)
            rows.append(items[i:end])
            i = end
        with pm.frameLayout(lv=False, bv=False) as layout:
            if path is not None:
                with pm.frameLayout(lv=False, bs='out'):
                    kw = dict(h=26, bgc=self.pathbgc)
                    # TODO: make a path:title map for custom names in path title bars
                    t = LibraryPathTitle(path, **kw)
                    t.dropCommand = self.onItemDropped
            with pm.frameLayout(lv=False, bv=False):
                for row in rows:
                    with pm.formLayout() as form:
                        for item in row:
                            item.build(editable=self.editable)
                        layoutForm(form, [0] * len(row), spacing=0)
        return layout
        
    def update(self, path=None):
        """ Update the library to reflect the current paths and their items """
        self.updateItems(path)
        self.updateContent()

    def updateItemSizes(self):
        for itms in self.items().values():
            for i in itms:
                i.size = self.itemSize

    def updateContent(self):
        """ Update the content of the library to reflect the current items and filters """
        self.contentLayout.clear()
        for i in self.allItems():
            i.clearBuild()
        with self.contentLayout:
            self.buildLibraryContent()

    def updateItems(self, path=None):
        """
        Update the current items for all paths or the given path.
        Will also clear old items that are no longer in one of the current paths.
        """
        toupdate = []
        # determine paths to update
        if path is not None:
            if path not in paths:
                return
            toupdate = [path]
        else:
            toupdate = self.paths
        # trim old paths
        for k in self._items.keys():
            if k not in self.paths:
                del self._items[k]
        # update
        for p in toupdate:
            items = self.getItemsForPath(p)
            for i in items:
                self.setupItem(i)
            self._items[p] = items

    def updateItemSelection(self, keep=None):
        """ Update item selection based on the multipleSelection property """
        keep = asList(keep)
        if not self.multipleSelection:
            for i in self.allItems():
                if i not in keep:
                    i.deselect()

    def getItemsForPath(self, path):
        """
        Return a list of LibraryItems for the given path.
        Attempts to create an item from each file in the path using with
        each of the classes from itemClasses. The first item that is
        created successfully from any of the classes will be used.
        """
        # TODO: setup a regex:class map for associating files with item classes
        # TODO: add a filter regex to skip certain files, eg. .DS_Store, Thumbs.db, .*
        items = []
        if os.path.isdir(path):
            files = [os.path.join(path, f) for f in os.listdir(path)]
            files = self.sortFiles(files)
            for f in files:
                for c in self.itemClasses:
                    item = c.fromFile(f)
                    if item is not None:
                        items.append(item)
                        break
        return items

    def sortFiles(self, files):
        """ Sort the given files. Override to implement custom sorting """
        return sorted(files)

    def setupItem(self, item):
        """
        Tell the LibraryItem to associate itself with this library.
        """
        if not isinstance(item, LibraryItem):
            raise TypeError('expected LibraryItem, got {0}'.format(type(item).__name__))
        item.setup(self)

    def fitItemSize(self):
        # subtract scroll bar and margins
        w = self.scrollLayout.getWidth() - 20
        margins = (4 * self.columns)
        newSize = (w - margins) / float(self.columns)
        self.itemSize = newSize

    def setItemSize(self, value, minValue=50, maxValue=150):
        self.itemSize = min(max(minValue, value), maxValue)

    def setColumns(self, minValue=1, maxValue=10, **kwargs):
        kw = dict(
            t = 'Set Column Count',
            m = 'Enter the number of columns to use ({0} - {1})'.format(minValue, maxValue),
            b=['Ok'],
            tx=self.columns,
        )
        kw.update(kwargs)
        result = pm.promptDialog(**kw)
        if 'Ok' not in result:
            return
        try:
            val = int(pm.promptDialog(q=True).strip())
        except:
            LOG.warning('invalid value, please enter an integer')
            return
        if val < minValue or val > maxValue:
            LOG.warning('invalid value, enter a number from {0} to {1}'.format(minValue, maxValue))
            return
        self.columns = val

    def onItemSelect(self, item):
        self.updateItemSelection(keep=item)
        if self.selectCallback is not None:
            self.selectCallback(item)

    def onItemDeselect(self, item):
        if self.selectCallback is not None:
            self.selectCallback(item)        

    def onItemRename(self, item):
        if self.renameCallback is not None:
            self.renameCallback(item)
        pm.evalDeferred(self.update)

    def onItemDelete(self, item):
        if self.deleteCallback is not None:
            self.deleteCallback(item)
        pm.evalDeferred(self.update)

    def onItemDragged(self, obj, x, y, mods):
        self._dragItem = obj

    def onItemDropped(self, dragobj, dropobj, msgs, x, y, type):
        if isinstance(dropobj, LibraryPathTitle):
            if self._dragItem is not None:
                path = dropobj.path
                copy = (type == 1)
                self._dragItem.moveToPath(path, asCopy=copy)
        pm.evalDeferred(self.update)



class LibraryPathTitle(object):
    """
    Creates a frame layout with text in it to represent a folder
    within a LibraryLayout. These objects handle drag and drop as well
    to provide easy moving of LibraryItem objects.
    """
    def __init__(self, path, **kwargs):
        self._path = path
        self.build(**kwargs)
        self.dropCommand = None

    def __str__(self):
        return str(self.control)

    @property
    def path(self):
        if self._path is None:
            return ''
        return self._path
    @path.setter
    def path(self, value):
        self._path = value
        self.update()

    def build(self, **kwargs):
        self.control = pm.text(l='', dpc=self._dropCommand, **kwargs)
        buildShowMenu(self.control, self.path)
        self.update()

    def update(self):
        self.control.setLabel(os.path.basename(self.path).title())

    def _dropCommand(self, dragged, dropped, msgs, x, y, type):
        if hasattr(self.dropCommand, '__call__'):
            self.dropCommand(dragged, self, msgs, x, y, type)




class LibraryItem(object):
    @classmethod
    def fromFile(cls, filename):
        """
        Return a new LibraryItem from the given filename.
        This should be overridden to only return an item
        if the given file is valid
        """
        if cls.validate(filename):
            return cls(filename)

    @classmethod
    def validate(cls, filename):
        """
        Validate that the given filename can be used for this item class.
        Override this in subclasses to only create items from certain files.
        """
        return os.path.isfile(filename)

    def __init__(self, filename=None):
        self.itemName = 'file'
        self._filename = filename
        self._selected = False
        self.dialogParent = None
        self.selectCallback = None
        self.deselectCallback = None
        self.renameCallback = None
        self.deleteCallback = None
        self.dragCallback = None
        self.clearBuild()

    def __repr__(self):
        return '<{0.__class__.__name__} | {0.name}>'.format(self)

    def clearBuild(self):
        """ Clear all stored ui items """
        self.button = None

    @property
    def filename(self):
        return self._filename
    @filename.setter
    def filename(self, value):
        self._filename = value
        self.onFilenameChanged()

    @property
    def name(self):
        if self.filename is not None:
            return self.getName(self.filename)

    def getName(self, filename):
        """
        Return a name for the given filename
        Override to customize how names are determined from the file
        """
        return os.path.basename(filename)

    def getFilenameForName(self, name):
        """
        Return a file basename for the given name
        Override to customize how file names are determined from names
        """
        return name

    @property
    def selected(self):
        return self._selected
    @selected.setter
    def selected(self, value):
        self._selected = value
        self.onSelectedChanged()

    def build(self, editable=True):
        kw = dict(
            l=self.name,
            st='textOnly',
            cc=pm.Callback(self.onClick),
            ann=self.filename,
        )
        if editable:
            kw['dgc'] = self._dragCallback
        self.button = pm.iconTextCheckBox(**kw)
        if editable:
            pm.popupMenu(p=self.button)
            self.buildMenu()

    def buildMenu(self):
        pm.menuItem(l='Rename', rp='N', c=pm.Callback(self.rename))
        pm.menuItem(l='Delete', rp='S', c=pm.Callback(self.delete))

    def onFilenameChanged(self):
        if self.button is not None:
            self.button.setLabel(self.name)
            self.button.setAnnotation(self.filename)

    def onSelectedChanged(self):
        if self.button is not None:
            self.button.setValue(self.selected)

    def onClick(self):
        self.selected = self.button.getValue()
        if self.selected:
            self._callback('select')
        else:
            self._callback('deselect')

    def setup(self, lib):
        self.selectCallback = lib.onItemSelect
        self.deselectCallback = lib.onItemDeselect
        self.renameCallback = lib.onItemRename
        self.deleteCallback = lib.onItemDelete
        self.dragCallback = lib.onItemDragged
        self.dialogParent = lib.dialogParent

    def moveToPath(self, path, asCopy=False, force=False):
        """
        Move this item to the given folder.
        Essentially performs a rename while maintaining the files base name.
        """
        if self.filename is None:
            return
        if not os.path.isdir(path):
            term = 'copy' if asCopy else 'move'
            LOG.warning('cannot {1} to missing folder: {0}'.format(path, term))
            return
        newFile = os.path.join(path, os.path.basename(self.filename))
        self.moveFile(newFile, asCopy=asCopy, force=force)

    def rename(self, asCopy=False, force=False, **kwargs):
        kw = dict(
            t='Rename {0}'.format(self.itemName.title()),
            m='Enter a new name for\n{0}'.format(self.filename),
            b=['Cancel', 'Rename'],
            db='Rename',
            tx=self.name,
        )
        if self.dialogParent is not None:
            kw['p'] = self.dialogParent
        kw.update(kwargs)
        result = pm.promptDialog(**kw)
        if 'Rename' not in result:
            return
        # get new filename
        newName = pm.promptDialog(q=True)
        if newName == self.name:
            return
        newFile = os.path.join(os.path.dirname(self.filename), self.getFilenameForName(newName))
        # move file
        self.moveFile(newFile, asCopy=asCopy, force=force)

    def delete(self, force=False, **kwargs):
        if not force:
            kw = dict(
                t='Delete {0}'.format(self.itemName.title()),
                m='Are you sure you want to delete:\n{0}'.format(self.filename),
                b=['Cancel', 'Ok'],
                db='Ok',
            )
            if self.dialogParent is not None:
                kw['p'] = self.dialogParent
            kw.update(kwargs)
            result = pm.confirmDialog(**kw)
            if 'Ok' not in result:
                return
        self.deleteFile()

    def select(self):
        self.selected = True

    def deselect(self):
        self.selected = False

    def moveFile(self, filename, asCopy=False, force=False):
        if not force:
            # check if destination is available
            if os.path.isfile(filename):
                kw = dict(
                    t='Overwrite {0}'.format(self.itemName.title()),
                    m='Are you sure you want to overwrite:\n{0}'.format(filename),
                    b=['Cancel', 'Ok'],
                    db='Cancel',
                )
                if self.dialogParent is not None:
                    kw['p'] = self.dialogParent
                result = pm.confirmDialog(**kw)
                if 'Ok' not in result:
                    return
        try:
            self.performMoveFile(filename, asCopy=asCopy)
        except Exception as e:
            LOG.warning('could not rename: {0}'.format(e))
        else:
            self._callback('rename')

    def performMoveFile(self, filename, asCopy=False):
        """
        Perform the actual copy or move of the current file to the given filename.
        """
        if asCopy:
            shutil.copy2(self.filename, filename)
        else:
            shutil.move(self.filename, filename)
        self.filename = filename

    def deleteFile(self):
        if os.path.isfile(self.filename):
            try:
                self.performDeleteFile()
            except Exception as e:
                LOG.warning('could not delete: {0}'.format(e))
            else:
                self._callback('delete')

    def performDeleteFile(self):
        os.remove(self.filename)

    def _callback(self, name):
        cmdName = '{0}Callback'.format(name)
        if hasattr(getattr(self, cmdName), '__call__'):
            getattr(self, cmdName)(self)

    def _dragCallback(self, ctl, x, y, mods):
        if hasattr(self.dragCallback, '__call__'):
            self.dragCallback(self, x, y, mods)




DEFAULT_ICON = 'default.svg'

def renderIcon(filename, w=256, h=256, **kwargs):
    """
    Hardware render an icon to the given filename.
    Pass a value for `cam` to use a specific camera.
    """
    # change render file type
    rg = pm.PyNode('defaultRenderGlobals')
    origFmt = rg.imageFormat.get()
    # 32 = png
    rg.imageFormat.set(32)
    kw = dict(w=w, h=h, eaa=(2, 16))
    kw.update(kwargs)
    try:
        tmp = pm.hwRender(**kw)
        shutil.move(tmp, filename)
    except:
        import traceback
        traceback.print_exc()
    finally:
        # restore file type
        rg.imageFormat.set(origFmt)

def getIconFilename(filename):
    """ Return the name of the png that would be associated with the given file """
    return '{0}.png'.format(filename)

class LibraryIconItem(LibraryItem):
    @classmethod
    def validate(cls, filename):
        """
        Icon items automatically associate themselves with a png,
        so ignore all pngs as they should not be represented individually.
        """
        if os.path.splitext(filename)[-1] == '.png':
            return False
        return super(LibraryIconItem, cls).validate(filename)

    def __init__(self, filename=None, showLabel=True, size=50, labelHeight=14):
        super(LibraryIconItem, self).__init__(filename)
        self._showLabel = showLabel
        self._size = size
        self._labelHeight = labelHeight
        self.defaultIcon = DEFAULT_ICON

    def clearBuild(self):
        self.button = None
        self.label = None
        self.layout = None

    @property
    def icon(self):
        if self.iconFilename is not None and os.path.isfile(self.iconFilename):
            return self.iconFilename
        return self.defaultIcon

    @property
    def iconFilename(self):
        if self.filename is not None:
            return getIconFilename(self.filename)

    def build(self, editable=True):
        with pm.formLayout(w=self.size, h=self.size + self.labelHeight) as form:
            kw = dict(
                i=self.icon,
                cc=pm.Callback(self.onClick),
                w=self.size, h=self.size,
                v=self.selected,
                ann=self.filename,
            )
            if editable:
                kw['dgc'] = self._dragCallback
            self.button = pm.iconTextCheckBox(**kw)
            self.label = pm.text(
                l=self.name,
                fn='smallPlainLabelFont',
                h=self.labelHeight,
                m=self.showLabel,
            )
            if editable:
                pm.popupMenu(p=self.button, mm=True)
                self.buildMenu()
            layoutForm(form, (0, 0), vertical=True)
        self.layout = form

    def setup(self, lib):
        super(LibraryIconItem, self).setup(lib)
        self.size = lib.itemSize

    def onFilenameChanged(self):
        if self.label is not None:
            self.label.setLabel(self.name)
            self.button.setAnnotation(self.filename)

    def performMoveFile(self, filename, asCopy=False):
        """ For Icon items, this will also move the icon file if it exists. """
        fnc = shutil.copy2 if asCopy else shutil.move
        # move/copy file
        fnc(self.filename, filename)
        # move/copy icon
        if os.path.isfile(self.iconFilename):
            newIcon = getIconFilename(filename)
            fnc(self.iconFilename, newIcon)
        self.filename = filename

    def performDeleteFile(self):
        icon = self.iconFilename
        os.remove(self.filename)
        if os.path.isfile(icon):
            os.remove(icon)

    @property
    def showLabel(self):
        return self._showLabel
    @showLabel.setter
    def showLabel(self, value):
        self._showLabel = value
        self.label.setManage(value)

    @property
    def size(self):
        return self._size
    @size.setter
    def size(self, value):
        self._size = value
        if self.layout is not None:
            self.button.setWidth(value)
            self.button.setHeight(value)
            self.layout.setWidth(value)
            self.layout.setHeight(value + self.labelHeight)

    @property
    def labelHeight(self):
        return self._labelHeight
    @labelHeight.setter
    def labelHeight(self, value):
        self._labelHeight = int(value)



