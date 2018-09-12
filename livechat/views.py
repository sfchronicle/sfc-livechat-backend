# chat/views.py

from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt

from livechat.models import ChatChannel, ChatMessage
from django.http import JsonResponse
from django.test.client import RequestFactory
from django.utils.decorators import classonlymethod
from django.http import Http404

class ChatJson(View):
    """
    Local JSON feed for a particular Chat channel and its messages.
    """
    @classonlymethod
    def as_string(self, object, live_only=True):
        """
        Renders and returns the JSON response as a plain string.
        """
        request = RequestFactory().get('')
        response = self.as_view()(request, channel=object.channel_id, live_only=live_only)
        return response.content

    def get_chat_messages(self, channel, live_only=True):
        """
        Get all the messages from channel not marked as deleted.
        """
        if ChatChannel.objects.filter(channel_id=channel).exists():
            self.channel = ChatChannel.objects.get(channel_id=channel)
            if live_only == True:
                self.messages = ChatMessage.messages.live().filter(
                    channel__channel_id=channel
                )
            else:
                self.messages = ChatMessage.messages.filter(
                    channel__channel_id=channel
                )
            return True
        else:
            return False

    def get_json(self):
        """
        Creates the JSON feed structure with the necessary elements.
        """
        output_messages = []
        for message in self.messages:
            output_message = {
                'html': message.html,
                'ts': message.ts,
                'user': {
                    'image_48': message.user.image_48,
                    'display_name': message.user.display_name,
                    'title': message.user.title
                }
            }
            # Add to JSON output if thread ID exists
            if (message.thread_id != ''):
                output_message['thread_id'] = message.thread_id

            output_messages.append(output_message)

        return JsonResponse({
            'channel': {
                'id': self.channel.channel_id,
                'headline': self.channel.headline,
                'slug': self.channel.slug,
                'description': self.channel.description,
                'live_content': self.channel.live_content,
            },
            'messages': output_messages
        })

    def get(self, request, *args, **kwargs):
        """
        Returns the latest JSON feed.
        """
        check_live = True
        if 'live_only' in self.kwargs:
            check_live = self.kwargs['live_only']

        if self.get_chat_messages(self.kwargs['channel'], check_live):
            return self.get_json()
        else:
            raise Http404("Channel does not exist")