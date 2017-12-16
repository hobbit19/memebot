import praw
import json
import requests
import tweepy
import time
import os
import csv
import re
import configparser
import urllib.parse
import sys
from glob import glob
from gfycat.client import GfycatClient
import distutils.core
import itertools
import photohash

# Location of the configuration file
CONFIG_FILE = 'config.ini'

def strip_title(title):
	# Shortlink is 22 characters long, plus one character for a space
	if len(title) < 280:
		return title
	else:
		return title[:276] + '...'

def save_file(img_url, file_path):
	resp = requests.get(img_url, stream=True)
	if resp.status_code == 200:
		with open(file_path, 'wb') as image_file:
			for chunk in resp:
				image_file.write(chunk)
		# Return the path of the image, which is always the same since we just overwrite images
		return file_path
	else:
		print('[EROR] File failed to download. Status code: ' + resp.status_code)
		return ''

def get_media(img_url, post_id):
	if any(s in img_url for s in ('i.imgur.com', 'i.redd.it', 'i.reddituploads.com')):
		# This adds support for all imgur links (including galleries), but I need to make a new regex
		#if ('i.imgur.com' not in img_url) and ('imgur.com' in img_url):
			#print('[bot] Attempting to retrieve image URL for', img_url, 'from imgur...')
			#regex = r"(https?:\/\/imgur\.com\/a\/(.*?)(?:\/.*|$))"
			#m = re.search(regex, img_url, flags=0)
			#print(m.group(0))
			#img_url = imgur.get_image(img_url)
		file_name = os.path.basename(urllib.parse.urlsplit(img_url).path)
		file_extension = os.path.splitext(img_url)[-1].lower()
		# Fix for issue with i.reddituploads.com links not having a file extension in the URL
		if not file_extension:
			file_extension += '.jpg'
			file_name += '.jpg'
			img_url += '.jpg'
		# Grab the GIF versions of .GIFV links
		# When Tweepy adds support for video uploads, we can use grab the MP4 versions
		if (file_extension == '.gifv'):
			file_extension = file_extension.replace('.gifv', '.gif')
			file_name = file_name.replace('.gifv', '.gif')
			img_url = img_url.replace('.gifv', '.gif')
		# Download the file
		file_path = IMAGE_DIR + '/' + file_name
		print('[ OK ] Downloading file at URL ' + img_url + ' to ' + file_path + ', file type identified as ' + file_extension)
		img = save_file(img_url, file_path)
		return img
	elif ('gfycat.com' in img_url): # Gfycat
		gfycat_name = os.path.basename(urllib.parse.urlsplit(img_url).path)
		client = GfycatClient()
		gfycat_info = client.query_gfy(gfycat_name)
		# Download the 2MB version because Tweepy has a 3MB upload limit for GIFs
		gfycat_url = gfycat_info['gfyItem']['max2mbGif']
		file_path = IMAGE_DIR + '/' + gfycat_name + '.gif'
		print('[ OK ] Downloading Gfycat at URL ' + gfycat_url + ' to ' + file_path)
		gfycat_file = save_file(gfycat_url, file_path)
		return gfycat_file
	elif ('giphy.com' in img_url): # Giphy
		# Working demo of regex: https://regex101.com/r/eC9gL6/10
		regex = r"https?://(media\.giphy\.com/media/|giphy.com/gifs/|i.giphy.com/)(.*-)?([^ /\n]+)"
		m = re.search(regex, img_url, flags=0)
		# Get the Giphy ID
		id = m.group(3)
		# Download the 2MB version because Tweepy has a 3MB upload limit for GIFs
		giphy_url = 'https://media.giphy.com/media/' + id + '/giphy-downsized.gif'
		file_path = IMAGE_DIR + '/' + id + '-downsized.gif'
		print('[ OK ] Downloading Giphy at URL ' + giphy_url + ' to ' + file_path)
		giphy_file = save_file(giphy_url, file_path)
		return giphy_file
	else:
		print('[WARN] Post', post_id, 'doesn\'t point to an image/GIF:', img_url)
		return ''

