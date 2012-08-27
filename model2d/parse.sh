#!/bin/bash

../bllip-parser/first-stage/PARSE/parseIt -l399 -N1 ../bllip-parser/first-stage/DATA/EN/ $* | perl -ne "print unless /^\s*$/"
