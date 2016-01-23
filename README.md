# GroupMeRedditBot
Bot For GroupMe + Reddit Integration (rbot)

This bot retrieves and process messages from GroupMe groups, looking for commands issued to it.

Rbot can be commanded to retrieve 1-3 message posts from any subreddit.

## Setup and running:
Reccommend usage is to schedule a cron job that runs every few minutes
```
python check_for_messages.py groupme_auth_token groupme_group_id groupme_bot_id
```

## Example usage:
```
rbot 3 comics             # show 3 posts from /r/comics
rbot show some comics     # show 2 posts from /r/comics
rbot show comics          # show 1 post  from /r/comics
```


### Known Subreddits
Preffered subreddits can be added to a list, to make it easier for rbot to find them.
Example usage:
```
rbot I want comics        # show 1 post  from /r/comics
```
Example known_subs.csv file:
```
comics,highqualitygifs,python
```


### Blacklist Subreddits
Inappropriate or unwanted subreddits can be blacklisted, and rbot will not post images from them.
Create a blacklisted_subs.csv file, with comma separated subreddits
Example blacklisted_subs.csv file:
```
funny,adviceanimals,pics
```
