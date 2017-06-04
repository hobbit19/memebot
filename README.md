# Meme Bot

This is a Python bot that looks up images from a specified subreddit and automatically posts them on Twitter. This was created for the [@ItMeIRL](https://twitter.com/ItMeIRL) and [@ItsMeowIRL](https://twitter.com/ItsMeowIRL) Twitter accounts, based on [reddit-twitter-bot](https://github.com/rhiever/reddit-twitter-bot).

## Disclaimer

I hold no liability for what you do with this script or what happens to you by using this script. Abusing this script *can* get you banned from Twitter, so make sure to read up on proper usage of the Twitter API.

## Dependencies

First, you will need to install Python 3 on your system. After that, you will also need to install the [tweepy](https://github.com/tweepy/tweepy), [PRAW](https://praw.readthedocs.org/en/), and [py-gfycat](https://github.com/ankeshanand/py-gfycat) libraries. You can do so by running these commands:

    pip install tweepy
    pip install praw
    pip install gfycat

## Setting up the bot

All settings for the bot can be found in the `config.ini` file. Open the file in any text editor and add the following info:

1. Under the [BotSettings] section, add the username of the Twitter account you will use to `TwitterUsername` (do not include the @ symbol)
2. Under the [BotSettings] section, add the name of the subreddit to `SubredditToMonitor` (do not include the /r/)
3. By default, the bot will wait at least 600 seconds between tweets to prevent spamming, you can change this by editing the `DelayBetweenTweets` setting in the [BotSettings] section

Next, you'll need to give Meme Bot access to a Twitter account, and add the required information to the config file.

1. [Sign in](https://dev.twitter.com/apps) with the Twitter account you want to use with the bot
2. Click the 'Create New App' button
3. Fill out the Name, Description, and Website fields with anything you want (you can leave the callback field blank)
4. Make sure that 'Access level' says 'Read and write'
5. Click the 'Keys and Access Tokens' tab
6. Click the 'Create my access token' button
7. Fill out the [PrimaryTwitterKeys] section in the config file with the info

You can also optionally use another Twitter account to reply to every tweet with the original source on Reddit ([example](https://twitter.com/IRL_Context/status/846069261474938880)). The bot will work fine if you skip this step.

1. [Sign in](https://dev.twitter.com/apps) with the Twitter account you want to use with the bot
2. Click the 'Create New App' button
3. Fill out the Name, Description, and Website fields with anything you want (you can leave the callback field blank)
4. Make sure that 'Access level' says 'Read and write'
5. Click the 'Keys and Access Tokens' tab
6. Click the 'Create my access token' button
7. Fill out the [AltTwitterKeys] section in the config file with the info

In addition, you will have to create an application on Reddit:

1. Sign in with your Reddit account
2. Go to your [app preferences](https://www.reddit.com/prefs/apps) and create a new application at the bottom
3. Select the application type as 'script'
4. Add the token (seen below the name of the bot after it's generated) and the secret to the [Reddit] section of the config file

## Usage

Once you edit the bot script to provide the necessary API keys and the subreddit you want to tweet from, you can run the bot on the command line:

    python memebot.py
