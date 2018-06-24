"""
Example of a cued-recall experiment using the cogandmem package.
Tyler M. Ensor (tyler.ensor@mun.ca)

This experiment implements a list-length manipulation in A-B/C-D cued
recall. Results are saved in data.csv (found in the same folder as the
present script--cogandmem/examples/cued recall).

I have commented this script more heavily than I would ordinarily.
Here, I make the assumption that the reader is familiar with Python but
not necessarily with pygame or cogandmem.

This is a simple list-length experiment with list length manipulated
within subjects. Tetromino is interpolated between study and test. At
study, likeability judgments are collected for word pairs.
"""

from __future__ import division

import numpy as np

import cogandmem
import pygame
from pygame.locals import *
# I know it is not good practice to use "from package import *". However,
# importing pygame's constants like this is standard.

# Constants:
QUIT_TUPLE = (K_ESCAPE,)   # used to exit the experiment
# Note that, in pygame, every key has a constant that takes the form "K_[key
# name]". So, a, b, and c are denoted K_a, K_b, and K_c, respectively.
ADVANCE_TUPLE = (K_SPACE,)   # advances instructions
SHORT = "short"
LONG = "long"
ORDER = [SHORT, LONG]
np.random.shuffle(ORDER)
SHORT_LENGTH = 16   # word pairs in the short list
LONG_LENGTH = 32   # word pairs on the long list
STIM_DURATION = 3000   # ms for word-pair presentation
SCALE_DURATION = 2500   # ms for the rating scale
ISI_DURATION = 500   # ms for the interstimulus interval (ISI)
LONG_TETROMINO_DURATION = 60000   # ms for Tetromino in the long-list condition
# Seconds rather than milliseconds are needed for Tetromino, but getting the
# short-list condition's Tetromino duration in ms is easier first (because
# constants like STIM_DURATION are in ms).
# cogandmem.generic.milliseconds_to_seconds() helps here.
SHORT_TETROMINO_DURATION = cogandmem.generic.milliseconds_to_seconds(
    LONG_TETROMINO_DURATION+(
        (LONG_LENGTH-SHORT_LENGTH)*(STIM_DURATION+SCALE_DURATION+ISI_DURATION)
    )
)
# And change LONG_TETROMINO_DURATION to s:
LONG_TETROMINO_DURATION = cogandmem.generic.milliseconds_to_seconds(
    LONG_TETROMINO_DURATION
)
FIXATION = "+"   # string for the ISI fixation
CONTINUE_TEXT = "Press the space bar to continue."
FPS = 60   # frame rate
WHITE = (255, 255, 255)   # white RGB
BLACK = (0, 0, 0)
TEXT_COLOUR = WHITE
BACKGROUND_COLOUR = BLACK
# Some constants for keys in returned dicts:
PROPORTION_RECALL = "proportion recall"
OVERALL = "overall"

# Tetromino line and loss counters:
lines = []
losses = []

# Get a date and time string to have a unique subject identifier:
subject_id = cogandmem.generic.date_time_string()
# returns a string of the form "yyyy.mm.dd.hh.mm.ss"; uses local time

# We need to initialize pygame to access some of its functionality.
pygame.init()

# pygame requires a main display Surface. This is an instance of pygame.
# Surface, and is the surface currently visible to the user. Once set, a
# reference to the main display Surface can be obtained by calling
# pygame.display.get_surface() (returns None if a main Surface does not
# exist).
# When running memory experiments, it's possible that you will want the
# experiment to appear on several computers with different sized monitors.
# Provided that you want the experiment to take up the entire screen, this is
# straightforward.
window = pygame.display.set_mode(pygame.display.list_modes()[0], FULLSCREEN)
# FULLSCREEN is a pygame constant that tells pygame to run the experiment in
# full-screen mode. When full-screen mode is enabled, you will not be able to
# exit the experiment by, for example, navigating to Terminal and quitting.
# Therefore, you usually will not want to use FULLSCREEN when testing and
# debugging an experiment. You can simply skip the second argument to leave
# pygame in standard mode.
# The main display Surface was set with a call to pygame.display.set_mode().
# The first argument to this function is a list of two numbers--width and
# height, expressed in pixels. For this value, we passed
# pygame.display.list_modes()[0]. That function returns a list of valid
# width-height lists, with the first taking up the entirety of the computer's
# monitor.

# In pygame, font size is expressed as the height of the font in pixels.
# Depending on the monitor, then, size 100 could look large or small.
# Therefore, scale font size with screen height:
font_size = window.get_size()[1]//15
# Surface.get_size() returns [width, height] of the Surface instance.
# Dividing by 15 is arbitrary, but has worked in my experience.

