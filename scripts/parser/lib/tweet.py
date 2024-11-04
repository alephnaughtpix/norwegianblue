from lib.utils import UriLoader
from lib.user_profile import UserProfile
import os

class Tweet:
    def __init__(self, 
                 id,
                 date = None,
                 full_text = None,
                 source = None,
                 retweet_count = None,
                 favourite_count = None,
                 in_reply_to_status_id = None,
                 in_reply_to_user_id = None,
                 in_reply_to_screen_name = None,
                 user_mentions = None,
                 hashtags = None,
                 media = None,
                 symbols = None,
                 urls = None,
                 lang = None,
                 pinned = False,
                 in_thread = False,
                 thread_id = None,
                 is_retweet = False,
                 no_of_favorites = None,
                 no_of_retweets = None
            ):
        self.id = id
        self.date = date
        self.full_text = full_text
        self.source = source
        self.retweet_count = retweet_count
        self.favorite_count = favourite_count
        self.in_reply_to_status_id = in_reply_to_status_id
        self.in_reply_to_user_id = in_reply_to_user_id
        self.in_reply_to_screen_name = in_reply_to_screen_name
        self.user_mentions = user_mentions
        self.hashtags = hashtags
        self.media = media
        self.symbols = symbols
        self.urls = urls
        self.lang = lang
        self.pinned = pinned
        self.in_thread = in_thread
        self.thread_id = thread_id
        self.is_retweet = is_retweet
        
        
    @staticmethod
    def import_tweet_json(tweet_json):
        #print(tweet_json)
        new_tweet = Tweet(
            tweet_json['id'],
            date = tweet_json['created_at'],
            full_text = tweet_json['full_text'],
            source = tweet_json['source'],
            retweet_count = tweet_json['retweet_count'],
            favourite_count = tweet_json['favorite_count'],
            lang = tweet_json['lang']
        )
        
        if 'in_reply_to_status_id' in tweet_json:
            new_tweet.in_reply_to_status_id = tweet_json['in_reply_to_status_id']
        if 'in_reply_to_user_id' in tweet_json:
            new_tweet.in_reply_to_user_id = tweet_json['in_reply_to_user_id']
        if 'in_reply_to_screen_name' in tweet_json:
            new_tweet.in_reply_to_screen_name = tweet_json['in_reply_to_screen_name']
        
        media_jsons = []
        symbols = []
        urls = []
        user_mentions = []
        
        entities = tweet_json['entities']
        if 'extended_entities' in tweet_json:
            extended_entities = tweet_json['extended_entities']
        else:
            extended_entities = None
        if 'hashtags' in entities:
            hashtags = entities['hashtags']
        if 'media' in entities:
            media_jsons = entities['media']
        if 'symbols' in entities:
            symbols = entities['symbols']
        if 'urls' in entities:
            urls = entities['urls']
        if 'user_mentions' in entities:
            user_mentions = entities['user_mentions']
        
        if extended_entities:
            if 'media' in tweet_json['extended_entities']:
                media_jsons = extended_entities['media']
        
        media = []
        for media_json in media_jsons:
            media.append(Media.import_media_json(media_json, new_tweet.id))
        new_tweet.media = media
        
        hashtags_list = []
        for hashtag in hashtags:
            hashtags_list.append(hashtag['text'])
        new_tweet.hashtags = hashtags_list

        new_tweet.symbols = [symbol['text'] for symbol in symbols]
        new_tweet.urls = [url['expanded_url'] for url in urls]
        new_tweet.user_mentions = [mention['screen_name'] for mention in user_mentions]
        
        return new_tweet
    
class Media:
    def __init__(self, 
                    id,
                    url = None,
                    tco_url = None,
                    local_filename = None,
                    file_size = None,
                    expanded_url = None,
                    type = None,
                    video_info = None,
                    sizes = None,
                    tweet_id = None,
                    source_tweet_id = None,
                    source_user_id = None,
                    additional_media_info = None,
                    description = None,
                    alt_text = None,
                    duration_millis = None,
        ):
        self.id = id
        self.url = url
        self.tco_url = tco_url
        self.local_filename = local_filename
        self.file_size = file_size
        self.expanded_url = expanded_url
        self.type = type
        self.video_info = video_info
        self.sizes = sizes
        self.source_tweet_id = source_tweet_id
        self.tweet_id = tweet_id
        self.source_tweet_id = source_tweet_id
        self.source_user_id = source_user_id
        self.additional_media_info = additional_media_info
        self.description = description
        self.alt_text = alt_text
        self.duration_millis = duration_millis

    @staticmethod
    def __get_best_video_url(video_info):
        variants = video_info['variants']
        best_variant = None
        best_variant_bitrate = -1
        for variant in variants:
            if 'bitrate' in variant:
                current_bitrate = int(variant['bitrate'])
                if not best_variant:
                    best_variant = variant
                    best_variant_bitrate = int(best_variant['bitrate'])
                elif current_bitrate > best_variant_bitrate:
                    best_variant = variant
                    best_variant_bitrate = current_bitrate
        return best_variant['url'].split('?')[0]                # Strip off any query parameters
    
    @staticmethod
    def import_media_json(media_json, tweet_id = None):
        media_object = Media(
            media_json['id'],
            url = media_json['media_url_https'],
            tco_url = media_json['url'],
            local_filename = None,
            expanded_url = media_json['expanded_url'],
            type = media_json['type'],
            sizes = media_json['sizes']
        )
        if 'source_status_id' in media_json:
            media_object.source_tweet_id = media_json['source_status_id']
        if 'source_user_id' in media_json:
            media_object.source_user_id = media_json['source_user_id']
        if 'video_info' in media_json:
            media_object.video_info = media_json['video_info']
        if 'additional_media_info' in media_json:
            media_object.additional_media_info = media_json['additional_media_info']
        if 'description' in media_json:
            media_object.description = media_json['description']
        if 'alt_text' in media_json:
            media_object.alt_text = media_json['alt_text']  
        if tweet_id:
            media_object.tweet_id = tweet_id
        else:
            media_object.tweet_id = media_json['source_status_id']
            
        if media_object.type == 'video' and media_object.video_info:
            media_object.duration_millis = media_object.video_info['duration_millis']
            media_object.url = Media.__get_best_video_url(media_object.video_info)
        if media_object.type == 'animated_gif':
            media_object.url = media_object.video_info['variants'][0]['url']
        return media_object
    
    def make_local_filename(self, source_directory):
        original_expanded_url = self.url
        original_filename = os.path.split(original_expanded_url)[1]
        archive_media_filename = self.tweet_id + '-' + original_filename
        archive_media_path = os.path.join(source_directory, archive_media_filename)
        if os.path.exists(archive_media_path):
            self.local_filename = archive_media_path
            self.file_size = os.path.getsize(archive_media_path)
            return archive_media_path
        else:
            return None
        
    def make_output_filename(self, output_media_folder_name):
        if self.local_filename:
            original_filename = os.path.split(self.local_filename)[1]
        else:
            original_filename = os.path.split(self.url)[1]
        if not os.path.exists(output_media_folder_name):
            os.makedirs(output_media_folder_name)
        output_filename = os.path.join(output_media_folder_name, original_filename)
        return output_filename
