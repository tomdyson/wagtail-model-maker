# Wagtail Model Maker

## Run the web interface locally

In a virtual environment:

```bash
export CLAUDE_API_KEY=your_api_key
pip install -r requirements.txt
python api.py
```

or with Docker:

```bash
docker build -t model_maker .
docker run --env CLAUDE_API_KEY=your_api_key -p 8000:8000 model_maker
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