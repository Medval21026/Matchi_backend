release: python manage.py migrate --noinput
web: gunicorn reservation_cite.wsgi:application --bind 0.0.0.0:$PORT
