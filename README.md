# bolt

This repository stores the files related to the *bolt* project.

Everything is under one directory temporarily, but it will eventually
be organized into different modules, depending on usage and implementation
languages.


## instructions

    git clone https://github.com/marcovzla/bolt.git
    cd bolt
    git submodule init
    git submodule update
    cd bllip-parser
    make
    cd ../model2d
    curl -O http://nlp.stanford.edu/software/stanford-tregex-2012-05-22.tgz
    tar xzvf stanford-tregex-2012-05-22.tgz
    mv stanford-tregex-2012-05-22 stanford-tregex
    ./pipeline.sh
