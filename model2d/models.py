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
    productions = relationship('Production', backref=backref('parent',
                                                             remote_side=[id]))

    def __unicode__(self):
        return u'%s -> %s' % (self.lhs, self.rhs)

    @classmethod
    def get_productions(cls, lhs=None, parent=None, lmk=None, rel=None):
        q = cls.query

        if lhs is not None:
            q = q.filter(Production.lhs==lhs)
        
        if lmk is not None:
            q = q.filter(Production.landmark==lmk)
        
        if rel is not None:
            q = q.filter(Production.relation==rel)
        
        if parent is not None:
            q = q.join(Production.parent, aliased=True).\
                  filter(Production.lhs==parent).\
                  reset_joinpoint()
        
        return q

class WordCPT(Base):
    id = Column(Integer, primary_key=True)

    word = Column(String, nullable=False)
    prob = Column(Float)

    # conditioned on
    pos = Column(String)
    lmk = Column(Integer)
    rel = Column(String)

    fields = ['pos', 'lmk', 'rel']

    def __unicode__(self):
        given = [(f,getattr(self,f)) for f in self.fields if getattr(self,f) is not None]
        given = ', '.join(u'%s=%r' % g for g in given)
        if given:
            return u'Pr(word=%r | %s) = %s' % (self.word, given, self.prob)
        else:
            return u'Pr(word=%r) = %s' % (self.word, self.prob)

    @classmethod
    def calc_prob(cls, word, **given):
        """calculates conditional probability"""
        wp = WordCPT(word=word, **given)
        q = Word.get_words(**given)
        const = q.count()  # normalizing constant
        if const:
            wp.prob = q.filter(Word.word==word).count() / const
        return wp

    @classmethod
    def get_prob(cls, word, **given):
        """gets probability from db"""
        params = dict((f,None) for f in cls.fields)
        params.update(given)
        return cls.query.filter_by(word=word, **given).one()

    @classmethod
    def probability(cls, word, **given):
        try:
            wp = cls.get_prob(word=word, **given)
        except:
            wp = cls.calc_prob(word=word, **given)
            session.commit()
        return wp.prob

class ExpansionCPT(Base):
    id = Column(Integer, primary_key=True)

    rhs = Column(String, nullable=False)
    prob = Column(Float)

    # conditioned on
    lhs = Column(String)
    parent = Column(String)
    lmk = Column(Integer)
    rel = Column(String)

    fields = ['lhs', 'parent', 'lmk', 'rel']

    def __unicode__(self):
        given = [(f,getattr(self,f)) for f in self.fields if getattr(self,f) is not None]
        given = ', '.join(u'%s=%r' % g for g in given)
        if given:
            return u'Pr(rhs=%r | %s) = %s' % (self.rhs, given, self.prob)
        else:
            return u'Pr(rhs=%r) = %s' % (self.rhs, self.prob)

    @classmethod
    def calc_prob(cls, rhs, **given):
        """calculates conditional probability"""
        ep = ExpansionCPT(rhs=rhs, **given)
        q = Production.get_productions(**given)
        const = q.count()  # normalizing constant
        if const:
            ep.prob = q.filter_by(rhs=rhs).count() / const
        return ep

    @classmethod
    def get_prob(cls, rhs, **given):
        """gets probability stored in db"""
        params = dict((f, None) for f in cls.fields)
        params.update(given)
        return cls.query.filter_by(rhs=rhs, **params).one()

    @classmethod
    def probability(cls, rhs, **given):
        try:
            ep = cls.get_prob(rhs=rhs, **given)
        except:
            ep = cls.calc_prob(rhs=rhs, **given)
            session.commit()
        return ep.prob







if __name__ == '__main__':
    engine.echo = True
    create_all()
