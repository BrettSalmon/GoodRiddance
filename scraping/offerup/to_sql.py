#!/usr/bin/env python
# coding: utf-8
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import psycopg2
import pandas as pd

def to_sql(thedir, city, item):
    fiducial_filn = thedir+city+'/fiducial_'+item+'.csv'

    dbname = 'goodriddnce'
    username = 'bsalmon' # change this to your username

    engine = create_engine('postgres://%s@localhost/%s'%(username,dbname))

    print(engine.url)
    ## create a database (if it doesn't exist)
    #if not database_exists(engine.url):
    #    create_database(engine.url)
    #print(database_exists(engine.url))
    
    item_data = pd.read_csv(thedir+city+'/fiducial_'+item+'.csv', index_col=0)
    item_data.to_sql(city+'_'+item+'_data_table', engine, if_exists='replace')
    return 
