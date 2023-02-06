#!/usr/bin/env python3
"""
    twitter-archive-parser - Python code to parse a Twitter archive and output in various ways
    Copyright (C) 2022  Tim Hutton

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
    
    ADDITIONAL MODIFICATIONS FOR NORWEGIAN BLUE BY M.P. James 21 Nov 2022.
"""

from collections import defaultdict
from collections import OrderedDict
import datetime
import glob
import importlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
# hot-loaded if needed, see import_module():
#  imagesize
#  requests


# Print a compile-time error in Python < 3.6. This line does nothing in Python 3.6+ but is reported to the user
# as an error (because it is the first line that fails to compile) in older versions.
f' Error: This script requires Python 3.6 or later.'

SESSION_BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'

class UserData:
    def __init__(self, id, handle = None, name = None, description = None, url = None, avatar = None):
        self.id = id
        self.handle = handle
        self.name = name
        self.description = description
        self.url = url
        self.avatar = avatar
 
def yes_no_input(prompt):
    """Prompts the user for a yes/no answer and returns True or False."""
    user_input = input(prompt + ' [y/n]')
    return user_input.lower() in ('y', 'yes')

def create_or_enter_output_directory(output_directory):
    """Creates the output directory if it doesn't exist, otherwise enters it."""
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    #os.chdir(output_directory)

def download_media(image_url, output_directory, skip_existing=False):
    requests = import_module('requests')
    sleep_time=0.25
    image_filename = image_url.split('/')[-1]
    output_filename = f'{output_directory}/{image_filename}'
    if os.path.exists(output_filename) and skip_existing:
        print(f'Image already downloaded to {output_filename}')
        return image_filename
    try:
        time.sleep(sleep_time)
        print('Attempting to download image at: ', image_url)
        with requests.get(image_url, stream=True) as res:
            if not res.status_code == 200:
                # Try to get content of response as `res.text`. For twitter.com, this will be empty in most (all?) cases.
                # It is successfully tested with error responses from other domains.
                raise Exception(f'Download failed with status "{res.status_code} {res.reason}". Response content: "{res.text}"')
            else:
                print(f'Downloading image from {image_url}', end='\r')
                with open(f'{output_directory}/{image_filename}','wb') as f:
                    shutil.copyfileobj(res.raw, f)
    except Exception as err:
        logging.error(f"FAIL. Media couldn't be retrieved from {image_url} because of exception: {err}")
        image_filename = None
    if image_filename:
        print(f'Downloaded image from {image_url} to {image_filename}')
        return image_filename
    else:
        return None


def import_module(module):
    """Imports a module specified by a string. Example: requests = import_module('requests')"""
    try:
        return importlib.import_module(module)
    except ImportError:
        print(f'\nError: This script uses the "{module}" module which is not installed.\n')
        if not yes_no_input('OK to install using pip?'):
            exit()
        subprocess.run([sys.executable, '-m', 'pip', 'install', module], check=True)
        return importlib.import_module(module)


def get_twitter_api_guest_token(session, bearer_token):
    """Returns a Twitter API guest token for the current session."""
    guest_token_response = session.post("https://api.twitter.com/1.1/guest/activate.json",
                                        headers={'authorization': f'Bearer {bearer_token}'})
    guest_token = json.loads(guest_token_response.content)['guest_token']
    if not guest_token:
        raise Exception(f"Failed to retrieve guest token")
    return guest_token


def get_twitter_users(session, bearer_token, guest_token, user_ids):
    """Asks Twitter for all metadata associated with user_ids."""
    users = {}
    while user_ids:
        max_batch = 100
        user_id_batch = user_ids[:max_batch]
        user_ids = user_ids[max_batch:]
        user_id_list = ",".join(user_id_batch)
        query_url = f"https://api.twitter.com/1.1/users/lookup.json?user_id={user_id_list}"
        response = session.get(query_url,
                               headers={'authorization': f'Bearer {bearer_token}', 'x-guest-token': guest_token})
        if not response.status_code == 200:
            raise Exception(f'Failed to get user handle: {response}')
        response_json = json.loads(response.content)
        with open('output.json','w') as output_json:
            output_json.write(response.text)
        for user in response_json:
            users[user["id_str"]] = user
    return users


def get_users_from_cached_request(input_file):
    """Returns a list of users from a cached request."""
    users = {}
    if input_file:
        with open(input_file, 'r') as cached_file:
            response_json = json.load(cached_file)
            for user in response_json:
                users[user["id_str"]] = user
    return users

