import os
import time
import logging

import requests
import telegram

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='homework.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def parse_homework_status(homework):
    """Used to return string status of homework.

    Attributes:
    homework - JSON of homeworks status
    """
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if status == 'reviewing':
        return f'Работа {homework_name} взята в ревью.'

    if status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = ('Ревьюеру всё понравилось, '
                   'можно приступать к следующему уроку.')
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    """Used to return JSON of request.

    Attributes:
    current_timestamp - current time in unix
    """
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
    }
    params = {'from_date': current_timestamp}
    link = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    homework_statuses = requests.get(
        link,
        params=params,
        headers=headers
    )
    return homework_statuses.json()


def send_message(message, bot_client):
    """Used to return send_message object.

    Attributes:
    message - text to send
    bot_client - telegram.Bot object
    """
    logging.info('Сообщение отправлено')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    """Used to polling bot and get request from API."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(
                        new_homework.get(
                            'homeworks'
                        )[0]
                    ),
                    bot_client=bot
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(1200)

        except Exception as e:
            message = f'Бот столкнулся с ошибкой: {e}'
            logging.error(e)
            bot.send_message(chat_id=CHAT_ID, text=message)
            print(message)
            time.sleep(5)


if __name__ == '__main__':
    logging.debug('Бот запущен')
    main()
