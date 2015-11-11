
config = {}

crontable = []
outputs = []


def process_connected(data):
    password = config['irc'].get('pass', None)
    if password is not None:
        outputs.append(['PASS', password])
    nick = config['irc'].get('nick', 'slairck')
    outputs.append(['NICK', nick])
    outputs.append(['USER', 'slairck', '8', '*', 'SlaIRCk'])


def process_ping(data):
    outputs.append('pong :{}'.format(data.args[1]))
