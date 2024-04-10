# Wagtail Model Maker

## Run locally

`docker build -t model_maker .`
`docker run -p 8000:8000 model_maker`

## CLI usage

- Make the page models: `python modelmaker.py "a blog page with a date, image and rich text body"`
- Ask for help refining the description: `python modelmaker.py -r "a blog page with a date, image and rich text body"`

## Deploy

`fly deploy`
