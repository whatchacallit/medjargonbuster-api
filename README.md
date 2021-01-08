# Med Jargon Buster - API Server


PLEASE wait, docs in progress ;)


# Project Vision
TBD

# Architecture Overview

Overview diagram:



This is a monolith backend, acting as a facade to different NLP services and APIs.
On the highest level, these are thre API server responsibilities:
* extract: extract text and metadata from different document types (e.g. .pdf, word, .jpeg, .html ...). 
Supports public URLs (e.g. to news articles, blog posts, hosted documents ...) and HTTP file upload.
* NLP analysis: execute a spaCy NLP analysis pipeline. 
This will enrich with additional meta-data, automatic (extractive) summary, medical named entity recognition, story generation etc.
Results from the NLP stages are aggregated and filtered into before sending it back to client.
* Medical dictionary: A simplified and integrated way of looking up terms in a medical dictionary, e.g. via Merrial-Webster API
* Token exchange, auth: Supports clients to securely get access API tokens (e.g. for Immersive reader) and auth flows


For detailied technical and architecture docs, please go to our technical docs site: xxxx

# Run locally
You can run, test, debug the API server locally. 
However, some text processing steps will require calling external (REST) services, such as Azure Cognitive services.
You need to configure the services before, and set the credentials in the ```'.env'``` file (see below).

## Prerequisites
* Python 3.8+
* pip / pip3
* bash terminal (if powershell etc, please adapt the steps below accordingly)
* Optional:
  * Model xxxx

## Local setup
```python
# clone repository
git clone ....

# Create & activate local Python mvirtual environment
python -m venv venv
source ./venv/Scripts/activate
# Install dependencies
pip install -f requirements.txt

```

### The .env file 
See ```.env.example``` for available (amd sometimes required) credentials. 


## Launch/Debug the API Server
The API is implemeneted with FastAPI, uvicorn, Starlette, Pydantic, spaCy
Start it with: 
```python
python main.py
```

In Visual Studio code, you can also use the debug launch config in ```.vscode/launch.json``` to start the server in debug mode.

After uvicorn is up, go to http://localhost:5000/docs (or http://localhost:5000/redoc) to explore the API

## Run Med Jargon Buster Studio
Jargon Buster Studio is a small local app powered by Streamlit. Once you have the API server running (locally or remote), 
it can be used to test and explore the API. Maybe event more, in the future.

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



# Links and resources

## Med Jargon Buster
* Homepage
* Technical documentation

* Presentation 1
* Presentation 2
* Demo Video
* Miro Whiteboard

## APIs, Cloud Services and Libraries
* Azure Computer Vision
* Azure Text Analytics
* Azure Text Analytics for Health
* Azure Immersive Reader

* Abbyy Cloud OCR - SDK
* Merriam-Webster Medical Dictionary v3 API


* spaCy
* FastAPI
* Starlette
* Pydantic
* Apache Tika
* Python lib: "wikipedia"
* Python lib: "newspaper3k"

## Research Paper
* ...
* ...




# Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.microsoft.com.

When you submit a pull request, a CLA-bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
