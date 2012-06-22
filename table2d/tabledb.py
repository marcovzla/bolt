#!/usr/bin/env python



from elixir import *



metadata.bind = 'sqlite:///table2d.db'
metadata.bind.echo = False



class Context(Entity):
    using_options(tablename='contexts')
    location = Field(String)
    landmark_location = Field(String)
    landmark_name = Field(String)
    relation = Field(String)
    degree = Field(Integer)
    words = OneToMany('Word')
    bigrams = OneToMany('Bigram')
    trigrams = OneToMany('Trigram')
    relation_structs = OneToMany('RelationStructure')
    landmark_structs = OneToMany('LandmarkStructure')

    # like Django's `get_or_create`
    @classmethod
    def get_or_create(cls, **params):
        result = cls.get_by(**params)
        if not result:
            result = cls(**params)
        return result

class Word(Entity):
    using_options(tablename='words')
    word = Field(String)
    pos = Field(String)
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

class RelationStructure(Entity):
    using_options(tablename='relation_structures')
    structure = Field(String)
    context = ManyToOne('Context')

class LandmarkStructure(Entity):
    using_options(tablename='landmark_structures')
    structure = Field(String)
    context = ManyToOne('Context')



setup_all()



if __name__ == '__main__':
    metadata.bind.echo = True
    create_all()
