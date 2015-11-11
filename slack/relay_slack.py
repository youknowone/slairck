
crontable = []
outputs = []
relay_outs = []


def process_user_typing(data):
    pass

def process_message(data):
    user_id = config['slack'].get('user_id')
    if not user_id or data.get('user', None) == user_id:
        relay_outs.append(data)

def process_channel_joined(data):
    relay_outs.append({'type': 'join', 'channel': data['channel']['id']})
