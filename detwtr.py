#!/usr/bin/env python3

import html
import logging

import requests
from peewee import DoesNotExist, IntegrityError
from twython import TwythonStreamer

import settings
from database import db, Tweet, User, Event, Job


def init_detwtr_stream():
    return detwtrStreamer(settings.STREAM_APP_KEY,
                          settings.STREAM_APP_SECRET,
                          settings.STREAM_OAUTH_TOKEN,
                          settings.STREAM_OAUTH_TOKEN_SECRET)


class detwtrStreamer(TwythonStreamer):
    def on_success(self, data):
        if "text" in data:
            payload = {}

            # skip if tweet is from bot itself
            if data["user"]["id_str"] == settings.BOT_ID:
                return

            # skip tweet if it's just a RT
            if "retweeted_status" in data:
                return

            payload["text"] = data["text"]
            payload["tweet_id"] = data["id_str"]
            payload["user"] = User.get_or_create(user_id=data["user"]["id_str"])[0]

            if "media" in data["entities"]:
                media_url = data["entities"]["media"][0]["media_url"]
                url_in_tweet = data["entities"]["media"][0]["url"]
                payload["text"] = payload["text"].replace(url_in_tweet, "")
                r = requests.get(media_url)
                payload["media"] = r.content

            # unescape HTML entities
            payload["text"] = html.unescape(payload["text"])

            # storing tweet in database
            logging.info("Adding new tweet to DB: {id} from {user}".format(id=payload["tweet_id"],
                                                                           user=payload["user"].user_id))
            tweet_db = Tweet(**payload)
            try:
                tweet_db.save()
            except IntegrityError:
                logging.error("Tweet already present in DB")

        if "delete" in data:
            logging.info("Received delete message, checking if corresponding tweet is stored: {id}".format(
                id=data["delete"]["status"]["id_str"]))

            instance = None
            try:
                instance = Tweet.get(Tweet.tweet_id == data["delete"]["status"]["id_str"])
                logging.info("Tweet found! :)")
            except DoesNotExist:
                logging.info("Tweet not found! :(")

            event_db = Event(event="delete",
                             user=User.get_or_create(user_id=data["delete"]["status"]["user_id_str"])[0],
                             tweet=instance)
            event_db.save()

            if instance:
                # mark this tweet as deleted
                instance.is_deleted = True
                instance.save()

                # add tweet to job queue
                jobs_db = Job(tweet=instance)
                try:
                    jobs_db.save()
                except IntegrityError:
                    logging.error("Tweet is already marked for restoration")

        if "status_withheld" in data:
            logging.info("Received withheld content notice, checking if corresponding tweet is stored: {id}".format(
                id=str(data["status_withheld"]["id"])))

            instance = None
            try:
                instance = Tweet.get(Tweet.tweet_id == str(data["status_withheld"]["id"]))
                logging.info("Tweet found! :)")
            except DoesNotExist:
                logging.info("Tweet not found! :(")

            event_db = Event(event="withheld",
                             user=User.get_or_create(user_id=str(data["status_withheld"]["user_id"]))[0],
                             tweet=instance)
            event_db.save()

            if instance:
                # mark this tweet as deleted
                instance.is_withheld = True
                instance.save()

                # add tweet to job queue
                jobs_db = Job(tweet=instance)
                try:
                    jobs_db.save()
                except IntegrityError:
                    logging.error("Tweet is already marked for restoration")

    def on_error(self, status_code, data):
        logging.error("Error while processing stream: {}".format(status_code))


if __name__ == '__main__':
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
    db.connect()
    db.create_tables([Tweet, User, Event, Job, ], safe=True)
    stream = init_detwtr_stream()
    stream.user()
    db.close()
