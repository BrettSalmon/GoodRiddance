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

import cosine_similarity as cs

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
    thedir='/Users/bsalmon/BrettSalmon/data_science/Insight/scraping/offerup/'
    """Main page"""
    form = UploadForm()
    files = os.listdir('myflask/static/uploads/')
    for ifile in files:
       os.remove('myflask/static/uploads/'+ifile)
    files = os.listdir('myflask/static/matches/')
    for ifile in files:
       os.remove('myflask/static/matches/'+ifile)

    item = form.furnitures.data
    item= str(item).lower()
    cityname = form.city.data.title()
    city=cityname.lower().replace(' ','_')
    #if form.validate_on_submit():
    filename = secure_filename(form.image.data.filename)
    form.image.data.save( os.path.join('myflask/static/uploads/', filename) )
   
    #search=("python /Users/bsalmon/BrettSalmon/data_science/Insight/semantic-search/search.py"+
    #          #" --input_image uploads/"+filename+
    #          " --input_image "+thedir+city+'/'+item+'_images/'+filename+
    #          " --features_path "+thedir+city+"/cnn/"+item+"_features/"+
    #          " --file_mapping  "+thedir+city+"/cnn/"+item+"_file_mapping/"+
    #          " --index_boolean False"+
    #          " --features_from_new_model_boolean False")
    #search=["python", "/Users/bsalmon/BrettSalmon/data_science/Insight/semantic-search/search.py"+
    #          #" --input_image uploads/"+filename+
    #          " --input_image "+thedir+city+'/'+item+'_images/'+filename+
    #          " --features_path "+thedir+city+"/cnn/"+item+"_features/"+
    #          " --file_mapping  "+thedir+city+"/cnn/"+item+"_file_mapping/"+
    #          " --index_boolean False"+
    #          " --features_from_new_model_boolean False"]
    #proc = subprocess.call(search, stdout=f)
    output=subprocess.check_output(search, shell=True, stderr=subprocess.STDOUT)
    output = output.decode("utf-8").split('...')[-1]
    output = pd.DataFrame(eval(output), columns=['id', 'file', 'match'])
    output['objid']=[int(i.split('/')[-1].replace('.jpg','')) for i in output['file']]
    output = output.set_index('objid')
    #output = output.drop('Unnamed: 0', axis=1)
    output.to_csv('matches.csv', index=True)

    fiducial_df=pd.read_csv(thedir+city+'/fiducial_'+item+'.csv', index_col='id')
    prices=[]
    images=[]
    imgurl=[]

    #(fiducial_df.loc[output.iloc[0]['id'],'imgurl'])
    for i in range(len(output)):
        prices.append(fiducial_df.loc[output.index[i],'price'])
        imgurl.append(fiducial_df.loc[output.index[i],'imgurl'])

        imgfile=output.loc[output.index[i]]['file'].split('/')[-1]
        copyfile(output.loc[output.index[i]]['file'],'myflask/static/matches/'+imgfile)
        images.append(imgfile)

    input_path='../static/uploads/'+filename
    print(thedir+city+'/'+item+'_images/'+filename)
    copyfile(thedir+city+'/'+item+'_images/'+filename,'myflask/static/uploads/')
    #out.to_csv('out.csv')
    the_result=str(item) +' around '+str(cityname)
    ## do whatever you need to do here, then send output to
    ## show in HTML
    return render_template('result.html', form=form, the_result=the_result, 
                            prices=prices, images=images, imgurl=imgurl,
                            input_path=input_path)
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
