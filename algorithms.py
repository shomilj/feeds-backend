#!/usr/bin/env python

import pandas as pd
import numpy as np
import twint
import json
from textblob import TextBlob
import nest_asyncio
nest_asyncio.apply()

def get_tweets(keyword, num_posts):
    c = twint.Config()
    c.Limit = num_posts
    c.Search = keyword
    c.Language = "en"
    c.Pandas = True
    c.Store_object = False
    c.Hide_output = True
    c.User_full = True
    twint.run.Search(c)
    tweets = twint.storage.panda.Tweets_df
    return tweets

def get_controversial(keyword, num_posts):
    textblob = get_tweets(keyword, num_posts)
    textblob['tweet'] = textblob['tweet'].astype(str)
    polarity = lambda x: TextBlob(x).sentiment.polarity
    subjectivity = lambda x: TextBlob(x).sentiment.subjectivity
    textblob['polarity'] = textblob['tweet'].apply(polarity)
    textblob['subjectivity'] = textblob['tweet'].apply(subjectivity)

    controversial_tweets = textblob[textblob['polarity'] > 0.1]
    return controversial_tweets

def get_tweets_using_algorithm(algorithm, keyword):
    num_posts = 100
    if('controversial' in algorithm):
        tweets = get_controversial(keyword, num_posts)
    elif('explained' in algorithm):
        tweets = get_explained(keyword, 1000)
    elif('influencer' in algorithm):
        _, username = algorithm.split("-", 1)
        tweets = get_influencer_feed(username, keyword, num_posts)
    elif('viral' in algorithm):
        tweets = get_viral(keyword, 100)
    elif('verified' in algorithm):
        tweets = get_verified(keyword, 100)
    else:
        tweets = pd.DataFrame()
    result = tweets.to_json(orient="index")
    parsed = list(json.loads(result).values())
    json_tweets = json.dumps(parsed, indent=4)
    return json_tweets

