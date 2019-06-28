#!/bin/bash

#python run_scrape.py couch 'Los Angeles'
#python run_scrape.py dresser 'Los Angeles'
#python run_scrape.py table 'Los Angeles'
#python run_scrape.py chair 'Los Angeles'
#rsync -auvz los_angeles/fiducial_* ubuntu@13.52.168.176:goodriddance/scraping/offerup/los_angeles/
#rsync -auvz los_angeles/cnn/ ubuntu@13.52.168.176:goodriddance/scraping/offerup/los_angeles/cnn/

#python run_scrape.py couch 'Baltimore'
#python run_scrape.py dresser 'Baltimore'
#python run_scrape.py table 'Baltimore'
#python run_scrape.py chair 'Baltimore'
rsync -auvz baltimore/fiducial_* ubuntu@13.52.168.176:goodriddance/scraping/offerup/baltimore/
rsync -auvz baltimore/cnn/ ubuntu@13.52.168.176:goodriddance/scraping/offerup/baltimore/cnn/
#
#python run_scrape.py couch 'Santa Monica'
#python run_scrape.py dresser 'Santa Monica'
#python run_scrape.py table 'Santa Monica'
#python run_scrape.py chair 'Santa Monica'
#rsync -auvz santa_monica/fiducial_* ubuntu@13.52.168.176:goodriddance/scraping/offerup/santa_monica/
#rsync -auvz santa_monica/cnn/ ubuntu@13.52.168.176:goodriddance/scraping/offerup/santa_monica/cnn/
