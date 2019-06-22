import pandas as pd
import numpy as np
import os
import re
import ast
import sys
import glob
import time
import requests
import urllib.request
from tqdm import tqdm
from subprocess import call
from itertools import islice
from bs4 import BeautifulSoup
from shutil import copyfile, move
from datetime import datetime, timedelta

now = datetime.now()
date=now.strftime("%d-%m-%Y")

item = sys.argv[1]
cityname = sys.argv[2].title()
city=cityname.lower().replace(' ','_')

thedir='/Users/bsalmon/BrettSalmon/data_science/Insight/goodriddance/scraping/offerup/'

if not (os.path.exists(thedir+city)):
    os.mkdir(thedir+city)

def check_date_version(date,thedir=thedir, city=city):
    # First, check if you already have a scrape file for this object and location
    filen=thedir+city+'/offerup_'+item+'_'+date+'.json'
    if os.path.exists(filen):
            # Okay the file exists for today, but have you done this already?
        if not filen.replace('.json','')[-1].isalpha():
            print('%% A scrape file exists, but doesnt end in alpha character')
            date=date+'a'
        else:
            print('%% A scrape file exists AND ends it ends in an alpha character')
            date=date + chr(ord(filen.replace('.json','')[-1])+1)
    else:
        print("%% I have no scrape record for this object on this date")
    print('====== setting date  =  '+date)
    return date

def scrape_offerup(date, item, thedir=thedir, city=city, cityname=cityname,**kwargs):
    """ Runs a javascript node file to scrape OfferUp for items

    Args:
        date: today's date
        item: The item you want to search for (e.g., couch)

    Returns:
        Returns a DF of the most recent file
    """
    todays_scrape = (thedir+city+'/offerup_'+item+'_'+date+'.json')
    if not os.path.exists(todays_scrape) or ('scrapeagain' in kwargs):
        print('%% No scrape detected for this date and city.')
        print('%% Scraping OfferUp Now')

        # Run the Puppeteer node again to pull the data
        call(["node", thedir+"java_scrape.js",item,cityname])

        print("%% Scrape finished.. moving files.")
        move(thedir+city+'/offerup_'+item+'.json',todays_scrape)
        
        print('============== done!')
        print('file saved to '+todays_scrape)
    else:
        print("%% Looks like you've already done a scrape for today.. ")
        print("%% set flag scrapeagain='a' if you'd like to do it again")

def read_scrape(date,item, thedir=thedir,city=city,**kwargs):
    df=pd.read_json((thedir+city+'/offerup_'+item+'_'+date+'.json'),lines=True)
    df['info'] = df['info'].astype(str).str.lower().transform(ast.literal_eval)
    df.rename(columns={'detailUrl':'url', 'imgUrl':'img'}, inplace=True)
    df = df.drop_duplicates(subset='url', keep="first")
    df = pd.DataFrame(df[~df['url'].str.contains("bing")])
    
    # Sold things go into "sold_df"
    # Things still being sold are under "todays_scrape_df"
    sold_df = pd.DataFrame(df[df['info'].astype(str).str.upper().str.contains("SOLD")])
    todays_scrape_df = pd.DataFrame(df[~df['info'].astype(str).str.upper().str.contains("SOLD")])

    # Write the URL of each object so you can find it
    sold_df['url'] = 'https://offerup.com'+sold_df['url'].astype(str)
    todays_scrape_df['url'] = 'https://offerup.com'+todays_scrape_df['url'].astype(str)
    
    # Extract the object ID 
    objid = [ int(todays_scrape_df['url'][i].split('detail/')[1].replace('/','')) 
             for i,row in todays_scrape_df.iterrows()]    
    todays_scrape_df['id']=objid

    sold_objid = [ int(sold_df['url'][i].split(
        'detail/')[1].replace('/','')) for i,row in sold_df.iterrows()]
    sold_df['id']=sold_objid

    # Now change the index label to be the object ID
    if (sold_df.index.name)!='id':
        sold_df = sold_df.set_index('id')
    if (todays_scrape_df.index.name)!='id':
        todays_scrape_df = todays_scrape_df.set_index('id')


    # Extract the listed price
    prices=[]
    for index, row in todays_scrape_df.iterrows():    
        if 'free' in row['info']:
            row['info'][row['info'].index('free')]='$0.00'
        val=([s for s in row['info'] if ("$" in s) 
              and ("." in s) and (re.search('[a-zA-Z]', s)==None)])[0]
        prices.append( np.float(val.replace('$','').replace(',','')) )
    if not ('price' in todays_scrape_df.columns):
        todays_scrape_df['price']=prices
    
    if 'return_sold' in kwargs:
        return sold_df
    else:
        return todays_scrape_df

