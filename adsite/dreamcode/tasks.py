from celery import Celery
from time import sleep
from ejudge import run
import re

app = Celery('tasks', backend='rpc://', broker='pyamqp://guest@localhost//', namespace='CELERY')


@app.task
def add(x, y):
    return x / y

@app.task
def test_code(src, lang, i_input, i_output):
    with open(str(i_input), 'r') as myfile:
        inp_scr = myfile.read()
    with open(str(i_output), 'r') as myfile:
        out_scr = myfile.read()
    spec = run(src, [inp_scr], lang=lang)
    out_array = spec[0].to_json()['data']

    real_output = ""
    for out in out_array:
        if 'Out' == out[0]:
            real_output += out[1]

    if str(real_output) == str(out_scr)[0:-1]:
        result = "OK"
        print("OK")
    else:
        result = "FA"
        print("FA")

    return result
