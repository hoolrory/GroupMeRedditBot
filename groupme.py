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

import keystore
import os
import requests
import simplejson
import sys
import time
import urllib

def make_bot(auth_token, group_id, bot_name):
    url = 'https://api.groupme.com/v3/bots?token={0}'.format(auth_token)
    data = {'bot':{'name':bot_name, 'group_id':group_id}}
    headers = {'Content-type':'application/json'}

    r = requests.post(url, data=simplejson.dumps(data), headers=headers)

    print r.status_code
    print r.json()

def print_groups(auth_token):
    r = requests.get('https://api.groupme.com/v3/groups?token={0}'.format(auth_token))
    print r.status_code
    print r.json()

def post_message(bot_id, message):
    url = 'https://api.groupme.com/v3/bots/post'
    query_string = urllib.urlencode({'bot_id':bot_id, 'text':message})
    wholeRequest = url + "?" + query_string 

    print wholeRequest

    r = requests.post(wholeRequest)

    logs_directory = "logs"
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)
    logFile = open("{0}/bot_{1}.txt".format(logs_directory, bot_id), "a+")
    
    logFile.write("\n\n" )
    logFile.write("------------------------------\n")
    logFile.write("----------PostMessage---------\n")
    logFile.write("------------------------------\n")
    logFile.write(" bot_id      = {0}\n".format(bot_id))
    logFile.write(" message     = {0}\n".format(message))
    logFile.write(" status_code = {0}\n".format(r.status_code))
    logFile.write(" response    = {0}\n".format(r.text))
    logFile.write("------------------------------\n") 
    logFile.close()
    
    if r.status_code == 420:
        print 'Got groupme status code 420, waiting 15 minutes'
        keystore.put('timeout_until', time.time() + 900)

def get_messages(auth_token, group_id, last_message_id):
    
    url = 'https://api.groupme.com/v3/groups/{0}/messages?token={1}&limit=100'.format(group_id, auth_token)
    if last_message_id != "":
        url += "&since_id={0}".format(last_message_id)
    r = requests.get(url)

    if r.status_code == 420:
        print 'Got groupme status code 420, waiting 15 minutes'
        keystore.put('timeout_until', time.time() + 900)

    if r.status_code != 200:
        return {}
    
    jsonDict = r.json()
    messages = jsonDict["response"]["messages"]
    return messages    
 