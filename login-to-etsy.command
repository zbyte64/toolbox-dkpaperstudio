#!/bin/sh
here="`dirname \"$0\"`"
cd "$here" 
poetry run authorize-etsy