def lookup_users(user_ids, user_id_url_template, users, download_images=False, input_file=None):
    """Fill the users dictionary with data from Twitter"""
    # Filter out any users already known, or we need to download images for
    if download_images:
        filtered_user_ids = []
        for id in user_ids:
            if id not in users:
                filtered_user_ids.append(id)
            elif users[id].avatar is None:
                filtered_user_ids.append(id)
    else:
        filtered_user_ids = [id for id in user_ids if id not in users]
    if not filtered_user_ids:
        # Don't bother opening a session if there's nothing to get
        return
    # Account metadata observed at ~2.1KB on average.
    use_input_file = False
    if input_file and os.path.exists(input_file):
        use_input_file = yes_no_input(f'We found a previously cached request in "{input_file}" do you want to use that?')
    if use_input_file:
        retrieved_users = get_users_from_cached_request(input_file)
        for user_id, user in retrieved_users.items():
            url = user_id_url_template.format(user_id)
            if "profile_image_url_https" in user:
                profile_image_url = user["profile_image_url_https"] 
            elif "profile_image_url" in user:
                profile_image_url = user["profile_image_url"]
            else:
                profile_image_url = None
            users[user_id] = UserData(
                user_id, 
                user["screen_name"], 
                user["name"], 
                user["description"],
                url,
                profile_image_url
            )
    else:
        estimated_size = int(2.1 * len(filtered_user_ids))
        print(f'{len(filtered_user_ids)} users are unknown.')
        if not yes_no_input(f'Download user data from Twitter (approx {estimated_size:,}KB)?'):
            return
        requests = import_module('requests')
        try:
            with requests.Session() as session:
                guest_token = get_twitter_api_guest_token(session, SESSION_BEARER_TOKEN)
                retrieved_users = get_twitter_users(session, SESSION_BEARER_TOKEN, guest_token, filtered_user_ids)
                for user_id, user in retrieved_users.items():
                    url = user_id_url_template.format(user_id)
                    if "profile_image_url_https" in user:
                        profile_image_url = user["profile_image_url_https"] 
                    elif "profile_image_url" in user:
                        profile_image_url = user["profile_image_url"]
                    else:
                        profile_image_url = None
                    users[user_id] = UserData(
                        user_id, 
                        user["screen_name"], 
                        user["name"], 
                        user["description"],
                        url,
                        profile_image_url
                    )
        except Exception as err:
            print(f'Failed to download user data: {err}')
    print(f'Found {len(users)} users')

def read_json_from_js_file(filename):
    """Reads the contents of a Twitter-produced .js file into a dictionary."""
    print(f'Parsing {filename}...')
    with open(filename, 'r', encoding='utf8') as f:
        data = f.readlines()
        # if the JSON has no real content, it can happen that the file is only one line long.
        # in this case, return an empty dict to avoid errors while trying to read non-existing lines.
        if len(data) <= 1:
            return {}
        # convert js file to JSON: replace first line with just '[', squash lines into a single string
        prefix = '['
        if '{' in data[0]:
            prefix += ' {'
        data =  prefix + ''.join(data[1:])
        # parse the resulting JSON and return as a dict
        return json.loads(data)


def extract_username(account_js_filename):
    """Returns the user's Twitter username from account.js."""
    account = read_json_from_js_file(account_js_filename)
    return account[0]['account']['username']




