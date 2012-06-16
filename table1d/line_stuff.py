#!/usr/bin/env python

import sys
from planar import Vec2
from planar.line import LineSegment
from planar.line import Line

def get_line_features(lmk):
       ps = [Vec2(0, 0), Vec2(1, 0)]
       ls = LineSegment.from_points(ps)

       dist_start = lmk.distance_to(ls.start)
       dist_end = lmk.distance_to(ls.end)
       dist_mid = lmk.distance_to(ls.mid)

       tl = Line.from_normal(ls.direction, ls.start.x)
       dir_start = -1 if tl.point_left(lmk) else 1

       tl = Line.from_normal(ls.direction, ls.end.x)
       dir_end = -1 if tl.point_left(lmk) else 1

       tl = Line.from_normal(ls.direction, ls.mid.x)
       dir_mid = -1 if tl.point_left(lmk) else 1

       return {
               'dist_start': dist_start,
               'dist_mid': dist_mid,
               'dist_end': dist_end,
               'dir_start': dir_start,
               'dir_mid': dir_mid,
               'dir_end': dir_end,
              }


if __name__ == '__main__':
       lmk = Vec2(float(sys.argv[1]), 0)

       f = get_line_features(lmk)

       print 'dist_start = {dist_start}, dist_end = {dist_end}, dist_mid = {dist_mid}'.format(**f)
       print 'dir_start = {dir_start}, dir_end = {dir_end}, dir_mid = {dir_mid}'.format(**f)