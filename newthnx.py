import asyncio
import concurrent.futures

import arrow
import bottom
import collections
from tinydb import TinyDB, Query
import re

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sql_declarative import Factoid_history, Factoids, Seen, Tell

engine = create_engine('sqlite:///reprap_database.db')
session = sessionmaker()
session.configure(bind=engine)
s = session()

prefix = "!"
nick = 'omgthx'
channels = ["#monkeyclub"]
commands = {}
awaiting_commands = collections.defaultdict(dict)

# import db stuff here.
reprapDB = TinyDB('reprap.json')
factoids = reprapDB.table('factoids')
factoids_history = reprapDB.table('factoids_history')
seentable = reprapDB.table('seen')
telltable = reprapDB.table('tell')
generalquery = Query()


def command(*args, name=None):
    def _command(func):
        async def wrapper(nick, target, user, host, data):
            if len(data) != max_args:
                return
            else:
                return asyncio.Task(func(nick, target, user, host, data))

        commands[name if name else func.__name__] = wrapper
        print(commands)
        return wrapper

    if len(args) == 1 and callable(args[0]):
        max_args = 6e10
        return _command(args[0])
    else:
        max_args = args[0]
        return _command


bot = bottom.Client('chat.freenode.net', 6697)


async def future_command(nick, command):
    future = asyncio.Future()
    awaiting_commands[nick][command] = future
    return await future


async def future_race(nick, *commands):
    futures = [future_command(nick, command) for command in commands]
    done, pending = await asyncio.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
    for task in pending:
        task.cancel()
    res = list(done)[0].result()
    return res


def msg(target, message):
    bot.send('PRIVMSG', target=target, message=message)


def me(target, message):
    msg(target, chr(1) + "ACTION " + message + chr(1))


@bot.on('CLIENT_CONNECT')
async def connect():
    bot.send('NICK', nick=nick)
    bot.send('USER', user=nick, realname='DummyBot')
    await join(channels)


async def join(*channels):
    for channel in channels:
        bot.send('JOIN', channel=channel)


@bot.on('PING')
async def keepalive(message):
    bot.send('PONG', message=message)


# [{"id":1,"name":"gunnbr","channel":"#reprap",
# "timestamp":"2014-01-15 18:13:48","message":"RoyOnWheels|MTW: Oh! I like it!!"},
@bot.on('PRIVMSG')
async def message(nick: str, target: str, message: str, user: str, host: str):
    if seentable.contains(generalquery.name.test(lambda s: s.lower() == nick.lower())):
        seentable.update({"channel": target, "timestamp": str(arrow.utcnow()), "message": message},
                         generalquery.name == nick)
    else:
        seentable.insert({"name": nick, "channel": target, "timestamp": str(arrow.utcnow()), "message": message})
    message = message.strip()
    split_message = message.split()
    command = split_message.pop(0).lower()
    for c in commands:
        if command.lower().startswith(c):
            await commands[command](nick, target, user, host, split_message)
            break
    if command in awaiting_commands[nick]:
        awaiting_commands[nick][command].set_result((command, split_message))


@bot.on('PRIVMSG')
async def checkmessage(nick: str, target: str, message: str, user: str, host: str):
    message = message.strip()
    data = message.split()
    if data[-1][-1] in ['!', '?']:
        if data[0].lower in ['omgthx', 'omgthx,', 'omgthx:']:
            del data[0]
        data[-1] = data[-1][:-1]
        factlet = ' '.join(data)
        checkfactlet = factoids.contains(generalquery.item.test(lambda s: s.lower() == factlet.lower()))
        if checkfactlet:
            currentvalue = factoids.get(generalquery.item.test(lambda s: s.lower() == factlet.lower()))
            # {"id":3029,"item":"JATMN","are":0,"value":"a whore","nick":"eogra7","dateset":"2014-01-01 02:46:22","locked":null,"lastsync":null}
            msg(target, "{} is {}".format(factlet, currentvalue['value']))


@bot.on('PRIVMSG')
# omgthx(?:.)? ([^(is)]*) is (.*)$
async def changefactoid(nick: str, target: str, message: str, user: str, host: str):
    message = message.strip()
    data = message.split()
    await check_forget(message, target)
    if not await check_also(message, nick, target):
        await check_is(data, message, nick, target)
    await check_stats(nick, target, message, user, host, data)


