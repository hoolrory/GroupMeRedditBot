#!/user/bin/python

'''
   Copyright (c) 2020 Rory Hool
   
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

import discord
import os
import reddit
import sys

from discord.ext import commands

discordToken = ""
try:
    discordToken = str(sys.argv[1])
except:
   print("Provide token")

client = discord.Client()


async def send_message(channel, message):
   await channel.send(message)

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

async def remove_auto_params(bot_id):
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
    await send_message(bot_id, "Auto posting stopped")
    return


async def check_subreddit(bot_id, subreddit):
    subredditResult = reddit.subreddit_exists( subreddit )

    if subredditResult.error is not None:
        await send_message( bot_id, subredditResult.error )
        return False

    if not subredditResult.exists:
        message = "Subreddit /r/{0} does not exist.".format(subreddit)
        if subredditResult.suggestion is not None:
            message += " Did you mean /r/{0}?".format(subredditResult.suggestion)
        await send_message(bot_id, message)
        return False

    return True

async def check_blacklist(bot_id, subreddit):
    blacklisted_subs_file = "blacklisted_subs.csv"
    if os.path.isfile(blacklisted_subs_file):
        with open(blacklisted_subs_file, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                if subreddit.lower() in (sub.lower() for sub in row):
                    await send_message(bot_id, "We're not gonna go there")
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

async def check_auto_words(bot_id, subreddit, words):
    if "cancel" in words:
        await remove_auto_params(bot_id)
        return
    elif "stop" in words:
        await remove_auto_params(bot_id)
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
            await end_message(bot_id, "No active Auto post to change. Sorry.")
            return
       if lastChange != 0:
          diff = now - lastChange
          if diff < 300:
              await send_message(bot_id, "Why you wanna change things so much?")
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
                  if not await check_subreddit(bot_id, subreddit):
                     return
                  if not await check_blacklist(bot_id, subreddit):
                     print("changing sub")
                     keystore.put('auto_sub', subreddit)
                     keystore.put('last_auto_change', now)
                     return
                else:
                    return
           else:
              if not await check_blacklist(bot_id, subreddit):
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
           await send_message(bot_id, "Active auto post already exists.")
           return
        subreddit = find_word_before(words, "every")
        count = find_word_before(words, str(subreddit))
        interval = find_word_after(words, "every")
        if not await check_subreddit(bot_id, subreddit):
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
        if not await check_blacklist(bot_id, subreddit):
            keystore.put('auto_sub', subreddit)
            keystore.put('auto_interval', interval)
            keystore.put('auto_count', count)
            keystore.put('last_auto_change', now)
            keystore.put('last_auto_post', now)
            keystore.put('active_auto', 1)

    return

async def check_words(bot_id, words):
    count = find_number(words)
    subreddit = find_subreddit(words)

    if "every" in words or "change" in words or "stop" in words or "cancel" in words:
        await check_auto_words(bot_id, subreddit, words)
        return

    if count == 0:
        if "some" in words:
            print("Found word some")
            wordAfterSome = find_word_after(words, "some")
            if subreddit == '':
                subreddit = wordAfterSome
                count = 2
            elif subreddit == wordAfterSome:
                count = 2
        elif "show" in words:
            print("Found word show")
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

    print ('Found number {0}'.format(count))

    if subreddit == '':
        subreddit = find_word_after(words, str(count))
    if subreddit is None or subreddit == '':
        return True

    print('Found subreddit {0}'.format(subreddit))

    await process_rbot_message(bot_id, subreddit, count)

async def post_message(bot_id, subreddit):
    message = reddit.get_url_from_subreddit(bot_id, subreddit)
    if message is None:
        message = "Failed to get url"
    await send_message(bot_id, message)
    #send_message(message)

async def process_rbot_message(bot_id, subreddit, count):
    if await check_blacklist(bot_id, subreddit):
        print("blacklist")
        return True

    if not await check_subreddit(bot_id, subreddit):
        return True

    for i in range( 0, count ):
       await post_message(bot_id, subreddit)

    return True

async def process_message(bot_id, text):
        words = text.split(' ')
        for word in words:
            if word.lower() == 'rbot':
                #print('Found rbot in message', message['id'].encode('utf-8'))
                await check_words(bot_id, words)

        return

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await process_message(message.channel, message.content)
    #if message.content.startswith('RBot'):
    #    await message.channel.send('Hello World')

client.run(discordToken)