import argparse
import base64
import os
import re
import subprocess

import anthropic
from openai import OpenAI

API_PROVIDER = "anthropic"

SYSTEM_PROMPT = """
You are a tool which helps Wagtail developers write their page models. 
They describe the structure of their pages in a declarative way, and 
you generate the code for them. If the developer says 
'A page with a title and a body', you reply with the code for a 
model with a title and a body field, including the necessary imports 
and boilerplate code. Only return the Python code, don't provide an explanation.

Remember that Wagtail pages already have title fields, so you 
don't need to include them in the model. 

Current Wagtail models use 'FieldPanel' for images, not 'ImageChooserPanel'.

For example, if the developer says "A blog page with a date field called 'Post date',
an intro field, an image, and a rich text body field", you should reply with:

```python
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.search import index

class BlogPage(Page):
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    image = models.ForeignKey(
        "wagtailimages.Image", on_delete=models.CASCADE, related_name="+"
    )
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("intro"),
        FieldPanel("image"),
        FieldPanel("body"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]
```

Don't say "here's the code", just return the code. The first line of your 
response should be '```python' and the last line should be '```'.
"""

IMAGE_PROMPT = """
You are a tool which helps Wagtail developers write their page models. 
They provide a screenshot of an existing page, and  
you generate the code for them, including the necessary imports. 
Only return the Python code, don't provide an explanation.

Remember that Wagtail pages already have title fields, so you 
don't need to include them in the model. 

Current Wagtail models use 'FieldPanel' for images, not 'ImageChooserPanel'.

For example, if the the screenshot shows a blog page with a title, a date, 
an intro, an image, and a rich text body, you could reply with:

```python
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.search import index

class BlogPage(Page):
    date = models.DateField()
    intro = models.CharField(max_length=250)
    image = models.ForeignKey(
        "wagtailimages.Image", on_delete=models.CASCADE, related_name="+"
    )
    body = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("intro"),
        FieldPanel("image"),
        FieldPanel("body"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]
```

Don't say "here's the code", just return the code. The first line of your 
response should be '```python' and the last line should be '```'.
"""

REFINE_PROMPT = """
You are a tool which helps Wagtail developers write their page models. 
They describe the structure of their pages in a declarative way, and 
another tool will generate the code for them. Respond to their description 
with a more precise version which will help the code generator produce better results.
Don't include title or slug fields, as Wagtail pages already have them. Don't explain 
your suggestions, just provide a more detailed description. Include suggested constraints 
(e.g. 'required', 'optional') and field types (e.g. 'date', 'rich text'). Use natural 
language for the field types, not the Django or Wagtail model field names.
"""

EXAMPLE_PROMPT = """
An event page with a title, a rich text body field called 'description' (optional), a hero image 
called 'lead image' (required), and a date field called 'launch date'.
"""


def extract_code(response):
    # Regular expression pattern to match markdown code blocks with language name
    pattern = r"```(?:python)?(.*?)```"

    if match := re.search(pattern, response, re.DOTALL):
        # If a markdown code block is found, return its contents without the language name
        return match[1].strip()
    else:
        # If no markdown code block is found, return the whole response
        return response.strip()


def usage_cost(usage):
    input_token_cost = 3 / 1000000  # https://www.anthropic.com/api
    output_token_cost = 15 / 1000000
    cost = (usage["input_tokens"] * input_token_cost) + (
        usage["output_tokens"] * output_token_cost
    )
    return f"${cost:.3f}"


def ask_claude(description, system_prompt):
    # Claude API wrapper
    resp = anthropic.Anthropic().messages.create(
        model="claude-3-5-sonnet-20240620", # claude-3-5-sonnet-20240620 or claude-3-opus-20240229
        temperature=0,
        system=system_prompt,
        max_tokens=2048,
        messages=[{"role": "user", "content": description}],
    )
    answer = resp.content[0].text
    usage = {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
    }
    return answer, usage


def ask_openai(description, system_prompt):
    print("OpenAI")
    client = OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": description},
        ],
    )
    answer = resp.choices[0].message.content
    usage = {
        "input_tokens": resp.usage.prompt_tokens,
        "output_tokens": resp.usage.completion_tokens,
    }
    return answer, usage


def ask_claude_image(image_path, image_prompt):
    image_media_type = "image/png"
    image_data = open(image_path, "rb").read()
    encoded_image_data = base64.b64encode(image_data).decode("utf-8")
    resp = anthropic.Anthropic().messages.create(
        model="claude-3-opus-20240229",
        temperature=0,
        system=image_prompt,
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_media_type,
                            "data": encoded_image_data,
                        },
                    }
                ],
            }
        ],
    )
    answer = resp.content[0].text
    usage = {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
    }
    # delete image file
    os.remove(image_path)
    return answer, usage


# def make_model(description):
#     code, usage = ask_claude(description, SYSTEM_PROMPT)
#     code = extract_code(code)
#     return code, usage


def make_model(description, api=API_PROVIDER):
    if api == "anthropic":
        code, usage = ask_claude(description, SYSTEM_PROMPT)
    elif api == "openai":
        code, usage = ask_openai(description, SYSTEM_PROMPT)
    code = extract_code(code)
    return code, usage


def make_model_from_image(image_path):
    code, usage = ask_claude_image(image_path, IMAGE_PROMPT)
    code = extract_code(code)
    return code, usage


def suggest_improvements(description, api=API_PROVIDER):
    if api == "anthropic":
        improvements, usage = ask_claude(description, REFINE_PROMPT)
    elif api == "openai":
        improvements, usage = ask_openai(description, REFINE_PROMPT)
    return improvements, usage


def format_python(code):
    try:
        return subprocess.check_output(
            ["ruff", "format", "--line-length", "76", "-"], input=code, encoding="utf-8"
        )
    except subprocess.CalledProcessError:
        return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Wagtail page models")
    parser.add_argument(
        "text", nargs="?", default=EXAMPLE_PROMPT, help="Page model description"
    )
    parser.add_argument(
        "-r",
        "--refine",
        action="store_true",
        help="Suggest improvements to the description",
    )
    args = parser.parse_args()

    if args.refine:
        improvements, usage = suggest_improvements(args.text)
        print(improvements)
    else:
        model_code, usage = make_model(args.text)
        formatted_code = format_python(model_code)
        cost = usage_cost(usage)
        print(formatted_code, cost, sep="\n\n")
