#!/bin/sh
here="`dirname \"$0\"`"
cd "$here" 
poetry run package-products
