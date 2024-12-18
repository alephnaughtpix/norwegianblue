# Norwegian Blue

## It is an X-Twitter, it has ceased to be!

Norwegian Blue is a Jekyll framework and conversion tool for housing your Twitter archive.

## Overview

When you decide to move on from Twitter, you given an option of downloading an archive of your time on Twitter. This is a pretty good option as far as it goes, but it does have a few problems.

* Any link goes through X-Twitter's t.co link shortener, so if that goes down, you lose the link. This is particularly annoying as the archive *does* contain the original link.
* If you click on an image or video, it takes you to the X-Twitter page for that media.
* Tweets are in a JSON format, which is not very easy to copy and paste into a blog post.
* The archive does not contain the avatars of the people you follow and who follow you.

Norwegian Blue contains a conversion tool to convert your Twitter archive into a Jeykll based website, allowing you (depending on the size) to host your Twitter archive on web hosts compatible with Jekyll, such as GitHub Page, GitLab Pages, or Netlify, or even your own server. As the output of a Jekyll project is static HTML, CSS, and JavaScript, it is very easy to host, and very quick.

### Features
Out of the box, Norwegian Blue provides the following features:

* A Jekyll project with layouts and includes for displaying your Twitter archive.
* A parser tool to convert your Twitter archive into Jekyll pages.
* Your tweets, sorted by year, month, and day.
* Threads of tweets.
* Media files, such as images and videos.
* Where possible, the avatars of the people you follow and who follow you.
* Any threads of tweets you have made.
* If you've regualrly used hashtags, the archive will contain an index of tweets for each hashtag.

As this is a Jekyll project, you can customise the layouts and includes to your heart's content, and add your own CSS and JavaScript to make the site your own.

### What it doesn't do
* The conversion is designed to not use the Twitter API, and query the website as little as possible, so there will be some information it cannot obtain, such as information about some of your followers.
* **Direct messages**. As this is a public facing website, it doesn't make sense to include direct messages. Your Twitter archive will contain your direct messages if you want to keep them.

## What you need

* **Your Twitter archive**. You can download this from Twitter. Go to your settings, and at the bottom of the page, you will see an option to request a download your Twitter archive. It will normally take around a week for this request to be processed, and you will be sent a link to download a zip file of your Twitter archive. Once you do this you will need to unzip the archive into a folder, which you'll point to when you run the parser tool.
* **Your Twitter pages for your Followers and Following**. This is more a nice to have, but the parser tool can parse these pages to get more information about the people you follow and who follow you. Obviously I wouldn't recommend this if you have elevently squillion followers, but if you have a reasonable amount, say less than 2000, this is an option. The next section will explain how to do save these pages.

