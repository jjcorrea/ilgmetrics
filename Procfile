#web: gunicorn metrics.wsgi
web: python metrics/manage.py collectstatic --noinput; bin/gunicorn_django --workers=4 --bind=0.0.0.0:$PORT metrics/settings.py 
