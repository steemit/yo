# simple script to make a docker-env from yo.cfg
# spits out the results to stdout
import configparser
import sys
import os

if len(sys.argv)==1:
   filename = '%s/../yo.cfg' % os.path.dirname(os.path.realpath(__file__))
else:
   filename = sys.argv[1]

config_data = configparser.ConfigParser(inline_comment_prefixes=';')
config_data.read(filename)

for section in config_data.sections():
    for k in config_data[section]:
        if section.startswith('yo_'):
           outstr='%s=%s' % (k.upper(),config_data[section].get(k))
        else:
           outstr='YO_%s_%s=%s' % (section.upper(),k.upper(),config_data[section].get(k))
        print(outstr)

