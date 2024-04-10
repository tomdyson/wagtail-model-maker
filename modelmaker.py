import argparse
import os
import re
import subprocess

import llm

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

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

REFINE_PROMPT = """
You are a tool which helps Wagtail developers write their page models. 
They describe the structure of their pages in a declarative way, and 
another tool will generate the code for them. Respond to their description 
by suggesting ways they can improve the text description to help the code 
generator produce better results.
"""

EXAMPLE_PROMPT = """
An event page with a title, a rich text body field called 'description' (optional), a hero image 
called 'lead image' (required), and a date field called 'launch date'.
"""


def extract_code(response):
    # Regular expression pattern to match markdown code blocks with language name
    pattern = r"```(?:python)?(.*?)```"

    # Search for the markdown code block in the response
    match = re.search(pattern, response, re.DOTALL)

    if match:
        # If a markdown code block is found, return its contents without the language name
        return match.group(1).strip()
    else:
        # If no markdown code block is found, return the whole response
        return response.strip()


def make_model(description):
    model = llm.get_model(
        "claude-3-opus"
    )  # claude-3-sonnet or claude-3-haiku or claude-3-opus
    model.key = CLAUDE_API_KEY
    response = model.prompt(description, system=SYSTEM_PROMPT, temperature=0)
    return extract_code(response.text())


def format_python(code):
    try:
        return subprocess.check_output(
            ["ruff", "format", "--line-length", "76", "-"], input=code, encoding="utf-8"
        )
    except subprocess.CalledProcessError:
        return code


def suggest_improvements(description):
    model = llm.get_model("claude-3-opus")
    model.key = CLAUDE_API_KEY
    response = model.prompt(description, system=REFINE_PROMPT, temperature=0)
    return response.text()


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
        improvements = suggest_improvements(args.text)
        print(improvements)
    else:
        model_code = make_model(args.text)
        formatted_code = format_python(model_code)
        print(formatted_code)