def tweet_creator(subreddit_info):
	post_dict = {}
	print ('[ OK ] Getting posts from Reddit')
	for submission in subreddit_info.hot(limit=20):
		# If the OP has deleted his account, save it as "a deleted user"
		if submission.author is None:
			submission.author = "a deleted user"
			submission.author.name = "a deleted user"
		else:
			submission.author.name = "/u/" + submission.author.name
		post_dict[strip_title(submission.title)] = [submission.id,submission.url,submission.shortlink,submission.author.name]
	return post_dict

def setup_connection_reddit(subreddit):
	print ('[ OK ] Setting up connection with Reddit...')
	r = praw.Reddit(
		user_agent='bot irl',
		client_id=REDDIT_AGENT,
		client_secret=REDDIT_CLIENT_SECRET)
	return r.subreddit(subreddit)

def duplicate_check(id):
	value = False
	with open(CACHE_CSV, 'rt', newline='') as f:
		reader = csv.reader(f, delimiter=',')
		for row in reader:
			if id in row:
				value = True
	return value
	
def hash_check(hash):
	if hash:
		value = False
		# Only extract last three lines from cache file
		post_list = []
		with open(CACHE_CSV, 'rt', newline='') as f:
			for line in f:
				post_list.append(line)
				if len(post_list) > REPOST_LIMIT:
					post_list.pop(0)
			if any(hash in s for s in post_list):
				value = True
	else:
		value = True
	return value

def log_post(id, hash, tweetID):
	with open(CACHE_CSV, 'a', newline='') as cache:
			date = time.strftime("%d/%m/%Y") + ' ' + time.strftime("%H:%M:%S")
			wr = csv.writer(cache, delimiter=',')
			wr.writerow([id, date, hash, tweetID])

def main():
	# Make sure logging file and media directory exists
	if not os.path.exists(CACHE_CSV):
		with open(CACHE_CSV, 'w', newline='') as cache:
			default = ['Post','Date and time','Image hash', 'Tweet link']
			wr = csv.writer(cache)
			wr.writerow(default)
		print ('[ OK ] ' + CACHE_CSV + ' file not found, created a new one')
	if not os.path.exists(IMAGE_DIR):
		os.makedirs(IMAGE_DIR)
		print ('[ OK ] ' + IMAGE_DIR + ' folder not found, created a new one')
	# Continue with script
	subreddit = setup_connection_reddit(SUBREDDIT_TO_MONITOR)
	post_dict = tweet_creator(subreddit)
	tweeter(post_dict)

def alt_tweeter(post_link, op, username, newestTweet):
	try:
		# Log into alternate account
		auth = tweepy.OAuthHandler(ALT_CONSUMER_KEY, ALT_CONSUMER_SECRET)
		auth.set_access_token(ALT_ACCESS_TOKEN, ALT_ACCESS_TOKEN_SECRET)
		api = tweepy.API(auth)

		# Post the tweet
		tweetText = '@' + username + ' Originally posted by ' + op + ' on Reddit: ' + post_link
		print('[ OK ] Posting this on alt Twitter account:', tweetText)
		api.update_status(tweetText, newestTweet)
	except BaseException as e:
		print ('[EROR] Error while posting tweet on alt account:', str(e))	
		return

