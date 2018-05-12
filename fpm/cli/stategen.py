'''
    fpm State generator/editor script
        Generates/Edits state files for fpm
'''
import click
from datetime import datetime
from tzlocal import get_localzone
import pytz

from fpm.controller.state import FpmState

@click.command()
@click.option('-n', '--new', is_flag=True,
        help='Create new state file with default values')
@click.option('-e', '--edit', type=click.Path(exists=True, readable=True), 
        default='fpm.state.pickle',
        help='Edit existing state file given as argument')
@click.option('-s', '--sheets-row', type=int, default=None,
        help='Overwrite value of \'current_sheets_row\' in state.\n'
        'This argument allows setting of a starting point when reading '
        'post lists from google sheets documents to avoid having to fetch '
        'and scan the entire document.')
@click.option('-p', '--post-number', type=int, default=None,
        help='FORMAT: "year-month-dayThour:minute:second"'
        '    e.g. "2018-01-01T13:10:12"\n'
        'Overwrite value of \'current_post_number\' in state.\n'
        'This argument allows the current post number to be modified; future '
        'posts will be enumerated from this value')
@click.option('-i', '--ignore-messages-older-than', type=str, 
        default=None,
        help = 'Overwrite value of \'ignore_messages_older_than\' in state.\n'
        'This argument sets a starting point for new posts to be read from. '
        'Any sheets or fb graph data older than this value will be ignored '
        'when creating post lists.')
@click.option('-o', '--output-file', type=click.Path(writable=True), 
        default='fpm.state.pickle',
        help = 'File to output new state to.')
@click.option('-q', '--post', type=str, multiple=True,
        help = 'Add additional post hashes to existing hashset in state.\n'
        'This argument allows additional post hashes to be stored, ensuring '
        'duplicate posts with the same hash will not be added to post lists.')
def stategen(new, edit, sheets_row, post_number, ignore_messages_older_than,
        output_file, post):
    '''
    Script to generate a new fpm state file or modify the values stored in an
    existing one.
    '''
    if new:
        state = FpmState()
    else:
        state = FpmState.load(edit)

    if sheets_row:
        state.current_sheets_row = sheets_row
    if post_number:
        state.current_post_number = post_number
    if ignore_messages_older_than:
        ts = datetime.strptime(ignore_messages_older_than, 
                '%Y-%m-%dT%H:%M:%S')
        dts = get_localzone().localize(ts, is_dst=None)
        state.ignore_messages_older_than = dts

    if post is not None:
        state.posts = state.posts.union(set(post))

    state.save(output_file)


