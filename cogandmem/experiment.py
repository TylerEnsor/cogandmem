"""
Classes and functions for running memory experiments.

This module contains the following classes. For more information on each
class, including its methods and attributes, see the class' docstring.
    InterTrialStimulus: stimulus presented during the interstimulus interval.
    RatingScale: used to collect ratings.
    Stimulus: used to create a string stimulus to display to the screen.
    WordPair: same as Stimulus, but used for two strings to be presented
together.
    Image: class for images.

The following functions are included. Again, see the docstrings for more
information.
    get_position: find a position on the screen given a string; primarily used
internally.
    copy_stimuli: create a copy of a list of Stimulus objects. The copy can be
modified without affecting the source.
    copy_word_pairs: same as copy_stimuli, but for WordPair objects.
    single_item_study_phase: present a study phase consisting of Stimulus
objects as stimuli.
    free_recall_test: present a free-recall test.
    free_recall: present a free-recall study phase and a free-recall test.
Essentially, this combines the previous two functions.
    generate_word_pairs: divides a list of strings into a list of pairs of
strings. This function is useful when randomly pairing word pairs.
Restrictions can be included so that certain pairs cannot be generated.
    cued_recall_study: the study phase for WordPair objects.
    cued_recall_test: test phase for cued recall.
"""

from __future__ import division

import sys
import os
import numpy as np
import time
import copy

import pygame
from pygame.locals import *

import text
import score
import tetromino
import writing
import generic


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LETTERS = (
    K_a, K_b, K_c, K_d, K_e, K_f, K_g, K_h, K_i, K_j, K_k, K_l, K_m,
    K_n, K_o, K_p, K_q, K_r, K_s, K_t, K_u, K_v, K_w, K_x, K_y, K_z
)
NUMBERS = (K_0, K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_9)
SCREEN_POSITIONS = (
    "top left", "top centre", "top center", "top right",
    "middle left", "middle centre", "middle center", "middle right",
    "bottom left", "bottom centre", "bottom center", "bottom right"
)
TOP = "top"
BOTTOM = "bottom"
LEFT = "left"
RIGHT = "right"
MIDDLE = "middle"
SENTENCE_TERMINATORS = (".", "!", "?"'')
START = USEREVENT+1   # to know when time within an interval begins
TIME_UP = USEREVENT+2 # used to track when stimulus presentation ends

# dict keys:
CONDITION = "condition"
RAW_RECALL = "raw recall"
PROPORTION_RECALL = "proportion recall"
CLOSE_MATCHES = "close matches"
ITEMS_RECALLED = "items recalled"
OVERALL = "overall"
INTRUSIONS = "intrusions"
DISTRACTOR = "distractor"
LINES = "lines"
LOSSES = "losses"


