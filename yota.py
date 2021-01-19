import uuid
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import logging
import logging.handlers
from datetime import datetime
from pytz import timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

ylog = logging.getLogger('ylogger')
ylog.setLevel(logging.DEBUG)

def timetz(*args):
    return datetime.now(tz).timetuple()

tz = timezone('Europe/Moscow')

logging.Formatter.converter = timetz

handler = logging.handlers.TimedRotatingFileHandler(Path(BASE_DIR, 'yota.log'), when="midnight", interval=1, backupCount=30)
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(filename)s %(lineno)d %(threadName)s - %(message)s"))
ylog.addHandler(handler)

headers = {
    'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) ApaymentIdleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'
}

s = requests.Session()
try:
    resp = s.get("http://ya.ru", headers=headers, verify=False, allow_redirects=False)
    ylog.debug('Connected')
except:
    # Если отвалился модем или пропал сигнал, ждем 5 секунд и пробуем еще раз
    ylog.debug('Retry')

# Если Яндекс пытается редиректить с http на https, то интернет работает
# Будем ждать 60 секунд и проверим еще раз
if resp.headers['Location'] != 'https://ya.ru/':
    # Зайдем на hello.yota.ru, чтобы получить cookies
    url = "https://hello.yota.ru"
    try:
        resp = s.get(url, headers=headers, verify=False)
    except:
        pass

    # Сгенерируем номер транзации. Все последующие запросы должны проходить с этим номером в заголовке
    transaction = str(uuid.uuid4())

    # Получаем какие-то настройки. Не вдавался в подробности, какие именно, но так делает сайт
    url = "https://hello.yota.ru/wa/v1/info/sa"

    headers = {
        'User-agent':                   'Mozilla/5.0 (Windows NT 6.1; WOW64) ApaymentIdleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
        'Authority':                    'hello.yota.ru',
        'Origin':                       'https://hello.yota.ru',
        'x-compress':                   'null',
        'x-transactionid':              transaction,
        'Upgrade-Insecure-Requests':    '1',
        'Content-Type':                 'application/json',
        'Accept':                       'application/json, text/plain, */*',
        'Referer':                      'https://hello.yota.ru/light?redirurl=http:%2F%2Fya.ru%2F'
    }

    try:
        resp = s.get(url, headers=headers, verify=False)
    except:
        pass
    ylog.debug([url, headers, resp.status_code, resp.text, resp.headers])

    url = "https://hello.yota.ru/wa/v1/service/temp"

    # Дальше два варианта, как я понял
    # Первый: если в личном кабинете устройство переведено на бесплатный тариф, то надо раз в сутки делать так
    data = '{"serviceCode":"light"}'
    try:
        resp = s.post(url, data=data, headers=headers, verify=False)
    except:
        pass
    ylog.debug([url, data, resp.status_code, resp.text, resp.headers])

    # Dnjhjq: если в личном кабинете устройство не переведено на бесплатный тариф, а просто закончились деньги,
    # то надо раз в 2 часа делать так
    data='{"serviceCode":"sa"}'
    try:
        resp = s.post(url, data=data, headers=headers, verify=False)
    except:
        pass
    ylog.debug([url, data, resp.status_code, resp.text, resp.headers])
