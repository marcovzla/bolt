#!/usr/bin/env python

from __future__ import division

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.ext.declarative import _declarative_constructor





### configuration ###

db_url = 'sqlite:///table1d.db'
echo = False
encoding = 'utf-8'





### utilities ###

# as seen on http://stackoverflow.com/a/1383402
class ClassProperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

def create_all():
    """create all tables"""
    Base.metadata.create_all(engine)

def force_unicode(s, encoding=encoding, errors='strict'):
    """convert `s` to unicode or die trying"""
    if isinstance(s, unicode):
        return s
    elif hasattr(s, '__unicode__'):
        return unicode(s)
    elif isinstance(s, str):
        return s.decode(encoding, errors)
    else:
        return str(s).decode(encoding, errors)





### setting up sqlalchemy stuff ###

engine = create_engine(db_url, echo=echo)
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

# stuff that every model needs
class Base(object):
    # everybody needs an identifier
    id = Column(Integer, primary_key=True)

    # give us a `__unicode__` method
    # and we will give you `__str__` and `__repr__` for free!
    def __str__(self):
        return unicode(self).encode(encoding)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self)

    # figure out your own table name
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    # easy access to the `Query` object
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

def _base_constructor(self, **kwargs):
    # first let `_declarative_constructor` do its job
    _declarative_constructor(self, **kwargs)
    # then add `self` to `session`
    session.add(self)

Base = declarative_base(cls=Base, constructor=_base_constructor)





### our models start here ###

class Context(Base):
    # we probably don't need the location
    # but better safe than sorry
    location = Column(Float, nullable=False)
    landmark = Column(Float, nullable=False, index=True)
    landmark_name = Column(String)
    relation = Column(String, nullable=False, index=True)
    degree = Column(Integer, nullable=False, index=True)
    lmk_prob = Column(Float)
    reldeg_prob = Column(Float)
    # has many
    words = relationship('Word', backref='context')
    phrases = relationship('Phrase', backref='context')

    def __unicode__(self):
        return u'(loc=%s lmk=%s rel=%s deg=%s)' % (
                self.location, self.landmark,
                self.relation, self.degree)

class Word(Base):
    word = Column(String, nullable=False)
    pos = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False, index=True)
    phrase = Column(String, nullable=False, index=True)
    # belongs to
    context_id = Column(Integer, ForeignKey('context.id'))

    def __unicode__(self):
        return force_unicode(self.word)

    @classmethod
    def get_words(cls, pos=None, role=None, phr=None, lmk=None, rel=None, deg=None):
        q = cls.query.join(Context)
        if pos is not None:
            q = q.filter(Word.pos==pos)
        if role is not None:
            q = q.filter(Word.role==role)
        if phr is not None:
            q = q.filter(Word.phrase==phr)
        if lmk is not None:
            q = q.filter(Context.landmark==lmk)
        if rel is not None:
            q = q.filter(Context.relation==rel)
        if deg is not None:
            q = q.filter(Context.degree==deg)
        return q

class Phrase(Base):
    expansion = Column(String)
    role = Column(String)
    parent = Column(String, index=True)
    # belongs to
    context_id = Column(Integer, ForeignKey('context.id'))

    def __unicode__(self):
        return force_unicode(self.expansion)

    @classmethod
    def get_expansions(cls, role=None, parent=None, lmk=None, rel=None, deg=None):
        q = cls.query.join(Context)
        if role is not None:
            q = q.filter(Phrase.role==role)
        if parent is not None:
            q = q.filter(Phrase.parent==parent)
        if lmk is not None:
            q = q.filter(Context.landmark==lmk)
        if rel is not None:
            q = q.filter(Context.relation==rel)
        if deg is not None:
            q = q.filter(Context.degree==deg)
        return q

class Pword(Base):
    word = Column(String)
    prob = Column(Float)

    # conditioned on
    pos = Column(String)    # Word.pos
    phr = Column(String)    # Word.phrase
    role = Column(String)   # Word.role
    lmk = Column(Float)     # Context.landmark
    rel = Column(String)    # Context.relation
    deg = Column(String)    # Context.degree

    def __unicode__(self):
        fields = 'pos phr lmk rel deg'
        given = [(f, getattr(self,f)) for f in fields.split() if getattr(self,f) is not None]
        given = ', '.join(u'%s=%s' % g for g in given)
        if given:
            return u'P(word=%s | %s) = %s' % (self.word, given, self.prob)
        else:
            return u'P(word=%s) = %s' % (self.word, self.prob)

    @classmethod
    def calc_prob(cls, word, **kwargs):
        """calculates probability"""
        pw = Pword(word=word, **kwargs)
        q = Word.get_words(**kwargs)
        divisor = q.count()
        # if divisor is 0 then prob will be None
        if divisor:
            pw.prob = q.filter(Word.word==word).count() / divisor
        return pw

    @classmethod
    def get_prob(cls, word, **given):
        """gets probability stored in db"""
        fields = 'pos phr lmk rel deg'
        params = dict((f, None) for f in fields.split())
        params.update(given)
        return cls.query.filter_by(word=word, **params).one()

    @classmethod
    def probability(cls, word, **given):
        try:
            pw = cls.get_prob(word, **given)
        except:
            pw = cls.calc_prob(word, **given)
            session.commit()
        return pw.prob

class Pexpansion(Base):
    expansion = Column(String)
    prob = Column(Float)

    # conditioned on
    parent = Column(String)  # Phrase.parent
    role = Column(String)    # Phrase.role
    lmk = Column(Float)      # Context.landmark
    rel = Column(String)     # Context.relation
    deg = Column(String)     # Context.degree

    def __unicode__(self):
        fields = 'parent lmk rel deg'
        given = [(f, getattr(self,f)) for f in fields.split() if getattr(self,f) is not None]
        given = ', '.join(u'%s=%s' % g for g in given)
        if given:
            return u'P(expansion=%s | %s) = %s' % (self.expansion, given, self.prob)
        else:
            return u'P(expansion=%s) = %s' % (self.expansion, self.prob)

    @classmethod
    def calc_prob(cls, expansion, **kwargs):
        """calculates probability"""
        pe = Pexpansion(expansion=expansion, **kwargs)
        q = Phrase.get_expansions(**kwargs)
        divisor = q.count()
        if divisor:
            pe.prob = q.filter(Phrase.expansion==expansion).count() / divisor
        return pe

    @classmethod
    def get_prob(cls, expansion, **given):
        """gets probability stored in db"""
        fields = 'parent lmk rel deg'
        params = dict((f, None) for f in fields.split())
        params.update(given)
        return cls.query.filter_by(expansion=expansion, **params).one()

    @classmethod
    def probability(cls, expansion, **given):
        try:
            pe = cls.get_prob(expansion, **given)
        except:
            pe = cls.calc_prob(expansion, **given)
            session.commit()
        return pe.prob





if __name__ == '__main__':
    engine.echo = True
    create_all()
