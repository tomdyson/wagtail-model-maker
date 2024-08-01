from openai import OpenAI

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


client = OpenAI()


def ask_openai(description, system_prompt):
    resp = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": description},
        ],
    )
    answer = resp.choices[0].message.content
    usage = {"total_tokens": resp.usage.total_tokens}
    return answer, usage


print(
    ask_openai(
        "A blog page with a date field called 'Post date', an intro field, an image, and a rich text body field",
        SYSTEM_PROMPT,
    )
)
