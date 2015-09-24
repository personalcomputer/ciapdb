#!/usr/bin/env python
from __future__ import print_function
import os
import signal
import sys
import subprocess
import re
import numpy as np
import pandas as pd
import math
import sqlite3
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns; sns.set()

from common import *

matplotlib.style.use('ggplot')


#def get_binned_pub_freqs(db, brief_names,brief_names_excl=None):
#  #where_icl = '('+(' OR '.join(['brief_name=="'+bn+'"' for bn in brief_names]))+')'
#  #where_exl = '('+(' AND '.join(['brief_name!="'+bn+'"' for bn in brief_names_excl]))+')'
#  #where = where_icl+(' AND ' if (where_incl and where_excl) else '')+where_exl
#  df = pd.read_sql_query('SELECT strftime("%Y-%m",pub_date) AS date, COUNT(*) AS mi_count FROM briefs WHERE '+where+' GROUP BY date', db)
#  df.date = df.date.astype("datetime64")
#  return df.set_index('date').reindex(index, fill_value=0)

def plot_freq(db):
  pdb_hist = pd.read_sql_query('SELECT strftime("%Y-%m",pub_date) AS date, COUNT(*) AS mi_count FROM briefs WHERE brief_name=="THE PRESIDENT\'S DAILY BRIEF" GROUP BY date', db)
  picl_hist = pd.read_sql_query('SELECT strftime("%Y-%m",pub_date) AS date, COUNT(*) AS mi_count FROM briefs WHERE brief_name=="THE PRESIDENT\'S INTELLIGENCE CHECKLIST" GROUP BY date', db)
  piclreview_hist = pd.read_sql_query('SELECT strftime("%Y-%m",pub_date) AS date, COUNT(*) AS mi_count FROM briefs WHERE brief_name=="THE PRESIDENT\'S INTELLIGENCE REVIEW" GROUP BY date', db)
  other_hist = pd.read_sql_query('SELECT strftime("%Y-%m",pub_date) AS date, COUNT(*) AS mi_count FROM briefs WHERE brief_name!="THE PRESIDENT\'S INTELLIGENCE CHECKLIST" AND brief_name!="THE PRESIDENT\'S DAILY BRIEF" AND brief_name!="THE PRESIDENT\'S INTELLIGENCE REVIEW" GROUP BY date', db)

  pdb_hist.date =               pdb_hist.date.astype("datetime64")
  picl_hist.date =             picl_hist.date.astype("datetime64")
  piclreview_hist.date = piclreview_hist.date.astype("datetime64")
  other_hist.date =           other_hist.date.astype("datetime64")
  pdb_hist =               pdb_hist.set_index('date').reindex(monthly_index_extra_years, fill_value=0)
  picl_hist =             picl_hist.set_index('date').reindex(monthly_index_extra_years, fill_value=0)
  piclreview_hist = piclreview_hist.set_index('date').reindex(monthly_index_extra_years, fill_value=0)
  other_hist =           other_hist.set_index('date').reindex(monthly_index_extra_years, fill_value=0)

  # hist = pd.DataFrame({'The President\'s Daily Brief': pdb_hist.mi_count,
  #                      'The President\'s Intelligence Checklist': picl_hist.mi_count,
  #                      'The President\'s Intelligence Review': piclreview_hist.mi_count,
  #                      'Special Issues': other_hist.mi_count},
  #                      index=monthly_index)
  #hist.plot(type="line",title="Briefs Issued Per Month")
  #plt.savefig()

  fig = plt.figure(**FIGURE_SIZE)
  fig_ax = fig.add_subplot(1, 1, 1)
  fig_ax.set_title('Briefs Issued Per Month')
  fig_ax.plot(pdb_hist.index, pdb_hist.mi_count, '-', label='The President\'s Daily Brief')
  fig_ax.plot(picl_hist.index, picl_hist.mi_count, '-', label='The President\'s Intelligence Checklist')
  fig_ax.plot(piclreview_hist.index, piclreview_hist.mi_count, '-', label='The President\'s Intelligence Review')
  fig_ax.plot(other_hist.index, other_hist.mi_count, '-', label='Special Issues')
  fig_ax.legend(loc='center right')
  fig.savefig(os.path.join(CHARTS_DIR,'publication-frequency-1.png'))

  db_c = db.cursor()
  dates = db_c.execute('SELECT strftime("%Y-%m-%d",pub_date) AS date FROM briefs GROUP BY date ORDER BY date ASC').fetchall()
  dates_set = set([datetime.datetime.strptime(d[0],'%Y-%m-%d').date() for d in dates])
  missing1 = alldates-dates_set
  print('Missing briefs: '+str(len(missing1))+' out of '+str(len(alldates))+' days')

  missing2 = alldates_nosundays-dates_set
  print('Missing briefs (excl. sundays): '+str(len(missing2))+' out of '+str(len(alldates_nosundays))+' days')

  missing3 = alldates_nosundays_noholidays-dates_set
  print('Missing briefs (excl. sundays + federal holidays): **'+str(len(missing3))+'** out of '+str(len(alldates_nosundays_noholidays))+' days')
  print(', '.join(map(str, sorted(missing3))))


