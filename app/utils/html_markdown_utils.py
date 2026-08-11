import re

def is_html(text: str) -> bool:
    # Common HTML tags
    html_pattern = re.compile(
        r"<(html|head|body|div|span|p|br|img|a|h1|h2|h3|h4|h5|h6|ul|ol|li|table|tr|td|th|strong|em|b|i)[\s>]",
        re.IGNORECASE
    )
    return bool(html_pattern.search(text))

def is_markdown(text: str) -> bool:
    # Markdown indicators
    md_patterns = [
        r"(^|\s)#{1,6}\s",         # headings
        r"\*\*.*?\*\*",            # bold
        r"\*.*?\*",                # italic
        r"\[.*?\]\(.*?\)",         # links
        r"!\[.*?\]\(.*?\)",        # images
        r"(^|\n)-\s",              # lists
        r"(^|\n)\d+\.\s",          # numbered lists
        r"`[^`]+`",                # inline code
        r"```[\s\S]+?```",         # code blocks
    ]
    return any(re.search(p, text) for p in md_patterns)
