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
#import cartopy
from pylab import figure, show
import seaborn as sns; sns.set()
import wordcloud

from common import *

matplotlib.style.use('ggplot')

def print_redactions(db):
  db_c = db.cursor()

  cte = 'WITH redaction_t(redaction_count,filename,page_count) AS (SELECT COUNT(*) AS redaction_count,briefs.filename,briefs.page_count from words LEFT JOIN briefs ON words.doc_number=briefs.doc_number WHERE words.word=="50X1" OR words.word=="50x1" GROUP BY words.doc_number) '
  db_c.execute(cte+'SELECT COUNT(*) FROM redaction_t')
  briefs_with_1ormore_total_redactions = db_c.fetchone()[0]
  db_c.execute(cte+'SELECT COUNT(*) FROM redaction_t WHERE redaction_count>page_count')
  briefs_with_1ormore_redaction_per_page = db_c.fetchone()[0]
  db_c.execute('SELECT COUNT(*) FROM briefs')
  total_briefs = db_c.fetchone()[0]

  print('Briefs that have redacted content: '+str(briefs_with_1ormore_total_redactions)+' ('+str(((briefs_with_1ormore_total_redactions/float(total_briefs))*100))+'%)')
  print('Briefs that have more redactions than pages: '+str(briefs_with_1ormore_redaction_per_page)+' ('+str(((briefs_with_1ormore_redaction_per_page/float(total_briefs))*100))+'%)')

def plot_raw_topics(db):
  db_c = db.cursor()
  db_c.execute('WITH cte AS (SELECT count(*) as c,topic FROM topics_raw GROUP BY topic) SELECT topic,c FROM cte WHERE c>=3 ORDER BY c DESC')

  frequencies = [(t.encode('ascii', 'ignore'),c) for (t,c) in db_c.fetchall()]

  word_cloud = wordcloud.WordCloud(font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', background_color='white', scale=1, width=CHART_SIZE[0], height=CHART_SIZE[1]).generate_from_frequencies(frequencies)
  fig = plt.figure(**FIGURE_SIZE)
  fig_ax = plt.Axes(fig, [0., 0., 1., 1.])
  fig_ax.set_axis_off()
  fig.add_axes(fig_ax)
  fig_ax.imshow(word_cloud)
  fig.savefig(os.path.join(CHARTS_DIR,'raw-topics-cloud.png'))

  '''for topic in frequencies():

  .reindex(monthly_index_extra_years, fill_value=0)
  hist = pd.DataFrame({})'''

  indexed_frequencies = []

  index_to_use = monthly_index

  for i,date in enumerate(index_to_use):
    try:
      start_d = date
      end_d = index_to_use[i+1]
      db_c.execute('WITH cte AS (SELECT count(*) as c,topic FROM topics_raw LEFT JOIN briefs ON topics_raw.doc_number=briefs.doc_number WHERE briefs.pub_date BETWEEN ? AND ? GROUP BY topic) SELECT c,topic FROM cte ORDER BY c DESC', (start_d, end_d))
      indexed_frequencies.append(db_c.fetchall())
    except IndexError:
      break

  top_topics = list(reversed([x[0] for x in db_c.execute('WITH cte AS (SELECT count(*) as c,topic FROM topics_raw GROUP BY topic) SELECT topic FROM cte ORDER BY c DESC LIMIT 50').fetchall()]))

  topics_monthly_pop = pd.DataFrame({},index=index_to_use, columns=top_topics).fillna(0)

  os.system('mkdir -p topics-gif')
  for i,topics in enumerate(indexed_frequencies):
    for freq,topic in topics:
      if topic in top_topics:
        topics_monthly_pop[topic][index_to_use[i]] = freq
    # plot_data = topics_monthly_pop.loc[index_to_use[i]]
    # fig = plt.figure(figsize=(895/100.0, 1200/100.0), dpi=100)
    # fig_ax = fig.add_subplot(1, 1, 1)
    # fig_ax.set_title('Top Topics')
    # fig_ax.set_xlim([0,50])
    # alt_index = range(len(plot_data.index))
    # fig_ax.barh(alt_index, plot_data)
    # fig_ax.set_yticks(alt_index)
    # fig_ax.set_yticklabels(plot_data.index)
    # fig.suptitle(index_to_use[i].strftime('%Y-%m'))
    # fig.savefig(os.path.join(CHARTS_DIR,'topics-gif','topics-'+str(i).zfill(3)+'.png'))
    # plt.close(fig)


def plot_countries(db):
  pass
  '''db_c = db.cursor()
  db_c.execute('WITH cte AS (SELECT count(*) as c,topic FROM topics_raw GROUP BY topic) SELECT topic,c FROM cte WHERE c>=3 ORDER BY c DESC')

  countries_shapes = cartopy.io.shapereader.natural_earth(resolution='100m',category='cultural',name='admin_0_countries')

  ax = plt.axes(projection=cartopy.crs.PlateCarree())
  for country in cartopy.io.shapereader.Reader(countries_shapes).records():
    name = country.attributes['name_long'].lower() #This simply can never work, I need historical data like http://geacron.com
    frequency = frequencies[name]
    color = plt.cm.jet(frequency) #?
    ax.add_geometries(country.geometry, cartopy.crs.PlateCarree(), facecolor=color, label=country.attributes['name_long'])

  plt.savefig(os.path.join(CHARTS_DIR,'countries.png'))'''


def main():
  db = sqlite3.connect(DB_NAME, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

  print_redactions(db)
  plot_raw_topics(db)

  db.close()

if __name__ == '__main__':
  main()