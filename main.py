import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import requests
import json

from title import get_titles

@dataclass
class Comment:
    post_url: str
    discussion_url: str
    author: str
    comment_url: str

@dataclass
class AuthorInfo:
    name: Optional[str]
    url: str

class ConfigurationError(Exception):
    """Raised when there's an issue with the configuration."""

class APIError(Exception):
    """Raised when there's an issue with the API request."""

class GitHubAPI:
    GRAPHQL_URL = 'https://api.github.com/graphql'

    def __init__(self, token: Optional[str] = None):
        self.token = token or self._get_token_from_env()
        self.headers = {'Authorization': f'token {self.token}'}

    @staticmethod
    def _get_token_from_env() -> str:
        try:
            return os.environ["TOKEN"]
        except KeyError:
            raise ConfigurationError('GitHub token not available in environment variables')

    def post_query(self, query: str) -> Dict:
        try:
            response = requests.post(self.GRAPHQL_URL, json={'query': query}, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise APIError(f"Failed to query GitHub API: {str(e)}")

class GitHubCommentsExtractor:
    def __init__(self, website_url: str, query_path: str):
        self.api = GitHubAPI()
        self.website_url = website_url
        self.query_path = query_path

    def _load_query(self, filename: str) -> str:
        try:
            return Path(filename).read_text()
        except FileNotFoundError:
            raise ConfigurationError(f"Query file not found: {filename}")

    def _generate_user_query(self, authors: List[str]) -> str:
        query_parts = [f"""
        user{i}: user(login:"{author}") {{
            name
            url
            login
        }}""" for i, author in enumerate(authors)]
        
        return "query get_user {" + "".join(query_parts) + "\n}"

    def fetch_discussions(self) -> Dict:
        discussions_query = self._load_query(self.query_path)
        return self.api.post_query(discussions_query)

    def extract_comments(self, data: Dict) -> Tuple[List[Comment], List[str]]:
        all_comments = []
        authors = set()
        
        for discussion in data['data']['repository']['discussions']['nodes']:
            if discussion['comments']['totalCount'] > 0:
                for comment in discussion['comments']['nodes']:
                    comment_info = Comment(
                        post_url=f"{self.website_url}{discussion['title']}",
                        discussion_url=discussion['url'],
                        author=comment['author']['login'],
                        comment_url=comment['url']
                    )
                    all_comments.append(comment_info)
                    authors.add(comment['author']['login'])
        
        return all_comments, list(authors)

    def fetch_author_info(self, authors: List[str]) -> Dict[str, AuthorInfo]:
        user_query = self._generate_user_query(authors)
        author_data = self.api.post_query(user_query)['data']
        return {
            author['login']: AuthorInfo(name=author['name'], url=author['url'])
            for author in author_data.values()
        }

    @staticmethod
    def generate_html_content(comments: List[Comment], url_titles: List[Tuple[str, str]], author_info: Dict[str, AuthorInfo]) -> str:
        html_content = """
    <div class="latest-comments">
    <div class="comments-title">آخرین دیدگاه‌ها</div>
    """
        for comment, (url, title) in zip(comments, url_titles):
            author_info_item = author_info[comment.author]
            name = author_info_item.name or comment.author
            post_title = title.split('|')[0]
            
            html_content += f"""
    <div class="comment-item">
    <a href="{author_info_item.url}">{name}</a>
     در 
    <a href="{comment.post_url}">{post_title}</a>
    </div>"""
        
        html_content += "</div>"
        return html_content

    def run(self) -> None:
        discussions_data = self.fetch_discussions()
        comments, authors = self.extract_comments(discussions_data)
        author_info = self.fetch_author_info(authors)
        
        urls = [comment.post_url for comment in comments]
        url_titles = get_titles(urls=urls)
        
        html_content = self.generate_html_content(comments, url_titles, author_info)
        Path('comments.html').write_text(html_content)
        
        self.print_results(comments, url_titles, author_info)

    @staticmethod
    def print_results(comments: List[Comment], url_titles: List[Tuple[str, str]], author_info: Dict[str, AuthorInfo]) -> None:
        for comment, (url, title) in zip(comments, url_titles):
            author_info_item = author_info[comment.author]
            name = author_info_item.name or comment.author
            post_title = title.split('|')[0]
            
            print(f"Post_url: {comment.post_url}")
            print(f"Post title: {post_title}")
            print(f"Discussion URL: {comment.discussion_url}")
            print(f"Author URL: {author_info_item.url}")
            print(f"Author Name: {name}")
            print(f"Comment URL: {comment.comment_url}")
            print()

if __name__ == "__main__":
    try:
        extractor = GitHubCommentsExtractor(
            website_url="https://aprd.ir/",
            query_path='discussion.query'
        )
        extractor.run()
    except (ConfigurationError, APIError) as e:
        print(f"Error: {str(e)}")