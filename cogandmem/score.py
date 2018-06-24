"""
Functions for scoring results.

This module contains the following functions (see the docstrings of the
functions for more information):
    free_recall: score a free-recall test.
    cued_recall: score a cued-recall test.
    serial_position_cued_recall: score a cued-recall test as a function of
serial position.
"""

from __future__ import division

import difflib
import copy

# Keys for dicts:
CONDITION = "condition"
RAW_RECALL = "raw recall"
PROPORTION_RECALL = "proportion recall"
TOTAL_RECALL = "total recall"
CLOSE_MATCHES = "close matches"
ITEMS_RECALLED = "items recalled"
OVERALL = "overall"
INTRUSIONS = "intrusions"
DISTRACTOR = "distractor"


def free_recall(targets, responses):
    """
    Score the results of a free-recall test given the targets and responses.
    
    A strict scoring criterion is used--that is, responses are considered
    correct if they match exactly the spelling of targets and wrong otherwise.
    However, case and leading/trailing white space are not evaluated in
    scoring. A list of close matches is returned for further examination by
    the experimenter.
    
    Parameters:
        targets: the words seen at study; targets may be a file with one
            target per line, a list/tuple of Stimulus objects, or a list/tuple
            of strings.
        responses: the responses given at test; may be a file with one
            response per line or a list/tuple of strings.
    
    Returns:
        recall_dict: a dict with the following keys:
            "condition": Unless Stimulus objects are passed to the function,
                this key is simply "condition". Otherwise, there is a separate
                key for each of the conditions in targets. The entry for this
                key is itself a dict with the following entries:
                "raw recall": the total number of targets recalled.
                "proportion recall": the proportion of targets recalled.
            "overall": same as "condition", but conditions are ignored. If no
                conditions were specified, this key is the same as
                "condition".
            "close matches": the responses that came close to matching one or
                more target. The entry for "close matches" is a dict with keys
                for each close match. The entry for each close match is a
                tuple of the targets to which the response came close to
                matching.
            "intrusions": a list of responses that neither matched nor closely
                matched any targets.
            "items recalled": a list of the specific items recalled in the
                order they were recalled; includes targets, close matches, and
                intrusions.
    """
    template = {RAW_RECALL: 0, PROPORTION_RECALL: None}
    recall_dict = {
        OVERALL: copy.deepcopy(template), CLOSE_MATCHES: {}, INTRUSIONS: [],
        ITEMS_RECALLED: []
    }
    targets_as_strings = []
    try:
        with open(targets) as file_object:
            targets_as_strings = file_object.readlines()
            targets_as_strings = [t.strip() for t in targets_as_strings]
    except TypeError:
        try:
            conditions = []
            denominators = {}
            for i in xrange(len(targets)):
                target = targets[i]
                current_condition = target.condition
                targets_as_strings.append(target.word)
                if current_condition not in conditions:
                    conditions.append(current_condition)
            if len(conditions) == 1:
                # Treat this the same as if no conditions were specified.
                recall_dict[CONDITION] = copy.deepcopy(template)
                del conditions
                del denominators
            else:
                for current_condition in conditions:
                    try:
                        recall_dict[current_condition] = copy.deepcopy(template)
                        denominators[current_condition] = 0
                    except TypeError:
                        recall_dict[str(current_condition)] = copy.deepcopy(
                            template
                        )
                        denominators[str(current_condition)] = 0
                for target in targets:
                    current_condition = target.condition
                    try:
                        denominators[current_condition] = denominators[current_condition]+1
                    except TypeError:
                                            denominators[str(current_condition)] = denominators[str(current_condition)]+1
        except AttributeError:
            del conditions
            del denominators
            recall_dict[CONDITION] = copy.deepcopy(template)
            targets_as_strings = list(targets)
    
    try:
        with open(responses) as file_object:
            responses = file_object.readlines()
    except TypeError:
        pass
    
    # Make sure targets_as_strings and responses are "clean":
    targets_as_strings = [t.strip() and t.upper() for t in targets_as_strings]
    # Don't overwrite responses though, in case calling script needs it
    # intact.
    responses_clean = list(responses)
    responses_clean = [r.strip() and r.upper() for r in responses_clean]
    
    # Scoring next:
    for r in responses_clean:
        if r in targets_as_strings and r not in recall_dict[ITEMS_RECALLED]:
            recall_dict[OVERALL][RAW_RECALL] = recall_dict[OVERALL][RAW_RECALL]+1
            if len(recall_dict) > 5:
                i = targets_as_strings.index(r)
                current_condition = targets[i].condition
                try:
                    recall_dict[current_condition][RAW_RECALL] = recall_dict[current_condition][RAW_RECALL]+1
                except TypeError:
                    recall_dict[str(current_condition)][RAW_RECALL] = recall_dict[str(current_condition)][RAW_RECALL]+1
            else:
                recall_dict[CONDITION][RAW_RECALL] = recall_dict[CONDITION][RAW_RECALL]+1
        elif r not in targets_as_strings:
            # r is either a close match or an intrusion.
            close_matches = difflib.get_close_matches(r, targets_as_strings)
            if close_matches:
                # There is at least one close match to r.
                recall_dict[CLOSE_MATCHES][r] = close_matches
            else:
                recall_dict[INTRUSIONS].append(r)
        recall_dict[ITEMS_RECALLED].append(r)
    
    # Calculate proportions:
    recall_dict[OVERALL][PROPORTION_RECALL] = recall_dict[OVERALL][RAW_RECALL]/len(targets)
    if len(recall_dict) > 5:
        for current_condition in denominators.keys():
            recall_dict[current_condition][PROPORTION_RECALL] = recall_dict[current_condition][RAW_RECALL]/denominators[current_condition]
    else:
        recall_dict[CONDITION][PROPORTION_RECALL] = recall_dict[OVERALL][PROPORTION_RECALL]
    return recall_dict


