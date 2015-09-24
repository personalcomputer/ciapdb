#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function
import os
import signal
import sys
import subprocess
import re
import numpy as np
import pandas as pd
import sqlite3

from common import *

matplotlib.style.use('ggplot')

def main():
  db = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
  db_c = db.cursor()

  db_c.execute('CREATE TABLE IF NOT EXISTS countries (topic TEXT, doc_number INT, FOREIGN KEY(doc_number) REFERENCES briefs(doc_number))')
  db_c.execute('DELETE FROM countries')
  db.commit()

  #all_countries = {} #'country':set([associated docs])

  topics_raw = db_c.execute('WITH cte AS topic,(SELECT count(*) as c FROM topics_raw GROUP BY topic) SELECT topic,c FROM cte WHERE c>=2 ORDER BY c DESC').fetchall()
  for result in topics_raw:
    topic = result[0]
    frequency = result[1]

    countries=[t for t in topic.split('-') if t != '']
    associated_docs = db_c.execute('SELECT doc_number FROM raw_topics WHERE topic==?',topic).fetchall()
    for country in countries:
      for associated_doc in associated_docs:
        db_c.execute('INSERT INTO countries (country,doc_number) VALUES (?,?)', country,associated_doc)


  db.commit()
  db.close()

if __name__ == '__main__':
  main()