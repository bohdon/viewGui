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


def gridFormLayout(numberOfRows=None, numberOfColumns=None, spacing=2):
    return GridFormLayout(numberOfRows, numberOfColumns, spacing)


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

