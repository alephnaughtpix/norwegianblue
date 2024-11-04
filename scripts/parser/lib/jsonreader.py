import json

class JsonReader:
    def __init__(self, filename = None):
        self.data = None
        if filename:
            self.filename = filename
            self.read()

    def read(self):
        with open(self.filename, 'r', encoding='utf8') as f:
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
            self.data = json.loads(data)
            return self.data