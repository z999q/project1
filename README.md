```md
# Web Crawler with SQLite Storage

This project is a multithreaded web crawler built in Python. It collects various types of data from websites, such as links, files, emails, API endpoints, and more. The collected data is stored in an SQLite database for further analysis.

## Features

- Crawls and extracts:
  - Links (internal and external)
  - Files (HTML, PDFs, images, archives, etc.)
  - Emails
  - Cookies
  - IP addresses
  - API endpoints
  - Phone numbers
  - Physical addresses
  - Social media URLs and handles
  - Google Analytics tracking IDs
- Uses multiple user agents to avoid detection.
- Detects and stores API endpoints.
- Supports concurrency with multi-threading.
- Stores all extracted data in an SQLite database.

## Installation

### Prerequisites

- Python 3.x
- Required dependencies:
  - `requests`
  - `beautifulsoup4`
  - `sqlite3`

### Install Dependencies

Run the following command:

```sh
pip install requests beautifulsoup4
```

## Usage

1. Run the crawler:

   ```sh
   python crawler.py
   ```

2. Enter the starting URL when prompted:

   ```
   Enter the website URL to start crawling (e.g., https://example.com):
   ```

3. The crawler will scan the website and store the data in `crawler_data.db`.

## Database Schema

The crawler stores data in an SQLite database (`crawler_data.db`) with the following tables:

| Table Name          | Description                                  |
|---------------------|----------------------------------------------|
| `directories`       | Stores discovered directories               |
| `files`            | Stores file URLs and their types            |
| `links`            | Stores all extracted links                  |
| `emails`           | Stores extracted email addresses            |
| `cookies`          | Stores site cookies                         |
| `ip_addresses`     | Stores resolved IP addresses of domains     |
| `api_endpoints`    | Stores detected API endpoints               |
| `phone_numbers`    | Stores extracted phone numbers              |
| `physical_addresses` | Stores extracted physical addresses      |
| `social_media_urls` | Stores extracted social media links       |
| `social_media_handles` | Stores extracted social media handles |
| `ga_tracking_ids`  | Stores detected Google Analytics IDs        |

## Example Output

```
Crawled: https://example.com (text/html)
Crawled: https://example.com/contact (text/html)
Found email: contact@example.com
Found phone number: +1-555-555-5555
Found social media handle: @example
Data saved to crawler_data.db
```

## Handling Interruptions

If you stop the crawler using `Ctrl+C`, it will automatically save the collected data before exiting.

## Notes

- The crawler has a built-in list of common hidden directories to scan (e.g., `/admin`, `/login`).
- It respects website structure but does **not** follow robots.txt rules.
- The database will grow over time, so consider using SQL queries to extract relevant data.

## License

This project is licensed under the MIT License.
```

Let me know if you need modifications!
