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

  for row in db_c.execute('SELECT filename,page_count FROM briefs WHERE tesseract IS NULL').fetchall():
    filename = row[0]
    page_count = row[1]
    file_pngs_dir = os.path.join(PNG_DIR,filename)

    full_ocr = u''
    for page_n in range(1,page_count+1):
      page_png = os.path.join(file_pngs_dir,'page-'+str(page_n)+'.png')
      if not os.path.exists(page_png):
        page_png = os.path.join(file_pngs_dir,'page-'+str(page_n).zfill(2)+'.png')

      page_ocr = subprocess.check_output(['tesseract',page_png,'stdout']).decode('utf8')
      full_ocr += '\n'+page_ocr

    db_c.execute('UPDATE briefs SET tesseract=? WHERE filename==?', (full_ocr,filename))
    db.commit()

    char_count = len(full_ocr)
    print('Processed '+filename+': '+str(char_count)+' characters, '+str(char_count/float(page_count))+' characters per page.')

  db.commit()
  db.close()

if __name__ == '__main__':
  main()
