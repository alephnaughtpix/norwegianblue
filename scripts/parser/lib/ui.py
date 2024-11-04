import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# MAIN WINOW ======================================================================================
# Here the user can select the source and output directories. 
# The start button is disabled until both directories have been selected.
class MainWindow:
    
    # Constructor- takes a Processor object as an argument.
    def __init__(self, processor):
        self.processor = processor
        self.main_window = tk.Tk()
        self.main_window.title('Norwegian Blue Twitter Parser')
        self.main_window.config(bg="skyblue")
        
        title_frame = tk.Frame(self.main_window, bg="skyblue", pady=10, padx=10)
        title_frame.pack(side='top', fill='x')
        title_label = tk.Label(title_frame, text='Norwegian Blue Twitter Parser', font=('Arial', 24), bg="skyblue", justify='center')
        title_label.pack(fill='x')
        
        start_frame= tk.Frame(self.main_window, padx=10, pady=10, bg="skyblue")
        self.start_button = tk.Button(start_frame, text='Start', font=('Arial', 12), state='disabled', command=lambda: self.__start())

        source_frame = tk.Frame(self.main_window, padx=10, pady=10)
        source_frame.pack(fill='x')
        source_label = tk.Label(source_frame, text='Source directory:', font=('Arial', 12, 'bold'), justify='left')
        source_label.pack(side='top', fill='x')
        self.source_directory_label = tk.Label(source_frame, text=self.processor.config.input_folder , font=('Arial', 12))
        self.source_directory_label.pack(side='left')
        source_directory_button = tk.Button(source_frame, text='Change', font=('Arial', 12), command=lambda: self.__select_source_directory())
        source_directory_button.pack(side='right')
        
        output_frame = tk.Frame(self.main_window, padx=10, pady=10)
        output_frame.pack(fill='x')
        output_label = tk.Label(output_frame, text='Output directory:', font=('Arial', 12, 'bold'), justify='left')
        output_label.pack(side='top', fill='x')
        self.output_directory_label = tk.Label(output_frame, text=self.processor.config.output_folder , font=('Arial', 12))
        self.output_directory_label.pack(side='left')
        output_directory_button = tk.Button(output_frame, text='Change', font=('Arial', 12), command=lambda: self.__select_output_directory())
        output_directory_button.pack(side='right')
        
        followers_frame = tk.Frame(self.main_window, padx=10, pady=10)
        followers_frame.pack(fill='x')
        followers_label = tk.Label(followers_frame, text='Followers page (optional):', font=('Arial', 12, 'bold'), justify='left')
        followers_label.pack(side='top', fill='x')
        self.followers_directory_label = tk.Label(followers_frame, text=self.processor.config.followers_page , font=('Arial', 12))
        self.followers_directory_label.pack(side='left')
        followers_directory_button = tk.Button(followers_frame, text='Change', font=('Arial', 12), command=lambda: self.__select_followers_directory())
        followers_directory_button.pack(side='right')
        
        following_frame = tk.Frame(self.main_window, padx=10, pady=10)
        following_frame.pack(fill='x')
        following_label = tk.Label(following_frame, text='Following page (optional):', font=('Arial', 12, 'bold'), justify='left')
        following_label.pack(side='top', fill='x')
        self.following_directory_label = tk.Label(following_frame, text=self.processor.config.following_page , font=('Arial', 12))
        self.following_directory_label.pack(side='left')
        following_directory_button = tk.Button(following_frame, text='Change', font=('Arial', 12), command=lambda: self.__select_following_directory())
        following_directory_button.pack(side='right')

        start_frame.pack(fill='x')
        self.start_button.pack()
        
        self.__check_start_button()
        
    # Show main window
    def show(self):
        self.main_window.mainloop()
        
    # PRIVATE METHODS ==============================================================================
    
    # Close the main window, and start the progress window.
    def __start(self):
        input_folder = self.source_directory_label.cget('text')
        output_folder = self.output_directory_label.cget('text')
        followers_folder = self.followers_directory_label.cget('text')
        following_folder = self.following_directory_label.cget('text')
        if followers_folder == '':
            followers_folder = None
        if following_folder == '':
            following_folder = None
        self.main_window.destroy()
        self.processor.start(input_folder, output_folder, followers_folder, following_folder)
        
    # Enables or disables the start button based on the selected directories.
    def __check_start_button(self):
        if self.source_directory_label.cget('text') != 'No directory selected' and self.output_directory_label.cget('text') != 'No directory selected':
            self.start_button.config(state='normal')
        else:
            self.start_button.config(state='disabled')
        
    # Selects the source directory, and checks for the Twitter archive files.
    def __select_source_directory(self):
        directory = self.__select_directory(self.source_directory_label, "Select folder of Twitter Archive")
        if directory == '':
            return
        if not self.processor.is_twitter_archive(directory):
            answer = messagebox.askquestion("Twitter archive not found", "We can't find the twitter archive in this folder. Are you sure?")
            if answer == 'no':
                self.source_directory_label.config(text='No directory selected')
                self.start_button.config(state='disabled')
    
    # Selects the output directory, and checks if it is empty.
    def __select_output_directory(self):
        directory = self.__select_directory(self.output_directory_label, "Select folder to save the website to")
        if directory == '':
            return
        if not self.processor.output_directory_is_empty(directory):
            answer = messagebox.askquestion("Folder not empty", "This folder is not empty, and as a result the files in this folder may be overwritten. Are you sure?")
            if answer == 'no':
                self.output_directory_label.config(text='No directory selected')
                self.start_button.config(state='disabled')
    
    # Selects the saved followers page, and checks if it is empty.
    def __select_followers_directory(self):
        filepath = self.__select_file(self.followers_directory_label, "Select a copy of your followers page.")
        
        # Selects the saved followers page, and checks if it is empty.
    def __select_following_directory(self):
        filepath = self.__select_file(self.following_directory_label, "Select a copy of your following page.")

    # Selects a directory and updates the label with the directory path.
    # Also enables the start button if both directories have been selected.
    def __select_directory(self, label, title):
        directory = filedialog.askdirectory(title=title)
        if directory != '':
            label.config(text=directory)
            self.__check_start_button()
        return directory

    
    # Selects a file and updates the label with the file path.
    def __select_file(self, label, title):
        filepath = filedialog.askopenfile(title=title)
        if filepath:
            filename = filepath.name
            if filepath != '':
                label.config(text=filename)
                self.__check_start_button()
        return filepath

