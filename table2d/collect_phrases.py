if __name__ == '__main__':
    import argparse
    import subprocess
    import csv
    import sys
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    bad = 0
    with open('table2D_phrases3.csv') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)  # skip headers

        phrases = []

        for rownum,row in enumerate(reader):
            location, phrase = row
            phrases.append('<s> ' + phrase + ' </s>\n')

    out_filename = 'just_phrases3.txt'
    with open(out_filename,'w') as out:
        out.writelines(phrases)
        out.flush()

    #subprocess.call(["../BLLIP-bllip-parser-70c25a0/parse.sh", out_filename])
    '''
    with open('parses.txt') as out:
        with open('table2D_phrases3.csv') as in_csv:
            for parse, line in zip( out.readlines(), in_csv.readlines()[1:] ):
                print line.rstrip(), ';', parse.rstrip()