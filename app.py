from flask import Flask, request
from main import query_tweets

app = Flask(__name__)
@app.route('/query_tweets', methods=['POST'])
def query():
    return query_tweets(request)
