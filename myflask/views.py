from flask import session, redirect, url_for, render_template, request, Response
from flask_wtf import FlaskForm
from wtforms import Form, BooleanField, StringField, SelectField, validators, SubmitField
from flask_wtf.file import FileField, FileRequired

from myflask import app
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
import psycopg2
from werkzeug.utils import secure_filename
import os
import subprocess
from shutil import copyfile

import my_cosine_similarity as cs

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

user = 'bsalmon' #add your username here (same as previous postgreSQL)            
host = 'localhost'
dbname = 'goodriddnce'
db = create_engine('postgres://%s%s/%s'%(user,host,dbname))
con = None
con = psycopg2.connect(database = dbname, user = user)

class UploadForm(FlaskForm):
    city = StringField(u'City', render_kw={"placeholder": "e.g., Los Angeles"})
    image = FileField(validators=[FileRequired()])
    furnitures = SelectField(u'Select Furniture', 
                             choices=[(None, 'Select One:'),
                                      ('chair', 'Chair'), 
                                      ('dresser', 'Dresser'), 
                                      ('table', 'Table'), 
                                      ('couch', 'Couch')] )
    submit = SubmitField(u'Upload')
#@app.route('/index')
#def index():
#    return render_template("index.html",
#       title = 'Home', user = { 'nickname': 'Michael' },
#       )

@app.route('/upload', methods=['GET', 'POST'])
def goodriddnce_input():
    form = UploadForm()
    return render_template("upload.html", form=form)

@app.route('/result', methods=['GET','POST'])
def result():
    thedir='/Users/bsalmon/BrettSalmon/data_science/Insight/goodriddance/scraping/'
    """Main page"""
    form = UploadForm()

    # Before you start, clear out all the upload files and matches
    dirs=['uploads/','matches/craigslist/','matches/offerup/']
    for idir in dirs:
        files = os.listdir('myflask/static/'+idir)
        for ifile in files:
           os.remove('myflask/static/'+idir+ifile)

    item = form.furnitures.data
    item= str(item).lower()
    cityname = form.city.data.title()
    city=cityname.lower().replace(' ','_')

    # This is the path to the user-uploaded file
    filename = secure_filename(form.image.data.filename)
    input_path='../static/uploads/'+filename
    form.image.data.save( os.path.join('myflask/static/uploads/', filename) )
   
    (offerup_image_paths,offerup_image_ids,
     offerup_cs) = cs.run(item, city, thedir+'offerup/', 
                          'offerup',first=False)
    offerup_df=pd.read_csv(thedir+'offerup/'+city+'/fiducial_'+item+'.csv', index_col='id')
    offerup_prices=[]
    offerup_days=[]
    offerup_valdays=[]
    offerup_imgurl=[]

    (craigslist_image_paths,craigslist_image_ids,
     craigslist_cs) = cs.run(item, city, thedir+'craigslist/', 
                             'craigslist',first=False)
    craigslist_df=pd.read_csv(thedir+'craigslist/'+city+'/fiducial_'+item+'.csv', index_col='id')
    craigslist_prices=[]
    craigslist_days=[]
    craigslist_valdays=[]
    craigslist_imgurl=[]

    #(fiducial_df.loc[output.iloc[0]['id'],'imgurl'])
    for i in range(12):
        offerup_valdays.append(offerup_df.loc[offerup_image_ids[i],'time_since_posting']) 
        tdays= round(offerup_df.loc[offerup_image_ids[i],'time_since_posting'])
        if tdays==0:tdays='< 1 day'
        elif tdays==1: tdays='1 day'
        else: tdays=str(tdays)+' days'
        offerup_days.append(tdays) 

        offerup_prices.append( int(offerup_df.loc[offerup_image_ids[i],
                                                  'price']) )
        offerup_imgurl.append(offerup_df.loc[offerup_image_ids[i],'imgurl'])

        craigslist_valdays.append(craigslist_df.loc[craigslist_image_ids[i],'time_since_posting']) 
        tdays= round(craigslist_df.loc[craigslist_image_ids[i],'time_since_posting'])
        if tdays==0: tdays='< 1 day'
        elif tdays==1: tdays='1 day'
        else: tdays=str(tdays)+' days'

        craigslist_prices.append( int(craigslist_df.loc[craigslist_image_ids[i],
                                                        'price']) )
        craigslist_days.append( tdays)
        craigslist_imgurl.append(craigslist_df.loc[craigslist_image_ids[i],'imgurl'])

    #copyfile(thedir+city+'/'+item+'_images/'+filename,'myflask/static/uploads/')
    the_result=str(item) +' around '+str(cityname)

    from final_answer import final_answer
    (early_result, late_result) = final_answer(offerup_prices,offerup_valdays, 
                                               craigslist_prices,craigslist_valdays)
    early_result[0]=early_result[0].title()
    late_result[0]=late_result[0].title()
    early_result[1]=round(early_result[1])
    late_result[1]=round(late_result[1])

    ## do whatever you need to do here, then send output to show in HTML
    return render_template('result.html', form=form, the_result=the_result, 
                            offerup_prices=offerup_prices, offerup_imgurl=offerup_imgurl, 
                            offerup_days=offerup_days,
                            craigslist_prices=craigslist_prices, craigslist_imgurl=craigslist_imgurl, 
                            craigslist_days=craigslist_days,
                            input_path=input_path, 
                            early_result=early_result,late_result=late_result)
#@app.route('/input')
#def city_input():
#    return render_template("city.html")
##    city_name = request.args.get('city_name')
##    print("I have found the city! It's: "+str(city_name))
##    return 'text'
#
#@app.route('/db')
#def birth_page():
#    sql_query = """                                                             
#                SELECT * FROM birth_data_table WHERE delivery_method='Cesarean'\
#;                                                                               
#                """
#    query_results = pd.read_sql_query(sql_query,con)
#    births = ""
#    print(query_results[:10])
#    for i in range(0,10):
#        births += query_results.iloc[i]['birth_month']
#        births += "<br>"
#    return births
#
#@app.route('/db_fancy')
#def cesareans_page_fancy():
#    sql_query = """
#               SELECT index, attendant, birth_month FROM birth_data_table WHERE delivery_method='Cesarean';
#                """
#    query_results=pd.read_sql_query(sql_query,con)
#    births = []
#    for i in range(0,query_results.shape[0]):
#        births.append(dict(index=query_results.iloc[i]['index'], attendant=query_results.iloc[i]['attendant'], birth_month=query_results.iloc[i]['birth_month']))
#    return render_template('cesareans.html',births=births)
#
#@app.route('/output', methods=['GET','POST'])
#def city_output():
#    #pull 'birth_month' from input field and store it
#    city = request.args.get('city_name')
#      #just select the Cesareans  from the birth dtabase for the month that the user inputs
#    #query = "SELECT index, attendant, birth_month FROM birth_data_table WHERE delivery_method='Cesarean' AND birth_month='%s'" % patient
#    #print(query)
#    #query_results=pd.read_sql_query(query,con)
#    #print(query_results)
#    #births = []
#    #for i in range(0,query_results.shape[0]):
#    #    births.append(dict(index=query_results.iloc[i]['index'], 
#    #                  attendant=query_results.iloc[i]['attendant'], 
#    #                  birth_month=query_results.iloc[i]['birth_month']))
#    #the_result = ModelIt(patient,births)
#    if city == None:
#        the_result='bananas'
#    else:
#        the_result = city
#    return render_template("output.html", the_result = the_result)
#
