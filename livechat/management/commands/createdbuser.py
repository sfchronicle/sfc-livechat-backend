#!/usr/bin/env python

import os
from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError

class Command(createsuperuser.Command):
    help = 'Create a superuser'

    def handle(self, *args, **options):
        password = os.getenv('db_pass')
        username = os.getenv('db_user')
        database = 'django_db'

        if createsuperuser.get_user_model().objects.filter(username=os.getenv('db_user')):
            print('Superuser already exists. SKIPPING...')
        else:
            super(Command, self).handle(*args, **options)

            print('Creating superuser for this app...')
            user = self.UserModel._default_manager.db_manager(database).get(username=username)
            user.set_password(password)
            user.save()
            print('Superuser created!')