def get_position(p, s, f, top, right, bottom, left):
    """
    Return an x-y pixel tuple at which to centre a stimulus.
    
    Parameters:
        p: a string indicating the position; must be in SCREEN_POSITIONS.
        s: the stimulus to position.
        f: the pygame.font.Font object in which s will be rendered.
        top, right, bottom, and left: the proportion of the screen to ignore
            when setting the position. Note that asymmetrical values for top
            and bottom or left and right will only affect stimuli on that part
            of the screen--that is, centring is still with reference to the
            overall screen dimensions, not those passed to the present
            function.
    
    Returns:
        x and y: the x-y pixel coordinate for the centre of s.
    """
    assert p in SCREEN_POSITIONS, "p must be a string from SCREEN_POSITIONS."
    assert 0 <= top+bottom < 1, "The sum of top and bottom must be between 0 \
and 1."
    assert 0 <= left+right < 1, "The sum of left and right must be between 0 \
and 1."
    screen_width, screen_height = text.screen_dimensions()
    left_trim = int(left*screen_width//2)
    right_trim = int(right*screen_width//2)
    top_trim = int(top*screen_height//2)
    bottom_trim = int(bottom*screen_height//2)
    stimulus_width, stimulus_height = f.size(s)
    if "left" in p:
        x = left_trim+stimulus_width//2
    elif "centre" in p or "center" in p:
        x = screen_width//2
    elif "right" in p:
        x = screen_width-right-stimulus_width//2
    if "top" in p:
        y = top_trim+stimulus_height//2
    elif "middle" in p:
        y = screen_height//2
    elif "bottom" in p:
        y = screen_height-bottom_trim-stimulus_height//2
    return x, y


class InterTrialStimulus:
    """
    Class for inter-trial stimuli.
    
    Attributes:
        duration: milliseconds for which the ISI is presented.
    
    Keyword Attributes:
        fixation: the string displayed; defaults to "+". To have just a blank
            screen, set this to "".
        font: pygame.font.Font object used for rendering fixation; defaults to
            None, and only needs to be set if fixation evaluates to True in a
            Boolean context.
        colour: RGB list/tuple for rendering fixation; defaults to white.
        background: background RGB; defaults to black.
        antialiasing: Boolean indicating if antialiasing is used in fixation
            rendering; defaults to True.
        location: the location of fixation on the screen; defaults to "middle
            centre". Pass either a literal location on the screen from the
            SCREEN_POSITIONS constant or an x-y pixel coordinate for this
            attribute. If a string is passed, the attribute will still be
            converted to pixel coordinates.
    
    Other Attributes:
        These are not set by the user.
        x: the x coordinate of fixation's centre; None if fixation is False in
            a Boolean context.
        y: the y coordinate of fixation's centre; None if fixation is False in
            a Boolean context.
        surface: pygame.Surface object for displaying the InterTrialStimulus.
        rect: pygame.Rect object corresponding to the surface.
    
    Non-Attribute Parameters:
        top, right, bottom, left: any proportion of each part of the screen to
            remove when computing location. These all default to 0.025.
        final_width, final_height: the width and height of the final surface
            and rect. These both default to None, in which case the surface
            and rect fill the entire screen.
    
    Methods:
        present: present an interstimulus interval.
    """
    
    def __init__(self, duration, fixation = "+", font = None, colour = WHITE, background = BLACK, antialiasing = True, location = "middle centre", top = 0.025, right = 0.025, bottom = 0.025, left = 0.025, final_width = None, final_height = None):
        """Initialize an InterTrialStimulus object."""
        self.duration = duration
        self.fixation = fixation
        self.font = font
        self.colour = colour
        self.background = background
        self.antialiasing = antialiasing
        if fixation:
            assert 0 <= top+bottom < 1, "The sum of top and bottom must be \
between 0 and 1."
            assert 0 <= left+right < 1, "The sum of left and right must be \
between 0 and 1."
            try:
                location = get_position(
                    location, fixation, font, top, right, bottom, left
                )
                x, y = location
            except AssertionError:
                x, y = location
            self.x = x
            self.y = y
            self.location = location
        fixation_surface, fixation_rect = text.render_string(
            fixation, font, colour, background, antialiasing
        )
        # Surface and rect probably aren't the right size.
        try:
            final_surface = pygame.Surface((final_width, final_height))
        except ValueError:
            final_width, final_height = text.screen_dimensions()
            final_surface = pygame.Surface((final_width, final_height))
        final_rect = final_surface.get_rect()
        # final_rect may not be positioned correctly in relation to the
        # current display surface.
        screen = pygame.display.get_surface()
        try:
            screen_width, screen_height = screen.get_size()
        except AttributeError:
            # Just guess:
            screen_width, screen_height = pygame.display.list_modes()[0]
        if final_rect.width < screen_width:
            final_rect.left = (screen_width-final_rect.width)//2
        elif final_rect.width > screen_width:
            raise ValueError("The specified screen dimensions are too big.")
        if final_rect.height < screen_height:
            final_rect.top = (screen_height-final_rect.height)//2
        elif final_rect.height > screen_height:
            raise ValueError("The specified screen dimensions are too big.")
        fixation_rect.center = final_rect.center
        final_surface.fill(background)
        final_surface.blit(fixation_surface, fixation_rect)
        self.surface = final_surface
        self.rect = final_rect
    
    def present(self, time_change = 0, clock = None, frame_rate = 30, exit_keys = (K_ESCAPE,), files = ()):
        """
        Present the InterTrialStimulus for self.duration milliseconds.
        
        Keyword Parameters:
            time_change: milliseconds to add or subtract from self.duration;
                defaults to 0. The duration attribute is left unchanged.
            clock: pygame.time.Clock object; defaults to None, in which case
                one is created.
        frame_rate: frames per second; defaults to 30.
            exit_keys: keys that exit the program; defaults to escape.
            files: any files to close if the program exits; defaults to an
                    empty tuple.
        """
        try:
            set_timer_for = self.duration+time_change
        except TypeError:
            # time_change is probably None or something. Either way:
            set_timer_for = self.duration
        if set_timer_for <= 0:
            return
        else:
            main_surface = pygame.display.get_surface()
            main_surface.fill(self.background)
            main_surface.blit(self.surface, self.rect)
            if isinstance(set_timer_for, float):
                set_timer_for = int(round(set_timer_for))
            pygame.time.set_timer(TIME_UP, set_timer_for)
            pygame.display.update()
            while True:
                for event in pygame.event.get():
                    if event.type == QUIT or (event.type == KEYUP and event.key in exit_keys):
                        generic.terminate(files)
                    elif event.type == TIME_UP:
                        pygame.time.set_timer(TIME_UP, 0)
                        return
                    else:
                        pass
                try:
                    clock.tick(frame_rate)
                except AttributeError:
                    clock = pygame.time.Clock()
                    clock.tick(frame_rate)
        return


class RatingScale:
    """
    Class for rating scales.
    
    NB: Currently, the Scale class only supports scales that respond to
        keypresses (i.e., mouse-click scales are not supported).
    
    Attributes:
        choices: the number of points or categories one can select on the
            rating scale. For example, a seven-point rating scale would have
            choices equal to 7.
        font: pygame.font.Font object to use for rendering the scale.
    
    Keyword Attributes:
        horizontal: Boolean indicating if the scale is arranged horizontally
            (True) or vertically (False); defaults to True.
        colour: the colour an RGB list or tuple for the text colour; defaults
            to white.
        background: RGB for the background colour; defaults to black.
        antialiasing: Boolean indicating whether antialiasing is used in scale
            rendering; defaults to True.
        size: the proportion of the screen's width or height (depending on
            horizontal) the rating scale can take up; defaults to 0.5. This
            parameter can be a float between 0 and 1 or an int specifying the
            number of pixel columns/rows the scale should take up. Note that
            this parameter may decrease somewhat in size to ensure even
            spacing between scale anchors. Note too that, after
            initialization, this parameter is always an int referring to the
            number of pixel columns/rows the rating scale takes up (i.e., it
            will not remain a proportion).
        numbers: Boolean indicating whether numbers (True) or letters (False)
            are used for responding to the rating scale. If numbers is True,
            then choices must be between 2 and 9 (inclusive). If numbers is
            False, then choices must be between 2 and 26 (inclusive). This
            parameter defaults to True.
        characters: the characters used in depicting the rating scale;
            defaults to None, in which case it is set starting with "1" or "A"
            depending on numbers. If a list or tuple is passed, it must
            consist of choices unique strings.
        keys: the keys used for responding. This parameter defaults to None,
            in which case it is set starting with 1 or a (depending on
            numbers). If the calling script passes a list or tuple for this
            parameter, the list or tuple must be equal in length to the scale
            and must be composed of unique keys.
    
        Other Attributes:
            surface: the rating scale's pygame.Surface object.
        rect: the pygame.Rect object corresponding to surface.
    
    Methods:
        get_rating: present rating scale and get response.
    """
    
    def __init__(self, choices, font, horizontal = True, colour = WHITE, background = BLACK, antialiasing = True, size = 0.5, numbers = True, characters = None, keys = None):
        """Initialize a RatingScale object."""
        if numbers and not keys:
            assert 2 <= choices <= 9, "Because numbers is True, choices must \
be between 2 and 9, inclusive."
        elif not numbers and not keys:
            assert 2 <= choices <= 26, "Because numbers is False, choices \
must be between 2 and 26, inclusive."
        if characters:
            assert len(set(characters)) == len(characters) == choices, "The \
number of characters must be equal to the number of choices."
        if keys:
            assert len(set(keys)) == len(keys) == choices, "The number of \
keys must be equal to the number of choices."
        self.choices = choices
        self.font = font
        self.horizontal = horizontal
        self.colour = colour
        self.background = background
        self.antialiasing = antialiasing
        self.numbers = numbers
        if size <= 1:
            # size is a proportion, so determine the specific number of pixel
            # columns/rows:
            screen = pygame.display.get_surface()
            if horizontal:
                try:
                    pixels = screen.get_size()[0]
                except AttributeError:
                    # Just take the first supported screen width:
                    pixels = pygame.display.list_modes()[0][0]
            else:
                try:
                    pixels = screen.get_size()[1]
                except AttributeError:
                    pixels = pygame.display.list_modes()[0][1]
            size = int(size*pixels)
        if not characters:
            characters = []
            if numbers:
                current_key = K_1
            else:
                current_key = K_a
            for i in xrange(choices):
                character = pygame.key.name(current_key)
                if not numbers:
                    character = character.upper()
                characters.append(character)
                current_key = current_key+1
        self.characters = characters
        if not keys:
            keys = []
            if numbers:
                current_key = K_1
            else:
                current_key = K_a
            for i in xrange(choices):
                keys.append(current_key)
                current_key = current_key+1
        self.keys = keys
        pixels_per_anchor = size//len(characters)
        # Update size:
        size = pixels_per_anchor*len(characters)
        self.size = size
        if horizontal:
            assert all(font.size(character)[0] < pixels_per_anchor for \
character in characters), "At least one of the anchor characters is too wide \
when rendered with the given font."
            # Build the surface and rect attributes:
            height = font.size(characters[0])[1]
            for character in characters[1:]:
                if font.size(character)[1] > height:
                    height = font.size(character)[1]
            scale_surface = pygame.Surface((size, height))
            scale_surface.fill(background)
            left_margin = 0
            for character in characters:
                character_surf, character_rect = text.render_string(
                    character, font, colour, background, antialiasing
                )
                character_rect.topleft = (left_margin, 0)
                left_margin = left_margin+pixels_per_anchor
                scale_surface.blit(character_surf, character_rect)
        else:
            assert all(font.size(character)[1] < pixels_per_anchor for \
character in characters), "At least one of the anchor characters is too tall \
when rendered with the given font."
            width = font.size(characters[0])[0]
            for character in characters[1:]:
                if font.size(character)[0] > width:
                    width = font.size(character)[0]
            scale_surface = pygame.Surface((width, size))
            scale_surface.fill(background)
            top_margin = 0
            for character in characters:
                character_surf, character_rect = text.render_string(
                    character, font, colour, background, antialiasing
                )
                character_rect.topleft = (0, top_margin)
                top_margin = top_margin+pixels_per_anchor
                scale_surface.blit(character_surf, character_rect)
        self.surface = scale_surface
        self.rect = scale_surface.get_rect()
    
    def get_rating(self, scale_position = BOTTOM, rated_text = None, duration = None, return_after_input = False, text_position = MIDDLE, exclude_top = 0.025, exclude_right = 0.025, exclude_bottom = 0.025, exclude_left = 0.025, text_colour = None, text_background = None, text_font = None, text_antialias = True, timer = None, frame_rate = 30, exit_keys = (K_ESCAPE,), files = ()):
        """
        Get input on the rating scale.
        
        Keyword Parameters:
            scale_position: the location of the scale on the screen; defaults
                to "bottom". If RatingScale.horizontal is True, then
                scale_position must be "top", "middle", or "bottom".
                Otherwise, scale_position must be "left", "middle", or
                "right".
            rated_text: text to be rated; defaults to None, in which case just
                the scale appears. This parameter can be a pygame.Surface object,
                a string, a Stimulus object, or a WordPair object.
            duration: the time, in milliseconds, for which the scale appears;
                defaults to None, in which case the function only returns when
                a response is made.
            return_after_input: only has an effect if a number is passed for
                duration. This is a Boolean indicating whether the function
                ends as soon as input is made or if the scale remains on the
                screen until duration milliseconds have elapsed.
            text_position: the position of rated_text on the screen, if
                applicable. If self.horizontal is True, this must be "top",
                "middle", or "bottom". Otherwise, text_position must be
                "left", "middle", or "right". text_position and scale_position
                may not be equal.
            top_exclude, right_exclude, bottom_exclude, and left_exclude: the
                proportion of this quadrant of the screen to exclude when
                calculating positions; all default to 0.025.
            text_colour: the RGB colour of rated_text, if applicable; defaults
                to None, in which case it is set to self.colour if needed.
            text_background: the RGB colour on which rated_text is shown, if
                applicable; defaults to None, in which case it is set to
                self.background if needed.
            text_font: pygame.font.Font object to use for rated_text, if
                applicable; defaults to None, in which case self.font is used.
            text_antialias: Boolean indicating whether antialiasing is used in
                rendering rated_text; defaults to True, but only applies if a
                string is passed for rated_text.
            timer: pygame.time.Clock object; defaults to None, in which case
                one is created.
            frame_rate: frames per second; defaults to 30.
            exit_keys: keys that close the program; defaults to escape.
            files: any files that need to be closed if the program closes.
        
        Returns:
            rating: the rating made to the scale.
            time_remaining: None unless duration and return_after_input both
                evaluate to True in a Boolean context, in which case the
                number of milliseconds remaining is returned.
        """
        screen = pygame.display.get_surface()
        try:
            screen.fill(self.background)
        except AttributeError:
            screen = pygame.display.set_mode(pygame.display.list_modes()[0])
            screen.fill(self.background)
        # Get permitted dimensions:
        screen_width, screen_height = screen.get_size()
        pixel_columns = int(screen_width-(exclude_left+exclude_right)*screen_width)
        pixel_rows = int(screen_height-(exclude_top+exclude_bottom)*screen_height)
        # Position scale:
        scale_surface = self.surface
        scale_rect = self.rect
        if self.horizontal:
            scale_rect.left = int(exclude_left*screen_width+pixel_columns//2-scale_rect.width//2)+1
            if scale_position == TOP:
                scale_rect.top = int(exclude_top*screen_height+1)
            elif scale_position == MIDDLE:
                scale_rect.top = int(
                    exclude_top*screen_height+pixel_rows//2-scale_rect.height//2
                )
            else:
                scale_rect.bottom = int(
                    screen_height-exclude_bottom*screen_height-1
                )
        else:
            scale_rect.top = int(
                exclude_top*screen_height+pixel_rows//2-scale_rect.height//2+1
            )
            if scale_position == LEFT:
                scale_rect.left = int(exclude_left*screen_width+1)
            elif scale_position == MIDDLE:
                scale_rect.left = int(
                    exclude_left*screen_width+pixel_columns//2-scale_rect.width//2
                )
            else:
                scale_rect.right = int(screen_width-exclude_right*screen_width-1)
        if rated_text:
            try:
                # rated_text might be a Stimulus object.
                rated_surf, rated_rect = rated_text.get_surface_and_rect()
            except AttributeError:
                try:
                    # Or maybe it's a WordPair.
                    rated_surf = rated_text.get_pair_surface()
                    rated_rect = rated_surf.get_rect()
                except AttributeError:
                    # Then it's a string or already a surface.
                    try:
                        rated_rect = rated_text.get_rect()
                        rated_surf = rated_text
                    except AttributeError:
                        # It's a string.
                        if not text_colour:
                            text_colour = self.colour
                        if not text_background:
                            text_background = self.background
                        if not text_font:
                            text_font = self.font
                        if text_antialias is None:
                            text_antialias = self.antialiasing
                        # Determine max dimensions for rated_surf.
                        if scale_position == TOP or scale_position == BOTTOM:
                            max_width = pixel_columns
                            if scale_position == TOP:
                                max_height = pixel_rows-scale_rect.height-self.font.get_linesize()
                            else:
                                max_height = pixel_rows-scale_rect.height-text_font.get_linesize()
                        elif scale_position == LEFT or scale_position == RIGHT:
                            max_height = pixel_rows
                            max_width = pixel_columns-scale_rect.width-self.font.size(" ")[0]
                        elif self.horizontal:
                            max_width = pixel_columns
                            if text_position == TOP:
                                max_height = pixel_rows//2-scale_rect.height//2-text_font.get_linesize()
                            else:
                                max_height = pixel_rows//2-scale_rect.height//2-self.font.get_linesize()
                        else:
                            max_height = pixel_rows
                            max_width = pixel_columns//2-scale_rect.width//2-self.font.size(" ")[0]
                        rated_surf, rated_rect = memory.text.string_to_surface_and_rect(
                            rated_text, text_font, text_colour,
                            text_background, max_width, max_height,
                            antialiasing = text_antialias
                        )
            # Check if rated_surf fits (already done if rated_text is str):
            if not isinstance(rated_text, str):
                rated_width, rated_height = scale_rect.size
                assert rated_width <= pixel_columns, "rated_text is too wide."
                assert rated_height <= pixel_rows, "rated_text is too tall."
                if scale_position == TOP or scale_position == BOTTOM:
                    assert rated_height < pixel_rows-scale_rect.height, \
"rated_text is too tall."
                elif scale_position == LEFT or scale_position == RIGHT:
                    assert rated_width < pixel_columns-scale_rect.width, \
"rated_text is too wide."
                elif self.horizontal:
                    assert rated_height < pixel_rows//2-scale_rect.height//2, \
"rated_text is too tall."
                else:
                    assert rated_width < pixel_columns//2-scale_rect.width//2, \
"rated_text is too wide."
            # Position rated_rect:
            if scale_position == TOP or scale_position == BOTTOM:
                rated_rect.left = pixel_columns//2-rated_rect.height//2+int(exclude_left*screen_width)
                if scale_position == TOP:
                    rated_rect.top = scale_rect.bottom+(pixel_rows-scale_rect.height)//2-rated_rect.height//2
                else:
                    rated_rect.bottom = scale_rect.top-(pixel_rows-scale_rect.height)//2+rated_rect.height//2
            elif scale_position == LEFT or scale_position == RIGHT:
                rated_rect.top = pixel_rows//2-rated_rect.height//2+exclude_top*screen_height
                if scale_position == LEFT:
                    rated_rect.left = scale_rect.right+(pixel_columns-scale_rect.width)//2-rated_rect.width//2
                else:
                    scale_rect.right = scale_rect.left-(pixel_columns-scale_rect.width)//2+rated_rect.width//2
            screen.blit(rated_surf, rated_rect)
        screen.blit(scale_surface, scale_rect)
        pygame.display.update()
        if duration:
            duration_as_seconds = generic.milliseconds_to_seconds(duration)
            start_time = time.time()
            if not return_after_input:
                response_obtained = False
        while True:
            if duration and time.time()-start_time >= duration_as_seconds:
                if return_after_input:
                    return None, 0
                else:
                    try:
                        return rating
                    except NameError:
                        return
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYUP and event.key in exit_keys):
                    generic.terminate(files)
                elif event.type == KEYUP and event.key in self.keys:
                    if duration and return_after_input:
                        return self.characters[self.keys.index(event.key)], time.time()-start_time
                    elif duration and not return_after_input:
                        rating = self.characters[self.keys.index(event.key)]
                        response_obtained = True
                    else:
                        return self.characters[self.keys.index(event.key)]
                else:
                    pass
            try:
                timer.tick(frame_rate)
            except AttributeError:
                timer = pygame.time.Clock()
                timer.tick(frame_rate)
        return


class Stimulus:
    """
    Class for stimuli.
    
    Attributes:
        word: the stimulus.
        font: pygame.font.Font object in which word appears.
    
    Keyword Attributes:
        colour: RGB list or tuple for the text colour; defaults to white.
        background: RGB for the background on which word is rendered; defaults
            to black.
        antialiasing: Boolean indicating whether antialiasing is used when
            rendering word; defaults to True.
        condition: optional attribute to keep track of the stimulus'
            condition; defaults to None.
        x: the x coordinate at which word is centred.
        y: the y coordinate at which word is centred.
        response: the response made to Stimulus; defaults to None.
    
    Non-Attribute Parameters:
        These are only necessary if coordinates are not passed for x and y.
        position: the location on the screen at which word is centred
            during the study phase; must be a string from SCREEN_POSITIONS
defaults to "middle centre".
        top_exclude, right_exclude, bottom_exclude, and left_exclude: the
            proportion of the screen to ignore when positioning word; all
            default to 0.025.
    
    Methods:
        get_surface: returns a pygame.Surface object for Stimulus.
        get_surface_and_rect: returns pygame.Surface and pygame.Rect objects
            for Stimulus.
        study: present Stimulus for study.
        test: present Stimulus for a cued-recall or recognition test.
        create_copy: return a copy of Stimulus.
    """
    
    def __init__(self, word, font, colour = WHITE, background = BLACK, antialiasing = True, condition = None, x = None, y = None, response = None, position = "middle centre", top_exclude = 0.025, right_exclude = 0.025, bottom_exclude = 0.025, left_exclude = 0.025):
        """Initialize a Stimulus object."""
        self.word = word
        self.font = font
        self.colour = colour
        self.background = background
        self.antialiasing = antialiasing
        self.condition = condition
        self.response = response
        if x == None and y == None:
            x, y = get_position(
                position, word, font, top_exclude, right_exclude,
                bottom_exclude, left_exclude
            )
        elif x == None or y == None:
            raise TypeError(
                "You cannot set only one of the x and y attributes. Either"
                "set both or neither."
            )
        self.x = x
        self.y = y
    
    def get_surface(self):
        """Return the pygame.Surface for the Stimulus."""
        return self.font.render(self.word, self.antialiasing, self.colour)
    
    def get_surface_and_rect(self):
        """Get the Surface and Rect objects with Rect centred at (x, y)."""
        s = self.get_surface()
        r = s.get_rect()
        r.center = (self.x, self.y)
        return s, r
    
    def study(self, duration, ticker = None, frame_rate = 30, quit_keys = (K_ESCAPE,), files = ()):
        """
        Present the stimulus for duration milliseconds.
        
        Parameters:
            duration: milliseconds for which to present stimulus.
        
        Keyword Parameters:
            ticker: pygame.time.Clock object; defaults to None. If one is not
                passed, one is created.
            frame_rate: frames per second; defaults to 30.
            quit_keys: keys that exit the program; defaults to the escape key.
            files: any files that need to be closed if the program exits;
                defaults to an empty tuple.
        """
        s, r = self.get_surface_and_rect()
        trial_over = False
        screen = pygame.display.get_surface()
        try:
            screen.fill(self.background)
        except AttributeError:
            screen = pygame.display.set_mode(pygame.display.list_modes()[0])
            screen.fill(self.background)
        screen.blit(s, r)
        pygame.time.set_timer(TIME_UP, duration)
        pygame.display.update()
        while not trial_over:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYUP and event.key in quit_keys):
                    generic.terminate(files)
                elif event.type == TIME_UP:
                    trial_over = True
                    pygame.time.set_timer(TIME_UP, 0)
                else:
                    pass
            try:
                ticker.tick(frame_rate)
            except AttributeError:
                ticker = pygame.time.Clock()
                ticker.tick(frame_rate)
    
    def test(self, allowed_keys = LETTERS, require_return = True, allow_changes = True, show_input = True, min_input = 1, max_input = None, ticker = None, frame_rate = 30, quit_keys = (K_ESCAPE,), files = ()):
        """
        Present the Stimulus object for cued recall, old/new recognition, or
        any other paradigm that requires a response to a single-word probe.
        
        A couple things to note:
            1. For now, probes always appear in the centre of the screen. This
                makes rendering the user's typed response (if necessary)
                straightforward.
            2. Stimulus objects passed to this function gain a new attribute:
                response. This contains the response given at test.
        
        Keyword Parameters:
            allowed_keys: keys that can be included in the subject's response;
                defaults to the letters a to z.
            require_return: Boolean indicating whether pressing return is
                required upon completing input; defaults to True, and will
                only have an effect when set to False if min_response and
                max_response are equal (i.e., if min_response and max_response
                are unequal, then it is impossible to know when the response
                is finished without a return keypress).
            allow_changes: Boolean indicating whether characters can be
                deleted after being input; defaults to True; changes obviously
                cannot be made if min_response and max_response are 1 and
                require_return is False.
            show_input: Boolean indicating whether typed keys from
                allowed_keys appear on the screen. show_input is effectively
                False if max_input is 1 and require_return is False. The
                default value is True. If allow_changes is True, show_input is
                automatically changed to True.
            min_input: the minimum length of the response; defaults to 1.
            max_input: the maximum length of the response; defaults to None,
                in which case no maximum is placed.
            ticker: pygame.time.Clock object; if one is not passed, one is
                created.
            frame_rate: frames per second; defaults to 30.
            quit_keys: keys that exit the program; defaults to the escape key.
            files: files to close if a key from quit_keys is pressed.
        """
        if max_response == 1 and min_response == 1 and not require_return and allow_changes:
            allow_changes = False
        if allow_changes and not show_input:
            show_input = True
        
        user_response = ""
        response_obtained = False
        probe_surf = self.get_surface()
        screen = pygame.display.get_surface()
        try:
            screen.fill(self.background)
        except AttributeError:
            screen = pygame.display.set_mode(pygame.display.list_modes[0])
            screen.fill(self.background)
        screen_width, screen_height = screen.get_size()
        screen_centre = (screen_width//2, screen_height//2)
        probe_rect = probe_surf.get_rect()
        probe_rect.center = screen_centre
        screen.blit(probe_surf, probe_rect)
        
        if show_input:
            line_size = self.font.get_linesize()
            response_top_left = (probe_rect.left, probe_rect.bottom+line_size)
        pygame.display.update()
        while not response_obtained:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYUP and event.key in quit_keys):
                    generic.terminate(files)
                elif event.type == KEYUP and event.key in allowed_keys and (max_input != None or len(user_response) < max_input):
                    # This is an allowed keypress.
                    user_response = user_response+pygame.key.name(event.key)
                    if show_input:
                        r_surface, r_rect = text.render_string(
                            user_response, self.font, self.colour,
                            self.background, antialiasing = self.antialiasing
                        )
                        r_rect.topleft = response_top_left
                        screen_surface.fill(self.background, r_rect)
                        screen.blit(r_surface, r_rect)
                        pygame.display.update(r_rect)
                    if not require_return and len(user_response) == max_input:
                        # The response is finished.
                        response_obtained = True
                elif event.type == KEYUP and event.key == K_BACKSPACE and allow_changes and len(user_response) > 0:
                    # The last character has been deleted.
                    user_response = user_response[:len(r)-1]
                    update_rect = r_rect
                    r_surface, r_rect = text.render_string(
                        user_response, self.font, self.colour,
                        self.background, antialiasing = self.antialiasing
                    )
                    r_rect.topleft = response_top_left
                    screen.fill(self.background, update_rect)
                    screen.blit(r_surface, r_rect)
                    pygame.display.update(r_rect)
                elif event.type == KEYUP and event.key == K_RETURN and require_return and len(user_response) >= min_input:
                    # The subject has finished the response.
                    response_obtained = True
                else:
                    pass
            try:
                ticker.tick(frame_rate)
            except AttributeError:
                ticker = pygame.time.Clock()
                ticker.tick(frame_rate)
        self.response = user_response
    
    def create_copy(self):
        """
        Create and return a copy of Stimulus.
        
        The returned copy can be tampered with without affecting the original:
        This is because mutable objects (like lists and dicts) are copied to
        the new Stimulus using the copy.deepcopy() function.
        """
        word_copy = self.word
        font_copy = self.font
        colour_copy = copy.deepcopy(self.colour)
        background_copy = copy.deepcopy(self.background)
        antialiasing_copy = self.antialiasing
        condition_copy = copy.deepcopy(self.condition)
        x_copy = self.x
        y_copy = self.y
        response_copy = copy.deepcopy(self.response)
        stimulus_copy = Stimulus(
            word_copy, font_copy, colour = colour_copy,
            background = background_copy, antialiasing = antialiasing_copy,
            condition = condition_copy, x = x_copy, y = y_copy,
            response = response_copy
        )
        return stimulus_copy


class WordPair:
    """
    Class for word pairs.
    
    Attributes:
        word1: the left or top word.
        word2: the right or bottom word.
        font: pygame.font.Font object in which word appears.
    
    Keyword Attributes:
        apart: the number of pixels between word1 and word2; defaults to 135,
            which is about an inch based on my back-of-the-hand calculations
            (don't rely on this too much). The apart parameter can also be
            between 0 and 1, in which case the distance between the words will
            be set to the specified proportion of the screen.
        left_to_right: Boolean indicating whether word1 and word2 are
            presented with word1 on the left and word2 on the right; defaults
            to True. If left_to_right is False, word1 is presented above
            word2.
        cue: the member of the word pair that serves as the cue at test;
            defaults to None, in which case one of the words is randomly
            chosen to be the cue.
        target: the member of the word pair that serves as the target at test;
            defaults to None, in which case it is set to the noncue member of
            the pair.
        colour: RGB list or tuple for the text colour; defaults to white.
        background: RGB for the background on which the words appear; defaults
            to black.
        antialiasing: Boolean indicating whether antialiasing is used in text
            rendering; defaults to True.
        condition: optional attribute to keep track of the word pair's
            condition; defaults to None.
        response: the response made to the cue at test; defaults to None.
        rating: rating made to WordPair at study (e.g., relatedness judgment
            as an orienting task); may not be applicable, and defaults to
            None.
    
    Methods:
        get_surface1: get the pygame.Surface for word1.
        get_surface2: get the pygame.Surface for word2.
        get_cue_surface: get the pygame.Surface object for cue.
        get_target_surface: get the pygame.Surface object for target.
        get_pair_surface: get the pygame.Surface object for WordPair.
        study: present WordPair for study.
        test: get the WordPair for test.
        create_copy: create an independently modifiable copy of WordPair.
    """
    
    def __init__(self, word1, word2, font, apart = 135, left_to_right = True, cue = None, target = None, colour = WHITE, background = BLACK, antialiasing = True, condition = None, response = None, rating = None):
        """Initialize a WordPair object."""
        self.word1 = word1
        self.word2 = word2
        self.font = font
        self.left_to_right = left_to_right
        self.colour = colour
        self.background = background
        self.antialiasing = antialiasing
        self.condition = condition
        self.response = response
        self.rating = rating
        if apart >= 1:
            self.apart = apart
        else:
            # apart is specifying a proportion of the screen.
            main_surface = pygame.display.get_surface()
            try:
                width, height = main_surface.get_size()
            except AttributeError:
                width, height = pygame.display.list_modes()[0]
            if left_to_right:
                self.apart = int(apart*width)
            else:
                self.apart = int(apart*height)
        if not cue:
            cue, target = np.random.choice((word1, word2), 2, False)
        self.cue = cue
        self.target = target
    
    def get_surface1(self):
        """Return a surface for word1."""
        return self.font.render(
            self.word1, self.antialiasing, self.colour, self.background
        )
    
    def get_surface2(self):
        """Return a surface for word2."""
        return self.font.render(
            self.word2, self.antialiasing, self.colour, self.background
        )
    
    def get_cue_surface(self):
        """Return a surface for the cue."""
        if self.cue == self.word1:
            return self.get_surface1()
        return self.get_surface2()
    
    def get_target_surface(self):
        """Return a surface for the target."""
        if self.target == self.word1:
            return self.get_surface1()
        return self.get_surface2()
    
    def get_pair_surface(self):
        """Return a surface for the word pair."""
        surf1 = self.get_surface1()
        surf2 = self.get_surface2()
        rect1 = surf1.get_rect()
        rect2 = surf2.get_rect()
        main_surface = pygame.display.get_surface()
        try:
            width, height = main_surface.get_size()
        except AttributeError:
            width, height = pygame.display.list_modes()[0]
        if self.left_to_right:
            centre = width//2
            rect1.right = centre-self.apart//2
            rect2.left = centre+self.apart//2
            rect1.top = height//2-rect1.height//2
            rect2.top = height//2-rect2.height//2
        else:
            centre = height//2
            rect1.bottom = centre-self.apart//2
            rect2.top = centre+self.apart//2
            rect1.left = width//2-rect1.width//2
            rect2.left = width//2-rect2.width//2
        s = pygame.Surface((width, height))
        s.fill(self.background)
        s.blit(surf1, rect1)
        s.blit(surf2, rect2)
        return s
    
    def study(self, duration, scale = None, end_after_input = True, ticker = None, frame_rate = 30, exit_keys = (K_ESCAPE,), other_files = ()):
        """
        Present WordPair for duration milliseconds. Optionally, a Scale object
        can be included. If a Scale is included, the input on the Scale is
        saved in self.rating. If end_after_input is True, the trial ends
        following scale input and the remaining milliseconds in the trial is
        returned.
        
        Parameters:
            duration: milliseconds for which WordPair is presented.
        
        Keyword Parameters:
            scale: an optional Scale object to appear with WordPair; defaults
                to None. If set, it is assumed that the scale is already on
                the main screen (i.e., it does not need to be blitted).
            end_after_input: Boolean indicating whether a trial ends when
                input to a Scale object is entered; defaults to True, and has
                no effect unless a Scale object is passed.
            ticker: pygame.time.Clock object; defaults to None, in which case
                one is created.
            frame_rate: frames per second; defaults to 30; must be > 0.
            exit_keys: keys that cause the program to terminate.
            files: any files to close if generic.terminate() is called; defaults
                to an empty tuple.
        """
        if scale:
            if any(key in exit_keys for key in scale.keys):
                raise ValueError(
                    "There cannot be overlap between exit_keys and \
scale.keys."
                )
        screen = pygame.display.get_surface()
        study_surface = self.get_pair_surface()
        study_rect = study_surface.get_rect()
        try:
            screen.fill(self.background)
        except AttributeError:
            screen = pygame.display.set_mode(pygame.display.list_modes()[0])
            screen.fill(self.background)
        screen.blit(study_surface, study_rect)
        if scale:
            screen.blit(scale.surface, scale.rect)
        pygame.display.update()
        pygame.time.set_timer(TIME_UP, duration)
        if scale and end_after_input:
            start_time = time.time()
        while True:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYUP and event.key in exit_keys):
                    generic.terminate(other_files)
                elif event.type == TIME_UP:
                    pygame.time.set_timer(TIME_UP, 0)
                    if end_after_input:
                        # No response was made.
                        return 0
                    else:
                        return
                elif event.type == KEYUP and scale and event.key in scale.keys:
                    self.rating = pygame.key.name(event.key)
                    if end_after_input:
                        time_studying = generic.seconds_to_milliseconds(
                            time.time()-start_time
                        )
                        time_left = duration-time_studying
                        return time_left
                else:
                    pass
            try:
                ticker.tick(frame_rate)
            except AttributeError:
                ticker = pygame.time.Clock()
                ticker.tick(frame_rate)
        return
    
    def test(self, allowed_keys = LETTERS, ticker = None, frame_rate = 30, exit_keys = (K_ESCAPE,), files = ()):
        """
        Present the cue and wait for a response. Nothing is returned, but the
        response is saved in self.response.
        
        Keyword Parameters:
            allowed_keys: keys the can be typed in response to the cue;
                defaults to a-z.
            ticker: pygame.time.Clock object; defaults to None, in which case
                one is created.
            frame_rate: frames per second; defaults to 30.
            exit_keys: keys that cause the program to terminate; defaults to
                the escape key.
            files: any files that need to be closed if the program closes.
        """
        response = ""
        cue_surf = self.get_cue_surface()
        cue_rect = cue_surf.get_rect()
        screen = pygame.display.get_surface()
        screen_width, screen_height = screen.get_size()
        cue_rect.center = (screen_width//2, screen_height//2)
        screen.fill(self.background)
        screen.blit(cue_surf, cue_rect)
        response_top = cue_rect.bottom+self.font.get_linesize()
        pygame.display.update()
        while True:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYUP and event.key in exit_keys):
                    generic.terminate(files)
                elif event.type == KEYUP and event.key == K_RETURN:
                    self.response = response
                    return
                elif event.type == KEYUP and event.key == K_BACKSPACE and response:
                    old_rect = response_rect.copy()
                    response = response[:len(response)-1]
                    screen.fill(self.background, old_rect)
                    response_surf, response_rect = text.render_string(
                        response, self.font, self.colour, self.background,
                        antialiasing = self.antialiasing
                    )
                    response_rect.center = (screen_width//2, screen_height//2)
                    response_rect.top = response_top
                    screen.blit(response_surf, response_rect)
                    pygame.display.update(
                        generic.combine_rects((old_rect, response_rect))
                    )
                elif event.type == KEYUP and event.key in allowed_keys:
                    if response:
                        old_rect = response_rect.copy()
                        screen.fill(self.background, old_rect)
                    response = response+pygame.key.name(event.key)
                    response_surf, response_rect = text.render_string(
                        response, self.font, self.colour, self.background,
                        antialiasing = self.antialiasing
                    )
                    response_rect.center = (screen_width//2, screen_height//2)
                    response_rect.top = response_top
                    screen.blit(response_surf, response_rect)
                    try:
                        pygame.display.update(
                            generic.combine_rects((old_rect, response_rect))
                        )
                    except UnboundLocalError:
                        pygame.display.update(response_rect)
            try:
                ticker.tick(frame_rate)
            except AttributeError:
                ticker = pygame.time.Clock()
                ticker.tick(frame_rate)
    
    def create_copy(self):
        """
        Create and return a copy of WordPair.
        
        The returned copy can be changed without affecting the original.
        This is because mutable objects are copied to the new WordPair using
        copy.deepcopy() function.
        """
        word1_copy = self.word1
        word2_copy = self.word2
        font_copy = self.font
        left_to_right_copy = self.left_to_right
        cue_copy = self.cue
        target_copy = self.target
        colour_copy = copy.deepcopy(self.colour)
        background_copy = copy.deepcopy(self.background)
        antialiasing_copy = self.antialiasing
        condition_copy = copy.deepcopy(self.condition)
        response_copy = copy.deepcopy(self.response)
        word_pair_copy = WordPair(
            word1_copy, word2_copy, font_copy,
            left_to_right = left_to_right_copy, cue = cue_copy,
            target = target_copy, colour = colour_copy,
            background = background_copy, antialiasing = antialiasing_copy,
            condition = condition_copy, response = response_copy
        )
        return word_pair_copy


def copy_stimuli(stimuli):
    """
    Return a copy of a list of stimuli. The returned copy can be modified
    without affecting the original.
    """
    new_list = []
    for stim in stimuli:
        stim_copy = stim.create_copy()
        new_list.append(stim_copy)
    return new_list


def copy_word_pairs(word_pairs):
    """
    Return a copy of a list of WordPairs. The returned copy can be modified
    without affecting the original.
    """
    new_list = []
    for pair in word_pairs:
        pair_copy = pair.create_copy()
        new_list.append(pair_copy)
    return new_list


class Image:
    """
    Class for images.
    
    Attributes:
        file_name: string pointing to the file containing the image.
    
    Keyword Attributes:
        label: an optional label for the picture; used to score, for example,
             a free-recall test; defaults to None.
        background: RGB tuple for the colour of the surface on which the
            picture is blitted; defaults to black. This attribute has no
            effect if the picture takes up the whole screen.
        height and width: the desired height and width (in pixels) of the
            image; default to None, in which case the dimensions contained in
            image_file are used. Pixel values can be passed for height and
            width or, alternatively, proportions can be passed, in which case
            height and width are set to that proportion of the screen. So, a
            value of .60 for height will result in an image that takes up 60%
            of the screen's height, and a value of .31 for the width will
            result in an image that takes up 31% of the screen's width. Pixel
            values in this case are rounded down to the nearest pixel.
        condition: optional attribute to keep track of the image's condition.
        x and y: the horizontal and vertical coordinates at which the image is
            centred; default to None, in which case the centre of the
            currently active surface is used.
        response: the response made to the image; defaults to None.
        rating: the rating made to the picture; defaults to None.
    
    Methods:
        get_surface: returns a pygame.Surface object for the image.
        get_surface_and_rect: returns pygame.Surface and pygame.Rect objects
            for the image.
        study: present the image for study.
        get_keypress: present the image and wait for a keypress.
        recognition_probe: present the image for a old/new recognition test.
        rate: get a rating for the image.
        create_copy: return a copy of the image.
    """
    
    def __init__(self, file_name, label = None, background = BLACK, height = None, width = None, condition = None, x = None, y = None, response = None, rating = None):
        """Initialize an Image object."""
        self.file_name = file_name
        self.label = label
        self.background = background
        self.condition = condition
        self.response = response
        self.rating = rating
        if 0 < width < 1 or 0 < height < 1 or x is None or y is None:
            # The active surface is needed.
            active_surface = pygame.display.get_surface()
            try:
                active_width, active_height = active_surface.get_size()
            except AttributeError:
                active_width, active_height = pygame.display.list_modes()[0]
            if width < 1:
                width = int(active_width*width)
            if height < 1:
                height = int(active_height*height)
            if x is None:
                x = active_width//2
            if y is None:
                y = active_height//2
        self.width = width
        self.height = height
        self.x = x
        self.y = y
    
    def get_surface(self):
        """Return a pygame.Surface object for the image."""
        image_surface = pygame.image.load(self.file_name)
        # image_surface may need to be scaled.
        if self.width != image_surface.get_width or self.height != image_surface.get_height:
            image_surface = pygame.transform.scale(
                image_surface, (self.width, self.height)
            )
        return image_surface
    
    def get_surface_and_rect(self):
        """
        Returns pygame.Surface and pygame.Rect objects for Image. The rect is
        positioned according to the x-y coordinates.
        """
        image_surface = self.get_surface()
        image_rect = image_surface.get_rect()
        image_rect.center = (self.x, self.y)
        return image_surface, image_rect
    
    def study(self, duration, ticker = None, frame_rate = 30, quit_keys = (K_ESCAPE,), files = ()):
        """
        Present Image for duration milliseconds.
        
        NB: If timing is important, the study_pictures() function should be
            used instead. In that function, image_i+1 is loaded while image_i
            is presented. Here, if the picture files are large, there may be
            some lag.
        
        Parameters:
            duration: milliseconds for which to present Image.
        
        Keyword Parameters:
            ticker: pygame.time.Clock object or None (default). If the latter,
                a clock is created.
            frame_rate: frames per second; defaults to 30.
            quit_keys: keys that close the program when pressed; defaults to
                the escape key.
            files: any files that need to be closed if the program exits;
                defaults to an empty tuple.
        """
        s, r = self.get_surface_and_rect()
        trial_over = False
        screen = pygame.display.get_surface()
        try:
            screen.fill(self.background)
        except AttributeError:
            screen = pygame.display.set_mode(pygame.display.list_modes()[0])
            screen.fill(self.background)
        screen.blit(s, r)
        pygame.time.set_timer(TIME_UP, duration)
        pygame.display.update()
        while not trial_over:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYUP and event.key in quit_keys):
                    generic.terminate(files)
                elif event.type == TIME_UP:
                    trial_over = True
                    pygame.time.set_timer(TIME_UP, 0)
                else:
                    pass
            try:
                ticker.tick(frame_rate)
            except AttributeError:
                ticker = pygame.time.Clock()
                ticker.tick(frame_rate)
    
    def get_keypress(self, response_keys = (K_o, K_n), start_time = 0, end_time = None, ticker = None, frame_rate = 30, quit_keys = (K_ESCAPE,), files = ()):
        """
        Present Image to the screen and wait for a key from response_keys to
        be pressed. A string denoting the pressed key is returned.
        
        Keyword Parameters:
            response_keys: the keys that can be pressed in response to the
                probe; defaults to the o and n keys.
            start_time: the time, in milliseconds, that must elapse before a
            response can be made; defaults to 0.
            end_time: the total number of time, in milliseconds, allowed for a
                response to be made. If end_time milliseconds elapse without
                a response, the trial ends. If end_time is None, no time limit
                is imposed, and the probe remains on the screen until the
                subject responds.
            ticker: pygame.time.Clock object; defaults to None, in which case
                a clock is created.
            frame_rate: frames per second; defaults to 30.
            quit_keys: keys that close the program; defaults to escape.
            files: any files that need to be closed if the program closes.
        """
        s, r = self.get_surface_and_rect()
        trial_over = False
        screen = pygame.display.get_surface()
        try:
            screen.fill(self.background)
        except AttributeError:
            screen = pygame.display.set_mode(pygame.display.list_modes()[0])
            screen.fill(self.background)
        screen.blit(s, r)
        if end_time is not None:
            pygame.time.set_timer(TIME_UP, end_time)
        if start_time == 0:
            response_allowed = True
        else:
            response_allowed = False
            pygame.time.set_timer(START, start_time)
        pygame.display.update()
        while not trial_over:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYUP and event.key in quit_keys):
                    generic.terminate(files)
                elif event.type == START:
                    response_allowed = True
                    pygame.time.set_timer(START, 0)
                elif event.type == TIME_UP:
                    trial_over = True
                    pygame.time.set_timer(TIME_UP, 0)
                    pressed = None
                elif event.type == KEYUP and event.key in response_keys and response_allowed:
                    pressed = pygame.key.name(event.key)
                    trial_over = True
                else:
                    pass
            try:
                ticker.tick(frame_rate)
            except AttributeError:
                ticker = pygame.time.Clock()
                ticker.tick(frame_rate)
        return pressed
    
    def recognition_probe(self, allowed_keys = (K_o, K_n), begin_time = 0, finish_time = None, c = None, fps = 30, exit_keys = (K_ESCAPE,), files = ()):
        """
        Present Image as a recognition probe. Nothing is returned; rather, the
        response is recorded in self.response. Note that this means that any
        value currently in self.response will be overwritten.
        
        Keyword Parameters:
            allowed_keys: keys that can be pressed to respond to the probe;
                defaults to O and N.
            begin_time: the time, in milliseconds, that must elapse before a
                response can be made; defaults to 0.
            finish_time: the number of milliseconds from probe onset that can
                elapse before the subject runs out of time to make a response.
                The default is None, in which case no time limit is imposed.
            c: pygame.time.Clock object; defaults to None, in which case one
                is created.
            fps: frames per second; defaults to 30.
            exit_keys: keys that cause the program to close if pressed;
                defaults to escape.
            files: any files that need to be closed if the program closes;
                defaults to an empty tuple.
        """
        self.response = self.get_keypress(
            response_keys = allowed_keys, start_time = begin_time,
            end_time = finish_time, ticker = c, frame_rate = fps,
            quit_keys = exit_keys, files = files
        )
    
    def rate(self, allowed_keys = NUMBERS, begin_time = 0, finish_time = None, c = None, fps = 30, exit_keys = (K_ESCAPE,), files = ()):
        """
        Present Image for a rating. As currently written, the function does
        not present a RatingScale object along with the Image object but,
        provided Image does not take up the entire screen, the scale could be
        displayed by the calling script. Nothing is returned, but self.rating
        is updated. Note that this means that any value currently in
        self.rating will be overwritten.
        
        Keyword Parameters:
            allowed_keys: keys that can be pressed to make a rating; defaults
                to all of the single-digit numbers, including 0.
            begin_time: the time, in milliseconds, that must elapse before a
                rating can be made; defaults to 0.
            finish_time: the number of milliseconds from Image onset that can
                elapse before the subject runs out of time to make a rating.
                The default is None, in which case no time limit is imposed.
            c: pygame.time.Clock object; defaults to None, in which case one
                is created.
            fps: frames per second; defaults to 30.
            exit_keys: keys that cause the program to close if pressed;
                defaults to escape.
            files: any files that need to be closed if the program closes;
                defaults to an empty tuple.
        """
        self.rating = self.get_keypress(
            response_keys = allowed_keys, start_time = begin_time,
            end_time = finish_time, ticker = c, frame_rate = fps,
            quit_keys = exit_keys, files = files
        )
    
    def create_copy(self):
        """
        Create and return a copy of Image.
        
        The returned copy can be modified without affecting the original: This
        is because mutable objects (like lists and dicts) are copied to the
        new Image using the copy.deepcopy() function.
        """
        new_file_name = self.file_name
        new_label = self.label
        new_background = copy.deepcopy(self.background)
        new_height = self.height
        new_width = self.width
        new_condition = copy.deepcopy(self.condition)
        new_x = self.x
        new_y = self.y
        new_response = self.response
        new_rating = self.rating
        new_image = Image(
            new_file_name, new_label, new_background, new_height, new_width,
            new_condition, new_x, new_y, new_response, new_rating
        )
        return new_image


def single_item_study_phase(stimuli, duration, isi, isi_fixation = "+", randomize = False, case = "", location = "middle centre", locations = None, top_margin = 0.025, right_margin = 0.025, bottom_margin = 0.025, left_margin = 0.025, font = None, fonts = None, use_antialiasing = True, stimulus_colour = None, stimulus_colours = None, background_colour = None, background_colours = None, isi_font = None, isi_antialiasing = True, isi_colour = None, isi_background = None, timer = None, fps = 30, keys_to_quit = (K_ESCAPE,), data_file = None, other_files = ()):
    """
    Present a single-item study phase.
    
    Parameters:
        stimuli: a filename with one stimulus per line; a list of strings,
            each element representing a stimulus; a list of Stimulus objects;
            or (unlikely, but will work) a list comprising both strings and
            Stimulus objects.
        duration: the presentation duration, in milliseconds, of each
            stimulus.
        isi: the duration, in milliseconds, of the interstimulus interval.
    
    Keyword Parameters:
        isi_fixation: stimulus that appears during the interstimulus interval;
            defaults to "+"; ignored if isi = 0.
        randomize: Boolean indicating whether stimuli are shuffled before the
            study phase; if False, stimuli are presented in the same order as
            the stimuli list or in the same order as contained in the stimuli
            file; defaults to False. When True, if fonts, stimulus_colours,
            background_colours, and/or locations are set, these, too, are
            shuffled.
        case: "u", "l", or an empty string; only applies if stimuli are
            strings or read from a file; all are set to uppercase if case is
            "u"; all are set to lowercase if case is "l"; all are left as is
            if case is left as an empty string.
        location: Set this parameter if all stimuli appear in the same
            location on the screen; must either be a list or tuple of the x-y
            coordinates or a string from the SCREEN_POSITIONS constant;
            defaults to "middle centre". Note that, if stimuli are Stimulus
            objects, this variable is ignored, with screen locations pulled
            from the Stimulus.x and Stimulus.y attributes.
        locations: Set this parameter if stimuli appear in different
            locations; Each element in locations must be either a list/tuple
            of x-y coordinates or strings from the SCREEN_POSITIONS constant;
            defaults to None. locations is ignored if stimuli contains
            Stimulus objects.
        top_margin, right_margin, bottom_margin, and left_margin: only apply
            if location is a string or locations contains strings; refers to
            the proportion of the screen to remove when determining, for
            example, where the top left is; default to 0.025.
        font: a pygame.font.Font object to use if all stimuli are rendered in
            the same font; ignored if stimuli are Stimulus objects.
        fonts: list or tuple of fonts to use in rendering stimuli; defaults to
            None, and only applies if stimuli are not Stimulus objects. Fonts
            will be assigned to stimuli in the same order (i.e., the ith font
            in fonts will go to the ith stimulus in stimuli).
        use_antialiasing: Boolean indicating whether antialiasing is used;
            ignored if stimuli are already Stimulus objects.
        stimulus_colour: RGB list or tuple for the colour of stimuli; ignored
            if stimuli are Stimulus objects but otherwise must be set.
            stimulus_colour should only be set if all stimuli are presented in
            the same colour.
        stimulus_colours: a list or tuple of RGB lists or tuples; defaults to
            None, and only applies if stimuli are not Stimulus objects. Use
            this parameter when stimuli are presented in different colours.
            This works like the fonts and locations parameters.
        background_colour and background_colours: analogous to stimulus_colour
            and stimulus_colours.
        isi_font, isi_antialiasing, isi_colour, and isi_background: same
            meaning as f, use_antialiasing, stimulus_colour, and
            background_colour, respectively, but apply to the interstimulus
            interval; if not set and needed, they are set first from f,
            use_antialiasing, stimulus_colour, and background_colour and, if
            these also are not set, they are set from one of the Stimulus
            objects in stimuli.
        timer: pygame.time.Clock object; created if none is passed.
        fps: frame refreshes per second; defaults to 30.
        keys_to_quit: keypresses that cause the program to close; defaults to
            the escape key.
        data_file: an optional file to which to write the study list. The
            argument passed to this parameter can be a file opened for
            writing, a string pointing to an extant file, or a string
            containing the path and name of a to-be-created file.. In the case
            of an already opened file, the study list is written wherever the
            file is set to write. In the case of a string pointing to an
            extant file, the study list is written to the file's end. Finally,
            in the case of a not-yet-created file, the file is created and the
            data written.
        other_files: files to close if a key from quit_keys is pressed;
            may include data_file if opened, but this is not a necessary
            condition.
    """
    assert duration > 0, "duration must be positive."
    assert fps > 0, "fps must be positive."
    
    try:
        with open(stimuli) as file_object:
            stimuli = file_object.readlines()
            stimuli = [stimulus.strip() for stimulus in stimuli]
    except TypeError:
        pass
    
    if randomize:
        np.random.shuffle(stimuli)
        if fonts:
            np.random.shuffle(fonts)
        if stimulus_colours:
            np.random.shuffle(stimulus_colours)
        if background_colours:
            np.random.shuffle(background_colours)
        if locations:
            np.random.shuffle(locations)
    
    # Convert non-Stimulus objects to Stimulus objects:
    for i in xrange(len(stimuli)):
        current_stim = stimuli[i]
        if not isinstance(current_stim, Stimulus):
            if fonts:
                current_font = fonts[i]
            elif i == 0:
                current_font = font
            if stimulus_colours:
                current_colour = stimulus_colours[i]
            elif i == 0:
                current_colour = stimulus_colour
            if background_colours:
                current_background = background_colours[i]
            elif i == 0:
                current_background = background_colour
            if case == "u" and not current_stim.isupper():
                current_stim = current_stim.upper()
            elif case == "l" and not current_stim.islower():
                current_stim = current_stim.lower()
            if locations:
                current_location = locations[i]
                # current_location should either be a list or string.
                try:
                    pixel_x, pixel_y = current_location
                except ValueError:
                    pixel_x, pixel_y = get_position(
                        current_location, current_stim, current_font,
                        top_margin, right_margin, bottom_margin, left_margin
                    )
            elif i == 0:
                current_location = location
                try:
                    pixel_x, pixel_y = current_location
                except ValueError:
                    pixel_x, pixel_y = get_position(
                        current_location, current_stim, current_font,
                        top_margin, right_margin, bottom_margin, left_margin
                    )
            new_stim = Stimulus(
                current_stim, current_font, colour = current_colour,
                background = current_background,
                antialiasing = use_antialiasing, x = pixel_x, y = pixel_y
            )
            stimuli[i] = new_stim
    
    if isi and not isi_background:
        if background_colour:
            isi_background = background_colour
        elif background_colours:
            isi_background = background_colours[0]
        else:
            isi_background = stimuli[0].background
    if isi and isi_fixation:
        if not isi_font:
            if font:
                isi_font = font
            elif fonts:
                isi_font = fonts[0]
            else:
                isi_font = stimuli[0].font
        if not isi_colour:
            if stimulus_colour:
                isi_colour = stimulus_colour
            elif stimulus_colours:
                isi_colour = stimulus_colours[0]
            else:
                isi_colour = stimuli[0].colour
        if isi_antialiasing == None:   # unlikely
            isi_antialiasing = use_antialiasing
    
    # Present the study phase:
    for stim in stimuli:
        stim.study(
            duration, ticker = timer, frame_rate = fps,
            quit_keys = keys_to_quit, files = other_files
        )
        if isi:
            interstimulus_interval(
                isi, fixation = isi_fixation, font = isi_font,
                fixation_colour = isi_colour,
                background_colour = isi_background,
                antialiasing = isi_antialiasing, ticker = timer,
                frame_rate = fps, quit_keys = keys_to_quit,
                files = other_files
            )
    
    # Write to data_file, if necessary:
    if data_file:
        writing.study_phase(stimuli, data_file)
    return


def free_recall_test(f, line_size = None, antialias = True, text_colour = WHITE, background_colour = BLACK, prompt = "Enter words you remember from the study phase. When you can't remember more words, enter q.", verification = "Are you finished? Press y for yes and n for no.", finished_string = "q", trim_width = 0.05, trim_height = 0.05, allowed_keys = LETTERS, time_limit = None, time_up_message = "Time up.", time_up_message_duration = 2000, show_previous_input = False, ticker = None, frame_rate = 30, quit_keys = (K_ESCAPE,), data_file = None, close_data_file = True, other_files = ()):
    """
    Administer a free-recall test.
    
    Parameters:
        f: pygame.font.Font object.
    
    Keyword Parameters:
        line_size: the number of pixels between lines of text; defaults to
            None, in which case it is obtained from f.
        antialias: Boolean indicating whether antialiasing is used with text
            rendering; defaults to True.
        text_colour: RGB for the text colour; defaults to white.
        background_colour: RGB for the background; defaults to black.
        prompt: instructions that appear at the top of the screen prompting
            the subject to type responses; defaults to "Enter words you
            remember from the study phase. When you can't remember more words,
            enter q."; definitely should be changed if finished_string is
            changed from "q".
        verification: message that appears when subjects give up; defaults to
            "Are you finished? Press y for yes and n for no."
        finished_string: string that triggers the test phase to end; defaults
            to "q".
        trim_width and trim_height: the proportion of the screen's width and
            height to always leave blank; default to 0.05.
        allowed_keys: the keys allowed for input; defaults to LETTERS.
       time_limit: total time, in milliseconds, allowed  for recall; defaults
            to None, in which case no time limit is placed.
        time_up_message: appears if the subject runs out of time; defaults to
            "Time up."
        time_up_message_duration: milliseconds for which time_up_message
            appears; defaults to 2000.
        show_previous_input: Boolean indicating whether previously input
            responses remain visible after being input; defaults to False.
        ticker: pygame.time.Clock object; created if none is passed.
        frame_rate: frames per second; defaults to 30.
        quit_keys: keys that exit the program; defaults to escape.
        data_file: an optional file to which to write the subject's output
            protocol. The argument passed to this parameter can be a file
            opened for writing, a string pointing to an extant file, or a
            string containing the path and name of a to-be-created file. In
            the case of an already opened file, the protocol is written
            wherever the file is set to write. In the case of a string
            pointing to an extant file, the protocol is written to the file's
            end. Finally, in the case of a not-yet-created file, the file is
            created and the protocol written.
        close_data_file: Boolean indicating whether data_file is closed after
            being written to; defaults to True, but has no effect if data_file
            is None.
        other_files: files to close if a key from quit_keys is pressed; may
            include data_file if opened, but this is not a necessary
            condition.
        NB: Any of the message variables can be disabled by passing an empty
            string for its value.
    
    Returns:
        protocol: the subject's responses in the order entered.
    """
    assert 0 <= trim_width < 1 and 0 <= trim_height < 1, "trim_width and \
trim_height must be proportions."
    assert not any(k in allowed_keys for k in (K_RETURN, K_BACKSPACE)), \
"Neither return nor backspace may appear in allowed_keys."
    assert not any(k in quit_keys for k in (K_RETURN, K_BACKSPACE)), \
"Neither return nor backspace may appear in quit_keys."
    assert not any(k in allowed_keys for k in quit_keys), "There may not be \
overlap between allowed_keys and quit_keys."
    assert frame_rate > 0, "frame_rate must be positive."
    
    screen = pygame.display.get_surface()
    try:
        screen_width, screen_height = screen.get_size()
    except AttributeError:
        screen = pygame.display.set_mode(pygame.display.list_modes()[0])
        screen_width, screen_height = screen.get_size()
    screen.fill(background_colour)
    pixel_columns = int(screen_width-trim_width*screen_width)
    pixel_rows = int(screen_height-trim_height*screen_height)
    top_margin = int(trim_height/2*screen_height)
    left_margin = int(trim_width/2*screen_width)
    bottom_margin = screen_height-top_margin
    right_margin = screen_width-left_margin
    if not line_size:
        line_size = f.get_linesize()
    if prompt:
        prompt_surface, prompt_rect = text.string_to_surface_and_rect(
            prompt, f, text_colour, background_colour, pixel_columns,
            pixel_rows, line_size = line_size, antialiasing = antialias
        )
        prompt_surface = prompt_surface[0]
        prompt_rect = prompt_rect[0]
        prompt_rect.center = (
            pixel_columns//2+left_margin, pixel_rows//2+top_margin
        )
        if show_previous_input:
            # prompt should appear at the top of the screen to leave room for
            # responses to accumulate.
            prompt_rect.top = top_margin
        else:
            # Since room isn't needed for numerous typed responses, prompt can
            # appear a third of the way down.
            prompt_rect.top = top_margin+pixel_rows//3
    if verification:
        verification_surface, verification_rect = text.string_to_surface_and_rect(
            verification, f, text_colour, background_colour, pixel_columns,
            pixel_rows, line_size = line_size, antialiasing = antialias
        )
        verification_surface = verification_surface[0]
        verification_rect = verification_rect[0]
        verification_rect.center = (
            pixel_columns//2+left_margin, pixel_rows//2+top_margin
        )
    if time_limit and time_up_message and time_up_message_duration:
        time_up_surface, time_up_rect = text.string_to_surface_and_rect(
            time_up_message, f, text_colour, background_colour, pixel_columns,
            pixel_rows, line_size = line_size, antialiasing = antialias
        )
        time_up_surface = time_up_surface[0]
        time_up_rect = time_up_rect[0]
        time_up_rect.center = (
            pixel_columns//2+left_margin, pixel_rows//2+top_margin
        )
    
    # Get the coordinate at which responses are located (depends on
    # show_previous_input):
    if show_previous_input:
        try:
            response_position = (left_margin, prompt_rect.bottom+line_size)
        except NameError:
            response_position = (left_margin, top_margin)
    else:
        try:
            response_position = (
                pixel_columns//2+left_margin, prompt_rect.bottom+line_size
            )
        except NameError:
            response_position = (
                screen_width//2+left_margin, pixel_rows//2+top_margin
            )
    
    if show_previous_input:
        # Each time a new response is added to the screen, it is necessary to
        # ascertain that there will be room for another. If there will not be,
        # earliest-input words are removed from view until room is made.
        # Get the room available for responses:
        try:
            space_for_responses = pixel_rows-prompt_rect.height-line_size
        except NameError:
            space_for_responses = pixel_rows
        # Get the height of the tallest possible line:
        max_line_height = tallest_letter(f)
        assert max_line_size <= space_for_responses, "There isn't enough \
room for responses to appear. Try shortening the prompt message or \
decreasing the font size."
    
    protocol = []
    response = ""
    if time_limit:
        pygame.time.set_timer(TIME_UP, time_limit)
    if prompt:
        screen.blit(prompt_surface, prompt_rect)
    pygame.display.update()
    keep_testing = True
    while keep_testing:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key in quit_keys):
                generic.terminate(other_files)
            elif event.type == TIME_UP:
                pygame.time.set_timer(TIME_UP, 0)
                screen.fill(background_colour)
                if time_up_message and time_up_message_duration > 0:
                    screen.blit(time_up_surface, time_up_rect)
                    pygame.time.set_timer(TIME_UP, time_up_message_duration)
                    end_loop = False
                    while not end_loop:
                        for subevent in pygame.event.get():
                            if subevent.type == QUIT or (subevent.type == KEYUP and subevent.key in quit_keys):
                                generic.terminate(other_files)
                            elif subevent.type == TIME_UP:
                                pygame.time.set_timer(TIME_UP, 0)
                                end_loop = True
                            else:
                                pass
                        try:
                            ticker.tick(frame_rate)
                        except AttributeError:
                            ticker = pygame.time.Clock()
                            ticker.tick(frame_rate)
                keep_testing = False
            elif event.type == KEYUP and event.key == K_BACKSPACE and response:
                response = response[:len(response)-1]
                update_rect = response_rect
                response_surface, response_rect = text.render_string(
                    response, f, text_colour, background_colour, antialias
                )
                if show_previous_input:
                    response_rect.topleft = response_position
                else:
                    response_rect.center = response_position
                screen.fill(background_colour, update_rect)
                screen.blit(response_surface, response_rect)
                pygame.display.update(response_rect)
            elif event.type == KEYUP and event.key == K_RETURN and response:
                # The subject has input the response.
                if response == finished_string:
                    original_surface = screen.copy()
                    screen.fill(background_colour)
                    screen.blit(verification_surface, verification_rect)
                    pygame.display.update()
                    finished_verifying = False
                    while not finished_verifying:
                        for subevent in pygame.event.get():
                            if subevent.type == QUIT or (subevent.type == KEYUP and subevent.key in quit_keys):
                                generic.terminate(other_files)
                            elif subevent.type == TIME_UP:
                                finished_verifying = True
                                pygame.time.set_timer(TIME_UP, 0)
                                screen.fill(background_colour)
                                if time_up_message and time_up_message_duration > 0:
                                    screen.blit(time_up_surface, time_up_rect)
                                    pygame.time.set_timer(
                                        TIME_UP, time_up_message_duration
                                    )
                                    end_loop = False
                                    while not end_loop:
                                        for subsubevent in pygame.event.get():
                                            if subsubevent.type == QUIT or (subsubevent.type == KEYUP and subsubevent.key in quit_keys):
                                                generic.terminate(other_files)
                                            elif subsubevent.type == TIME_UP:
                                                pygame.time.set_timer(
                                                    TIME_UP, 0
                                                )
                                                end_loop = True
                                            else:
                                                pass
                                        try:
                                            ticker.tick(frame_rate)
                                        except AttributeError:
                                            ticker = pygame.time.Clock()
                                            ticker.tick(frame_rate)
                                keep_testing = False
                            elif subevent.type == KEYUP and subevent.key == K_y:
                                finished_verifying = True
                                keep_testing = False
                            elif subevent.type == KEYUP and subevent.key == K_n:
                                finished_verifying = True
                                response = ""
                                screen.blit(
                                    original_surface,
                                    (left_margin, top_margin, pixel_columns, pixel_rows)
                                )
                                screen.fill(background_colour, response_rect)
                                pygame.display.update()
                            else:
                                pass
                        try:
                            ticker.tick(frame_rate)
                        except AttributeError:
                            ticker = pygame.time.Clock()
                            ticker.tick(frame_rate)
                else:
                    # response is not finished_string.
                    protocol.append(response)
                    response = ""
                    if show_previous_input:
                        on_screen.append(protocol[-1])
                        # There needs to be room for another response or the
                        # earliest responses move off the screen.
                        responses_height = text.height_of_strings(
                            on_screen, f, line_size
                        )
                        if space_for_responses-responses-height-line_size < max_line_size:
                            while space_for_responses-responses-height-line_size < max_line_size:
                                del on_screen[0]
                                responses_height = text.height_of_strings(
                                    on_screen, f, line_size
                                )
                                new_surface, new_rect = text.render_lines(
                                    on_screen, f, text_colour, background_colour,
                                    line_size = line_size,
                                    use_antialias = antialias
                                )
                                try:
                                    new_rect.topleft = (
                                        prompt_rect.left,
                                        prompt_rect.bottom+line_size
                                    )
                                except NameError:
                                    new_rect.topleft = (left_margin, top_margin)
                                screen.blit(new_surface, new_rect)
                                try:
                                    response_position = (prompt_rect.left, top_margin+prompt_rect.height+line_size+responses_height)
                                except NameError:
                                    response_position = (left_margin, top_margin+responses_height+line_size)
                                pygame.display.update()
                        else:
                            # There is room for this response.
                            response_surface, response_rect = text.render_string(
                                protocol[-1], f, text_colour,
                                background_colour, antialias
                            )
                            response_rect.topleft = response_position
                            response_position[1] = response_rect.bottom+line_size
                            screen.blit(response_surface, response_rect)
                            pygame.display.update(response_rect)
                    else:
                        # Previous responses are not shown.
                        screen.fill(background_colour, response_rect)
                        pygame.display.update(response_rect)
            elif event.type == KEYUP and event.key in allowed_keys:
                # Another letter has been added to response.
                response = response+pygame.key.name(event.key)
                response_surface, response_rect = text.render_string(
                    response, f, text_colour, background_colour, antialias
                )
                if show_previous_input:
                    response_rect.topleft = response_position
                else:
                    response_rect.center = response_position
                screen.fill(background_colour, response_rect)
                screen.blit(response_surface, response_rect)
                pygame.display.update(response_rect)
        try:
            ticker.tick(frame_rate)
        except AttributeError:
            ticker = pygame.time.Clock()
            ticker.tick(frame_rate)
    
    # Write protocol, if necessary:
    if data_file:
        data_file = writing.ready_file_for_writing(data_file)
        data_file.write("output_position,response\n")
        for i in xrange(len(protocol)):
            data_file.write("{:d},{:s}\n".format(i+1, protocol[i]))
        if close_data_file:
            data_file.close()
    return protocol


def free_recall(targets, stim_duration, isi_duration, study_instructions, test_instructions, top_margin = 0.025, right_margin = 0.025, bottom_margin = 0.025, left_margin = 0.025, response_keys = LETTERS, randomize = True, blocks = 1, balance_conditions = True, targets_per_block = (), recall_prompt = "Enter words you remember from the study phase. When you can't remember more words, enter q.", recall_verification = "Are you finished? Press y for yes and n for no.", finished_string = "q", time_for_recall = None, time_up_message = "Time up.", time_up_message_duration = 2000, previous_responses_stay_on_screen = False, antialiasing = True, stim_case = "", stim_font = None, stim_fonts = None, stim_colour = WHITE, stim_colours = None, stim_background = BLACK, stim_backgrounds = None, stim_location = "middle centre", stim_locations = None, conditions = None, preliminary_instructions = (), distraction_instructions = None, instruction_font = None, instruction_colour = WHITE, instruction_background = BLACK, instruction_line_size = None, lines_between_instructions_and_continue_message = 2, continue_instruction_message = "Press the space bar to continue.", continue_instruction_font = None, continue_instruction_line_size = None, continue_keys = (K_SPACE,), backward_keys = (), split_sentences_between_screens = False, sentence_terminators = SENTENCE_TERMINATORS, sentence_terminator_exclusions = (), isi_string = "+", isi_font = None, isi_colour = WHITE, isi_background = BLACK, isi_position = "middle centre", distractor = True, distraction_duration = 120000, tetromino_sound_file = None, clock = None, frame_rate = 30, exit_keys = (K_ESCAPE,), study_file = None, study_files = None, distractor_file = None, distractor_files = None, protocol_file = None, protocol_files = None, intrusion_file = None, intrusion_files = None, close_matches_file = None, close_matches_files = None, results_file = None, results_files = None, other_files = ()):
    """
    Administer a free-recall experiment (study, distractor task [if desired],
    and test). Results are returned in a dict (see below for more details).
    
    Parameters:
        targets: the study items for the free-recall test. This parameter can
            be a file with one target per line, a list of strings, or a list
            of Stimulus objects.
        stim_duration: the time, in milliseconds, for which each target is
            displayed during study.
        isi_duration: the time, in milliseconds, that the interstimulus
            interval (ISI) lasts. To disable the ISI, set this to 0.
        study_instructions: instructions that appear before the study phase.
        test_instructions: instructions that appear before the test phase.
    
        Keyword Parameters:
        top_margin, right_margin, bottom_margin, and left_margin: the
            proportion of the part of the screen excluded when positioning
            stimuli and instructions. Nothing from this function will touch
            the proportion of the screen declared by the margin variables.
        response_keys: the keys that can be pressed during recall; defaults to
            all the letters.
        randomize: Boolean indicating whether targets are randomized before
            presentation; defaults to True. If randomize is True and
            stim_fonts, stim_colours, and/or stim_backgrounds are set, these
            are also randomized before assignment to stimuli.
        blocks: the number of study-test/study-distraction-test blocks.
        balance_conditions: defaults to True, but only applies if randomize is
            True and there is more than one block. When True, this ensures
            that an equal number of targets from each condition appear in each
            block. If this is impossible, an error is raised. When False,
            targets are assigned to blocks without regard to condition.
        targets_per_block: list/tuple equal in length to blocks with the
            number of targets to appear in each block. This parameter can also
            be an empty tuple (its default value), in which case blocks have
            the same number of targets. If even distribution of targets is
            impossible and targets_per_block is empty, an error is raised.
        recall_prompt: the message that appears during recall (i.e., it is on
            the screen while subjects type responses). Set this to an empty
            string to disable it. The default string is "Enter words you
            remember from the study phase. When you can't remember more words,
            enter q.".
        recall_verification: appears when subjects indicate they are finished
            recalling items; defaults to "Are you finished? Press y for yes
            and n for no.". To disable this message appearing, set it to an
            empty string.
        finished_string: what subjects have to type when they are finished recalling information; defaults to "q".
        time_for_recall: the time, in milliseconds, allowed for recall.
            time_for_recall defaults to None, in which case no time limit is
            imposed.
        time_up_message: the message that appears when the subject runs out of
            time; defaults to "Time up."
        time_up_message_duration: the number of milliseconds that
            time_up_message stays on screen.
        previous_responses_stay_on_screen: Boolean indicating whether
            responses stay on the screen after they are input. This defaults
            to False, in which case typed responses disappear.
        antialiasing: Boolean indicating whether antialiasing is used in text
            rendering.
        stim_case: indicates whether targets are presented in all uppercase
            letters, all lowercase letters, or whether case is left as is.
            stim_case defaults to an empty string, which tells the function to
            do nothing. For all uppercase, set stim_case to "u", and for all
            lowercase, set stim_case to "l".
        stim_font and stim_fonts: pygame.font.Font object or list of
            pygame.font.Font objects used for rendering targets; default to
            None. Set stim_font if you want all stimuli to be presented in the
            same font. If multiple fonts are desired, use the stim_fonts
            parameter. Note that, if stimuli is a list of Stimulus objects,
            stim_font and stim_fonts are ignored, with the font type drawn
            from the Stimulus.font attribute.
        stim_colour and stim_colours: an RGB list/tuple or a list of RGB
            list/tuples for rendering the targets; default to None. These
            parameters work the same way as stim_font and stim_fonts.
        stim_background and stim_backgrounds: same as stim_colour and
            stim_colours but applies to the screen on which targets are
            presented.
        stim_location and stim_locations: an x-y pixel coordinate or string
            from the SCREEN_POSITIONS constant (or lists of these). Stimuli
            are centred at the x-y coordinates. stim_location defaults to
            "middle centre" and stim_locations defaults to None. These operate
            in the same manner as stim_font(s), stim_colour(s), and
            stim_background(s).
        conditions: defaults to None, in which case target condition is
            ignored. The purpose of this parameter is to obtain clearer data.
            If this parameter is set, the returned dict contains keys
            corresponding to each condition (i.e., performance is broken down
            by condition). If condition is a list or tuple, its length should
            correspond to the number of targets.
        preliminary_instructions: an optional set of instructions to appear
            before study_instructions (defaults to an empty tuple). This
            parameter can be a string or a list of strings. In the latter
            case, screen breaks occur following each element. Note that, even
            for strings, if the content will not fit on a single screen, there
            will be a screen break.
        distraction_instructions: instructions for the distraction phase, if
            applicable.
        instruction_font: pygame.font.Font to use for instructions; defaults
            to None, in which stim_font (or stim_font[0]) is used.
        instruction_colour and instruction_background: RGB lists/tuples for
            instructions.
        instruction_line_size: the number of pixel rows between the bottom of
            one line of text and the top of the next; defaults to None, in
            which case it is obtained from instruction_font.
        lines_between_instructions_and_continue_message: the number of lines
            to leave between the bottom of instructions on a screen and the
            top of the prompt to continue to the next; defaults to 2.
        continue_instruction_message: defaults to "Press the space bar to
            continue."; this is the message that appears when instructions
            fail to fit on a single screen.
        continue_instruction_font: pygame.font.Font object for
            continue_instruction_message; instruction_font is used if left as
            None.
    continue_instruction_line_size: same as instruction_line_size but for
            continue_instruction_message.
        continue_keys: list or tuple of keys to press to advance passed
            instructions; defaults to the space bar.
        backward_keys: list or tuple of keys that can be used to move backward
            through instructions. This only works when a given instruction
            string extends over multiple screens (i.e., subjects cannot move
            backward beyond the start of the currently presented instruction
            string). This parameter defaults to an empty tuple, in which case
            backward movement is disabled.
        split_sentences_between_screens: Boolean indicating whether it is okay
            to split sentences between screens for situations in which a
            string intended for one screen will not fit. If set to False,
            sentences may still be divided across screens if a sentence is too
            long to fit on one.
        sentence_terminators: characters that end a sentence; only applicable
            if split_sentences_between_screens is False; defaults to period,
            exclamation mark, and question mark.
        sentence_terminator_exclusions: only applies if
            split_sentences_between_screens is False; any strings that should
            be excluded from the sentence_terminators list. If, for example,
            your instructions refer to "Dr. Smith", it would be necessary to
            pass a list containing "Mr." to this parameter to ensure the
            function does not think "Mr." and "Smith" are part of separate
            sentences.
        isi_string: the character(s) to appear during the ISI; defaults to
            "+". For the ISI to show an empty screen, pass an empty string for
            isi_string.
        isi_font: pygame.font.Font object for isi_string rendering; defaults
            to None. If this parameter is left as None, the font from the
            first target in targets is used.
        isi_colour and isi_background: RGB lists/tuples for isi_string and its
            background.
        isi_location: the position of isi_string on the screen; defaults to
            "middle centre". This parameter must be x-y pixel coordinates or a
            string from the SCREEN_POSITIONS constant.
        distractor: Boolean indicating whether a distractor task is
            interpolated between study and test. Currently, only Tetromino (a
            Tetris clone) is supported. distractor defaults to True.
        distraction_duration: the duration, in milliseconds, of the distractor
            task; defaults to 120000.
        tetromino_sound_file: a sound file to play while tetromino runs;
            defaults to None, in which no sound is used.
        clock: a pygame.time.Clock object; defaults to None and is created if
            one is not passed.
        frame_rate: the frames per second; defaults to 30.
        exit_keys: keys that can be pressed to close the program.
        study_file: a file to which to write each study phase; defaults to
            None. If one is passed, the order of word presentation is written
            for each block.
        study_files: a list of files for writing study lists; defaults to
            None. If an argument is passed for this parameter, the list must
            be equal in length to blocks.
        distractor_file and distractor_files: same as study_file and
            study_files, but performance on the distractor task is written.
            For Tetromino, the number of lines completed and the number of
            losses (i.e., the number of times the blocks reached the top of
            the game board) are recorded.
        protocol_file and protocol_files: same as above, but response
            protocols are recorded.
        intrusion_file and intrusion_files: same as previous files, but
            records intrusions.
        close_matches_file and close_matches_files: same as above, but records
            close matches.
        result_file and results_files: records all information in a single
            file (i.e., result_file puts all blocks and overall in a single
            file, and result_files puts each block in a separate file).
        other_files: any currently open files that need to be closed if the
            program is terminated.
    
    Returns:
        results: a list of blocks+1 dictionaries, with the ith dictionary
            corresponding to the ith block and the final dictionary
            corresponding to overall performance. Dictionaries have the
            following keys:
                "condition": unless conditions were specified, this key is simply "condition". Otherwise, there is a separate key for each of the keys in targets. The entry for this key is itself a dictionary with the following entries:
                    "raw recall": the total number of targets recalled.
                    "proportion recall": the proportion of targets recalled.
                    "close matches": a list of responses that are close to
                        matching a target from the condition. Be careful with
                        this entry, as a response can conceivably appear in
                        more than one condition.
                "items recalled": the specific items recalled in the order in
                        which they were recalled.
                "overall": same as "condition", but conditions are ignored. If
                    no conditions were specified, this key is the same as
                "condition".
                "intrusions": a list of responses that neither match nor
                    closely match any targets.
                "distractor": This entry only appears if distractor is True.
                    It is a dictionary with entries for "lines" and "losses".
    """
    recall_responses = []
    results = []
    if distractor:
        lines = []
        losses = []
    if not instruction_font:
        try:
            instruction_font = stim_fonts[0]
        except TypeError:
            if stim_font:
                instruction_font = stim_font
            else:
                # Get instruction_font from a Stimulus object:
                instruction_font = targets[0].font
    if not instruction_line_size:
        instruction_line_size = instruction_font.get_linesize()
    
    if randomize:
        if stim_fonts:
            np.random.shuffle(stim_fonts)
        if stim_colours:
            np.random.shuffle(stim_colours)
        if stim_backgrounds:
            np.random.shuffle(stim_backgrounds)
        if stim_locations:
            np.random.shuffle(stim_locations)
    
    # Create a list of Stimulus objects for targets if one does not already
    # exist:
    try:
        # targets might be a file.
        with open(targets) as target_file:
            targets = target_file.readlines()
        targets = [target.strip() for target in targets]
    except TypeError:
        # targets is not a file.
        pass
    
    # Convert any non-Stimulus objects from targets to Stimulus objects:
    for i in xrange(len(targets)):
        target = targets[i]
        if not isinstance(target, Stimulus):
            if stim_fonts:
                target_font = targets[i]
            elif i == 0:
                target_font = stim_font
            if stim_colours:
                target_colour = stim_colours[i]
            elif i == 0:
                target_colour = stim_colour
            if stim_backgrounds:
                target_background = stim_backgrounds[i]
            elif i == 0:
                target_background = stim_background
            if stim_case == "u" and not target.isupper():
                target = target.upper()
            elif stim_case == "l" and not target.islower():
                target = target.lower()
            if stim_locations:
                target_location = stim_location
                try:
                    pixel_x, pixel_y = target_location
                except ValueError:
                    pixel_x, pixel_y = get_position(
                        target_location, target, target_font, top_margin,
                        right_margin, bottom_margin, left_margin
                    )
            elif (i == 0 and not stim_fonts) or stim_fonts:
                target_location = stim_location
                try:
                    pixel_x, pixel_y = target_location
                except ValueError:
                    pixel_x, pixel_y = get_position(
                        target_location, target, target_font, top_margin,
                        right_margin, bottom_margin, left_margin
                    )
            new_target = Stimulus(
                target, target_font, colour = target_colour,
                background = target_background,
                antialiasing = antialiasing, x = pixel_x, y = pixel_y
            )
            targets[i] = new_target
    
    # ISI cleanup, if necessary:
    if isi_duration > 0 and isi_string and not isi_font:
        isi_font = targets[0].font
    
    # Next, lists are created according to the randomize, blocks,
    # balance_conditions, and targets_per_block parameters.
    if randomize:
        np.random.shuffle(targets)
    study_lists = []
    if blocks == 1:
        study_lists.append(targets)
    else:
        if not balance_conditions:
            if targets_per_block:
                assert sum(targets_per_block) == len(targets), "Values in \
targets_per_block must sum to the length of targets."
                target_count = 0
                for list_length in targets_per_block:
                    current_study_list = []
                    for i in xrange(list_length):
                        current_study_list.append(targets[target_count])
                        target_count = target_count+1
                    study_lists.append(current_study_list)
            else:
                assert len(targets)%blocks == 0, "The length of targets does \
not evenly divide into the specified number of blocks."
                list_length = len(targets)//blocks
                target_count = 0
                for i in xrange(blocks):
                    current_study_list = []
                    for j in xrange(list_length):
                        current_study_list.append(targets[j])
                    study_lists.append(current_study_list)
        else:
            # Conditions need to be balanced.
            # Get a dict of conditions with the number of time each occurs in
            # targets:
            conditions = {}
            for target in targets:
                current_condition = target.condition
                if isinstance(current_condition, list):
                    current_condition = tuple(current_condition)
                    # necessary because dicts do not allow list keys.
                if current_condition not in conditions:
                    conditions[current_condition] = 1
                else:
                    conditions[current_condition] = conditions[current_condition]+1
            if not targets_per_block:
                # Make sure balancing conditions is possible:
                for key in conditions:
                    assert conditions[key]%blocks == 0, "The number of \
targets in each condition must evenly divide by the number of blocks."
                # targets are deleted below, so create a copy:
                targets_copy = copy_stimuli(targets)
                for i in xrange(blocks):
                    current_study_list = []
                    for key in conditions:
                        to_delete_indices = []
                        for j in xrange(len(targets_copy)):
                            target = targets_copy[j]
                            current_condition = target.condition
                            if isinstance(current_condition, list):
                                current_condition = tuple(current_condition)
                            if current_condition == key:
                                current_study_list.append(target)
                                to_delete_indices.append(j)
                                if len(to_delete_indices) == conditions[key]//blocks:
                                    break
                        for k in xrange(len(to_delete_indices)-1, -1, -1):
                            index = to_delete_indices[k]
                            del targets_copy[index]
                    study_lists.append(current_study_list)
            else:
                for list_length in targets_per_block:
                    assert list_length%len(conditions) == 0, "List lengths \
in targets_per_block must evenly divide by the number of conditions."
                    current_study_list = []
                    for key in conditions:
                        to_delete_indices = []
                        for j in xrange(len(targets_copy)):
                            target = targets_copy[j]
                            current_condition = target.condition
                            if isinstance(current_condition, list):
                                current_condition = tuple(current_condition)
                            if current_condition == key:
                                current_study_list.append(target)
                                to_delete_indices.append(j)
                                if len(to_delete_indices) == list_length%conditions:
                                    break
                        for k in xrange(len(to_delete_indices)-1, -1, -1):
                            index = to_delete_indices[k]
                            del targets_copy[index]
                    study_lists.append(current_study_list)
    
    # Present preliminary_instructions (if applicable):
    for instructions in preliminary_instructions:
        text.display_text_until_keypress(
            instructions, instruction_font, instruction_colour,
            instruction_background,
            proportion_width = 1-left_margin-right_margin,
            proportion_height = 1-top_margin-bottom_margin,
            main_line = instruction_line_size,
            break_sentences = split_sentences_between_screens,
            sentence_terminators = sentence_terminators,
            terminator_exceptions = sentence_terminator_exclusions,
            gap = lines_between_instructions_and_continue_message,
            bottom_message = continue_instruction_message,
            bottom_font = continue_instruction_font,
            bottom_line = continue_instruction_line_size,
            advance_keys = continue_keys, reverse_keys = backward_keys,
            quit_keys = exit_keys, ticker = clock, frame_rate = frame_rate,
            files = other_files
        )
    
    for study_list in study_lists:
        # Show study_instructions:
        text.display_text_until_keypress(
            study_instructions, instruction_font, instruction_colour,
            instruction_background,
            proportion_width = 1-left_margin-right_margin,
            proportion_height = 1-top_margin-bottom_margin,
            main_line = instruction_line_size,
            break_sentences = split_sentences_between_screens,
            sentence_terminators = sentence_terminators,
            terminator_exceptions = sentence_terminator_exclusions,
            gap = lines_between_instructions_and_continue_message,
            bottom_message = continue_instruction_message,
            bottom_font = continue_instruction_font,
            bottom_line = instruction_line_size, advance_keys = continue_keys,
            reverse_keys = backward_keys, quit_keys = exit_keys,
            ticker = clock, frame_rate = frame_rate, files = other_files
        )
        # Now the study phase itself:
        single_item_study_phase(
            study_list, stim_duration, isi_duration,
            isi_fixation = isi_string, case = stim_case,
            use_antialiasing = antialiasing, isi_font = isi_font,
            isi_antialiasing = antialiasing, isi_colour = isi_colour,
            isi_background = isi_background, timer = clock, fps = frame_rate,
            keys_to_quit = exit_keys, other_files = other_files
        )
        if distractor:
            text.display_text_until_keypress(
                distraction_instructions, instruction_font,
                instruction_colour, instruction_background,
                proportion_width = 1-left_margin-right_margin,
                proportion_height = 1-top_margin-bottom_margin,
                main_line = instruction_line_size,
                break_sentences = split_sentences_between_screens,
                sentence_terminators = sentence_terminators,
                terminator_exceptions = sentence_terminator_exclusions,
                gap = lines_between_instructions_and_continue_message,
                bottom_message = continue_instruction_message,
                bottom_font = continue_instruction_font,
                bottom_line = continue_instruction_line_size,
                advance_keys = continue_keys, reverse_keys = backward_keys,
                quit_keys = exit_keys, ticker = clock,
                frame_rate = frame_rate, files = other_files
            )
            lines_formed, times_lost = tetromino.distractor(
                distraction_duration/1000, instruction_font,
                top_exclude = top_margin, right_exclude = right_margin,
                bottom_exclude = bottom_margin, left_exclude = left_margin,
                antialias = antialiasing,
                text_colour = instruction_colour,
                c = clock, fps = frame_rate,
                sound_file = tetromino_sound_file, press_to_quit = exit_keys,
                files = other_files
            )
            lines.append(lines_formed)
            losses.append(times_lost)
        text.display_text_until_keypress(
            test_instructions, instruction_font, instruction_colour,
            instruction_background,
            proportion_width = 1-left_margin-right_margin,
            proportion_height = 1-top_margin-bottom_margin,
            main_line = instruction_line_size,
            break_sentences = split_sentences_between_screens,
            sentence_terminators = sentence_terminators,
            terminator_exceptions = sentence_terminator_exclusions,
            gap = lines_between_instructions_and_continue_message,
            bottom_message = continue_instruction_message,
            bottom_font = continue_instruction_font,
            bottom_line = continue_instruction_line_size,
            advance_keys = continue_keys, reverse_keys = backward_keys,
            quit_keys = exit_keys, ticker = clock,
            frame_rate = frame_rate, files = other_files
        )
        recall_responses_i = free_recall_test(
            instruction_font, line_size = instruction_line_size,
            antialias = antialiasing, text_colour = instruction_colour,
            background_colour = instruction_background,
            prompt = recall_prompt, verification = recall_verification,
            finished_string = finished_string,
            trim_width = left_margin+right_margin,
            trim_height = top_margin+bottom_margin,
            allowed_keys = response_keys, time_limit = time_for_recall,
            time_up_message = time_up_message,
            time_up_message_duration = time_up_message_duration,
            show_previous_input = previous_responses_stay_on_screen,
            ticker = clock, frame_rate = frame_rate, quit_keys = exit_keys,
            other_files = other_files
        )
        recall_responses.append(recall_responses_i)
    
    # Score results and fill the results list with dicts next.
    for i in xrange(blocks):
        study_list = study_lists[i]
        response_list = recall_responses[i]
        dict_i = score.free_recall(study_list, response_list)
        if distractor:
            dict_i[LINES] = lines[i]
            dict_i[LOSSES] = losses[i]
        results.append(dict_i)
    
    # If there was more than one block, add dict collapsing across blocks:
    if blocks > 1:
        all_stimuli = []
        all_responses = []
        for i in xrange(blocks):
            all_stimuli = all_stimuli+study_lists[i]
            all_responses = all_responses+recall_responses[i]
        overall_dict = score.free_recall(all_stimuli, all_responses)
        overall_dict[LINES] = sum(lines)
        overall_dict[LOSSES] = sum(losses)
        results.append(overall_dict)
    
    # Write any requested data to files:
    if study_file:
        study_file = writing.ready_file_for_writing(study_file)
        for i in xrange(blocks):
            study_file.write("Study list {:d} follows.\n".format(i+1))
            writing.study_phase(
                study_list, study_file, close_when_finished = False
            )
            study_file.write("\n")
        study_file.close()
    
    if study_files:
        for i in xrange(blocks):
            study_list = study_lists[i]
            writing.study_phase(study_list, study_files[i])
    
    if distractor_file and distractor:
        distractor_file = writing.ready_file_for_writing(distractor_file)
        for i in xrange(blocks):
            distractor_file.write(
                "For Block {:d}, this subject completed {:d} lines and lost \
{:d} times.\n".format(
                    i+1, lines[i], losses[i]
                )
            )
        distractor_file.close()
    
    if distractor_files and distractor:
        for i in xrange(blocks):
            current_file = writing.ready_file_for_writing(distractor_files[i])
            current_file.write(
                "lines = {:d}\nlosses = {:d}".format(lines[i], losses[i])
            )
            current_file.close()
    
    if protocol_file:
        protocol_file = writing.ready_file_for_writing(protocol_file)
        for i in xrange(blocks):
            protocol = results[i][ITEMS_RECALLED]
            if protocol:
                protocol_file.write(
                    "The protocol for Block {:d} follows.\n".format(i+1)
                )
                writing.list_or_tuple(protocol_file, protocol, c = False)
            else:
                protocol_file.write(
                    "No items were recalled for Block {:d}.\n".format(i+1)
                )
        protocol_file.close()
    
    if protocol_files:
        for i in xrange(blocks):
            current_file = protocol_files[i]
            protocol = results[i][ITEMS_RECALLED]
            if protocol:
                writing.list_or_tuple(current_file, protocol)
            else:
                current_file = writing.ready_file_for_writing(current_file)
                current_file.write("No items recalled.")
                current_file.close()
    
    if intrusion_file:
        intrusion_file = writing.ready_file_for_writing(intrusion_file)
        for i in xrange(blocks):
            current_intrusions = results[i][INTRUSIONS]
            if current_intrusions:
                intrusion_file.write(
                    "Intrusions for Block {:d} follow.\n".format(i+1)
                )
                writing.list_or_tuple(
                    intrusion_file, current_intrusions, c = False
                )
            else:
                intrusion_file.write(
                    "There were no intrusions for Block {:d}.\n".format(i+1)
                )
        intrusion_file.close()
    
    if intrusion_files:
        for i in xrange(blocks):
            current_file = intrusion_files[i]
            current_intrusions = results[i][INTRUSIONS]
            if current_intrusions:
                writing.list_or_tuple(current_file, current_intrusions)
            else:
                current_file = writing.ready_file_for_writing(current_file)
                current_file.write("No intrusions.")
                current_file.close()
    
    if close_matches_file:
        close_matches_file = writing.ready_file_for_writing(close_matches_file)
        for i in xrange(blocks):
            close_ones = results[i][CLOSE_MATCHES]
            if close_ones:
                close_matches_file.write(
                    "Block {:d} close matches follow.\n".format(i+1)
                )
                for key in close_ones:
                    close_matches_file.write(key+": ")
                    for j in xrange(len(close_ones[key])):
                        if j < len(close_ones[key])-1:
                            close_matches_file.write(close_ones[key][j]+", ")
                        else:
                            close_matches_file.write(close_ones[key][j]+"\n")
            else:
                close_matches_file.write(
                    "Block {:d} had no close matches.\n".format(i+1)
                )
        close_matches_file.close()
    
    if close_matches_files:
        for i in xrange(blocks):
            current_file = close_matches_files[i]
            current_file = writing.ready_file_for_writing(current_file)
            close_ones = results[i][CLOSE_MATCHES]
            if close_ones:
                for key in close_ones:
                    current_file.write("{:s}: ".format(key))
                    for j in xrange(len(close_ones[key])):
                        if j < len(close_ones[key])-1:
                            current_file.write(close_ones[key][j]+", ")
                        else:
                            current_file.write(close_ones[key][j]+"\n")
            else:
                current_file = writing.ready_file_for_writing(current_file)
                current_file.write("No close matches.")
                current_file.close()
    
    if results_file:
        results_file = writing.ready_file_for_writing(results_file)
        for i in xrange(blocks):
            results_file.write("Block {:d}\n".format(i+1))
            writing.write_dict(results[i], results_file, False)
            results_file.write("\n\n")
        if blocks > 1:
            results_file.write("Collapsing across block:")
            writing.write_dict(results[blocks], results_file)
    
    if results_files:
        for i in xrange(blocks):
            current_file = results_files[i]
            writing.write_dict(results[i], current_file)
    return results


def generate_word_pairs(words, illegal_pairs = (), max_attempts = 100, relatedness_matrix = None, sep = None, cutoff = 0.6):
    """
    Return a list of word pairs from a set of words.
    
    Parameters:
        words: a file or list/tuple of words; there must be an even number of
        these.
    
    Keyword Parameters:
        illegal_pairs: an optional list/tuple/file of pairs that cannot;
            defaults to an empty tuple.
        max_attempts: the maximum number of times to try creating the pairs;
            defaults to 100. If max_attempts are made without success, an
            error is raised.
        relatedness_matrix: a string pointing to a file containing a matrix
            with the semantic relatedness of the words in words; defaults to
            None, in which case the rest of the keyword parameters are
            ignored. It is assumed that the matrix in this file has words+1
            rows and words+2 columns. The leftmost column is for the
            individual words and then each word has its own column and row.
        sep: the character separating items in the matrix; defaults to None,
            in which white space is treated as the separator.
        cutoff: the degree of relatedness permitted for a word pair.
    
    Returns:
        word_pairs: a list of the word pairs; each element is a list of two
            words.
    """
    try:
        with open(words) as file_:
            words = file_.readlines()
        words = [word.strip() for word in words]
    except TypeError:
        pass
    assert len(words)%2 == 0, "There must be an even number of words."
    if isinstance(illegal_pairs, str):
        with open(illegal_pairs) as file_:
            illegal_pairs = file_.readlines()
        illegal_pairs = [pair.split() for pair in illegal_pairs]
    if relatedness_matrix:
        with open(relatedness_matrix) as file_:
            matrix_ = file_.readlines()
        matrix_ = [line.strip() for line in matrix_]
        matrix_ = [line.split(sep) for line in matrix_]
        # Get the number of columns and rows (saves len() overhead):
        columns_and_rows = len(matrix_[1])
        if len(matrix_[0]) == columns_and_rows-1:
            # Add dummy value to equalize:
            matrix_[0].insert(0, None)
        elif len(matrix_[0]) != columns_and_rows:
            raise ValueError("Something is wrong with the similarity matrix.")
        assert all(len(row) == columns_and_rows for row in matrix_[1:]), \
"Something is wrong with the relatedness_matrix file. The number of rows \
isn't adding up."
        assert len(matrix_) == columns_and_rows, "The number of columns \
doesn't add up in the relatedness_matrix file."
        # Convert matrix_ to a dict:
        matrix_dict = {}
        for i in xrange(1, columns_and_rows):
            key_i = matrix_[0][i]
            matrix_dict[key_i] = {}
            for j in xrange(1, columns_and_rows):
                key_j = matrix_[0][j]
                matrix_dict[key_i][key_j] = float(matrix_[i][j])
    
    number_of_pairs = len(words)//2
    i = 0
    while i < max_attempts:
        word_pairs = np.random.choice(
            words, size = (number_of_pairs, 2), replace = False
        )
        # Regular tuples are better for Boolean comparisons than numpy arrays.
        word_pairs = generic.convert_to_tuple(word_pairs)
        if illegal_pairs or relatedness_matrix:
            works = True   # until proven otherwise
            for word_pair in word_pairs:
                if any(current_pair in illegal_pairs for current_pair in (word_pair, list(word_pair), [word_pair[1], word_pair[0]], (word_pair[1], word_pair[0]))):
                    works = False
                    break
                if relatedness_matrix:
                    word1_key, word2_key = word_pair
                    relatedness = matrix_dict[word1_key][word2_key]
                    if relatedness >= cutoff:
                        works = False
                        break
        try:
            if works:
                return word_pairs
            else:
                i = i+1
        except NameError:
            return word_pairs
    # Reaching this points means max_attempts were made without success.
    raise ValueError("The word pairs couldn't be created.")
    return


def cued_recall_study(stimuli, duration, distance = 135, horizontal = True, balance_targets = True, isi_object = None, isi_duration = None, isi_fixation = "+", isi_location = "middle centre", illegal_pairs = None, similarity_matrix = None, similarity_cutoff = None, matrix_sep = None, randomize = False, scale = None, end_trial_after_scale_input = False, case = "", stim_font = None, stim_fonts = None, use_antialiasing = True, stim_colour = None, stim_colours = None, stim_background = None, stim_backgrounds = None, isi_font = None, isi_colour = None, isi_background = None, isi_antialiasing = True, timer = None, fps = 30, keys_to_quit = (K_ESCAPE,), data_file = None, other_files = ()):
    """
    Administer a study phase in which word pairs are presented on each trial.
    
    Parameters:
        stimuli: the word pairs to present. This can be a file containing the
            word pairs (the file should have either one word per line, in
            which case pairs are generated randomly, or two words per line, in
            which case each line is a word pair [although cue and target
            status will be assigned randomly]), a list of string pairs (lists
            or tuples), or a list of WordPair objects.
        duration: the presentation duration, in milliseconds, for each word
            pair.
    
    Keyword Parameters:
        distance: the distance between the two words; this can be a proportion
            of the screen or the specific number of pixels (there is probably
            a very slight speed advantage to passing the latter). This
            parameter defaults to 135.
        horizontal: whether words are presented from left to right (True) or
            top to bottom (False); defaults to True.
        balance_targets: Boolean indicating whether there are an equal number
            of targets on the left/top and bottom/right; defaults to True. If
            there are an odd number of pairs, then one side will have an extra
            target.
        isi_object: an InterTrialStimulus object; defaults to None. If no
            InterTrialStimulus object is passed but isi_duration > 0, one is
            created.
        isi_duration: the time, in milliseconds, for which the ISI is
            presented; defaults to None, in which case no ISI is presented
            unless an InterTrialStimulus object is passed for the isi_object
            parameter.
        isi_fixation: string that appears during the interstimulus interval;
            defaults to "+".
        isi_location: where isi_fixation is centred; defaults to "middle
            centre". This parameter must be a string from the SCREEN_POSITIONS
            constant or a pixel coordinate.
        illegal_pairs: any pairs to exclude from the study list (i.e., words
            that cannot appear together); defaults to None, and only applies
            if stimuli is a file or list of individual words. illegal_pairs
            must be as a list or tuple of two-element lists or tuples.
        similarity_matrix: an optional string pointing to a file containing a
            matrix of the study words and their degree of similarity to one
            another. This parameter defaults to None.
        similarity_cutoff: if a similarity matrix is passed, this is the
            maximum degree of similarity a word pair can have.
        matrix_sep: the character separating values in the similarity matrix;
            defaults to None, in which case white space is used as the value
            separator.
        randomize: Boolean indicating whether stimuli are shuffled before the
            study phase; defaults to False. When True, if stim_fonts,
            stim_colours, or stim_backgrounds are set, these, too, are
            shuffled.
        scale: an optional RatingScale object to present with word pairs;
            defaults to None.
        end_trial_after_scale_input: Boolean indicating whether the study pair
            disappears following a scale response; defaults to False, and has
            no effect if no Scale object is passed.
        case: "u", "l", or an empty string; only applies if stimuli are not
            WordPair objects; defaults to an empty string. If case is "u", all
            words are presented in uppercase; if case is "l", all words are
            presented in lowercase; and if case is an empty string, all words
            are left as is.
        stim_font: pygame.font.Font object to use if all stimuli are rendered
            in the same font; ignored if stimuli are WordPair objects.
        stim_fonts: list or tuple of fonts to use in rendering stimuli;
            defaults to None, and only applies if stimuli are not WordPair
            objects. The ith font in stim_fonts will be assigned to the ith
            WordPair in stimuli. stim_fonts will be randomized if randomize is
            True.
        use_antialiasing: Boolean indicating whether antialiasing is used in
            rendering WordPairs; defaults to True, but is ignored if stimuli
            are WordPair objects.
        stim_colour, stim_colours, stim_background, stim_backgrounds: like
            stim_font and stim_fonts.
        isi_font, isi_colour, isi_background, and isi_antialiasing: controls
            ISI characteristics; default to None (or True for
            isi_antialiasing); if needed and set to None, characteristics are
            taken from the first-presented WordPair.
        timer: pygame.time.Clock object; defaults to None, in which case one
            is created.
        fps: frames per second; defaults to 30.
        keys_to_quit: keys that close the program; defaults to escape.
        data_file: a file to which to write the study list and (if applicable)
            ratings; defaults to None.
        other_files: any files that are open and should be closed if a quit
            event is encountered; defaults to an empty tuple.
    
    Returns:
        If stimuli are passed as WordPair objects, then nothing is returned.
        However, if a file or strings are passed for stimuli, then the list of
        WordPair objects is returned, as it will be needed for the test phase.
    """
    assert duration > 0, "duration must be positive."
    assert fps > 0, "fps must be positive."
    return_stimuli = False   # until proven otherwise
    # stimuli could be a file, a string pointing to a file, a list of WordPair
    # objects, a list of word pairs, or a list of single words.
    # There's probably a more elegant way of doing this with try/except...
    if (isinstance(stimuli, (list, tuple)) and isinstance(stimuli[0], str)) or (isinstance(stimuli, (str, file))):
        return_stimuli = True
        stimuli = generate_word_pairs(
            stimuli, illegal_pairs, relatedness_matrix = similarity_matrix,
            sep = matrix_sep, cutoff = similarity_cutoff
        )
    # stimuli is now a list of WordPair objects or a list of string pairs.
    if isinstance(stimuli[0], (list, tuple)):
        return_stimuli = True
        if case == "u":
            for i in xrange(len(stimuli)):
                for j in xrange(2):
                    if not stimuli[i][j].upper():
                        stimuli[i][j] = stimuli[i][j].upper()
        elif case == "l":
            for i in xrange(len(stimuli)):
                for j in xrange(2):
                    if not stimuli[i][j].islower():
                        stimuli[i][j] = stimuli[i][j].lower()
        if randomize:
            try:
                np.random.shuffle(stimuli)
            except TypeError:
                # stimuli might be a tuple.
                stimuli = list(stimuli)
                np.random.shuffle(stimuli)
            if stim_fonts:
                try:
                    np.random.shuffle(stim_fonts)
                except TypeError:
                    stim_fonts = list(stim_fonts)
                    np.random.shuffle(stim_fonts)
            if stim_colours:
                try:
                    np.random.shuffle(stim_colours)
                except TypeError:
                    stim_colours = list(stim_colours)
                    np.random.shuffle(stim_colours)
            if stim_backgrounds:
                try:
                    np.random.shuffle(stim_backgrounds)
                except TypeError:
                    stim_backgrounds = list(stim_backgrounds)
                    np.random.shuffle(stim_backgrounds)
        if balance_targets:
            first = len(stimuli)//2
            second = first
            if len(stimuli)%2 == 1:
                extra_goes_to = np.random.choice(("first", "second"))
                if extra_goes_to == "first":
                    first = first+1
                else:
                    second = second+1
        # Create WordPair objects:
        for i in xrange(len(stimuli)):
            item1, item2 = stimuli[i]
            if balance_targets:
                if first and second:
                    target_item, cue_item = np.random.choice(
                        (item1, item2), 2, False
                    )
                    if target_item == item1:
                        first = first-1
                    else:
                        second = second-1
                elif first:
                    target_item = item1
                    cue_item = item2
                else:
                    target_item = item2
                    cue_item = item1
            else:
                target_item, cue_item = np.random.choice(
                    (item1, item2), 2, False
                )
            if stim_fonts:
                current_font = stim_fonts[i]
            elif i == 0:
                current_font = stim_font
            if stim_colours:
                current_colour = stim_colours[i]
            elif i == 0:
                current_colour = stim_colour
            if stim_backgrounds:
                current_background = stim_backgrounds[i]
            elif i == 0:
                current_background = stim_background
            stimuli[i] = WordPair(
                item1, item2, current_font, apart = distance,
                left_to_right = horizontal, cue = cue_item,
                target = target_item, colour = current_colour,
                background = current_background,
                antialiasing = use_antialiasing
            )
    if not isi_object and isi_duration:
        if isi_fixation:
            if not isi_font:
                isi_font = stimuli[0].font
            if not isi_colour:
                isi_colour = stimuli[0].colour
        if not isi_background:
            isi_background = stimuli[0].background
        isi_object = InterTrialStimulus(
            isi_duration, isi_fixation, isi_font, isi_colour, isi_background,
            isi_antialiasing, location = isi_location
        )
    if scale:
        screen = pygame.display.get_surface()
        try:
            screen_width, screen_height = screen.get_size()
        except AttributeError:
            screen_width, screen_height = pygame.display.list_modes()[0]
        scale.rect.top = screen_height-scale.rect.height-scale.font.get_linesize()
        scale.rect.left = screen_width//2-scale.rect.width//2
    
    # Present study phase:
    for i in xrange(len(stimuli)):
        word_pair = stimuli[i]
        left_over_time = word_pair.study(
            duration, scale, end_after_input = end_trial_after_scale_input,
            ticker = timer, frame_rate = fps, exit_keys = keys_to_quit,
            other_files = other_files
        )
        if isi_object:
            if scale:
                time_to_add = left_over_time
            elif i == 0:
                time_to_add = 0
            isi_object.present(
                time_change = time_to_add, clock = timer, frame_rate = fps,
                exit_keys = keys_to_quit, files = other_files
            )
    if data_file:
        writing.paired_study(stimuli, data_file)
    if return_stimuli:
        return stimuli
    return


def cued_recall_test(stimuli, isi_object = None, isi_duration = None, isi_fixation = "+", isi_location = "middle centre", isi_font = None, isi_colour = None, isi_background = None, isi_antialiasing = True, randomize = False, response_font = None, use_antialiasing = True, timer = None, fps = 30, allowed_keys = LETTERS, keys_to_quit = (K_ESCAPE,), data_file = None, other_files = ()):
    """
    Administer a cued-recall test.
    
    Parameters:
        stimuli: a list or tuple of WordPair objects.
    
    Keyword Parameters:
        isi_object InterTrialStimulus object; defaults to None.
        isi_duration: milliseconds for which the InterTrialStimulus is
            presented; defaults to None, and is ignored if isi_object is set.
        isi_fixation: string presented during the ISI; defaults to "+";
            ignored if isi_object is set.
        isi_location: the location of isi_fixation, either in pixel
            coordinates or as a string from the SCREEN_POSITIONS constant;
            defaults to "middle centre", but is ignored if isi_object is set.
        isi_font, isi_colour, isi_background, and isi_antialiasing: the text
            attributes used for presenting isi_fixation; default to None (or
            True for isi_antialiasing); if any are None, isi_duration > 0, and
            an InterTrialStimulus is not passed for isi_object,, the
            attributes are obtained from stimuli[0]
        randomize: Boolean indicating whether stimuli are randomized before
            test; defaults to False.
        response_font, response_colour, response_background: the text
            attributes for the user's responses; defaults to None, in which
            case attributes are taken from stimuli[0].
        use_antialiasing: Boolean indicating whether antialiasing is used for
            text input; defaults to True.
        timer: an optional pygame.time.Clock object; defaults to None, in
            which case one is created.
        fps: frames per second; defaults to 30.
        allowed_keys: keys that can be pressed in response input; defaults to
            the letters.
        keys_to_quit: keys that exit the program; defaults to escape.
        data_file: a file to which to write the subject's responses; defaults
            to None, in which case nothing is written. To write data, pass a
            string pointing to a file or a file object.
        other_files: any currently opened files that need to be closed if the
            program is closed.
    """
    assert not any(k in allowed_keys for k in (K_RETURN, K_BACKSPACE)), \
"Neither return nor backspace may appear in allowed_keys."
    assert not any(k in keys_to_quit for k in (K_BACKSPACE, K_RETURN)), \
"Neither return nor backspace may appear in keys_to_quit."
    assert not any(k in allowed_keys for k in keys_to_quit), "There may not \
be overlap between allowed_keys and keys_to_quit."
    assert fps > 0, "fps must be positive."
    if randomize:
        np.random.shuffle(stimuli)
    if not isi_object and isi_duration:
        if isi_fixation:
            if not isi_font:
                isi_font = stimuli[0].font
            if not isi_colour:
                isi_colour = stimuli[0].colour
        if not isi_background:
            isi_background = stimuli[0].background
        isi_object = InterTrialStimulus(
            isi_duration, isi_fixation, isi_font, isi_colour, isi_background,
            isi_antialiasing, isi_location
        )
    
    # Test phase now:
    for word_pair in stimuli:
        word_pair.test(allowed_keys, timer, fps, keys_to_quit, other_files)
        try:
            isi_object.present(
                clock = timer, frame_rate = fps, exit_keys = keys_to_quit,
                files = other_files
            )
        except AttributeError:
            pass
    if data_file:
        writing.cued_recall_results(stimuli, data_file)
    return


def rate_images(images, response_keys = NUMBERS, start_after = 0, end_after = None, isi = None, ticker = None, frame_rate = 30, quit_keys = (K_ESCAPE,), files = ()):
    """
    Rate a list of Image objects.
    
    Parameters:
        images: the Image objects to be rated.
    
    Keyword Parameters:
        response_keys: keys that can be pressed to make a rating; defaults to
            single-digit numbers including 0.
        start_after: milliseconds for which to wait before allowing a
            response; defaults to 0.
        end_after: milliseconds after image onset after which a rating is not
            allowed; defaults to None, in which case the image stays on the
            screen until an appropriate keypress is made.
        isi: an optional InterTrialStimulus object to display between rated
            Images.
        ticker: pygame.time.Clock object; defaults to None, in which case one
            is created.
        frame_rate: frames per second; defaults to 30.
        quit_keys: keys that close the program; defaults to escape.
        files: any files that need to be closed if the program exits; defaults
            to an empty tuple.
    """
    assert frame_rate > 0, "frame_rate must be positive."
    screen = pygame.display.get_surface()
    for i in xrange(len(images)):
        image = images[i]
        image.rate(
            allowed_keys = response_keys, begin_time = start_after,
            finish_time = end_after, c = ticker, fps = frame_rate,
            exit_keys = quit_keys, files = files
        )
        if isi and i < len(images)-1:
            isi.present()
    return
