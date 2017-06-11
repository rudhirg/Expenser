'''
Created on Oct 27, 2016

@author: rudhir
'''
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.core.urlresolvers import resolve
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
import json

from ExpenseMgmt.models import *
from google.appengine.ext import ndb

import calendar
import datetime
import logging
log = logging.getLogger(__name__)

class ExpenseInfo:
    def __init__(self, expense):
        self.type = expense.type.get().type
        self.category = expense.category.get().category
        self.price = expense.price
        self.onlineTx = expense.onlineTx
        self.loc = expense.loc
        self.comment = expense.comment
        #expense.date += datetime.timedelta(days=1)
        self.date = expense.date

class GroceryInfo:
    def __init__(self, grocery):
        self.itemName = grocery.item.get().itemName
        self.place = grocery.place.get().place
        self.price = grocery.price
        self.quantity = grocery.quantity
        self.unit = grocery.unitType
        self.date = grocery.date
        
class ShoppingItemInfo:
    def __init__(self, shoppingItem):
        self.itemName = shoppingItem.item.get().itemName
        self.quantity = shoppingItem.quantity
        self.unit = shoppingItem.unitType
        self.id = shoppingItem.key.id()
        self.places = {}
        
'''
Stats classes
'''
class Stats:
    def __init__(self):
        self.totalSpent = 0.0
        self.totalEarned = 0.0
        
    def addStat(self, expenseInfo):
        if expenseInfo.category == 'credit':
            self.totalEarned += expenseInfo.price
        else:
            self.totalSpent += expenseInfo.price

class CategoryStats:
    def __init__(self):
        self.overallStats = Stats()
        self.perTypeStats = {}
        
    def addStat(self, expenseInfo):
        self.overallStats.addStat(expenseInfo)
            
        if expenseInfo.type not in self.perTypeStats:
            self.perTypeStats[expenseInfo.type] = Stats()
        self.perTypeStats[expenseInfo.type].addStat(expenseInfo)
                
class ExpenseStats:
    def __init__(self, expenseInfoList):
        self.perCategory = {}
        self.overall = CategoryStats()
        self.extractStats(expenseInfoList)
        
    def extractStats(self, expenseInfoList):
        for expense in expenseInfoList:
            if expense.category not in self.perCategory:
                self.perCategory[expense.category] = CategoryStats()
            
            self.perCategory[expense.category].addStat(expense)
            self.overall.addStat(expense)
     
def home_page(request):
    return TemplateResponse(request, 'ExpenseMgmt/home_page.html', {})

def expenses_show(request):
    expensesQuery = Expense.query().order(-Expense.date)
    expenses = expensesQuery.fetch()
    
    expenseInfoList = []
    for expense in expenses:
        expenseInfoList.append(ExpenseInfo(expense))
    
    template_values = {
        "expenses" : expenseInfoList,
        }
    
    return TemplateResponse(request, 'ExpenseMgmt/show_page.html', template_values)
    
def grocery_show(request):
    groceryQuery = Grocery.query().order(-Grocery.date)
    groceries = groceryQuery.fetch()
    
    groceryInfoList = []
    for grocery in groceries:
        groceryInfoList.append(GroceryInfo(grocery))
    
    template_values = {
        "groceries" : groceryInfoList,
        }
    
    return TemplateResponse(request, 'ExpenseMgmt/show_grocery_page.html', template_values)

def show_page(request):
    current_url = str(request.path)
    print current_url
    retObj = None
    if "expense" in current_url:
        retObj = expenses_show(request)
    elif "grocery" in current_url:
        retObj = grocery_show(request)
    return retObj
    
def stats_page(request):
    def getStatData(datesList):
        filterList = []
        for date in datesList:
            (year, mon) = date
            monFirst = mon
            monLast = mon
            first = 1
            if mon != None:
                (_, last) = calendar.monthrange(year, mon)
            else:
                last = 31 
                monFirst = 1 
                monLast = 12
            datetimeFirst = datetime.datetime(year, monFirst, first)
            datetimeLast = datetime.datetime(year, monLast, last)
            filterList.append( ndb.AND(Expense.date >= datetimeFirst, Expense.date <= datetimeLast) )
            
        query = Expense.query(ndb.OR(*filterList))
        expenses = query.fetch()
        
        expenseInfoList = []
        for expense in expenses:
            expenseInfoList.append(ExpenseInfo(expense))
            
        return ExpenseStats(expenseInfoList)
        
    dates = request.GET.get('dates', '')
    dateList = dates.split(',');
    if dates == '' or not dateList:
        now = datetime.datetime.now()
        dateList = [(now.year, None)]
    else:
        dateList = [ dat.split('-') for dat in dateList ]
        dateList = [ (int(dat[0]), int(dat[1])) for dat in dateList ]
        
    expenseStats = getStatData(dateList)
        
    template_values = {
        'Stats' : expenseStats
        }
    
    return TemplateResponse(request, 'ExpenseMgmt/stats_page.html', template_values)


