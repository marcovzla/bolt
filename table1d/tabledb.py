#!/usr/bin/env python



from elixir import *



metadata.bind = 'sqlite:///table1d.db'
metadata.bind.echo = False



# like Django's `get_or_create`
def get_or_create(cls, defaults={}, **params):
    obj = cls.get_by(**params)
    if not obj:
        params.update(defaults)
        obj = cls(**params)
    return obj

Entity.get_or_create = classmethod(get_or_create)



class Context(Entity):
    using_options(tablename='contexts')
    ## location = Field(Integer)
    relation = ManyToOne('RelationContext')
    landmark = ManyToOne('LandmarkContext')
    bigrams = OneToMany('Bigram')
    trigrams = OneToMany('Trigram')

    def __repr__(self):
        return '(%s, %d) %s' % (
                self.relation.relation,
                self.relation.degree,
                self.landmark.landmark_name)



class RelationContext(Entity):
    using_options(tablename='relation_contexts')
    relation = Field(String)
    degree = Field(Integer)
    context = OneToMany('Context')
    words = OneToMany('Word')
    expansions = OneToMany('PhraseExpansion')



class LandmarkContext(Entity):
    using_options(tablename='landmark_contexts')
    landmark_name = Field(String)
    landmark_location = Field(String)
    context = OneToMany('Context')
    words = OneToMany('Word')
    expansions = OneToMany('PhraseExpansion')



class Phrase(Entity):
    using_options(tablename='phrases')
    phrase = Field(String)
    role = Field(String)
    expansion = OneToMany('PhraseExpansion')
    words = OneToMany('Word')



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