### Getting your Twitter pages for your Followers and Following
1. What you will need is a web browser extension that can save a web page as a complete web page including images. The one that I found the best was **SingleFile** which you can get an extension for [Firefox](https://addons.mozilla.org/en-US/firefox/addon/single-file/) and [Chrome](https://chromewebstore.google.com/detail/singlefile/mpiodijhokgodhhofbcjdecpffjipkle). This extension will save the page as a single HTML file, including images, CSS, and JavaScript.
2. Log on to Twitter, and go to your followers page.
3. Go to bottom of the page, and it will load more followers. Keep moving down the page until you have all your followers loaded.
4. Once you have all your followers loaded, go back to the top of the page.
5. Click on the SingleFile icon in your browser, and save the page as a complete web page. This will take a couple of minutes, depending on how many followers you have. Once it's done, the saved page will be saved to your downloads folder. Rename the file to something sensible like `followers.html` and move it to a safe folder.
6. Repeat steps 3-5 for your following page, saving the page as something like `following.html`.
7. For reference I had around 1000 followers and around 1000 following, and the saved pages were around 17-20MB each. The size is dependent on the number of followers and following you have, but also includes the images as data URLs, which the parser tool can extract and save as separate files. This saves the bother of having to download the images separately.

## How to use
Converting your Twitter archive into a website is a two-step process:
1. You run the parser tool, which will convert your Twitter archive into a Jeykll project.
2. You then run a Jekyll build to generate the website.
Many Jekyll compatible hosts, such as GitHub Pages, GitLab Pages, and Netlify, will actually do step 2 for you, but you can also host the site on your own server.

## Running the parser tool

### Windows

### Linux

## Requirements

* [Python 3.6](https://www.python.org) or later.
* [Ruby 3.0.2](https://www.ruby-lang.org/en/) or later.
* [Jekyll 3.9.2](https://jekyllrb.com/news/2022/03/27/jekyll-3-9-2-released/) or later.

## Work used

* The parser tool is hugely indebted to Tim Hutton's [Twitter Archive Parser](https://github.com/timhutton/twitter-archive-parser) from November, modified to output Jekyll source pages in a format for this project.

## How to use

* Download your Twitter archive from [Twitter](https://twitter.com/settings/your_twitter_data).
* Unzip the archive into the folder `source`.
* From the folder `scripts`, run `python3 parser.py`.
* As the script runs, it ask you a certain points whether you want to download data from the Twitter API, (see section *"Post Twitter API Shutdown"* below.) or download images and media. Note that the latter can take some time upon first run. The script will cache data from the Twitter API if you want to run it again.
* Note if you want to run the script again, you need to clean up `_config.yml` to avoid duplicate settings.

### Post Twitter API shutdown

As noted above, as of February 14th 2023, Twitter has shut down the free-to-use Twitter API. This means that the parser script will no longer be able to download data from the Twitter API as is. However, if you have previously run the parser script, it will have cached the data from the Twitter API, and you will be able to run the parser script again to generate the Jekyll pages.

However, if you are lucky enough to have paid access to the Twitter API, you can run the parser script if you get a session bearer token. The variable name is `SESSION_BEARER_TOKEN`, set at line 44 in `scripts/parser.py`.

Note that how much data you can download from the Twitter API is limited by your access level. See [Twitter's documentation](https://developer.twitter.com/en/docs/twitter-api/rate-limits) for more information.

## What you get

* Inside the folder `_status` is each tweet as a Jekyll page.
* Inside the folder `_thread` is each thread of tweets in your Twitter archive as a Jekyll page.
* Inside the folder `media` is each image and video in your Twitter archive.
* Inside the folder `media/avatars` are the avatars of the people you follow and your followers.
* Inside the folder `archive` are indexs for days months and years of your tweets.
* Inside the folder `scripts` is the downloaded data from the Twitter API in the files `following.json`  `followers.json` and `profile.json` (Your profile). This is so that you have cached data for future runs of the parser script, and also in case the Twitter API gets shut down. (**COUGH**!)
* Inside the folder `_data` are the YML files `following.yml` and `followers.yml` which contain the data of the people you follow and who follow you.
* Your profile informartion is appended to the file `_config.yml`.

## Front Matter

The Jekyll pages generated by the parser script contain front matter to allow for flexible use of the data.

All pages have the following front matter:

* `layout`: The layout of the page.

### Tweets

* `id`: The ID of the tweet. (This is also the format of the filename.)
* `created`: The date of the tweet.
* `year`: The year of the tweet.
* `month`: The month of the tweet.
* `day`: The day of the tweet.
* `original_url`: The URL of the tweet on Twitter.
* `repy_to_url`: (optional) The URL of the tweet this tweet is a reply to.
* `reply_to_names`: (optional) The names of the people this tweet is a reply to.
* `reply_to_id`: (optional) The ID of the tweet this tweet is a reply to if it's a reply to your own tweet.
* `is_in_thread`: (optional) If the tweet is in a thread, this is set to true.
* `thread_id`: (optional) The ID of the thread the tweet is in.

### Threads

* `id`: The ID of the thread. (This is also the format of the filename.)
* `tweets`: The IDs of the tweets in the thread, seperated by a space.

## Format of YML data files

The YML files in the folder `_data` contain the data of the people you follow and who follow you. The format in both `followers.yaml` and `following.yaml` is as follows:

* `handle`: The handle of the Twitter user.
* `name`: The screen name of the Twitter user.
* `url`: The URL of the Twitter user's profile.
* `avatar`: (optional) The filename of the Twitter user's avatar if they have one, and you have instructed the parser script to download user's avatars. Any downloaded avatars are stored in the folder `media/avatars`.

## Using the Norwegian Blue framework

Once your have run the parser script, you can make a copy of this project for your use, and use the Norwegian Blue framework to generate a static website from your Twitter archive.

### Generating a site

* To generate a static website from your project, go to the root directory of the project and type the command:
  `bundle exec jekyll build --verbose --config _config.yml,_config.dev.yml`

  **WARNING!** Unless you have been *very* quiet on Twitter, this site generation process will take a **LONG** time. This is why I put `--verbose` in the command, so you can see what's going on, and you don't think your computer has crashed.
* Once finished generated site will be in the folder `_site`.

### Preparing for adding to a repository

You might want to add your Jekyll project to a repository. To do this, you need to:

* Remove the folder `.git` from the project.
* Edit the file `.gitignore`, as it hides all the generated posts and downloaded media from git. Of the lines to keep in this file, you will need to keep `_site` and `source`.
* You can now initialise a new git repository in a folder, and add the files from your project to the repository.

I should note that, with the amount of status posts combined with the amount of media downloaded, that this project will tend to be very large. If you're thinking of hosting this repository on the likes of GitHub, never mind hosting it on GitHub pages, I would caution against it, or at least consider using [Git LFS](https://git-lfs.github.com) to store the media files for the project, as standard GitHub projects have a soft limit of 1GB. (There is also a [limitation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github) on file size of 100MB for a file, and a warning for files of 50MB or over, which could happen with, say, video files.) Even if the resulting project is less than that, it will still be really pushing it to host it on GitHub pages. There's a good discussion of GitHub storage limits [here](https://stackoverflow.com/questions/38768454/repository-size-limits-for-github-com).

Another issue is that if you have a repository host that can handle this size of project, it's going to be difficult to cope with the sheer amount of files on the first push. It might better to either break down the push into smaller steps, or host it yourself on your own server if you have one, as in that case, you could FTP the whole project to the server, set up a Git service on there, and then do a `git init` on your project *in situ*.

### Working with the Jekyll project

As noted above, it takes a long time to generate a site from your project, which makes developing the site difficult. To make this easier, I've found that having a copy of the folders `_status` and `_thread` with only a small amount of posts in them makes it much easier, and when I'm done I can slot the original folders back in. Obviously make sure you have made a copy of these folders, and not just moved them, as you will need the originals to generate the site.

### Layouts

The folllowing layouts are provided:

* `base.html`: The base layout for all pages.
* `compress.html`: A utility layout to compress the HTML output.
* `single-tweet.html`: The layout for a single tweet.
* `thread.html`: The layout for a thread of tweets.
* `tweetlist.html`: The layout for a list of tweets.
* `nb_day_index.html`: The layout for the index of tweets for a day.
* `nb_month_index.html`: The layout for the index of tweets for a month.
* `nb_year_index.html`: The layout for the index of tweets for a year.

### Includes

* `tweet.html`: HTML for a single tweet.
* `twitter-user.html`: HTML for a Twitter user profile.