def admin_page(request):
    
    def fillEntries():
        # fill the Type and TypeCategory tables
        types = ['flight', 'hotel', 'rentalCar', 'grocery', 'gas', 'utility', 'movie', 
                 'activity', 'eating-out', 'misc', 'salary', 'rent', 'carInsurance',
                 'kitchenItem', 'furniture', 'appliances', 'decor', 'medicine', 'doctor',
                 'healthCheckups', 'gifts', 'clothing', 'carService', 'donation', 'parking',
                 'taxi']
        categories = ['travel', 'day-to-day', 'relaxation', 'health' ,'credit', 'returns']
        '''
        categoryTypesDict = {
            'travel' : ['flight', 'hotel', 'rentalCar'],
            'expenses' : ['grocery', 'gas', 'utility'],
            'entertainment' : ['movie', 'activity'],
            'food' : ['restaurant'],
            'misc' : ['misc'],
            'credit' : ['salary']
            }
        
        for c in categoryTypesDict.keys():
            cat = Category(category=c)
            cat.put()
            for t in categoryTypesDict[c]:
                typ = Type(type=t)
                typ.put()
                TypeCategory(type=typ.key, category=cat.key).put()
        '''
        for t in types:
            typ = Type(type=t)
            typ.put()
            
        for c in categories:
            cat = Category(category=c)
            cat.put()
                
    def removeEntries():
        def removeModel(mod):
            q = mod.query()
            keys = q.fetch()
            ndb.delete_multi([k.key for k in keys])
        # remove TypeCategory entries
        removeModel(Type)
        removeModel(Category)
        #removeModel(TypeCategory)
        
    add = request.GET.get('add', False)
    remove= request.GET.get('remove', False)
    
    log.debug("Admin request: " + str(add))
    
    if add:
        fillEntries()
    #if remove:
    #    removeEntries()
    
    return TemplateResponse(request, 'ExpenseMgmt/admin_page.html', {})

def add_page(request):
    def getCategoryList():
        keys = Category.query().fetch()
        return [str(v.category) for v in keys]
    
    def getTypeList():
        keys = Type.query().fetch()
        return [str(v.type) for v in keys]
    
    categoryList = getCategoryList()
    typeList = getTypeList()
    
    template_values = {
        "categories" : categoryList,
        "types" : typeList
        }
    
    return TemplateResponse(request, 'ExpenseMgmt/add_page.html', template_values)

def submitExpense(request):
    
    def addExpense(price, category, type, date, onlineTx, lat, lng, comment):
        # get type
        typeKey = Type.query(Type.type == type).fetch()
        catKey = Category.query(Category.category == category).fetch()
        e = Expense(price=price, type=typeKey[0].key, category=catKey[0].key, 
                    date=date, onlineTx=onlineTx, loc=ndb.GeoPt(lat, lng), comment=comment)
        e.put()
    
    price = float(request.GET.get('price', 0.0))
    category = str(request.GET.get('category', ''))
    type = str(request.GET.get('type', ''))
    txType = str(request.GET.get('txType', ''))
    onlineTx = (True if txType == 'online' else False)
    comment = str(request.GET.get('comment', ''))
    lat = float(request.GET.get('lat', 0.0))
    lng = float(request.GET.get('long', 0.0))
    
    #date = datetime.datetime.now()
    date = str(request.GET.get('date', ''))
    date = (datetime.datetime.now() if not date else datetime.datetime.strptime(date,'%Y-%m-%d'))
    
    addExpense(price, category, type, date, onlineTx, lat, lng, comment)
    #return redirect("/add")
    return HttpResponseRedirect('/add/' )

def submitGrocery(request):
    def addGrocery(itemName, price, date, quantity, unit, place):
        itemName = itemName.strip()
        place = place.strip()
        item = Item(itemName=itemName.lower(), id=itemName.lower())
        item.put()
        gplace = GroceryPlace(place=place.lower(), id=place.lower())
        gplace.put()
        g = Grocery(item=item.key, place=gplace.key, price=price, quantity=quantity, date=date, unitType=unit)
        g.put()
        
    price = float(request.GET.get('price', 0.0))
    item = str(request.GET.get('item', 0.0))
    place = str(request.GET.get('place', 0.0))
    quantity = float(request.GET.get('quantity', 0.0))
    unit = str(request.GET.get('unit', 0.0))
    date = str(request.GET.get('date', ''))
    date = (datetime.datetime.now() if not date else datetime.datetime.strptime(date,'%Y-%m-%d'))
    
    addGrocery(item, price, date, quantity, unit, place)
    return HttpResponseRedirect('/grocery/' )
    
