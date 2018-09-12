# chat/tasks.py

import re
import json
import os
from livechat import views as chat_views
from livechat.models import ChatChannel, ChatUser, ChatMessage
from django.conf import settings
from django.http import HttpResponse

CHAT_COMMENT_TAG = '&lt;#&gt;'


def new_message(channel, data):
    simple_text = data.get('text', '')
    # Bail out if the message text is blank 
    if (simple_text == ""):
        return False

    # By default, the thread ID is blank, unless we find one
    thread_id = ''
    if ('thread_ts' in data):
        thread_id = data['thread_ts']

    # Don't save if the chat comment tag is found
    comment_regex = r'^\s*{}'.format(CHAT_COMMENT_TAG)
    if not re.match(comment_regex, simple_text):
        user, c = ChatUser.objects.get_or_create(
            user_id=data['user']
        )
        m = ChatMessage(
            data=json.dumps(data),
            user=user,
            channel=channel,
            thread_id=thread_id,
            # This will prevent the message from going live on post
            # Comment this out to revert to immediate posting
            # live=False
        )

        # Scan chat string for this ts -- if it doesn't exist already, save
        # False scans even not-live posts
        json_string = str(chat_views.ChatJson.as_string(channel, False))

        if str(data['ts']) not in json_string:
            # Only save if it's unique to prevent Slack's weird duplicate POSTs
            m.save()
        else:
            # This is either a weird Slack artifact or it's a Reaction
            # If it's the right reaction, flip it live
            # print(data['reaction'])
            if 'reaction' in data and data['reaction'] == 'white_check_mark':
                m = ChatMessage.objects.get(ts=data['ts'])
                m.live = True
                m.save()


def update_message(data):
    m = ChatMessage.objects.get(ts=data['message']['ts'])
    m.data = json.dumps(data['message'])
    m.save()


def delete_message(data):
    try:
        m = ChatMessage.objects.get(ts=data['deleted_ts'])
    except ChatMessage.DoesNotExist:
        m = None
    if m:
        m.live = False
        m.save()


def publish_json(channel_id):
    """
    Render and publish a JSON feed representation of a channel
    to a local file
    """
    # Get the Channel obj
    channel = ChatChannel.objects.get(channel_id=channel_id)

    # Get the JSON from the ChatJson and convert to JSONP
    json_string = chat_views.ChatJson.as_string(channel)
    jsonp_string = "%s(%s);" % ("callback", json_string)

    # Used for development or small server load.
    # Consider uploading to a server bucket instead for optimal performance.
    with open(os.path.join(settings.ROOT_DIR, 'livechat', '.json', '%s.jsonp' % channel_id), 'w') as f:
        f.write(jsonp_string)



