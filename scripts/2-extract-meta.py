#!/usr/bin/env python
from __future__ import print_function
import os
import signal
import sys
import subprocess
import re
import sqlite3
import calendar
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfpage import PDFPage

from common import *

MONTH_NAMES = [m.upper() for m in calendar.month_name]
SPECIAL_ISSUE_TEXT = 'SPECIAL'
DATE_FORMATS = [ #tuple indicating match index of the day,month,year to be used, then the regexp
  ((1,2,3), r'(\d{1,2}) ([A-Z]+) (\d{4})'),    #'27 JULY 1961'
  ((2,3,4), r'(\d{1,2})--?(\d{1,2}),? ([A-Z]+) (\d{4})'),    #'18-20 MARCH 1964'
  ((3,4,5), r'(\d{1,2}) ([A-Z]+) ?--? ?(\d{1,2}) ([A-Z]+) (\d{4})'),   #'30 SEPTEMBER-2 OCTOBER 1964'
  ((4,3,5), r'(\d{1,2}) ([A-Z]+) ?--? ?([A-Z]+) (\d{1,2}) (\d{4})')   #'31 OCTOBER-NOVEMBER 3 1964'
]

known_date_corrections = {5995905: datetime.date(1962, 8, 30), 5995907: datetime.date(1962, 8, 31), 5974151: datetime.date(1967, 12, 2), 5996681: datetime.date(1963, 11, 23), 5996685: datetime.date(1963, 11, 25), 5995801: datetime.date(1962, 7, 12), 5995803: datetime.date(1962, 7, 13), 5995805: datetime.date(1962, 7, 14), 5995807: datetime.date(1962, 7, 16), 5973800: datetime.date(1967, 5, 13), 5995817: datetime.date(1962, 7, 21), 5973804: datetime.date(1967, 5, 16), 5973824: datetime.date(1967, 5, 27), 5973826: datetime.date(1967, 5, 29), 5992260: datetime.date(1962, 3, 20), 5995853: datetime.date(1962, 7, 31), 5973838: datetime.date(1967, 6, 5), 5973840: datetime.date(1967, 6, 6), 5967825: datetime.date(1965, 8, 7), 5973842: datetime.date(1967, 6, 7), 5974357: datetime.date(1968, 4, 1), 5973846: datetime.date(1967, 6, 9), 5995893: datetime.date(1962, 8, 23), 5995901: datetime.date(1962, 8, 28)}

def parse_date(date_str):
  for date_format in DATE_FORMATS:
    date_format_match_indices = date_format[0]
    date_regexp = date_format[1]
    m = re.match('^'+date_regexp+'$', date_str)
    if m:
      day = int(m.group(date_format_match_indices[0]))
      month = m.group(date_format_match_indices[1])
      year = int(m.group(date_format_match_indices[2]))

      return datetime.date(year,MONTH_NAMES.index(month),day)
      #print(date_str+' -> '+str(brief.pub_date))

  raise ValueError('can\'t parse date from '+date_str)

class Brief(object): #POD struct
  def __init__(self):
    self.doc_number = None
    self.brief_name = None
    self.pub_date = None
    self.page_count = None
    self.pdf_title = None
    self.filename = None

