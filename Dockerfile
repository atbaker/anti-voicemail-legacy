# Dockerfile for Anti-Voicemail
# https://github.com/atbaker/anti-voicemail

FROM python:3-onbuild

EXPOSE 5000

CMD gunicorn manage:app --bind=0.0.0.0 --log-file=-
