#!/usr/bin/env python
# coding: utf-8

from __future__ import division

from sqlalchemy import create_engine, and_, or_
from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship, backref, aliased, sessionmaker
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.ext.declarative import _declarative_constructor

from utils import force_unicode





### configuration ###

db_url = 'sqlite:///table2d.db'
echo = False





### utilities ###

# as seen on http://stackoverflow.com/a/1383402
class ClassProperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

def create_all():
    """create all tables"""
    Base.metadata.create_all(engine)






### setting up sqlalchemy stuff ###

engine = create_engine(db_url, echo=echo)
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

class Base(object):
    # if you have a __unicode__ method
    # you get __str__ and __repr__ for free!
    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self)

    # figure out your own table name
    @declared_attr
    def __tablename__(cls):
        # table names should be plural
        return cls.__name__.lower() + 's'

    # easy access to `Query` object
    @ClassProperty
    @classmethod
    def query(cls):
        return session.query(cls)

    # like in elixir
    @classmethod
    def get_by(cls, **kwargs):
        return cls.query.filter_by(**kwargs).first()

    # like in django
    @classmethod
    def get_or_create(cls, defaults={}, **kwargs):
        obj = cls.get_by(**kwargs)
        if not obj:
            kwargs.update(defaults)
            obj = cls(**kwargs)
        return obj

    def _constructor(self, **kwargs):
        _declarative_constructor(self, **kwargs)
        # add self to session
        session.add(self)

Base = declarative_base(cls=Base, constructor=Base._constructor)





### models start here ###

class Location(Base):
    id = Column(Integer, primary_key=True)

    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)

    # has many
    words = relationship('Word', backref='location')
    productions = relationship('Production', backref='location')

    def __unicode__(self):
        return u'(%s,%s)' % (self.x, self.y)

class Word(Base):
    id = Column(Integer, primary_key=True)

    word = Column(String, nullable=False)
    pos = Column(String, nullable=False)

    # belongs to
    parent_id = Column(Integer, ForeignKey('productions.id'))
    location_id = Column(Integer, ForeignKey('locations.id'))

    def __unicode__(self):
        return force_unicode(self.word)

    @classmethod
    def get_words(cls, pos=None, lmk=None, rel=None):
        q = cls.query.join(Production)

        if pos is not None:
            q = q.filter(Word.pos==pos)

        if lmk is not None:
            q = q.filter(Production.landmark==lmk)

        if rel is not None:
            q = q.filter(Production.relation==rel)

        return q

class Production(Base):
    id = Column(Integer, primary_key=True)

    lhs = Column(String, nullable=False)
    rhs = Column(String, nullable=False)

    # semantic content
    landmark = Column(Integer)
    relation = Column(String)

    # belongs_to
    parent_id = Column(Integer, ForeignKey('productions.id'))
    location_id = Column(Integer, ForeignKey('locations.id'))

    # has many
    words = relationship('Word', backref='parent')
    productions = relationship('Production', backref=backref('parent', remote_side=[id]))

    def __unicode__(self):
        return u'%s -> %s' % (self.lhs, self.rhs)

    @classmethod
    def get_productions(cls, lhs=None, parent=None, lmk=None, rel=None):
        parent_prod = aliased(Production)
        q = cls.query.join(parent_prod, Production.parent)

        if lhs is not None:
            q = q.filter(Production.lhs==lhs)
        
        if lmk is not None:
            q = q.filter(Production.landmark==lmk)
        
        if rel is not None:
            q = q.filter(Production.relation==rel)
        
        if parent is not None:
            q = q.filter(parent_prod.lhs==parent)
        
        return q





if __name__ == '__main__':
    engine.echo = True
    create_all()
