#!/user/bin/python

'''
   Copyright (c) 2016 Rory Hool
   
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
   
       http://www.apache.org/licenses/LICENSE-2.0
   
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

import groupme
import json
import keystore
import os
import pickle
import requests
import sys
import time

from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import create_engine
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class SubredditResult():
    exists = False
    suggestion = None
    error = None

class RedditArchive( Base ):
    __tablename__ = 'RedditArchive'

    id = Column(Integer, primary_key=True)
    subreddit = Column(String)
    jsonFile = Column(String)
    timeStamp = Column(Float)    

    def __repr__( self ):
        return "<RedditArchive(subreddit='%s', jsonFile='%s', timeStamp='%f')>" % (self.subreddit, self.jsonFile, self.timeStamp) 

def get_engine():
    engine = create_engine('sqlite:///RedditArchives.db')
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind = engine)
    session = Session()
    return session

def create_reddit_archive(subreddit, jsonFile):
    session = get_session()
    redditArchive = RedditArchive(subreddit = subreddit, jsonFile = jsonFile, timeStamp = time.time())
    session.add(redditArchive)
    session.commit()
    session.close()
    return get_reddit_archive(subreddit)

def get_reddit_archive(subreddit):
    session = get_session()
    archive = session.query(RedditArchive).filter_by(subreddit = subreddit).first()
    session.close()
    return archive

def download_hot_list(subreddit, afterId):
    reddit_url = 'http://api.reddit.com/r/{0}/hot?over_18=true'.format(subreddit)

    print "Reddit url is", reddit_url
    if afterId is not None:
        reddit_url += '&after=' + afterId

    headers = {
        'User-Agent': 'GroupMe Bot'
    }

    r = requests.get(reddit_url, headers = headers)
    if r.status_code == 200:
        try:
            jsonDict = r.json()
            return jsonDict
        except ValueError:
            error = 'Value error when getting json for /r/' + subreddit
            print error
            return error
    else:
        if r.status_code == 404:
            return None
        elif r.status_code == 429:
            keystore.put('timeout_until', time.time() + 900)
            return 'Reddit is rate-limiting rbot, sleeping for 15 minutes'
        elif r.status_code == 403:
            message = "Failed to download /r/{0}, it may be private ({1})".format(subreddit, r.status_code)
            print message
            return message
        else:
            message = "Failed to download /r/{0}, got status code {1}".format(subreddit, r.status_code)
            print message
            return message

def save_json_to_file(jsonDict, fileName):
    if jsonDict is not None:
        with open(fileName, 'w+') as json_file:
            json_file.write(json.dumps(jsonDict))

def update_archive(archive):
    print "Updating archive", archive.subreddit

    result = download_hot_list(archive.subreddit, None)
    
    print result
    if type(result) is str:
        return result
    
    jsonDict = result

    reddit_json_directory = 'reddit-json'
    if not os.path.exists(reddit_json_directory):
        os.makedirs(reddit_json_directory)

    jsonFileName = '{0}/reddit-{1}-hot.json'.format(reddit_json_directory, archive.subreddit)
    
    save_json_to_file(jsonDict, jsonFileName)
        
    archive.timeStamp = time.time()

    session = get_session()
    session.add(archive)
    session.commit()

    return None

def load_json_from_file(fileName):
    with open(fileName, 'r') as json_file:
        jsonstr = json_file.read()
        jsonDict = json.loads(jsonstr)
    
        return jsonDict

def save_recent_urls(bot_id, recentUrls):
    pickles_directory = 'pickles'
    if not os.path.exists(pickles_directory):
        os.makedirs(pickles_directory)

    recentURLsFileName = '{0}/recentURLS-{1}.pickle'.format(pickles_directory, bot_id)
    with open(recentURLsFileName, 'w+') as recentUrlsFile:
        pickle.dump(recentUrls[:500], recentUrlsFile)

def get_recent_urls(bot_id):
    pickles_directory = 'pickles'
    if not os.path.exists(pickles_directory):
        os.makedirs(pickles_directory)

    recentURLsFileName = '{0}/recentURLS-{1}.pickle'.format(pickles_directory, bot_id)
    
    recentUrls = list()
    
    if os.path.isfile(recentURLsFileName):
        with open(recentURLsFileName, 'r') as recentUrlsFile:
            recentUrls = pickle.load(recentUrlsFile)

    return recentUrls

def subreddit_exists(subreddit):
    print "subreddit_exists(", subreddit, ")"
    subredditResult = SubredditResult()

    archive = get_reddit_archive(subreddit)
    
    if archive is not None:
        subredditResult.exists = True
        return subredditResult

    result = download_hot_list(subreddit, None)
    
    if result is None:
        subredditResult.exists = False
        return subredditResult

    if type(result) is str:
        subredditResult.error = result
        return subredditResult

    jsonDict = result

    posts = jsonDict["data"]["children"]

    if len(posts) == 0:
        subredditResult.exists = False
        return subredditResult

    firstPost = posts[0]

    if firstPost["kind"] == "t5":
        subredditResult.exists = False
        subredditResult.suggestion = firstPost["data"]["display_name"]
        return subredditResult
    
    reddit_json_directory = 'reddit-json'
    if not os.path.exists(reddit_json_directory):
        os.makedirs(reddit_json_directory)

    jsonFileName = '{0}/reddit-{1}-hot.json'.format(reddit_json_directory, subreddit)

    save_json_to_file(jsonDict, jsonFileName)

    create_reddit_archive(subreddit, jsonFileName)
    
    subredditResult.exists = True
    return subredditResult

def url_is_image(url):
    rest, fileExtension = os.path.splitext(url)
    return fileExtension in [".jpg", ".jpeg", ".gif", ".png", ".gifv"]
    
def get_unused_url_from_json(bot_id, posts):    
    recentUrls = get_recent_urls(bot_id)

    for post in posts:
        postData = post["data"]
        if "url" in postData:
            url = postData["url"]
            if url_is_image(url):
                if url not in recentUrls:
                    recentUrls.insert(0, url)
                    save_recent_urls(bot_id, recentUrls)
                    return url

    return None

def get_url_from_subreddit(bot_id, subreddit):
    archive = get_reddit_archive(subreddit)

    currentTimeStamp = time.time()
    timeDiff = currentTimeStamp - archive.timeStamp
    
    if timeDiff > 3600:
        result = update_archive(archive)
        if type(result) is str:
            return "Failed to update subreddit. " + result

    jsonDict = load_json_from_file(archive.jsonFile)

    posts = jsonDict["data"]["children"]

    url = get_unused_url_from_json(bot_id, posts)

    if url is None:
        print 'Url is None, downloading new json to get url'

        reddit_json_directory = 'reddit-json'
        if not os.path.exists(reddit_json_directory):
            os.makedirs(reddit_json_directory)

        jsonFileName = '{0}/reddit-{1}-hot.json'.format(reddit_json_directory, subreddit)
        
        lastPostName = None
        if len( posts ) > 0: 
            lastPost = posts[len(posts) - 1]
            lastPostName = lastPost['data']['name']

        result = download_hot_list(subreddit, lastPostName)
        
        if type(result) is str:
            return "Failed to update subreddit, " + result

        jsonDict = result

        if jsonDict is not None:
            save_json_to_file(jsonDict, jsonFileName)
        
            posts = jsonDict["data"]["children"]
            url = get_unused_url_from_json(bot_id, posts)
            print "Got url", url, "from second try"

    return url 

