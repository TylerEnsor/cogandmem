"""
Use Tetromino, a Tetris clone, as a distractor task in a memory experiment.

This is code modified by Tyler M. Ensor. The original code was written by Al
Sweigart and released under a "Simplified BSD" license. The Tetromino code is
available in Sweigart's book Making Games with Python & Pygame (detailed in
Chapter 7). The book has a copyright date of 2012 and was freely available
online from http://inventwithpython.com/pygame as of May 17, 2017. Sweigart's
book was released under a Creative Commons License (see
http://creativecommons.org/licenses/by-nc-sa/3.0/us/).

Brief Description:
The following brief description is a direct quotation from Chapter 7 of Al
Sweigart's book, page 153.
Tetromino is a Tetris clone. Differently shaped blocks (each made up of four
boxes) fall from the top of the screen, and the player must guide them down to
form complete rows that have no gaps in them. When a complete row is formed,
the row disappears and each row above it moves down one row. The player tries
to keep forming complete lines until the screen fills up and a new falling
block cannot fit on the screen.

The present script uses the following terminology, taken from Al Sweigart's
book. This is a direct quotation (pp. 153-154).
    board: The board is made up of 10 x 20 spaces that the blocks fall and
           stack up in.
    box: A box is a single filled-in square piece on the board.
    piece: The things that fall from the top of the screen that the player can
           rotate and position. Each piece has a shape that is made up of four
           boxes.
    shape: The shapes are the different types of pieces in the game. The names
            of the shapes are T, S, Z, J, L, I, and O.
    template: A list of shape data structures that represents all of the
              possible rotations of a shape. These are stored in variables
              with names like S_SHAPE_TEMPLATE or J_SHAPE_TEMPLATE.
    landed: When a piece has either reached the bottom of the board or is
            touching a box on the board, we say that the piece has landed. At
            that point, the next piece should start falling.

Differences Between the Present Script and Sweigart's:
Note that the below list is not exhaustive. I have attempted to cover the
major changes--minor changes are not mentioned.
1. The most important modification made to the code is the introduction of a
    function, distraction(), which provides a straightforward way in which to
    use Tetromino as a distractor in memory experiments. Rather than function
    returning when the pieces reach the top of the board, the function returns
    when a specified number of seconds elapses. Canonical losses (i.e., the
    pieces reaching the top of the board) simply cause the board to reset and
    the game to continue.
2. In the original code, the piece objects were dictionaries. Here, I have
    created a Piece class.
3. Similarly, I created a class for the game board (GameBoard).
4. The original code used a default pixel size for the game. Relative to a
    given screen, this could yield a board that looked disproportionately
    large or small. In the present script, the fit_board_to_screen() function
    adjusts the size of each cell on the board to the size of the screen on
    which it will be displayed.

The present module contains the following classes (see the docstrings for more
information):
    Piece: class for Tetromino pieces.
    GameBoard: class for the Tetromino game board.

The present module contains the following functions (see the docstrings
for more information):
    get_board_boundaries: return the coordinates of the top-left corner of the
game board given the cell size, the number of blank pixel rows at the bottom
of the screen, the number of columns, and the number of rows.
    fit_board_to_screen: get the ideal size of the game board for a particular
screen.
    midpoint: return the midpoint between two integers.
    calculate_level: returns the level given a score.
    calculate_fall_frequency: return the piece fall frequency given the level.
    draw_status: draw the player's level and score to the screen.
    distractor: present Tetromino as a distractor task.
"""

from __future__ import division

import sys
import numpy as np
import time

import pygame
from pygame.locals import *

import experiment
import text
import generic


# Game Constants:
LINES_PER_LEVEL = 10
BASE_FALL_FREQUENCY = 0.35
FALL_FREQUENCY_INCREASE_PER_LEVEL = 0.01
NEW_PIECES_START_Y = -2   # y coordinate for new pieces
MOVE_SIDEWAYS_FREQUENCY = 0.15
MOVE_DOWN_FREQUENCY = 0.1

# Key Constants:
MOVE_LEFT = (K_LEFT, K_a)
MOVE_RIGHT = (K_RIGHT, K_d)
MOVE_DOWN = (K_DOWN, K_s)
MOVE_TO_BOTTOM = (K_SPACE,)
ROTATE_CLOCKWISE = (K_UP, K_w)
ROTATE_COUNTERCLOCKWISE = (K_q,)

