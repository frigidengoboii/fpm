import signal, sys, click

from fpm.controller.controller import FpmController
from fpm.graph.api import GraphApi

global_controller = None

CLS='\033[H\033[J'

@click.command()
@click.option('-c', '--config', type=click.Path(exists=True, readable=True),
        default='config.json', 
        help='Config file location. Defaults to \'config.json\' in local '
        'directory')
def crap_line_interface(config):
    '''
    fpm Command Line Interface

    Currently pretty trash, but it does the job. On startup, generates post
    list from specified locations (google sheets document, facebook message
    log) in config file. This may require authenticating with Facebook's
    device login feature (follow command line instructions) and with Google
    sheets API (again follow command line instructions). 

    Once postlist is fetched and parsed, Selenium will start. Log into 
    facebook when prompted (if cookies haven't already been stored). Then 
    each post will be pre-filled into Facebook's post field. Edit the post
    if necessary, then use the COMMAND LINE to post (i.e. type y and hit
    enter). This ensures no desync during program flow. Program terminates 
    when end of postlist is reached. 

    You can terminate at any point using <ctrl-c>. If so, the current post
    will not be marked as finished, and the program will resume there next
    time.
    '''
    print('::WARNING::\nThis CLI implementation is utter garbage and only '
            'suitable for testing and masochism purposes.\nUse at own risk')
    signal.signal(signal.SIGINT, signal_handler)

    controller = FpmController(config)
    global_controller = controller

    postlist = controller.setup(GraphApi.device_login)
    controller.setup_selenium(login_prompt)
    
    for post in postlist:
        controller.process_post_selenium(post, cli_confirmation, cli_success)

    controller.stop_selenium()

def signal_handler(signal, frame):
    if global_controller and global_controller.selenium:
        global_controller.stop_selenium()
    sys.exit(1)

def cli_confirmation(post):
    print(CLS)
    print(post['_repr'])
    print('----------------------------------------------------------')
    conf = input('Would you like to post the above? Y/n? ')
    return ('y' in conf or 'Y' in conf)
    
def cli_success(post):
    print('----------------------------------------------------------')
    print('Post successfully posted!\n')
    conf = input('Press enter to continue... ')
    return
    
def login_prompt():
    print('----------------------------------------------------------')
    conf = input('Please log in to Facebook, then press enter to continue...')
    return

