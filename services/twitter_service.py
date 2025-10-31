from config import settings
from tweepy import Client

class TwitterService:
    def __init__(self):
        self.api_key = settings.TWITTER_API_KEY
        self.api_secret = settings.TWITTER_API_SECRET
        self.access_token = settings.TWITTER_ACCESS_TOKEN
        self.access_token_secret = settings.TWITTER_ACCESS_TOKEN_SECRET

    def post_tweet(self, tweet_text: str):
        """
        Authenticates and posts a tweet using the X API (Tweepy v2).
        REQUIRES: Consumer Key, Consumer Secret, Access Token, and Access Token Secret.
        These must be stored securely as environment variables.
        """ 
        if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            print("X API credentials missing. Skipping tweet post.")
            print("Please set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET environment variables.")
            return
        try:
            # Authenticate using OAuth 1.0a (required for posting tweets)
            client = Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret
            )
            # Post the tweet
            response = client.create_tweet(text=tweet_text)
            print(f"X POST SUCCESS: Tweeted: {tweet_text}")
            print(f"X Response ID: {response.data['id']}")
        except Exception as e:
            print(f"X POST ERROR: Failed to post tweet. {e}")