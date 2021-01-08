import requests


def run_pipeline(base_url, text, meta, settings):
    url = f"{base_url}/pipeline/default"
    data = {"text": text, "meta": meta, "settings": settings}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json()
    else:
        result = {"text": f"<Error: {response}>", "meta": {}}
    return result