def convert_tweet(tweet, username, archive_media_folder, output_media_folder_name, output_media_url_base,
                  tweet_icon_path, media_sources, users, download_missing_media = False):
    """Converts a JSON-format tweet. Returns tuple of timestamp, HTML, and tweet ID."""
    if 'tweet' in tweet.keys():
        tweet = tweet['tweet']
    timestamp_str = tweet['created_at']
    timestamp_date = datetime.datetime.strptime(timestamp_str, '%a %b %d %X %z %Y')
    output_timestamp = timestamp_date.strftime('%Y-%m-%d %H:%M:%S')
    timestamp = int(round(timestamp_date.timestamp())) # Example: Tue Mar 19 14:05:17 +0000 2019
    body_html = tweet['full_text']
    tweet_id_str = tweet['id_str']
    front_matter = f'''---
id: {tweet_id_str}
created: {output_timestamp}
year: {timestamp_date.year}
month: {timestamp_date.month}
day: {timestamp_date.day}
'''
    # replace t.co URLs with their original versions
    if 'entities' in tweet and 'urls' in tweet['entities']:
        for url in tweet['entities']['urls']:
            if 'url' in url and 'expanded_url' in url:
                expanded_url = url['expanded_url']
                expanded_url_html = f'<a href="{expanded_url}">{expanded_url}</a>'
                body_html = body_html.replace(url['url'], expanded_url_html)

    # if the tweet is a reply, construct a header that links the names of the accounts being replied to the tweet being replied to
    header_html = ''
    if 'in_reply_to_status_id' in tweet:
        reply_to_id = None
        is_in_thread = False
        # match and remove all occurences of '@username ' at the start of the body
        replying_to = re.match(r'^(@[0-9A-Za-z_]* )*', body_html)[0]
        if replying_to:
            body_html = body_html[len(replying_to):]
        else:
            # no '@username ' in the body: we're replying to self
            replying_to = f'@{username}'
            reply_to_id = tweet['in_reply_to_status_id']
            is_in_thread = True
        names = replying_to.split()
        # some old tweets lack 'in_reply_to_screen_name': use it if present, otherwise fall back to names[0]
        in_reply_to_screen_name = tweet['in_reply_to_screen_name'] if 'in_reply_to_screen_name' in tweet else names[0]
        # create a list of names of the form '@name1, @name2 and @name3' - or just '@name1' if there is only one name
        name_list = ', '.join(names[:-1]) + (f' and {names[-1]}' if len(names) > 1 else names[0])
        safe_name_list = name_list.replace('@', '')
        in_reply_to_status_id = tweet['in_reply_to_status_id']
        replying_to_url = f'https://twitter.com/{in_reply_to_screen_name}/status/{in_reply_to_status_id}'
        front_matter += f'reply_to_url: {replying_to_url}' + '\n'
        front_matter += f'reply_to_names: {safe_name_list}' + '\n'
        if is_in_thread:
            front_matter += f'is_in_thread: {is_in_thread}' + '\n'
        if reply_to_id:
            front_matter += f'reply_to_id: {reply_to_id}' + '\n'
        header_html += f'Replying to <a href="{replying_to_url}">{name_list}</a><br>'
    # replace image URLs with image links to local files
    if 'entities' in tweet and 'media' in tweet['entities'] and 'extended_entities' in tweet and 'media' in tweet['extended_entities']:
        original_url = tweet['entities']['media'][0]['url']
        html = ''
        for media in tweet['extended_entities']['media']:
            if 'url' in media and 'media_url' in media:
                original_expanded_url = media['media_url']
                original_filename = os.path.split(original_expanded_url)[1]
                archive_media_filename = tweet_id_str + '-' + original_filename
                archive_media_path = os.path.join(archive_media_folder, archive_media_filename)
                new_location = output_media_folder_name + archive_media_filename
                new_url = output_media_url_base + archive_media_filename
                html += '' if not html and body_html == original_url else '<br>'
                if os.path.isfile(archive_media_path):
                    # Found a matching image, use this one
                    if not os.path.isfile(new_url):
                        shutil.copy(archive_media_path, new_location)
                    html += '<img src="{{ "' + f'{new_url}' + '" | relative_url }}"/>'
                    # Save the online location of the best-quality version of this file, for later upgrading if wanted
                    best_quality_url = f'https://pbs.twimg.com/media/{original_filename}:orig'
                    media_sources.append((os.path.join(output_media_folder_name, archive_media_filename), best_quality_url))
                else:
                    # Is there any other file that includes the tweet_id in its filename?
                    archive_media_paths = glob.glob(os.path.join(archive_media_folder, tweet_id_str + '*'))
                    if len(archive_media_paths) > 0:
                        for archive_media_path in archive_media_paths:
                            archive_media_filename = os.path.split(archive_media_path)[-1]
                            media_location = f'{output_media_folder_name}{archive_media_filename}'
                            if not os.path.isfile(media_location):
                                shutil.copy(archive_media_path, media_location)
                            media_url = f'{output_media_url_base}{archive_media_filename}'
                            html += '<video controls><source src="{{ "' + f'{media_url}' + '" | relative_url }}">Your browser does not support the video tag.</video>\n'
                            # Save the online location of the best-quality version of this file, for later upgrading if wanted
                            if 'video_info' in media and 'variants' in media['video_info']:
                                best_quality_url = ''
                                best_bitrate = -1 # some valid videos are marked with bitrate=0 in the JSON
                                for variant in media['video_info']['variants']:
                                    if 'bitrate' in variant:
                                        bitrate = int(variant['bitrate'])
                                        if bitrate > best_bitrate:
                                            best_quality_url = variant['url']
                                            best_bitrate = bitrate
                                if best_bitrate == -1:
                                    print(f"Warning No URL found for {original_url} {original_expanded_url} {archive_media_path} {media_url}")
                                    print(f"JSON: {tweet}")
                                else:
                                    media_sources.append((os.path.join(output_media_folder_name, archive_media_filename), best_quality_url))
                    else:
                        if download_missing_media:
                            # Download the image from the original URL and save it to the archive
                            print(f'Downloading missing media from {original_url}')
                            downloaded_filename = download_media(original_url, archive_media_path, True)
                            if downloaded_filename:
                                archive_media_filename = os.path.split(archive_media_path)[-1]
                                media_url = f'{output_media_url_base}{archive_media_filename}'
                                html += f'<a href="{media_url}">{media_url}</a>'
                                print(f'Tweet ID is: {tweet_id_str}')
                            else:
                                print(f'Warning: failed to download missing media from {original_url}. Using original link instead: {original_url} (expands to {original_expanded_url})')
                                html += f'<a href="{original_url}">{original_url}</a>'
                        else:
                            print(f'Warning: missing local file: {archive_media_path}. Using original link instead: {original_url} (expands to {original_expanded_url})')
                            html += f'<a href="{original_url}">{original_url}</a>'
        body_html = body_html.replace(original_url, html)
    # make the body a quote
    body_html = '<p>' + '<br>\n'.join(body_html.splitlines()) 
    # append the original Twitter URL as a link
    original_tweet_url = f'https://twitter.com/{username}/status/{tweet_id_str}'
    front_matter += f'original_url: {original_tweet_url}' + '\n'
    body_html = body_html + '</p>'
    # extract user_id:handle connections
    if 'in_reply_to_user_id' in tweet and 'in_reply_to_screen_name' in tweet:
        id = tweet['in_reply_to_user_id']
        if int(id) >= 0: # some ids are -1, not sure why
            handle = tweet['in_reply_to_screen_name']
            users[id] = UserData(id=id, handle=handle)
    if 'entities' in tweet and 'user_mentions' in tweet['entities']:
        for mention in tweet['entities']['user_mentions']:
            id = mention['id']
            if int(id) >= 0: # some ids are -1, not sure why
                handle = mention['screen_name']
                users[id] = UserData(id=id, handle=handle)
				
    body_html = front_matter + '---\n' + body_html

    return timestamp, body_html, tweet_id_str