# =================================================================================================

# PROGRESS WINDOW =================================================================================

class ProgressWindow:
    
    def __init__(self):
        self.progress_window = tk.Tk()
        self.progress_window.title('Norwegian Blue Twitter Parser')
        
        title_frame = tk.Frame(self.progress_window, pady=10, padx=10)
        title_frame.pack(side='top', fill='x')
        title_label = tk.Label(title_frame, text='Converting Twitter Archive', font=('Arial', 16), justify='center')
        title_label.pack(fill='x')
        
        top_status_frame = tk.Frame(self.progress_window, pady=10, padx=10, name='top_status_frame')
        top_status_frame.pack(fill='x')
        self.top_status_label = tk.Label(top_status_frame, text='Starting...', font=('Arial', 12), justify='center', name='top_status_label')
        self.top_status_label.pack(fill='x')
        
        top_progress_frame = tk.Frame(self.progress_window, pady=10, padx=10)
        top_progress_frame.pack(fill='x')
        self.top_progress = ttk.Progressbar(top_progress_frame, orient='horizontal', length=100, mode='determinate')
        self.top_progress.pack(fill='x')
        
        status_frame = tk.Frame(self.progress_window, pady=10, padx=10)
        status_frame.pack(fill='x')
        self.status_label = tk.Label(status_frame, text='Starting...', font=('Arial', 12), justify='center')
        self.status_label.pack(fill='x')
        
        progress_frame = tk.Frame(self.progress_window, pady=10, padx=10)
        progress_frame.pack(fill='x')
        self.progress = ttk.Progressbar(progress_frame, orient='horizontal', length=100, mode='determinate')
        self.progress.pack(fill='x')
        
    def thread(self, function):
        self.progress_window.after(250, function)
        
    def show(self):
        self.progress_window.mainloop()
        
    def top_status(self, status):
        self.top_status_label.config(text=status)
        self.progress_window.update()
        
    def status(self, status):
        self.status_label.config(text=status)
        self.progress_window.update()
        
    def update_top_progress(self, progress):
        self.top_progress['value'] = progress
        self.progress_window.update()
        
    def update_progress(self, progress):
        self.progress['value'] = progress
        self.progress_window.update()
 