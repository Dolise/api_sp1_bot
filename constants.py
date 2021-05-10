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
        'approved': ('Ревьюеру всё понравилось, '
                     'можно приступать к следующему уроку.')
}

