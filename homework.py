import os
import time
import logging
import datetime as dt

import requests
import telegram

from dotenv import load_dotenv

import constants
import error

load_dotenv()


PRAKTIKUM_TOKEN = os.environ.get('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
if PRAKTIKUM_TOKEN is None or TELEGRAM_TOKEN is None or CHAT_ID is None:
    logging.exception('Нет необходимого токена в .env')
    raise SystemExit('Не удалось получить токены')


def parse_homework_status(homework):
    """Used to return string status of homework.

    Attributes:
    homework - JSON of homeworks status
    """
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if (homework_name is None or status is None
            or status not in constants.STATUSES_MESSAGES):
        raise error.PraktikumApiError('API вернул поле с None')
    message = constants.STATUSES_MESSAGES[status]
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
        try:
            headers = {
                'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
            }
            params = {'from_date': current_timestamp}
            response = requests.get(
                constants.HOMEWORK_STATUSES_API_LINK,
                params=params,
                headers=headers
            )
        except requests.exceptions.RequestException:
            raise error.PraktikumApiError('Проблема с запросом к API')
        homework_statuses = response.json()
        if 'error' in homework_statuses:
            error_explanation = homework_statuses.get('error')
            raise error.PraktikumApiError(
                f'Произошла ошибка при запросе к API: {error_explanation}'
            )
        elif 'code' in homework_statuses:
            code_explanation = homework_statuses.get('code')
            raise error.PraktikumApiError(
                f'Произошла ошибка при запросе: {code_explanation}'
            )
        elif response is None:
            logging.error('API вернул None')
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
    logging.basicConfig(
        level=logging.DEBUG,
        filename='homework.log',
        filemode='w',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
    )
    logging.debug('Бот запущен')
    main()
