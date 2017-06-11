'''
Created on Oct 27, 2016

@author: rudhir
'''
from google.appengine.ext import ndb
'''
class Type(ndb.Model):
    type = ndb.StringProperty()
  
class Category(ndb.Model):
    category = ndb.StringProperty()

class TypeCategory(ndb.Model):
    type = ndb.KeyProperty(kind=Type)
    category = ndb.KeyProperty(kind=Category)
  
class Expense(ndb.Model):
    price = ndb.FloatProperty()
    date = ndb.DateProperty()
    credit = ndb.BooleanProperty()
    onlineTx = ndb.BooleanProperty()
    type = ndb.KeyProperty(kind=Type, repeated=True)
    comment = ndb.TextProperty()
'''
class Type(ndb.Model):
    type = ndb.StringProperty()
  
class Category(ndb.Model):
    category = ndb.StringProperty()
  
class Expense(ndb.Model):
    price = ndb.FloatProperty()
    date = ndb.DateProperty()
    onlineTx = ndb.BooleanProperty()
    type = ndb.KeyProperty(kind=Type)
    category = ndb.KeyProperty(kind=Category)
    loc = ndb.GeoPtProperty()
    comment = ndb.TextProperty()
    
class Item(ndb.Model):
    itemName = ndb.StringProperty()    

class GroceryPlace(ndb.Model):
    place = ndb.StringProperty()    
    
class Grocery(ndb.Model):
    item = ndb.KeyProperty(kind=Item)
    date = ndb.DateProperty()
    price = ndb.FloatProperty()
    quantity = ndb.FloatProperty()
    unitType = ndb.StringProperty() #pounds, oz, gallons, number, liter, kg
    place = ndb.KeyProperty(kind=GroceryPlace)

class ShoppingItem(ndb.Model):
    item = ndb.KeyProperty(kind=Item)
    quantity = ndb.FloatProperty()
    unitType = ndb.StringProperty() #pounds, oz, gallons, number, liter, kg
    
class ShoppingList(ndb.Model):
    items = ndb.KeyProperty(kind=ShoppingItem, repeated=True)
        
