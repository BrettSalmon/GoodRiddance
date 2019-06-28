#!/usr/bin/env python
# coding: utf-8

# In[271]:


#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import ast
import glob
import re
import sys
import os
from subprocess import call
from shutil import copyfile, move
from tqdm import tqdm_notebook
from datetime import datetime
from datetime import timedelta
import time
import urllib.request
from itertools import islice
import math

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import random

from selenium import webdriver
from selenium.webdriver.common.keys import Keys


# In[272]:


now = datetime.now()
date=now.strftime("%d-%m-%Y")

thedir='/Users/bsalmon/BrettSalmon/data_science/Insight/goodriddance/scraping/craigslist/'
cityname='Baltimore'
city=cityname.lower().replace(' ','_')
item='couch'


def check_date_version(date,thedir=thedir, city=city):
    # First, check if you already have a scrape file for this object and location
    filen=thedir+city+'/scrape_'+item+'_'+date+'.csv'
    if os.path.exists(filen):
            # Okay the file exists for today, but have you done this already?
        if not filen.replace('.csv','')[-1].isalpha():
            print('%% A scrape file exists, but doesnt end in alpha character')
            date=date+'a'
        else:
            print('%% A scrape file exists AND ends it ends in an alpha character')
            date=date + chr(ord(filen.replace('.csv','')[-1])+1)
    else:
        print("%% I have no scrape record for this object on this date")
    print('====== setting date  =  '+date)
    return date




date = check_date_version(date)




if not (os.path.exists(thedir+city)):
    os.mkdir(thedir+city)
if not (os.path.exists(thedir+city+'/'+item+'_images/')):
    os.mkdir(thedir+city+'/'+item+'_images/')




def todays_scrape(thedir, item, city, cityname, now):
    zips = pd.read_csv(thedir+'zipcodes.csv', index_col=0)
    thezip=zips.loc[zips['City']==cityname,'Zipcode'].iloc[0]

    if cityname=='Baltimore':
        thezip=21211
    hdrs = {'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 '+
            '(KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'}
    proxies = setup_proxy_rotation()
    proxy_index = random_proxy(proxies)
    proxy = proxies[proxy_index]

    first_url=('https://'+cityname.lower().replace(' ','')+
                '.craigslist.org/search/lac/fuo?postal='+str(thezip)+'&query='+item+'&s='+
                '0'+'&search_distance=30')

    # create a new Firefox session
    #driver = webdriver.Chrome()
    #driver.implicitly_wait(30)
    #driver.get(first_url)
    page = requests.get(first_url, headers=hdrs, proxies=proxy)
    soup = BeautifulSoup(page.content,'html.parser')
    #soup = BeautifulSoup(driver.page_source,'html.parser')

    # Get total number of couches
    totalcount = int(str(soup.find('span',class_='totalcount')).split(">")[1].split("<")[0])

    badid=[]
    theid=[]
    theurl=[]
    theprice=[]
    theimgurl=[]
    time_since_posting=[]

    # This cycles through the Craigslist search result pages
    for ipage in tqdm_notebook(range(0,math.floor(totalcount/120))):
    #ipage=1
    #if 1:
        next_url=('https://'+cityname.lower().replace(' ','')+
                    '.craigslist.org/search/lac/fuo?postal='+str(thezip)+'&query='+item+'&s='+
                    str(120*ipage)+'&search_distance=30')

        proxies = setup_proxy_rotation()
        proxy_index = random_proxy(proxies)
        proxy = proxies[proxy_index]
        page = requests.get(next_url, headers=hdrs, proxies=proxy)
        soup = BeautifulSoup(page.content,'html.parser')

        for i in soup.find_all('a', class_='result-image gallery empty'):
            badid.append(int(str(i).split('/')[-2].split('.')[0]))

        badcounter=0
        for i in range(len(soup.find_all('a',class_="result-title"))):
        #i=116
            tit=str(soup.find_all('a',class_="result-title")[i])
            theid.append(int(tit.split(' ')[3].replace('data-id="','')[0:-2]))
            theurl.append(tit.split(' ')[4].split('"')[1])

            trow=str(soup.find_all('li', class_='result-row')[i])
            theprice.append(int(trow.split(
                'result-meta')[1].split(">")[2].split("<")[0].replace('$','')))


            if ('result-image gallery empty' in str(soup.find_all('li', class_='result-row')[i])):
                theimgurl.append('bad')
                badcounter+=-1
            else:
                imgid = str(soup.find_all('a', class_='result-image gallery')[i +badcounter]).split('"')[3].split(',')[0][2:] 
                tturl = (theurl[i].replace(theurl[i].split('/')[-2], imgid+'_300x300'))
                theimgurl.append('https://images.craigslist.org/'+tturl.split('/')[-2]+'.jpg')


            # Save image to disk
            outfile = thedir+city+'/'+item+'_images/'+str(theid[i])+'.jpg'
            if not os.path.exists(outfile):
                urllib.request.urlretrieve(theimgurl[i], outfile)            

            timepost=str(soup.find_all('time', class_='result-date')[i]).split('"')[3]
            mydelta=(now-datetime.strptime(timepost, '%Y-%m-%d %H:%M'))
            time_since_posting.append(mydelta.days + mydelta.seconds/60/60/24)

    # Get rid of shitty posts
    boolcompare=[True]*len(theid)
    for i in range(len(boolcompare)):
        if theid[i] in badid: boolcompare[i]=False
    theid = list(np.array(theid)[boolcompare])
    theprice = list(np.array(theprice)[boolcompare])
    theurl = list(np.array(theurl)[boolcompare])
    time_since_posting = list(np.array(time_since_posting)[boolcompare])
    theimgurl = list(np.array(theimgurl)[boolcompare])


    todays_scrape_df = pd.DataFrame(list(zip(theprice, time_since_posting, theimgurl, theurl)),
                                    columns=['price','time_since_posting', 'imgurl','url'],
                                    index=theid)
    return todays_scrape_df