# Colour constants:
BLACK = (0, 0, 0)
BLUE = (0, 0, 155)
GREEN = (0, 155, 0)
LIGHT_BLUE = (20, 20, 175)
LIGHT_GREEN = (20, 175, 20)
LIGHT_RED = (175, 20, 20)
LIGHT_YELLOW = (175, 175, 20)
RED = (155, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (155, 155, 0)

BORDER_COLOUR = BLUE
BACKGROUND_COLOUR = BLACK
TEXT_COLOUR = WHITE

COLOURS = (BLUE, GREEN, RED, YELLOW)
LIGHT_COLOURS = (LIGHT_BLUE, LIGHT_GREEN, LIGHT_RED, LIGHT_YELLOW)

# Template constants:
BLANK = "."
TEMPLATE_WIDTH = 5
TEMPLATE_HEIGHT = 5

# Shape templates:
S_SHAPE_TEMPLATE = [
    [".....", ".....", "..OO.", ".OO..", "....."],
    [".....", "..O..", "..OO.", "...O.", "....."]
]
Z_SHAPE_TEMPLATE = [
    [".....", ".....", ".OO..", "..OO.", "....."],
    [".....", "..O..", ".OO..", ".O...", "....."]
]
I_SHAPE_TEMPLATE = [
    ["..O..", "..O..", "..O..", "..O..", "....."],
    [".....", ".....", "OOOO.", ".....", "....."]
]
O_SHAPE_TEMPLATE = [
    [".....", ".....", ".OO..", ".OO..", "....."]
]
J_SHAPE_TEMPLATE = [
    [".....", ".O...", ".OOO.", ".....", "....."],
    [".....", "..OO.", "..O..", "..O..", "....."],
    [".....", ".....", ".OOO.", "...O.", "....."],
    [".....", "..O..", "..O..", ".OO..", "....."]
]
L_SHAPE_TEMPLATE = [
    [".....", "...O.", ".OOO.", ".....", "....."],
    [".....", "..O..", "..O..", "..OO.", "....."],
    [".....", ".....", ".OOO.", ".O...", "....."],
    [".....", ".OO..", "..O..", "..O..", "....."]
]
T_SHAPE_TEMPLATE = [
    [".....", "..O..", ".OOO.", ".....", "....."],
    [".....", "..O..", "..OO.", "..O..", "....."],
    [".....", ".....", ".OOO.", "..O..", "....."],
    [".....", "..O..", ".OO..", "..O..", "....."]
]
PIECES = {
    "S": S_SHAPE_TEMPLATE, "Z": Z_SHAPE_TEMPLATE, "J": J_SHAPE_TEMPLATE,
    "L": L_SHAPE_TEMPLATE, "I": I_SHAPE_TEMPLATE, "O": O_SHAPE_TEMPLATE,
    "T": T_SHAPE_TEMPLATE
}


def get_board_boundaries(cell_size, pixels_at_bottom, columns = 10, rows = 20):
    """
    Return the coordinates of the top left corner of a game board given the
    cell size and the number of blank pixel rows at the bottom of the screen.
    """
    screen = pygame.display.get_surface()
    try:
        screen_width, screen_height = screen.get_size()
    except AttributeError:
        screen = pygame.display.set_mode(pygame.display.list_modes()[0])
        screen_width, screen_height = screen.get_size()
    x = (screen_width-columns*cell_size)//2
    y = screen_height-rows*cell_size-pixels_at_bottom
    return x, y


def fit_board_to_screen(blank_horizontal, blank_top, blank_bottom, top = (), left = (), right = (), f = None, min_cell_size = 1, columns = 10, rows = 20):
    """
    Return the maximum cell size for the game board given screen dimensions.
    If it is impossible to fit a game board to the given dimensions, an error
    is raised.
    
    Parameters:
        blank_horizontal: the proportion of the screen's width that must be
            left blank.
        blank_top: the proportion of the screen's height that must be left
            blank at the top.
        blank_bottom: the proportion of the screen's height that must be left
            blank at the bottom.
    
    Keyword Parameters:
        top: the information that appears at the top of the game board;
            defaults to an empty tuple. Elements in top may be "next piece",
            "score", and "level".
        left and right: same as top but for the left and right of the game
            board, respectively. Like top, these default to empty tuples.
        f: the font in which to render information in top, left, and right.
        min_cell_size: the minimum number of pixels to use for the side of a
            box; defaults to 1.
        columns: the number of columns for the game board; defaults to 10,
            which is the standard for Tetris clones.
        rows: the number of rows for the game board; defaults to 20, which is
            the standard for Tetris clones.
    
    Returns:
        cell_size: the maximum cell size given the above parameters.
        x: the pixel coordinate of the left edge of the game board.
        y: the pixel coordinate of the top edge of the game board.
    """
    screen = pygame.display.get_surface()
    try:
        screen_width, screen_height = screen.get_size()
    except AttributeError:
        screen = pygame.display.set_mode(pygame.display.list_modes()[0])
        screen_width, screen_height = screen.get_size()
    
    max_width = int(screen_width-blank_horizontal*screen_width)
    max_height = int(screen_height-blank_top*screen_height-blank_bottom*screen_height)
    
    if any((top, left, right)):
        left_widths = []
        left_heights = []
        right_widths = []
        right_heights = []
        top_widths = []
        top_heights = []
        for to_be_written in ("next piece", "level", "score"):
            if to_be_written in tuple(left)+tuple(right)+tuple(top):
                if to_be_written == "next piece":
                    string_to_write = "next:"
                elif to_be_written == "level":
                    string_to_write = "level: 10"
                else:
                    string_to_write = "score: 100"
                w, h = f.size(string_to_write)
                if to_be_written in left:
                    left_widths.append(w)
                    left_heights.append(h)
                if to_be_written in right:
                    right_widths.append(w)
                    right_heights.append(h)
                if to_be_written in top:
                    top_widths.append(w)
                    top_heights.append(h)
        if left_widths or right_widths:
            # Get the longest string to be accommodated:
            longest = max(left_widths+right_widths)
            max_width = max_width-longest
        if top_heights:
            tallest = max(top_heights)
            max_height = max_height-tallest
    
    if max_width >= max_height:
        # The screen is either square or landscape.
        # Start with the widest possible board and work down until one fits.
        cell_size = max_width//columns
        while cell_size >= min_cell_size:
            if (2+rows)*cell_size <= max_height:
                # This size works.
                break
            else:
                cell_size = cell_size-1
        else:
            raise ValueError(
                "A board cannot be created with the given parameters."
            )
    else:
        # The screen is portrait style.
        # Start with the tallest possible screen:
        cell_size = max_height//(rows+2)
        while cell_size >= min_cell_size:
            if columns*cell_size <= max_width:
                break
            else:
                cell_size = cell_size-1
        else:
            raise ValueError(
                "A board cannot be created with the given parameters."
            )
    
    x, y = get_board_boundaries(
        cell_size,
        screen_height-int(screen_height-(blank_bottom*screen_height)),
        columns, rows
    )
    return cell_size, x, y


def midpoint(p1, p2, round = "down"):
    """
    Get the midpoint between two integers. The round parameter must be
    "up" or "down" in case of ties.
    """
    if p1 <= p2:
        smaller = p1
        larger = p2
    else:
        smaller = p2
        larger = p1
    difference = larger-smaller
    if difference%2 == 0:
        middle = smaller+difference//2
    else:
        if round == "down":
            middle = smaller+difference//2
        elif round == "up":
            middle = smaller+1+difference//2
        else:
            raise ValueError('The round parameter must be "down" or "up".')
    return middle


class Piece:
    """
    Class for Tetromino pieces.
    
    Pieces have the following attributes:
        shape: the Piece's shape specified as a key from PIECES.
        x: its x pixel coordinate on the game board.
        y: its y pixel coordinate on the game board.
        orientation: its orientation, expressed as an index in the Piece's
            PIECES key.
        colour: the Piece's colour, expressed as an index from COLOURS.
    
    Pieces have the following methods (see the related doc strings for
    more detailed descriptions):
        add_to_board: add a piece to a Board-object's state attribute.
        is_valid_position: determine if a Piece's x-y attributes represent a
            valid position.
        legal left: check if moving left by one cell is legal.
        legal_right and legal_down: same as legal_left but for right and down.
        move_left: move a Piece left by one cell.
        move_right and move_down: same as move_left but for right and down.
        move_to_bottom: drop a Piece to the bottom of the game board.
        rotate_clockwise: if legal, rotate a piece clockwise.
        rotate_counterclockwise: if legal, rotate a Piece counterclockwise.
        draw: draw a Piece to the game board.
        draw_as_next_piece: draw the Piece as the next-to-drop piece.
    """
    
    def __init__(self, b, shape = None, orientation = None, colour = None):
        """
        Initialize a Piece object.
        
        The shape, orientation, and colour parameters default to None, in
        which case they are chosen randomly.
        The x and y attributes have default values depending on where pieces
        start and thus cannot be passed as arguments.
        The b parameter must be the GameBoard object on which the piece will
            appear.
        """
        self.x = b.columns//2-TEMPLATE_WIDTH//2
        self.y = NEW_PIECES_START_Y
        if shape == None:
            self.shape = np.random.choice(tuple(PIECES.keys()))
        else:
            self.shape = shape
        if orientation == None:
            self.orientation = np.random.randint(0, len(PIECES[self.shape]))
        else:
            self.orientation = orientation
        if colour == None:
            self.colour = np.random.randint(0, len(COLOURS))
        else:
            self.colour = colour
    
    def add_to_board(self, b):
        """Add the Piece object to the game board (b)."""
        for x in xrange(TEMPLATE_WIDTH):
            for y in xrange(TEMPLATE_HEIGHT):
                # Check if this x-y coordinate needs colour:
                if PIECES[self.shape][self.orientation][y][x] != BLANK:
                    b.state[x+self.x][y+self.y] = self.colour
    
    def is_valid_position(self, b, x_adjustment = 0, y_adjustment = 0):
        """Return True if a Piece's location is valid."""
        valid = True
        for x in xrange(TEMPLATE_WIDTH):
            for y in xrange(TEMPLATE_HEIGHT):
                is_above_board = y+self.y+y_adjustment < 0
                if is_above_board or PIECES[self.shape][self.orientation][y][x] == BLANK:
                    continue
                if not b.is_on_board(x+self.x+x_adjustment, y+self.y+y_adjustment):
                    valid = False
                    break
                if b.state[x+self.x+x_adjustment][y+self.y+y_adjustment] != BLANK:
                    # A piece already occupies this coordinate.
                    valid = False
                    break
        return valid
    
    def legal_left(self, b):
        """
        Return True if moving left, given the board (b), is legal and False
        otherwise.
        """
        return self.is_valid_position(b, x_adjustment = -1)
    
    def legal_right(self, b):
        """
        Return True if moving right, given the board (b), is legal and False
        otherwise.
        """
        return self.is_valid_position(b, x_adjustment = 1)
    
    def legal_down(self, b):
        """
        Return True if moving down, given the board (b), is legal and False
        otherwise.
        """
        return self.is_valid_position(b, y_adjustment = 1)
    
    def move_left(self):
        """
        Move a piece left by one cell. Be sure to check legal_left before
        calling this method.
        """
        self.x = self.x-1
    
    def move_right(self):
        """
        Move a piece right by one cell. Be sure to check legal_right before
        calling this method.
        """
        self.x = self.x+1
    
    def move_down(self):
        """
        Move a piece down by one cell. Be sure to check legal_down before
        calling this method.
        """
        self.y = self.y+1
    
    def move_to_bottom(self, b):
        """Move the piece to the bottom of the game board (b)."""
        for i in xrange(1, b.rows):
            if not self.legal_down(b):
                # The ith row is blocked.
                break
            else:
                self.y = self.y+1
    
    def rotate_clockwise(self, b):
        """
        If legal given the state of the board (b), rotate the piece clockwise.
        If not legal, nothing happens.
        """
        self.orientation = (self.orientation+1)%len(PIECES[self.shape])
        if not self.is_valid_position(b):
            # The rotation is illegal, so reverse it.
            self.orientation = (self.orientation-1)%len(PIECES[self.shape])
    
    def rotate_counterclockwise(self, b):
        """
        If legal given the state of the board (b), rotate the piece
        counterclockwise. If not legal, nothing happens.
        """
        self.orientation = (self.orientation-1)%len(PIECES[self.shape])
        if not self.is_valid_position(b):
            # The rotation is illegal, so reverse it:
            self.orientation = (self.orientation+1)%len(PIECES[self.shape])
    
    def draw(self, b, x_y = ()):
        """
        Draw Piece to the board.
        
        Parameters:
            b: GameBoard object.
        
        Keyword Parameters:
            x_y: optional x-y pixel coordinates at which to draw Piece;
                defaults to an empty tuple, in which case the pixel
                coordinates are obtained from self.x and self.y.
        """
        screen = pygame.display.get_surface()
        try:
            x_coord, y_coord = x_y
        except ValueError:
            x_coord = self.x
            y_coord = self.y
            # Convert to pixels:
            x_coord, y_coord = b.board_to_pixels(x_coord, y_coord)
        shape_to_draw = PIECES[self.shape][self.orientation]
        for x in xrange(TEMPLATE_WIDTH):
            for y in xrange(TEMPLATE_HEIGHT):
                if shape_to_draw[y][x] != BLANK:
                    b.draw_box(
                        x_coord+x*b.cell_size, y_coord+y*b.cell_size,
                        self.colour, format = "pixel"
                    )
    
    def draw_as_next_piece(self, b, f, centre, antialias = True):
        """
        Draw a Piece when it is the next to fall.
        
        Parameters:
            b: a GameBoard object.
            f: pygame.font.Font object in which to render "next:".
            centre: the pixel coordinate at which to centre the "next:" text.
        
        Keyword Parameters:
            antialias: Boolean indicating whether antialiasing is used for
                text rendering; defaults to True.
        """
        screen = pygame.display.get_surface()
        next_surface, next_rect = text.render_string(
            "next:", f, TEXT_COLOUR, BACKGROUND_COLOUR,
            antialiasing = antialias
        )
        next_rect.center = centre
        screen.blit(next_surface, next_rect)
        
        # The next piece will have the same x coordinate as the "next:" text
        # but a different y coordinate.
        piece_coordinates = (centre[0], centre[1]+next_rect.height//2+2)
        self.draw(b, x_y = piece_coordinates)


class GameBoard:
    """
    A class for the Tetromino game board.
    
    Attributes:
        state: a columns by rows multidimensional list that represents the
            game board. Each coordinate in the board array is either BLANK or
            an index from COLOURS.
        top: the pixel coordinate of the top of the board.
        left: the pixel coordinate of the left side of the board.
        cell_size: the size, in pixels, of a cell on the board.
        columns: the number of columns comprising the board; defaults to 10.
        rows: the number of rows comprising the board; defaults to 20.
    
    GameBoard objects have the following methods (see doc strings for more
    details):
        reset: set all of the cels to BLANK.
        is_on_board: check whether a given x-y board coordinate is part of the
            game board.
        is_complete_line: check if a given row on the board is full.
        remove_complete_lines: remove complete lines from GameBoard.state.
        board_to_pixels: convert an x-y coordinate on GameBoard to pixel
            coordinates on the screen.
        draw_box: draw a box to the screen.
        draw: draw the entire board to the screen.
    """
    
    def __init__(self, left, top, cell_size, columns = 10, rows = 20):
        """Initialize a GameBoard object."""
        self.columns = 10
        self.rows = 20
        self.state = []
        for x in xrange(columns):
            column = [BLANK]*rows
            self.state.append(column)
        self.left = left
        self.top = top
        self.cell_size = cell_size
    
    def reset(self):
        """Reset the game board."""
        self.state = []
        for x in xrange(self.columns):
            column = [BLANK]*self.rows
            self.state.append(column)
    
    def is_on_board(self, x, y):
        """Return True if the x-y pair is on the game board."""
        if 0 <= x < self.columns and 0 <= y < self.rows:
            return True
        return False
    
    def is_complete_line(self, y):
        """Return True if Row y is a complete line and False otherwise."""
        for x in xrange(self.columns):
            current_cell = self.state[x][y]
            if current_cell == BLANK:
                # The line is not complete.
                complete = False
                break
        else:
            complete = True
        return complete
    
    def remove_complete_lines(self):
        """Remove lines from GameBoard and return number of lines removed."""
        lines = 0
        y = self.rows-1   # bottom of board
        while y >= 0:
            if self.is_complete_line(y):
                # Remove the complete line and pull higher lines down a row:
                for pull_down_y in xrange(y, 0, -1):
                    for x in xrange(self.columns):
                        self.state[x][pull_down_y] = self.state[x][pull_down_y-1]
                # Set very top line to blank:
                for x in xrange(self.columns):
                    self.state[x][0] = BLANK
                lines = lines+1
            else:
                # This line is not complete.
                y = y-1
        return lines
    
    def board_to_pixels(self, board_x, board_y):
        """Convert board coordinates to pixel coordinates."""
        pixel_x = self.left+board_x*self.cell_size
        pixel_y = self.top+board_y*self.cell_size
        return pixel_x, pixel_y
    
    def draw_box(self, x, y, colour, format = "box"):
        """
        Draw a box (i.e., one quarter of a piece) to the main display surface.
        
        Parameters:
            x: the x coordinate of the to-be-drawn box.
            y: the y coordinate of the to-be-drawn box.
            colour: the colour of the to-be-drawn box, corresponding to an
                index in the COLOURS constant.
        
        Keyword Parameters:
            format: indicates whether x and y are expressed in box ("box") or
                pixel ("pixel") coordinates; defaults to "box".
        """
        # The present function has no effect if colour == BLANK.
        if colour != BLANK:
            assert format == "box" or format == "pixel", 'The format \
parameter must be "box" or "pixel".'
            if format == "box":
                x, y = self.board_to_pixels(x, y)
            screen = pygame.display.get_surface()
            pygame.draw.rect(
                screen, COLOURS[colour],
                (x+1, y+1, self.cell_size-1, self.cell_size-1)
            )
            pygame.draw.rect(
                screen, LIGHT_COLOURS[colour],
                (x+1, y+1, self.cell_size-4, self.cell_size-4)
            )
    
    def draw(self):
        """Draw the entire board to the main display surface."""
        screen = pygame.display.get_surface()
        pygame.draw.rect(
            screen, BORDER_COLOUR, (
                self.left-3, self.top-7, self.columns*self.cell_size+8,
                self.rows*self.cell_size+8
            ), 5
        )
        for column in xrange(self.columns):
            for row in xrange(self.rows):
                self.draw_box(column, row, self.state[column][row])


def calculate_level(score):
    """Get the level associated with a given score."""
    return score//LINES_PER_LEVEL+1


def calculate_fall_frequency(level):
    """Get the piece fall frequency associated with a given level."""
    return BASE_FALL_FREQUENCY-(level*FALL_FREQUENCY_INCREASE_PER_LEVEL)


def draw_status(score, level, score_centre, level_centre, f, antialias = True):
    """
    Draw the player's score and level to the main display surface.
    
    Parameters:
        score: the player's score.
        level: the player's level.
        score_centre: the pixel coordinates on which to centre the player's
            score.
        level_centre: the pixel coordinates at which to centre the player's
            level.
        f: the pygame.font.Font object to use for text rendering.
    
    Keyword Parameters:
        antialias: Boolean indicating whether antialiasing is used in text
            rendering; defaults to True.
    """
    screen = pygame.display.get_surface()
    score_string = "score: {:d}".format(score)
    level_string = "level: {:d}".format(level)
    # Get surfaces and rects:
    score_surface, score_rect = text.render_string(
        score_string, f, TEXT_COLOUR, BACKGROUND_COLOUR,
        antialiasing = antialias
    )
    level_surface, level_rect = text.render_string(
        level_string, f, TEXT_COLOUR, BACKGROUND_COLOUR,
        antialiasing = antialias
    )
    # Position rects:
    score_rect.center = score_centre
    level_rect.centre = level_centre
    screen.blit(score_surface, score_rect)
    screen.blit(level_surface, level_rect)


def distractor(duration, game_font, columns = 10, rows = 20, top_exclude = 0.025, right_exclude = 0.025, bottom_exclude = 0.025, left_exclude = 0.025, antialias = True, instructions = "", continue_instructions = "", finish_instructions = "", instruction_font = None, instruction_line_size = None, continue_font = None, text_colour = WHITE, background_colour = BLACK, split_sentences = False, sentences_end = (".", "!", "?"), sentences_end_exceptions = (), advance_instructions = (K_SPACE,), reverse_instructions = (K_LEFT, K_BACKSPACE,), fall_frequency = 0.3, c = None, fps = 30, sound_file = None, press_to_quit = (K_ESCAPE,), files = (), data_file = None):
    """
    Play Tetromino as a distractor task for a memory experiment.
    
    Parameters:
        duration: the time, in seconds, that the distractor lasts.
        game_font: pygame.font.Font object used to display "next:" during game
            play.
    
    Keyword Parameters:
        columns: the number of columns for the game board; defaults to 10.
        rows: the number of rows for the game board; defaults to 20.
        top_exclude, right_exclude, bottom_exclude, and left_exclude: the
            proportion of the screen from the given side to exclude from game
            play.
        antialias: Boolean indicating whether antialiasing is used for text
            rendering.
        instructions: optional string to pass for instructions appearing prior
            to game play; defaults to an empty string, in which case the
            instruction phase is skipped and the game starts immediately.
        continue_instructions: applies if instructions does not fit on a
            single screen. continue_instructions prompts subjects to press a
            given key to see more of the instructions (defaults to an empty
            string).
        finish_instructions: appears at the end of instructions, prompting
            subjects to press a given key to start playing Tetromino (defaults
            to an empty string).
        instruction_font: pygame.font.Font object in which to display
            instructions; defaults to None, but must be set if instructions
            are displayed.
        instruction_line_size: the line size used with instruction font; if
            not set, instruction_line_size is obtained from instruction_font.
        instruction_font: pygame.font.Font object used for instruction
            rendering; defaults to None, but must be set if instructions are
            displayed.
        continue_font: same as instruction_font but for the continue message;
            if not set, instruction_font is used.
        continue_line_size: same as instruction_line_size but for
            continue_font.
        text_colour: RGB list or tuple for the colour of instruction text;
            defaults to white.
        background_colour: RGB for the colour on which instructions appear;
            defaults to black.
        split_sentences: Boolean indicating whether sentences can be split
            across screens; defaults to False. Note that, even if set to
            False, it is possible for a sentence to exceed a single screen if
            it is too long.
        sentences_end: list or tuple of characters that end a sentence;
            defaults to period, exclamation mark, and question mark.
        sentences_end_exceptions: any characters that should be treated as
            exceptions to sentences_end (e.g., "Dr." is unlikely to end a
            sentence).
        advance_instructions: a list or tuple of keys that advance
            instructions; defaults to the space bar.
        reverse_instructions: keys to move backward through the instructions;
            defaults to the left arrow key and backspace.
        fall_frequency: the rate at which pieces fall; defaults to 0.30.
        c: pygame.time.Clock object to use; defaults to None, in which case
            one is created.
        fps: frames per second; defaults to 30.
        sound_file: an optional sound file to play during game play; defaults
            to None.
        press_to_quit: a list or tuple of keys that close the program;
            defaults to escape. To disable this feature, pass an empty list or
            tuple.
        files: a list or tuple of files to close if the program closes.
        data_file: a file to which to write the subject's results (line total
            and number of losses [i.e., times where the blocks reached the top
            of the game board]). This can be an index in files, a file opened
            for writing, or a string containing the path and name of a
            to-be-created file.
    
    Returns:
        lines: the number of lines completed.
        losses: the number of times the pieces reached the top of the game
            board.
    """
    assert columns > 4 and rows > 4, "The columns and rows variables must \
exceed 4."
    assert fps > 0, "Frame rate (fps) must be positive."
    assert 0 <= top_exclude+bottom_exclude < 1, "The sum of top_exclude and \
bottom_exclude must be between 0 and 1."
    assert 0 <= left_exclude+right_exclude < 1, "The sum of left_exclude and \
right_exclude must be between 0 and 1."
    lines = 0
    losses = 0
    window = pygame.display.get_surface()
    try:
        window_width, window_height = window.get_size()
    except AttributeError:
        window = pygame.display.set_mode(pygame.display.list_modes()[0])
        window_width, window_height = window.get_size()
    allowed_width = window_width-(left_exclude+right_exclude)*window_width
    allowed_height = window_height-(left_exclude+right_exclude)*window_height
    pygame.mouse.set_visible(False)
    # Get the optimal board size:
    cell_size, x_margin, top_margin = fit_board_to_screen(
        left_exclude+right_exclude, top_exclude, bottom_exclude,
        right = ("next piece"), f = game_font, columns = columns, rows = rows
    )
    # "next:" appears before the upcoming piece.
    next_string = "next:"
    next_width, next_height = game_font.size(next_string)
    x_next = midpoint(
        window_width-int(right_exclude*window_width),
        x_margin+columns*cell_size
    )
    y_next = top_margin+int(0.05*rows*cell_size)
    next_coordinates = (x_next, y_next)
    game_board = GameBoard(
        x_margin, top_margin, cell_size, columns = columns, rows = rows
    )
    falling_piece = Piece(game_board)
    next_piece = Piece(game_board)
    if instructions:
        text.display_text_until_keypress(
            instructions, instruction_font, text_colour, background_colour,
            proportion_width = left_exclude+right_exclude,
            proportion_height = top_exclude+bottom_exclude,
            main_line = instruction_line_size,
            break_sentences = split_sentences,
            sentence_terminators = sentences_end,
            terminator_exceptions = sentences_end_exceptions,
            bottom_message = continue_instructions,
            bottom_font = continue_font, bottom_line = continue_line_size,
            advance_keys = advance_instructions,
            reverse_keys = reverse_instructions, quit_keys = press_to_quit,
            ticker = c, frame_rate = fps, files = files
        )
    if sound_file:
        pygame.mixer.music.load(sound_file)
        pygame.mixer.music.play(-1, 0.0)
    # Set directional and time variables:
    moving_down = False
    moving_left = False
    moving_right = False
    last_move_down_time = time.time()
    last_move_sideways_time = time.time()
    last_fall_time = time.time()
    # Get the start and finish times:
    start_time = time.time()
    finish_time = start_time+duration
    while time.time() < finish_time:
        if not falling_piece:
            falling_piece = next_piece
            next_piece = Piece(game_board)
            last_fall_time = time.time()
            # Check if the new piece fits:
            fits = falling_piece.is_valid_position(game_board)
            if not fits:
                # The player loses.
                losses = losses+1
                game_board.reset()
                moving_down = False
                moving_left = False
                moving_right = False
                last_move_down_time = time.time()
                last_move_sideways_time = time.time()
                last_fall_time = time.time()
                falling_piece = Piece(game_board)
                next_piece = Piece(game_board)
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key in press_to_quit):
                generic.terminate(files)
            elif event.type == KEYUP:
                if event.key in MOVE_LEFT:
                    # The player has just stopped moving the piece left.
                    moving_left = False
                elif event.key in MOVE_RIGHT:
                    moving_right = False
                elif event.key in MOVE_DOWN:
                    moving_down = False
            elif event.type == KEYDOWN:
                if event.key in MOVE_LEFT and falling_piece.legal_left(game_board):
                    falling_piece.move_left()
                    moving_left = True
                    moving_right = False
                    last_move_sideways_time = time.time()
                elif event.key in MOVE_RIGHT and falling_piece.legal_right(game_board):
                    falling_piece.move_right()
                    moving_right = True
                    moving_left = False
                    last_move_sideways_time = time.time()
                elif event.key in ROTATE_CLOCKWISE:
                    falling_piece.rotate_clockwise(game_board)
                elif event.key in ROTATE_COUNTERCLOCKWISE:
                    falling_piece.rotate_counterclockwise(game_board)
                elif event.key in MOVE_DOWN and falling_piece.legal_down(game_board):
                    moving_down = True
                    falling_piece.move_down()
                    last_move_down_time = time.time()
                elif event.key in MOVE_TO_BOTTOM:
                    moving_left = False
                    moving_right = False
                    moving_down = False
                    falling_piece.move_to_bottom(game_board)
            else:
                # This is an event without an effect.
                # This block may be unnecessary; I read somewhere that it's
                # needed to clear the event from the queue.
                pass
        if (moving_left or moving_right) and time.time()-last_move_sideways_time > MOVE_SIDEWAYS_FREQUENCY:
            # If legal, it's time for falling_piece to move again.
            if moving_left and falling_piece.legal_left(game_board):
                falling_piece.move_left()
            if moving_right and falling_piece.legal_right(game_board):
                falling_piece.move_right()
            last_move_sideways_time = time.time()
        if moving_down and time.time()-last_move_down_time > MOVE_DOWN_FREQUENCY and falling_piece.legal_down(game_board):
            falling_piece.move_down()
            last_move_down_time = time.time()
        if time.time()-last_fall_time > fall_frequency:
            if not falling_piece.legal_down(game_board):
                # falling_piece has landed.
                falling_piece.add_to_board(game_board)
                new_lines = game_board.remove_complete_lines()
                lines = lines+new_lines
                # falling_piece has landed, so:
                falling_piece = None
            else:
                # falling_piece has not landed, so move it down:
                falling_piece.move_down()
                last_fall_time = time.time()
        # Draw everything to window:
        window.fill(background_colour)
        game_board.draw()
        next_piece.draw_as_next_piece(
            game_board, game_font, next_coordinates, antialias = antialias
        )
        if falling_piece:
            # Draw the currently falling piece:
            falling_piece.draw(game_board)
        pygame.display.update()
        try:
            c.tick(fps)
        except AttributeError:
            # Create the clock:
            c = pygame.time.Clock()
            c.tick(fps)
    window.fill(background_colour)
    if sound_file:
        pygame.mixer.music.stop()
    
    if data_file:
        # lines and losses are written to a file.
        data_to_write = "lines = {:d}\nlosses = {:d}".format(lines, losses)
        try:
            # data_file might already be an opened file.
            data_file.write(data_to_write)
        except AttributeError:
            # data_file is a string or an index in files.
            try:
                data_file = files[data_file]
                data_file.write(data_to_write)
            except TypeError:
                # data_file is a string.
                # Check if the strung file already exists:
                if os.path.isfile(data_file):
                    # To prevent overwriting, append to the end of data_file.
                    data_file = open(data_file, "a")
                else:
                    data_file = open(data_file, "w")
                data_file.write(data_to_write)
                data_file.close()
    return lines, losses

