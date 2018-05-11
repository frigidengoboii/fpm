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

Run SetupTools installer
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
Your config file should look something like the two examples provided in the repository, and should be named config.json and sit in the `fpm` working directory.

#### Selenium section
Here you want to specify the python module and driver executable path corresponding to your specific webdriver. For example, for the Chrome webdriver on OS X it looks something like this:
```
    "selenium": {
        "python_module": "selenium.webdriver.chrome.webdriver",
        "driver_path": "/Applications/chromedriver"
    }
```

## 
