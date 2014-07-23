from pyramid.config import Configurator
from pyramid.events import subscriber
from pyramid.events import NewRequest
from airsci_netstatus.resources import Root
from pymongo import MongoClient
import pymongo
import datetime

try:
    # for python 2
    from urlparse import urlparse
except ImportError:
    # for python 3
    from urllib.parse import urlparse

from gridfs import GridFS
import pymongo

def main(global_config, **settings):
    """ This function returns a WSGI application.
    """
    config = Configurator(settings=settings, root_factory=Root)
    config.include('pyramid_chameleon')
    config.add_view('airsci_netstatus.views.my_view',
                    context='airsci_netstatus:resources.Root',
                    renderer='airsci_netstatus:templates/home.pt'
		    )
    config.add_route('detail', '/{hostname}')
    config.add_view('airsci_netstatus.views.detail',
                    context='airsci_netstatus:resources.Root',
                    renderer='airsci_netstatus:templates/detail.pt',
		    route_name = 'detail'
		    )
    config.add_route('addhost', '/add/host')
    config.add_view('airsci_netstatus.views.add',
                    context='airsci_netstatus:resources.Root',
                    renderer='airsci_netstatus:templates/add.pt',
		    route_name = 'addhost'
		    )
    config.add_route('addservice', '/add/service')
    config.add_view('airsci_netstatus.views.add',
                    context='airsci_netstatus:resources.Root',
                    renderer='airsci_netstatus:templates/add.pt',
		    route_name = 'addservice'
		    )
    config.add_route('edit', '/{hostname}/edit')
    config.add_view('airsci_netstatus.views.edit',
                    context='airsci_netstatus:resources.Root',
                    renderer='airsci_netstatus:templates/edit.pt',
		    route_name = 'edit'
		    )
    config.add_static_view('static', 'airsci_netstatus:static')

    config.scan('airsci_netstatus')

    return config.make_wsgi_app()
