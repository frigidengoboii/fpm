# fpm
Facebook Page Manager (originally Frigid Page Manager)

This python-based script and interface module allows for automated aggregation and posting of facebook posts from either auto-updating Google Sheets documents (e.g. tied to a survey) or Facebook Page message logs.

## Requirements

Tested on OS X, Debian. Should work without major issues on Ubuntu. Could probably be coerced to run on Windows, but I don't currently have access to a dev-friendly box, so not tested (please let me know if you get it to work and send a pull request).

#### Pre-Install Requirements:
 - Python3 + pip3 + SetupTools (tested homebrew, debian apt); generally Python 3.6 >= cause I tend to write modern code
   You can usually get Python etc. from `apt-get`, `yum` or `homebrew` on Debian-Ubuntu-Mint, RHEL-Centos-Fedora or OS X respectively.
 - Browser of choice supporting Selenium webdriver instance (e.g. Chrome + chromedriver [ http://chromedriver.chromium.org ])
 - Facebook Developer account and Graph API app (see below section on APIs)
 - Google Developer account and Sheets API credentials (see below section on APIs)
 - virtualenv or other general python environment you're willing to install dependency packages into
 
## Install

Clone git repo
```
git clone https://github.com/frigidengoboii/fpm.git
cd fpm
```

Run SetupTools installer. (If you want to use a python `virtualenv`, make sure you have set it up and it is currently loaded) 
```
./setup.py develop
```
*I recommend the develop flag, since it makes any debugging much easier, and this code shouldn't be considered any form of production ready; it's beta at best, probably more like alpha quality.*

## API Credentials and Setup

**Warning:** This is something of an involved and lengthy process; it will almost certainly be the most annoying part of this whole process. It is necessary since we need API access to pull data from Messenger and Sheets. We could scrape using Selenium, but it would take forever and likely be slower than manual entry. 

### Facebook Graph API

We register ourselves as a *device* with facebook's graph API to access messages without having to worry about providing a web interface and handling redirects. 

1. Create a Facebook Developer Account (usually linked to a standard FB account) [ https://developers.facebook.com ]
1. Create a new app in your developer account. Give it a name, etc. 
1. Make sure to keep your app in **Development Mode** - this gives us just enough read access (for message logs), but no write access (hence Selenium). Write access, even to our own page, would require us to get our app reviewed by FB. 
1. Under *Products* select **Facebook Login** and enable for your app. 
1. Enable **Device Login** on the **Facebook Login** page, and add https://google.com as a Valid OAuth Redirect URI (this is a workaround for Facebook's silly requirements).
1. On the **Settings > Basic** page, copy the **App ID** and **App Secret** to the respective fields in the json config file. Do the same for the **Client Token** on the **Settings > Advanced** page:
```
    "fb_api": {
        ...
        "app_id": "00000000000000000000",
        "app_secret": "0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a",
        "client_token": "0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a",
        ...
    },
```

### Google Sheets API
*This set of instructions is verbatim plaigiarised from [ https://developers.google.com/sheets/api/quickstart/python ].*

1. Create a google developer account. 
1. Use this wizard [ https://console.developers.google.com/start/api?id=sheets.googleapis.com ] to create or select a project in the Google Developers Console and automatically turn on the API. Click Continue, then Go to credentials.
1. On the Add credentials to your project page, click the Cancel button.
1. At the top of the page, select the OAuth consent screen tab. Select an Email address, enter a Product name if not already set, and click the Save button.
1. Select the Credentials tab, click the Create credentials button and select OAuth client ID.
1. Select the application type Other, enter the name `Sheets fpm API hook`, and click the Create button.
1. Click OK to dismiss the resulting dialog.
1. Click the file_download (Download JSON) button to the right of the client ID.
1. Move this file to your working directory for `fpm` and rename it `sheets_client_secret.json`.


## Config File
Your config file should look something like the two examples provided in the repository, and should be named config.json and sit in the `fpm` working directory. It follows standard json notation and formatting.

#### fpm section
The fpm section contains general configuration values for the utility, including the location of a program state file, location of a desired post template (see templates section below) and a timestamp format for timestamps printed into posts (following strftime format conventions). 
```
    "fpm": {
        "state_file": "fpm.state.pickle",
	       "post_format": "templates/feb.tmpl",
        "timestamp_format": "%d/%m/%Y %H:%M"
    },
```

#### Facebook Graph API section
Configuration for FB graph API. The `enable` flag enables fetching facebook messages as potential posts. The `page_id` stores the facebook page id of the page we want to post to and fetch messages from. This can be found using various online tools.
```
    "fb_api": {
        "enable": true,
        "app_id": "0000000000000000",
        "app_secret": "0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a",
        "client_token": "0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a",
        "page_id": "0000000000000000"
    },
```

#### Google Sheets API section
Configuration for Sheets API. Again, `enable` turns on or off functionality to fetch sheets rows as potential posts. `spreadsheet_id` refers to the id of the google sheet to fetch data from (can be found in URL of spreadsheet). The `api_key` parameter should be filled with the API key of the app you set up earlier. The `column_range` field specifies a range of columns to fetch data from. The `column_mappings` field specifies a named mapping for each column in the range. 

The following named mappings carry special significance:
 - `content`: should generally be used for main content of posts. Facebook messages will be mapped to just `content`.
 - `timestamp`: should contain a standard-format timestamp to be included in posts. 
 - `credit`: has some inbuilt format hacks (i.e. an added dash) necessary for Frigid Engo Boii posts.
```
    "sheets_api": {
        "enable": true,
        "api_key": "0az0az0az0az0az0az0az0az0az0az0az0az0az0az0az0az",
        "spreadsheet_id": "0az0az0az0az0az0az0az0az0az0az0az0az0az0az0az0az",
        "column_range": "A:F",
        "column_mappings": 
            ["timestamp", "content", "credit", "topic", "response", "code"]
    },
```

#### Selenium section
Here you want to specify the python module and driver executable path corresponding to your specific webdriver. For example, for the Chrome webdriver on OS X it looks something like this:
```
    "selenium": {
        "python_module": "selenium.webdriver.chrome.webdriver",
        "driver_path": "/Applications/chromedriver"
    }
```

## Program State File
You will need to generate a starting state file for your program, to specify initial options. Use the `fpm_stategen` utility to do so. Most options are well-explained in the help output (i.e. `fpm_stategen --help`)
```
Usage: fpm_stategen [OPTIONS]

  Script to generate a new fpm state file or modify the values stored in an
  existing one.

Options:
  -n, --new                       Create new state file with default values
  -e, --edit PATH                 Edit existing state file given as argument
  -s, --sheets-row INTEGER        Overwrite value of 'current_sheets_row' in
                                  state.
                                  This argument allows setting of a
                                  starting point when reading post lists from
                                  google sheets documents to avoid having to
                                  fetch and scan the entire document.
  -p, --post-number INTEGER       FORMAT: "year-month-dayThour:minute:second"
                                  e.g. "2018-01-01T13:10:12"
                                  Overwrite value
                                  of 'current_post_number' in state.
                                  This
                                  argument allows the current post number to
                                  be modified; future posts will be enumerated
                                  from this value
  -i, --ignore-messages-older-than TEXT
                                  Overwrite value of
                                  'ignore_messages_older_than' in state.
                                  This
                                  argument sets a starting point for new posts
                                  to be read from. Any sheets or fb graph data
                                  older than this value will be ignored when
                                  creating post lists.
  -o, --output-file PATH          File to output new state to.
  -q, --post TEXT                 Add additional post hashes to existing
                                  hashset in state.
                                  This argument allows
                                  additional post hashes to be stored,
                                  ensuring duplicate posts with the same hash
                                  will not be added to post lists.
  --help                          Show this message and exit.
```

An example of such a command is below; it generates a new state file for use by `fpm` that constrains it to only look for posts past row 1000 of a sheets document, sets the starting post number to 1500, and ignores messages older than the 13th May 2018, saving this state file to `fpm.state.pickle` as specified in our config:
```
fpm_stategen -n -o fpm.state.pickle -s 1000 -p 1500 -i "2018-05-13T00:00:00"
```
*(If you are using a virtualenv, make sure it is loaded so fpm's commands are exposed on the path)*

Existing states can be edited using `-e`.

## Post Template Files
Your config must specify a post template file. A couple examples exist in the `templates` directory. 

Template files are essentially valid `format()` strings for Python's string format utility. Any field specified in `column_mappings` in your config file will be referenced. Any field that cannot be found will be ignored, and an empty string will silently be substituted. 

Since Facebook messages do not have a multiple-field structure, they will only provide `content` and `timestamp` fields. 

The `post_number` field is always available, and provides a numeric iteration of accepted posts. The {timestamp} field will be formatted as specified in the config file.

An example template file might look like:
*template.tmpl*
```
#{post_number}

{content}

Submitted [{timestamp}]
```

## Running `fpm`
A quick double check at this point:
1. You've installed all dependencies and fpm itself.
1. Facebook Graph and Google Sheets API's are set up (if enabled in config).
1. You have a valid config file stored in the working directory as `config.json`.
1. You have a valid initial program state file generated using `fpm_stategen`. 
1. You have set up and chosen a suitable template.

Start the (currently mostly garbage) fpm command line interface by invoking 
```
fpm_cli
```
*(If you are using a virtualenv, make sure it is loaded so fpm's commands are exposed on the path)*

The first time you run fpm, it will need to authenticate with all the APIs we set up. It will print out instructions on the command line interface to navigate to facebook.com/device and allow access to your page by your previously set-up facebook app. It will also either attempt to start a browser or print instructions on the command line to allow access to your google account by your previous set-up google app.

Next it will generate an interal post-list from the data collected from both sources, and order by the `timestamp` field. Once completed, it will start Selenium, and you will see a new browser window open. It will navigate to the Facebook login page, and ask you to login. After login, follow the command-line instructions to continue. 

For each post identified, it will open your page, input the post into the text field, then ask for confirmation before posting. You can modify the post in-browser, then type 'y' on the command line and hit enter for the post to be posted. Upon hitting enter again, you will continue to the next post. 

Once no posts remain, the program will terminate. Alternatively, you can use <ctrl-c> at any time to terminate. Program state is saved after each post is successfully posted. As a result, any incomplete/unfinished posts **will** be re-visited the next time the program runs and you will be given a chance to post them. If you select 'n' and opt out of posting any post, your choice will be saved, and the post will be ignored on future runs of the program.