def find_input_filenames(data_folder):
    """Identify the tweet archive's file and folder names - they change slightly depending on the archive size it seems."""
    tweet_js_filename_templates = ['tweet.js', 'tweets.js', 'tweets-part*.js']
    input_filenames = []
    for tweet_js_filename_template in tweet_js_filename_templates:
        input_filenames += glob.glob(os.path.join(data_folder, tweet_js_filename_template))
    if len(input_filenames)==0:
        print(f'Error: no files matching {tweet_js_filename_templates} in {data_folder}')
        exit()
    tweet_media_folder_name_templates = ['tweet_media', 'tweets_media']
    tweet_media_folder_names = []
    for tweet_media_folder_name_template in tweet_media_folder_name_templates:
        tweet_media_folder_names += glob.glob(os.path.join(data_folder, tweet_media_folder_name_template))
    if len(tweet_media_folder_names) == 0:
        print(f'Error: no folders matching {tweet_media_folder_name_templates} in {data_folder}')
        exit()
    if len(tweet_media_folder_names) > 1:
        print(f'Error: multiple folders matching {tweet_media_folder_name_templates} in {data_folder}')
        exit()
    archive_media_folder = tweet_media_folder_names[0]
    return input_filenames, archive_media_folder


def download_file_if_larger(url, filename, index, count, sleep_time):
    """Attempts to download from the specified URL. Overwrites file if larger.
       Returns whether the file is now known to be the largest available, and the number of bytes downloaded.
    """
    requests = import_module('requests')
    imagesize = import_module('imagesize')

    pref = f'{index:3d}/{count:3d} {filename}: '
    # Sleep briefly, in an attempt to minimize the possibility of trigging some auto-cutoff mechanism
    if index > 1:
        print(f'{pref}Sleeping...', end='\r')
        time.sleep(sleep_time)
    # Request the URL (in stream mode so that we can conditionally abort depending on the headers)
    print(f'{pref}Requesting headers for {url}...', end='\r')
    byte_size_before = os.path.getsize(filename)
    try:
        with requests.get(url, stream=True) as res:
            if not res.status_code == 200:
                # Try to get content of response as `res.text`. For twitter.com, this will be empty in most (all?) cases.
                # It is successfully tested with error responses from other domains.
                raise Exception(f'Download failed with status "{res.status_code} {res.reason}". Response content: "{res.text}"')
            byte_size_after = int(res.headers['content-length'])
            if (byte_size_after != byte_size_before):
                # Proceed with the full download
                tmp_filename = filename+'.tmp'
                print(f'{pref}Downloading {url}...            ', end='\r')
                with open(tmp_filename,'wb') as f:
                    shutil.copyfileobj(res.raw, f)
                post = f'{byte_size_after/2**20:.1f}MB downloaded'
                width_before, height_before = imagesize.get(filename)
                width_after, height_after = imagesize.get(tmp_filename)
                pixels_before, pixels_after = width_before * height_before, width_after * height_after
                pixels_percentage_increase = 100.0 * (pixels_after - pixels_before) / pixels_before

                if (width_before == -1 and height_before == -1 and width_after == -1 and height_after == -1):
                    # could not check size of both versions, probably a video or unsupported image format
                    os.replace(tmp_filename, filename)
                    bytes_percentage_increase = 100.0 * (byte_size_after - byte_size_before) / byte_size_before
                    logging.info(f'{pref}SUCCESS. New version is {bytes_percentage_increase:3.0f}% '
                                 f'larger in bytes (pixel comparison not possible). {post}')
                    return True, byte_size_after
                elif (width_before == -1 or height_before == -1 or width_after == -1 or height_after == -1):
                    # could not check size of one version, this should not happen (corrupted download?)
                    logging.info(f'{pref}SKIPPED. Pixel size comparison inconclusive: '
                                 f'{width_before}*{height_before}px vs. {width_after}*{height_after}px. {post}')
                    return False, byte_size_after
                elif (pixels_after >= pixels_before):
                    os.replace(tmp_filename, filename)
                    bytes_percentage_increase = 100.0 * (byte_size_after - byte_size_before) / byte_size_before
                    if (bytes_percentage_increase >= 0):
                        logging.info(f'{pref}SUCCESS. New version is {bytes_percentage_increase:3.0f}% larger in bytes '
                                    f'and {pixels_percentage_increase:3.0f}% larger in pixels. {post}')
                    else:
                        logging.info(f'{pref}SUCCESS. New version is actually {-bytes_percentage_increase:3.0f}% smaller in bytes '
                                f'but {pixels_percentage_increase:3.0f}% larger in pixels. {post}')
                    return True, byte_size_after
                else:
                    logging.info(f'{pref}SKIPPED. Online version has {-pixels_percentage_increase:3.0f}% smaller pixel size. {post}')
                    return True, byte_size_after
            else:
                logging.info(f'{pref}SKIPPED. Online version is same byte size, assuming same content. Not downloaded.')
                return True, 0
    except Exception as err:
        logging.error(f"{pref}FAIL. Media couldn't be retrieved from {url} because of exception: {err}")
        return False, 0


