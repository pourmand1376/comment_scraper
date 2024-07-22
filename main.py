import requests
import json 
import os
from title import get_titles
WEBSITE_URL = "https://aprd.ir/"
try:
    TOKEN = os.environ["TOKEN"]
except KeyError:
    raise ValueError('Token not available')

def extract_comments(data):
    all_comments = []
    authors = set()  # Using a set to ensure unique authors
    discussions = data['data']['repository']['discussions']['nodes']
    
    for discussion in discussions:
        comment_count = discussion['comments']['totalCount']
        if comment_count > 0:
            for comment in discussion['comments']['nodes']:
                comment_info = {
                    'post_url': WEBSITE_URL+discussion['title'],
                    'discussion_url': discussion['url'],
                    'author': comment['author']['login'],
                    'comment_url': comment['url']
                }
                all_comments.append(comment_info)
                authors.add(comment['author']['login'])

    
    return all_comments, list(authors)

GRAPHQL_URL = 'https://api.github.com/graphql'
discussions_query = """
query {
repository(owner: "pourmand1376", name: "hugo-papermod-farsi-template") {
    discussions(first: 10) {
      # type: DiscussionConnection
      totalCount # Int!
      nodes {
        # type: Discussion
          url
          updatedAt
          title
          comments(last:2)
          {
            totalCount
            nodes {
              author {
                login
                url
              }
              url
            }
          }
      }
    }
  }
}"""

def generate_graphql_query(authors):
    query_parts = []
    for i, author in enumerate(authors):
        query_parts.append(f"""
    user{i}: user(login:"{author}") {{
        name
        url
        login
    }}""")
    
    full_query = "query get_user {" + "".join(query_parts) + "\n}"
    return full_query

if __name__ == "__main__":
    headers = {'Authorization': f'token {TOKEN}'}
    discussions = requests.post(url=GRAPHQL_URL, json={ 'query' :  discussions_query}, headers=headers)
    json_data = json.loads(discussions.text)

    # Extract comments
    result, authors = extract_comments(json_data)
    user_query = generate_graphql_query(authors=authors)

    authors_request = requests.post(url=GRAPHQL_URL, json={ 'query' :  user_query}, headers=headers)
    author_parsed=json.loads(authors_request.text)['data']

    author_info = {author['login']:{'name':author['name'], 'url':author['url']} for author in author_parsed.values()}

    urls = [comment['post_url'] for comment in result]
    url_titles = get_titles(urls=urls)

    html_content = """
<div class="latest-comments">
<h3 class="comments-title">آخرین دیدگاه‌ها</h3>
"""
    # Print the result
    for comment,(url, title) in zip(result, url_titles):
        author_login = comment['author']
        author_name_url = author_info[author_login]
        name = author_name_url['name'] if author_name_url['name'] and len(author_name_url['name']) > 0 else author_login
        print(f"Post_url: {comment['post_url']}")
        print(f"Post title: {title.split('|')[0]}")
        print(f"Discussion URL: {comment['discussion_url']}")
        print(f"Author URL: {author_name_url['url']}")
        print(f"Author Name: {name}")
        print(f"Comment URL: {comment['comment_url']}")
        print()
        html_content += f"""
<div class="comment-item">
<a href="{author_name_url['url']}">{name}</a>
 در 
<a href="{comment['post_url']}">{title.split('|')[0]}</a>
</div>"""

    html_content+= "</div>"
    from pathlib import Path
    Path('comments.html').write_text(html_content)