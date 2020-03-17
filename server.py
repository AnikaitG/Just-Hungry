import sys
import Pyro4
import Pyro4.naming
import multiprocessing
import json
import urllib
import urllib.request

@Pyro4.expose
class JustHungry(object):
    orders = {}
    is_primary = '0'
    r_no = '0'
    backups = []
    next = None

    def __init__(self):
        if self.r_no == '1':
            self.is_primary = '1'
        r_dict = {'1':['2', '3'], '2':['3'], '3':[]}
        self.backups = r_dict[self.r_no]
        for i, r in enumerate(self.backups):
            r_name = "PYRONAME:jhbs" + r
            r = Pyro4.Proxy(r_name)
            self.backups[i] = r
        self.next = self.backups[0]

    def getNext(self):
        return self.next

    def update(self, orderlist):
        self.orders = orderlist

    def updateBackups(self):
        for r in self.backups:
            try:
                r.update(self.orders)
            except IndexError:
                break

    def greet(self, name):
        self.orders[name] = []
        if self.is_primary == '1':
            self.updateBackups()
        return "Hello, {0}! Please input the names of the food items you wish to add to your delivery one at a time.\n" \
        "Input 'done' when you have finished.\n".format(name)
    
    def addItem(self, name, item):
        if item == '':
            return
        self.orders[name].append(item)
        if self.is_primary == '1':
            self.updateBackups()

    def sendOrder(self, name):
        orderstr = "\nYour requested delivery: \n"
        if self.orders[name] == []:
            orderstr = "\nNo order recieved, please try again."
        for item in self.orders[name]:
            orderstr += '\t- ' + item + '\n'
        return orderstr

    def getAddr(self, post):
        query = urllib.request.urlopen('http://api.postcodes.io/postcodes/{0}/validate'.format(post))
        str_response = query.read().decode('utf-8')
        js = json.loads(str_response)
        if js["result"]:
            query = urllib.request.urlopen('http://api.postcodes.io/postcodes/{0}'.format(post))
            str_response = query.read().decode('utf-8')
            js = json.loads(str_response)
            return "Your order will be dispatched to our store in {0}, thank you for using Just Hungry!".format(js["result"]["admin_district"])
        else:
            return "Invalid address"

class Callback(object):
    JH = Pyro4.Proxy("PYRONAME:jhbs1")
    backup = None

    def __init__(self):
        self.backup = self.JH.getNext()

    def changePrimary(self):
        self.JH = self.backup
        self.__init__()

    @Pyro4.expose
    def greet(self, name):
        try:
            response = self.JH.greet(name)
        except Pyro4.errors.ConnectionClosedError:
            self.changePrimary()
            return self.greet(name)
        return response

    @Pyro4.expose
    def addToOrder(self, name, item):
        try:
            self.JH.addItem(name, item)
        except Pyro4.errors.ConnectionClosedError:
            self.changePrimary()
            self.addToOrder(name, item)

    @Pyro4.expose
    def getOrder(self, name):
        try:
            response = self.JH.sendOrder(name)
        except Pyro4.errors.ConnectionClosedError:
            self.changePrimary()
            return self.getOrder(name)
        return response

    @Pyro4.expose
    def confAddr(self, post):
        try:
            response = self.JH.getAddr(post)
        except Pyro4.errors.ConnectionClosedError:
            self.changePrimary()
            return self.confAddr(post)
        return response

def nameServer():
    Pyro4.naming.startNSloop()

def backServer(name):
    daemon = Pyro4.Daemon()
    ns = Pyro4.locateNS()
    uri = daemon.register(JustHungry)
    JustHungry.r_no = name[-1]
    ns.register(name, uri)
    daemon.requestLoop()

def serverInterface():
    daemon = Pyro4.Daemon()
    ns = Pyro4.locateNS() 
    uri = daemon.register(Callback)
    ns.register("JustHungry", uri)
    print("Server is ready")
    daemon.requestLoop()

if __name__ == '__main__':
    multiprocessing.Process(target=nameServer).start()
    multiprocessing.Process(target=backServer, args=("jhbs1",)).start()
    multiprocessing.Process(target=backServer, args=("jhbs2",)).start()
    multiprocessing.Process(target=backServer, args=("jhbs3",)).start()
    multiprocessing.Process(target=serverInterface).start()