def plot_density(db):
  '''pdb_densities = pd.read_sql_query('SELECT strftime("%Y-%m",pub_date) AS date, SUM(page_count)/COUNT(*) AS avg_pages FROM briefs WHERE brief_name LIKE "THE PRESIDENT\'S DAILY BRIEF%" OR brief_name LIKE "THE PRESIDENT\'S INTELLIGENCE CHECKLIST%" GROUP BY date', db)
  pdb_densities.date = pdb_densities.date.astype("datetime64")
  pdb_densities = pdb_densities.set_index('date').reindex(monthly_index, fill_value=0)

  fig = plt.figure()#**FIGURE_SIZE)
  fig_ax = fig.add_subplot(1, 1, 1)
  fig_ax.set_title('Average Pages Per Daily Brief')
  fig_ax.plot(pdb_densities.index, pdb_densities.avg_pages, '-')
  fig_ax.legend(loc='center right')
  fig.savefig(os.path.join(CHARTS_DIR,'density-1.png'))'''

  pdb_densities2 = pd.read_sql_query('SELECT strftime("%Y-%m-%d",pub_date) AS date, filename, doc_number, brief_name, page_count FROM briefs WHERE brief_name LIKE "THE PRESIDENT\'S DAILY BRIEF%" OR brief_name LIKE "THE PRESIDENT\'S INTELLIGENCE CHECKLIST%" ORDER BY page_count DESC', db)

  fig = plt.figure(**FIGURE_SIZE)
  fig_ax = fig.add_subplot(1, 1, 1)
  fig_ax.set_title('Daily Briefs Page Count Distribution')
  fig_ax.plot(pdb_densities2.index, pdb_densities2.page_count, '-')
  fig_ax.legend(loc='center right')
  fig.savefig(os.path.join(CHARTS_DIR,'density-2.png'))

  db_c = db.cursor()
  db_c.execute('SELECT AVG(page_count) FROM briefs WHERE brief_name=="THE PRESIDENT\'S DAILY BRIEF" OR brief_name=="THE PRESIDENT\'S INTELLIGENCE CHECKLIST"')
  print('Average length (excl special issues): '+str(db_c.fetchone()[0]))#round down because last pages are often partly empty, as is usual in documents.

  pdb_densities3 = pd.read_sql_query('SELECT strftime("%Y-%m-%d",pub_date) AS date, filename, doc_number, brief_name, page_count FROM briefs WHERE brief_name == "THE PRESIDENT\'S DAILY BRIEF" OR brief_name == "THE PRESIDENT\'S INTELLIGENCE CHECKLIST" ORDER BY page_count DESC LIMIT 20', db)

  print('Longest Daily Briefs (excl special issues):')
  for br_i in pdb_densities3.index[:10]:
    br = pdb_densities3.ix[br_i]
    print('- ['+str(br.brief_name).title().replace('\'S','\'s')+' on '+str(br.date)+']('+CIA_URL_BASE+str(br.filename)+')')

def main():
  db = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

  plot_freq(db)
  plot_density(db)

  db.close()


if __name__ == '__main__':
  main()