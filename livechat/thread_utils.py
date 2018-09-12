from slackclient import SlackClient
from .events import SlackEventHandler
import requests
import os
import time
import sys

slack_token = os.getenv('slack_bot_token')
sc = SlackClient(slack_token)
app_slack_token = os.getenv('slack_app_token')
app_sc = SlackClient(app_slack_token)
wait_emoji = "clock1"
placeholder_img = os.getenv('placeholder_img')
photo_drop_url = os.getenv('photo_drop_url')
photo_domain = os.getenv('photo_domain')

def rtmConnect():
	if sc.rtm_connect(with_team_state=False, auto_reconnect=True):
		while (True):
			# Run it forever!
			try:
				# Try to print from feed
				SlackEventHandler().handle(sc.rtm_read())
			except Exception as e: 
				# Print exception and exit thread
				print(e)

		  # Delay and run again	
			time.sleep(0.5)
			print("Scanning...")
	else:
		print("Connection failed")


def checkImageUpload(source_id, payload, im_width):
	# Loop until we get a result
	result = None
	result_count = 0
	# Add initial emoji to indicate it's processing
	sc.api_call(
	  "reactions.add",
	  channel=payload['channel'],
	  name=wait_emoji,
	  timestamp=payload['event_ts']
	)
	# Add the thread placeholder so we can swap in media later
	thread_msg = sc.api_call(
	  "chat.postMessage",
	  channel=payload['channel'],
	  thread_ts=payload['event_ts'],
	  text='caption: '+payload['text']+'\n'+placeholder_img,
	  as_user=True
	)
	# Get the thread message ID
	thread_msg = thread_msg['ts'];

	while result is None:

		if result_count > 30:
			# If we've retried for 1.5 minutes, bail out
			result = False
			# Send fail emoji to original message
			sc.api_call(
			  "reactions.add",
			  channel=payload['channel'],
			  name="x",
			  timestamp=payload['event_ts']
			)
			# Remove the wait emoji 
			sc.api_call(
			  "reactions.remove",
			  channel=payload['channel'],
			  name=wait_emoji,
			  timestamp=payload['event_ts']
			)
			# Exit thread
			result = False

		# Try and get the image from WCM
		uploading_image = requests.get(photo_drop_url+source_id+'&class=photo')

		# React when the file is finished
		if uploading_image.status_code == 200 and 'wcmId' in uploading_image.json():
			# If we have a wcmId, try to get the image and send updates
			try:
				wcm_id = uploading_image.json()['wcmId']
				image_url = photo_domain+'0/0/0/'+wcm_id+'/3/'+str(im_width)+'x0.jpg'

				# # Don't do this, but leave in case we want later
				# # Go get the latest version of the message in case it was updated during upload
				# latest_msg = app_sc.api_call(
				#   "groups.history",
				#   channel=payload['channel'],
				#   latest=payload['event_ts'],
				#   inclusive=True,
				#   count=1	
				# )
				# new_text = latest_msg['messages'][0]['text'];
				# Remove placeholder image from text
				# new_text = new_text.replace('<https://projects.sfchronicle.com/shared/assets/chat-image-loading.jpg>', '')

				# Update the thread message and let RTM pick it up
				sc.api_call(
				  "chat.update",
				  channel=payload['channel'],
				  text='caption: '+payload['text']+'\n'+image_url,
				  ts=thread_msg,
				  as_user=True
				)
				# Send success emoji to original message
				sc.api_call(
				  "reactions.add",
				  channel=payload['channel'],
				  name="rocket",
				  timestamp=payload['event_ts']
				)
				# Remove the wait emoji 
				sc.api_call(
				  "reactions.remove",
				  channel=payload['channel'],
				  name=wait_emoji,
				  timestamp=payload['event_ts']
				)
				# Exit thread
				result = True
			except Exception as e: 
				# Print exception and exit thread
				print(e)
				result = False
		else:
			# Retry and increment
			result_count += 1;
			print("RETRYING " +str(result_count)+"...")

			# Delay and run again	
			time.sleep(3)