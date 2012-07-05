#!/usr/bin/env python

import re
import os
import csv
import sys
import random
import tempfile
import subprocess
from cStringIO import StringIO
from table2d.speaker import Speaker
from planar import Vec2, BoundingBox
from table2d.landmark import RectangleRepresentation, Scene, Landmark



def parse_sentences(ss):
    """parse sentences with the charniak parser"""
    # create a temporary file and write the sentence in it
    temp = tempfile.NamedTemporaryFile()
    for s in ss:
        temp.write('<s> %s </s>\n' % s)
    temp.flush()
    # get into the charniak parser directory
    os.chdir('bllip-parser')
    # call the parser
    proc = subprocess.Popen(['./parse.sh', temp.name],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    # capture output
    output = proc.communicate()[0]
    # return to parent directory
    os.chdir('..')
    # get rid of temporary file
    temp.close()
    # return the parse trees
    return output.splitlines()

    

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--num-sentences', '-n', action='store', dest='num_sentences', type=int, default=1)
    args = parser.parse_args()



    print 'building scene...'
    sys.stdout.flush()

    ### setup scene ###
    speaker = Speaker(Vec2(5.5,4.5))
    scene = Scene(3)

    table = Landmark('table',
                 RectangleRepresentation(rect=BoundingBox([Vec2(5,5), Vec2(6,7)]), descriptions=['table', 'table surface']),
                 None,
                 ['table', 'table surface'])

    obj1 = Landmark('obj1',
                 RectangleRepresentation(rect=BoundingBox([Vec2(5,5), Vec2(5.1,5.1)]), descriptions=['cup']),
                 None,
                 ['cup'])

    obj2 = Landmark('obj2',
                 RectangleRepresentation(rect=BoundingBox([Vec2(5.5,6), Vec2(5.6,6.1)]), descriptions=['bottle']),
                 None,
                 ['bottle'])

    obj3 = Landmark('obj3',
                 RectangleRepresentation(rect=BoundingBox([Vec2(4.5,4.5), Vec2(4.8,4.8)]), descriptions=['chair']),
                 None,
                 ['chair'])

    scene.add_landmark(table)
    scene.add_landmark(obj1)
    scene.add_landmark(obj2)
    scene.add_landmark(obj3)



    print 'generating sentences...'
    sys.stdout.flush()

    # capture stdout because `Speaker.describe` doesn't return the sentence
    # it only prints it
    real_stdout = sys.stdout
    sys.stdout = fake_stdout = StringIO()

    # generate as many random sentences as requested in the command line
    for i in xrange(args.num_sentences):
        location = Vec2(random.random()+5, random.random()*2+5)
        speaker.describe(location, scene)

    # restore stdout
    sys.stdout = real_stdout



    print 'reading output...'
    sys.stdout.flush()

    # get locations and sentences
    locxs = []
    locys = []
    sents = []
    for line in fake_stdout.getvalue().splitlines():
        m = re.match(r'^Vec2\((?P<x>[0-9.]+), (?P<y>[0-9.]+)\); (?P<sent>.+)$', line)
        if m:
            locxs.append(float(m.group('x')))
            locys.append(float(m.group('y')))
            sents.append(m.group('sent'))



    print 'parsing sentences...'
    sys.stdout.flush()

    # parse sentences
    parses = parse_sentences(sents)



    print 'writing csv...'
    sys.stdout.flush()

    # write csv file
    with open('sentences.csv', 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(['loc_x', 'loc_y', 'sentence', 'parsetree'])
        for row in zip(locxs, locys, sents, parses):
            writer.writerow(row)
