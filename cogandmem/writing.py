"""
Functions for writing to files.

To the best of my knowledge, the functions in this module work. However, the
module can be improved. At present, it does not take advantage of Python's csv
module. Since data is usually written to csv files, this is a major oversight.

This module contains the following functions (see the docstrings for more
information):
    ready_file_for_writing: given a string, returns a file object ready for
writing.
    list_or_tuple: write a list or tuple to a file.
    write_dict: write a dictionary to a file.
    study_phase: write a study phase to a file.
    paired_study: write a study phase with WordPair objects to a file.
    cued_recall_results: write the results of a cued-recall test to a file.
"""

import os

def ready_file_for_writing(f):
    """Make sure a file is ready for writing. f should be a string or file."""
    try:
        extant = os.path.isfile(f)
    except TypeError:
        # Presumably, this is already a file.
        return f
    if extant:
        # Don't overwrite the extant file.
        f = open(f, "a")
    else:
        f = open(f, "w")
    return f


def list_or_tuple(f, w, sep = "\n", c = True, end_string = "\n"):
    """
    Write a list or tuple to a file.
    
    Parameters:
        f: the file to which to write w; can be a file open for writing, a
            string pointing to an extant file, or a string pointing to a
            to-be-created file.
        w: the to-be-written list or tuple.
    
    Keyword Parameters:
        sep: the string separating each list element; defaults to "\n".
        c: Boolean indicating whether the file should be closed before the
            function ends; defaults to True.
        end_string: a string to write at the end; defaults to "\n".
    """
    f = ready_file_for_writing(f)
    for i in xrange(len(w)):
        e = w[i]
        if isinstance(e, (list, tuple)):
            list_or_tuple(f, e, c = False, end_string = "")
        elif isinstance(e, dict):
            write_dict(e, f, False, end_string = "")
        else:
            f.write(str(e))
        if i < len(w)-1:
            f.write(sep)
        elif end_string:
            f.write(end_string)
    if c:
        f.close()


def write_dict(d, f, c = True, end_string = "\n"):
    """
    Write a dictionary (d) to a file (f). f can be a file open for writing or
    a string pointing to an extant or to-be-created file.
    
    Entries in d are written one by one to f. Each key is written first,
    followed by the entry. Two blank lines separate keys. Dicts, lists, and
    tuples are written with each entry/element on a separate line. All other
    types are converted to strings and written on the same line as the key.
    If c is True, f is closed before the function ends. The end_string
    parameter defaults to "\n". It is written after d is written.
    """
    f = ready_file_for_writing(f)
    for k in d:
        f.write(str(k)+": ")
        w = d[k]
        if isinstance(w, (list, tuple)):
            f.write("[\n")
            list_or_tuple(f, w, c = False)
            f.write("]\n")
        elif isinstance(w, dict):
            f.write("{\n")
            write_dict(w, f, False)
            f.write("}\n")
        else:
            f.write(str(w)+"\n")
    if end_string:
        f.write(end_string)
    if c:
        f.close()


def study_phase(stimuli, f, sep = ",", close_when_finished = True):
    """
    Write a study list to a file.
    
    If the Stimulus objects passed to the function contain information in
    their condition attribute, then a three-column table is written to f
    (serial position, word, condition). If no condition information is
    included, then the condition column is omitted.
    
    Parameters:
        stimuli: a list of Stimulus objects representing the study list.
        f: the file to which to write stimuli; this can be a file opened for
            writing, a string pointing to an extant file, or a string pointing
            to a to-be-created file. If f is a file, writing starts wherever
            the file is currently positioned for writing; if f is a string
            pointing to an extant file, stimuli are written to the end; and if
            f is a to-be-created file, stimuli are written in the file at the
            top.
    
    Keyword Parameters:
        sep: string denoting what separates the values; defaults to ",".
        close_when_finished: Boolean indicating whether f should be closed
            before ending the function; defaults to True.
    """
    f = ready_file_for_writing(f)
    f.write("serial_position{:s}word".format(sep))
    if stimuli[0].condition:
        write_condition = True
        f.write("{:s}condition\n".format(sep))
    else:
        write_condition = False
        f.write("\n")
    for i in xrange(len(stimuli)):
        f.write("{:d}{:s}{:s}".format(i+1, sep, stimuli[i].word))
        if write_condition:
            f.write("{:s}{:s}\n".format(sep, str(stimuli[i].condition)))
        else:
            f.write("\n")
    if close_when_finished:
        f.close()


def paired_study(stimuli, f, sep = ",", close_when_finished = True):
    """
    Write a paired study list to a file.
    
    If the WordPair objects passed to the function contain information in
    their condition attribute, then a four-column table is written to f
    (serial position, cue, target, condition). If no condition information is
    included, then the condition column is omitted.
    
    Parameters:
        stimuli: a list of WordPair objects representing the study list.
        f: the file to which to write stimuli; this can be a file opened for
            writing, a string pointing to an extant file, or a string pointing
            to a to-be-created file. If f is a file, writing starts wherever
            the file is currently positioned for writing; if f is a string
            pointing to an extant file, stimuli are written to the end; and if
            f is a to-be-created file, stimuli are written in the file at the
            top.
    
    Keyword Parameters:
        sep: string denoting what separates the values; defaults to ",".
        close_when_finished: Boolean indicating whether f should be closed
            before ending the function; defaults to True.
    """
    f = ready_file_for_writing(f)
    f.write("serial_position"+sep+"cue"+sep+"target")
    if stimuli[0].condition:
        write_condition = True
        f.write(sep+"condition\n")
    else:
        write_condition = False
        f.write("\n")
    for i in xrange(len(stimuli)):
        pair = stimuli[i]
        f.write(str(i+1)+sep+pair.cue+sep+pair.target)
        if write_condition:
            f.write(sep+str(pair.condition)+"\n")
        else:
            f.write("\n")
    if close_when_finished:
        f.close()


def cued_recall_results(word_pairs, f, sep = ",", close_when_finished = True):
    """
    Write the results of a cued-recall test to a file.
    
    If the WordPair objects passed to the function contain information in
    their condition attribute, then a five-column table is written to f
    (test position, cue, target, response, condition). If no condition
    information is included, then the condition column is omitted.
    
    Parameters:
       word_pairs: the WordPair objects to write.
        f: the file to which to write stimuli; this can be a file opened for
            writing, a string pointing to an extant file, or a string pointing
            to a to-be-created file. If f is a file, writing starts wherever
            the file is currently positioned for writing; if f is a string
            pointing to an extant file, stimuli are written to the end; and if
            f is a to-be-created file, stimuli are written in the file at the
            top.
    
    Keyword Parameters:
        sep: string denoting what separates the values; defaults to ",".
        close_when_finished: Boolean indicating whether f should be closed
            before ending the function; defaults to True.
    """
    f = ready_file_for_writing(f)
    f.write("test_position"+sep+"cue"+sep+"target"+sep+"response")
    if word_pairs[0].condition:
        write_condition = True
        f.write(sep+"condition"+sep+"\n")
    else:
        write_condition = False
        f.write("\n")
    for i in xrange(len(word_pairs)):
        pair = word_pairs[i]
        f.write(str(i+1)+sep+pair.cue+sep+pair.target+sep+pair.response)
        if write_condition:
            f.write(sep+str(pair.condition)+"\n")
        else:
            f.write("\n")
    if close_when_finished:
        f.close()
