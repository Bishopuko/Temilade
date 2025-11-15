import re
from bs4 import BeautifulSoup

def render_template(content, variables):
    for key, value in variables.items():
        content = re.sub(r"{{\s*"+re.escape(key)+r"\s*}}", str(value), content)
    # Pretty-print HTML if it's HTML content
    try:
        soup = BeautifulSoup(content, 'html.parser')
        return soup.prettify()
    except Exception:
        # If not HTML, return as is
        return content