def correct_briefs_dates(briefs):
  briefs.sort(key=lambda x: x.doc_number)

  # Correct unknown dates
  given_date_corrections = {}
  for i,brief in enumerate(briefs):
    if brief.pub_date == None:
      # Get date from corrections lookup
      if brief.doc_number in known_date_corrections:
        brief.pub_date = known_date_corrections[brief.doc_number]
        continue

      # Guess date.
      guessed_date = None
      guessed_date_str = ''
      if briefs[i-1].pub_date and (briefs[i-1].doc_number == brief.doc_number-2):
        guessed_date = briefs[i-1].pub_date + datetime.timedelta(days=1)
        if guessed_date.weekday() == SUNDAY_DAY_OF_WEEK: #no briefs were given on a sunday, supposedly
          guessed_date += datetime.timedelta(days=1)
        guessed_date_str = guessed_date.strftime('%d %B %Y').upper()

      # Show document to user so they can manually identify the date
      print('Uncertain publication date for "'+brief.filename+'"'+(' (date guessed to be '+guessed_date_str+')' if guessed_date  else '')+'. Displaying file in '+PDF_VIEWER+'.')
      pdf_viewer_proc = subprocess.Popen([PDF_VIEWER, os.path.join(PDF_DIR,brief.filename)]) #open pdf viewer

      while brief.pub_date == None:
        # Get good date from user
        #corrected_date = raw_input('Enter file\'s date'+(' ['+guessed_date_str+']' if guessed_date  else '')+': ').strip().upper() #very very common CLI pattern, but requires special knowledge/experience to identify, so I've decided to do something more friendly to inexperienced CLI users.
        corrected_date = raw_input('Enter file\'s date'+(' if guess is incorrect' if guessed_date  else '')+': ').strip().upper()
        if corrected_date:
          try:
            corrected_date = parse_date(corrected_date)
            brief.pub_date = corrected_date
            given_date_corrections[brief.doc_number] = brief.pub_date
          except ValueError:
            print('Error: Unable to parse given date, please enter in this format: "dd MONTH yyyy" (eg: 1 JANUARY 1950)')
        elif guessed_date:
          brief.pub_date = guessed_date
          given_date_corrections[brief.doc_number] = brief.pub_date
        else:
          print('Error: No correction supplied, please supply the date indicated within the file.')

      os.kill(pdf_viewer_proc.pid, signal.SIGKILL) #kill pdf viewer

  if given_date_corrections: #this would make a lot more sense if a wrote a json 'known-date-corrections' file instead of storing the corrections raw in the .py
    known_date_corrections.update(given_date_corrections)
    print('known_date_corrections = '+str(known_date_corrections))

  return briefs

def extract_pdf_metadata(filename):
  pdf_file = open(filename, 'rb')
  parser = PDFParser(pdf_file)
  doc = PDFDocument(parser)

  pdf_title = doc.info[0]['Title']
  page_count = len(list(PDFPage.create_pages(doc)))

  pdf_file.close()

  return pdf_title, page_count

def extract_briefs_meta_info(pdf_directory, pdfs):
  briefs = []
  for filename in pdfs:
    brief = Brief()

    brief.filename = filename
    brief.doc_number = int(filename[4:14]) #"DOC_0005996917.pdf"

    # Extract pdf metadata
    pdf_title, page_count = extract_pdf_metadata(os.path.join(pdf_directory,filename))
    brief.pdf_title = pdf_title
    brief.page_count = page_count

    # Parse name part from title
    m = re.match(r'([A-Z:,\' ]+)', pdf_title)

    latter_part_of_pdf_title = pdf_title[len(m.group(0)):]

    special_issue = False
    special_issue_location = latter_part_of_pdf_title.find('SPECIAL')
    special_issue_text = ''
    if special_issue_location != -1:
      special_issue = True
      special_issue_text = latter_part_of_pdf_title[special_issue_location:]

    brief.brief_name = m.group(1).strip()
    if special_issue:
      brief.brief_name += ' '+special_issue_text

    # Parse date part
    date_part = latter_part_of_pdf_title
    if special_issue:
      date_part = latter_part_of_pdf_title[:-len(special_issue_text)-1]

    if date_part == '':
      brief.pub_date = None
    else:
      try:
        brief.pub_date = parse_date(date_part)
      except ValueError:
        pass #will be corrected later in the manual corrections #this pass is still not really great, there could be documents with seriously nonconforming titles, with the brief_name also being interpreted incorrectly - which would only be caught at this point.

    briefs.append(brief)
    print('Processed '+filename+': '+brief.brief_name+' ('+str(brief.pub_date)+')', file=sys.stderr)

  return briefs

def init_database(db, db_c):
  db_c.execute('CREATE TABLE briefs (doc_number INT PRIMARY KEY, brief_name TEXT, pub_date DATE, page_count INT, pdf_title TEXT, tesseract TEXT, filename TEXT)')
  db.commit()

def save_brief_meta_info(db, db_c, briefs):
  for brief in briefs:
    db_c.execute('INSERT INTO briefs (doc_number, brief_name, pub_date, page_count, pdf_title, filename) VALUES (?,?,?,?,?,?)', (brief.doc_number, brief.brief_name, brief.pub_date, brief.page_count, brief.pdf_title, brief.filename))
  db.commit()

def main():
  if os.path.exists(DB_NAME):
    raise RuntimeError('Error: Database '+DB_NAME+' has already been created.')

  briefs = extract_briefs_meta_info(PDF_DIR, os.listdir(PDF_DIR))
  briefs = correct_briefs_dates(briefs) #assignment technically unnecessary.

  db = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
  db_c = db.cursor()

  init_database(db, db_c)
  save_brief_meta_info(db, db_c, briefs)

  db.close()

if __name__ == '__main__':
  main()

