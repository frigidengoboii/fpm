from datetime import datetime, timezone
import pytz
from tzlocal import get_localzone
from collections import defaultdict

FB_DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
SHEETS_DATETIME_FORMAT = '%d/%m/%Y %H:%M:%S'

def messages_to_postlist(messages, page_id=None,
        ignore_messages_older_than=datetime.utcfromtimestamp(0)):
    if not ignore_messages_older_than.tzinfo:
        ignore_messages_older_than = (
                ignore_messages_older_than.replace(tzinfo=timezone.utc)
            )
    for conv in messages:
        if (datetime.strptime(conv['updated_time'], FB_DATETIME_FORMAT) 
                < ignore_messages_older_than):
            continue
        for message in conv['messages']['data']:
            timestamp = datetime.strptime(
                    message['created_time'],
                    FB_DATETIME_FORMAT
                    )
            if timestamp < ignore_messages_older_than:
                break
            if page_id and message['from']['id'] == page_id:
                continue
            post = defaultdict(str)
            post['timestamp'] = timestamp
            post['content'] = message['message']
            if 'attachments' in message:
                post['attachments'] = message['attachments']['data']
            post['link'] = conv['link']
            yield post

def sheets_to_postlist(sheet, mappings, 
        ignore_messages_older_than=datetime.utcfromtimestamp(0)):
    for row in sheet:
        post = defaultdict(str)
        if 'timestamp' in mappings:
            try:
                ts = datetime.strptime(
                        row[mappings.index('timestamp')], 
                        SHEETS_DATETIME_FORMAT
                    )
                dts = get_localzone().localize(ts, is_dst=None)

            except ValueError as ve:
                continue
            if dts < ignore_messages_older_than:
                continue
            post['timestamp'] = dts

        for i, m in enumerate(mappings):
            if not m or m == 'timestamp':
                continue
            else:
                post[m] = row[i]
        yield post