def download_larger_media(media_sources, log_path):
    """Uses (filename, URL) tuples in media_sources to download files from remote storage.
       Aborts downloads if the remote file is the same size or smaller than the existing local version.
       Retries the failed downloads several times, with increasing pauses between each to avoid being blocked.
    """
    # Log to file as well as the console
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(message)s')
    logfile_handler = logging.FileHandler(filename=log_path, mode='w')
    logfile_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(logfile_handler)
    # Download new versions
    start_time = time.time()
    total_bytes_downloaded = 0
    sleep_time = 0.25
    remaining_tries = 5
    while remaining_tries > 0:
        number_of_files = len(media_sources)
        success_count = 0
        retries = []
        for index, (local_media_path, media_url) in enumerate(media_sources):
            success, bytes_downloaded = download_file_if_larger(media_url, local_media_path, index + 1, number_of_files, sleep_time)
            if success:
                success_count += 1
            else:
                retries.append((local_media_path, media_url))
            total_bytes_downloaded += bytes_downloaded
        media_sources = retries
        remaining_tries -= 1
        sleep_time += 2
        logging.info(f'\n{success_count} of {number_of_files} tested media files are known to be the best-quality available.\n')
        if len(retries) == 0:
            break
        if remaining_tries > 0:
            print(f'----------------------\n\nRetrying the ones that failed, with a longer sleep. {remaining_tries} tries remaining.\n')
    end_time = time.time()

    logging.info(f'Total downloaded: {total_bytes_downloaded/2**20:.1f}MB = {total_bytes_downloaded/2**30:.2f}GB')
    logging.info(f'Time taken: {end_time-start_time:.0f}s')
    print(f'Wrote log to {log_path}')

'''
Parsing the user profile information. This does three things:
1. Appends user profile information to the _config.yml to so it can be used in the site.
2. Translates the website link from the t.co link to the original link.
3. Downloads the avatar and header images (if they exist).
'''
def parse_profile(input_folder, users, user_id_url_template):
    print('\n== PARSING PROFILE INFORMATION =================================\n')
    download_avatar = yes_no_input('Do you wish to download your avatar and banner images?')
    requests = import_module('requests')
    sleep_time=0.25

    profile_data = read_json_from_js_file(os.path.join(input_folder, 'data/profile.js'))[0]['profile']
    bio = profile_data['description']['bio']
    website_tco = profile_data['description']['website']
    location = profile_data['description']['location']
    avatar_url = profile_data['avatarMediaUrl']
    header_url = profile_data['headerMediaUrl']
    if avatar_url:
        avatar_url_ext = os.path.splitext(avatar_url)[1]
    # Append info to Jekyll config
    with open(f'../_config.yml','a') as profile_config:
        if bio:
            profile_config.write('\n' + f'bio: {bio}')
        if location:
            profile_config.write('\n' + f'location: {location}')
        if website_tco:
            # Get original link for t.co link
            try:
                print('getting URL of website from profile.')
                with requests.get(website_tco, stream=True) as res:
                    print('res.status_code', res.status_code)
                    website = res.url
                    profile_config.write('\n' + f'website: {website}')
            except Exception as err:
                logging.error(f"FAIL. Original URL of {website_tco} because of exception: {err}")
        print(f'Sleeping...', end='\r')
        time.sleep(sleep_time)

        if download_avatar:
            # Get avatar image. This has a file extension at the end, so we can use that whilst saving.
            if avatar_url:
                try:
                    print('Attempting to download avatar image at: ', avatar_url)
                    with requests.get(avatar_url, stream=True) as res:
                        if not res.status_code == 200:
                            # Try to get content of response as `res.text`. For twitter.com, this will be empty in most (all?) cases.
                            # It is successfully tested with error responses from other domains.
                            raise Exception(f'Download failed with status "{res.status_code} {res.reason}". Response content: "{res.text}"')
                        else:
                            print('Downloading profile avatar...            ', end='\r')
                            with open(f'../assets/images/avatar{avatar_url_ext}','wb') as f:
                                shutil.copyfileobj(res.raw, f)
                                profile_config.write('\n' + f'avatar: /assets/images/avatar{avatar_url_ext}')
                except Exception as err:
                    logging.error(f"FAIL. Media couldn't be retrieved from {avatar_url} because of exception: {err}")
            print(f'Sleeping...', end='\r')
            time.sleep(sleep_time)
            # Get header image. There is *no* file extension here, so we have to infer it from the content-type.
            if header_url:
                try:
                    print('Attempting to download header banner image at: ', header_url)
                    with requests.get(header_url, stream=True) as res:
                        if not res.status_code == 200:
                            # Try to get content of response as `res.text`. For twitter.com, this will be empty in most (all?) cases.
                            # It is successfully tested with error responses from other domains.
                            raise Exception(f'Download failed with status "{res.status_code} {res.reason}". Response content: "{res.text}"')
                        else:
                            content_type = response.headers['Content-Type']
                            if content_type == 'image/gif':
                                header_ext = '.gif'
                            elif content_type == 'image/png':
                                header_ext = '.png'
                            elif content_type == 'image/svg-xml':
                                header_ext = '.svg'
                            else:
                                header_ext = '.jpg' 
                            print(f'Saving as {header_ext} file.')
                            print('Downloading profile header...            ', end='\r')
                            with open(f'../assets/images/header{header_ext}','wb') as f:
                                shutil.copyfileobj(res.raw, f)
                                profile_config.write('\n' + f'avatar: /assets/images/header{avatar_url_ext}')
                except Exception as err:
                    logging.error(f"FAIL. Media couldn't be retrieved from {header_url} because of exception: {err}")
        # Now we get additional information via Twitter API about the profile thats *not* in account.js.
        users = {}
        user_id = read_json_from_js_file(os.path.join(input_folder, 'data/account.js'))[0]['account']['accountId']
        user = []
        user.append(user_id)
        use_cached_request = False
        if os.path.exists(f'profile.json'):
            use_cached_request = yes_no_input('We have found a cached request for your profile. Do you want to use it? (y/n) ')
        if use_cached_request:
            users = get_users_from_cached_request('profile.json')
        else:
            if yes_no_input(f'Download additional profile information from Twitter (approx 2.5KB)?'):
                with requests.Session() as session:
                    guest_token = get_twitter_api_guest_token(session, SESSION_BEARER_TOKEN)
                    users = get_twitter_users(session, SESSION_BEARER_TOKEN, guest_token, [user_id])
                    if os.path.exists(f'profile.json') and os.path.exists(f'output.json'):
                        os.remove(f'profile.json')
                    if os.path.exists(f'output.json'):
                        os.rename('output.json', 'profile.json')
        if users:
            user = users[user_id]
        else:
            user = None
        if user:
            print('Saving user profile information to _config.yml...')
            if user['id']:
                profile_config.write('\n' + f"twitter_id: {user['id']}")
            if user['screen_name']:
                profile_config.write('\n' + f"screen_name: {user['screen_name']}")
            if user['created_at']:
                profile_config.write('\n' + f"twitter_join_date: {user['created_at']}")
            if user['profile_background_color']:
                profile_config.write('\n' + f"profile_background_color: #{user['profile_background_color']}")
            if user['profile_link_color']:
                profile_config.write('\n' + f"profile_link_color: #{user['profile_link_color']}")
            if user['profile_sidebar_border_color']:
                profile_config.write('\n' + f"profile_sidebar_border_color: #{user['profile_sidebar_border_color']}")
            if user['profile_sidebar_fill_color']:
                profile_config.write('\n' + f"profile_sidebar_fill_color: #{user['profile_sidebar_fill_color']}")
            if user['profile_text_color']:
                profile_config.write('\n' + f"profile_text_color: #{user['profile_text_color']}")
            if user['profile_use_background_image']:
                profile_config.write('\n' + f"profile_use_background_image: {user['profile_use_background_image']}")
            return user['id']
        else:
            print('No user profile information was found.')
            return None

