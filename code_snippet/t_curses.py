#!/usr/bin/env python3

import sys,time
import curses
from curses import wrapper

def testPad(stdscr):
    pad = curses.newpad(100, 100)
    # These loops fill the pad with letters; addch() is
    # explained in the next section
    for y in range(0, 99):
        for x in range(0, 99):
            pad.addch(y,x, ord('a') + (x*x+y*y) % 26)

    # Displays a section of the pad in the middle of the screen.
    # (0,0) : coordinate of upper-left corner of pad area to display.
    # (5,5) : coordinate of upper-left corner of window area to be filled
    #         with pad content.
    # (20, 75) : coordinate of lower-right corner of window area to be
    #          : filled with pad content.
    pad.addstr( 0,1, 'blink', curses.A_BLINK)
    pad.addstr( 1,1, 'bold', curses.A_BOLD)
    pad.addstr( 2,1, 'dim', curses.A_DIM)
    pad.addstr( 3,1, 'A_STANDOUT', curses.A_STANDOUT)
    pad.addstr( 4,1, 'A_UNDERLINE', curses.A_UNDERLINE)
    pad.addstr( 5,2, 'curses.A_REVERSE', curses.A_REVERSE)
    pad.addstr( 6,2, 'color 7', curses.color_pair(7))
    pad.addstr( 7,2, 'color 5', curses.color_pair(2))

    for i in range(0, 50):
        pad.addstr( 10+i, 0,f'pair_content {curses.pair_content(i)}' )

    pad.refresh( 0,0, 5,5, 40,75)
    pass

def main(stdscr):
    curses.start_color()
    # Clear screen
    ncols, nlines = 8, 3
    stdscr.clear()
    stdscr.addstr(2,3,'2222222')
    stdscr.addstr(0,1,f"has color {'TRUE' if  curses.has_colors() else 'FALSE'  } "
            f"can change color: {curses.can_change_color()}  "
            f"colors:{curses.COLORS}"
            )


    # This raises ZeroDivisionError when i == 10.
    #for i in range(0, 11):
    #    v = i-10
    #    stdscr.addstr(i, 0, '10 divided by {} is {}'.format(v, 10/v))

    stdscr.refresh()



    begin_x = 20; begin_y = 7
    height = 5; width = 40
    #win = curses.newwin(height, width, begin_y, begin_x)
    testPad(stdscr)
    stdscr.getkey()



wrapper(main)
