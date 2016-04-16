from tinydb import TinyDB, Query
import arrow

reprapDB = TinyDB('reprap.json')
factoids = reprapDB.table('factoids')
#{"id":3027,"item":"vodka","are":0,"value":"what comes out of russia's tap","nick":"eogra7_","dateset":"2014-01-01 02:43:41","locked":null,"lastsync":null}
factoids_history = reprapDB.table('factoids_history')
seen = reprapDB.table('seen')
tell = reprapDB.table('tell')



Nick = Query()
x = None

#{"id":3030,"item":"JATMN","are":0,"value":"JAT.MN","nick":"JATMN","dateset":"2014-01-01 02:46:48","locked":null,"lastsync":null}
count = factoids_history.count(Nick.item == x)
namelist = factoids.search(Nick.nick == x)

# for name in namelist:
#     name["dateset"] = arrow.get(name["dateset"]).timestamp
# sorted_facts = sorted(namelist, key=lambda k: k["dateset"], reverse=True)


try:
    # print ('count: {}'.format(count))
    b = tell.all()
    print(len(b))
except:
    pass
#print(factoids.get(eid=2674))

#{"id":19,"author":"Chewonit64","recipient":"kthx",
# "timestamp":"2014-01-10 16:36:12","message":"botsmack!","inTracked":1}
#tell.update({"message":"botsmack r dum"}, Nick.author == "Chewonit64")
#result = factoids.search(Nick.item.test(lambda s: s.lower() == x.lower()))
#result = tell.search(Nick.author.test(lambda s: s.lower() == x.lower()))
# result = seen.search(Nick.name.test(lambda s: s.lower() == x.lower()))
# if result != []:
#     print(result)
# else: print('boop')
# print(result[0]['message'])