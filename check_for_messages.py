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
import multiprocessing
import os
import reddit
import simplekv
import sys
import time;
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

def find_word_before(words, beforeWord):
    i = 0
    for word in words:
        if word == beforeWord:
            return words[i-1]
        i += 1

def set_auto_interval(interval, words):
    int(interval)
    if interval != 0:
        if "hour" in words:
            interval = interval * 60 * 60
        elif "hours" in words:
            interval = interval * 60 * 60
        elif "half" in words:
            interval = interval * 30 * 60
        elif "minutes" in words:
            interval = interval * 60
	    elif "minute" in words:
	        interval = interval *60
    elif interval == 0:
        if "hours" in words:
            interval = 120 * 60
        elif "hour" in words:
            interval = 60 * 60
        elif "half" in words:
            interval = 30 * 60
        elif "minutes" in words:
	        interval = find_word_before(words, "minutes")
	        if is_number(interval):
	            int(interval)
                interval = interval * 60
	        else:
                interval = 5 * 60
	    elif "minute" in words:
	        interval = 60

    return interval

def remove_auto_params(bot_id):
    try:
        keystore.delete('auto_sub')
        keystore.delete('auto_interval')
        keystore.delete('last_auto_post')
        keystore.delete('auto_count')
    except:
        return

    lastChange = time.time()
    keystore.put('last_auto_change', lastChange)
    keystore.put('active_auto', 0)
    groupme.post_message(bot_id, "Auto posting stopped")
    return


def check_subreddit(bot_id, subreddit):
    subredditResult = reddit.subreddit_exists( subreddit )

    if subredditResult.error is not None:
        groupme.post_message( bot_id, subredditResult.error )
        return False

    if not subredditResult.exists:
        message = "Subreddit /r/{0} does not exist.".format(subreddit)
        if subredditResult.suggestion is not None:
            message += " Did you mean /r/{0}?".format(subredditResult.suggestion)
        groupme.post_message(bot_id, message)
        return False

    return True

