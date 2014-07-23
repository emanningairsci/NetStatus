from pyramid.httpexceptions import HTTPFound
from pyramid.renderers import get_renderer
from pyramid.view import view_config
from pyramid.response import Response
import airsci_netstatus.resources
from airsci_netstatus.readdb import readDB
import pymongo
from pymongo import MongoClient



def dashboard(request):
    return {'project':'airsci_netstatus'}

def my_view(request):
    #| create a "home page" with a table of monitored hosts and their
    #| current status (ping response), timestamp, uptime or downtime
    read_data = readDB()
    online_hosts = read_data.get_online_hosts()
    offline_hosts = read_data.get_offline_hosts()
    return dict( online_hosts = online_hosts, offline_hosts = offline_hosts)

def detail(request):
    #| create a page detailing each host's services, percent uptime, and thier uptime history
    hostname = request.matchdict['hostname']
    read_data = readDB()
    history_data = read_data.get_host_history(hostname)
    service_data = read_data.get_host_services(hostname)
    host_data = read_data.get_host_status(hostname)
    uptime_percent = read_data.get_uptime_percent(hostname)
    return dict(hostname = hostname, history_data = history_data, service_data = service_data, host_data = host_data, uptime_percent = uptime_percent)

def add(self, request):
    #| create a page to add a new host and its IP
    home = "http://0.0.0.0:8080"
    if 'submit' in request.params:
        new_host = str(request.GET['new_host'])
        new_ip = str(request.GET['new_ip'])
        read_data = readDB()
        result = read_data.add_host(new_host, new_ip)
    return dict(home = home)

def edit(request):
    read_data = readDB()
    hostname = request.matchdict['hostname']
    host_data = read_data.get_host_status(hostname)

    if 'delete' in request.params:
        new_hostname = str(request.GET['new_hostname'])
        read_data = readDB()
        read_data.delete_host(new_hostname)

    elif 'save' in request.params:
       new_hostname = str(request.GET['new_hostname'])
       new_ip_addr = str(request.GET['new_ip_addr'])
       serv_name = str(request.GET['new_service'])
       serv_type = str(request.GET['new_serv_type'])
       try:
           remove_service = request.GET['remove_service']
       except LookupError:
           remove_service = "off"
       read_data = readDB()
       read_data.edit_host(hostname, new_hostname, new_ip_addr, serv_name, serv_type, remove_service)
        
    return dict(hostname = hostname, host_data = host_data)
