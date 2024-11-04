class UserProfile:
    def __init__(self, 
            id, 
            username = None, 
            screen_name = None, 
            description = None, 
            url = None, 
            avatar_url = None,
            header_url = None,
            location = None,
            joined_date = None,
            timezone = None,
            birthdate = None,
            email = None,
            created_via = None
        ):
        self.id = id
        self.username = username
        self.screen_name = screen_name
        self.description = description
        self.url = url
        self.avatar_url = avatar_url
        self.header_url = header_url
        self.location = location
        self.joined_date = joined_date
        self.timezone = timezone
        self.birthdate = birthdate
        self.email = email
        self.created_via = created_via
        
    def __str__(self):
        return f"{self.username} ({self.screen_name})"
    
    def add_to_config_file(self, filepath):
        with open( filepath, 'a', encoding='utf8') as config_file:
            config_file.write(f"\n\n# Twitter Profile\n")
            config_file.write(f"\ntwitter_profile:\n")
            if self.id:
                config_file.write(f"  id: {self.id}\n")
            if self.username:
                config_file.write(f"  username: {self.username}\n")
            if self.screen_name:
                config_file.write(f"  screen_name: {self.screen_name}\n")
            if self.description:
                config_file.write(f"  description: {self.description}\n")
            if self.url:
                config_file.write(f"  url: {self.url}\n")
            if self.avatar_url:
                config_file.write(f"  avatar_url: {self.avatar_url}\n")
            if self.header_url:
                config_file.write(f"  header_url: {self.header_url}\n")
            if self.location:
                config_file.write(f"  location: {self.location}\n")
            if self.joined_date:
                config_file.write(f"  joined_date: {self.joined_date}\n")
            if self.timezone:
                config_file.write(f"  timezone: {self.timezone}\n")
            if self.birthdate:  
                config_file.write(f"  birthdate: {self.birthdate}\n")
            if self.email:
                config_file.write(f"  email: {self.email}\n")
            if self.created_via:
                config_file.write(f"  created_via: {self.created_via}\n")

