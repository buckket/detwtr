#!/usr/bin/env python


from twython import Twython


APP_KEY = ""
APP_SECRET = ""


twitter = Twython(APP_KEY, APP_SECRET)
auth = twitter.get_authentication_tokens()
OAUTH_TOKEN = auth["oauth_token"]
OAUTH_TOKEN_SECRET = auth["oauth_token_secret"]

print(auth["auth_url"])
oauth_verifier = input('Enter your pin: ')

twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)
final_step = twitter.get_authorized_tokens(oauth_verifier)
print(final_step['oauth_token'])
print(final_step['oauth_token_secret'])
