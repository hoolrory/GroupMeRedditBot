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

import csv
import groupme
import keystore
import os
import reddit
import simplekv
import sys
import time
import traceback

def is_number(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def find_number(words):
    number = 0
    for word in words:
        if is_number(word):
            return int(word)
            
    return number

def find_subreddit(words):
    known_subs_file = "known_subs.csv"
    if os.path.isfile(known_subs_file):
        with open(known_subs_file, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                for word in words:
                    if word.lower() in (sub.lower() for sub in row):
                        return word
    return ''

def find_word_after(words, afterWord):
    i = 0    
    for word in words:
        i += 1
        if word == afterWord:
            return words[i]

def process_rbot_message(bot_id, words):
    subreddit = ''
    count = find_number(words)
    subreddit = find_subreddit(words)
    
    if count == 0:
        if "some" in words:
            print "Found word some"
            wordAfterSome = find_word_after(words, "some")
            if subreddit == '':
                subreddit = wordAfterSome
                count = 2
            elif subreddit == wordAfterSome:
                count = 2
        elif "show" in words:
            print "Found word show"
            wordAfterShow = find_word_after(words, "show")
            if subreddit == '':
                subreddit = wordAfterShow
                count = 1
            elif subreddit == wordAfterShow:
                count = 1
    elif subreddit == '' :
        subreddit = find_word_after(words, str(count))

    if count == 0:
        count = 1
    if count > 3:
        count = 3

    print 'Found number {0}'.format(count)

    if subreddit == '':
        subreddit = find_word_after(words, str(count))

    if subreddit is None or subreddit == '':
        return True

    print 'Found subreddit {0}'.format(subreddit)

    blacklisted_subs_file = "blacklisted_subs.csv"
    if os.path.isfile(blacklisted_subs_file):
        with open(blacklisted_subs_file, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                if subreddit.lower() in (sub.lower() for sub in row):
                    groupme.post_message(bot_id, "We're not gonna go there")
                    return True

    subredditResult = reddit.subreddit_exists( subreddit )

    if subredditResult.error is not None:
        groupme.post_message( bot_id, subredditResult.error )
        return True
    
    if not subredditResult.exists:
        message = "Subreddit /r/{0} does not exist.".format(subreddit)
        if subredditResult.suggestion is not None:
            message += " Did you mean /r/{0}?".format(subredditResult.suggestion)
        groupme.post_message(bot_id, message)
        return True 

    for i in range( 0, count ):
        message = reddit.get_url_from_subreddit(bot_id, subreddit)
        if message is None:
            message = "Failed to get url"

        groupme.post_message(bot_id, message)

    return True

def process_command(auth_token, group_id, bot_id):
    if keystore.contains('timeout_until'):
        timeoutTime = float(keystore.get('timeout_until'))
        now = time.time()    
        if timeoutTime > now:
            timeDiff = timeoutTime - now

            print 'Timeout - Waiting {0} minute(s) longer'.format(int(timeDiff * 0.0166667))
            sys.exit()
        else:
            keystore.delete('timeout_until')

    lastMessageId = ''

    lastMessageIdKey = 'lastMessageId-' + str(bot_id)

    if keystore.contains(lastMessageIdKey):
        lastMessageId = keystore.get(lastMessageIdKey)
        print "LastMessageId was", lastMessageId
    else:
        print "No LastMessageId with key {0}".format(lastMessageIdKey)

    messages = groupme.get_messages(auth_token, group_id, lastMessageId)

    print 'Got {0} new messages'.format(len(messages))

    if len(messages) > 0:
        message = messages[0]
        print message
        print message['id'].encode('utf-8')
        keystore.put(lastMessageIdKey, message['id'].encode('utf-8'))
        print "x"
        for message in messages:
            text = ''
            messageText = message['text']
            if messageText is not None:
                text = messageText.encode('utf-8')
                words = text.split(' ')    
                for word in words:
                    if word.lower() == 'rbot':
                        print 'Found rbot in message', message['id'].encode('utf-8')
                        if not process_rbot_message(bot_id, words):
                            break

try:
    auth_token = str(sys.argv[1])
    group_id = str(sys.argv[2])
    bot_id = str(sys.argv[3])

    process_command(auth_token, group_id, bot_id)
except:
    logs_directory = "logs"
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)
    with open("{0}/{1}_error_log.txt".format(logs_directory, group_id), "a+") as logFile:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logFile.write("Rbot crashed in with group_id: " + group_id + " and bot_id " + bot_id + "\r\n")
        traceback.print_tb(exc_traceback, limit=1, file=logFile)
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=100, file=logFile)
        logFile.write("\r\n\r\n")
