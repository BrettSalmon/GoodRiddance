#!/usr/bin/env python
# coding: utf-8
from astropy.stats import sigma_clip
from scipy import stats
import numpy as np
def final_answer(offerup_prices,offerup_days, craigslist_prices,craigslist_days):
    offerup_prices=np.array(offerup_prices)
    offerup_days=np.array(offerup_days)
    craigslist_prices=np.array(craigslist_prices)
    craigslist_days=np.array(craigslist_days)

    craigslist_filter = sigma_clip(craigslist_prices, sigma=2, maxiters=5)
    offerup_filter = sigma_clip(offerup_prices, sigma=2, maxiters=5)

    slope, intercept, r_value, p_value, std_err = stats.linregress(offerup_days[~offerup_filter.mask], 
                                                                   offerup_prices[~offerup_filter.mask])
    offerup_slope = slope
    offerup_intercept = intercept
    offerup_pvalue = p_value

    slope, intercept, r_value, p_value, std_err = stats.linregress(craigslist_days[~craigslist_filter.mask], 
                                                                   craigslist_prices[~craigslist_filter.mask])
    craigslist_slope = slope
    craigslist_intercept = intercept
    craigslist_pvalue = p_value

    sites = ['offerup', 'craigslist']

    craigslist_sigclip_prices= craigslist_prices[~craigslist_filter.mask]
    craigslist_sigclip_days= craigslist_days[~craigslist_filter.mask]

    offerup_sigclip_prices= offerup_prices[~offerup_filter.mask]
    offerup_sigclip_days= offerup_days[~offerup_filter.mask]


    early_means = [np.mean(offerup_sigclip_prices[offerup_sigclip_days < 2]),
                   np.mean(craigslist_sigclip_prices[craigslist_sigclip_days < 2])]
    early_std = [np.std(offerup_sigclip_prices[offerup_sigclip_days < 2]),
                 np.std(craigslist_sigclip_prices[craigslist_sigclip_days < 2])]

    late_means =[np.mean(offerup_sigclip_prices[offerup_sigclip_days >= 2]), 
                 np.mean(craigslist_sigclip_prices[craigslist_sigclip_days >= 2])]
    late_std = [np.std(offerup_sigclip_prices[offerup_sigclip_days >= 2]),
                np.std(craigslist_sigclip_prices[craigslist_sigclip_days >= 2])]

    early_result = [sites[np.argmax( np.array(early_means)/np.array(early_std) )], np.mean(early_means)]
    late_result = [sites[np.argmax( np.array(late_means)/np.array(late_std))], np.mean(late_means)]
    return early_result, late_result