def parse_threads(input_filenames, user_account_id, output_thread, output_status):
    print('\n== PARSING PERSONAL THREADS ======================================\n')
    create_or_enter_output_directory(output_thread)
    tweets = OrderedDict()
    print('Reading tweets for threads...')
    for tweets_js_filename in input_filenames:
        json = read_json_from_js_file(tweets_js_filename)
        for tweet in json:
            if 'tweet' in tweet.keys():
                tweet = tweet['tweet']
            if 'in_reply_to_status_id' in tweet:
                if 'in_reply_to_user_id' in tweet:
                    if tweet['in_reply_to_user_id'] == str(user_account_id):
                        tweets[tweet['id_str']] = tweet['in_reply_to_status_id']
                        tweets[tweet['in_reply_to_status_id']] = None
    tweets = dict(sorted(tweets.items(), key=lambda x: x[0], reverse=True))
    thread_counter = 1 
    for tweet_id in tweets.keys():
        tweet_id_list=[]
        while tweets[tweet_id] is not None:
            tweet_id_list.append(tweet_id)#
            old_tweet_id = tweet_id
            tweet_id = tweets[tweet_id]
            tweets[old_tweet_id] = None # Mark as processed
        #tweet_id_list.append(tweet_id)
        tweet_id_list.reverse()
        if len(tweet_id_list) > 1:
            print(f'Found thread {thread_counter}: Tweet IDs {tweet_id_list}')
            tweet_id_list_output = ' '.join(tweet_id_list)
            for tweet_id in tweet_id_list:
                tweet_filename = os.path.join(output_status, f'{tweet_id}' + '.html')
                if os.path.exists(tweet_filename):
                    with open(tweet_filename, 'r', encoding='utf-8') as tweet_file:
                        tweet_content = tweet_file.read()
                        tweet_content = tweet_content.replace('created: ', f'thread: {thread_counter}\ncreated: ')
                        with open(tweet_filename, 'w', encoding='utf-8') as tweet_file:
                            tweet_file.write(tweet_content)
            thread_filename = os.path.join(output_thread, f'{thread_counter}.html')
            thread_post = f'''
---
layout: thread
thread_id: {thread_counter}
tweets: {tweet_id_list_output}
---
'''
            with open(thread_filename, 'w') as f:
                f.write(thread_post)
            thread_counter += 1


