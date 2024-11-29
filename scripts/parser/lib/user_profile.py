from lib.utils import *

class UserProfile:
    def __init__(self, 
            id, 
            username = None, 
            screen_name = None, 
            description = None, 
            url = None, 
            avatar_url = None,
            local_url = None,
            header_url = None,
            local_header_url = None,
            location = None,
            joined_date = None,
            timezone = None,
            birthdate = None,
            email = None,
            created_via = None,
            following = None,
            follower = None,
            no_of_followers = None,
            no_following = None,
            no_tweets = None
        ):
        self.id = id
        self.username = username
        self.screen_name = screen_name
        self.description = description
        self.url = url
        self.avatar_url = avatar_url
        self.local_url = local_url
        self.local_header_url = local_header_url
        self.header_url = header_url
        self.location = location
        self.joined_date = joined_date
        self.timezone = timezone
        self.birthdate = birthdate
        self.email = email
        self.created_via = created_via
        self.following = following
        self.follower = follower
        self.no_of_followers = no_of_followers
        self.no_following = no_following
        self.no_tweets = no_tweets
        
    def __str__(self):
        return f"{self.username} ({self.screen_name})"
    
    def add_to_config_file(self, filepath):
        config_yaml_string = self.as_yaml("\n\n# Twitter Profile\ntwitter_profile:\n  ")
        with open( filepath, 'a', encoding='utf8') as config_file:
            config_file.write(config_yaml_string)

    def as_yaml(self, prefix = '- '):
        yaml_string = prefix
        if self.id:
            yaml_string += f"id: {self.id}\n"
        if self.username:
            yaml_string += f"  username: \"{self.username}\"\n"
        if self.screen_name:
            yaml_string += f"  screen_name: {self.screen_name}\n"
        if self.description:
            yaml_string += f"  description: {self.description}\n"
            #print('description:', self.description)
        if self.url:
            yaml_string += f"  url: \"{self.url}\"\n"
        if self.avatar_url:
            yaml_string += f"  avatar_url: \"{self.avatar_url}\"\n"
        if self.local_url:
            local_url = self.local_url.replace('\\', '\\\\')
            yaml_string += f"  local_url: \"{local_url}\"\n"
        if self.header_url:
            yaml_string += f"  header_url: \"{self.header_url}\"\n"
        if self.local_header_url:
            local_header_url = self.local_header_url.replace('\\', '\\\\')
            yaml_string += f"  local_header_url: \"{local_header_url}\"\n"
        if self.location:
            yaml_string += f"  location: {self.location}\n"
        if self.joined_date:
            join_date = self.joined_date.replace('T', ' ').replace('Z', '')
            yaml_string += f"  joined_date: {join_date}\n"
        if self.timezone:
            yaml_string += f"  timezone: {self.timezone}\n"
        if self.birthdate:  
            yaml_string += f"  birthdate: {self.birthdate}\n"
        if self.email:
            yaml_string += f"  email: {self.email}\n"
        if self.created_via:
            yaml_string += f"  created_via: {self.created_via}\n"
        if self.following:
            yaml_string += f"  following: {self.following}\n"
        if self.follower:
            yaml_string += f"  follower: {self.follower}\n"
        if self.no_of_followers:
            yaml_string += f"  no_of_followers: {self.no_of_followers}\n"
        if self.no_following:
            yaml_string += f"  no_following: {self.no_following}\n"
        if self.no_tweets:
            yaml_string += f"  no_tweets: {self.no_tweets}\n"
        return yaml_string
    
    def as_dict(self):
        dict = {}
        if self.id:
            dict['id'] = self.id
        if self.username: 
            dict['username'] = self.username
        if self.screen_name:
            dict['screen_name'] = self.screen_name
        if self.description:
            dict['description'] = self.description
        if self.url:
            dict['url'] = self.url
        if self.avatar_url:
            dict['avatar_url'] = self.avatar_url
        if self.local_url:
            dict['local_url'] = self.local_url
        if self.header_url:
            dict['header_url'] = self.header_url
        if self.local_header_url:
            dict['local_header_url'] = self.local_header_url
        if self.location:
            dict['location'] = self.location
        if self.joined_date:
            dict['joined_date'] = self.joined_date
        if self.timezone:
            dict['timezone'] = self.timezone
        if self.birthdate:
            dict['birthdate'] = self.birthdate
        if self.email:
            dict['email'] = self.email
        if self.created_via:
            dict['created_via'] = self.created_via
        if self.following:
            dict['following'] = self.following
        if self.follower:
            dict['follower'] = self.follower
        if self.no_of_followers:
            dict['no_of_followers'] = self.no_of_followers
        if self.no_following:
            dict['no_following'] = self.no_following
        if self.no_tweets:
            dict['no_tweets'] = self.no_tweets
        return dict 
    
    @staticmethod
    def find_id_for_username(username, user_profiles):
        for user_profile in user_profiles:
            if user_profiles[user_profile].username == username:
                return user_profiles[user_profile].id
        return None

