#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import curses


def testHV(stdscr):
    '''

    - 1d 3d 1w 2w 1mon 2mon 4mon 0.5y 1y
        A Average
        P Parksinson1980
        G GarmaanKlass
        Y YangZhang2000
        E ewma

    	1D					3D					1W					2W
	avg	PK80	GK	YZ00	EWMA	avg	PK80	GK	YZ00	EWMA	avg	PK80	GK	YZ00	EWMA	avg	PK80	GK	YZ00	EWMA
FUTU
    '''
    periods     = [ '1d',  '3d',  '1w',  '2w',  '1mon',  '2mon',  '4mon',  '0.5y',  '1y', ]
    hvAlgrithms = [ 'Average',  'Parksinson1980',  'GarmaanKlass',  'YangZhang2000',  'Ewma', ]


    headerPerPeriod =  '|'  + ' '.join([ a[0]  for a in hvAlgrithms])
    headerPerPeriod +=  ' '
    nHeaderPerPeriod =  len(headerPerPeriod)
    line = 0
    stdscr.addstr(line,0, '\t'.join([ f'{a[0]}:{a} '  for a in hvAlgrithms]))
    line += 1
    symbolPeriod = 'Symbol\Period'
    nSymbolPeriod = len('Symbol\Period  ')
    stdscr.addstr(line,  0, symbolPeriod)
    stdscr.addstr(line+1,0, 'Symbol\HVRatio')
    for p in range(0, len(periods)):
        x  = nSymbolPeriod + p *nHeaderPerPeriod
        stdscr.addstr(line,x, periods[p])
        stdscr.addstr(line+1,x, headerPerPeriod)
        pass
    line += 1
    stdscr.refresh()
    stdscr.getch()
    pass


def testColor(pad, bgcolor):
    for i in range(0,int(curses.COLORS)):
        x,y  = (i %16) , int(i/16)
        #curses.init_color(250, 1000, 0, 0)
        if i > 0:
            curses.init_pair(i, i, bgcolor)
        pad.addstr(y,   8*x, f'{i} ', curses.color_pair(i))
    pass

def demo1(screen):
    screen.clear()
    curses.curs_set(0)
    pad1  = curses.newpad(16, 128)
    testColor(pad1, curses.COLOR_WHITE)
    pad1.refresh(0,0,0,0, 16,128)
    screen.getch()
    return
    pad2  = curses.newpad(16, 128)
    testColor(pad2, curses.COLOR_WHITE)
    pad2.refresh(0,0,16,0, 16,128)
    #screen.refresh()
    pass


def demo(screen):
    # save the colors and restore it later
    save_colors = [curses.color_content(i) for i in range(curses.COLORS)]
    curses.curs_set(0)
    curses.start_color()

    # use 250 to not interfere with tests later
    curses.init_color(250, 1000, 0, 0)
    curses.init_pair(250, 250, curses.COLOR_BLACK)
    curses.init_color(251, 0, 1000, 0)
    curses.init_pair(251, 251, curses.COLOR_BLACK)

    screen.addstr(0, 20, 'Test colors for r,g,b = {0, 200}\n',
                  curses.color_pair(250) | curses.A_BOLD | curses.A_UNDERLINE)
    i = 0
    for r in (0, 200):
        for g in (0, 200):
            for b in (0, 200):
                i += 1
                curses.init_color(i, r, g, b)
                curses.init_pair(i, i, curses.COLOR_BLACK)
                screen.addstr('{},{},{}  '.format(r, g, b), curses.color_pair(i))

    screen.addstr(3, 20, 'Test colors for r,g,b = {0..1000}\n',
                  curses.color_pair(251) | curses.A_BOLD | curses.A_UNDERLINE)
    for r in range(0, 1001, 200):
        for g in range(0, 1001, 200):
            for b in range(0, 1001, 200):
                i += 1
                curses.init_color(i, r, g, b)
                curses.init_pair(i, i, curses.COLOR_BLACK)
                # screen.addstr('{},{},{} '.format(r, g, b), curses.color_pair(i))
                screen.addstr('test ', curses.color_pair(i))

    screen.getch()
    # restore colors
    for i in range(curses.COLORS):
        curses.init_color(i, *save_colors[i])

    screen.getch()


if __name__ == '__main__':
    curses.wrapper(testHV)
