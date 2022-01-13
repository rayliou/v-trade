#!/usr/bin/env python3
# coding=utf-8
#!/home/tops/bin/python2.7

'''
- pip3 install Flask

'''
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
#@click.option('-g', '--global_conf',  default='',help='Global hocon conf, need  _global section')
def cli():
    """
    FLASK_APP=WebMain flask run
    \b
    """
    # click.echo('Debug is %s' % debug)
    pass



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


from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/')
def hello():
    return '<H1>Hello World </H1>'

@app.route('/pair')
def pair():
    return '<H1>Hello World </H1>'





if __name__ == '__main__':
    socketio.run(app)
    os.umask(0o0022)
    versionCheck()
    signal.signal(signal.SIGUSR1, debugToConsole)
    # add workflow sub command
    #from lib.wordlist import WordList
    #cli.add_command(WordList.merge, 'wordlist_merge')
    #cli.add_command(WordList.word_roots_proc)
    #cli.add_command(WordList.reading_to_words)
    cli()
    sys.exit(0)