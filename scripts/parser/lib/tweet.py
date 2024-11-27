from lib.utils import *
from lib.user_profile import UserProfile
from dateutil import parser
import json
import os
import re

class Tweet:
    def __init__(self, 
                 id,
                 date = None,
                 date_day = None,
                 date_month = None,
                 date_year = None,
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
                 embed_urls = None,
                 lang = None,
                 pinned = False,
                 in_thread = False,
                 thread_id = None,
                 is_retweet = False,
                 is_quote_tweet = False,
                 no_of_favorites = None,
                 no_of_retweets = None,
                 filename = None
            ):
        self.id = id
        self.date = date
        self.date_day = date_day
        self.date_month = date_month
        self.date_year = date_year
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
        self.embed_urls = embed_urls
        self.lang = lang
        self.pinned = pinned
        self.in_thread = in_thread
        self.thread_id = thread_id
        self.is_retweet = is_retweet
        self.is_quote_tweet = is_quote_tweet
        self.no_of_favorites = no_of_favorites
        self.no_of_retweets = no_of_retweets
        self.filename = filename
        
        
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
        user_mentions = None
        
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
        new_tweet.urls = []
        new_tweet.embed_urls = []
        for media_json in media_jsons:
            media.append(Media.import_media_json(media_json, new_tweet.id))
            new_tweet.urls.append({
                'url': media_json['url'],
                'expanded_url': media_json['expanded_url'],
                'display_url': media_json['display_url']
            })
        new_tweet.media = media
        
        hashtags_list = []
        for hashtag in hashtags:
            hashtags_list.append(hashtag['text'])
        new_tweet.hashtags = hashtags_list

        new_tweet.symbols = [symbol['text'] for symbol in symbols]
        for url in urls:
            expanded_url = url['expanded_url']
            status_search = re.search(r'http.*\:\/\/twitter.com\/\w+\/status\/(\d+)', expanded_url)
            if status_search:
                new_tweet.embed_urls.append( { 'type': 'twitter', 'embed_id': status_search.group(1) } )
            new_tweet.urls.append({
                'url': url['url'],
                'expanded_url': url['expanded_url'],
                'display_url': url['display_url']
            })
        
        if user_mentions:
            new_tweet.user_mentions =  user_mentions
        
        if new_tweet.date:
            new_datetime = Utils.import_date(new_tweet.date)
            new_tweet.date = new_datetime
            new_date = new_datetime.date()
            new_tweet.date_day = new_date.day
            new_tweet.date_month = new_date.month
            new_tweet.date_year = new_date.year    
        
        return new_tweet
    
    
    def process(self, media, users, hashtags, config):
        root_directory = config.output_folder
        output_directory = config.output_status
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        index_directory = os.path.join(root_directory, 'tweets')
        if not os.path.exists(index_directory):
            os.makedirs(index_directory)
        if not os.path.exists(os.path.join(index_directory, 'index.html')):
            with open(os.path.join(index_directory, 'index.html'), 'w', encoding='utf8') as f:
                f.write('---\n')
                f.write('layout: full_index\n')
                f.write('---\n')
        year_directory = os.path.join(output_directory, str(self.date_year))
        if not os.path.exists(year_directory):
            os.makedirs(year_directory)
        year_index_directory = os.path.join(index_directory, str(self.date_year))
        if not os.path.exists(year_index_directory):
            os.makedirs(year_index_directory)
        if not os.path.exists(os.path.join(year_index_directory, 'index.html')):
            with open(os.path.join(year_index_directory, 'index.html'), 'w', encoding='utf8') as f:
                f.write('---\n')
                f.write('layout: year_index\n')
                f.write('year: ' + str(self.date_year) + '\n')
                f.write('---\n')
        month_directory = os.path.join(year_directory, str(self.date_month))
        if not os.path.exists(month_directory):
            os.makedirs(month_directory)
        month_index_directory = os.path.join(year_index_directory, str(self.date_month))
        if not os.path.exists(month_index_directory):
            os.makedirs(month_index_directory)
        if not os.path.exists(os.path.join(month_index_directory, 'index.html')):
            with open(os.path.join(month_index_directory, 'index.html'), 'w', encoding='utf8') as f:
                f.write('---\n')
                f.write('layout: month_index\n')
                f.write('year: ' + str(self.date_year) + '\n')
                f.write('month: ' + str(self.date_month) + '\n')
                f.write('---\n')
        day_directory = os.path.join(month_directory, str(self.date_day))
        if not os.path.exists(day_directory):
            os.makedirs(day_directory)
        day_index_directory = os.path.join(month_index_directory, str(self.date_day))
        if not os.path.exists(day_index_directory):
            os.makedirs(day_index_directory)
        if not os.path.exists(os.path.join(day_index_directory, 'index.html')):
            with open(os.path.join(day_index_directory, 'index.html'), 'w', encoding='utf8') as f:
                f.write('---\n')
                f.write('layout: day_index\n')
                f.write('year: ' + str(self.date_year) + '\n')
                f.write('month: ' + str(self.date_month) + '\n')
                f.write('day: ' + str(self.date_day) + '\n')
                f.write('---\n')
                
        self.filename = os.path.join(day_directory, self.id + '.html')
        
        # Now let's parse the tweet text. We'll want to change the t.co URLs to the expanded URLs,
        # and we'll want to add links to any relevant hashtags, user mentions, and URLs.
        source_full_text = self.full_text
        # First, let's replace the t.co URLs with the expanded URLs.
        tco_urls = re.findall(r'(http.*t\.co\/\w+)', source_full_text)
        if tco_urls:
            for tco_url in tco_urls:
                for url in self.urls:
                    if str(url['url']) == str(tco_url):
                        replacment_url = '<a href="' + url['expanded_url'] + '">' + url['display_url'] + '</a>'
                        source_full_text = source_full_text.replace(str(tco_url), replacment_url)
                        #print('Replaced:', replacment_url)
        # Next come the hashtags.
        if self.hashtags:
            for hashtag in self.hashtags:
                if hashtag in hashtags:
                    hashtag_link = '<a href=" {{ "/hashtags/' + hashtag + '.html" | relative_url }}>#' + hashtag + '</a>'
                    source_full_text = source_full_text.replace('#' + hashtag, hashtag_link)
        # Now the user mentions.
        if self.user_mentions:
            for user_mention in self.user_mentions:
                if user_mention['id'] in users:
                    user_details = users[user_mention['id']]
                    if user_details.following and not user_details.follower:
                        link_page = 'following.html'
                    elif user_details.follower and not user_details.following:
                        link_page = 'followers.html'
                    elif user_details.follower and user_details.following:
                        link_page = 'following.html'
                    if link_page:
                        user_link = '<a href="{{ "/' + link_page + '#' + user_details.id + '" | relative_url }}>@' + user_mention['screen_name'] + '</a>'
                        source_full_text = source_full_text.replace('@' + user_mention['screen_name'], user_link)
        self.full_text = source_full_text
        # Finally, let's check the media, and remove any duplicates.
        if self.media:
            media_check = self.media
            self.media = []
            for media_item in media_check:
                if media[media_item.id].local_filename:
                    if media[media_item.id].is_duplicated:
                        duplicate_id = media[media_item.id].duplicate_of
                        #print('Duplicate:', media_item.id, 'of', duplicate_id)      
                        original_media = media[duplicate_id]
                    else:
                        original_media = media[media_item.id]
                        original_media.local_filename = original_media.local_filename.replace(root_directory, '').replace('\\', '/')
                    #print('Filename:', root_directory, original_media.local_filename)
                    self.media.append(original_media)
                    
    def as_dict(self):
        dest_dict = {}
        if self.id:
            dest_dict['id'] = self.id
        if self.date:
            dest_dict['date'] = self.date.strftime('%Y-%m-%d %H:%M:%S')
        if self.date_day:
            dest_dict['date_day'] = self.date_day
        if self.date_month:
            dest_dict['date_month'] = self.date_month
        if self.date_year:
            dest_dict['date_year'] = self.date_year
        if self.full_text:
            dest_dict['full_text'] = self.full_text
        if self.source:
            dest_dict['source'] = self.source
        if self.retweet_count:
            dest_dict['retweet_count'] = self.retweet_count
        if self.favorite_count:
            dest_dict['favorite_count'] = self.favorite_count
        if self.in_reply_to_status_id:
            dest_dict['in_reply_to_status_id'] = self.in_reply_to_status_id
        if self.in_reply_to_user_id:
            dest_dict['in_reply_to_user_id'] = self.in_reply_to_user_id
        if self.in_reply_to_screen_name:
            dest_dict['in_reply_to_screen_name'] = self.in_reply_to_screen_name
        if self.user_mentions:
            dest_dict['user_mentions'] = self.user_mentions
        if self.hashtags:
            dest_dict['hashtags'] = self.hashtags
        if self.symbols:
            dest_dict['symbols'] = self.symbols
        if self.urls:
            dest_dict['urls'] = self.urls
        if self.embed_urls:
            dest_dict['embed_urls'] = self.embed_urls
        if self.lang:
            dest_dict['lang'] = self.lang
        if self.in_thread:
            dest_dict['in_thread'] = self.in_thread
        if self.thread_id:
            dest_dict['thread_id'] = self.thread_id
        if self.is_retweet:
            dest_dict['is_retweet'] = self.is_retweet
        if self.is_quote_tweet:
            dest_dict['is_quote_tweet'] = self.is_quote_tweet
        if self.no_of_favorites:
            dest_dict['no_of_favorites'] = self.no_of_favorites
        if self.no_of_retweets:
            dest_dict['no_of_retweets'] = self.no_of_retweets
        return dest_dict
                    
    def write(self):
        with open(self.filename, 'w', encoding='utf8') as f:
            f.write('---\n')
            f.write('layout: tweet\n')
            f.write('tweet_id: ' + str(self.id) + '\n')
            f.write('date: ' + str(self.date) + '\n')
            if self.date_day:
                f.write('date_day: ' + str(self.date_day) + '\n')
            if self.date_month:
                f.write('date_month: ' + str(self.date_month) + '\n')
            if self.date_year:
                f.write('date_year: "' + str(self.date_year) + '"\n')
            if self.source:
                f.write('source: ' + self.source + '\n')
            if self.retweet_count:
                f.write('retweet_count: ' + str(self.retweet_count) + '\n')
            if self.favorite_count:
                f.write('favorite_count: ' + str(self.favorite_count) + '\n')
            if self.no_of_favorites:
                f.write('no_of_favorites: ' + str(self.no_of_favorites) + '\n')
            if self.no_of_retweets:
                f.write('no_of_retweets: ' + str(self.no_of_retweets) + '\n')
            if self.pinned:
                f.write('pinned: ' + str(self.pinned) + '\n')
            if self.in_reply_to_status_id:
                f.write('in_reply_to_status_id: ' + str(self.in_reply_to_status_id) + '\n')
            if self.in_reply_to_user_id:
                f.write('in_reply_to_user_id: ' + str(self.in_reply_to_user_id) + '\n')
            if self.in_reply_to_screen_name:
                f.write('in_reply_to_screen_name: "' + self.in_reply_to_screen_name + '"\n')
            if self.user_mentions:
                f.write('user_mentions:\n')
                for user_mention in self.user_mentions:
                    f.write('  - id: ' + user_mention['id'] + '\n')
                    f.write('    screen_name: "' + user_mention['screen_name'] + '"\n')
            if self.hashtags:
                f.write('hashtags:\n')
                for hashtag in self.hashtags:
                    f.write('  - ' + hashtag + '\n')
            if self.symbols:
                f.write('symbols:\n')
                for symbol in self.symbols:
                    f.write('  - ' + symbol + '\n')
            if self.urls:
                f.write('urls:\n')
                for url in self.urls:
                    f.write('  - url: "' + url['url'] + '"\n')
                    f.write('    expanded_url: "' + url['expanded_url'] + '"\n')
                    f.write('    display_url: "' + url['display_url'] + '"\n')
            if self.embed_urls:
                f.write('embed_urls:\n')
                for embed_url in self.embed_urls:
                    f.write('  - type: ' + embed_url['type'] + '\n')
                    f.write('    embed_id: ' + embed_url['embed_id'] + '\n')
            if self.lang:
                f.write('lang: ' + self.lang + '\n')
            if self.in_thread:
                f.write('in_thread: ' + str(self.in_thread) + '\n')
            if self.thread_id:
                f.write('thread_id: ' + str(self.thread_id) + '\n')
            if self.is_retweet:
                f.write('is_retweet: ' + str(self.is_retweet) + '\n')
            if self.is_quote_tweet:
                f.write('is_quote_tweet: ' + str(self.is_quote_tweet) + '\n')
            if self.media:
                for media_item in self.media:
                    if media_item.local_filename:
                        f.write('media:\n')
                        f.write('  - id: ' + str(media_item.id) + '\n')
                        f.write('    url: "' + media_item.url + '"\n')
                        f.write('    local_filename: "' + media_item.local_filename + '"\n')
                        f.write('    file_size: ' + str(media_item.file_size) + '\n')
                        f.write('    type: ' + media_item.type + '\n')
                        if media_item.video_info:
                            f.write('    video_info:\n')
                            f.write('      duration_millis: ' + str(media_item.duration_millis) + '\n')
                    #if media_item.additional_media_info:
                        #f.write('    additional_media_info:\n')
                        #if media_item.additional_media_info['description']:
                        #    f.write('      description: ' + media_item.additional_media_info['description'] + '\n')
                        #if media_item.additional_media_info['alt_text']:
                        #    f.write('      alt_text: ' + media_item.additional_media_info['alt_text'] + '\n')
                    if media_item.source_tweet_id:
                        f.write('    source_tweet_id: ' + str(media_item.source_tweet_id) + '\n')
                    if media_item.source_user_id:
                        f.write('    source_user_id: ' + str(media_item.source_user_id) + '\n')
                    if media_item.is_duplicated:
                        f.write('    is_duplicated: ' + str(media_item.is_duplicated) + '\n')
                    if media_item.duplicate_of:
                        f.write('    duplicate_of: ' + str(media_item.duplicate_of) + '\n')
            if self.no_of_favorites:
                f.write('no_of_favorites: ' + str(self.no_of_favorites) + '\n')
            if self.no_of_retweets:
                f.write('no_of_retweets: ' + str(self.no_of_retweets) + '\n')
            f.write('---\n')
            f.write(self.full_text) 