# Create pygame.font.Font objects:
font = pygame.font.SysFont("timesnewroman", font_size)
# Note that pygame has two functions for generating pygame.font.Font objects.
# With pygame.font.SysFont, a system font needs to be passed (e.g.,
# "timesnewroman"). You can see a list of your system's available fonts by
# calling pygame.font.get_fonts().
# Alternatively, you can create a pygame.font.Font object by calling
# pygame.font.Font() directly. This requires two arguments: a string pointing
# to a font file and a font size (again in pixels). This sounds similar to
# pygame.font.SysFont(), but note that, in the case of pygame.font.Font(), you
# need the actual path to a font file (e.g., ".ttf")--the name of the font
# alone will not suffice. I find pygame.font.Font() useful when I need to have
# an experiment run on multiple machines, and I can't guarantee they will all
# have the font I need. In that case, I simply place the ttf file in the same
# folder as the experiment (this makes passing the string for the first
# positional argument to pygame.font.Font() simple).

# We don't use the mouse in this experiment, so:
pygame.mouse.set_visible(False)

# Instruction strings:
# In my own work, I generally put instructions in txt files, then read them
# into strings with glob.glob(). However, to prevent increasing the number of
# files packaged with cogandmem, they are written out here.
starting_instructions = (
    ("Thank you for participating in this experiment."),
    (
        "This experiment is broken into three phases, which you will cycle "
        "through two times."
    ),
    (
        "In the study phase, you will see word pairs presented one at a time "
        "in the centre of the screen. We would like you to rate how much you "
        "like each pair."
    ),
    (
        "You will make your ratings on a seven-point scale, which will "
        "appear after the word pair is removed from the screen. Enter your "
        "rating by pressing the number on the keyboard corresponding to your"
    ),
    (
        "On the rating scale, think of 1 as representing extremely "
        "unlikeable, 7 as representing extremely likeable, and 4 as a neutral "
        " point."
    ),
    (
        "After you have studied the word pairs, you will play Tetromino (a "
        "Tetris clone)."
    ),
    (
        "After Tetromino, you will have a memory test. You will be cued with "
        "one of the words from each word pair and asked to recall the word"
        " that accompanied it during the study phase."
    ),
    (
        "When you are ready to start, press the space bar."
    )
)
tetromino_instructions = "To start playing Tetromino, press the space bar."
test_instructions = (
    "The memory test is next. If you cannot hazard a guess for any of the "
    "words, type q."
)
next_block_instructions = (
    "You're halfway done! Press the space bar to start the second half."
)
finished_instructions = "Finished! Press the space bar to close the program."

# cogandmem.experiment.RatingScale is a class for rating scales. Create the
# scale for the present experiment:
rating_scale = cogandmem.experiment.RatingScale(
    7,   # anchors
    font,   # pygame.font.Font instance needed
    colour = TEXT_COLOUR,
    background = BACKGROUND_COLOUR
)

# cogandmem.experiment also has an InterTrialStimulus class for ISI displays.
isi = cogandmem.experiment.InterTrialStimulus(
    ISI_DURATION, fixation = FIXATION, font = font, colour = TEXT_COLOUR,
    background = BACKGROUND_COLOUR
)

# Get and create the stimuli:
# The words from the Toronto Noun Pool are included in the file "Toronto Noun
# Pool.txt" (located in the same folder as the present script).
# Put these words in a list:
nouns = cogandmem.generic.file_lines("Toronto Noun Pool.txt")
# This produces a list of the lines in the file, with leading and trailing
# white space removed.
# We will draw randomly without replacement from this list to get the words
# for the experiment.
experimental_words = np.random.choice(nouns, 2*(SHORT_LENGTH+LONG_LENGTH))
experimental_pairs = cogandmem.experiment.generate_word_pairs(
    experimental_words,
    # illegal_pairs = an optional parameter to which you can pass a list of unacceptable pairings
)
# Currently, cogandmem.experiment.generate_word_pairs() returns a tuple of
# tuples. (This will be fixed in future versions.) Tuples will not work for
# present purposes, so:
experimental_pairs = cogandmem.generic.convert_to_list(experimental_pairs)

# cogandmem.experiment has a class called WordPair. The pairs in
# experimental_pairs are made into WordPair objects next. A future version of
# cogandmem should probably include a function to do this automatically.
for i in xrange(len(experimental_pairs)):
    word1, word2 = experimental_pairs[i]
    # Overwrite the list of strings with a WordPair object:
    experimental_pairs[i] = cogandmem.experiment.WordPair(word1, word2, font)
    # NB: WordPair has a number of keyword attributes. See the docstring for
    # more information.

# Separate experimental_pairs into short and long study lists:
short_study = experimental_pairs[:SHORT_LENGTH]
long_study = experimental_pairs[SHORT_LENGTH:]

