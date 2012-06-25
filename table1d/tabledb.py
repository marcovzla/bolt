#!/usr/bin/env python



from elixir import *



metadata.bind = 'sqlite:///table1d.db'
metadata.bind.echo = False



class Context(Entity):
    using_options(tablename='contexts')
    ## location = Field(Integer)
    relation = ManyToOne('RelationContext')
    landmark = ManyToOne('LandmarkContext')
    bigrams = OneToMany('Bigram')
    trigrams = OneToMany('Trigram')

    def __repr__(self):
        print '(%s, %d) %s' % (self.relation.relation, self.relation.degree,
                               self.landmark.landmark_name)

    # like Django's `get_or_create`
    @classmethod
    def get_or_create(cls, **params):
        result = cls.get_by(**params)
        if not result:
            result = cls(**params)
        return result


class RelationContext(Entity):
    using_options(tablename='relation_contexts')
    relation = Field(String)
    degree = Field(Integer)
    context = OneToMany('Context')
    words = OneToMany('Word')
    expansions = OneToMany('PhraseExpansion')

    @classmethod
    def get_or_create(cls, **params):
        result = cls.get_by(**params)
        if not result:
            result = cls(**params)
        return result


class LandmarkContext(Entity):
    using_options(tablename='landmark_contexts')
    landmark_name = Field(String)
    landmark_location = Field(String)
    context = OneToMany('Context')
    words = OneToMany('Word')
    expansions = OneToMany('PhraseExpansion')

    @classmethod
    def get_or_create(cls, **params):
        result = cls.get_by(**params)
        if not result:
            result = cls(**params)
        return result


class Phrase(Entity):
    using_options(tablename='phrases')
    phrase = Field(String)
    role = Field(String)
    expansion = OneToMany('PhraseExpansion')
    words = OneToMany('Word')
    
    @classmethod
    def get_or_create(cls, **params):
        result = cls.get_by(**params)
        if not result:
            result = cls(**params)
        return result

    
class PhraseExpansion(Entity):
    using_options(tablename='phrase_expansions')
    expansion = Field(String)
    role = Field(String)
    parent = ManyToOne('Phrase')
    relation_context = ManyToOne('RelationContext')
    landmark_context = ManyToOne('LandmarkContext')
    context = ManyToOne('Context')


class PartOfSpeech(Entity):
    using_options(tablename='parts_of_speech')
    pos = Field(String)
    role = Field(String)
    words = OneToMany('Word')
    
    @classmethod
    def get_or_create(cls, **params):
        result = cls.get_by(**params)
        if not result:
            result = cls(**params)
        return result


class Word(Entity):
    using_options(tablename='words')
    word = Field(String)
    role = Field(String)
    pos = ManyToOne('PartOfSpeech')
    phrase = ManyToOne('Phrase')
    relation_context = ManyToOne('RelationContext')
    landmark_context = ManyToOne('LandmarkContext')
    context = ManyToOne('Context')
    

class Bigram(Entity):
    using_options(tablename='bigrams')
    word1 = Field(String)
    word2 = Field(String)
    context = ManyToOne('Context')


class Trigram(Entity):
    using_options(tablename='trigrams')
    word1 = Field(String)
    word2 = Field(String)
    word3 = Field(String)
    context = ManyToOne('Context')

setup_all()



if __name__ == '__main__':
    metadata.bind.echo = True
    create_all()
