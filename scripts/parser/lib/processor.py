from bs4 import BeautifulSoup
from filecmp import cmp
from lib.config import Config
from lib.ui import ProgressWindow
from lib.user_profile import UserProfile
from lib.utils import *
from lib.tweet import Tweet, Media, DateStats
from tkinter import messagebox
import data_url
import glob
import json
import os
import re
import shutil
import time

class Processor:

    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.source_directory = None
        self.output_directory = None
        self.config = Config(root_dir)
        self.processing = False
        self.__user_profile = None
        self.__tweets = None
        self.__media = None
        self.__hastags = None
        self.__users = None
        self.__data_directory = None
        self.__assets_directory = None
        self.__tweet_filenames = []
        self.__tweet_media_folder = None
        self.__process_window = None
        self.__MAX_STEPS = 15
        self.__CURRENT_STEP = 0
        self.__tweetstats = None
        self.__threadstats = None
    
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
        
        self.processing = True
        
        self.source_directory = source_directory
        self.output_directory = output_directory
        
        self.__tweet_stats = DateStats()
        self.__thread_stats = DateStats()
        
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
            self.__copy_jekyll_files()              # Step 1
            self.__get_user_profile()               # Step 2
            self.__read_tweets()                    # Step 3
            self.__copy_local_media()               # Step 4
            self.__download_missing_media()         # Step 5
            self.__write_hashtag_pages()            # Step 6
            self.__analyse_followers_following()    # Step 7
            self.__parse_followers_page()           # Step 8
            self.__parse_following_page()           # Step 9
            self.__save_users_avatars()             # Step 10 
            self.__save_followers_following()       # Step 11
            self.__analyse_retweets()               # Step 12
            self.__analyse_threads()                # Step 13
            self.__consolidate_media()              # Step 14
            self.__write_tweets()                   # Step 15
            self.__clear_duplicates()               # Step 16
            
            self.processing = False
            
            self.__process_window.top_status('Complete')
            self.__process_window.status('Twitter archive processed successfully.')
            messagebox.showinfo('Processing complete', 'Twitter archive processed successfully.\n\nThe website has been created in the directory:\n\n' + self.output_directory)
            self.__process_window.close()
            
            
            #if config.already_existing():
            #    raise ValueError(f'Error: Output directory "{output_directory}" already contains files')
            
    def __next_step(self):
        self.__CURRENT_STEP += 1
        self.__process_window.update_top_progress(int((self.__CURRENT_STEP / self.__MAX_STEPS) * 100))
    
    # Extract user information from the a fragment of HTML of the followers/following page. As the HTML
    # fragment contains lots of divs within divs, which loads of inscrutable class names which suspiciously
    # look like they're generated by a UI framework like Angular or React, we have to think laterally in
    # how we extract from the HTML. We're using the BeautifulSoup library to parse.
    def __extract_user_data_from_html(self, follower_node, follower_id, output_dir, user_list):
        sleep_time = self.config.sleep_time
        # First, to make things easier, we extract the bit that's 
        # easy to extract. The user cell, which is in a <button> tag (!!!) with the data-testid
        # attribute set to 'UserCell'.
        user_cell_search = follower_node.find_all('button', attrs={'data-testid': 'UserCell'})
        if not len(user_cell_search) > 0:
            return None, None, None, None, None, None, None
        user_cell = user_cell_search[0]
                
        # Getting the username is a bit tricky. It's in a <span> class with the inline style attribute
        # 'text-overflow:unset', and there are a lot of those! So we look for ones that contain text starting
        # with '@' and extract that. We also have to verify this, as a lot of people put the usernames of their
        # other social media on the screen name and descriptions. Luckily, the <span> is contained within an
        # <a> tag three parents up with the href attribute set to the user's profile URL. (https//x.com/[username without @])
        style_spans = user_cell.select('span[style*="text-overflow:unset"]')    # There may be more than one of these.
        username = None
        a_tag = None
        for style_span in style_spans:
            span_text = style_span.string
            if span_text:
                if span_text.startswith('@'):
                    username = span_text.replace('@', '')
            # For the verification, we look for the <a> tag three parents up.
            if username:
                a_tag = style_span.parent.parent.parent
                if a_tag.name == 'a':
                    test_url = 'https://x.com/' + username
                    actual_url = a_tag['href']
                    if test_url == actual_url:
                        break
                    else:
                        username = None
        
        # If we've got the username, we can get the user ID from the user list.
        user_id = None       
        if username:
            user_id = UserProfile.find_id_for_username(username, user_list)
        else:
            user_id = follower_id   # <- If don't have an id, allocate one.
            print('user_id:', user_id)
            
        # We're going to use the <a> to get to the node containing the screen name, as we can
        # just go up two parents, and it's contained in the previous sibling next to it.
        screen_name = None
        if a_tag:
            screen_name_tag = a_tag.parent.parent.previous_sibling
            if screen_name_tag:
                screen_name =" ".join(el.strip() for el in screen_name_tag.strings)
                if screen_name:
                    screen_name = '"' + screen_name + '"'
                #print('Screen name:', screen_name)
        
        # The easiest thing to extract is the avatar, which is a div with an inline style attribute
        # containing a background-image CSS property (!) pointing to the avatar.
        avatar_url = None
        local_url = None
        avatar_tag = user_cell.select('div[style*="background-image"]')
        if avatar_tag:
            avatar_style = str(avatar_tag[0]['style'])
            #print('avatar_style:', avatar_style)
            avatar_url_search = re.search(r'url\((.*?)\)', avatar_style)
            if avatar_url_search:
                avatar_url = avatar_url_search.group(1)
            else:
                avatar_url = None
                    
        # Get "follow/following" state. This is 4 parents up from the <a>, and the next sibling along
        follow_state = None
        follow_state_tag = None
        if a_tag:
            follow_state_tag = a_tag.parent.parent.parent.parent.next_sibling
            if follow_state_tag:
                #follow_state = follow_state_tag.string
                follow_state = " ".join(el.strip() for el in follow_state_tag.strings)
                follow_state = follow_state.split(' ')[0].lower()
                #print('Follow state:', follow_state)
                
        # This is where it gets dirty! The desciption text is up a parent, and then the next sibling,
        # we can't use the '.string' method to get it as it's a div tag containing a series of <span>, <div>
        # or <a> tags, containing parts of the description text in order. For example, links are in separate 
        # <span> tags. This also contains emojis, which are in <img> containing a data url for an SVG image. (Quite a good
        # idea, really, as it means they're compatible across devices.)
        description_tag = None
        description = None
        if follow_state_tag:
            description_tag = follow_state_tag.parent.next_sibling
            if description_tag:
                description_parts = description_tag.findChildren(recursive=False)
                if description_parts:
                    description = ''
                    for part in description_parts:
                        if part:
                            link_start = ''
                            if part.name == 'img':
                                description += '<img src=\\\"' + part['src'] + '\\\"/>'
                            else:
                                for content in part.contents:
                                    if content:
                                        content_result = ''
                                        if content.name == 'span':
                                            content_result += str(content.text)
                                            if content_result.startswith('http'):
                                                link_start = content_result
                                                content_result = ''
                                        elif content.name == 'div':
                                            twitter_handle = content.select('a')
                                            if twitter_handle:
                                                content_result = '<a href=\"' + twitter_handle[0]['href'] + '\">' + twitter_handle.text + '</a>'
                                            else:
                                                content_result = str(content)
                                        else:
                                            if link_start != '':
                                                content_result = '<a href=\"' + link_start + str(content) + '\">' + str(content) + '</a>' 
                                                link_start = ''
                                            else:
                                                content_result = str(content)
                                        if content_result != '':
                                            description += str(content_result).replace('\n', '<br/>').replace('\"', '\\\"')
                    if description != '':
                        description = '"' + Utils.sanitise_html(description) + '"'
                        description = description.replace('\'\\\"', '\\\"').replace('\\\"\'', '\\\"')
        return user_id, username, screen_name, description, follow_state, avatar_url, local_url
        
    # Step 1: Copy the Norwegian Blue Jekyll template files to the output directory
    def __copy_jekyll_files(self):
        self.__process_window.top_status('Copying Norwegian Blue template files...')
        self.__process_window.update_top_progress(0)
        file_scan = os.walk(self.root_dir)
        no_of_files = 0
        for root, subFolder, files in file_scan:        # Weed out the .git, compiled Python and .jekyll-cache files
            if '.git' in root or '.jekyll-cache' in root or '__pycache__' in root \
                or 'venv' in root or 'parser' in root:
                continue 
            no_of_files += len(files)
        file_count = 0
        for root, subFolder, files in os.walk(self.root_dir):
            if '.git' in root or '.jekyll-cache' in root or '__pycache__' in root \
                or 'venv' in root or 'parser' in root:
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
        no_of_steps = 9
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
        header_url = profile_data['headerMediaUrl'] + '/1500x500'
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
                    #print('Redirect code:', redirect_code)
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
                        self.__user_profile.local_url = avatar_file.replace(self.config.output_folder, '')
                time.sleep(sleep_time)
        step += 1
        self.__process_window.update_progress(int((step / no_of_steps)*100))
        
        # Get header image. The header image URL in the account.js file no longer works straight out the box, and
        # has to have an additional parameter added to the URL, which is '/1500x500' There is *no* file 
        # extension here, so we have to infer it from the content-type.
        if header_url and download_media:
            self.__process_window.status('Downloading header...')
            with UriLoader(header_url, self.config) as header_loader:
                if header_loader.success:
                    header_ext = header_loader.guess_ext()
                    header_file = os.path.join(self.config.output_assets_images_folder, 'header.' + header_ext)
                    with open(header_file, 'wb') as f:
                        f.write(header_loader.data.content)
                        self.__user_profile.local_header_url = header_file.replace(self.config.output_folder, '')
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
        self.__process_window.update_progress(int((step / no_of_steps)*100))
        
        # Get no of followers and following
        self.__process_window.status('Getting no. of followers and following...')
        followers_data = Utils.read_json_file(os.path.join(self.config.data_folder, 'follower.js'))
        following_data = Utils.read_json_file(os.path.join(self.config.data_folder, 'following.js'))
        followers = len(followers_data)
        following = len(following_data)
        self.__user_profile.no_of_followers = followers
        self.__user_profile.no_following = following
        time.sleep(sleep_time)
        step += 1
        self.__process_window.update_progress(int((step / no_of_steps)*100))
        
        # Get no of tweets
        self.__process_window.status('Getting no. tweets...')
        tweet_count = 0
        for tweet_filename in self.__tweet_filenames:
            tweet_data = Utils.read_json_file(tweet_filename)
            tweet_count += len(tweet_data)
        self.__user_profile.no_tweets = tweet_count
        time.sleep(sleep_time)
        step += 1
        self.__process_window.update_progress(int((step / no_of_steps)*100))

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
        self.__tweets = {}
        self.__media = {}
        self.__hastags = {}
        self.__process_window.update_progress(0)
        for tweet_filename in self.__tweet_filenames:
            tweet_data = Utils.read_json_file(tweet_filename)
            no_of_tweets = len(tweet_data)
            for tweet in tweet_data:
                self.__process_window.update_progress(int((tweet_count / no_of_tweets)*100))
                self.__process_window.status(f'Reading {tweet_count} of {no_of_tweets} tweets.')
                new_tweet = Tweet.import_tweet_json(tweet['tweet'])
                self.__tweet_stats.add_date(new_tweet.date)
                self.__tweets[new_tweet.id] = new_tweet
                for media_obj in new_tweet.media:
                    if media_obj.id not in self.__media:
                        self.__media[media_obj.id] = media_obj
                for hashtag in new_tweet.hashtags:
                    if hashtag not in self.__hastags:
                        self.__hastags[hashtag] = []
                    self.__hastags[hashtag].append(new_tweet.id)
                tweet_count += 1
        # If a hashtag has only one tweet from your archive, then it's a bit of a waste of time
        # to create a whole page for it. So we'll remove hastags with only one tweet.
        current_hashtags = self.__hastags.copy()
        for hashtag in current_hashtags:
            if len(current_hashtags[hashtag]) < 2:
                del self.__hastags[hashtag]
        self.__next_step()
        
    # Step 4: Copy local media files from the archive to the output directory
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
                if os.path.exists(local_filename):
                    output_filename = media_obj.make_output_filename(output_folder)
                    shutil.copy(local_filename, output_filename)
                    self.__media[media_id].local_filename = output_filename
                    self.__media[media_id].file_size = os.path.getsize(output_filename)
                    self.__media[media_id].downloaded = True
            media_count += 1
            self.__process_window.update_progress(int((media_count / media_total)*100))
            self.__process_window.status(f'Copying {media_count} of {media_total} media files.')
        self.__next_step()
        
    # Step 5: Download any media files missing from the archive.
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
        not_downloaded = 0
        for media_id in media_downloads:
            media_obj = self.__media[media_id]
            output_filename = media_obj.make_output_filename(output_folder)
            with UriLoader(media_obj.url, self.config) as media_loader:
                if media_loader.success:
                    with open(output_filename, 'wb') as f:
                        f.write(media_loader.data.content)
                    self.__media[media_id].local_filename = output_filename
                    self.__media[media_id].file_size = os.path.getsize(output_filename)
                    self.__media[media_id].downloaded = True    # <- Mark as downloaded. (The default is False.)
                else:
                    not_downloaded += 1
            media_count += 1
            self.__process_window.update_progress(int((media_count / media_total)*100))
            self.__process_window.status(f'Downloading {media_count} of {media_total} media files.')
            if not_downloaded > 0:
                self.__process_window.top_status(f'Downloading media not in archive... ({not_downloaded} failed)')
            time.sleep(sleep_time)
        self.__next_step()
        
    # Step 6: After going through the tweets, we've got all the information about hashtags used in the tweets.
    # So now we can create the pages for the hashtags.
    def __write_hashtag_pages(self):
        self.__process_window.top_status('Creating pages for hashtags...')
        self.__process_window.update_progress(0)
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
        
    # Step 7: Analyse followers and following.
    def __analyse_followers_following(self):
        if not self.config.save_followers:
            return
        self.__process_window.top_status('Analysing followers and following...')
        self.__process_window.update_progress(0)
        followers_data = Utils.read_json_file(os.path.join(self.config.data_folder, 'follower.js'))
        following_data = Utils.read_json_file(os.path.join(self.config.data_folder, 'following.js'))
        followers_following = {}
        # Initial pass- just get the basic data from the archive json. There's not very much to work
        # with here, as you only get the user ID and the URL to the user's profile page. The most 
        # useful information we can get at this point is the followers and following count.
        for follower in followers_data:
            follower_id = follower['follower']['accountId']
            if follower_id in followers_following:
                followers_following[following_id].follower = True
                continue
            url = follower['follower']['userLink']
            follower_user_profile = UserProfile(follower_id, url=url, follower=True)
            followers_following[follower_id] = follower_user_profile
        for following in following_data:
            following_id = following['following']['accountId']
            if following_id in followers_following:
                followers_following[following_id].following = True
                continue
            url = following['following']['userLink']
            following_user_profile = UserProfile(following_id, url=url, following=True)
            followers_following[following_id] = following_user_profile
        # Second pass- go through the tweets and see if any of the users are mentioned in the tweets. This
        # will give us the screen name and the user name, which we match up with the user ID. The next two
        # steps will go through the followers/following pages, which will give us more information.
        self.__process_window.top_status('Analysing tweets for mentions...')
        found_mentions = 0
        current_tweet_count = 0
        no_of_tweets = len(self.__tweets)
        for tweet in self.__tweets:
            current_tweet = self.__tweets[tweet]
            current_tweet_count += 1
            self.__process_window.update_progress(int((current_tweet_count / no_of_tweets)*100))
            self.__process_window.status(f'Analysing tweet {current_tweet_count} of {no_of_tweets}.')
            # While we're here, we'll also check for a retweet.
            if current_tweet.full_text.startswith('RT @'):
                self.__tweets[tweet].is_retweet = True
            # Check the the mentions in the tweet, as this contains the screen names of the users mentioned
            mentions = current_tweet.user_mentions
            if mentions:
                for mention in mentions:
                    if 'id' in mention:
                        if mention['id'] in followers_following:
                            found = False
                            mention_id = mention['id']
                            if followers_following[mention_id].username is None:
                                followers_following[mention_id].username = mention['screen_name']
                                followers_following[mention_id].url =self.config.user_id_URL_template.format(mention['screen_name'])
                                found = True
                            if followers_following[mention_id].screen_name is None:
                                followers_following[mention_id].screen_name = mention['name']
                                found = True
                            if found:
                                found_mentions += 1
                            self.__process_window.top_status('Analysing tweets for mentions... (Found ' + str(found_mentions) + ')')

        # Finally, weed out any users that don't have a username linked to their ID.
        # (Hopefully we'll be able to get most of those from the followers/following pages)
        self.__users = {}
        for user_id in followers_following:
            if followers_following[user_id].username:
                self.__users[user_id] = followers_following[user_id]
        self.__next_step()
                            
    # Step 8: Go through the pre-saved followers page if the user has supplied one
    #
    # This is the ugliest part of the process. To say the HTML for a Twitter page is a bit
    # bloated is like saying the sun is a bit warm. This is where we use the Beuatiful Soup
    # library to parse the HTML.
    def __parse_followers_page(self):
        if self.config.followers_page:
            if os.path.exists(self.config.followers_page):
                self.__process_window.top_status('Analysing followers page...')
                self.__process_window.status('Reading followers page...')
                self.__process_window.update_progress(0)
                with open(self.config.followers_page, 'r', encoding='utf8') as followers_page_file:
                    html_parser = BeautifulSoup(followers_page_file, 'html.parser')
                    page_title = html_parser.title.string
                    print('Page title:', page_title)
                    # The followers list is in a div with the aria-label attribute set to 'Timeline: Followers'. Within *that* is another div that contains the followers list.
                    follower_list = html_parser.find_all('div', attrs={'aria-label': 'Timeline: Followers'})[0].find_all('div')[0]
                    # Each follower is in a div with the data-testid attribute set to 'cellInnerDiv'
                    follower_nodes = follower_list.find_all('div', attrs={'data-testid': 'cellInnerDiv'})
                    no_nodes_found = len(follower_nodes)
                    current_node_count = 0
                    for follower_node in follower_nodes:
                        user_id, username, screen_name, description, follow_state, avatar_url, local_url = self.__extract_user_data_from_html(follower_node, current_node_count, os.path.join(self.config.output_assets_images_folder, 'followers'), self.__users)
                        
                        if user_id:
                            if username:
                                self.__users[user_id].username = username
                                self.__users[user_id].url =self.config.user_id_URL_template.format(username)
                            if screen_name:
                                self.__users[user_id].screen_name = screen_name
                            if description:
                                self.__users[user_id].description = description
                            if avatar_url:
                                self.__users[user_id].avatar_url = avatar_url
                            if local_url:
                                self.__users[user_id].local_url = local_url
                            if follow_state:
                                if follow_state == 'Following':
                                    self.__users[user_id].following = True
                                    
                        current_node_count += 1
                        
                        self.__process_window.update_progress(int((current_node_count / no_nodes_found)*100))
                        self.__process_window.status(f'Analysing node {current_node_count} of {no_nodes_found}.')
        self.__next_step()

    # Step 9: Go through the pre-saved following page if the user has supplied one
    #
    # See notes above about parsing the followers page.
    def __parse_following_page(self):
        if self.config.following_page:
            if os.path.exists(self.config.following_page):
                self.__process_window.top_status('Analysing following page...')
                self.__process_window.status('Reading following page...')
                self.__process_window.update_progress(0)
                with open(self.config.following_page, 'r', encoding='utf8') as followings_page_file:
                    html_parser = BeautifulSoup(followings_page_file, 'html.parser')
                    page_title = html_parser.title.string
                    print('Page title:', page_title)
                    # The following list is in a div with the aria-label attribute set to 'Timeline: Following'. Within *that* is another div that contains the followings list.
                    following_list = html_parser.find_all('div', attrs={'aria-label': 'Timeline: Following'})[0].find_all('div')[0]
                    # Each following is in a div with the data-testid attribute set to 'cellInnerDiv'
                    following_nodes = following_list.find_all('div', attrs={'data-testid': 'cellInnerDiv'})
                    no_nodes_found = len(following_nodes)
                    current_node_count = 0
                    for following_node in following_nodes:
                        user_id, username, screen_name, description, follow_state, avatar_url, local_url = self.__extract_user_data_from_html(following_node, current_node_count, os.path.join(self.config.output_assets_images_folder, 'following'), self.__users)
                        
                        if user_id:
                            if username:
                                self.__users[user_id].username = username
                                self.__users[user_id].url =self.config.user_id_URL_template.format(username)
                            if screen_name:
                                self.__users[user_id].screen_name = screen_name
                            if description:
                                self.__users[user_id].description = description
                            if avatar_url:
                                self.__users[user_id].avatar_url = avatar_url
                            if local_url:
                                self.__users[user_id].local_url = local_url
                                    
                        current_node_count += 1
                        
                        self.__process_window.update_progress(int((current_node_count / no_nodes_found)*100))
                        self.__process_window.status(f'Analysing nodes {current_node_count} of {no_nodes_found}.')
        self.__next_step()
        
    # Step 10: Save the user avatars
    def __save_users_avatars(self):
        self.__process_window.top_status('Saving user avatars...')
        self.__process_window.update_progress(0)
        sleep_time= self.config.sleep_time
        avatar_count = 0
        current_user = 0
        user_count = len(self.__users)
        output_dir = os.path.join(self.config.output_assets_images_folder, 'users')
        for user_id in self.__users:
            current_user += 1
            if self.__users[user_id].avatar_url:
                avatar_url = self.__users[user_id].avatar_url
                image_data = None
                file_ext = None
  
                # If you've been a good person and saved the webpage using a web page saver that saves
                # the images as data URLs, then we already have the image, and all we need to do is save it.
                #print('avatar_url:', avatar_url)
                if avatar_url:
                    if avatar_url.startswith('data:image'):
                        image_data_url =  data_url.DataURL.from_url(avatar_url)
                        image_data = image_data_url.data
                        if avatar_url.startswith('data:image/png'):
                            file_ext = 'png'
                        elif avatar_url.startswith('data:image/jpeg'):
                            file_ext = 'jpg'
                        elif avatar_url.startswith('data:image/gif'):
                            file_ext = 'gif'
                        avatar_url = None
                    # If you've been a bad person and saved the webpage using a web page saver that saves
                    # the image URLs, then we need to download the image.
                    elif avatar_url.startswith('https://') or avatar_url.startswith('http://'):
                        with UriLoader(avatar_url, self.config) as avatar_loader:
                            if avatar_loader.success:
                                image_data = avatar_loader.data.content
                                file_ext = avatar_loader.guess_ext()
                            time.sleep(sleep_time)
                    else:
                        avatar_url = None       # Generic avatar
                if image_data:
                    avatar_count += 1
                    output_filename = os.path.join(output_dir, f'avatar-{user_id}.{file_ext}')
                    with open(output_filename, 'wb') as f:
                        f.write(image_data)
                    self.__users[user_id].avatar_url = avatar_url
                    self.__users[user_id].local_url = f'assets/images/users/avatar-{user_id}.{file_ext}'
                    #time.sleep(sleep_time)
                    self.__process_window.top_status(f'Saving user avatars... ({avatar_count} found)')
            self.__process_window.update_progress(int((current_user / user_count)*100))
            self.__process_window.status(f'Scanning {current_user} of {user_count} user.')
        self.__next_step()

    # Step 11: Now we have all the information we can possibly get for the followers and following data,
    # we save it to a JSON file (for the search) and a YAML file. (For Jekyll.)
    def __save_followers_following(self):
        followers_following = self.__users  
        # First the JSON file
        users_output_json_filename = os.path.join(self.config.output_json_folder_name, 'users.js')
        users_data = []
        for user_id in followers_following:
            if followers_following[user_id].username:     # Only save users with usernames and screen names
                users_data.append(followers_following[user_id].as_dict())
        users_output_json = json.dumps(users_data, indent=4)
        with open(users_output_json_filename, 'w', encoding='utf8') as followers_output_json_file:
            followers_output_json_file.write('var users = '+ (users_output_json + ';'))
        # Now the YAML file
        output_yaml = ''
        for user_id in followers_following:
            if followers_following[user_id].follower:
                output_yaml += followers_following[user_id].as_yaml()
        with open(self.config.output_users_filename, 'w', encoding='utf8') as users_output_yaml_file:
            users_output_yaml_file.write(output_yaml)

    # Step 12: Analyse for retweets.
    #
    # It's quite interesting to see that the tweets JSON in the Twitter archive saves the retweet/quote tweet
    # info in the full text of the tweet, in a manner just like the olden days of retweets and quote tweets!
    # I guess this is for compatibility with the original retweet/quote tweets. Annoyingly, this means the 
    # retweeted text is potentially truncated. (Does this mean every time a retweet or quote tweet is displayed, 
    # there's a database call to retrieve that tweet?) 
    # 
    # So all retweets start with 'RT @' and quote tweets have a 'RT @' somewhere in the tweet. Interestingly, 
    # I couldn't find any examples of 'QT @' in the tweets, which was sometimes used for quote tweets, so I 
    # guess they've been converted to 'RT @' in the archive, but I've included the old-school quote tweet 
    # 'QT @' in the search, just in case.
    def __analyse_retweets(self):
        self.__process_window.top_status('Analysing for retweets...')
        self.__process_window.update_progress(0)
        tweet_count = len(self.__tweets)
        current_tweet_count = 0
        no_of_retweets = 0
        for tweet_id in self.__tweets:
            tweet = self.__tweets[tweet_id]
            # Case 1: simple retweet
            if tweet.full_text.startswith('RT @'):
                tweet.is_retweet = True
            # Case 2: quote tweet
            quote_tweet_search = re.search(r'.*\WRT\W\@', tweet.full_text)
            if quote_tweet_search:
                if not tweet.is_retweet:            # Make sure it's not a retweet of a retweet!
                    tweet.is_quote_tweet = True
            # Case 3: old-school quote tweet.
            quote_tweet_search = re.search(r'QT\W\@', tweet.full_text)
            if quote_tweet_search:
                tweet.is_quote_tweet = True
            if tweet.is_retweet or tweet.is_quote_tweet:
                no_of_retweets += 1
            current_tweet_count += 1
            self.__process_window.update_progress(int((current_tweet_count / tweet_count)*100))
            self.__process_window.status(f'Analysing tweet {current_tweet_count} of {tweet_count}.')
            self.__process_window.top_status('Analysing for retweets... (Found ' + str(no_of_retweets) + ')')
        self.__next_step()
            
    # Step 13: Look for threads within the tweets
    def __analyse_threads(self):
        self.__process_window.top_status('Analysing for threads...')
        self.__process_window.update_progress(0)
        tweet_count = len(self.__tweets)
        threads = {}
        tweets_in_threads = []
        current_tweet_count = 0
        no_of_threads = 0
        for tweet_id in self.__tweets:
            tweet = self.__tweets[tweet_id]
            current_tweet_count += 1
            reply_id = tweet.in_reply_to_status_id
            if reply_id:                                    # Is it a reply
                if reply_id in self.__tweets:               # Is the tweet it's replying to in my tweets?
                    if reply_id not in tweets_in_threads:   # Make sure we haven't already processed this
                        no_of_threads += 1
                        self.__tweets[reply_id].in_thread = True
                        self.__tweets[tweet_id].thread_id = no_of_threads
                        thread_start_date = tweet.date
                        self.__thread_stats.add_date(thread_start_date)
                        threads[no_of_threads] = [ reply_id, tweet_id ]
                        tweets_in_threads.append(tweet_id)
                        tweets_in_threads.append(reply_id)
                        next_tweet = self.__tweets[reply_id]
                        next_reply_id = next_tweet.in_reply_to_status_id
                        while next_reply_id:
                            if next_reply_id in self.__tweets:
                                if next_reply_id not in tweets_in_threads:
                                    self.__tweets[next_reply_id].in_thread = True
                                    self.__tweets[tweet_id].thread_id = no_of_threads
                                    threads[no_of_threads].insert(0, next_reply_id)
                                    tweets_in_threads.append(next_reply_id)
                                    next_tweet = self.__tweets[next_reply_id]
                                    next_reply_id = next_tweet.in_reply_to_status_id
                                else:
                                    break
                            else:
                                break
                        if len(threads[no_of_threads]) > 1:     # If there's only one tweet in the thread, ignore. This can happen if it's a reply to another user.
                            self.__process_window.top_status('Analysing for threads... (Found ' + str(no_of_threads) + ')') 
                            output_filename = os.path.join(self.config.output_threads_folder_name, str(no_of_threads) + '.html')
                            with open(output_filename, 'w', encoding='utf8') as output_file:
                                output_file.write('---\n')
                                output_file.write('layout: thread\n')
                                output_file.write('id: ' + str(no_of_threads) + '\n')
                                output_file.write('start_date: ' + Utils.export_date(thread_start_date) + '\n')
                                output_file.write('tweets:\n')
                                for tweet_id in threads[no_of_threads]:
                                    self.__tweets[tweet_id].thread_id = no_of_threads
                                    self.__tweets[tweet_id].in_thread = True
                                    #print('Tweet ID:', tweet_id, 'thread_id:', self.__tweets[tweet_id].thread_id)
                                    output_file.write('  - ' + tweet_id + '\n')
                                output_file.write('---\n')

            self.__process_window.update_progress(int((current_tweet_count / tweet_count)*100))
            self.__process_window.status(f'Analysing tweet {current_tweet_count} of {tweet_count}.')
            
        self.__next_step()
        
    # Step 14: Consolidate any duplicate media files
    def __consolidate_media(self):
        no_of_duplicates = 0
        self.__process_window.top_status('Consolidating media...')
        self.__process_window.update_progress(0)
        media_count = len(self.__media)
        current_media_count = 0
        size_saved = 0
        for current_media_id in self.__media:
            current_media_count += 1
            self.__process_window.update_progress(int((current_media_count / media_count)*100))
            self.__process_window.status(f'Checking media item {current_media_count} of {media_count}.')
            current_media = self.__media[current_media_id]
            if current_media.downloaded:
                if current_media.file_size is None:
                    current_media.file_size = os.path.getsize(current_media.local_filename)
                    self.__media[current_media_id].file_size = current_media.file_size
                for other_media_id in self.__media:
                    is_duplicate = False
                    other_media = self.__media[other_media_id]
                    if other_media.downloaded:
                        if current_media_id != other_media_id:
                            if other_media.file_size is None:
                                other_media.file_size = os.path.getsize(other_media.local_filename)
                                self.__media[other_media_id].file_size = other_media.file_size
                            # First check if the media is the same size
                            if current_media.file_size == other_media.file_size:
                                # Check if it's the same filename.
                                if current_media.local_filename == other_media.local_filename:
                                    is_duplicate = True
                                    self.__media[other_media_id].is_duplicated = True
                                    self.__media[other_media_id].duplicate_of = current_media_id
                                else:
                                    # Now check if the media is the same file
                                    is_duplicate = cmp(current_media.local_filename, other_media.local_filename, shallow=False)
                                    if is_duplicate:
                                        self.__media[other_media_id].is_duplicated = True
                                        self.__media[other_media_id].duplicate_of = current_media_id
                                if is_duplicate:
                                    no_of_duplicates += 1
                                    size_saved += current_media.file_size
                                    self.__process_window.top_status('Consolidating media... (Found ' + str(no_of_duplicates) + ' duplicates, saved ' + str(size_saved) + ' bytes)')
        self.__next_step()
        
    # Step 15: Write the tweets to the output directory
    def __write_tweets(self):
        self.__process_window.top_status('Writing tweets...')
        self.__process_window.status('Writing tweet data...')
        tweets_output_json_filename = os.path.join(self.config.output_json_folder_name, 'tweets.js')
        tweets_data = []
        for tweet_id in self.__tweets:
            tweets_data.append(self.__tweets[tweet_id].as_dict())
        tweets_output_json = json.dumps(tweets_data, indent=4)
        with open(tweets_output_json_filename, 'w', encoding='utf8') as tweets_output_json_file:
            tweets_output_json_file.write('var tweets = '+ (tweets_output_json + ';'))
 
        self.__process_window.update_progress(0)
        tweet_count = len(self.__tweets)
        current_tweet_count = 0
        for tweet_id in self.__tweets:
            current_tweet_count += 1
            self.__process_window.update_progress(int((current_tweet_count / tweet_count)*100))
            self.__process_window.status(f'Writing tweet {current_tweet_count} of {tweet_count}.')
            self.__tweets[tweet_id].process(self.__media, self.__users, self.__hastags, self.config)
            if self.__tweets[tweet_id].filename:
                self.__tweets[tweet_id].write()
            self.__process_window.update_progress(int((current_tweet_count / tweet_count)*100))
            self.__process_window.status(f'Writing tweet {current_tweet_count} of {tweet_count}.')
        # Add tweet and thread stats to the data folder.
        with open(self.config.output_tweetstats_filename, 'w', encoding='utf8') as tweet_stats_file:
            tweet_stats_file.write(self.__tweet_stats.as_yaml())
        with open(self.config.output_threadstats_filename, 'w', encoding='utf8') as thread_stats_file:
            thread_stats_file.write(self.__thread_stats.as_yaml())
        # Add tweet and thread stats to the Javascript data folder.
        with open(os.path.join(self.config.output_json_folder_name, 'tweet_stats.js'), 'w', encoding='utf8') as tweet_stats_file:
            tweet_stats_file.write('var tweet_stats = ' + self.__tweet_stats.as_json() + ';')
        with open(os.path.join(self.config.output_json_folder_name, 'thread_stats.js'), 'w', encoding='utf8') as thread_stats_file:
            thread_stats_file.write('var thread_stats = ' + self.__thread_stats.as_json() + ';')
        self.__next_step()
        
    # Step 16: Clear up any duplicate media files
    def __clear_duplicates(self):
        self.__process_window.top_status('Clearing up files...')
        self.__process_window.update_progress(0)
        duplicate_files = 0
        for media_id in self.__media:
            if self.__media[media_id].is_duplicated:
                duplicate_files += 1
        if duplicate_files == 0:
            self.__process_window.update_progress(100)
            self.__next_step()
            return
        current_duplicate_file = 0
        for media_id in self.__media:
            if self.__media[media_id].is_duplicated:
                current_duplicate_file += 1
                self.__process_window.update_progress(int((current_duplicate_file / duplicate_files)*100))
                self.__process_window.status(f'Removing {current_duplicate_file} of {duplicate_files}.')
                if self.__media[media_id].local_filename:
                    os.remove(self.__media[media_id].local_filename)
        self.__next_step()
