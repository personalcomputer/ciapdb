#!/usr/bin/env python
from __future__ import print_function
import os
import sys
import re

BASE_FILENAME = '../html/PDBs?page='
PAGE_COUNT = 124
FILENAMES = ['../html/PDBs']+[BASE_FILENAME+str(n) for n in range(1,PAGE_COUNT+1)]

def main():
  for filename in FILENAMES:
    htmlfile = open(filename, 'r')
    html_listing = htmlfile.read()
    htmlfile.close()
    m = re.findall(r'/document/(\d+)">([^<]+)</a>', html_listing)
    for match in m:
      curr_name = 'DOC_'+match[0]+'.pdf'
      new_name = 'DOC_'+match[0]+' '+match[1].replace('&#039;','\'')+'.pdf'
      #new_name = new_name.replace('&#039;','\'')

      if os.path.exists(curr_name):
        print('mv '+curr_name+' '+new_name)
        os.rename(curr_name, new_name)

if __name__ == '__main__':
  main()
