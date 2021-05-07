FROM python:3.7-slim

# Package gettext-base provides envsubst which is used by ./tools/mkconf.sh
# To use compiled version of uWSGI replace "uwsgi uwsgi-plugin-python3" by
#   "gcc libpcre3-dev"
RUN apt-get update && \
    apt-get install -y --no-install-recommends gettext-base make uwsgi uwsgi-plugin-python3 && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash vino

USER vino

ENV PATH "/home/vino/.local/bin:$PATH"

WORKDIR /home/vino

COPY --chown=vino . .

RUN make init && \
    rm -fr data/static/ && \
    pipenv run ./manage.py collectstatic --no-input

# Uncomment this line to use compiled version of uWSGI
#RUN pipenv run pip install uwsgi

RUN mkdir -p data/logs

EXPOSE 8000

CMD ["pipenv", "run", "uwsgi", "./tools/docker/uwsgi.ini"]
