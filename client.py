import Pyro4

JH = Pyro4.Proxy("PYRONAME:JustHungry")

name = input("Welcome to Just Hungry! What is your name? ").strip()
print(JH.greet(name))

item = input("Add to delivery: ")
while item.lower() != "done":
    JH.addToOrder(name, item)
    item = input("Add to delivery: ")
print(JH.getOrder(name))

postcode = input("What is your postcode? ")
print(JH.confAddr(postcode))