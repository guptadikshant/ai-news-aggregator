from typing import Literal, TypedDict


class InputAnalyser(TypedDict):
    user_input: str
    analyse_output: str
    platforms: Literal['youtube', 'social_media', 'blog_posts', 'news_articles']