def random_proxy(proxies):
    return random.randint(0, len(proxies) - 1)

def setup_proxy_rotation():
    ua = UserAgent() # From here we generate a random user agent
    hdrs = {'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 '+
            '(KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'}
    # Retrieve latest proxies
    proxies_req = Request('https://www.sslproxies.org/', headers=hdrs)
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = None
    while proxies_doc == None:
        try:
            proxies_doc = urlopen(proxies_req).read().decode('utf8')
        except:
            print('%% Taking a nap! These proxies are hard -_-')
            time.sleep(5)

    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

    proxies = [] # Will contain proxies [ip, port]
    # Save proxies in the array
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append({'ip':   row.find_all('td')[0].string,
                        'port': row.find_all('td')[1].string })
    return proxies




def first_scrape(thedir, item, city, modify_id=False, modify_url=False, modify_price=False):
    
    if not modify_id:
        (theid,theurl,theprice) = gather_ids(thedir, item, city, cityname)
    else:
        theid=modify_id
        theurl=modify_url
        theprice=modify_price
    
    badid=[]
    imgurl = ['']*len(np.array(theid))
    postdate=['']*len(np.array(theid))
    time_since_posting=[0]*len(np.array(theid))

    proxies = setup_proxy_rotation()

    for i in tqdm_notebook(range(len(theurl))):
        #if not os.path.exists(thedir+city+'/'+item+'_images/'+str(theid[i])+'.jpg'):
        #headers = requests.utils.default_headers()
        #headers['User-Agent'] = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'+
        #                         ' (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36')
        hdrs = {'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 '+
                '(KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept-Encoding': 'none',
                'Accept-Language': 'en-US,en;q=0.8',
                'Connection': 'keep-alive'}

        if not (i%10):
            # Renew proxies every 50, otherwise this is pretty slow
            proxies = setup_proxy_rotation()
            proxy_index = random_proxy(proxies)
            proxy = proxies[proxy_index]
        page = requests.get(theurl[i], proxies=proxy,headers=hdrs)
        singlesoup=BeautifulSoup(page.content,'html.parser')

        if len(singlesoup.find_all('meta', property="og:image"))==0:
            print('bad ID')
            badid.append(theid[i])
        else:
            tmp_image_url=str(singlesoup.find_all('meta', property="og:image")[0]).split('"')[1]
            #if not (i % 50):
             #   print('changing proxy')
             #   proxy_index = random_proxy(proxies)
             #   proxy = proxies[proxy_index]
            #    request = requests.get(tmp_image_url, proxies=proxy, headers={'Connection':'close'})
            #else:

            check_if_exists=None
            while check_if_exists == None:
                try:
                    check_if_exists = requests.get(tmp_image_url,proxies=proxy,headers=hdrs)
                except:
                    print("%% Taking a nap, page check didn't like me")
                    time.sleep(5)

            if check_if_exists.status_code == 200:
                # Save the image URL path
                imgurl[i]=tmp_image_url

                # Save the post image
                outfile = thedir+city+'/'+item+'_images/'+str(theid[i])+'.jpg'
                if not os.path.exists(outfile):
                    urllib.request.urlretrieve(tmp_image_url, outfile)            

                # Save the post date information
                adate = str(singlesoup.find('time')).split('"')[3]
                adate = adate.replace('T',' ')
                adate = adate.replace('-',' ')
                adate = adate[0:-5]
                tpostdate = datetime.strptime(adate, '%Y %m %d %H:%M:%S')
                postdate[i]=(tpostdate.strftime("%d-%m-%Y"))

                # And time since posting
                datetime_object = datetime.strptime(adate, '%Y %m %d %H:%M:%S')
                time_since_posting[i]=((now - datetime_object).days)
            else:
                badid.append(theid[i])

    # Get rid of shitty posts
    boolcompare=[True]*len(theid)
    for i in range(len(boolcompare)):
        if theid[i] in badid:boolcompare[i]=False
    theid = list(np.array(theid)[boolcompare])
    theprice = list(np.array(theprice)[boolcompare])
    theurl = list(np.array(theurl)[boolcompare])

    todays_scrape_df = pd.DataFrame(list(zip(theprice,time_since_posting, imgurl, theurl)),
                                    columns=['price','time_since_posting', 'imgurl','url'],
                                    index=theid)
    return todays_scrape_df




