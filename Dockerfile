FROM python:3.10.6-alpine

ENV APP_DIR /src
ENV PYTHONPATH $PYTHONPATH:$APP_DIR

WORKDIR $APP_DIR

RUN python -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt --no-cache-dir && rm -f requirements.txt

COPY src $APP_DIR
CMD python viewer.py