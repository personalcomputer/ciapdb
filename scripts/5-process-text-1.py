#!/usr/bin/env python
#coding=utf-8
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




def clean_topic(match): #because regex isn't that good.
  match = match.strip()
  if len(match) < 3 and match.lower() != 'uk':
    return None

  if match.count('\n') >= 3:
    n1 = match.find('\n')
    n2 = match[n1:].find('\n')
    match = match[:n2]

  if match[-2] == ' ': #remove trailing character
    match = match[:-2]
  found_the = match.find(' The')
  if found_the >= 3:
    match = match[:found_the]

  match = match.lower()


  match = match.replace('--','-').replace(u'—','-').replace(u'–','-').replace(' -','-').replace('- ','-').replace(' \n','').replace('\n','') #normalize

  #fix frequent identified ocr errors
  match = match.replace('sine-soviet','sino-soviet') #simple ocr error
  match = match.replace('libza','libya') #simple ocr error
  manual_fixes = {
    'haiti-domini-': 'haiti-dominican republic', #normally it would handle this split, but dominican republic appears 2 lines down each time instead of one, don't know why.
    'west new': 'west new guinea', #simple ocr error, reads Guinea as Gu1nea each time.
    'uk-indonesia-': 'uk-indonesia-malaysia', #takes 3 lines, my parser avoids 3lines+, too unusual.
    'uar-yemen-': 'uar-yemen-saudi arabia', #OCRed in a weird way each time, intermixing the second line with the content, breaks parser
    'tanganyika-': 'tanganyika-zanzibar', #OCRed in a weird way each time ^
    'arab states-': 'arab states-israel', #OCRed in a weird way each time ^
    'morocco-': 'morocco-algeria', #OCRed in a weird way each time ^
    'indonesia-': 'indonesia-malaysia', #OCRed in a weird way each time ^
    'dominican': 'dominican republic', #not built to handle no-dash splits like this, simply too hard to parse.
    'nonproliferation': 'nonproliferation treaty', #no-dash split ^
    #somalia- -> somalia-communist bloc, somalia-ethiopia
  }
  try:
    match = manual_fixes[match]
  except KeyError:
    pass
  if match.startswith('north vietnamese reflections of us political'):
    match = 'north vietnamese reflections of us political attitudes on the war'

  if len(match) < 2:
    return None
  if match.startswith('declassified in pa') or match.startswith('notes'):
    return None
  if match in ['cz','ft', 'fnr tim', 'fnr tl', 'lie', 'cid', 'eee', 'egg']: #ocr errors, almost all of these are from the very start/very end of pages. I think it happens when the declassified disclaimer gets partly cut off? I don't really know.
    return None
  if match in ['for', 'fnr th']: #misc error, happens when "For The Presidenf OnIV—Tan Secret" is ocred incorrectly.
    return None
  if match in ['mum']: #oddly common ocr error when the text is really hazy
    return None
  if match in ['cite', 'from']: #"from" is part of the addressing on the brief. Citations similarly are not topics.
    return None
  if match in ['this']: #I believe these are legitimate sections, but unable to parse.
    return None
  if match in ['we have noted no', 'the']: #the main source of errors for this parsing system is that the ocr will detect letters as numbers and numbers as letters, which causes small lettered sections to get detected sometimes and cause things like this.
    return None

  return match

def parse_topics(full_ocr):
    matches = set(     re.findall(u'^[,\-_i:\.‘\'\\/\|—]? ?[1-9][0-9A-F]? ?\.(?: \')?\s*([A-Z][a-zA-Z ]+(?:[—\-–]\n?[a-zA-Z ]+(?:[—\-–]\n?[a-zA-Z—\-– ]+)?)?):?\.?\s+', full_ocr, re.MULTILINE))
    matches.update(set(re.findall(u'\s\n\n([A-Z][a-zA-Z —\-–]+):\s+', full_ocr, re.MULTILINE)))
    return [match for match in map(clean_topic, matches) if match]

def parse_words(full_ocr):
    matches = re.findall(r'\w+', full_ocr, re.MULTILINE)
    return matches

def main():
  db = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
  db_c = db.cursor()

  db_c.execute('CREATE TABLE IF NOT EXISTS topics_raw (topic TEXT, doc_number INT, FOREIGN KEY(doc_number) REFERENCES briefs(doc_number))')
  db_c.execute('CREATE TABLE IF NOT EXISTS words (word  TEXT, doc_number INT, FOREIGN KEY(doc_number) REFERENCES briefs(doc_number))')
  db_c.execute('DELETE FROM topics_raw')
  db_c.execute('DELETE FROM words')
  db.commit()

  briefs = db_c.execute('SELECT doc_number,tesseract,filename FROM briefs').fetchall() #ORDER BY random() LIMIT 5
  for brief in briefs:
    doc_number = brief[0]
    full_ocr = brief[1]
    filename = brief[2]

    topics = parse_topics(full_ocr)
    #print(filename+str(topics))
    for topic in topics:
      db_c.execute('INSERT INTO topics_raw (topic, doc_number) VALUES (?,?)', (topic, doc_number))

    words = parse_words(full_ocr)
    for word in words:
      db_c.execute('INSERT INTO words (word, doc_number) VALUES (?,?)', (word, doc_number))

    #db.commit()

    print('Processed '+filename+': '+str(len(topics))+' topics, '+str(len(words))+' words')

  db.commit()

  db.close()


if __name__ == '__main__':
  main()