def tweeter(post_dict):
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_secret)
	api = tweepy.API(auth)
	for post in post_dict:
		# Grab post details from dictionary
		post_id = post_dict[post][0]
		if not duplicate_check(post_id): # Make sure post is not a duplicate
			file_path = get_media(post_dict[post][1], post_dict[post][0])
			post_link = post_dict[post][2]
			post_op = post_dict[post][3]
			# Make sure the post contains media (if it doesn't, then file_path would be blank)
			if (file_path):
				# Scan the image against previously-posted images
				try:
					hash = photohash.average_hash(file_path)
					print ('[ OK ] Image hash check:', hash_check(hash))
				except:
					# Set hash to an empty string if the check failed
					hash = ""
					print ('[WARN] Could not check image hash, skipping.')
				# Only make a tweet if the post has not already been posted (if repost protection is enabled)
				if ((REPOST_PROTECTION is True) and (hash_check(hash) is False)):
					print ('[ OK ] Posting this on main twitter account:', post, file_path)
					try:
						# Post the tweet
						api.update_with_media(filename=file_path, status=post)
						# Log the tweet
						username = api.me().screen_name
						latestTweets = api.user_timeline(screen_name = username, count = 1, include_rts = False)
						newestTweet = latestTweets[0].id_str
						log_post(post_id, hash, 'https://twitter.com/' + username + '/status/' + newestTweet + '/')
						# Post alt tweet
						if ALT_ACCESS_TOKEN:
							alt_tweeter(post_link, post_op, username, newestTweet)
						else:
							print('[WARN] No authentication info for alternate account in config.ini, skipping alt tweet.')
						print('[ OK ] Sleeping for', DELAY_BETWEEN_TWEETS, 'seconds')
						time.sleep(DELAY_BETWEEN_TWEETS)
					except BaseException as e:
						print ('[EROR] Error while posting tweet:', str(e))
						# Log the post anyways
						log_post(post_id, hash, "Error while posting tweet:" + str(e))
				else:
					print ('[WARN] Skipping', post_id, 'because it seems to be a repost')
				# Cleanup media file
				try:
					os.remove(file_path)
					print ('[ OK ] Deleted media file at ' + file_path)
				except BaseException as e:
					print ('[EROR] Error while deleting media file:', str(e))
			else:
				print ('[WARN] Ignoring', post_id, 'because there was not a media file downloaded')
		else:
			print ('[WARN] Ignoring', post_id, 'because it was already posted')

if __name__ == '__main__':
	# Make sure config file exists
	try:
		config = configparser.ConfigParser()
		config.read(CONFIG_FILE)
	except BaseException as e:
		print ('[EROR] Error while reading config file:', str(e))
		sys.exit()
	# Create variables from config file
	CACHE_CSV = config['BotSettings']['CacheFile']
	IMAGE_DIR = config['BotSettings']['MediaFolder']
	DELAY_BETWEEN_TWEETS = int(config['BotSettings']['DelayBetweenTweets'])
	SUBREDDIT_TO_MONITOR = config['BotSettings']['SubredditToMonitor']
	REPOST_PROTECTION = bool(distutils.util.strtobool(config['RepostSettings']['RepostProtection']))
	REPOST_LIMIT = int(config['RepostSettings']['RepostLimit'])
	ACCESS_TOKEN = config['PrimaryTwitterKeys']['AccessToken']
	ACCESS_TOKEN_secret = config['PrimaryTwitterKeys']['AccessTokenSecret']
	CONSUMER_KEY = config['PrimaryTwitterKeys']['ConsumerKey']
	CONSUMER_SECRET = config['PrimaryTwitterKeys']['ConsumerSecret']
	ALT_ACCESS_TOKEN = config['AltTwitterKeys']['AccessToken']
	ALT_ACCESS_TOKEN_SECRET = config['AltTwitterKeys']['AccessTokenSecret']
	ALT_CONSUMER_KEY = config['AltTwitterKeys']['ConsumerKey']
	ALT_CONSUMER_SECRET = config['AltTwitterKeys']['ConsumerSecret']
	REDDIT_AGENT = config['Reddit']['Agent']
	REDDIT_CLIENT_SECRET = config['Reddit']['ClientSecret']
	# Run the main script
	while True:
		main()
		print('[ OK ] Sleeping for', DELAY_BETWEEN_TWEETS, 'seconds')
		time.sleep(DELAY_BETWEEN_TWEETS)
		print('[ OK ] Restarting main()...')