def cued_recall(word_pairs, close_match_cutoff = 0.6):
    """
    Score the results of a cued-recall test given the WordPair objects.
    
    A strict scoring criterion is used--that is, a response is considered to
    be correct if it exactly matches the target. Case is ignored. A list of
    close matches is returned for further examination by the experimenter.
    
    Parameters:
        word_pairs: the WordPair objects to be scored.
    
    Keyword Parameters:
        close_match_cutoff: the match between word_pairs[i].target and
            word_pairs[i].response required for the response to be categorized
            as a close match; defaults to 0.6. The similarity match is
            obtained from difflib.SequenceMatcher().ratio(), and ranges from 0
            to 1 with larger numbers indicating more similarity.
    
    Returns:
        results: a dict with the following keys:
            "condition": There is one key for each condition in word_pairs.
                If the condition attribute was not set in word_pairs, this key
                is omitted. The entry for this key is a dict with the
                following entries:
                "total recall": the total number of targets recalled.
                "proportion recall": the proportion of targets recalled.
            "overall": same as the condition dicts but conditions are ignored.
            "close matches": responses that came close to matching the target.
                This is a list of two-element tuples, with Element 0 being the
                target and Element 1 being the close match.
    """
    template = {TOTAL_RECALL: 0, PROPORTION_RECALL: None, }
    results = {OVERALL: copy.deepcopy(template), CLOSE_MATCHES: []}
    # Collect any conditions into a list:
    conditions = []
    for word_pair in word_pairs:
        if word_pair.condition not in conditions:
            conditions.append(word_pair.condition)
    if len(conditions) > 1:
        # Get denominators and add dicts to results:
        denominators = {}
        for condition in conditions:
            try:
                results[condition] = copy.deepcopy(template)
                denominators[condition] = 0
            except TypeError:
                # condition is unhashable.
                results[str(condition)] = copy.deepcopy(template)
                denominators[condition] = 0
        for word_pair in word_pairs:
            condition = word_pair.condition
            try:
                denominators[condition] = denominators[condition]+1
            except (TypeError, KeyError):
                denominators[str(condition)] = denominators[str(condition)]+1
    
    # Score results:
    for word_pair in word_pairs:
        target = word_pair.target.upper().strip()
        response = word_pair.response.upper().strip()
        if response == target:
            results[OVERALL][TOTAL_RECALL] = results[OVERALL][TOTAL_RECALL]+1
            if len(results) > 2:
                condition = word_pair.condition
                try:
                    results[condition][TOTAL_RECALL] = results[condition][TOTAL_RECALL]+1
                except (TypeError, KeyError):
                    results[str(condition)][TOTAL_RECALL] = results[str(condition)][TOTAL_RECALL]+1
        else:
            # response might be a close match.
            match = difflib.SequenceMatcher(a = target, b = response).ratio()
            if match >= close_match_cutoff:
                results[CLOSE_MATCHES].append((target, response))
    
    # Calculate proportions:
    results[OVERALL][PROPORTION_RECALL] = results[OVERALL][TOTAL_RECALL]/len(word_pairs)
    if len(results) > 2:
        for condition in denominators.keys():
            results[condition][PROPORTION_RECALL] = results[condition][TOTAL_RECALL]/denominators[condition]
    return results


def serial_position_cued_recall(word_pairs):
    """
    Get a list containing performance as a function of serial position.
    
    Parameters:
        word_pairs: the WordPair objects to be scored.
    
    Returns:
        serial_position: a list whose ith index corresponds to the result of
            the ith pair in word_pairs. Correct responses (using strict
            scoring) are denoted by a 1 and incorrect responses are denoted by
            a 0.
    """
    serial_position = []
    for word_pair in word_pairs:
        target = word_pair.target.upper().strip()
        response = word_pair.response.upper().strip()
        if target == response:
            serial_position.append(1)
        else:
            serial_position.append(0)
    return serial_position

