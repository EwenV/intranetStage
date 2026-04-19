import nh3

# Configuration des balises et des attributs autorisés
ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "ul",
    "li",
    "a",
    "img",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "blockquote",
    "hr",
    "div",
    "span",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target"],
    "img": ["src", "alt", "title", "width", "height"],
    "*": ["style", "class"],
}


def sanitize_html(html_content: str) -> str:
    """
    Nettoie le contenu HTML en supprimant les balises et attributs non autorisés.

    Args:
        html_content (str): Le contenu HTML à nettoyer.

    Returns:
        str: Le contenu HTML nettoyé.
    """
    return nh3.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip_comments=True,
        link_rel="noopener noreferrer nofollow",
    )