def grocery_page(request):
    def getItems():
        keys = Item.query().fetch()
        return [str(v.itemName) for v in keys]
    
    def getPlaces():
        keys = GroceryPlace.query().fetch()
        return [str(v.place) for v in keys]
    
    unitTypes = ['pound', 'oz', 'fl', 'kg', 'gallon', 'litre', 'gram', 'number']
    template_values = {
        "unitTypes" : unitTypes,
        "items" : getItems(),
        "places" : getPlaces()
        }
    
    return TemplateResponse(request, 'ExpenseMgmt/grocery_page.html', template_values)

@csrf_exempt
def shoppingList_page(request):
    def getItems():
        keys = Item.query().fetch()
        return [str(v.itemName) for v in keys]
    
    def getShoppingItems():
        ret = []
        sItems = ShoppingItem.query().fetch()
        for item in sItems:
            sItem = ShoppingItemInfo(item)
            ret.append(sItem)
        return ret
    
    shoppingItems = getShoppingItems()
    for item in shoppingItems:
        placesInfo = getItemInfo(item.itemName)
        for place in placesInfo:
            item.places[place.place] = place
            
    unitTypes = ['pound', 'oz', 'fl', 'kg', 'gallon', 'litre', 'gram', 'number']
    template_values = {
        "shopItems" : shoppingItems,
        "items" : getItems(),
        "unitTypes" : unitTypes
        }
    return TemplateResponse(request, 'ExpenseMgmt/shoppinglist_page.html', template_values)

@csrf_exempt
def ajaxHandle(request):
    current_url = str(request.path)
    print current_url
    
    retObj = None
    if "addShoppingItem" in current_url:
        retObj = addShoppingItem(request)
    if "delShoppingItem" in current_url:
        retObj = deleteShoppingItem(request)
        
    return retObj
    
def addShoppingItem(request):
    def addInShoppingList(itemName, quantity, unit):
        itemName = itemName.strip().lower()
        #item = Item(itemName=itemName.lower(), id=itemName.lower())
        #item.put()
        item = Item.query(Item.itemName==itemName).fetch()
        if len(item)  == 0:
            # put in item table
            item = Item(itemName=itemName, id=itemName)
            item.put()
        item = Item.query(Item.itemName==itemName).fetch()
        sI = ShoppingItem(item=item[0].key, quantity=quantity, unitType=unit)
        sI.put()
        return sI.key.id()
        
    itemName = str(request.POST.get('item', ''))
    quantity = float(request.POST.get('quantity', 0.0))
    unit = str(request.POST.get('unit', 0.0))
    
    itemId = addInShoppingList(itemName, quantity, unit);
    itemInfo = getItemInfo(itemName)
    
    jsonData = {'item': itemName, 'quantity': quantity, 'unit': unit, 'id': itemId, 'places': []}
    placeData = []
    for item in itemInfo:
        placeData.append({'place': item.place, 'price':item.price, 'unit':item.unit})
    jsonData['places'] = placeData
    
    response_data = {}
    response_data['result'] = jsonData
    return HttpResponse(
            json.dumps(response_data),
            content_type="application/json"
        )

def deleteShoppingItem(request):
    itemId = int(request.POST.get('itemId', ''))
    shoppingItemKey = ndb.Key('ShoppingItem', itemId)
    shoppingItemKey.delete()
    
    response_data = {}
    response_data['result'] = 'success'
    return HttpResponse(
            json.dumps(response_data),
            content_type="application/json"
        )

#get the price details for the item at each grocery place    
def getItemInfo(itemName):
    # get item
    item = Item.query(Item.itemName==itemName).fetch()
    if len(item) == 0:
        print 'No item: ' + itemName + ' in database'
        return []
    item = item[0]
    itemInfo = [];
    #get all grocery places
    gpList = GroceryPlace.query().fetch()
    for gp in gpList:
        place = gp.place
        # get the prices for item and place
        groceries = Grocery.query(Grocery.item==item.key, Grocery.place==gp.key).order(-Grocery.date).fetch()
        if len(groceries) == 0:
            continue
        # make the price per unit price
        gInfo = GroceryInfo(groceries[0])
        gInfo.price = round(gInfo.price/gInfo.quantity, 2)
        itemInfo.append(gInfo)
        
    return itemInfo
    