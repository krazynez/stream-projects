import os
import socket
import pandas as pd
from collections import namedtuple


TEMPLATE_COMMANDS = {
        '!discord': 'Please join the {message.channel} Discord server https://discord.gg/44pEhPqS',
        '!so': 'Check out {message.text_args[0]}, and thank them for visiting!',
        '!project': 'Currently, we have no idea what we are doing.',
        '!keyboard': 'Absenth762 is using an ErgodoxEZ with C3 Equalz Kiwi switches. https://ergodox-ez.com/',
        '!repo': 'The source code for all of this is likely here: https://github.com/absenth/stream-projects',
        '!wrong': "@absenth762, you're doing it wrong... Stop doing it wrong!",
}

Message = namedtuple(
    'Message',
    'prefix user channel irc_command irc_args text text_command text_args',
)


FILE = 'commands.csv'


class Bot:
    def __init__(self):
        self.irc_server = 'irc.twitch.tv'
        self.irc_port = 6667
        self.oauth_token = os.getenv('TWITCH_OAUTH_TOKEN')
        self.username = 'botsenth545'
        self.channels = ['absenth762']
        # Testing
        #self.channels = ['krazynez_2']

    def send_privmsg(self, channel, text):
        self.send_command(f'PRIVMSG #{channel} :{text}')

    def send_command(self, command):
        if 'PASS' not in command:
            print(f'< {command}')
        self.irc.send((command + '\r\n').encode())

    def connect(self):
        self.irc = socket.socket()
        self.irc.connect((self.irc_server, self.irc_port))
        self.send_command(f'PASS {self.oauth_token}')
        self.send_command(f'NICK {self.username}')
        for channel in self.channels:
            self.send_command(f'JOIN #{channel}')
            self.send_privmsg(channel, 'Hello Mortals')
        self.loop_for_messages()

    def get_user_from_prefix(self, prefix):
        domain = prefix.split('!')[0]
        if domain.endswith('.tmi.twitch.tv'):
            return domain.replace('.tmi.twitch.tv', '')
        return None

    def parse_message(self, received_msg):
        parts = received_msg.split(' ')

        prefix = None
        user = None
        channel = None
        text = None
        text_command = None
        text_args = None
        irc_command = None
        irc_args = None

        if parts[0].startswith(':'):
            prefix = parts[0][1:]
            user = self.get_user_from_prefix(prefix)
            parts = parts[1:]

        text_start = next(
            (idx for idx, part in enumerate(parts) if part.startswith(':')),
            None
        )
        if text_start is not None:
            text_parts = parts[text_start:]
            text_parts[0] = text_parts[0][1:]
            text = ' '.join(text_parts)
            text_command = text_parts[0]
            text_args = text_parts[1:]
            parts = parts[:text_start]

        irc_command = parts[0]
        irc_args = parts[1:]

        hash_start = next(
                (idx for idx, part in enumerate(irc_args) if part.startswith('#')),
                None
        )
        if hash_start is not None:
            channel = irc_args[hash_start][1:]

        message = Message(
                prefix=prefix,
                user=user,
                channel=channel,
                text=text,
                text_command=text_command,
                text_args=text_args,
                irc_command=irc_command,
                irc_args=irc_args,
        )
        return message

    def handle_template_command(self, message, template):
        #text = template.format(**{'message': message,})
        for i, m in enumerate(template):
            text = m.format(**{'message': message,}) 
        self.send_privmsg(message.channel, text)


    def handle_message(self, received_msg):

        if len(received_msg) == 0:
            return

        message = self.parse_message(received_msg)
        #print(f'> {message}')

        if message.irc_command == 'PING':
            self.send_command('PONG :tmi.twitch.tv')

        if message.irc_command == 'PRIVMSG':
            if os.path.isfile(FILE):
                df = pd.read_csv(FILE)
                
                for commands in pd.read_csv(FILE)['Commands']:
                    if commands.replace(" ", "") in message:
                        row = df.index[df['Commands'] == commands.replace(" ", "")].tolist()
                        out = df['Output'][row]
                        self.handle_template_command(
                                message,
                                out
                        )
            elif message.text_command in TEMPLATE_COMMANDS:
                self.handle_template_command(
                    message,
                    TEMPLATE_COMMANDS[message.text_command],

                )

    def loop_for_messages(self):
        while True:
            received_msgs = self.irc.recv(2048).decode()
            for received_msg in received_msgs.split('\r\n'):
                self.handle_message(received_msg)


def main():
    bot = Bot()
    bot.connect()


if __name__ == '__main__':
    main()
