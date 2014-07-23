from pymongo import MongoClient
import pymongo
import datetime
import time

try:
    # for python 2
    from urlparse import urlparse
except ImportError:
    # for python 3
    from urllib.parse import urlparse

class readDB():
    #| initialize MongoDB settings
    client = MongoClient('localhost', 27017)
    #| The database name used for this app is 'netstatusDB'
    db = client.netstatusDB
    #| The collection used within that database is 'log'
    collection = db.log

    #|---------------------------------------------------------------------------------------------------------------
    #| add_host: updates the 'log, history, and services' collections with the given new_hostname and IP address. If
    #| the new_hostname matches one already in the collection, it will overwrite the existing hostname
    #| and IP parameters with the new parameters. Returns the write results of the DB query.
    #|---------------------------------------------------------------------------------------------------------------
    def add_host(self, new_hostname, new_ip):
        client = MongoClient('localhost', 27017)
        db = client.netstatusDB
        write_result_log = self.collection.update({"hostname": new_hostname}, {'$set': {"hostname": new_hostname, "IP": new_ip, "status": "", "uptime": 0, "downtime": 0} }, True )
        write_result_history = db.history.update({"hostname": new_hostname}, {'$set': {"hostname": new_hostname}}, True)
        write_result_services = db.services.update({"hostname": new_hostname}, {'$set': {"hostname": new_hostname}}, True )
        return write_result_log, write_result_history, write_result_services

    #|-------------------------------------------------------------------------------------------
    #| delete_host: deletes the given host from the 'log', 'services', and 'history' collection
    #|-------------------------------------------------------------------------------------------
    def delete_host(self, hostname):
        client = MongoClient('localhost', 27017)
        db = client.netstatusDB
        write_result_log = self.collection.remove({"hostname": hostname})
        write_result_history = db.history.remove({"hostname": hostname})
        write_result_services = db.services.remove({"hostname": hostname})
        return write_result_log, write_result_history, write_result_services


    #|--------------------------------------------------------------------------------------------------------------------
    #| edit_host: updates the 'log' collection with the given new_hostname and new IP address.
    #| A service is added if anything in the Service Name input box exists. A service is deleted if it matches the name
    #| in that box and the "remove this service" button is selected.
    #|--------------------------------------------------------------------------------------------------------------------
    def edit_host(self, hostname, new_hostname, new_ip, service, serv_type, remove_service):
        client = MongoClient('localhost', 27017)
        db = client.netstatusDB
        write_result = self.collection.update({"hostname": hostname}, {'$set': {"hostname": new_hostname, "IP": new_ip} }, True )
        write_result_history = db.history.update({"hostname": hostname}, {'$set': {"hostname": new_hostname} }, True )

        #| Edit the services
        status = "Unknown"
        if service != "":
            #| Make sure the host has been logged in this database collection before
            host_in_DB = db.services.find({"hostname": hostname}).count()
            if host_in_DB == 0:
                db.services.insert({"hostname": hostname})
    
            #| if the service has been logged before, update its status. Otherwise create a new subdocument
            #| in 'services' for that host
            matching_service = db.services.find({ "hostname": hostname, "services.name": service }).count()
            if matching_service != 0:
                db.services.update(
                    {"hostname": hostname, "services.name": service},
                    {'$set': {"services.$.status": status, "services.$.downtime": 0, "services.$.uptime": 0, "services.$.type": serv_type}}
                )

            else:
                db.services.update(
                    { "hostname": hostname},
                    { '$push': {"services": {"name": service, "status": status, "uptime": 0, "downtime": 0, "type": serv_type} } }
                )

        if service != "" and remove_service == "on":
             db.services.update({"hostname": hostname}, {'$pull': {"services": {"name": service}}})
                
        return write_result


    #|---------------------------------------------------------------------------------------
    #| get_host_status: returns a list with the requested hostname, status, and up/downtime 
    #|---------------------------------------------------------------------------------------
    def get_host_status(self, hostname):
        host_data = []
        for host in self.collection.find({"hostname": hostname},{"hostname": 1, "status":1,"uptime":1, "downtime": 1, "timestamp":1, "IP":1, "_id":0}):
            host_data = [ str(host["hostname"]), str(host["status"]), str(host["uptime"]), str(host["downtime"]), str(host["IP"]) ]
        
        if host_data[1] is 'True':
            host_data.pop(3)
            host_data[1] = 'Online'
        elif host_data[1] is 'False':
            host_data.pop(2)
            host_data[1] = 'Offline'

        return host_data        



    #|---------------------------------------------------------------------------------------
    #| get_online_hosts: returns a matrix of hosts that are currently logged as online in 
    #| MongoDB as well as their latest timestamp and uptime counter
    #|---------------------------------------------------------------------------------------
    def get_online_hosts(self):
        online_hosts = []
        host_data = []
        for host in self.collection.find({"status":True},{"hostname":1,"uptime":1,"timestamp":1, "IP":1, "_id":0}):
            host_data = [ str(host["hostname"]), str(host["timestamp"]), str(host["uptime"]), str(host["IP"]) ]
            online_hosts.append(host_data)

        return online_hosts


    #|---------------------------------------------------------------------------------------
    #| get_offline_hosts: like online_hosts, returns a matrix of hosts that are currently  
    #| logged as offline in MongoDB as well as their latest timestamp and downtime counter.
    #|---------------------------------------------------------------------------------------
    def get_offline_hosts(self):
        offline_hosts = []
        host_data = []
        for host in self.collection.find({"status":False},{"hostname":1,"downtime":1, "timestamp":1, "IP":1, "_id":0}):
            host_data = [ str(host["hostname"]), str(host["timestamp"]), str(host["downtime"]), str(host["IP"]) ]
            offline_hosts.append(host_data)

        return offline_hosts


    #|-----------------------------------------------------------------------------------------------------
    #| get_host_history: Returns a json string regarding the uptime history of 'hostname' for
    #|                   use with cal-heatmap.  
    #| 
    #| json format: {'timestamp':'minutes', 1404421200.0: 40.0, 1404424800.0: 60.0, 1404428400: 55, etc...}
    #|------------------------------------------------------------------------------------------------------
    def get_host_history(self, hostname):
        client = MongoClient('localhost', 27017)
        db = client.netstatusDB
        try:
            for data in db.history.find({"hostname":hostname}, {"hostname":0, "_id":0, "status":0}):
                raw_history_data = str(data["history"])
        except LookupError:
            history_data = {}
            return history_data
            
        #| format the raw_history_data to a json string (not the prettiest way to do it, but it works)
        #| TODO: figure out a better way to do this 'cause it's probably pretty inefficient
        raw_history_data = raw_history_data.replace("[{u'timestamp': ", "{")
        raw_history_data = raw_history_data.replace(", u'minutes'", "")
        raw_history_data = raw_history_data.replace("}, {u'timestamp': ", ", ")
        history_data = raw_history_data.replace("]", "")
        
        return history_data


    #|------------------------------------------------------------------------------------------------------------------
    #| get_host_services: Returns a matrix of services being monitored on the host and their current status 
    #| 
    #| format: [['name', 'status', 'type', 'uptime', 'downtime'], ['fake_service', 'True', 'HTTP', 0, 60], etc...]
    #|
    #|------------------------------------------------------------------------------------------------------------------
    def get_host_services(self, hostname):
        client = MongoClient('localhost', 27017)
        db = client.netstatusDB
        #| check to see if the host has any services being monitored
        service_count = db.services.find({"hostname":hostname}).count()
        if service_count == 0:
            service_data = [['No monitored services', '-----', '-----', '-----', '-----']]
        else:
            service_data = []
            try:
                for data in db.services.find({"hostname":hostname}):
                    raw_service_data = data["services"]
            except LookupError:
                print "lookupError"
                service_data = [['No monitored services', '-----', '-----', '------', '-----']]
                return service_data
            i = 0
            for service in raw_service_data:
                name = str(raw_service_data[i]['name'])
                status = str(raw_service_data[i]['status'])
                serv_type = str(raw_service_data[i]['type'])
                uptime = raw_service_data[i]['uptime']
                downtime = raw_service_data[i]['downtime']
                service = [name, status, serv_type, uptime, downtime]
                service_data.append(service)
                i += 1

        if service_data == []:
            service_data = [['No monitored services', '-----', '-----', '------', '-----']]

        return service_data

    #|---------------------------------------------------------------------------------------------------
    #| get_uptime_percent: A function to return the percent uptime of the requested
    #| server for all of history, the past week, and past 24 hours. Returns a list with
    #| the percent for each time period: [total_percent_uptime, week_percent_uptime, day_percent_uptime]
    #|---------------------------------------------------------------------------------------------------
    def get_uptime_percent(self, hostname):
        client = MongoClient('localhost', 27017)
        db = client.netstatusDB
        try:
            for data in db.history.find({"hostname":hostname}, {"hostname":0, "_id":0, "status":0}):
                history = data["history"]
        except LookupError:
            uptime_percent = [0,0,0]
            return uptime_percent

        # Total percent uptime, all history
        total_online_minutes = 0.0
        count = 0
        for value in history:
            data = value.values()
            if count == 0:
                start_date = int(data[0])
                count += 1
            total_online_minutes += data[1]

        now = int(time.time())
        total_minutes = (now - start_date) / 60
        total_percent_uptime = int((total_online_minutes / total_minutes) * 100)

        # Last 7 days (168 hours)
        count = 1
        week_online_minutes = 0.0
        while (count < 168):
            if count == len(history) + 1:
                break
            value = history[-count]
            data = value.values()
            week_online_minutes += data[1]
            count += 1 
            week_start_date = int(data[0])

        week_total_minutes = (now - week_start_date) /60 
        week_percent_uptime = int((week_online_minutes / week_total_minutes) * 100)

        # Past 24 hours
        count = 1
        day_online_minutes = 0.0
        while (count < 24):
            if count == len(history) + 1:
                break
            value = history[-count]
            data = value.values()
            day_online_minutes += data[1]
            count += 1 
            day_start_date = int(data[0])

        day_total_minutes = (now - day_start_date) /60 
        day_percent_uptime = int((day_online_minutes / day_total_minutes) * 100)


        uptime_percent = [total_percent_uptime, week_percent_uptime, day_percent_uptime]

        return uptime_percent

