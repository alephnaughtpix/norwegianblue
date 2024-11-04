from lib.config import Config
import json
import os
import requests

class Utils:

    # Creates a directory if it doesn't exist.
    @staticmethod
    def create_directory(output_directory):
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
            
    # Reads the contents of a Twitter-produced .js file into a dictionary.
    @staticmethod
    def read_json_file(filename):
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

class UriLoader():
    def __init__(self, uri, config):
        self.uri = uri
        self.data = None
        self.user_agent = config.user_agent
        self.success = False
        
    def __enter__(self):
        self.load()
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        pass
        
    def load(self):
        headers = {'User-Agent': self.user_agent}
        try:
            self.data = requests.get(self.uri, headers=headers)
            self.success = self.data.status_code == 200
        except Exception as err:
            print(f"FAIL. Original URL of {self.uri} because of exception: {err}")
            self.success = False
    
    # Sometimes the content doesn't have an extension, so we have to guess it from the content-type header.
    def guess_ext(self):
        return self.data.headers['Content-Type'].split('/')[1] if 'Content-Type' in self.data.headers else None