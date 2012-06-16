#!/usr/bin/env python

from tabledb import *

s = set()
for c in Context.query.filter_by(landmark_location=100,
                                 relation='is-adjacent',
                                 degree=2):
    for w in c.words:
        if w.pos not in ('DT',):
            print c.location, w.word, w.pos
            s.add(c.location)

print len(s)
