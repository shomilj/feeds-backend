import pandas as pd
import numpy as np
import twint
import json
import openai
from textblob import TextBlob
import nest_asyncio
nest_asyncio.apply()

DEFAULT_KEYWORDS = ["trump", "impeachment", "bachelor", "covid"]

INFLUENCER_MAP = {
    'elonmusk': ['dogecoin', 'POTUS', 'cleantechnica', 'TheOnion', 'TheBabylonBee', 'karpathy', 'Astro_Soichi', 'PopMech', 'PyTorch', 'Nigel_Lockyer', 'jagarikin', 'AstroVicGlover', 'Grimezsz', 'TashaARK'],
    'satyanadella': ['Herbert_Diess', 'ChrstnKlein', 'vasujakkal', 'amandaksilver', 'nicoledezen', 'KingJames', 'drhew', 'panos_panay', 'youngdchris', 'MicrosoftWomen'],
    'vp': ['LaCasaBlanca', 'SecondGentleman', 'FLOTUS', 'POTUS', 'WhiteHouse', 'SenatorHick', 'RepBowman', 'RepRitchie', 'AlexPadilla4CA', 'AstroAnnimal', 'CASOSvote', 'CAPAction', 'RobBontaCA'], 
    'stephencurry30': ['BryceCash6', 'Patty_Mills', 'RealDealBeal23', 'gusjohnson', 'arneduncan', 'PatrikFrisk', 'iamcarljones', 'zlurie', 'TSM', 'QCook323'],    
}
openai.api_key = "sk-8xLMvhl5qyjjmajkSRQeEuggYQTdspJViTCInd9Y"

def get_tweets_helper(keyword, min_likes, min_retweets, min_replies, limit, verified):
    c = twint.Config()
    c.Limit = limit
    c.Search = keyword
    c.Language = "en"
    c.Pandas = True
    c.Store_object = False
    c.Hide_output = True
    c.User_full = True
    c.Min_likes = min_likes
    c.Verified = verified
    c.Min_replies = min_replies
    c.Min_retweets = min_retweets
    twint.run.Search(c)
    tweets = twint.storage.panda.Tweets_df
    return tweets

def get_tweets(keyword=None, min_likes=None, min_retweets=None, min_replies=None, limit=100, verified=None):
    if keyword:
        return get_tweets_helper(keyword, min_likes=min_likes, min_retweets=min_retweets, min_replies=min_replies, limit=limit, verified=verified)
    else:
        tweets = []
        for key in DEFAULT_KEYWORDS:
            tweets.append(get_tweets_helper(key, min_likes=min_likes, min_retweets=min_retweets, min_replies=min_replies, limit=limit, verified=verified))
        return pd.concat(tweets)

def get_controversial(keyword=None):
    textblob = get_tweets(keyword=keyword, min_likes=500, limit=500)
    textblob['tweet'] = textblob['tweet'].astype(str)
    polarity = lambda x: TextBlob(x).sentiment.polarity
    textblob['polarity'] = textblob['tweet'].apply(polarity)
    controversial_tweets = textblob[textblob['polarity'] > 0.30]
    return controversial_tweets

def get_explained(keyword=None):
    tweets = get_tweets(keyword=keyword, limit=1000, min_likes=50)
    return tweets[tweets['tweet'].str.contains('analysis|explanation|explained', regex=True)]

def get_verified(keyword=None):
    return get_tweets(keyword=keyword, limit=100, verified=True)

def get_viral(keyword=None):
    return get_tweets(keyword, min_likes=50000, min_retweets=1000, min_replies=1000)

def get_user_tweets(username, keyword=None, limit=10):
    c = twint.Config()
    c.Pandas = True
    c.Search = keyword
    c.Store_object = False
    c.Limit = limit
    c.Hide_output = True
    c.Username = username
    twint.run.Search(c)
    tweets = twint.storage.panda.Tweets_df
    return tweets

def get_influencer_feed(influencer, keyword=None):
    following = INFLUENCER_MAP[influencer]
    tweets = []
    for user in following:
        tweets.append(get_user_tweets(username=user, keyword=keyword))
    return pd.concat(tweets)

def get_openai_positive(keyword=None):
    positive_tweets = []
    for i, tweet in get_tweets(keyword).iterrows():
        response = openai.Completion.create(
          engine="davinci",
          prompt=f"Social media post: \"{tweet.tweet}\"\nSentiment (positive, neutral, negative):",
          temperature=0,
          max_tokens=1,
          top_p=1,
          frequency_penalty=0,
          presence_penalty=0
        )
        sentiment = response["choices"][0]["text"]
        if 'positive' in sentiment.lower():
            positive_tweets.append(tweet)
    return pd.DataFrame(positive_tweets)

def api(algo, keyword=None):
    try:
        if algo.startswith('influencer-'):
            result = get_influencer_feed(algo.split("-")[1], keyword=keyword)
        else:
            algorithms = {
                'controversial': get_controversial,
                'explained': get_explained,
                'verified': get_verified,
                'viral': get_viral,
                'positive': get_openai_positive,
            }
            result = algorithms[algo](keyword=keyword)
        filtered = result[['conversation_id', 'created_at', 'tweet', 'user_id', 'username', 'name', 'nlikes', 'nreplies', 'nretweets']]
        data = filtered.reset_index(drop=True).to_json(orient="index")
        return json.dumps(list(json.loads(data).values()))
    except Exception as e:
        print(e)
        return json.dumps({'error': str(e)})