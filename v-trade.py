#!/usr/bin/env python3
# coding=utf-8
#!/home/tops/bin/python2.7
import pprint
import sys
#reload(sys)
#sys.setdefaultencoding('utf8')
import os
curDir = os.path.abspath(os.path.dirname(__file__))
sys.path.append("{}/lib".format(curDir))

import time
import logging
import logging.handlers
import traceback
import getopt
import signal,code
import shutil
import random
import getpass

#from lib import click

import click



@click.group()
@click.option('-g', '--global_conf',  default='',help='Global hocon conf, need  _global section')
def cli(global_conf):
    """
    cd $ICLOUD/en_vocabulary/tools/ROOT_PART_INPUTS/ &&  ../voc_tool/voc_tool.py word_roots_proc  -s ./suffix.csv  -y ./youdict.csv   -l ./learnthat.csv  -a ./academic.csv  -m ./mwvb.csv

    \b
    cd $ICLOUD/en_vocabulary/tools/ROOT_PART_INPUTS/ &&  ../voc_tool/voc_tool.py word_roots_proc  -s ./suffix.csv  -y ./youdict.csv   -l ./learnthat.csv  -a ./academic.csv  -m ./mwvb.csv
    """
    # click.echo('Debug is %s' % debug)
    pass

@click.command()
def sync():
    click.echo('Synching')


def versionCheck():
    assert sys.version_info.major == 3 and sys.version_info.minor >= 9

def debugToConsole(sig, frame):
    """Interrupt running process, and provide a python prompt for
    interactive debugging."""
    d = {'_frame': frame}  # Allow access to frame object.
    d.update(frame.f_globals)  # Unless shadowed by global
    d.update(frame.f_locals)

    i = code.InteractiveConsole(d)
    message = "Signal received : entering python shell.\nTraceback:\n"
    message += ''.join(traceback.format_stack(frame))
    i.interact(message)
    pass


if __name__ == '__main__':
    os.umask(0o0022)
    versionCheck()
    showUsage = False
    signal.signal(signal.SIGUSR1, debugToConsole)
    # add workflow sub command
    #from lib.wordlist import WordList
    #cli.add_command(WordList.merge, 'wordlist_merge')
    #cli.add_command(WordList.word_roots_proc)
    #cli.add_command(WordList.reading_to_words)
    from  pairs_trading.Cointegrate import cointegrate
    cli.add_command(cointegrate)
    cli()
    sys.exit(0)
