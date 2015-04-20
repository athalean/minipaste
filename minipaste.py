import os
import re
import random
from flask import Flask, render_template, request, url_for, redirect
from pygments import highlight
from pygments.lexers import get_lexer_by_name, get_all_lexers
from pygments.formatters import HtmlFormatter
from functools import wraps
from string import ascii_lowercase, digits

app = Flask(__name__)


POPULAR_LANGS = ['python', 'php', 'js']
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
PASTES_DIR = os.path.join(CURRENT_DIR, "pastes")


def random_string(n=8):
    return ''.join(random.choice(ascii_lowercase + digits) for _ in range(n))


def handle_file_not_found_as_404(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except FileNotFoundError:
            return "No such paste", 404
    return wrapped


@app.route('/<pasteid>')
@handle_file_not_found_as_404
def showpaste(pasteid):
    with open(os.path.join(PASTES_DIR, pasteid)) as f:
        content = f.read()
    metastring, remainder = re.match(r'<\?meta (.*?) \?>(.*)', content).groups()
    code = '\n'.join((remainder, '\n'.join(content.splitlines()[1:])))

    meta = dict(elem.split("=") for elem in metastring.split(','))
    lexer = get_lexer_by_name(meta.get('language', 'text'))
    highlighted_code = highlight(code, lexer, HtmlFormatter(cssclass="codehilite"))

    return render_template('paste.html', code=highlighted_code, **meta)

lexers = [lexer[1][0] for lexer in get_all_lexers()]
lexers.sort(key=lambda x: x in POPULAR_LANGS, reverse=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.form and request.form.get('code'):
        payload = dict(request.form.items())
        code = payload.pop('code')
        # fix windows lines issue
        code = '\n'.join(code.splitlines())
        metadata = ','.join("{key}={value}".format(key=key, value=value)
                            for key, value in payload.items() if value)
        pasteid = random_string()

        with open(os.path.join(PASTES_DIR, pasteid), 'w') as f:
            f.write("<?meta {metadata} ?>{code}".format(
                code=code,
                metadata=metadata)
            )
        return redirect(url_for('showpaste', pasteid=pasteid))
    return render_template('index.html', languages=lexers)

if __name__ == '__main__':
    app.run(debug=True)
