#!/usr/bin/env python
# encoding: utf-8
"""
viewGui.utils

Created by Bohdon Sayre on 2012-06-21.
Copyright (c) 2012 Moonbot Studios. All rights reserved.
"""

import pymel.core as pm
import sys
import os
import math


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


def asList(value):
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        return [value]
    return value


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




