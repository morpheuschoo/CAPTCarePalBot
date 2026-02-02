import re

MDV2_SPECIAL_CHARS = r'_*[]()~`>#+-=|{}.!'

def escapeMarkdownV2(text: str) -> str:
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)
