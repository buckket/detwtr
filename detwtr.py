#!/usr/bin/env python


from twython import Twython
from twython import TwythonStreamer
from twython import TwythonError

from StringIO import StringIO

import requests
import HTMLParser

import settings
import database
from database import Tweet


def init_detwtr_stream():
    return detwtrStreamer(settings.STREAM_APP_KEY,
        settings.STREAM_APP_SECRET,
        settings.STREAM_OAUTH_TOKEN,
        settings.STREAM_OAUTH_TOKEN_SECRET)

def init_detwtr_bot():
    return Twython(settings.BOT_APP_KEY,
        settings.BOT_APP_SECRET,
        settings.BOT_OAUTH_TOKEN,
        settings.BOT_OAUTH_TOKEN_SECRET)


class detwtrStreamer(TwythonStreamer):

    def on_success(self, data):
        if 'text' in data:
            text = data['text']
            tweet_id = data['id_str']
            user_id = data['user']['id_str']
            media = None

            # checking if tweet has a picture attached
            if 'media' in data['entities']:
                media_url = data['entities']['media'][0]['media_url']
                url_in_tweet = data['entities']['media'][0]['url']
                text = text.replace(url_in_tweet, '')
                r = requests.get(media_url)
                media = r.content

            # unescape HTML entities
            text = HTMLParser.HTMLParser().unescape(text)

            # storing tweet in database
            tweet_db = Tweet(tweet_id=tweet_id, user_id=user_id, text=text, media=media)
            database.session.add(tweet_db)
            database.session.commit()
            print "Added new tweet to db"

        if 'delete' in data:
            print "Got a delete message, checking if I have the corresponding tweet...",
            instance = database.session.query(Tweet).filter_by(tweet_id=data['delete']['status']['id_str']).first()
            if instance:
                instance.gone = True

                # replace @ with & to avoid mentioning someone
                text = instance.text.replace('@', '&')

                # gonna tweet, bro
                try:
                    if instance.media:
                        media = StringIO(instance.media)
                        bot.update_status_with_media(status=text, media=media)
                    else:
                        bot.update_status(status=text)
                    print "Success!"

                except TwythonError, e:
                    print "TwythonError: %s" % repr(e)

                finally:
                    database.session.commit()
            else:
                print "Nope!"

    def on_error(self, status_code, data):
        print status_code


database.init_db()

stream = init_detwtr_stream()
bot = init_detwtr_bot()

stream.user()
