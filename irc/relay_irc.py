from ircclient.const import NOTICE, PRIVMSG


crontable = []
outputs = []
relay_outs = []


def catch_all(data):
    ignore = ['CONNECTED', 'PING', 'MODE', 'JOIN', 'PART', 'QUIT', 'INVITE', 'KICK', 'BAN']
    if data.type == PRIVMSG or data.type == NOTICE:
        channel = data.args[1]
        if channel.startswith('#'):
            channel = channel[1:]
            message = data.args[2]
            if data.type == NOTICE:
                message = 'NOTICE:' + message
            relay_outs.append({'type': 'message', 'channel': channel, 'user': data.nick, 'text': message})
        else:
            relay_outs.append({'debug': True, 'type': data.type, 'description': 'pm from {}'.format(data.user)})
    else:
        relay_outs.append({'debug': True, 'type': data.type, 'description': unicode(data)})


def process_001(data):
    relay_outs.append({'type': 'connected'})
    autojoin = data.config['irc'].get('autojoin', [])
    if isinstance(autojoin, str):
        autojoin = [autojoin]
    defaultchannel = data.config['irc'].get('defaultchannel')
    if defaultchannel:
        autojoin.insert(0, defaultchannel)
    for channel in autojoin:
        outputs.append('join :#{}'.format(channel))


def process_join(data):
    pass
    #relay_outs.append({'type': 'join', 'user': data.nick, 'channel': data.args[1][1:]})
