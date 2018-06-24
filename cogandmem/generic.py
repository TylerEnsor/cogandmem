"""
Miscellaneous, generic functions that do not fit elsewhere.

This module includes the following functions (see docstrings for more
information):
    terminate: to be called before exiting.
    string_file: get the contents of a file (or string pointing to a file) as
a string.
    file_lines: get a list of a file's lines with leading and trailing white
space removed.
    create_folder: create a folder.
    exclude_rect: get pygame.Rect objects surrounding another pygame.Rect
object.
    combine_rects: combine all of the pygame.Rect objects in a list into a
single pygame.Rect object.
    convert_to_tuple: convert an iterable to a tuple (probably will be removed
in future versions).
    convert_to_list: convert an iterable to a list (probably will be removed
in future versions).
    seconds_to_milliseconds: get the number of milliseconds in a given number
of seconds.
    milliseconds_to_seconds: get the number of seconds in a given number of
milliseconds.
    date_time_string: get a string of the form "yyyy.mm.dd.hh.mm.ss" for the
current local time.
"""

import sys
import os
import numpy
import time

import pygame

def terminate(files = ()):
    """Close everything, including an optional list or tuple of files.."""
    for file in files:
        try:
            file.close()
        except AttributeError:
            # This isn't a file.
            pass
    pygame.quit()
    sys.exit()


def string_file(source):
    """
    Read the content of a file (source) into a string. Leading and trailing
    white space is removed.
    """
    with open(source) as f:
        s = f.read().strip()
    return s


def file_lines(f):
    """Read lines from a file (f) into a list."""
    try:
        f = open(f)
    except TypeError:
        # probably already a file.
        pass
    with f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]
    return lines


def create_folder(p):
    """
    Create a folder corresponding to the path specified in p.
    If the specified path already exists, the function returns False;
    otherwise, the function returns True.
    """
    v = True
    try:
        os.makedirs(p)
    except OSError:
        v = False
        if not os.path.isdir(p):
            raise
    return v


def exclude_rect(rect1, rect2 = None):
    """
    Return a list of rects surrounding rect1. rect2 can be a rect within which
    rect1 is positioned or None (its default value). If rect2 is None, the
    main display surface is used.
    """
    rects = []
    if not rect2:
        rect2 = pygame.display.get_surface().get_rect()
    if rect2.top < rect1.top:
        rects.append(pygame.Rect(
            rect2.left, rect2.top, rect2.width, rect1.top-rect2.top
        ))
    if rect2.bottom > rect1.bottom:
        rects.append(pygame.Rect(
            rect2.left, rect2.bottom, rect2.width, rect2.bottom-rect1.bottom
        ))
    if rect2.left < rect1.left:
        rects.append(pygame.Rect(
            rect2.left, rect2.top, rect1.left-rect2.left, rect2.height
        ))
    if rect2.right > rect1.right:
        rects.append(pygame.Rect(
            rect1.right, rect2.top, rect2.right-rect1.right, rect2.height
        ))
    return rects


def combine_rects(rects):
    """Return a rect that encompasses all of the rects in rects."""
    tallest = rects[0].height
    widest = rects[0].width
    leftmost = rects[0].left
    topmost = rects[0].top
    for r in rects[1:]:
        if r.width > widest:
            widest = r.width
        if r.height > tallest:
            tallest = r.height
        if r.left < leftmost:
            leftmost = r.left
        if r.top < topmost:
            topmost = r.top
    large_rect = pygame.Rect(leftmost, topmost, widest, tallest)
    return large_rect


def convert_to_tuple(array_):
    """
    Convert all array_ elements and array_ itself to a tuple.
    
    I primarily use this for converting numpy arrays/matrices to tuples.
    array_ is returned as is if it is not possible to convert it to a tuple.
    """
    if isinstance(array_, str):
        as_tuple = array_
    else:
        try:
            as_tuple = tuple(convert_to_tuple(i) for i in array_)
        except TypeError:
            as_tuple = array_
    return as_tuple


def convert_to_list(array_):
    """
    Convert all elements and array_ itself to a list.
    array_ is returned as is if it can't be converted to a list.
    """
    if isinstance(array_, str):
        as_list = array_
    else:
        try:
            as_list = list(convert_to_list(i) for i in array_)
        except TypeError:
            as_list = array_
    return as_list


def seconds_to_milliseconds(seconds):
    """
    Convert seconds to milliseconds.
    NB: Rounds to the nearest whole millisecond.
    """
    return int(round(seconds*1000))


def milliseconds_to_seconds(milliseconds):
    """Convert milliseconds to seconds."""
    return milliseconds/1000


def date_time_string():
    """
    Return a string containing the numeric local date and time.
    
    This function is useful for producing nonoverlapping files that will sort
    chronologically. The date February 26, 2015 at 9:05:44 AM would produce
    the string "2015.02.26.09.05.44".
    """
    current_time = time.localtime()
    date_and_time = ""
    # Convert ints to strings, add leading 0s if necessary, and then add to
    # date_and_time:
    for i in xrange(6):
        if i < 5:
            unit_to_add = str(current_time[i])+"."
            if len(unit_to_add) == 2:
                unit_to_add = "0"+unit_to_add
        else:
            unit_to_add = str(current_time[i])
            if len(unit_to_add) == 1:
                unit_to_add = "0"+unit_to_add
        date_and_time = date_and_time+unit_to_add
    return date_and_time
