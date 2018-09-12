#!/usr/bin/env python

import os
from livechat import thread_utils
import threading
from concurrent.futures import ThreadPoolExecutor
from django.core.management.base import BaseCommand
from django.core.management import CommandError

class Command(BaseCommand):
    help = 'Starts Slack RTM'

    def handle(self, *args, **options):
        # Run the init code in new thread
        executor = ThreadPoolExecutor(max_workers=5)
        future = executor.submit(thread_utils.rtmConnect)

        print('Starting RTM thread!')
