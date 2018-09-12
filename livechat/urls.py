# chat/urls.py

from django.conf.urls import url
from django.contrib import admin
from livechat import views as chat_views

import os
from django.conf import settings
from django.views.static import serve

# Run the init code in new thread
# import threading
# t = threading.Thread(target=one_time_startup.threadConnect)
# t.start()

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # url(
    #     r'^slack/',
    #     chat_views.SlackEventWebhook.as_view(),
    #     name='slack-event-webhook'
    # ),
    url(
        r'^api/(?P<channel>.*)$',
        chat_views.ChatJson.as_view(),
        name='chat_api'
    ),
    url(r'^json/(?P<path>.*)$', serve, {
        'document_root': os.path.join(settings.ROOT_DIR, 'livechat', '.json'),
        'show_indexes': True,
    }),
]