def parse_tweets(input_filenames, username, users, archive_media_folder,
                 output_media_folder_name, output_media_url_base, output_posts, output_status, tweet_icon_path, 
                 output_html_filename):
    """Read tweets from input_filenames, write to output_html_filename.
       Copy the media used to output_media_folder_name.
       Collect user_id:user_handle mappings for later use, in 'users'.
       Returns the mapping from media filename to best-quality URL.
   """
    print('\n== PARSING TWEETS ==============================\n')
    tweets = []
    media_sources = []
    download_missing_media = yes_no_input('Download any media that is missing from your archive?')
    for tweets_js_filename in input_filenames:
        json = read_json_from_js_file(tweets_js_filename)
        for tweet in json:
            tweets.append(convert_tweet(tweet, username, archive_media_folder,
                                        output_media_folder_name, output_media_url_base, tweet_icon_path,
                                        media_sources, users, download_missing_media))
    tweets.sort(key=lambda tup: tup[0]) # oldest first

    current_year = 0
    current_month = 0
    current_day = 0
    for timestamp, html, id in tweets:
        dt = datetime.datetime.fromtimestamp(timestamp)
        if current_year != dt.year:
            current_year = dt.year
            year_folder = os.path.join(output_posts, f'{dt.year}')
            create_or_enter_output_directory(year_folder)
            index_file_html = f'''---
layout: nb_year_index
year: {current_year}
---
'''
            index_filepath = os.path.join(year_folder, 'index.html')
            with open(index_filepath, 'w', encoding='utf-8') as f:
                f.write(index_file_html)

        if current_month != dt.month:
            current_month = dt.month
            month_folder = os.path.join(output_posts, f'{dt.year}', f'{dt.month:02}')
            create_or_enter_output_directory(month_folder)
            index_file_html = f'''---
layout: nb_month_index
year: {current_year}
month: {current_month}
---
'''
            index_filepath = os.path.join(month_folder, 'index.html')
            with open(index_filepath, 'w', encoding='utf-8') as f:
                f.write(index_file_html)

        if current_day != dt.day:
            current_day = dt.day
            day_folder = os.path.join(output_posts, f'{dt.year}', f'{dt.month:02}', f'{dt.day:02}')
            create_or_enter_output_directory(day_folder)
            index_file_html = f'''---
layout: nb_day_index
year: {current_year}
month: {current_month}
day: {current_day}
---
'''
            index_filepath = os.path.join(day_folder, 'index.html')
            with open(index_filepath, 'w', encoding='utf-8') as f:
                f.write(index_file_html)
				
		
        day_folder = os.path.join(output_posts, f'{dt.year}', f'{dt.month:02}', f'{dt.day:02}')
        # Use a filename that can be imported into Jekyll: YYYY-MM-DD-your-title-here.html
        tweet_filename = os.path.join( output_status, f'{id}' + '.html')
        with open(tweet_filename, 'w', encoding='utf-8') as f:
            f.write(html)

 
    print(f'Wrote {len(tweets)} tweets to *.md and {output_html_filename}, with images and video embedded from {output_media_folder_name}')

    return media_sources


def parse_followings(data_folder, users, user_id_URL_template, output_following_filename, media_folder):
    """Parse data_folder/following.js, write to output_following_filename.
       Query Twitter API for the missing user handles, if the user agrees.
    """
    print('\n== PEOPLE YOU ARE FOLLOWING ============================================\n')
    download_avatars = yes_no_input('Do you want to download avatars for people who are following you? This make take some time.')
    if download_avatars:
        skip_existing = yes_no_input('To save time, do you want to skip downloading avatars that you have already downloaded?')
        avatar_folder = os.path.join(media_folder, 'avatars')
        print(f'Avatars will be downloaded to {avatar_folder}')
        create_or_enter_output_directory(avatar_folder)
    following = []
    following_json = read_json_from_js_file(os.path.join(data_folder, 'following.js'))
    following_ids = []
    print(f'Found {len(following_json)} people who are following you.')
    for follow in following_json:
        if 'following' in follow and 'accountId' in follow['following']:
            following_ids.append(follow['following']['accountId'])
    lookup_users(following_ids, user_id_URL_template, users, True, 'following.json')
    if os.path.exists(f'following.json') and os.path.exists(f'output.json'):
        os.remove(f'following.json')
    if os.path.exists(f'output.json'):
        os.rename('output.json', 'following.json')
    for id in following_ids:
        handle = users[id].handle if id in users else '~unknown~handle~'
        full_name = users[id].name if id in users else '~unknown~name~'
        description = users[id].description if id in users else '~unknown~description~'
        following_entry = '- handle: ' + handle + '\n  twitter_url: ' + user_id_URL_template.format(id)
        if full_name:
            following_entry += '\n  name: ' + full_name
        if description:
            following_entry += '\n  description: ' + description.replace('\n', ' ').replace('\r', ' ')
        if download_avatars:
            avatar_url = users[id].avatar if id in users else None
            if avatar_url:
                avatar_url = avatar_url.replace('_normal', '')
                image_filename = download_media(avatar_url, avatar_folder, skip_existing)
                if image_filename:
                    following_entry += '\n  avatar: ' + image_filename
        following.append(following_entry)
    following.sort()
    with open(output_following_filename, 'w', encoding='utf8') as f:
        f.write('\n'.join(following))
    print(f"Wrote {len(following)} accounts to {output_following_filename}")
    with open(f'../_config.yml','a') as profile_config:
        profile_config.write('\nFollowing: ' + str(len(following)))


