#!/bin/bash

# remove carriage return from file
perl -i -pe "s/\r\n/\n/" sentences.csv

# save parsetrees in trees.txt (excluding the column header)
cat sentences.csv | cut -d, -f4 | perl -ne "print unless $. == 1" > trees.txt

# perform surgery
java -mx100m -cp stanford-tregex.jar \
     edu.stanford.nlp.trees.tregex.tsurgeon.Tsurgeon \
     -s -treeFile trees.txt *.surgery > trees2.txt

# remove carriage return from file
perl -i -pe "s/\r\n/\n/" trees2.txt

# add column to csv file
echo modparse | cat - trees2.txt | paste -d, sentences.csv - > sentences2.csv
