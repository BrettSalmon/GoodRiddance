#!/usr/bin/env python
# coding: utf-8

import numpy as np
from PIL import Image
import streamlit as st
from keras_preprocessing import image
from keras.models import load_model, Model
from keras.callbacks import ModelCheckpoint
from keras.applications.vgg16 import VGG16, preprocess_input
from keras.applications.imagenet_utils import preprocess_input
from keras import backend as K

from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split

import os
import time
import logging
import inspect
from tqdm import tqdm
from shutil import copyfile
from argparse import ArgumentParser
from sematic_utils import load_paired_img_wrd
from vector_search import vector_search
from sklearn.metrics.pairwise import cosine_similarity

def load_images(folder):
    class_names = [fold for fold in os.listdir(folder) if ".DS" not in fold]
    image_list = []  
    paths_list = []

    files=os.listdir(folder)
    for i in files:
        if i[-4:]!='.jpg':
            files.remove(i)
    print("%% Loading latest image files. . .\n")
    for file in tqdm(files):
        full_path = os.path.join(folder, file)
        img = image.load_img(full_path, target_size=(224, 224))
        x_raw = image.img_to_array(img)
        x_expand = np.expand_dims(x_raw, axis=0)
        x = preprocess_input(x_expand)
        image_list.append(x)
        paths_list.append(full_path)
        
    img_data = np.array(image_list)
    img_data = np.rollaxis(img_data, 1, 0)
    img_data = img_data[0]

    return img_data, paths_list

def load_headless_pretrained_model():
    """
    Loads the pretrained version of VGG with the last layer cut off
    :return: pre-trained headless VGG16 Keras Model
    """
    #Before prediction
    K.clear_session()

    pretrained_vgg16 = VGG16(weights='imagenet', include_top=True)
    model = Model(inputs=pretrained_vgg16.input,
                  outputs=pretrained_vgg16.get_layer('fc1').output)
    return model

def generate_features(image_paths, model):
    """
    Takes in an array of image paths, and a trained model.
    Returns the activations of the last layer for each image
    :param image_paths: array of image paths
    :param model: pre-trained model
    :return: array of last-layer activations, and mapping from array_index to file_path
    """
    start = time.time()
    images = np.zeros(shape=(len(image_paths), 224, 224, 3))
    file_mapping = {i: f for i, f in enumerate(image_paths)}

    # We load all our dataset in memory because it is relatively small
    for i, f in enumerate(image_paths):
        img = image.load_img(f, target_size=(224, 224))
        x_raw = image.img_to_array(img)
        x_expand = np.expand_dims(x_raw, axis=0)
        images[i, :, :, :] = x_expand

    logging.info("%s images loaded" % len(images))
    inputs = preprocess_input(images)
    logging.info("Images preprocessed")
    images_features = model.predict(inputs)
    end = time.time()
    logging.info("Inference done, %s Generation time" % (end - start))
    return images_features, file_mapping

def run(item, city, thedir, site, input_file=False,
        outdir='myflask/static/matches/', first=False,
        sold=False,
        topn=12):
    """
        Puts everything together: loads the model, loads the features, 
        applies cosine similarity and returns the matching 10 items
    
        Args:
            item: The item you want to search for (e.g., couch)
            city: The city where you are searching
            thedir: the primary directory (defined early and passes around 
                    for easily porting all programs elsewhere (e.g., AWS)
    
        Returns:
            Nothing, but copies matching items to a temporary directory
    """
    #item='couch'
    #city='los_angeles'
    #thedir='/Users/bsalmon/BrettSalmon/data_science/Insight/goodriddance/scraping/offerup/'
    if not sold: 
        folder=(thedir+city+'/'+item+'_images/')
        features_path=(thedir+city+'/cnn/'+item+'_features/')
        file_mapping_path=(thedir+city+'/cnn/'+item+'_file_mapping/')
        if not os.path.exists(features_path.replace(features_path.split('/')[-2]+'/','')):
            os.mkdir(features_path.replace(features_path.split('/')[-2]+'/',''))
        if not os.path.exists(features_path):
            os.mkdir(features_path)
        if not os.path.exists(file_mapping_path):
            os.mkdir(file_mapping_path)
    else:
        folder=(thedir+city+'/'+item+'_images/sold/')
        features_path=(thedir+city+'/cnn/sold_'+item+'_features/')
        file_mapping_path=(thedir+city+'/cnn/sold_'+item+'_file_mapping/')
        if not os.path.exists(features_path):
            os.mkdir(features_path)
        if not os.path.exists(file_mapping_path):
            os.mkdir(file_mapping_path)
        

   
    model = load_headless_pretrained_model()

    # I'll load all images into memory because it's not that many
    #images=np.load(features_path+'images.npy')
    #image_paths=np.load(features_path+'image_paths.npy')
    if first:
        if item=='couch':plural='es'
        else: plural='s'
        print("%% You are generating the image features for all "+item+plural+" from "+city)
        images, image_paths = load_images(folder)
        #np.save(features_path+'images',images)
        #np.save(features_path+'image_paths',np.array(image_paths))

        images_features, file_index = generate_features(image_paths, model)
        vector_search.save_features(features_path, images_features, file_mapping_path, file_index)
    else:
        print("%% You already have the image features in hand-- loading them from disk.")
        images_features, file_index = vector_search.load_features(features_path, file_mapping_path)
        #images=np.load(features_path+'images.npy')
        #image_paths=np.load(features_path+'image_paths.npy')
    
    # Define the location of the file uploaded by the user
    if not input_file:
        tfiles = os.listdir('myflask/static/uploads/')
        for ifile in tfiles:
            if ifile.endswith(".jpg"):input_file='myflask/static/uploads/'+ifile

    # Load in the single input image from the user
    print(input_file)
    img = image.load_img(input_file, target_size=(224,224))
    x_raw = image.img_to_array(img)
    x_expand = np.expand_dims(x_raw,axis=0)
    
    # Extract the image features according to the headless model
    singleinput = preprocess_input(x_expand)
    single_image_features = model.predict(singleinput)
    
    # Apply cosine_similarities between features of loaded image
    # and features of all directory images
    print("%% That was fast! Applying cosine similarity and finding images")
    cosine_similarities = (cosine_similarity(single_image_features, images_features)[0])

    # Get top N similar image ID numbers
    top_N_idx = (np.argsort(cosine_similarities)[-topn:])[::-1]
   
    # Get top 10 similar image files
    topfiles = [file_index[i] for i in top_N_idx]
   
    # Move them to a happy static folder
    barefiles = []
    match_ids = []
    for i in range(len(topfiles)):
        copyfile(topfiles[i],outdir+site+'/'+topfiles[i].split('/')[-1])
        barefiles.append(topfiles[i].split('/')[-1])
        match_ids.append(int(topfiles[i].split('/')[-1].replace('.jpg','')))

    #After prediction
    K.clear_session()

    print("%% Cosine similarity complete. Matched "+
          "images are in myflask/static/matches/"+site)
    return barefiles, match_ids, (np.sort(cosine_similarities)[-topn:])[::-1]

##########################################################################

