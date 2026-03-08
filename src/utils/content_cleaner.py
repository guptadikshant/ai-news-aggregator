import re

# ---------------------------------------------------------------------------
# Boilerplate line patterns (case-insensitive, matched per-line)
# ---------------------------------------------------------------------------
_BOILERPLATE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        # Generic site chrome / navigation
        r"^(skip to (main )?content|table of contents|navigation|menu|sidebar|footer|header|breadcrumb).*$",
        r"^(advertisement|sponsored|promoted).*$",
        r"^(read more|continue reading|see also|related (posts|articles))\.?$",
        # LinkedIn-specific noise (## prefix optional on all)
        r"^#{0,3}\s*linkedin respects your privacy.*$",
        r"^linkedin and 3rd parties use.*$",
        r"^select accept to consent.*$",
        r"^you can update your choices at any time.*$",
        r"^this title was summarized by ai.*$",
        r"^\*?\s*\+?\s*report this post.*$",
        r"^\*?\s*\+?\s*report this comment.*$",
        r"^to view or add a comment.*$",
        r"^like\s*(comment)?\s*$",
        r"^like\s*reply\s*(\d+\s*reactions?)?.*$",
        r"^comment\s*$",
        r"^repost\s*$",
        r"^agree\s*[&+]\s*join\s*(linkedin)?.*$",
        r"^[\d,]+\s*(comments?|likes?)?\s*$",  # "3", "7   1 Comment", "13   2 Comments"
        r"^[\d,]+\s+[\d,]+\s*(comments?|likes?).*$",  # "13   2 Comments"
        r"^view profile.*$",
        r"^connect\s*$",
        r"^follow\s*$",
        r"^view profile\s+(connect|follow)?\s*$",
        r"^[\d,]+\s*followers?\s*$",  # "742 followers" or "10,379 followers"
        r"^\*?\s*[\d,]+\s*(posts?|articles?)\s*$",
        r"^#{0,3}\s*more from this author.*$",
        r"^#{0,3}\s*more relevant posts.*$",
        r"^#{0,3}\s*explore (related topics|content categories).*$",
        r"^#{0,3}\s*sign in to view more content.*$",
        r"^create your free account.*$",
        r"^new to linkedin\?.*$",
        r"^by clicking continue to join.*$",
        r"^never miss a beat.*$",
        r"^don.t have the app\?.*$",
        r"^(get it in the|open the app).*$",
        r"^sign\s*in\s*(join now)?.*$",
        r"^join now\s*$",
        r"^\*\s*(top content|people|learning|jobs|games)\s*$",
        r"^\d+[mhdwy]o?\s*$",  # relative time like "4mo", "2h", "3d"
        r"^\w+\s+\w+\.com\s*$",  # bare domain references like "morganstanley.com"
        # Generic social/website CTAs
        r"^(share|tweet|subscribe|follow us|sign up|log ?in|register).*$",
        r"^(cookie|privacy|terms of (service|use)|disclaimer).*$",
        r"^(©|copyright|all rights reserved).*$",
        # Orphan "Source:" with nothing useful
        r"^source:\s*$",
        # Lines that are just markdown "======" underlines with nothing above
        r"^=+\s*$",
        # Reddit-specific noise
        r"^open (menu|navigation|settings menu).*$",
        r"^expand (user menu|navigation).*$",
        r"^(go to|back to top|jump to|image \d+).*$",
        r"^r/\w+\s*$",  # bare subreddit names
        r"^u/\w+\s*$",  # bare user names
        r"^posted by.*$",
        r"^\d+\s*(upvotes?|downvotes?|points?).*$",
        r"^(join|create post|community info).*$",
        r"^get (app|the reddit app).*$",
        r"^log\s*in.*to\s*reddit.*$",
        r"^log\s*in\s*$",
        r"^(expand|collapse)\s*(thread|comment).*$",
        r"^(top|best|new|controversial|old|q&a)\s*$",  # sort options
        r"^(crosspost|save|hide|report|award).*$",
        # Share menu items (LinkedIn, general)
        r"^\*?\s*(copy|linkedin|facebook|x|twitter|email)\s*$",
        # Bare list markers with no content
        r"^\*\s*$",
        # Reddit login/signup wall
        r"^new to reddit\?.*$",
        r"^create your account.*$",
        r"^continue with (email|phone|google|apple).*$",
        r"^by continuing.*you agree.*$",
        r"^anyone can (view|post|comment).*$",
        r"^public\s*$",
        r"^\d+\s+\d+\s*$",  # "0 0" vote/comment counts
        r"^top posts.*$",
        r"^reddit re.*top posts.*$",
        r"^reddit rules.*$",
        r"^resources\s*$",
        r"^\w+\s*•\s*\d+[ymdh]?\s*(ago)?\s*$",  # "r/sub•1y ago" or "username•3d"
        r"^.+\s+open\s*$",  # "patreon.com Open"
        r"^user agreement.*$",
        # Reddit footer links
        r"^about reddit\s*$",
        r"^advertise\s*$",
        r"^developer platform\s*$",
        r"^reddit pro.*$",
        r"^help\s*$",
        r"^blog\s*$",
        r"^careers\s*$",
        r"^press\s*$",
        r"^communities\s*$",
        r"^best of reddit\s*$",
        r"^accessibility\s*$",
        r"^reddit,?\s*inc\.?\s*©.*$",
        # Combined / run-together CTA text
        r"^join\s*now\s*sign\s*in.*$",
        r"^sign\s*in\s*join\s*now.*$",
        # Lines that are just a title + domain (link captions like "Some Title   site.com")
        r"^.+\s{2,}\S+\.(com|org|net|io|co|dev)\s*$",
    ]
]

