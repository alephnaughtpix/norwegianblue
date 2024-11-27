import os
import json

class Config:
    
    def __init__(self, root_dir, source_dir = 'No directory selected', output_dir ='No directory selected'):
        self.data = {}
        self.input_folder = None
        self.output_folder = None
        self.followers_page = None
        self.following_page = None
        self.save_followers = False
        self.save_following = False
        self.root_dir = None
        self.output_media_folder_name = None
        self.output_hashtag_folder_name = None
        self.output_threads_folder_name = None
        self.output_json_folder_name = None
        self.output_media_url_base = None
        self.output_assets_folder = None
        self.output_assets_images_folder = None
        self.output_posts = None
        self.output_status = None
        self.output_thread = None
        self.tweet_icon_path = None
        self.output_html_filename = None
        self.data_folder = None
        self.account_js_filename = None
        self.log_path = None
        self.output_following_filename = None
        self.output_followers_filename = None
        self.output_users_filename = None
        self.output_tweetstats_filename = None
        self.output_threadstats_filename = None
        self.user_id_URL_template = None
        self.jekyll_config_filename = None
        self.user_agent = None
        self.sleep_time = None
        
        self.config_filename = 'config.json'
        if not self.load():     # if the config file doesn't exist, create it with the following defaults
            self.data['root_dir'] = root_dir
            self.update(source_dir, output_dir)
            
    def __update_constants(self):
        if 'input_folder' in self.data:
            self.input_folder = self.data['input_folder']
        if 'output_folder' in self.data:    
            self.output_folder = self.data['output_folder']
        if 'followers_page' in self.data:
            self.followers_page = self.data['followers_page']
        if 'following_page' in self.data:
            self.following_page = self.data['following_page']
        if 'save_followers' in self.data:
            self.save_followers = self.data['save_followers']
        if 'save_following' in self.data:
            self.save_following = self.data['save_following']
        if 'root_dir' in self.data:
            self.root_dir = self.data['root_dir']
        if 'output_media_folder_name' in self.data:
            self.output_media_folder_name = self.data['output_media_folder_name']
        if 'output_hashtag_folder_name' in self.data:
            self.output_hashtag_folder_name = self.data['output_hashtag_folder_name']
        if 'output_threads_folder_name' in self.data:
            self.output_threads_folder_name = self.data['output_threads_folder_name']
        if 'output_json_folder_name' in self.data:
            self.output_json_folder_name = self.data['output_json_folder_name']
        if 'output_media_url_base' in self.data:
            self.output_media_url_base = self.data['output_media_url_base']
        if 'output_assets_folder' in self.data:
            self.output_assets_folder = self.data['output_assets_folder']
        if 'output_assets_images_folder' in self.data:
            self.output_assets_images_folder = self.data['output_assets_images_folder']
        if 'output_posts' in self.data:
            self.output_posts = self.data['output_posts']
        if 'output_status' in self.data:
            self.output_status = self.data['output_status']
        if 'output_thread' in self.data:
            self.output_thread = self.data['output_thread']
        if 'tweet_icon_path' in self.data:
            self.tweet_icon_path = self.data['tweet_icon_path']
        if 'output_html_filename' in self.data:
            self.output_html_filename = self.data['output_html_filename']
        if 'data_folder' in self.data:
            self.data_folder = self.data['data_folder']
        if 'account_js_filename' in self.data:
            self.account_js_filename = self.data['account_js_filename']
        if 'log_path' in self.data:
            self.log_path = self.data['log_path']
        if 'output_following_filename' in self.data:
            self.output_following_filename = self.data['output_following_filename']
        if 'output_followers_filename' in self.data:
            self.output_followers_filename = self.data['output_followers_filename']
        if 'output_users_filename' in self.data:
            self.output_users_filename = self.data['output_users_filename']
        if 'output_tweetstats_filename' in self.data:
            self.output_tweetstats_filename = self.data['output_tweetstats_filename']
        if 'output_threadstats_filename' in self.data:
            self.output_threadstats_filename = self.data['output_threadstats_filename']
        if 'user_id_URL_template' in self.data:
            self.user_id_URL_template = self.data['user_id_URL_template']
        if 'jekyll_config_filename' in self.data:
            self.jekyll_config_filename = self.data['jekyll_config_filename']
        if 'user_agent' in self.data:
            self.user_agent = self.data['user_agent']
        if 'sleep_time' in self.data:
            self.sleep_time = self.data['sleep_time']
        if 'download_media' in self.data:
            self.download_media = self.data['download_media']
        
    def already_existing(self):
        return os.path.exists(self.output_media_folder_name) or os.path.exists(self.output_posts) or os.path.exists(self.output_status) or os.path.exists(self.output_thread)

    def load(self):
        if not os.path.exists(self.config_filename):
            return False
        try:
            with open(self.config_filename, 'r', encoding='utf8') as f:
                data = f.read()
                self.data.update(json.loads(data))
                self.__update_constants()
                return True
        except Exception as e:
            print(f"Error loading configuration file: {e}")
            return False
            
    def save(self):
        try:
            with open(self.config_filename, 'w', encoding='utf8') as f:
                f.write(json.dumps(self.data, indent=4))
            return True
        except Exception as e:
            print(f"Error saving configuration file: {e}")
            return False

    def update(self, 
               source_dir, output_dir, 
               followers_page = None, 
               following_page = None, 
               sleep_time = 0.25, 
               download_media = True):
        self.data['input_folder'] = source_dir
        self.data['output_folder'] = output_dir
        if 'save_followers' not in self.data:
            self.data['save_followers'] = False
        if 'save_following' not in self.data:
            self.data['save_following'] = False
        if followers_page:
            self.data['followers_page'] = followers_page
            self.data['save_followers'] = True
        else:
            self.data['followers_page'] = None
        if following_page:
            self.data['following_page'] = following_page
            self.data['save_following'] = True
        else:
            self.data['following_page'] = None
        self.data['output_media_folder_name'] = os.path.join(self.data['output_folder'],'media')
        self.data['output_hashtag_folder_name' ] = os.path.join(self.data['output_folder'],'_hashtags')
        self.data['output_json_folder_name' ] = os.path.join(self.data['output_folder'],'assets/js/data')
        self.data['output_threads_folder_name'] = os.path.join(self.data['output_folder'], '_threads')
        self.data['output_media_url_base'] = '/media/'
        self.data['output_assets_folder'] = os.path.join(self.data['output_folder'], 'assets')
        self.data['output_assets_images_folder'] = os.path.join(self.data['output_assets_folder'], 'images')
        self.data['output_posts'] = os.path.join(self.data['output_folder'], 'archive')
        self.data['output_status'] = os.path.join(self.data['output_folder'], '_status')
        self.data['output_thread'] = os.path.join(self.data['output_folder'], '_thread')
        self.data['tweet_icon_path'] = f'{self.data["output_media_folder_name"]}/tweet.ico'
        self.data['output_html_filename'] = 'TweetArchive.html'
        self.data['data_folder'] = os.path.join(self.data['input_folder'], 'data')
        self.data['account_js_filename'] = os.path.join(self.data['data_folder'], 'account.js')
        self.data['log_path'] = os.path.join(self.data['output_media_folder_name'], 'download_log.txt')
        self.data['output_following_filename'] = os.path.join(self.data['output_folder'], '_data/following.yaml')
        self.data['output_followers_filename'] = os.path.join(self.data['output_folder'], '_data/followers.yaml')
        self.data['output_users_filename'] = os.path.join(self.data['output_folder'], '_data/users.yaml')
        self.data['output_tweetstats_filename'] = os.path.join(self.data['output_folder'], '_data/tweet_stats.yaml')
        self.data['output_threadstats_filename'] = os.path.join(self.data['output_folder'], '_data/thread_stats.yaml')
        self.data['user_id_URL_template'] = 'https://twitter.com/{}'
        self.data['jekyll_config_filename'] = os.path.join(self.data['output_folder'], '_config.yml')
        self.data['user_agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
        if 'sleep_time' not in self.data:
            self.data['sleep_time'] = 0.25
        else:
            self.data['sleep_time'] = sleep_time
        if 'download_media' not in self.data:
            self.data['download_media'] = True
        else:
            self.data['download_media'] = download_media
        self.__update_constants()
        self.save()
        