# Find the most recent Puppeteer scrape (excluding the one you're about to do) and load it. 
def most_recent_file(item, thedir=thedir,city=city):
    """ Return the most recent file froma  list

    Args:
        param1: a string of the files you want
        param2: The second parameter.

    Returns:
        Returns a DF of the most recent file
    """
    
    files = glob.glob(thedir+city+'/scraped_'+item+'_*-2019*')
    file_date=[]
    for i in files:
        file_date.append(i.split('_')[-1].replace('.csv',''))

    lastdate=max(file_date)
    filen = 'scraped_'+item+'_'+lastdate+'.csv'
    
    print('This is the fiducial database of selling items:\n' + filen)
    fiducial_df = pd.read_csv(thedir+city+'/'+filen)
    # Change index name to be the ID name
    if (fiducial_df.index.name)!='id':
        fiducial_df=fiducial_df.set_index('id')
    if 'Unnamed: 0' in fiducial_df.columns:
        fiducial_df=fiducial_df.drop(columns='Unnamed: 0')
        
    # Extract the post date
    if not 'postdate' in fiducial_df.columns:
        if not np.isnan(fiducial_df['time_since_posting'].iloc[0]):
            now = datetime.now()
            date=now.strftime("%d-%m-%Y")
            postdate = []
            for index, row in tqdm(fiducial_df.iterrows(), total=fiducial_df.shape[0]):
                if row['time_since_posting']!='':
                    postdate.append(now - timedelta(days=row['time_since_posting']))
                else:
                    postdate.append('')
            fiducial_df['postdate']=postdate
        else:
            fiducial_df['postdate']=''
        
    return fiducial_df


def first_scrape(item,todays_scrape_df,date, thedir=thedir,city=city,**kwargs):
    for idetail in ['condition', 'description', 'imgurl', 'postdate','time_since_posting']:
        if not idetail in todays_scrape_df.columns:
            todays_scrape_df[idetail]=''

    # Okay now here we need to scrape each object's webpage to get more detailed information
    icount=0
    
    if 'sold' in kwargs:
        ifsold='sold/'
    else:ifsold=''

    for index, row in islice(todays_scrape_df.iterrows(),todays_scrape_df.shape[0]):
    #for index, row in tqdm_notebook(todays_scrape_df.iterrows(),total=todays_scrape_df.shape[0]):
        #if ((row['description']!= todays_scrape_df.loc[index]['description']) or
        #    (row['price']!= todays_scrape_df.loc[index]['price']) or
        #    (row['condition']!= todays_scrape_df.loc[index]['condition']) or
        #    (row['imgurl']!= todays_scrape_df.loc[index]['imgurl']):
        #    (row['postdate']!= todays_scrape_df.loc[index]['postdate'])):
        
        if not (row['description'] or
                row['condition']!= todays_scrape_df.loc[index]['condition'] or
                row['postdate']!= todays_scrape_df.loc[index]['postdate']):
        #if not (row['time_since_posting']==row['time_since_posting']):
            
            print('%% Scraping info from item '+str(index))
            page = ''
            while page == '':
                try:
                    page = requests.get(row['url'])
                    break
                except requests.exceptions.ConnectionError:
                    print("Connection refused by the server..")
                    print("Let me sleep for 5 seconds")
                    print("ZZzzzz...")
                    time.sleep(5)
                    print("Was a nice sleep, now let me continue...")
                    continue

            soup = BeautifulSoup(page.content,'html.parser')

            postresult =soup.find('div', class_="_147ao2d8")
            
            if postresult==None:
                todays_scrape_df.drop(index, axis=0,inplace=True)
            else:
                time_since_posting=str(postresult).split(
                    'posted-info">Posted ')[1].split('ago in <a class')[0]
                times = ['minutes','hours','days', 'weeks','months', 'years',
                         'minute','hour','day', 'week', 'month', 'year']
                splittime=[1/24/60,1/24,1,7,30,365,
                           1/24/60,1/24,1,7,30,365]

                # clean up time count into float number of days
                for itime in range(len(times)):
                    if times[itime] in str(time_since_posting):
                        time_since_posting= np.float(
                            time_since_posting.replace(times[itime],''))*splittime[itime]

                todays_scrape_df.loc[index,'time_since_posting'] = time_since_posting

                todays_scrape_df.loc[index,'condition'] = (str(
                    soup.find('span', class_="_csmifkq")).split(">")[1].split("</span")[0])

                if 'sold' in kwargs:
                    if soup.find('span', class_="_1pfzjcs")==None:
                        price = (str(soup.find(
                            'span', class_="_ckr320")).split(">")[1].split("</span")[0])
                    else:
                        price = (str(soup.find(
                            'span', class_="_1pfzjcs")).split(">")[1].split("</span")[0])                        
                else:
                    price = (str(soup.find('span', class_="_ckr320")).split(">")[1].split("</span")[0])
                if (price=='free'):price=0.0

                if '$' in str(price):
                    price = price.replace('$','')
                if ',' in str(price):
                    price = price.replace(',','')
                    
                todays_scrape_df.loc[index,'price'] = np.float(price)
                
                # clean up description because it repeats information
                description = (soup.find(attrs={"name": re.compile(r"description", re.I)})['content'])
                description = description.replace(todays_scrape_df['condition'].loc[index]+', ','')
                todays_scrape_df.loc[index,'description'] = description


                if (soup.find_all('img', class_="_fk4cz1")==None) or (
                    len(soup.find_all('img', class_="_fk4cz1"))==0):
                    todays_scrape_df.drop(index, axis=0,inplace=True)
                else: 
                    imgstr=str(soup.find_all('img', class_="_fk4cz1")[0])

                    todays_scrape_df.loc[index,'imgurl'] = (imgstr.split('src="')[1].split('" width')[0])

                    todays_scrape_df.loc[index, 'postdate']=(now - 
                    timedelta(days=np.float(todays_scrape_df.loc[index,'time_since_posting'])))
                        
                    # Download image
                    if not (os.path.exists(thedir+city+'/'+item+'_images/'+ifsold)):
                        os.mkdir(thedir+city+'/'+item+'_images/'+ifsold)
                    offerupdir = (thedir+city+'/'+item+'_images/'+ifsold)
                    outfile=offerupdir+str(index)+".jpg"
                    if not os.path.exists(outfile):
                        urllib.request.urlretrieve(todays_scrape_df.loc[index,'imgurl'], outfile)
                        
                    #if (icount % 10 == 0):
                    #    todays_scrape_df.to_csv(thedir+ifsold[:-1]+'scraped_'+item+'_'+date+'.csv')
                    #icount+=1
    if 'sold' in kwargs:
        todays_scrape_df.to_csv(thedir+city+'/sold_scraped_'+item+'_'+date+'.csv')
    else:
        todays_scrape_df.to_csv(thedir+city+'/scraped_'+item+'_'+date+'.csv')
    return todays_scrape_df

