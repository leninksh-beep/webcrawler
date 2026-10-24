import unittest
from crawl import (
    get_first_paragraph_from_html,
    get_heading_from_html,
    get_images_from_html,
    get_urls_from_html,
    normalize_url,
    extract_page_data,
)


class TestCrawl(unittest.TestCase):
    def test_normalize_url_strip_protocol(self):
        input_url = "https://blog.boot.dev/path"
        actual = normalize_url(input_url)
        expected = "blog.boot.dev/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_strip_trailing_slash(self):
        input_url = "https://blog.boot.dev/path/"
        actual = normalize_url(input_url)
        expected = "blog.boot.dev/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_http(self):
        input_url = "http://blog.boot.dev/path"
        actual = normalize_url(input_url)
        expected = "blog.boot.dev/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_http_slash(self):
        input_url = "http://blog.boot.dev/path/"
        actual = normalize_url(input_url)
        expected = "blog.boot.dev/path"
        self.assertEqual(actual, expected)

    def test_get_heading_h1_priority(self):
        html = "<html><body><h1>Primary Heading</h1><h2>Secondary Heading</h2></body></html>"
        actual = get_heading_from_html(html)
        expected = "Primary Heading"
        self.assertEqual(actual, expected)

    def test_get_heading_h2_fallback(self):
        html = "<html><body><h2>Fallback Heading</h2></body></html>"
        actual = get_heading_from_html(html)
        expected = "Fallback Heading"
        self.assertEqual(actual, expected)

    def test_get_heading_none(self):
        html = "<html><body><p>No headings present</p></body></html>"
        actual = get_heading_from_html(html)
        expected = ""
        self.assertEqual(actual, expected)
    def test_get_first_paragraph_main_priority(self):
        html = """<html><body>
            <p>Outside paragraph.</p>
            <main>
                <p>Main paragraph.</p>
            </main>
        </body></html>"""
        actual = get_first_paragraph_from_html(html)
        expected = "Main paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_fallback_no_main(self):
        html = "<html><body><p>First outside paragraph.</p></body></html>"
        actual = get_first_paragraph_from_html(html)
        expected = "First outside paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_none(self):
        html = "<html><body><h1>Only Heading</h1></body></html>"
        actual = get_first_paragraph_from_html(html)
        expected = ""
        self.assertEqual(actual, expected)
        # --- URL Extraction Tests ---
    def test_get_urls_from_html_absolute(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="https://crawler-test.com"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_relative(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="/path/one">Link</a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/path/one"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_multiple(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="/path/one">Link 1</a><a href="https://other.com/path">Link 2</a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = [
            "https://crawler-test.com/path/one",
            "https://other.com/path",
        ]
        self.assertEqual(actual, expected)
        # --- Image Extraction Tests ---
    def test_get_images_from_html_relative(self):
        input_url = "https://crawler-test.com"
        input_body = (
            '<html><body><img src="/logo.png" alt="Logo"></body></html>'
        )
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/logo.png"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_absolute(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="https://images.com/pic.jpg" alt="Pic"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://images.com/pic.jpg"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_missing_src(self):
        input_url = "https://crawler-test.com"
        input_body = (
            '<html><body><img alt="No Src"><img src="/valid.png"></body></html>'
        )
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/valid.png"]
        self.assertEqual(actual, expected)


    # --- Page Data Extraction Tests ---
    def test_extract_page_data_basic(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h1>Test Title</h1>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://crawler-test.com/link1"],
            "image_urls": ["https://crawler-test.com/image1.jpg"],
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_fallbacks(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h2>Fallback Subtitle</h2>
            <main>
                <p>Main paragraph priority.</p>
            </main>
            <a href="https://external.com">External Link</a>
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Fallback Subtitle",
            "first_paragraph": "Main paragraph priority.",
            "outgoing_links": ["https://external.com"],
            "image_urls": [],
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_empty(self):
        input_url = "https://crawler-test.com"
        input_body = "<html><body></body></html>"
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "",
            "first_paragraph": "",
            "outgoing_links": [],
            "image_urls": [],
        }
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