# Instances of WordPair have a test attribute. Rather than copying the
# WordPairs themselves to test lists, the test lists can be indices
# referencing elements from the study lists.
short_test = range(SHORT_LENGTH)
long_test = range(LONG_LENGTH)
np.random.shuffle(short_test)
np.random.shuffle(long_test)

# Present the starting instructions:
for instructions in starting_instructions:
    # cogandmem.text has a number of useful functions for displaying text. The
    # most important are display_text_until_keypress(), which, as the name
    # implies, leaves text on the screen until the user presses a specified
    # key. Note that, if the text does not all fit on one screen,  the text
    # will be automatically wrapped across multiple screens.
    # The other most useful function is ask_question(). This function allows
    # you to have the user answer a question. The response can be limited to
    # specific keys (e.g., if you are asking the user's age, you would only
    # allow numbers to be input; if you were asking about gender identity, you
    # would probably limit keypresses to f, m, and o, etc.).
    # Only the display_text_until_keypress() function is used in the present
    # script.
    cogandmem.text.display_text_until_keypress(
        instructions, font, TEXT_COLOUR, BACKGROUND_COLOUR,
        bottom_message = CONTINUE_TEXT, advance_keys = ADVANCE_TUPLE,
        frame_rate = FPS, quit_keys = QUIT_TUPLE
    )
    # bottom_message appears beneath the instructions, and its contents should
    # match the key specified in ADVANCE_TUPLE. Otherwise, you will have some
    # very confused subjects.

# Experimental session starts now.
for condition in ORDER:
    if condition == SHORT:
        # There probably would have been a more efficient way to set this up,
        # but hopefully this is the clearest.
        # The first thing to do is, if the short list came second, present the
        # halfway instructions.
        if ORDER[1] == SHORT:
            cogandmem.text.display_text_until_keypress(
                next_block_instructions, font, TEXT_COLOUR, BACKGROUND_COLOUR,
                bottom_message = CONTINUE_TEXT, advance_keys = ADVANCE_TUPLE,
                frame_rate = FPS, quit_keys = QUIT_TUPLE
            )
        for i in xrange(SHORT_LENGTH):
            pair = short_study[i]
            # Call the study method of WordPair:
            pair.study(
                STIM_DURATION, frame_rate = FPS, exit_keys = QUIT_TUPLE
            )
            # For presenting the rating scale, we need to know when the
            # subject entered a response. At that point, the scale disappears
            # and the ISI begins. So, if the total time has not elapsed for
            # the rating scale, the difference is added to the ISI.
            # The get-_rating method of RatingScale objects returns both the
            # subject's input rating (if one was made) and the time left when
            # the response was made.
            rating, time_left = rating_scale.get_rating(
                duration = SCALE_DURATION, return_after_input = True,
                frame_rate = FPS, exit_keys = QUIT_TUPLE
            )
            # The present script doesn't actually use the information, but the
            # rating can be saved in the rating attribute of WordPair:
            pair.rating = rating
            # Check if time needs to be added to the ISI:
            if time_left:
                # NB: time_left is 0 if total time elapsed.
                # time_left is in seconds, but we need ms:
                time_left = cogandmem.generic.seconds_to_milliseconds(
                    time_left
                )
            # Present the ISI:
            isi.present(
                time_change = time_left, frame_rate = FPS,
                exit_keys = QUIT_TUPLE
            )
            
        # Tetromino now.
        # Present the Tetromino instructions:
        cogandmem.text.display_text_until_keypress(
            tetromino_instructions, font, TEXT_COLOUR, BACKGROUND_COLOUR,
            bottom_message = CONTINUE_TEXT, advance_keys = ADVANCE_TUPLE,
            frame_rate = FPS, quit_keys = QUIT_TUPLE
        )
        # Call cogandmem.tetromino.distractor(), which has the user play
        # Tetromino for a specified duration. If the player loses, the board
        # refreshes and starts again. The function returns the number of lines
        # and the number of times the player lost.
        n_lines, n_losses = cogandmem.tetromino.distractor(
            SHORT_TETROMINO_DURATION, font, fps = FPS,
            press_to_quit = QUIT_TUPLE
        )
        # Save the lines and losses data:
        lines.append(n_lines)
        losses.append(n_losses)
        
        # Test phase now.
        # As before, present the instructions:
        cogandmem.text.display_text_until_keypress(
            test_instructions, font, TEXT_COLOUR, BACKGROUND_COLOUR,
            bottom_message = CONTINUE_TEXT, advance_keys = ADVANCE_TUPLE,
            frame_rate = FPS, quit_keys = QUIT_TUPLE
        )
        for j in short_test:
            pair = short_study[j]
            # NB: The test method of WordPair objects returns nothing, with
            # the user's response instead stored in the WordPair.response
            # attribute.
            pair.test(frame_rate = FPS, exit_keys = QUIT_TUPLE)
            
    else:
        # This is the long-list condition.
        # Since the code within this block is basically identical to the
        # previous block, it is not commented.
        if ORDER[1] == LONG:
            cogandmem.text.display_text_until_keypress(
                next_block_instructions, font, TEXT_COLOUR, BACKGROUND_COLOUR,
                bottom_message = CONTINUE_TEXT, advance_keys = ADVANCE_TUPLE,
                frame_rate = FPS, quit_keys = QUIT_TUPLE
            )
        for i in xrange(LONG_LENGTH):
            pair = long_study[i]
            pair.study(
                STIM_DURATION, frame_rate = FPS, exit_keys = QUIT_TUPLE
            )
            rating, time_left = rating_scale.get_rating(
                duration = SCALE_DURATION, return_after_input = True,
                frame_rate = FPS, exit_keys = QUIT_TUPLE
            )
            if time_left:
                time_left = cogandmem.generic.seconds_to_milliseconds(
                    time_left
                )
            isi.present(
                time_change = time_left, frame_rate = FPS,
                exit_keys = QUIT_TUPLE
            )
        cogandmem.text.display_text_until_keypress(
            tetromino_instructions, font, TEXT_COLOUR, BACKGROUND_COLOUR,
            bottom_message = CONTINUE_TEXT, advance_keys = ADVANCE_TUPLE,
            frame_rate = FPS, quit_keys = QUIT_TUPLE
        )
        n_lines, n_losses = cogandmem.tetromino.distractor(
            LONG_TETROMINO_DURATION, font, fps = FPS,
            press_to_quit = QUIT_TUPLE
        )
        lines.append(n_lines)
        losses.append(n_losses)
        cogandmem.text.display_text_until_keypress(
            test_instructions, font, TEXT_COLOUR, BACKGROUND_COLOUR,
            bottom_message = CONTINUE_TEXT, advance_keys = ADVANCE_TUPLE,
            frame_rate = FPS, quit_keys = QUIT_TUPLE
        )
        for j in long_test:
            long_study[j].test(frame_rate = FPS, exit_keys = QUIT_TUPLE)