async def check_is(data, message, nick, target):
    m = re.search("omgthx(?:.)? ((?!(?:is)).*) is (.*)", message, re.IGNORECASE)
    if m is None:
        return
    factlet = m.group(1)
    info = m.group(2)
    checkfactlet = factoids.contains(generalquery.item.test(lambda s: s.lower() == factlet.lower()))
    results = s.query.filter(Factoids.item.ilike(factlet))
    if results.count():
        currentvalue = results.first()
        # {"id":3029,"item":"JATMN","are":0,"value":"a whore","nick":"eogra7","dateset":"2014-01-01 02:46:22","locked":null,"lastsync":null}

        factoids.update(
                {"value": "{} and also {}".format(info, currentvalue['value']), "nick": nick,
                 "dateset": str(arrow.utcnow())}, generalquery.item.test(lambda s: s.lower() == factlet.lower()))
        msg(target, "I've updated {}".format(factlet))
    else:
        factoids.insert({"item": factlet, "value": info, "nick": nick, "dateset": str(arrow.utcnow()),
                         "locked": "0"})
        msg(target, "I know {} now".format(factlet))


async def check_forget(message, target):
    m = re.search("omgthx,? forget (.*)", message, re.IGNORECASE)
    if m is None:
        return
    factlet = m.group(1)
    checkfactlet = factoids.contains(generalquery.item.test(lambda s: s.lower() == factlet.lower()))
    if checkfactlet:
        currentvalue = factoids.get(generalquery.item.test(lambda s: s.lower() == factlet.lower()))
        eids = currentvalue.eid
        factoids.remove(eids=[eids])
        msg(target, "I've forgotten {}".format(factlet))


async def check_also(message, nick, target):
    m = re.search("omgthx(?:.)? ((?!(?:is also)).*) is also (.*)", message, re.IGNORECASE)
    if m is None:
        return
    factlet = m.group(1)
    info = m.group(2)
    checkfactlet = factoids.contains(generalquery.item.test(lambda s: s.lower() == factlet.lower()))
    if checkfactlet:
        # {"id":3029,"item":"JATMN","are":0,"value":"a whore","nick":"eogra7","dateset":"2014-01-01 02:46:22","locked":null,"lastsync":null}
        currentvalue = factoids.get(generalquery.item.test(lambda s: s.lower() == factlet.lower()))
        # factoids.update({"value": "is {} and is also {}".format(info, currentvalue[0]['value']), "nick": nick,"dateset": str(arrow.utcnow())})
        factoids.update({"value": " {} and also {}".format(info, currentvalue['value']), "nick": nick,
                         "dateset": str(arrow.utcnow())},
                        generalquery.item.test(lambda s: s.lower() == factlet.lower()))
        msg(target, "I've updated {}".format(factlet))
        return True


async def check_stats(nick: str, target: str, message: str, user: str, host: str, data):
    m = re.search("omgthx,? stats ([^?.;]*)", message, re.IGNORECASE)
    if m is None:
        return
    name = m.group(1)
    try:
        factoid_list = factoids.search(Query().nick.test(lambda s: s and s.lower() == name.lower()))
    except Exception as e:
        print(e)
        return
    for fact in factoid_list:
        fact["dateset"] = arrow.get(fact["dateset"]).timestamp
    sorted_facts = sorted(factoid_list, key=lambda k: k["dateset"], reverse=True)
    joined_list = sorted_facts[:10] if len(sorted_facts) >= 10 else sorted_facts
    joined_list = ", ".join(["{}".format(x["item"]) for x in joined_list])
    msg(nick, "{} results found for {}. 10 most recent: {}".format(len(sorted_facts), name, joined_list))


@command(1)
async def seen(nick, target, user, host, data):
    search = Query()
    # print("nick:{} target:{} user:{} host:{} data:{}".format(nick, target, user, host, data))
    if data[0][-1] == '?':
        x = data[0][0:-1]
        result = seentable.search(search.name.test(lambda s: s.lower() == x.lower()))
        me(target, '{}'.format(result[0]['message']))


# @command(0, name=None)
# async def multipart(nick, target, user, host, data):
#     msg(target, "Part 1, !more for more")
#     print("nick:{} target:{} user:{} host:{} data:{}".format(nick, target, user, host, data))
#     await future_command(nick, "more")
#     msg(target, "Part 2, !evenmore for even more")
#     await future_command(nick, "evenmore")
#     msg(target, "fartz")

try:
    asyncio.get_event_loop().run_until_complete(bot.run())
except KeyboardInterrupt:
    reprapDB.close()
