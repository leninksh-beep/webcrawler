import asyncio
from typing import TypedDict
from urllib.parse import urljoin, urlparse, urlsplit
import aiohttp
from bs4 import BeautifulSoup, Tag


class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]


def normalize_url(url: str) -> str:
    parsed = urlsplit(url)
    full_path = f"{parsed.netloc}{parsed.path}"
    if full_path.endswith("/"):
        full_path = full_path[:-1]
    return full_path


def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    h_tag = soup.find("h1") or soup.find("h2")
    if isinstance(h_tag, Tag):
        return h_tag.get_text(strip=True)
    return ""


def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    main_tag = soup.find("main")
    p_tag = None

    if isinstance(main_tag, Tag):
        p_tag = main_tag.find("p")

    if not p_tag:
        p_tag = soup.find("p")

    if isinstance(p_tag, Tag):
        return p_tag.get_text(strip=True)
    return ""


def get_urls_from_html(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for a_tag in soup.find_all("a"):
        href = a_tag.get("href")
        if href:
            absolute_url = urljoin(base_url, href)
            urls.append(absolute_url)
    return urls


def get_images_from_html(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    images = []
    for img_tag in soup.find_all("img"):
        src = img_tag.get("src")
        if src:
            absolute_url = urljoin(base_url, src)
            images.append(absolute_url)
    return images


def extract_page_data(html: str, page_url: str) -> PageData:
    return {
        "url": page_url,
        "heading": get_heading_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, page_url),
        "image_urls": get_images_from_html(html, page_url),
    }


class AsyncCrawler:
    def __init__(
        self,
        base_url: str,
        max_concurrency: int = 3,
        max_pages: int = 100,
    ):
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.page_data: dict[str, PageData] = {}
        self.visited: set[str] = set()
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.max_pages = max_pages
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.session: aiohttp.ClientSession | None = None
        self.should_stop = False
        self.all_tasks: set[asyncio.Task] = set()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def add_page_visit(self, normalized_url: str) -> bool:
        async with self.lock:
            if self.should_stop:
                return False

            if len(self.visited) >= self.max_pages:
                self.should_stop = True
                print("Reached maximum number of pages to crawl.")
                return False

            if normalized_url in self.visited:
                return False

            self.visited.add(normalized_url)
            return True

    async def get_html(self, url: str) -> str:
        headers = {"User-Agent": "BootCrawler/1.0"}
        async with self.session.get(url, headers=headers) as response:
            if response.status >= 400:
                raise Exception(
                    f"HTTP error {response.status}: {response.reason}"
                )

            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                raise Exception(
                    f"Invalid content type: {content_type}. Expected text/html."
                )

            return await response.text()

    async def crawl_page(self, current_url: str):
        if self.should_stop:
            return

        current_domain = urlparse(current_url).netloc
        if self.base_domain != current_domain:
            return

        normalized_current = normalize_url(current_url)
        is_first_visit = await self.add_page_visit(normalized_current)
        if not is_first_visit:
            return

        print(f"crawling: {current_url}")
        try:
            async with self.semaphore:
                html = await self.get_html(current_url)
        except Exception as e:
            print(f"Error crawling {current_url}: {e}")
            return

        data = extract_page_data(html, current_url)
        async with self.lock:
            self.page_data[normalized_current] = data

        for link in data["outgoing_links"]:
            if self.should_stop:
                break
            task = asyncio.create_task(self.crawl_page(link))
            self.all_tasks.add(task)
            try:
                await task
            finally:
                self.all_tasks.discard(task)

    async def crawl(self) -> dict[str, PageData]:
        await self.crawl_page(self.base_url)
        return self.page_data


async def crawl_site_async(
    base_url: str,
    max_concurrency: int = 3,
    max_pages: int = 100,
) -> dict[str, PageData]:
    async with AsyncCrawler(
        base_url, max_concurrency, max_pages
    ) as crawler:
        return await crawler.crawl()
