#!/usr/bin/env python
from __future__ import print_function
import os
import signal
import sys
import subprocess
import re
import sqlite3

from common import *

def main():
  db = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
  db_c = db.cursor()

  for row in db_c.execute('SELECT filename FROM briefs'):
    filename = row[0]
    file_pngs_dir = os.path.join(PNG_DIR,filename)
    print('Extracting PDF to '+file_pngs_dir)
    os.system('mkdir -p "'+file_pngs_dir+'"')
    os.system('pdftoppm -png "'+os.path.join(PDF_DIR,filename)+'" "'+os.path.join(file_pngs_dir,'page')+'"')
    #os.system('convert "'+os.path.join(PDF_DIR,filename)+'" "'+file_pngs_dir+'/page.png"')

  db.close()

if __name__ == '__main__':
  main()

