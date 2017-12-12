from celery import Celery
from time import sleep
from ejudge import run
import re

app = Celery('tasks', backend='rpc://', broker='pyamqp://guest@localhost//', namespace='CELERY')


@app.task
def add(x, y):
    return x / y

@app.task
def test_code(src, lang, input, output):
    spec = run(src, [input], lang=lang)
    out_array = spec[0].to_json()['data']
    real_output = ""
    for out in out_array:
        if 'Out' == out[0]:
            real_output += " " + out[1]

    # Replace all spacing characters with a single space.
    real_output = re.sub(r"\s+", " ", real_output, flags=re.UNICODE)

    if real_output == output:
        result = "OK"
    else:
        result = "FA"

    return result
