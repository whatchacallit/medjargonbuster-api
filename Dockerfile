FROM openjdk:slim
COPY --from=python:3.9.1 / /

ENV LOG_LEVEL debug
ENV WEB_CONCURRENCY 2


WORKDIR /medjargonbuster


###############################################################################################
########## Med Jargon Buster - API server 
###############################################################################################


# Install spacy requirments separately first so that Docker will 
# cache the (somewhat) expensive download of a spacy language model
COPY requirements-spacy.txt ./requirements-spacy.txt
RUN pip install -r requirements-spacy.txt

# Install everything else
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt



# This is where python tika expects the .jar - otherwise it will download it on first request, 
# which makes for a long cold start
# see: http://search.maven.org/remotecontent?filepath=org/apache/tika/tika-server/1.24/tika-server-1.24.jar
COPY tika/tika-server* /tmp/

COPY main.py main.py
COPY ./app ./app



EXPOSE 5000
WORKDIR /medjargonbuster

ENTRYPOINT ["uvicorn", "--host", "0.0.0.0",  "--port", "5000", "main:app"]