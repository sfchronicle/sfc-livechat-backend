# SFC Live Chat Backend

A Django-based system for reading in the RTM traffic from chosen Slack channels and filling out a database. An API endpoint creates a JSON file for rendering via any front-end system of your choice. All of this is rolled up and deployable as a Docker container.

This backend is a modfied version of the one from Andrew Briz's great tutorial here: https://source.opennews.org/articles/how-we-publish-live-chats-slack/

Give that a read as this setup requires many of the same concepts. Main changes made beyond Andrew's template:
- Everything runs on Docker. 
- The codebase uses Python3.
- Our backend is hosted on a internal server, so it cannot receive POST requests. To accomodate that, this build uses Slack's RTM API to ask repeatedly for the latest messages. It should work whether your backend server is public or private.
- Added functionality to delay posting of a message until an emoji is given to it. By default, this is turned off, but it could be turned on easily.
- Added image upload functionality from within Slack. The upload prompts the server to download the photo and send it to an FTP drop for upload to our CMS, but you could customize this to hit whatever service is desired.

## Getting started locally

1. Download Docker https://www.docker.com/get-started
1. Create a Slack app for your organization where the live chat will happen (follow Andrew's tutorial if you need a walkthrough on that, but see the list below for additional permissions the app will need)
1. Clone the repo to your code directory
1. Add the keys to the `env_template` file and rename it `.env`
  - secret_key should be a Django secret -- you can generate one on the command line like this `python -c 'import random; result = "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)]); print(result)'`
  - slack_app_token/slack_bot_token/slack_verification_token are keys you are given when creating a Slack app
  - db_user/db_pass are your choice, but should match the credentials for your database (we use MySQL, but anything Django integrates with should work)
  - db_host is the IP where your database is accessible
  - placeholder_img is an image URL that displays while your real image is uploading
  - photo_drop_url is where you expect the final photo will appear (if you have the luxury of a CMS that will just respond when an image is done uploading, you might not need to poll this)
  - photo_domain is the root domain where your photos are hosted
  - ftp_server/ftp_username/ftp_password/ftp_directory are self-explanatory 

Once that's all done, run `docker-compose up` from your project folder to start the backend locally. You should be able to access the Django backend by going to `localhost:8000/admin`. 

New chat channels can be created through this interface, and if the channel ID matches one of your workspace's channels, that chatter there will become messages in the backend. 

To get the JSON representation of the channel, go to `http://localhost:8000/api/<your channel ID here>`

## Permissions for the Slack app

Make sure you bundle the app with a bot that will allow the app to post messages as a user in Slack.

Add the following permissions for your Slack app so the backend can work properly:
```
chat:write:bot
chat:write:user
groups:history
groups:read
groups:write
files:write:user
bot
reactions:read
users:read
channels:read
channels:history
channels:read
```
