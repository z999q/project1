import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import random
import mimetypes
import concurrent.futures
import re
import sqlite3
import signal
import sys
import socket

class WebCrawler:
    def __init__(self):
        self.starting_url = input("Enter the website URL to start crawling (e.g., https://example.com): ").strip()
        if not self.starting_url.startswith(('http://', 'https://')):
            self.starting_url = 'https://' + self.starting_url
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
            "Googlebot/2.1 (+http://www.google.com/bot.html)"
        ]
        
        self.headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "*/*"
        }
        
        self.session = requests.Session()
        self.data_by_domain = {}
        self.visited = set()
        self.to_visit = [self.starting_url]
        base_netloc = urlparse(self.starting_url).netloc
        common_hidden = ['/admin', '/login', '/private', '/backup', '/.git']
        self.to_visit.extend([f"https://{base_netloc}{path}" for path in common_hidden])

        self.conn = sqlite3.connect("crawler_data.db")
        self.cursor = self.conn.cursor()
        self.setup_database()

        signal.signal(signal.SIGINT, self.signal_handler)

    def setup_database(self):
        # Existing tables
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS directories (domain TEXT, directory TEXT UNIQUE)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS files (domain TEXT, url TEXT UNIQUE, type TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS links (domain TEXT, url TEXT UNIQUE)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS emails (domain TEXT, email TEXT UNIQUE)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS cookies (domain TEXT, url TEXT, cookies TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS ip_addresses (domain TEXT UNIQUE, ip TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS api_endpoints (domain TEXT, url TEXT UNIQUE, response_type TEXT)''')
        
        # New tables for requested features
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS phone_numbers (domain TEXT, number TEXT UNIQUE)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS physical_addresses (domain TEXT, address TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS social_media_urls (domain TEXT, url TEXT UNIQUE)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS social_media_handles (domain TEXT, handle TEXT UNIQUE)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS ga_tracking_ids (domain TEXT, tracking_id TEXT UNIQUE)''')
        self.conn.commit()

    def signal_handler(self, sig, frame):
        print("\nCtrl+C detected. Saving data to database...")
        self.save_to_database()
        self.conn.close()
        sys.exit(0)

    def get_ip_address(self, domain):
        try:
            ip = socket.gethostbyname(domain)
            return ip
        except socket.gaierror as e:
            print(f"Could not resolve IP for {domain}: {e}")
            return None

    def add_file(self, domain, url, content_type):
        ext = (mimetypes.guess_extension(content_type) or urlparse(url).path.split('.')[-1]).lower()
        file_type = "other"
        if ext in ['.html', '.htm']:
            file_type = "html"
        elif ext == '.pdf':
            file_type = "pdf"
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            file_type = "images"
        elif ext in ['.zip', '.rar', '.jar']:
            file_type = "archives"
        
        if domain not in self.data_by_domain:
            self.data_by_domain[domain] = {
                "directories": set(),
                "files": {"html": set(), "pdf": set(), "images": set(), "archives": set(), "other": set()},
                "links": set(),
                "emails": set(),
                "cookies": {},
                "ip_addresses": set(),
                "api_endpoints": set(),
                "phone_numbers": set(),
                "physical_addresses": set(),
                "social_media_urls": set(),
                "social_media_handles": set(),
                "ga_tracking_ids": set()
            }
        self.data_by_domain[domain]["files"][file_type].add(url)

    def extract_links_from_text(self, content):
        url_pattern = r'https?://[^\s()<>]+|www\.[^\s()<>]+'
        return re.findall(url_pattern, content)

    def is_api_endpoint(self, url, content_type, response_text=None):
        api_patterns = [
            r'/api/', r'/v\d+/', r'/rest/', r'/graphql', r'\.json$', r'\.xml$',
            r'/endpoint', r'/service', r'/data'
        ]
        if any(re.search(pattern, url, re.IGNORECASE) for pattern in api_patterns):
            return True
        if content_type in ['application/json', 'application/xml', 'text/json', 'text/xml']:
            return True
        if response_text and (response_text.strip().startswith('{') or response_text.strip().startswith('<')):
            return True
        return False

    def extract_new_features(self, domain, response_text):
        # Phone numbers
        phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_numbers = set(re.findall(phone_pattern, response_text))
        self.data_by_domain[domain]["phone_numbers"].update(phone_numbers)

        # Physical addresses (basic pattern - can be refined)
        address_pattern = r'\d{1,5}\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd),\s+[\w\s]+,\s+[A-Z]{2}\s+\d{5}'
        addresses = set(re.findall(address_pattern, response_text))
        self.data_by_domain[domain]["physical_addresses"].update(addresses)

        # Social media profile URLs
        social_url_pattern = r'(https?://(?:www\.)?(?:facebook|twitter|instagram|linkedin)\.com/[^\s()<>]+)'
        social_urls = set(re.findall(social_url_pattern, response_text))
        self.data_by_domain[domain]["social_media_urls"].update(social_urls)

        # Social media handles
        handle_pattern = r'@[\w]{1,15}(?=\s|$)'  # Twitter/Instagram style handles
        handles = set(re.findall(handle_pattern, response_text))
        self.data_by_domain[domain]["social_media_handles"].update(handles)

        # Google Analytics tracking IDs
        ga_pattern = r'UA-\d{6,10}-\d{1,2}'
        ga_ids = set(re.findall(ga_pattern, response_text))
        self.data_by_domain[domain]["ga_tracking_ids"].update(ga_ids)

    def fetch_url(self, url):
        self.headers["User-Agent"] = random.choice(self.user_agents)
        try:
            response = self.session.get(url, headers=self.headers, timeout=1)
            response.raise_for_status()
            return url, response
        except requests.RequestException as e:
            print(f"Failed to crawl {url}: {e}")
            return url, None

    def process_response(self, url, response):
        content_type = response.headers.get('Content-Type', '').split(';')[0]
        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        # Initialize domain data structure if not exists
        if domain not in self.data_by_domain:
            self.data_by_domain[domain] = {
                "directories": set(),
                "files": {"html": set(), "pdf": set(), "images": set(), "archives": set(), "other": set()},
                "links": set(),
                "emails": set(),
                "cookies": {},
                "ip_addresses": set(),
                "api_endpoints": set(),
                "phone_numbers": set(),
                "physical_addresses": set(),
                "social_media_urls": set(),
                "social_media_handles": set(),
                "ga_tracking_ids": set()
            }

        # IP address resolution
        if not self.data_by_domain[domain]["ip_addresses"]:
            ip = self.get_ip_address(domain)
            if ip:
                self.data_by_domain[domain]["ip_addresses"].add(ip)

        # Directory extraction
        path = parsed_url.path.rstrip('/')
        if path and '/' in path:
            directory = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(path.split('/')[:-1])}/"
            self.data_by_domain[domain]["directories"].add(directory)

        self.add_file(domain, url, content_type)
        self.data_by_domain[domain]["links"].add(url)

        # API endpoints
        response_text = response.text if 'text' in content_type or 'application' in content_type else None
        if self.is_api_endpoint(url, content_type, response_text):
            response_type = content_type if content_type in ['application/json', 'application/xml'] else 'unknown'
            self.data_by_domain[domain]["api_endpoints"].add((url, response_type))

        # Process text-based content
        if 'text' in content_type or content_type in ['application/javascript', 'text/css']:
            # Existing extractions
            if 'text/html' in content_type:
                soup = BeautifulSoup(response.text, 'html.parser')
                emails = set(re.findall(r'[\w\.-]+@[\w\.-]+', response.text))
                self.data_by_domain[domain]["emails"].update(emails)
                cookies = response.cookies.get_dict()
                if cookies:
                    self.data_by_domain[domain]["cookies"][url] = cookies
                
                for tag in soup.find_all(['a', 'script', 'link', 'img'], src=True) + soup.find_all('a', href=True):
                    link = tag.get('href') or tag.get('src')
                    if link:
                        try:
                            absolute_url = urljoin(url, link)
                            if absolute_url not in self.visited and absolute_url not in self.to_visit:
                                self.to_visit.append(absolute_url)
                            self.data_by_domain[domain]["links"].add(absolute_url)
                        except ValueError as e:
                            print(f"Skipping invalid URL: {link} (Error: {e})")

            # New feature extractions
            self.extract_new_features(domain, response.text)

            # Text-based link extraction
            text_links = self.extract_links_from_text(response.text)
            for link in text_links:
                try:
                    absolute_url = urljoin(url, link)
                    if absolute_url not in self.visited and absolute_url not in self.to_visit:
                        self.to_visit.append(absolute_url)
                    self.data_by_domain[domain]["links"].add(absolute_url)
                except ValueError as e:
                    print(f"Skipping invalid URL: {link} (Error: {e})")

        print(f"Crawled: {url} ({content_type})")

    def crawl(self):
        pages_crawled = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            while self.to_visit:
                if not self.to_visit:
                    break
                batch = self.to_visit[:50]
                self.to_visit = self.to_visit[50:]
                
                results = executor.map(self.fetch_url, batch)
                for url, response in results:
                    if url in self.visited:
                        continue
                    self.visited.add(url)
                    pages_crawled += 1
                    if response:
                        self.process_response(url, response)

        print(f"Crawled {pages_crawled} pages/files in total.")
        print("Done")
        self.save_to_database()
        self.conn.close()

    def save_to_database(self):
        for domain, data in self.data_by_domain.items():
            for directory in data["directories"]:
                self.cursor.execute("INSERT OR IGNORE INTO directories (domain, directory) VALUES (?, ?)", (domain, directory))
            for file_type, urls in data["files"].items():
                for url in urls:
                    self.cursor.execute("INSERT OR IGNORE INTO files (domain, url, type) VALUES (?, ?, ?)", (domain, url, file_type))
            for url in data["links"]:
                self.cursor.execute("INSERT OR IGNORE INTO links (domain, url) VALUES (?, ?)", (domain, url))
            for email in data["emails"]:
                self.cursor.execute("INSERT OR IGNORE INTO emails (domain, email) VALUES (?, ?)", (domain, email))
            for url, cookies in data["cookies"].items():
                self.cursor.execute("INSERT OR IGNORE INTO cookies (domain, url, cookies) VALUES (?, ?, ?)", (domain, url, str(cookies)))
            for ip in data["ip_addresses"]:
                self.cursor.execute("INSERT OR IGNORE INTO ip_addresses (domain, ip) VALUES (?, ?)", (domain, ip))
            for url, response_type in data["api_endpoints"]:
                self.cursor.execute("INSERT OR IGNORE INTO api_endpoints (domain, url, response_type) VALUES (?, ?, ?)", (domain, url, response_type))
            
            # New features
            for number in data["phone_numbers"]:
                self.cursor.execute("INSERT OR IGNORE INTO phone_numbers (domain, number) VALUES (?, ?)", (domain, number))
            for address in data["physical_addresses"]:
                self.cursor.execute("INSERT OR IGNORE INTO physical_addresses (domain, address) VALUES (?, ?)", (domain, address))
            for url in data["social_media_urls"]:
                self.cursor.execute("INSERT OR IGNORE INTO social_media_urls (domain, url) VALUES (?, ?)", (domain, url))
            for handle in data["social_media_handles"]:
                self.cursor.execute("INSERT OR IGNORE INTO social_media_handles (domain, handle) VALUES (?, ?)", (domain, handle))
            for ga_id in data["ga_tracking_ids"]:
                self.cursor.execute("INSERT OR IGNORE INTO ga_tracking_ids (domain, tracking_id) VALUES (?, ?)", (domain, ga_id))
        
        self.conn.commit()
        print("Data saved to crawler_data.db")

if __name__ == "__main__":
    crawler = WebCrawler()
    crawler.crawl()
