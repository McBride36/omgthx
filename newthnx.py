import asyncio
import concurrent.futures

import arrow
import bottom
import collections
from tinydb import TinyDB, Query

prefix = "!"
nick = 'omgthx'
channels = ["#test_bride"]
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


@command(1)
async def seen(nick, target, user, host, data):
    search = Query()
    print("nick:{} target:{} user:{} host:{} data:{}".format(nick, target, user, host, data))
    if data[0][-1] == '?':
        x = data[0][0:-1]
        result = seentable.search(search.name.test(lambda s: s.lower() == x.lower()))
        msg(target, '{}'.format(result[0]['message']))


@command(1, name=nick)
async def tell(nick, target, user, host, data):
    if data[0] == "tell":
        left_message = ' '.join(data[2:])
        # {"id":21,"author":"swifty","recipient":"kthx","timestamp":"2014-01-11 11:10:33","message":"botsmack!","inTracked":1}
        seentable.insert(
                {"author": nick, "recipient": data[1], "timestamp": str(arrow.utcnow()), "message": left_message})
        msg(target, "okay {} I'll pass that on to {} when they get back".format(nick, data[1]))
    # result = factoids.search(Nick.item.test(lambda s: s.lower() == x.lower()))
    factlet = data[0]
    if data[1] == 'is':
        checkfactlet = factoids.contains(generalquery.item.test(lambda s: s.lower() == factlet.lower()))
        if checkfactlet:
            # {"id":3029,"item":"JATMN","are":0,"value":"a whore","nick":"eogra7","dateset":"2014-01-01 02:46:22","locked":null,"lastsync":null}
            currentvalue = factoids.get(generalquery.item.test(lambda s: s.lower() == factlet.lower()))
            factoids.update({"value": "is " + ' '.join(data[2:] + " and is also  " + currentvalue[0]['value']), "nick": nick,
                     "dateset": str(arrow.utcnow())}, generalquery.item.test(lambda s: s.lower() == factlet.lower()))
            msg(target, "I've updated {}".format(data[0]))
        else:
            factoids.insert({"item": data[0], "value": ' '.join(data[1:]), "nick": nick, "dateset": str(arrow.utcnow()),
                             "locked": "0"})
            msg(target, "I know {} now".format(data[0]))
    elif factlet in ["forget","Forget"]:
        pass


@command(0, name=None)
async def multipart(nick, target, user, host, data):
    msg(target, "Part 1, !more for more")
    print("nick:{} target:{} user:{} host:{} data:{}".format(nick, target, user, host, data))
    await future_command(nick, "more")
    msg(target, "Part 2, !evenmore for even more")
    await future_command(nick, "evenmore")
    msg(target, "fartz")


@command
async def calculate(nick, target, user, host, data):
    running_total = 0
    while True:
        msg(target,
            "Use !add to add a number, !subtract to subtract one, or !finish to end this nightmarish existence you find yourself trapped in.")
        msg(target, "Total: {}".format(running_total))
        command, args = await future_race(nick, "add", "subtract", "finish")
        if command == "finish":
            break
        if not args:
            msg(target, "You must provide a number.")
            continue
        number = args[0]
        number = float(number)
        if command == "subtract":
            number = -number
        running_total += number
    msg(target, "Final total: {}".format(running_total))


asyncio.get_event_loop().run_until_complete(bot.run())
