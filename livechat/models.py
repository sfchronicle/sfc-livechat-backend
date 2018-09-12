# chat/models.py

import re
import slackdown
import json
from livechat import managers
from django.db import models


class ChatChannel(models.Model):
    """
    A Slack channel logged by this application.
    """
    channel_id = models.CharField(
        unique=True,
        max_length=255,
        help_text="The id of the channel on Slack."
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text="A slug for the HTML story."
    )
    headline = models.CharField(
        max_length=255,
        help_text="Display headline for the channel."
    )
    description = models.TextField(
        max_length=1000,
        help_text="HTML for the introductory content.",
        blank=True,
    )
    live_content = models.TextField(
        max_length=1000,
        help_text="HTML for the live content.",
        blank=True,
    )

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        from livechat import tasks

        super(ChatChannel, self).save(*args, **kwargs)

        tasks.publish_json(self.channel_id)



class ChatUser(models.Model):
    """
    A Slack user that creates messages.
    """
    user_id = models.CharField(
        max_length=255,
        unique=True
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        help_text='The Slack username'
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        help_text="The user's title"
    )
    real_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="The user's real name from Slack",
    )
    image_24 = models.URLField(max_length=1000)
    image_32 = models.URLField(max_length=1000)
    image_48 = models.URLField(max_length=1000)
    image_72 = models.URLField(max_length=1000)
    image_192 = models.URLField(max_length=1000)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.display_name

    # dynamic property
    @property
    def display_name(self):
        """
        Return `real_name` or `name` if there is no `real_name`.
        """
        return self.real_name or self.name


class ChatMessage(models.Model):
    """
    A Slack message posted to a channel by a user.
    """
    ts = models.CharField(
        max_length=255,
        help_text='Timestamp of the original message used by Slack as unique identifier.'
    )
    user = models.ForeignKey(
        ChatUser,
        on_delete=models.CASCADE,
        help_text='Slack user the message was posted by.'
    )
    channel = models.ForeignKey(
        ChatChannel,
        on_delete=models.CASCADE,
        help_text='Slack channel the message was posted in.'
    )
    data = models.TextField(
        max_length=6000,
        help_text="The message's data"
    )
    live = models.BooleanField(
        default=True,
        help_text='Is this message live, or was it deleted on Slack?'
    )
    thread_id=models.CharField(
        max_length=255,
        help_text='The ID of the original message for this thread.',
        default=''
    )
    html = models.TextField(
        max_length=3000,
        help_text='HTML code representation of the message.'
    )
    override_text = models.TextField(
        max_length=3000,
        blank=True,
        help_text="Override the message by putting text here."
    )

    # See next section for these managers
    objects = models.Manager()
    messages = managers.ChatMessageManager()

    class Meta:
        ordering = ("-ts",)
        get_latest_by = "ts"

    def __str__(self):
        return self.ts

    def replace_with_names(self, match):
        # Get raw ID
        stripped_id = match.strip(" <>@")

        if ChatUser.objects.filter(user_id=stripped_id).exists():
            # If we can find the user in the database, return real name
            user_obj = ChatUser.objects.get(user_id=stripped_id)
            name = user_obj.display_name
            # Temp formating to call out ID but exempt it from Slackdown (which targets angle brackets)
            return u"###{}###".format(name)
        else:
            # If no user found, return a blank string
            return u""


    def format_id_as_html(self, match):
        # Remove message padding
        name = match.strip("#")
        return u" <span class='chat-mention'>{}</span> ".format(name)


    def update_html(self):
        """
        Updates the html field with the Slack data or
        with the override_text if it's not blank.
        """
        
        if self.override_text != '':
            override_text_obj = {
                'text': self.override_text
            }
            self.html = slackdown.parse(override_text_obj)
        else:
            parsed_data = json.loads(self.data)
            # convert user references with full names (or usernames as a fallback)
            parsed_data['text'] = re.sub('<@([\w\d]*)>', lambda m: self.replace_with_names(m.group()), parsed_data['text'])
            # Hit it with slackdown
            self.html = slackdown.parse(parsed_data)
            # Modify message text to put underscores back in
            self.html = re.sub(r'<i>|</i>', '_', self.html)
            # Modify message text to put ID callouts back in
            self.html = re.sub('###(.*?)###', lambda n: self.format_id_as_html(n.group()), self.html)


    def save(self, *args, **kwargs):
        self.ts = json.loads(self.data)['ts']
        self.update_html()
        super(ChatMessage, self).save(*args, **kwargs)

        # This should go underneath the call to super()
        from .tasks import publish_json 
        publish_json(self.channel.channel_id)

