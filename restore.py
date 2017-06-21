#!/usr/bin/env python3

import datetime
import io
import math
import logging

import editdistance
from twython import Twython
from twython import TwythonError

import settings
from database import db, Tweet, Job


def init_detwtr_bot():
    return Twython(settings.BOT_APP_KEY,
                   settings.BOT_APP_SECRET,
                   settings.BOT_OAUTH_TOKEN,
                   settings.BOT_OAUTH_TOKEN_SECRET)


def main():
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
    db.connect()
    bot = init_detwtr_bot()
    for job in Job.select():
        logging.info("Processing job: {id}".format(id=job.id))

        if (datetime.datetime.now() - job.tweet.created_at) < datetime.timedelta(minutes=5):
            logging.info("Tweet is not old enough, wait a few more minutes")
            continue

        is_duplicate = False
        for tweet in Tweet.select().where((Tweet.user == job.tweet.user) & (
                    Tweet.created_at > job.tweet.created_at) & ~(Tweet.is_deleted) & ~(Tweet.is_withheld)):
            levdist = editdistance.eval(tweet.text, job.tweet.text)
            if levdist <= max(2, int(math.ceil(5 / 140 * len(job.tweet.text)))) and job.tweet.media == tweet.media:
                is_duplicate = True
                logging.info("Duplicate found:\n{tweet_1}\n---\n{tweet_2}".format(tweet_1=job.tweet.text,
                                                                                  tweet_2=tweet.text))
                break

        if is_duplicate:
            logging.info("Tweet is very similar to other tweets, won't restore")
            job.delete_instance()
        else:
            logging.info("Found no similar tweets, going to restore! :3")
            text = job.tweet.text.replace("@", "&")
            try:
                if job.tweet.media:
                    media = io.BytesIO(job.tweet.media)
                    resp = bot.upload_media(media=media)
                    bot.update_status(status=text, media_ids=[resp["media_id"]])
                else:
                    bot.update_status(status=text)
                logging.info("Tweet restored, all is well...")
                job.delete_instance()
            except TwythonError as e:
                logging.error("TwythonError: {error}".format(error=repr(e)))
    db.close()


if __name__ == '__main__':
    main()
