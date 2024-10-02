from flask import Flask, render_template, request, send_from_directory
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import os

app = Flask(__name__)

# Function to fetch HTML content of a URL
def fetch_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return None
    except requests.exceptions.RequestException:
        return None

# Function to extract all links from a webpage and the tags they were found in
def extract_links(url, html):
    links = set()
    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all(['a', 'link', 'script', 'img'], href=True):
        href = link['href']
        # Handle relative URLs
        full_url = urljoin(url, href)
        links.add((full_url, link.name))
    for link in soup.find_all(['script', 'img'], src=True):
        src = link['src']
        # Handle relative URLs
        full_url = urljoin(url, src)
        links.add((full_url, link.name))
    return links

# Function to crawl specific routes and write links to a CSV file
def crawl_and_store(base_url, paths, max_depth=1):
    visited = set()
    queue = [(base_url + path, 0) for path in paths]
    graph = {}

    while queue:
        url, depth = queue.pop(0)
        if url in visited or depth > max_depth:
            continue

        html = fetch_url(url)
        if not html:
            continue

        links = extract_links(url, html)
        visited.add(url)
        graph[url] = list(links)

        for link, tag in links:
            if link not in visited:
                queue.append((link, depth + 1))
    
    # Write to CSV file
    csv_filename = 'website_links.csv'
    csv_filepath = os.path.join('static', csv_filename)
    with open(csv_filepath, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Source URL', 'Target URL', 'Tag'])
        for source_url, links in graph.items():
            for target_url, tag in links:
                writer.writerow([source_url, target_url, tag])

    return graph, csv_filename

# Flask routes for static pages
@app.route('/')
def home():
    return "<h1>Welcome to the Flask Server</h1><p>Select a site to view:</p><ul><li><a href='/blog'>Blog</a></li><li><a href='/portfolio'>Portfolio</a></li><li><a href='/restaurant'>Restaurant</a></li><li><a href='/crawl'>Crawl All</a></li></ul>"

@app.route('/blog')
def blog():
    return render_template('blog.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/restaurant')
def restaurant():
    return render_template('restaurant.html')

@app.route('/crawl')
def crawl():
    base_url = request.url_root.rstrip('/')
    paths = ['/blog', '/portfolio', '/restaurant']

    # Call crawl_and_store to crawl the specific routes and store links
    website_map, csv_filename = crawl_and_store(base_url, paths)

    # Provide a link to download the CSV file
    return render_template('crawl.html', base_url=base_url, website_map=website_map, csv_filename=csv_filename)

@app.route('/static/<path:filename>')
def download_file(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Ensure the 'static' directory exists
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)
