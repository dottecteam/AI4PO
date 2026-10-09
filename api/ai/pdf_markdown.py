
from markdown_it import MarkdownIt

_md = MarkdownIt("commonmark", {"html": False, "breaks": False}).enable(["table", "strikethrough"])


def md_para_html(texto: str) -> str:
    return _md.render(texto or "")