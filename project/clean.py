from os import listdir
import re

files = listdir('../books/')

for file in files:
    f = open('../books/' + file, 'r')
    text = f.read()
    f.close()

    text = re.sub('.*\*END\*', '', text, flags=re.DOTALL)

    f = open('../books/' + file, 'w')
    text = f.write(text)
    f.close()

    print 'Cleaned ' + file
