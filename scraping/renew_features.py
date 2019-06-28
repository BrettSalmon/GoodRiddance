#!/usr/bin/env python

import numpy as np
import pandas as pd
import my_cosine_similarity as cs
import sys

item = sys.argv[1]
cityname = sys.argv[2].title()
city=cityname.lower().replace(' ','_')

thedir='/Users/bsalmon/BrettSalmon/data_science/Insight/goodriddance/scraping/'

cs.run(item, city, thedir+'offerup/', 'offerup',first=False, features_only=True)
print('Finished regenerating image features. File saved and ready for upload to AWS')
