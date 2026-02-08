release: echo 'Starting migrations...' && python manage.py migrate --noinput && echo 'Migrations completed!'
web: gunicorn reservation_cite.wsgi:application --bind 0.0.0.0:$PORT