def modify_scrape(fiducial_scrape_df, todays_scrape_df, thedir, item, city):
    
    # Compare new and old posts by ID#
    new=list(todays_scrape_df.index)
    old=list(fiducial_scrape_df.index)

    # Figure out which postings are new and which were removed
    new_postings = [x for x in new if x not in old]
    removed_postings = [x for x in old if x not in new]

    fiducial_scrape_df.drop(removed_postings, axis=0,inplace=True)
    
    new_posts_bool=[(i in new_postings) for i in theid]
 
    for i in new_postings:
        if not i in fiducial_scrape_df.index:
            fiducial_scrape_df = fiducial_scrape_df.append( todays_scrape_df.loc[i] )
            
    return fiducial_scrape_df



# Regardless of how well it matches, just scrape the new list:
todays_scrape_df = todays_scrape(thedir, item, city, cityname, now)

# Load the fiducial list
files = glob.glob(thedir+city+'/scrape_'+item+'_*-2019*')

if not files:
    # No run exists yet for this object
    print('no scrapes done for this object, starting from scratch')
    fiducial_df = todays_scrape_df

else:
    file_date=[]
    for i in files:
        file_date.append(i.split('_')[-1].replace('.csv',''))

    lastdate=max(file_date)
    filen = 'scrape_'+item+'_'+lastdate+'.csv'
    fiducial_df = pd.read_csv(thedir+city+'/'+filen, index_col=0)

    print('okay, so at least one exists')
    #if not theid:
    #    (theid,theurl,theprice) = gather_ids(thedir, item, city, cityname)
    fiducial_df = modify_scrape(fiducial_df, todays_scrape_df, thedir, item, city)
                                #modify_id=theid, modify_url=theurl, modify_price=theprice)

