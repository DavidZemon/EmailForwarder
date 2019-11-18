#!/usr/bin/python3
import imaplib
import json
import os
import smtplib
import typing

CREDENTIALS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'credentials.json')
DEFAULT_DOMAIN = '@slwg.org'
IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 465
MSG_LINE_SEPARATOR = '\r\n'


class User:
    def __init__(self, src: str, dst: str, name: str, password: str) -> None:
        super().__init__()
        self.source = src
        self.destination = dst
        self.name = name
        self.password = password

    def __str__(self) -> str:
        return f'"{self.name}"/{self.source} -> {self.destination} ({self.password})'


def main() -> None:
    with open(CREDENTIALS_FILE_PATH, 'r') as f:
        credentials_json: typing.Dict[str, typing.Dict[str, str]] = json.loads(f.read())

    credentials: typing.List[User] = []
    for src, user in credentials_json.items():
        if '@' not in src:
            src += DEFAULT_DOMAIN
        credentials.append(User(src, user['destination'], user['name'], user['password']))

    for user in credentials:
        messages = read_mail(user)
        send_mail(user, messages)


def read_mail(user: User) -> typing.List[bytes]:
    with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as imap_server:
        imap_server.login(user.source, user.password)
        print(f'Successful IMAP login for {user}')
        try:
            imap_server.select(readonly=True)
            status, msg_nums = imap_server.search(None, 'SINCE', '15-Sep-2019', 'BEFORE', '17-Nov-2019')
            assert status == 'OK', f'Expected typ to be "OK" but got {status} from search'
            messages: typing.List[bytes] = []
            for m in msg_nums[0].decode().split():
                status, data = imap_server.fetch(m, '(RFC822)')
                assert status == 'OK', f'Expected typ to be "OK" but got {status} from fetch'
                messages.append(data[0][1])
        finally:
            imap_server.logout()
    return messages


def send_mail(u: User, messages: typing.List[bytes]):
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp_server:
        smtp_server.login(u.source, u.password)
        print(f'Successful SMTP login for {u}')
        try:
            # msg = messages[0]
            # lines = msg.decode().split(MSG_LINE_SEPARATOR)
            # from_address_line = list(filter(lambda l: l.startswith('From: '), lines))[0]
            # from_index = lines.index(from_address_line)
            # lines[from_index] = f'From: {u.source}'
            # lines.insert(from_index + 1, from_address_line.replace('From:', 'Reply-To:'))
            # message = MSG_LINE_SEPARATOR.join(lines)
            failures = smtp_server.sendmail(u.source, u.destination, messages[0])
            for dst, reason in failures.items():
                print(f'Failed to deliver message to {dst} due to {reason}')
        except Exception as e:
            print(f'Failed to send message from {u.source} -> {u.destination} due to {e}')


if __name__ == '__main__':
    main()
