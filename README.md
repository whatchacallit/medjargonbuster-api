# SumMed - API + Backend

This is the backend server and REST API for the https://summed.org project.

# Overview

This backend is acting as a facade to different NLP services and APIs.

On the highest level, these are the backend responsibilities:
- **extract**: extract text and metadata from different document types (e.g. .pdf, word, .jpeg, .html ...). 
Supports public URLs (e.g. to news articles, blog posts, hosted documents ...) and HTTP file upload.
- NLP analysis: execute a spaCy NLP analysis pipeline. 
This will enrich with additional meta-data, automatic (extractive) summary, medical named entity recognition, story generation etc.
Results from the NLP stages are aggregated and filtered into before sending it back to client.
- Medical dictionary: A simplified and integrated way of looking up terms in a medical dictionary, e.g. via Merrial-Webster API
- Token exchange, auth: Supports clients to securely get access API tokens (e.g. for Immersive reader) and auth flows. Called by the frontend.


## Tech Stack
* Python 3.8+
* pip / pip3
* spaCy 2.x
* FastAPI / uvicorn
* Starlette
* Pydantic
* Apache Tika
* Python lib: "wikipedia"
* Python lib: "newspaper3k"
* Azure Services
  * 
* 3rd party Cloud APIs
 * 
# Run locally
You can run, test, debug the API server locally. 
However, some text processing steps will require calling external (REST) services, such as Azure Cognitive services.
You need to configure the services before, and set the credentials in the ```'.env'``` file (see below).
## Local setup
```python
# clone repository
git clone https://github.com/whatchacallit/medjargonbuster-api

# Create & activate local Python mvirtual environment
python -m venv venv
source ./venv/Scripts/activate
# Install dependencies
pip install -f requirements.txt

```

### The .env file 
See ```.env.example``` for available (amd sometimes required) credentials. 


## Launch/Debug the API Server
Start it with: 
```python
python main.py
```
In Visual Studio code, you can also use the debug launch config in ```.vscode/launch.json``` to start the server in debug mode.
After uvicorn is up, go to http://localhost:5000/docs (or http://localhost:5000/redoc) to explore the API

## Run Med Jargon Buster Studio
Jargon Buster Studio is a small local app powered by **Streamlit**. 
Once you have the API server running (locally or remote), 
it can be used to test and explore the API.

```python
cd studio
run_studio.sh
```

## Run Tests
For contributors, you can run Test implemented via pytest:
```python
cd tests
pytest .
```

# Deploy on Azure using Github Actions
We use GitHub Actions to deploy to Azure. If you want to run your own installation on Azure,
please see below. It also shouldn't be too complicated to deploy this on other platforms, but you'll be on your own.

See the docs for using GitHub Actions for Containers to deploy to Azure App Service.
https://docs.microsoft.com/en-us/azure/app-service/deploy-container-github-action?tabs=publish-profile

# Prerequisites
Do a fork of this repository on GitHub.

# Create Azure Web App 
Portal, or via az CLI:

Also, 
set WEBSITE_WEBDEPLOY_USE_SCM =true

# Create a Publish Profile
Save the publish profile to a local file.
You can do this in the Azure portal Overview page of your App Service, 
or use the CLI:
```
az ...
```


