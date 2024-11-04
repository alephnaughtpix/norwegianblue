from lib.config import Config
from lib.ui import ProgressWindow
from lib.user_profile import UserProfile
from lib.utils import Utils, UriLoader
from lib.tweet import Tweet
import glob
import json
import os
import re
import requests
import shutil
import time

class Processor:

    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.source_directory = None
        self.output_directory = None
        self.config = Config(root_dir)
        self.__user_profile = None
        self.__tweets = None
        self.__media = None
        self.__hastags = None
        self.__data_directory = None
        self.__assets_directory = None
        self.__tweet_filenames = []
        self.__tweet_media_folder = None
        self.__process_window = None
        self.__MAX_STEPS = 10
        self.__CURRENT_STEP = 0
    
    # Check if the directory is a Twitter archive
    def is_twitter_archive(self, directory):
        exists = os.path.exists(os.path.join(directory, 'data'))
        exists = exists and os.path.exists(os.path.join(directory, 'assets'))#
        if exists:
            self.__data_directory = os.path.join(directory, 'data')
            self.__assets_directory = os.path.join(directory, 'assets')
            self.__tweet_filenames = self.__find_tweet_files( self.__data_directory )
            self.__tweet_media_folder = self.__find_media_folder( self.__data_directory )
            exists = exists and len(self.__tweet_filenames) > 0
            exists = exists and self.__tweet_media_folder is not None
            exists = exists and os.path.exists(os.path.join(self.__data_directory, 'account.js'))
            exists = exists and os.path.exists(os.path.join(self.__data_directory, 'profile.js'))
            exists = exists and os.path.exists(os.path.join(self.__data_directory, 'follower.js'))
            exists = exists and os.path.exists(os.path.join(self.__data_directory, 'following.js'))
            exists = exists and os.path.exists(os.path.join(self.__assets_directory, 'images/favicon.ico'))
        return exists
    
    def output_directory_is_empty(self, output_directory = None):
        if output_directory is None:
            output_directory = self.output_directory
        return (len(os.listdir(output_directory))==0)
            
    # Identify the tweet archive's filenames- they change slightly depending on the archive size it seems.
    def __find_tweet_files(self, data_folder):
        tweet_js_filename_templates = ['tweet.js', 'tweets.js', 'tweets-part*.js']
        tweet_files = []
        for tweet_js_filename_template in tweet_js_filename_templates:
            for filename in glob.glob(os.path.join(data_folder, tweet_js_filename_template)):
                if os.path.isfile(filename):
                    tweet_files.append(filename)
        return tweet_files
    
    # Identify the tweet archive's media folders- they change slightly depending on the archive size it seems.
    def __find_media_folder(self, data_folder):
        tweet_media_folder_name_templates = ['tweet_media', 'tweets_media']
        tweet_media_folder_names = []
        for tweet_media_folder_name_template in tweet_media_folder_name_templates:
            media_folders = glob.glob(os.path.join(data_folder, tweet_media_folder_name_template))
            for tweet_media_folder_name in media_folders:
                if os.path.isdir(tweet_media_folder_name):
                    tweet_media_folder_names.append(tweet_media_folder_name)
        if len(tweet_media_folder_names) > 0:
            return tweet_media_folder_names[0]
        else:
            return None


    def start(self, 
              source_directory, 
              output_directory, 
              followers_filename, 
              following_filename, 
              sleep_time = 0.25, 
              download_media = True):
        # Ensure the source directory exists
        if not os.path.isdir(source_directory):
            raise ValueError(f'Error: Source directory "{source_directory}" does not exist')
        
        # Ensure the output directory exists
        if not os.path.isdir(output_directory):
            raise ValueError(f'Error: Output directory "{output_directory}" does not exist')
        
        self.source_directory = source_directory
        self.output_directory = output_directory
        
        # Set up our config object, with all the directories we need
        self.config.update(source_directory, 
                           output_directory, 
                           followers_filename, 
                           following_filename, 
                           sleep_time, 
                           download_media)
        
        
        self.__tweet_filenames = self.__find_tweet_files( self.config.data_folder )
        self.__tweet_media_folder = self.__find_media_folder( self.config.data_folder )
        
        self.__process_window = ProgressWindow()
        self.__process_window.thread(self.process_steps)
        self.__process_window.show()
        
    def process_steps(self):
            self.__copy_jekyll_files()          # Step 1
            self.__get_user_profile()           # Step 2
            self.__read_tweets()                # Step 3
            self.__copy_local_media()           # Step 4
            self.__download_missing_media()     # Step 5
            self.__write_hashtag_pages()        # Step 6
            
            
            #if config.already_existing():
            #    raise ValueError(f'Error: Output directory "{output_directory}" already contains files')
            
    def __next_step(self):
        self.__CURRENT_STEP += 1
        self.__process_window.update_top_progress(int((self.__CURRENT_STEP / self.__MAX_STEPS) * 100))
        
    # Step 1: Copy the Norwegian Blue Jekyll template files to the output directory
    def __copy_jekyll_files(self):
        self.__process_window.top_status('Copying Norwegian Blue template files...')
        self.__process_window.update_top_progress(0)
        file_scan = os.walk(self.root_dir)
        no_of_files = 0
        for root, subFolder, files in file_scan:        # Weed out the .git, compiled Python and .jekyll-cache files
            if '.git' in root or '.jekyll-cache' in root or '__pycache__' in root or 'venv' in root:
                continue 
            no_of_files += len(files)
        file_count = 0
        for root, subFolder, files in os.walk(self.root_dir):
            if '.git' in root or '.jekyll-cache' in root or '__pycache__' in root or 'venv' in root:
                continue
            root = root.replace(self.root_dir, '').replace('\\', '/')
            output_directory = self.output_directory + root 
            if not os.path.exists(output_directory):
                os.makedirs(output_directory) 
            for file in files:
                file_count += 1
                self.__process_window.update_progress(int((file_count / no_of_files)*100))
                self.__process_window.status(f'Copying {file_count} of {no_of_files} files.')
                source_file = os.path.join(self.root_dir + root, file)
                shutil.copy(source_file, os.path.join(output_directory, file))
        self.__next_step()
        
    # Step 2: Get the user profile from the Twitter archive
    def __get_user_profile(self):
        step = 0
        no_of_steps = 8
        self.__process_window.update_progress(int((step / no_of_steps)*100))
        self.__process_window.top_status('Getting user profile...')
        sleep_time= self.config.sleep_time
        download_media = self.config.download_media 
        self.__process_window.status('Reading profile data...')
        
        # Get principle data from profile.js
        profile_data = Utils.read_json_file(os.path.join(self.config.data_folder, 'profile.js'))[0]['profile']
        description = profile_data['description']['bio']
        website_tco = profile_data['description']['website']
        location = profile_data['description']['location']
        avatar_url = profile_data['avatarMediaUrl']
        header_url = profile_data['headerMediaUrl']
        step += 1
        self.__process_window.update_progress(int((step / no_of_steps)*100))
            
        # Get extra data from account.js
        self.__process_window.status('Extra account info...')
        account_data = Utils.read_json_file(os.path.join(self.config.data_folder, 'account.js'))[0]['account']
        user_id = account_data['accountId']
        screen_name = account_data["accountDisplayName"]
        username = account_data["username"]
        joined_date = account_data["createdAt"]
        email = account_data["email"]
        created_via = account_data["createdVia"]

        self.__user_profile = UserProfile(user_id, 
                description=description, 
                location=location, 
                url=website_tco, 
                avatar_url=avatar_url, 
                header_url=header_url,
                username=username,
                screen_name=screen_name,
                joined_date=joined_date,
                email=email,
                created_via=created_via
            )
        step += 1
        self.__process_window.update_progress(int((step / no_of_steps)*100))

        if avatar_url:
            avatar_url_ext = os.path.splitext(avatar_url)[1]
        if website_tco:
            # Get original link for t.co link- currently the t.co link returns a short HTML page which
            # contain a javascript redirect to the original link, as well as a META http-equiv="refresh"
            # equivalent. (How very 1998!). The original link is in the <title> tag, so that's the 
            # easier bit to extract.
            #
            # Example of the HTML returned by t.co:
            # <head><noscript><META http-equiv="refresh" content="0;URL=[REAL URL]"></noscript><title>[REAL URL]</title></head><script>window.opener = null; location.replace("https:\\/\\/[REAL URL]")</script>
            self.__process_window.status('Getting website link...')
            with UriLoader(website_tco, self.config) as tco_loader:
                website = website_tco
                if tco_loader.success:
                    redirect_code = str(tco_loader.data.content)
                    urls = re.findall('<title>(.*)<\/title>', redirect_code)
                    if urls:
                        website = urls[0]
                self.__user_profile.url = website
                time.sleep(sleep_time)
        step += 1
        self.__process_window.update_progress(int((step / no_of_steps)*100))
        # Download avatar image.
        if avatar_url and download_media:      
            self.__process_window.status('Downloading avatar...')
            avatar_file = os.path.join(self.config.output_assets_images_folder, 'avatar' + avatar_url_ext)
            with UriLoader(avatar_url, self.config) as avatar_loader:
                if avatar_loader.success:
                    with open(avatar_file, 'wb') as f:
                        f.write(avatar_loader.data.content)
                time.sleep(sleep_time)
        step += 1
        self.__process_window.update_progress(int((step / no_of_steps)*100))
        # Get header image. There is *no* file extension here, so we have to infer it from the content-type.
        if header_url and download_media:
            self.__process_window.status('Downloading header...')
            with UriLoader(header_url, self.config) as header_loader:
                if header_loader.success:
                    header_ext = header_loader.guess_ext()
                    header_file = os.path.join(self.config.output_assets_images_folder, 'header.' + header_ext)
                    print('Header file:', header_file)
                    with open(header_file, 'wb') as f:
                        f.write(header_loader.data.content)
            time.sleep(sleep_time)
        step += 1
        self.__process_window.update_progress(int((step / no_of_steps)*100))

        # Timezone!
        self.__process_window.status('Getting timezone...')
        timezone_data = Utils.read_json_file(os.path.join(self.config.data_folder, 'account-timezone.js'))
        timezone = timezone_data[0]['accountTimezone']['timeZone']
        self.__user_profile.timezone = timezone
        time.sleep(sleep_time)
        step += 1
        self.__process_window.update_progress(int((step / no_of_steps)*100))
        
        # Birth date
        self.__process_window.status('Getting birthdate...')
        birthdate_data = Utils.read_json_file(os.path.join(self.config.data_folder, 'ageinfo.js'))
        birthdate = birthdate_data[0]['ageMeta']['ageInfo'] ['birthDate']
        self.__user_profile.birthdate = birthdate
        time.sleep(sleep_time)
        step += 1
        
        # Finally we write all the data we have to the Jekyll config file.
        self.__process_window.status('Writing profile data to website config...')
        self.__user_profile.add_to_config_file(self.config.jekyll_config_filename)
        step += 1
        self.__process_window.update_progress(int((step / no_of_steps)*100))
        time.sleep(sleep_time)
            
        self.__next_step()
        
    # Step 3: Read the tweets into memory for processing
    def __read_tweets(self):
        self.__process_window.top_status('Reading tweets...')
        self.__process_window.status('Reading tweet data...')
        tweet_count = 0
        sleep_time = self.config.sleep_time
        self.__tweets = {}
        self.__media = {}
        self.__hastags = {}
        self.__process_window.update_progress(0)
        #print(f"Reading {self.__tweet_filenames} tweet files.")
        for tweet_filename in self.__tweet_filenames:
            tweet_data = Utils.read_json_file(tweet_filename)
            no_of_tweets = len(tweet_data)
            for tweet in tweet_data:
                #print(f"Reading tweet {tweet_count} of {no_of_tweets} files.")
                self.__process_window.update_progress(int((tweet_count / no_of_tweets)*100))
                self.__process_window.status(f'Reading {tweet_count} of {no_of_tweets} tweets.')
                #time.sleep(sleep_time)
                new_tweet = Tweet.import_tweet_json(tweet['tweet'])
                self.__tweets[new_tweet.id] = new_tweet
                for media_obj in new_tweet.media:
                    if media_obj.id not in self.__media:
                        self.__media[media_obj.id] = media_obj
                for hashtag in new_tweet.hashtags:
                    if hashtag not in self.__hastags:
                        self.__hastags[hashtag] = []
                    self.__hastags[hashtag].append(new_tweet.id)
                tweet_count += 1
        self.__next_step()
        
    # Step 4: Copy local media files to the output directory
    def __copy_local_media(self):
        self.__process_window.top_status('Copying local media from archive...')
        self.__process_window.update_progress(0)
        media_count = 0
        media_total = len(self.__media)
        output_folder = self.config.output_media_folder_name
        for media_id in self.__media:
            media_obj = self.__media[media_id]
            local_filename = media_obj.make_local_filename(self.__tweet_media_folder)
            if local_filename:
                output_filename = media_obj.make_output_filename(output_folder)
                shutil.copy(local_filename, output_filename)
                self.__media[media_id].local_filename = output_filename
            media_count += 1
            self.__process_window.update_progress(int((media_count / media_total)*100))
            self.__process_window.status(f'Copying {media_count} of {media_total} media files.')
        self.__next_step()
        
    # Step 5: Download any media files missing from the archive
    def __download_missing_media(self):
        self.__process_window.top_status('Downloading media not in archive...')
        self.__process_window.update_progress(0)
        sleep_time= self.config.sleep_time
        media_count = 0
        media_downloads = []
        # Work out how many to download
        for media_id in self.__media:
            if not self.__media[media_id].local_filename:
                media_downloads.append(media_id)
        media_total = len(media_downloads)
        output_folder = self.config.output_media_folder_name
        for media_id in media_downloads:
            media_obj = self.__media[media_id]
            output_filename = media_obj.make_output_filename(output_folder)
            #('type:', media_obj.type, media_obj.url)
            with UriLoader(media_obj.url, self.config) as media_loader:
                if media_loader.success:
                    with open(output_filename, 'wb') as f:
                        f.write(media_loader.data.content)
                    self.__media[media_id].local_filename = output_filename
                    self.__media[media_id].file_size = os.path.getsize(output_filename)
            media_count += 1
            self.__process_window.update_progress(int((media_count / media_total)*100))
            self.__process_window.status(f'Downloading {media_count} of {media_total} media files.')
            time.sleep(sleep_time)
        self.__next_step()
        
    # Step 6: Write the pages for the hashtags
    def __write_hashtag_pages(self):
        self.__process_window.top_status('Creating pages for hashtags...')
        self.__process_window.update_progress(0)
        sleep_time= self.config.sleep_time
        hashtag_count = 0
        hashtag_total = len(self.__hastags)
        for hashtag in self.__hastags:
            hashtag_count += 1
            self.__process_window.status(f'Writing {hashtag_count} of {hashtag_total} hashtag pages.')
            output_filename = os.path.join(self.config.output_hashtag_folder_name, hashtag + '.html')
            with open(output_filename, 'w', encoding='utf8') as output_file:
                output_file.write('---\n')
                output_file.write('layout: hashtag\n')
                output_file.write('title: ' + hashtag + '\n')
                output_file.write('tweets:\n')
                for tweet_id in self.__hastags[hashtag]:
                    output_file.write('  - ' + tweet_id + '\n')
                output_file.write('---\n')
            self.__process_window.update_progress(int((hashtag_count / hashtag_total)*100))
        hashtags_json_filename = os.path.join(self.config.output_json_folder_name, 'hashtags.js')
        hashtags_json = json.dumps(self.__hastags, indent=4)
        with open(hashtags_json_filename, 'w', encoding='utf8') as hashtags_json_file:
            hashtags_json_file.write('var hashtags = '+ (hashtags_json + ';'))
        self.__next_step()
        
    # Step 7: Analyse followers
    def __analyse_followers(self):
        pass
        