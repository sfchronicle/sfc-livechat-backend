#!/bin/bash

sh -c './manage.py makemigrations livechat && ./manage.py migrate && ./manage.py createdbuser && ./manage.py updateusers --verbose && ./manage.py runserver 0.0.0.0:8000 & ./manage.py rtm'
