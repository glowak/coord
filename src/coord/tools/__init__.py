import re

def clean_text(text: str) -> str:
    '''
    Returns a string containing cleaned text without tags <p> or <h>.
    '''
    text_sub = re.sub(r'<p>|<h>',"", text)
    return text_sub