import argparse
import os
import re
import subprocess

import anthropic

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


def usage_cost(usage):
    input_token_cost = 15 / 1000000  # https://www.anthropic.com/api
    output_token_cost = 75 / 1000000
    cost = (usage["input_tokens"] * input_token_cost) + (
        usage["output_tokens"] * output_token_cost
    )
    return f"${cost:.3f}"


def ask_claude(description, system_prompt):
    # Claude API wrapper
    resp = anthropic.Anthropic().messages.create(
        model="claude-3-opus-20240229",
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


def make_model(description):
    code, usage = ask_claude(description, SYSTEM_PROMPT)
    code = extract_code(code)
    return code, usage


def suggest_improvements(description):
    improvements, usage = ask_claude(description, REFINE_PROMPT)
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
        improvements = suggest_improvements(args.text)
        print(improvements)
    else:
        model_code, usage = make_model(args.text)
        formatted_code = format_python(model_code)
        cost = usage_cost(usage)
        print(formatted_code, cost, sep="\n\n")
