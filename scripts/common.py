#!/usr/bin/env python
import datetime
import holidays
#from scipy import stats, integrate

CHART_SIZE = (895, 600)
FIGURE_SIZE = {'figsize':(CHART_SIZE[0]/100.0, CHART_SIZE[1]/100.0), 'dpi':100}

PDF_VIEWER = 'evince'

PNG_DIR = '../pdf_pngs'
CHARTS_DIR = '..'
PDF_DIR = '../pdfs'
DB_NAME = '../briefsdata.sqlite'

CIA_URL_BASE = 'http://www.foia.cia.gov/sites/default/files/document_conversions/1827265/'

SUNDAY_DAY_OF_WEEK = 6
US_HOLIDAYS = holidays.US()
BRIEFS_START = datetime.date(year=1961,month=06,day=17)
BRIEFS_END = datetime.date(year=1969,month=01,day=20)

#I'm unimpressed with pd.daterange()!
#How do I do this using a list comprehension?
monthly_index_extra_years = []
for i in range(1961,1970):
  for i2 in range(1,12+1):
    monthly_index_extra_years.append(datetime.date(year=i,month=i2,day=01))

monthly_index = []
i = datetime.date(BRIEFS_START.year, BRIEFS_START.month, 01)
while i < datetime.date(BRIEFS_END.year, BRIEFS_END.month+1, 01):
  monthly_index.append(i)
  last_month = i.month
  while i.month == last_month: #can't increment by months delta and days of the month varies, so here is a bruteforce solution.
    i += datetime.timedelta(days=1)

alldates = set([])
alldates_nosundays_noholidays = set([])
alldates_nosundays = set([])

i = BRIEFS_START
while i <= BRIEFS_END:
  alldates.add(i)
  if i.weekday() != SUNDAY_DAY_OF_WEEK:
    alldates_nosundays.add(i)
    if i not in US_HOLIDAYS:
      alldates_nosundays_noholidays.add(i)

  i += datetime.timedelta(days=1)