def modify_fiducial(item,fiducial_df, todays_scrape_df,date):
    new=list(todays_scrape_df.index)
    old=list(fiducial_df.index)

    # Figure out which postings are new and which were removed
    new_postings = [x for x in new if x not in old]
    removed_postings = [x for x in old if x not in new]
    
    #for i in sold_df.index:
    #    if i in fiducial_df.index:
    #        print('I was here, now im sold.')
    
    # Drop the removed postings
    fiducial_df.drop(removed_postings, axis=0,inplace=True)

    if (len(fiducial_df)+ len(new_postings))!= len(todays_scrape_df):
        print('%% Something is wrong, youve got a msimatch of DF lengths...')
    
    for idetail in ['condition', 'description', 'imgurl', 'postdate','time_since_posting']:
        if not idetail in todays_scrape_df.columns:
            todays_scrape_df[idetail]=''

    # Add new rows for the new postings
    for i in new_postings:
        if not i in fiducial_df.index:
            fiducial_df = fiducial_df.append( todays_scrape_df.loc[i] )
            
            
    # Okay now here we need to scrape each object's webpage to get more detailed information
    for index, row in islice(fiducial_df.iterrows(), fiducial_df.shape[0]):
    #for index, row in tqdm_notebook(fiducial_df.iterrows(),total=fiducial_df.shape[0]):
        #if ((row['description']!= todays_scrape_df.loc[index]['description']) or
        #    (row['price']!= todays_scrape_df.loc[index]['price']) or
        #    (row['condition']!= todays_scrape_df.loc[index]['condition']) or
        #    (row['imgurl']!= todays_scrape_df.loc[index]['imgurl']):
        #    (row['postdate']!= todays_scrape_df.loc[index]['postdate'])):
        if not (row['description'] or
                row['condition']!= todays_scrape_df.loc[index]['condition'] or
                row['postdate']!= todays_scrape_df.loc[index]['postdate']):
            print('%% Found a new item '+str(index)+
                  '! Either the post is new, the price changed, or some other update.')
            page = ''
            while page == '':
                try:
                    page = requests.get(row['url'])
                    break
                except requests.exceptions.ConnectionError:
                    print("Connection refused by the server..")
                    print("Let me sleep for 5 seconds")
                    print("ZZzzzz...")
                    time.sleep(5)
                    print("Was a nice sleep, now let me continue...")
                    continue

            soup = BeautifulSoup(page.content,'html.parser')
            postresult =soup.find('div', class_="_147ao2d8")
            
            if postresult==None: # "the item has been removed"
                todays_scrape_df.drop(index, axis=0,inplace=True)
            else:
                time_since_posting=str(postresult).split(
                    'posted-info">Posted ')[1].split('ago in <a class')[0]
                times = ['minutes','hours','days', 'weeks','months', 'years',
                         'minute','hour','day', 'week', 'month', 'year']
                splittime=[1/24/60,1/24,1,7,30,365,
                           1/24/60,1/24,1,7,30,365]

                # clean up time count into float number of days
                for itime in range(len(times)):
                    if times[itime] in str(time_since_posting):
                        time_since_posting= np.float(
                            time_since_posting.replace(' '+times[itime]+' ',''))*splittime[itime]

                fiducial_df.loc[index,'time_since_posting'] = time_since_posting

                fiducial_df.loc[index,'condition'] = (
                    str(soup.find('span', class_="_csmifkq")).split(">")[1].split("</span")[0])

                # clean up description because it repeats information
                description = (soup.find(attrs={"name": re.compile(r"description", re.I)})['content'])
                description = description.replace(fiducial_df['condition'].loc[index]+', ','')
                fiducial_df.loc[index,'description'] = description

                imgstr=str(soup.find_all('img', class_="_fk4cz1")[0])
                fiducial_df.loc[index,'imgurl'] = (imgstr.split('src="')[1].split('" width')[0])

                fiducial_df.loc[index, 'postdate']=(now - timedelta(
                    days=np.float(fiducial_df.loc[index,'time_since_posting']))
                                                   )

                # Download image
                offerupdir = (thedir+city+'/'+item+'_images/')
                outfile=offerupdir+str(index)+".jpg"
                if not os.path.exists(outfile):
                    urllib.request.urlretrieve(fiducial_df.loc[index,'imgurl'], outfile)

                thetype = (type(fiducial_df.loc[index,'time_since_posting']))
                if thetype != np.float:
                    fiducial_df.drop(index,axis=0,inplace=True)
    return fiducial_df