# Patterns for bullet-list items that are sidebar/explore/category noise
_SIDEBAR_BULLET = re.compile(
    r"^\*\s*(future trends|generative ai|how generative|ai and |ai in |"
    r"ai-driven|addressing generative|career|productivity|finance|"
    r"soft skills|project management|education|technology|leadership|"
    r"ecommerce|user experience)",
    re.IGNORECASE,
)


def clean_scraped_content(text: str) -> str:
    """Strip noisy artifacts from scraped markdown/HTML content.

    Removes images, bare URLs, HTML tags, navigation boilerplate,
    social-media sidebar/CTA noise, and collapses excessive whitespace
    while preserving only the core post/article body text.
    """
    if not text:
        return ""

    # --- HTML cleanup ---
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(
        r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE
    )
    text = re.sub(r"<[^>]+>", "", text)

    # Remove HTML entities
    text = re.sub(r"&nbsp;?", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&#?\w+;", "", text)  # remaining HTML entities

    # --- Markdown artifacts ---
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)  # images
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)  # links → text
    text = re.sub(r"\[\]\([^)]*\)", "", text)  # empty links [](url)
    text = re.sub(r"^\[[^\]]+\]:\s*\S+.*$", "", text, flags=re.MULTILINE)  # ref links
    text = re.sub(r"(?:https?|ftp)://\S+", "", text)  # bare URLs
    text = re.sub(r"mailto:\S+", "", text)
    text = re.sub(r"^[\s]*[-*_]{3,}[\s]*$", "", text, flags=re.MULTILINE)  # hr rules

    # Remove LinkedIn page-title duplicate lines (title followed by ====)
    text = re.sub(r"^(.+)\n=+\n", "", text, flags=re.MULTILINE)

    # Remove Reddit/LinkedIn run-together header lines
    text = re.sub(
        r"^.*(?:Get the Reddit app|Log\s*In\s*Log\s*in to Reddit|Open navigation).*$",
        "",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    text = re.sub(
        r"^.*(?:Join\s*now\s*Sign\s*in|Sign\s*in\s*Join\s*now).*$",
        "",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    # Strip everything after known footer markers
    _footer_markers = [
        r"^#{0,3}\s*More from this author",
        r"^#{0,3}\s*More Relevant Posts",
        r"^#{0,3}\s*Explore related topics",
        r"^#{0,3}\s*Explore content categories",
        r"^#{0,3}\s*Sign in to view more content",
    ]
    for marker in _footer_markers:
        match = re.search(marker, text, re.IGNORECASE | re.MULTILINE)
        if match:
            text = text[: match.start()]

    # --- Per-line boilerplate removal ---
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue
        if any(pat.match(stripped) for pat in _BOILERPLATE_PATTERNS):
            continue
        if _SIDEBAR_BULLET.match(stripped):
            continue
        cleaned_lines.append(stripped)

    text = "\n".join(cleaned_lines)

    # Collapse multiple blank lines into a single one
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
