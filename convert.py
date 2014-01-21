import oursql
import psycopg2
from collections import defaultdict

def main():
    mysql = oursql.connect(host='localhost', user='eve', passwd='eve', db='eve')
    postgres = psycopg2.connect("host='localhost' dbname='eveskill' user='eveskill' password='eveskill'")

    mysql_cursor = mysql.cursor(oursql.DictCursor)
    pg_cursor = postgres.cursor()

    mysql_cursor.execute('SELECT * FROM `invTypes` WHERE `groupID` IN (SELECT groupID FROM `invGroups` WHERE `categoryID` = 16 AND `published` = 1) and `published` = 1')
    skills = mysql_cursor.fetchall()

    # Replace decimals prices with integer ones
    skills_fixed = [dict(item, **{'price': int(item['basePrice']), 'categoryID':16}) for item in skills]

    pg_cursor.executemany("""INSERT INTO skills (typeid,groupid,categoryid,description,baseprice,name) VALUES (%(typeID)s, %(groupID)s, %(categoryID)s, %(description)s, %(price)s, %(typeName)s)""", skills_fixed)
    postgres.commit()

    # Now add the skill dependencies
    for skill in skills_fixed:
        mysql_cursor.execute("SELECT attributeID attr, coalesce(valueFloat,ValueInt) value FROM `dgmTypeAttributes` where `typeID` = %s" % skill['typeID'])
    
        (prereqs,attributes) = decode_rows(mysql_cursor.fetchall()) 
        attributes['typeID'] = skill['typeID']
        pg_cursor.execute("""UPDATE skills SET timeconstant = %(multiplier)s, primaryattr = %(primary)s, secondaryattr = %(secondary)s WHERE typeID = %(typeID)s""", attributes)

        prereqs_list = [dict(req, **{'typeID': skill['typeID']}) for req in prereqs.values()] 
        pg_cursor.executemany("""INSERT INTO reqs_temp (typeid,reqtypeid,level) VALUES (%(typeID)s, %(skill)s, %(level)s)""", prereqs_list)

        postgres.commit()

    # Now lets add in our items
    for category in [6, 7, 8, 18, 20, 22, 23, 30, 32]:
        mysql_cursor.execute('SELECT * FROM `invTypes` WHERE `groupID` IN (SELECT groupID FROM `invGroups` WHERE `categoryID` = %s AND `published` = 1) and `published` = 1' % category)
        items = mysql_cursor.fetchall()

        # Replace decimals prices with integer ones
        items_fixed = [dict(item, **{'price': int(item['basePrice']), 'categoryID': category}) for item in items]

        pg_cursor.executemany("""INSERT INTO items (typeid,groupid,categoryid,description,baseprice,name) VALUES (%(typeID)s, %(groupID)s, %(categoryID)s, %(description)s, %(price)s, %(typeName)s)""", items_fixed)
        postgres.commit()

        for item in items_fixed:
            mysql_cursor.execute("SELECT attributeID attr, coalesce(valueFloat,ValueInt) value FROM `dgmTypeAttributes` where `typeID` = %s" % item['typeID'])
    
            (prereqs,x) = decode_rows(mysql_cursor.fetchall()) 

            prereqs_list = [dict(req, **{'typeID': item['typeID']}) for req in prereqs.values()] 
            pg_cursor.executemany("""INSERT INTO reqs_temp (typeid,reqtypeid,level) VALUES (%(typeID)s, %(skill)s, %(level)s)""", prereqs_list)

            postgres.commit()

    # Execute procedure to flatten requrements table
    pg_cursor.execute("SELECT flatten_requirements()")
    postgres.commit()

def decode_rows(rows):
    prereqs = {'primary': defaultdict(), 'secondary': defaultdict(), 'tertiary': defaultdict(), 'quaternary': defaultdict(), 'quinary': defaultdict(), 'senary': defaultdict()}
    attributes = defaultdict()
    
    for row in rows:
        attr = row['attr']
        value = int(row['value'] or 0)

        if attr == 180:
            attributes['primary'] = value
        elif attr == 181:
            attributes['secondary'] = value
        elif attr == 275:
            attributes['multiplier'] = value
        elif attr == 277:
            prereqs['primary']['level'] = value
        elif attr == 278:
            prereqs['secondary']['level'] = value
        elif attr == 279:
            prereqs['tertiary']['level'] = value
        elif attr == 1286:
            prereqs['quaternary']['level'] = value
        elif attr == 1287:
            prereqs['quinary']['level'] = value
        elif attr == 1288:
            prereqs['senary']['level'] = value
        elif attr == 182:
            prereqs['primary']['skill'] = value
        elif attr == 183:
            prereqs['secondary']['skill'] = value
        elif attr == 184:
            prereqs['tertiary']['skill'] = value
        elif attr == 1285:
            prereqs['quaternary']['skill'] = value
        elif attr == 1289:
            prereqs['quinary']['skill'] = value
        elif attr == 1290:
            prereqs['senary']['skill'] = value

    # filter out skills that don't have all 3 prereq slots filled, or skills that have 
    # invalid attribute maps (I'm looking at you, old learning skills)
    for key in list(prereqs.keys()):
        try:
            prereqs[key]['skill']
            prereqs[key]['level']
        except KeyError:
            del(prereqs[key])

    return (prereqs, attributes)

if __name__ == "__main__":
    main()
