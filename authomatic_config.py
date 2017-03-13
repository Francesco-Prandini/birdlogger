# -*- coding: utf-8 -*-
"""
Keys with leading underscore are our custom provider-specific data.
"""

from authomatic.providers import oauth2, oauth1
import authomatic
import copy

DEFAULT_MESSAGE = 'Have you got a bandage?'

SECRET = '###########'

DEFAULTS = {
    'popup': True,
}


OAUTH2 = {
    
    'facebook': {
           
        'class_': oauth2.Facebook,
        'consumer_key': '1197024583728530',
        'consumer_secret': 'cbe80370ce39fe484d1ca4f1bc850af5',
        'id': authomatic.provider_id(),
        'scope': ['email', 'user_about_me', 'user_birthday','user_location'],
        '_apis': {'Get your recent statuses': ('GET', 'https://graph.facebook.com/{user.id}/feed'),
        'Share this page': ('POST', 'https://graph.facebook.com/{user.id}/feed?message={message}&link=http://authomatic-example.appspot.com','Enter comment', 'This app is ...')
        
        }
    }
    
}

# Concatenate the configs.
config = copy.deepcopy(OAUTH2)
config['__defaults__'] = DEFAULTS