class Media:
    def __init__(self, 
                    id,
                    url = None,
                    downloaded = False,
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
                    is_duplicated = None,
                    duplicate_of = None
        ):
        self.id = id
        self.url = url
        self.tco_url = tco_url
        self.downloaded = downloaded
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
        self.is_duplicated = is_duplicated
        self.duplicate_of = duplicate_of

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


class DateStats:
    
    def __init__(self, date = None):
        self.data = {}
        if date:
            self.add_date(date)
            
    def add_date(self, date):
        if not date:
            return
        date_day = date.day
        date_month = date.month
        date_year = date.year
        if date_year not in self.data:
            self.data[date_year] = {
                'count': 0,
                'months': {}
            }
        self.data[date_year]['count'] += 1
        
        if date_month not in self.data[date_year]['months']:
            self.data[date_year]['months'][date_month] = {
                'count': 0,
                'days': {}
            }
        self.data[date_year]['months'][date_month]['count'] += 1
        
        if date_day not in self.data[date_year]['months'][date_month]['days']:
            self.data[date_year]['months'][date_month]['days'][date_day] = {
                'count': 0
            }
        self.data[date_year]['months'][date_month]['days'][date_day]['count'] += 1

    def as_yaml(self):
        output_yaml = ''   
        for year in self.data:
            output_yaml += '- ' + str(year) + ':' + str(self.data[year]['count']) + '\n'
            for month in self.data[year]['months']:
                output_yaml += '  - ' + str(month) + ':' + str(self.data[year]['months'][month]['count']) + '\n'
                for day in self.data[year]['months'][month]['days']:
                    output_yaml += '    - ' + str(day) + ':' + str(self.data[year]['months'][month]['days'][day]['count']) + '\n'
        return output_yaml
    
    def as_json(self):
        return json.dumps(self.data, indent=4)