def check_blacklist(bot_id, subreddit):
    blacklisted_subs_file = "blacklisted_subs.csv"
    if os.path.isfile(blacklisted_subs_file):
        with open(blacklisted_subs_file, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                if subreddit.lower() in (sub.lower() for sub in row):
                    groupme.post_message(bot_id, "We're not gonna go there")
                    return True
    return False

def check_active_auto():
    auto = 0
    try:
	    auto = int(keystore.get('active_auto'))
    except:
	    return False
    if auto == 1:
	    return True
    else:
	    return False

def check_auto_words(bot_id, subreddit, words):
    if "cancel" in words:
        remove_auto_params(bot_id)
        return
    elif "stop" in words:
        remove_auto_params(bot_id)
        return

    now = time.time()
    interval = 0
    count = 0
    try:
        lastChange = float(keystore.get('last_auto_change'))
    except:
        lastChange = 0

    if "change" in words:
	    if not check_active_auto():
            groupme.post_message(bot_id, "No active Auto post to change. Sorry.")
	        return
        if lastChange != 0:
	        diff = now - lastChange
    	    if diff < 300:
		        groupme.post_message(bot_id, "Why you wanna change things so much?")
		        return
        if "time" in words:
	        interval = find_number(words)
            interval = set_auto_interval(int(interval), words)
	        if interval != 0:
	            keystore.put('auto_interval', interval)
		        keystore.put('last_auto_change', now)
		        return
	        else:
		        return
        elif "subreddit" in words:
	        subreddit = find_subreddit(words)
            if subreddit == '':
                if "to" in words:
                    subreddit = find_word_after(words, "to")
		            if not check_subreddit(bot_id, subreddit):
			            return
		            if not check_blacklist(bot_id, subreddit):
			            print("changing sub")
			            keystore.put('auto_sub', subreddit)
		    	        keystore.put('last_auto_change', now)
			            return
                else:
                    return
	        else:
		        if not check_blacklist(bot_id, subreddit):
     		        print("changing sub")
		            keystore.put('auto_sub', subreddit)
		            keystore.put('last_auto_change', now)
                    return
                else:
                    return
        elif "number" in words:
	        count = find_number(words)
            if count == 0:
                count = 1
            if count > 3:
                count = 3
	        keystore.put('auto_count', count)
	        keystore.put('last_auto_change', now)
	    return

    elif "every" in words:
	    if check_active_auto():
	        groupme.post_message(bot_id, "Active auto post already exists.")
	        return
        subreddit = find_word_before(words, "every")
        count = find_word_before(words, str(subreddit))
        interval = find_word_after(words, "every")
        if not check_subreddit(bot_id, subreddit):
            return
        if not is_number(count):
            count = 1
	    if is_number(interval):
	        interval = set_auto_interval(int(interval), words)
        else:
	        interval = 0
	        interval = set_auto_interval(int(interval), words)
	    if count == 0:
           count = 1
    	if int(count) > 3:
            count = 3
        if not check_blacklist(bot_id, subreddit):
	        keystore.put('auto_sub', subreddit)
            keystore.put('auto_interval', interval)
            keystore.put('auto_count', count)
	        keystore.put('last_auto_change', now)
            keystore.put('last_auto_post', now)
	        keystore.put('active_auto', 1)

    return

def check_words(bot_id, words):
    count = find_number(words)
    subreddit = find_subreddit(words)

    if "every" in words or "change" in words or "stop" in words or "cancel" in words:
        check_auto_words(bot_id, subreddit, words)
        return

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

    process_rbot_message(bot_id, subreddit, count)

def post_message(bot_id, subreddit):
    message = reddit.get_url_from_subreddit(bot_id, subreddit)
    if message is None:
        message = "Failed to get url"

    groupme.post_message(bot_id, message)

def process_rbot_message(bot_id, subreddit, count):
    if check_blacklist(bot_id, subreddit):
	print("blacklist")
        return True

    if not check_subreddit(bot_id, subreddit):
        return True

    for i in range( 0, count ):
	    post_message(bot_id, subreddit)

    return True

def process_auto_message(bot_id):
    print("auto message")
    subreddit = ''
    last_post = 0
    interval = 0
    count = 0

    try:
        subreddit = str(keystore.get('auto_sub'))
        interval = int(keystore.get('auto_interval'))
        count = int(keystore.get('auto_count'))
        last_post = float(keystore.get('last_auto_post'))
    except:
       print("auto message error")
       return

    now = 0.0
    if last_post != 0:
        now = time.time()
        diff = now - last_post
        if diff < interval:
            print("not enough time passed")
            return

    print(count)
    print(subreddit)
    for i in range(0, count):
        post_message(bot_id, subreddit)

    keystore.put('last_auto_post', now)
    return

def process_message(bot_id, message):
    text = ''
    messageText = message['text']
    if messageText is not None:
        text = messageText.encode('utf-8')
        words = text.split(' ')
        for word in words:
            if word.lower() == 'rbot':
                print 'Found rbot in message', message['id'].encode('utf-8')
                check_words(bot_id, words)

    return

def process_command(auth_token, group_id, bot_id):
    timeout_until()
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
	    jobs = []
        for message in messages:
            p = multiprocessing.Process(target=process_message, args=(bot_id, message))
	        jobs.append(p)
	        p.start()
    return

def timeout_until():
    if keystore.contains('timeout_until'):
        timeoutTime = float(keystore.get('timeout_until'))
        now = time.time()
        if timeoutTime > now:
            timeDiff = timeoutTime - now

            print 'Timeout - Waiting {0} minute(s) longer'.format(int(timeDiff * 0.0166667))
            sys.exit()
        else:
            keystore.delete('timeout_until')

try:
    auth_token = str(sys.argv[1])
    group_id = str(sys.argv[2])
    bot_id = str(sys.argv[3])

    process_command(auth_token, group_id, bot_id)
    process_auto_message(bot_id)
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