# ======================================================================
# Running scrape here
# ======================================================================

#date = check_date_version(date,thedir=thedir,city=city)
print('\n ==== scraping for '+cityname+' '+item+'\n')
scrape_offerup(date,item)

todays_scrape_df = read_scrape(date,item)
sold_df = read_scrape(date,item, return_sold=True)

# Load the fiducial list
files = glob.glob(thedir+city+'/scraped_'+item+'_*-2019*')
if not files:
    # No run exists yet for this object
    print('no scrapes done for this object, starting from scratch')
    fiducial_df = first_scrape(item,todays_scrape_df,date)
else:
    print('okay, so at least one exists')
    fiducial_df = most_recent_file(item)


# Save the "sold" list and append to master file
tsold=first_scrape(item,sold_df,date,sold=True)

if not os.path.isfile(thedir+city+'/all_'+item+'_sold.csv'):
    print('writing new "sold" file')
    tsold.to_csv(thedir+city+'/all_'+item+'_sold.csv', index=True)
else:
    print('appending to existing "sold" file')
    all_sold=pd.read_csv(thedir+city+'/all_'+item+'_sold.csv', index_col='id')
    all_sold=all_sold.append(tsold, sort=True)
    all_sold = all_sold.drop_duplicates(subset='url', keep="first")
    all_sold.to_csv(thedir+city+'/all_'+item+'_sold.csv', index_label='id')
print('"sold" file now updated to '+ '"all_'+item+'_sold.csv"')


modified_df = modify_fiducial(item,fiducial_df, todays_scrape_df, date)
modified_df.to_csv(thedir+city+'/scraped_'+item+'_'+date+'.csv', index=True)
copyfile(thedir+city+'/scraped_'+item+'_'+date+'.csv', thedir+city+'/fiducial_'+item+'.csv')


# delete things that are in the images directory but not in the living fiducial list
indir = os.listdir(thedir+city+'/'+item+'_images/')
indir.remove('sold')
files = [str(i)+'.jpg' for i in list(modified_df.index)]

if len(list(set(indir)-set(files)))!=0:
    for i in (list(set(indir)-set(files))):
        os.remove(thedir+city+'/'+item+'_images/'+i)




print('. . . . . . . . . Modified file saved to '+'scraped_'+item+'_'+date+'.csv')
print('. . . . . . . . .                   and fiducial_'+item+'.csv')

#from to_sql import to_sql
#to_sql(thedir, city, item)
#print('. . . . . . . . .                   and to SQL as well!')
