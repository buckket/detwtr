import datetime

from peewee import SqliteDatabase, Model
from peewee import CharField, TextField, BlobField, BooleanField, DateTimeField, ForeignKeyField

import settings

db = SqliteDatabase(settings.DB_URI)


class User(Model):
    user_id = CharField(max_length=32)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db


class Tweet(Model):
    tweet_id = CharField(max_length=32, unique=True)
    user = ForeignKeyField(User, related_name="tweets")
    text = TextField()
    media = BlobField(null=True)
    is_deleted = BooleanField(default=False)
    is_withheld = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db


class Event(Model):
    event = CharField(max_length=32)
    user = ForeignKeyField(User, related_name="events")
    tweet = ForeignKeyField(Tweet, related_name="event", null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db


class Job(Model):
    tweet = ForeignKeyField(Tweet, unique=True, related_name="jobs")
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
