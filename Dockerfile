FROM openjdk:slim
COPY --from=python:3.9 / /

ENV LOG_LEVEL debug
ENV WEB_CONCURRENCY 2


WORKDIR /app


# Install spacy requirments separately first so that Docker will 
# cache the (somewhat) expensive download of a spacy model
COPY ./requirements/spacy.txt ./requirements/spacy.txt
RUN pip install -r requirements/spacy.txt
RUN spacy download english

COPY ./requirements/base.txt ./requirements/base.txt
RUN pip install -r requirements/base.txt


###############################################################################################
########## PYTHON 
###############################################################################################

COPY ./app /app/app
# This is where python tika expects the .jar - otherwise it will download it on first request, 
# which makes for a long cold start
COPY tika/tika-server* /usr/tmp/


EXPOSE 5000
WORKDIR /app/app

ENTRYPOINT ["uvicorn", "--host", "0.0.0.0",  "--port", "5000", "api:app"]