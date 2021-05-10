import os
import time
import logging
import datetime as dt

import requests
import telegram

from dotenv import load_dotenv

import error

load_dotenv()

# constants
# tokens
PRAKTIKUM_TOKEN = os.environ.get('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
if PRAKTIKUM_TOKEN is None or TELEGRAM_TOKEN is None or CHAT_ID is None:
    logging.exception('Нет необходимого токена в .env')
    raise SystemExit('Не удалось получить токены')

# links
ROOT_LINK = 'https://praktikum.yandex.ru/'
API_LINK = f'{ROOT_LINK}api/'
USER_API_LINK = f'{API_LINK}user_api/'
HOMEWORK_STATUSES_API_LINK = f'{USER_API_LINK}homework_statuses/'

# time
REQUEST_RATE = 1200
ERROR_TIME_SLEEP = 5

# messages
STATUSES_MESSAGES = {
    'reviewing': 'Работа "{homework_name}" взята в ревью.',
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, '
                'можно приступать к следующему уроку.'
}

# params
STATUSES_MESSAGES_HEADERS = {
    'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
}


def parse_homework_status(homework):
    """Used to return string status of homework.

    Attributes:
    homework - JSON of homeworks status
    """
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if homework_name is None or status is None:
        raise error.PraktikumApiError('API вернул поле с None')
    elif status not in STATUSES_MESSAGES:
        raise error.PraktikumApiError('Нужного статуса нет в списке')
    message = STATUSES_MESSAGES[status]
    return (f'У вас проверили работу "{homework_name}"!'
            f'\n\n{message.format(homework_name=homework_name)}')


def get_homework_statuses(current_timestamp):
    """Used to return JSON of request.

    Attributes:
    current_timestamp - current time in unix
    """
    try:
        dt.datetime.utcfromtimestamp(current_timestamp)
    except TypeError:
        current_timestamp = int(time.time())
    finally:
        params = {'from_date': current_timestamp}
        response_params = dict(
            url=HOMEWORK_STATUSES_API_LINK,
            params=params,
            headers=STATUSES_MESSAGES_HEADERS
        )
        try:
            response = requests.get(**response_params)
        except requests.exceptions.RequestException as e:
            raise error.PraktikumApiError(f'Проблема с запросом к API: {e}\n'
                                          f'Параметры: {params}')
        homework_statuses = response.json()
        if 'error' in homework_statuses or 'code' in homework_statuses:
            error_explanation = homework_statuses.get('error')
            code_explanation = homework_statuses.get('code')
            raise error.PraktikumApiError(
                'Произошла ошибка при запросе к API: '
                f'{error_explanation}, {code_explanation}\n'
                f'Параметры: {params}'
            )
        elif response is None:
            logging.error('API вернул None\n'
                          f'Парамтеры: {params}')
            return dict()
        return homework_statuses


def send_message(message, bot_client):
    """Used to return send_message object.

    Attributes:
    message - text to send
    bot_client - telegram.Bot object
    """
    try:
        return bot_client.send_message(chat_id=CHAT_ID, text=message)
    except telegram.error.TelegramError as e:
        raise telegram.error.TelegramError(
            f'Проблема при отправке сообщения. {e}'
        )


def main():
    """Used to polling bot and get request from API."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    try:
        bot.get_me()
    except telegram.error.TelegramError:
        logging.exception('Проблема с созданием бота')
        raise SystemExit('Не удалось создать бота')
    current_timestamp = int(time.time()) - 1000000

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                message = send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client=bot
                )
                logging.info('Сообщение отправлено\n'
                             f'Текст: {message.text}')
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(REQUEST_RATE)

        except Exception as e:
            message = f'Бот столкнулся с ошибкой: {e}'
            logging.exception(e)
            bot.send_message(chat_id=CHAT_ID, text=message)
            time.sleep(ERROR_TIME_SLEEP)


if __name__ == '__main__':
    path = '~/homework.log'
    logging.basicConfig(
        level=logging.DEBUG,
        filename=os.path.expanduser(path),
        filemode='w',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    )
    logging.debug('Бот запущен')
    main()
