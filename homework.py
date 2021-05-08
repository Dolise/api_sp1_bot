import os
import time
import logging
import datetime as dt

import requests
import telegram

from dotenv import load_dotenv

import constants

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='homework.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)

PRAKTIKUM_TOKEN = os.environ.get('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')


def parse_homework_status(homework):
    """Used to return string status of homework.

    Attributes:
    homework - JSON of homeworks status
    """
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    statuses_messages = {
        'reviewing': f'Работа {homework_name} взята в ревью.',
        'rejected': 'К сожалению в работе нашлись ошибки.',
        'approved': ('Ревьюеру всё понравилось, '
                     'можно приступать к следующему уроку.')
    }
    if homework_name is None or status is None\
            or status not in statuses_messages:
        raise telegram.error.TelegramError('Ошибка API')
    return (f'У вас проверили работу "{homework_name}"!'
            f'\n\n{statuses_messages[status]}')


def get_homework_statuses(current_timestamp):
    """Used to return JSON of request.

    Attributes:
    current_timestamp - current time in unix
    """
    try:
        dt.datetime.utcfromtimestamp(current_timestamp)
    except TypeError:
        raise TypeError('Проблемы с current_timestamp')
    else:
        headers = {
            'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
        }
        params = {'from_date': current_timestamp}
        homework_statuses = requests.get(
            constants.HOMEWORK_STATUSES_API_LINK,
            params=params,
            headers=headers
        )
        if homework_statuses is None:
            logging.error('API вернул None')
            return dict()
        return homework_statuses.json()


def send_message(message, bot_client):
    """Used to return send_message object.

    Attributes:
    message - text to send
    bot_client - telegram.Bot object
    """
    try:
        return bot_client.send_message(chat_id=CHAT_ID, text=message)
    except telegram.error.TelegramError as e:
        raise telegram.error.TelegramError(f'Проблема с телеграмом. {e}')


def main():
    """Used to polling bot and get request from API."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    try:
        bot.get_me()
    except telegram.error.TelegramError:
        logging.exception('Проблема с созданием бота')
        raise SystemExit('Не удалось создать бота')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client=bot
                )
            logging.info('Сообщение отправлено')
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(constants.REQUEST_RATE)

        except Exception as e:
            message = f'Бот столкнулся с ошибкой: {e}'
            logging.exception(e)
            bot.send_message(chat_id=CHAT_ID, text=message)
            time.sleep(constants.ERROR_TIME_SLEEP)


if __name__ == '__main__':
    logging.debug('Бот запущен')
    main()
