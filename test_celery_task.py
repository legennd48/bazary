from bazary.celery import app

@app.task
def test_celery():
    return "Celery is working!"

# To test, run this in Django shell:
# result = test_celery.delay()
# print(result.get(timeout=10))