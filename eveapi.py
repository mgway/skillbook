import requests
import xml.etree.ElementTree as ET
from datetime import datetime

api_url = 'https://api.eveonline.com'


# -- API proxy methods
def key_info(key_id, key_code):
    data = {'keyID': key_id, 'vCode': key_code}
    query = Query('/account/APIKeyInfo.xml.aspx', data)
    key = query.tree.find('*//key')
    mask = key.attrib['accessMask']
    if key.attrib['expires'] != '':
        expires = datetime.strptime(key.attrib['expires'], '%Y-%m-%d %H:%M:%S')
    else:
        expires = None
    return mask, query, expires


def character_sheet(key_id, key_code, key_mask, character_id):
    allowed(key_mask, 8)
    data = {'keyID': key_id, 'vCode': key_code, 'characterID': character_id}
    query = Query('/char/CharacterSheet.xml.aspx', data)
    
    # Fix up the data a little bit
    query.birthday = datetime.strptime(query.dob, '%Y-%m-%d %H:%M:%S')
    query.bio = ' - '.join([query.gender, query.race, query.bloodline, query.ancestry])
    query.memory = query.attributes.memory
    query.intelligence = query.attributes.intelligence
    query.perception = query.attributes.perception
    query.charisma = query.attributes.charisma
    query.willpower = query.attributes.willpower

    #Ugh
    try:
        query.memorybonus = query.attributeenhancers.memorybonus.augmentatorvalue
    except AttributeError:
        query.memorybonus = 0
    try:
        query.intelligencebonus = query.attributeenhancers.intelligencebonus.augmentatorvalue
    except AttributeError:
        query.intelligencebonus = 0
    try:
        query.perceptionbonus = query.attributeenhancers.perceptionbonus.augmentatorvalue
    except AttributeError:
        query.perceptionbonus = 0
    try:
        query.willpowerbonus = query.attributeenhancers.willpowerbonus.augmentatorvalue
    except AttributeError:
        query.willpowerbonus = 0
    try:
        query.charismabonus = query.attributeenhancers.charismabonus.augmentatorvalue
    except AttributeError:
        query.charismabonus = 0

    return query


def character_info(character_id):
    data = {'characterID': character_id}
    query = Query('/eve/CharacterInfo.xml.aspx', data)
    
    # No alliance? No problem! just drop part of the schema from the response
    try:
        query.allianceid
    except AttributeError:
        query.allianceid = None
        query.alliance = None
        
    return query


def market_orders(key_id, key_code, key_mask, character_id):
    allowed(key_mask, 4096)
    data = {'keyID': key_id, 'vCode': key_code, 'characterID': character_id}
    query = Query('/char/MarketOrders.xml.aspx', data)
    return query


def market_transactions(key_id, key_code, key_mask, character_id, row_count=1000):
    allowed(key_mask, 4194304)
    data = {'keyID': key_id, 'vCode': key_code, 'characterID': character_id, 
            'rowCount': row_count}
    query = Query('/char/WalletTransactions.xml.aspx', data)
    return query


def wallet_journal(key_id, key_code, key_mask, character_id, row_count=1000):
    allowed(key_mask, 2097152)
    data = {'keyID': key_id, 'vCode': key_code, 'characterID': character_id, 
            'rowCount': row_count}
    query = Query('/char/WalletJournal.xml.aspx', data)
    return query


def skill_queue(key_id, key_code, key_mask, character_id):
    allowed(key_mask, 262144)
    data = {'keyID': key_id, 'vCode': key_code, 'characterID': character_id}
    query = Query('/char/SkillQueue.xml.aspx', data)
    return query


def allowed(mask, flag):
    if mask & flag == 0:
        raise APIException("The API key provided does not support this call")


# -- API classes
class Query:
    # full queries turn all child elements of the <result> into attributes 
    # which is useful for the character sheet
    def __init__(self, relative_url, data):
        result = requests.post(api_url + relative_url, data)
        if result.status_code == 200:
            self.tree = ET.fromstring(result.text)
            for element in self.tree.findall('./result/*'):
                node = Node(element)
                setattr(self, node.name, node.value)
            cached = self.tree.find('./cachedUntil').text
            self.cached_until = datetime.strptime(cached, '%Y-%m-%d %H:%M:%S')
        elif 400 <= result.status_code < 500:
            print(result.text)
            self.tree = ET.fromstring(result.text)
            message = self.tree.find('error').text
            raise APIException("API Error: " + message)


class Rowset:
    def __init__(self, rowset):
        attributes = rowset.attrib
        self.name = attributes['name']
        self.key = attributes['key']
        self.rows = []
        for row in rowset.findall('./row'):
            self.rows.append(Row(row))


class Row:
    def __init__(self, row):
        for k,v in row.attrib.items():
            setattr(self, k.lower(), v)
        
    def __str__(self):
        return "<Row: " + str(self.__dict__) + ">"


class Node:
    def __init__(self, element):
        if element.tag.lower() == 'rowset':
            rowset = Rowset(element)
            self.name = rowset.name
            self.value = rowset
            return
        self.name = element.tag.lower()
        self.value = element.text
        for child in element:
            node = Node(child)
            setattr(self, node.name, node.value)
            self.value = self


class HttpException(Exception):
    def __init__(self, message):
        self.message = message


class APIException(Exception):
    def __init__(self, message):
        self.message = message