def parse_followers(data_folder, users, user_id_URL_template, output_followers_filename, media_folder):
    """Parse data_folder/followers.js, write to output_followers_filename.
       Query Twitter API for the missing user handles, if the user agrees.
    """
    print('\n== PEOPLE WHO FOLLOW YOU ==============================================\n')
    followers = []
    download_avatars = yes_no_input('Do you want to download your followers avatars? This make take some time.')
    if download_avatars:
        skip_existing = yes_no_input('To save time, do you want to skip downloading avatars that you have already downloaded?')
        avatar_folder = os.path.join(media_folder, 'avatars')
        print(f'Avatars will be downloaded to {avatar_folder}')
        create_or_enter_output_directory(avatar_folder)
    follower_json = read_json_from_js_file(os.path.join(data_folder, 'follower.js'))
    follower_ids = []
    for follower in follower_json:
        if 'follower' in follower and 'accountId' in follower['follower']:
            follower_ids.append(follower['follower']['accountId'])
    lookup_users(follower_ids, user_id_URL_template, users, True)
    if os.path.exists(f'followers.json') and os.path.exists(f'output.json'):
        os.remove(f'followers.json')
    if os.path.exists(f'output.json'):
        os.rename('output.json', 'followers.json')
    for id in follower_ids:
        handle = users[id].handle if id in users else '~unknown~handle~'
        full_name = users[id].name if id in users else '~unknown~name~'
        description = users[id].description if id in users else '~unknown~description~'
        follower_entry = '- handle: ' + handle + '\n  twitter_url: ' + user_id_URL_template.format(id)
        if full_name:
            follower_entry += '\n  name: ' + full_name
        if description:
            follower_entry += '\n  description: ' + description.replace('\n', ' ').replace('\r', ' ')
        if download_avatars:
            avatar_url = users[id].avatar if id in users else None
            if avatar_url:
                avatar_url = avatar_url.replace('_normal', '')
                image_filename = download_media(avatar_url, avatar_folder, skip_existing)
                if image_filename:
                    follower_entry += '\n  avatar: ' + image_filename
        followers.append(follower_entry)
    followers.sort()
    with open(output_followers_filename, 'w', encoding='utf8') as f:
        f.write('\n'.join(followers))
    print(f"Wrote {len(followers)} accounts to {output_followers_filename}")
    with open(f'../_config.yml','a') as profile_config:
        profile_config.write('\nFollowers: ' + str(len(followers)))

def main():

    print('''
== NORWEGIAN BLUE TWITTER ARCHIVE PARSER ==========================================
==
== Based on the Twitter Archive Parser by Tim Hutton.
== https://github.com/timhutton/twitter-archive-parser
==
== Modifications by Michael James for the Norwegian Blue project.
== https://github.com/alephnaughtpix/norwegianblue
==
== FINAL "Goodbye to the Twitter API" VERSION: 2023-06-02.
==
==================================================================================+

''')

    input_folder = '../source'
    output_media_folder_name = '../media/'
    output_media_url_base = '/media/'
    output_posts = '../archive'
    output_status = '../_status/'
    output_thread = '../_thread/'
    tweet_icon_path = f'{output_media_folder_name}tweet.ico'
    output_html_filename = 'TweetArchive.html'
    data_folder = os.path.join(input_folder, 'data')
    account_js_filename = os.path.join(data_folder, 'account.js')
    log_path = os.path.join(output_media_folder_name, 'download_log.txt')
    output_following_filename = '../_data/following.yaml'
    output_followers_filename = '../_data/followers.yaml'
    user_id_URL_template = 'https://twitter.com/i/user/{}'

    users = {}

    # Extract the username from data/account.js
    if not os.path.isfile(account_js_filename):
        print(f'Error: Failed to load {account_js_filename}. Start this script in the root folder of your Twitter archive.')
        exit()
    username = extract_username(account_js_filename)
    
    user_account_id = parse_profile(input_folder, users, user_id_URL_template)

    # Identify the file and folder names - they change slightly depending on the archive size it seems.
    input_filenames, archive_media_folder = find_input_filenames(data_folder)

    # Make a folder to copy the images and videos into.
    os.makedirs(output_media_folder_name, exist_ok = True)
    if not os.path.isfile(tweet_icon_path):
        shutil.copy('../source/assets/images/favicon.ico', tweet_icon_path)

    media_sources = parse_tweets(input_filenames, username, users, archive_media_folder,
                                 output_media_folder_name, output_media_url_base, output_posts, output_status,tweet_icon_path, output_html_filename)
    parse_threads(input_filenames, user_account_id, output_thread, output_status)
    parse_followings(data_folder, users, user_id_URL_template, output_following_filename, output_media_folder_name )
    parse_followers(data_folder, users, user_id_URL_template, output_followers_filename, output_media_folder_name)

    # Download larger images, if the user agrees
    print(f"\nThe archive doesn't contain the original-size images. We can attempt to download them from twimg.com.")
    print(f'Please be aware that this script may download a lot of data, which will cost you money if you are')
    print(f'paying for bandwidth. Please be aware that the servers might block these requests if they are too')
    print(f'frequent. This script may not work if your account is protected. You may want to set it to public')
    print(f'before starting the download.')
    if yes_no_input('\nOK to start downloading?'):
        download_larger_media(media_sources, log_path)
        print('In case you set your account to public before initiating the download, do not forget to protect it again.')

    print('''
============================================================================================
== Archive parsing complete. Thank you for using the Norwegian Blue Twitter Archive Parser.
============================================================================================
''')

if __name__ == "__main__":
    main()
