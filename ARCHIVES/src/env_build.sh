#!/usr/bin/env zsh

#https://virtualenv.pypa.io/en/latest/user_guide.html#introduction

ML_DIR=ML_ENV
rm -fr $ML_DIR
#virtualenv $ML_DIR -p /usr/local/bin/python3.9
virtualenv $ML_DIR -p '/usr/local/Cellar/python@3.8/3.8.12_1/bin/python3'
source $ML_DIR/bin/activate
pip install plaidml-keras plaidbench
plaidml-setup
#plaidbench keras mobilenet

