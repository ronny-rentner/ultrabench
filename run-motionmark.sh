#!/bin/bash

BROWSER=chrome
TYPE=motionmark

DIR=`dirname $0`
cd $DIR

DIR_OUTPUT=$DIR/out/$BROWSER/
mkdir -p $DIR_OUTPUT

TIMESTAMP=`date +%Y-%m-%d_%H-%M-%S`
OUT=$DIR_OUTPUT/$TYPE-$TIMESTAMP.json

DRIVER=/usr/bin/chromedriver
DRIVER=~/.chromedriver-helper/106.0.5249.61/linux64/chromedriver

python3 motionmark.py  \
    -b $BROWSER        \
    -e $DRIVER         \
    -o $OUT

    #-a 'enable-features=CanvasOopRasterization'     \
