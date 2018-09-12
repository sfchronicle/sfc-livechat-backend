# chat/events.py

import os
import json
import time
import requests
import threading
from PIL import Image
from django.conf import settings
from livechat import thread_utils
from slackclient import SlackClient
from concurrent.futures import ThreadPoolExecutor
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse

# Import channels into this file
from .models import ChatChannel
# Import tasks into this file
from .tasks import * 

app_slack_token = os.getenv('slack_app_token')
app_sc = SlackClient(app_slack_token)
placeholder_img = os.getenv('placeholder_img')
ftp_server = os.getenv('ftp_server')
ftp_username = os.getenv('ftp_username')
ftp_password = os.getenv('ftp_password')
ftp_directory =  os.getenv('ftp_directory')

class SlackEventHandler(object):
    def handle(self, request):
        """
        Handles a Slack events POST request.
        Returns an HttpResponse.
        """
        #payload = self.parse_request(request)
        # Parse the request body (if there is no body, just exit)
        if (len(request) == 0):
            return False
        else:
            # If it has content, set it to first item
            payload = request[0]

        # Determine correct handler function
        event_name = payload['type']
        event_function_name = 'event_%s' % event_name
        try:
            event_function = getattr(self, event_function_name)
        except AttributeError:
            return HttpResponse('SlackEventHandler: %s event does not exist.' % event_name, status=200)

        # Runs the handler function and return the response
        return event_function(payload)

    def event_message(self, payload, is_reaction=False):
        """
        Processes events with the type of "message"
        Returns 200 HttpResponse
        """
        data = payload

        if is_reaction == True:
            # Rearrange a few things so this object can be processed the same way
            channel_id = data['item']['channel']
            data['ts'] = data['item']['ts']
        else:
            channel_id = data['channel']

        channel = ChatChannel.objects.filter(channel_id=channel_id)  

        if channel:
            channel = channel[0]
            subtype = data.get('subtype', None)
            if subtype:
                # Prepare to call subtype function
                # We are doing this odd thing where we create the name of the function dynamically and then call it 
                # But admittedly it is incredibly efficient
                subtype_function_name = 'message_%s' % subtype
                try:
                    subtype_function = getattr(self, subtype_function_name)
                except AttributeError:
                    return HttpResponse(
                        'SlackEventHandler: %s event message subtype does not exist.' % subtype,
                        status=200
                    )
                # Call it here
                return subtype_function(channel, data)
            else:
                # We are preparing to add a new message!
                # Check for any photos included with this message
                # Only jpgs supported for now
                if 'files' in data and data['files'][0]['filetype'] in ['jpg']:
                    # Only grab first photo
                    new_file = data['files'][0]

                    # Make download request to private URL (this will take 1 minute +
                    file_url = self.download_file(new_file['url_private'], payload)

                    # Add a blank message if there's no message
                    # Required so that the next updates don't get blocked
                    if (len(data['text']) == 0):
                        data['text'] = " "
                
                    # Update message with placeholder image
                    app_sc.api_call(
                      "chat.update",
                      channel=payload['channel'],
                      text=placeholder_img+'\n'+'caption: '+data['text'],
                      ts=payload['event_ts']    
                    )
                    
                    # Return 200, our swapped text will get picked up
                    return self.message_message_added(channel, data)
                else:
                    # Ignore thread messages (unless they are from our bot)
                    if 'thread_ts' not in data or 'bot_id' in data:
                        # This is a normal message (or a bot thread) - add it
                        return self.message_message_added(channel, data)

        return HttpResponse(status=200)

    def download_file(self, file_url, payload):
        # Set max width to constrain photos 
        maximum_width = 960;

        # Go fetch a file from Slack
        img_data = requests.get(file_url, headers={'Authorization': 'Bearer '+os.getenv('slack_bot_token')})

        # Get current time to stamp file
        file_id = 'SFLC'+str(int(time.time()))
        file_name = file_id+'-image.jpg'

        # Write file chunks to the system
        if img_data.status_code == 200:
            with open(file_name, 'wb') as f:
                for chunk in img_data:
                    f.write(chunk)

        # Use Pillow to resize the image if it's wider than maximum_width
        im = Image.open(file_name)
        im_width, im_height = im.size
        if (im_width > maximum_width):
            # Reduce width and height by same ratio
            ratio = maximum_width/im_width
            im.thumbnail((im_width*ratio, im_height*ratio), Image.ANTIALIAS)
            im.save(file_name, 'JPEG')
            # Set width for passing to image URL later
            im_width = maximum_width

        # Create unique upload ID
        os.system('exiftool -ProductID='+file_id+' '+file_name)
        # Optional for logging metadata:
        # os.system('exiftool -h image.jpg')

        # Init FTP session
        from ftplib import FTP
        session = FTP(ftp_server,ftp_username,ftp_password)

        # Change directory
        session.cwd(ftp_directory)

        # Special handling for FTP system
        file = open(file_name,'rb')
        session.storbinary('STOR '+file_name, file)
        file.close()    
        session.quit()

        # Clean up the temp file on the server if we can
        try:
            os.remove(file_name)
            os.remove(file_name+"_original")
        except Exception as e:
            # It's okay if this fails
            print(e)
            pass

        # Now that it's sent, we need to keep checking to see when it arrives
        executor = ThreadPoolExecutor(max_workers=5)
        future = executor.submit(thread_utils.checkImageUpload, file_id, payload, im_width)

        # Return path URL
        return True;

    def event_reaction_added(self, payload):
        self.event_message(payload, True)
        return HttpResponse(status=200)

    def message_message_added(self, channel, data):
        new_message(channel, data)
        return HttpResponse(status=200)

    def message_message_changed(self, channel, data):
        # Ignore thread messages (unless they are from our bot)
        if 'thread_ts' not in data or 'bot_id' in data:
            update_message(data)

        return HttpResponse(status=200)

    def message_message_deleted(self, channel, data):
        delete_message(data)
        return HttpResponse(status=200)