# Present the finished instructions:
cogandmem.text.display_text_until_keypress(
    finished_instructions, font, TEXT_COLOUR, BACKGROUND_COLOUR,
    bottom_message = CONTINUE_TEXT, advance_keys = ADVANCE_TUPLE,
    frame_rate = FPS, quit_keys = QUIT_TUPLE
)

# Calculate results:
# The cogandmem.score mopdule contains functions for scoring free- and
# cued-recall results (recognition coming soon). For present purposes, we need
# the cued_recall() function, which returns a dictionary of results (a future
# version of cogandmem will change this to a class to make accessing its
# content easier).
short_dict = cogandmem.score.cued_recall(short_study)
long_dict = cogandmem.score.cued_recall(long_study)
# cogandmem.score.cued_recall() actually returns a dictionary of dictionaries.
# One dictionary contains overall results (i.e., ignoring any within-list
# conditions); the other breaks performance down by condition. Since nothing
# was manipulated within list in this experiment, we can ignore this latter
# dict.
short_results = short_dict[OVERALL]
long_results = long_dict[OVERALL]
# We are really only interested in proportion recalled from each condition.
# This is contained in the "proportion recall" key of short_results and
# long_results. One fairly valuable key is "close matches", which stores a
# list of responses that, while not matching a target, came close. To see the
# other keys, consult the docstring for cogandmem.score.cued_recall().
short_recall = short_results[PROPORTION_RECALL]
long_recall = long_results[PROPORTION_RECALL]

# There are functions in the cogandmem.writing module that write results to
# files. These work, but are not ideally written. In future releases of
# cogandmem, I will be modifying these functions to utilize Python's csv
# module.
# Since this script is just for demonstration purposes, the results will
# simply be printed to the screen (e.g., if you called the script from a
# Terminal window, you will see your results upon the program closing).
print("Short-list performance = "+str(short_recall))
print("Long-list performance = "+str(long_recall))

# Cleaning up:
# Normally, you need a few lines of cleanup. You need to close pygame, close
# any files that are open, and make a call to sys.exit(). However,
# cogandmem.generic.terminate() does all of this in one line. This function
# accepts an optional list of files that need to be closed. We have none
# open, so simply:
cogandmem.generic.terminate()
# And that's it!
# If you have any questions about cogandmem, please don't hesitate to get in
# touch. I would be thrilled to learn that someone is using my package. You
# can contact me at tyler.ensor@mun.ca.
