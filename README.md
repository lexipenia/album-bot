# album-bot

This bot generates imaginary albums following the rules of a game that was popular online about 2009.

As it turns out, the fake reviews are funnier than the albums.

The bot is on Twitter here: https://twitter.com/bot_album

## Dependencies

`pip install unidecode selenium beautifulsoup4 pillow tweepy`

If you want to run the bot, you'll have to provide the fonts contained in the `fonts_list.py` file (or choose your own fonts and modify the list).

Twitter API keys need to be supplied in a file called `api_keys.py` with this format:

```
consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""
```