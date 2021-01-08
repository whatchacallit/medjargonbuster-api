## This is the next version of the Medical Jargon Buster Backend API
Key libraries used:
- FastAPI
- Spacy
- Packages from Spacy Universe:
    -   https://allenai.github.io/scispacy/ (problem w. numpy https://developercommunity.visualstudio.com/content/problem/1207405/fmod-after-an-update-to-windows-2004-is-causing-a.html)
    - https://kindred.readthedocs.io/en/stable/
    - https://github.com/medspacy/medspacy
    - https://github.com/NIHOPA/NLPre
    - https://github.com/nipunsadvilkar/pySBD


https://scispacy.apps.allenai.org/



python -m venv .env
source .env/bin/activate
pip install -U pip setuptools wheel
pip install spacy

python -m spacy download en_core_web_sm

python -m spacy validate

https://allenai.github.io/scispacy/
