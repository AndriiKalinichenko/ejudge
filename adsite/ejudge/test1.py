from celery.result import AsyncResult

from tasks import add
from time import sleep

from iospec import parse

str1 = """
Say your name: <john>
Hello, John!
"""
tree = parse(str1)
print(tree[0].to_json()['data'][0])



exit()

res = add.delay(2, None)
while not res.ready():
    # res = AsyncResult(res.id)
    print(res.ready())
    sleep(1)

print(res.ready())
print(res.result)
