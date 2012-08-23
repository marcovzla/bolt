#!/usr/bin/env python
from __future__ import division

from sentence_from_location import (
    generate_sentence,
    accept_correction,
    Point
)

from table2d.run import construct_training_scene
from table2d.landmark import Landmark, PointRepresentation
from nltk.metrics.distance import edit_distance
from planar import Vec2


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--location', type=Point, required=True)
    parser.add_argument('--consistent', action='store_true')
    args = parser.parse_args()

    scene, speaker = construct_training_scene()
    meaning, sentence = generate_sentence(args.location.xy, args.consistent, scene, speaker)

    print 'sentence:', sentence

    trajector = Landmark( 'point', PointRepresentation(Vec2(args.location.x, args.location.y)), None, Landmark.POINT )
    landmark, relation = meaning.args[0], meaning.args[3]
    head_on = speaker.get_head_on_viewpoint(landmark)
    all_descs = speaker.get_all_meaning_descriptions(trajector, scene, landmark, relation, head_on, 1)

    distances = []
    for desc in all_descs:
        distances.append([edit_distance( sentence, desc ), desc])

    distances.sort()
    print distances

    correction = distances[0][1]
    accept_correction( meaning, correction)
