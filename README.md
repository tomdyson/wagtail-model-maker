# Wagtail Model Maker

LLM-powered Web UI and CLI for stubbing out Wagtail page models

![screenshot](https://github.com/tomdyson/wagtail-model-maker/assets/15543/d29327b5-6732-49f8-95fa-d5ec1ed6aba9)

## Run the web interface locally

In a virtual environment:

```bash
export ANTHROPIC_API_KEY=your_api_key
pip install -r requirements.txt
python api.py
```

or with Docker:

```bash
docker build -t model_maker .
docker run --env ANTHROPIC_API_KEY=your_api_key -p 8000:8000 model_maker
```

## CLI usage

Make the page models:

```bash
python modelmaker.py "a blog page with a date, image and rich text body"
```

Ask for help refining the description:

```bash
python modelmaker.py -r "a blog page with a date, image and rich text body"
```

## Deploy

```bash
fly deploy
```
