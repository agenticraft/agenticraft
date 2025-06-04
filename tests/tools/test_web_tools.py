"""Tests for web tools."""

import pytest
from datetime import datetime
from urllib.parse import urlparse

from agenticraft.tools.web import (
    web_search,
    extract_text,
    get_page_metadata,
    check_url
)
from agenticraft.core.exceptions import ToolExecutionError


class TestWebSearchTool:
    """Test the web_search tool."""
    
    @pytest.mark.asyncio
    async def test_basic_search(self):
        """Test basic web search."""
        results = await web_search.arun(query="python programming")
        
        assert isinstance(results, list)
        assert len(results) == 5  # Default num_results
        
        # Check result structure
        for result in results:
            assert 'title' in result
            assert 'snippet' in result
            assert 'url' in result
            assert 'date' in result
            assert 'relevance_score' in result
            
            # Verify types
            assert isinstance(result['title'], str)
            assert isinstance(result['snippet'], str)
            assert isinstance(result['url'], str)
            assert result['url'].startswith('https://')
    
    @pytest.mark.asyncio
    async def test_search_with_custom_results(self):
        """Test search with custom number of results."""
        results = await web_search.arun(query="test query", num_results=3)
        assert len(results) == 3
        
        # Test max limit
        results = await web_search.arun(query="test query", num_results=20)
        assert len(results) == 10  # Should be capped at 10
    
    @pytest.mark.asyncio
    async def test_news_search(self):
        """Test news search type."""
        results = await web_search.arun(
            query="latest technology news",
            search_type="news"
        )
        
        assert len(results) > 0
        
        # Check news-specific fields
        for result in results:
            assert 'source' in result
            assert 'category' in result
            assert result['source'] == 'Example News'
            assert result['category'] == 'Technology'
    
    @pytest.mark.asyncio
    async def test_academic_search(self):
        """Test academic search type."""
        results = await web_search.arun(
            query="machine learning research",
            search_type="academic"
        )
        
        assert len(results) > 0
        
        # Check academic-specific fields
        for result in results:
            assert 'authors' in result
            assert 'citations' in result
            assert isinstance(result['authors'], list)
            assert isinstance(result['citations'], int)
    
    @pytest.mark.asyncio
    async def test_search_relevance_ordering(self):
        """Test that results are ordered by relevance."""
        results = await web_search.arun(query="test query")
        
        # Check relevance scores are decreasing
        scores = [r['relevance_score'] for r in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_tool_metadata(self):
        """Test web_search tool metadata."""
        assert web_search.name == "web_search"
        assert "search" in web_search.description.lower()
        
        # Check parameters
        param_names = {p.name for p in web_search.parameters}
        assert "query" in param_names
        assert "num_results" in param_names
        assert "search_type" in param_names


class TestExtractTextTool:
    """Test the extract_text tool."""
    
    @pytest.mark.asyncio
    async def test_extract_basic(self):
        """Test basic text extraction."""
        result = await extract_text.arun(url="https://example.com/article")
        
        assert isinstance(result, dict)
        assert result['url'] == "https://example.com/article"
        assert 'title' in result
        assert 'text' in result
        assert 'word_count' in result
        assert 'language' in result
        
        # Check content
        assert isinstance(result['text'], str)
        assert len(result['text']) > 0
        assert result['word_count'] > 0
    
    @pytest.mark.asyncio
    async def test_extract_with_links(self):
        """Test extraction with links included."""
        result = await extract_text.arun(
            url="https://example.com/article",
            include_links=True
        )
        
        assert 'links' in result
        assert isinstance(result['links'], list)
        assert len(result['links']) > 0
        
        # Check link structure
        for link in result['links']:
            assert 'text' in link
            assert 'url' in link
            assert isinstance(link['text'], str)
            assert isinstance(link['url'], str)
    
    @pytest.mark.asyncio
    async def test_extract_with_max_length(self):
        """Test extraction with max length limit."""
        result = await extract_text.arun(
            url="https://example.com/article",
            max_length=50
        )
        
        assert len(result['text']) <= 53  # 50 + "..."
        assert 'truncated' in result
        assert result['truncated'] is True
    
    @pytest.mark.asyncio
    async def test_extract_invalid_url(self):
        """Test extraction with invalid URL."""
        with pytest.raises(ToolExecutionError, match="Invalid URL"):
            await extract_text.arun(url="not-a-url")
        
        with pytest.raises(ToolExecutionError, match="Invalid URL"):
            await extract_text.arun(url="http://")
        
        with pytest.raises(ToolExecutionError, match="Invalid URL"):
            await extract_text.arun(url="")
    
    @pytest.mark.asyncio
    async def test_extract_url_components(self):
        """Test that URL components are properly handled."""
        urls = [
            "https://example.com",
            "https://example.com/path",
            "https://example.com/path?query=1",
            "https://example.com:8080/path",
            "http://subdomain.example.com"
        ]
        
        for url in urls:
            result = await extract_text.arun(url=url)
            assert result['url'] == url
            
            # Title should reference the domain
            parsed = urlparse(url)
            assert parsed.netloc in result['title']


class TestGetPageMetadataTool:
    """Test the get_page_metadata tool."""
    
    @pytest.mark.asyncio
    async def test_metadata_basic(self):
        """Test basic metadata extraction."""
        result = await get_page_metadata.arun(url="https://example.com")
        
        assert isinstance(result, dict)
        assert result['url'] == "https://example.com"
        
        # Check required fields
        required_fields = [
            'title', 'description', 'keywords', 'author',
            'image', 'type', 'locale', 'site_name'
        ]
        
        for field in required_fields:
            assert field in result
    
    @pytest.mark.asyncio
    async def test_metadata_url_parsing(self):
        """Test metadata with different URL formats."""
        test_urls = [
            ("https://example.com", "example.com"),
            ("https://blog.example.com", "blog.example.com"),
            ("https://example.co.uk", "example.co.uk"),
        ]
        
        for url, expected_domain in test_urls:
            result = await get_page_metadata.arun(url=url)
            assert expected_domain in result['title']
            assert result['site_name'] == expected_domain.replace('.', ' ').title()
    
    @pytest.mark.asyncio
    async def test_metadata_open_graph(self):
        """Test Open Graph metadata fields."""
        result = await get_page_metadata.arun(url="https://example.com/article")
        
        # Check OG fields
        assert result['type'] == 'website'
        assert result['locale'] == 'en_US'
        assert result['image'].startswith('https://')
        assert result['image'].endswith('.jpg')
    
    @pytest.mark.asyncio
    async def test_metadata_invalid_url(self):
        """Test metadata with invalid URL."""
        with pytest.raises(ToolExecutionError, match="Invalid URL"):
            await get_page_metadata.arun(url="invalid-url")


class TestCheckUrlTool:
    """Test the check_url tool."""
    
    @pytest.mark.asyncio
    async def test_check_valid_url(self):
        """Test checking a valid URL."""
        result = await check_url.arun(url="https://example.com")
        
        assert isinstance(result, dict)
        assert result['url'] == "https://example.com"
        assert result['accessible'] is True
        assert result['status_code'] == 200
        assert result['content_type'] == 'text/html; charset=utf-8'
        assert 'content_length' in result
        assert 'response_time_ms' in result
        assert 'ssl_valid' in result
        assert 'redirects' in result
    
    @pytest.mark.asyncio
    async def test_check_http_vs_https(self):
        """Test SSL validation for HTTP vs HTTPS."""
        # HTTPS should have valid SSL
        https_result = await check_url.arun(url="https://example.com")
        assert https_result['ssl_valid'] is True
        
        # HTTP should not
        http_result = await check_url.arun(url="http://example.com")
        assert http_result['ssl_valid'] is False
    
    @pytest.mark.asyncio
    async def test_check_response_time(self):
        """Test response time measurement."""
        result = await check_url.arun(url="https://example.com")
        
        assert isinstance(result['response_time_ms'], int)
        assert result['response_time_ms'] > 0
        assert result['response_time_ms'] < 10000  # Less than 10 seconds
    
    @pytest.mark.asyncio
    async def test_check_invalid_url(self):
        """Test checking invalid URL."""
        with pytest.raises(ToolExecutionError, match="Invalid URL"):
            await check_url.arun(url="not-a-url")
        
        with pytest.raises(ToolExecutionError, match="Invalid URL"):
            await check_url.arun(url="ftp://example.com")  # Wrong protocol
    
    @pytest.mark.asyncio
    async def test_check_url_components(self):
        """Test various URL components."""
        urls = [
            "https://example.com",
            "https://example.com/path",
            "https://example.com:8080",
            "https://api.example.com/v1"
        ]
        
        for url in urls:
            result = await check_url.arun(url=url)
            assert result['url'] == url
            assert result['accessible'] is True


class TestWebToolsMetadata:
    """Test metadata for all web tools."""
    
    def test_all_tools_have_proper_names(self):
        """Test that all tools have proper names."""
        tools = [web_search, extract_text, get_page_metadata, check_url]
        expected_names = ['web_search', 'extract_text', 'get_page_metadata', 'check_url']
        
        for tool, expected_name in zip(tools, expected_names):
            assert tool.name == expected_name
    
    def test_all_tools_have_descriptions(self):
        """Test that all tools have descriptions."""
        tools = [web_search, extract_text, get_page_metadata, check_url]
        
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 10
            assert isinstance(tool.description, str)
    
    def test_all_tools_have_parameters(self):
        """Test that all tools have proper parameters."""
        # Check web_search parameters
        search_params = {p.name for p in web_search.parameters}
        assert 'query' in search_params
        
        # Check extract_text parameters
        extract_params = {p.name for p in extract_text.parameters}
        assert 'url' in extract_params
        
        # Check get_page_metadata parameters
        metadata_params = {p.name for p in get_page_metadata.parameters}
        assert 'url' in metadata_params
        
        # Check check_url parameters
        check_params = {p.name for p in check_url.parameters}
        assert 'url' in check_params


class TestMockImplementationNotes:
    """Test to ensure mock implementation notes are clear."""
    
    def test_mock_implementation_warnings(self):
        """Ensure we note these are mock implementations."""
        # This test serves as documentation
        mock_tools = [web_search, extract_text, get_page_metadata, check_url]
        
        # All tools should work without external dependencies
        for tool in mock_tools:
            assert callable(tool)
        
        # Note for implementers
        assert True, """
        These web tools are mock implementations for demonstration.
        Real implementations would require:
        - HTTP client library (aiohttp)
        - HTML parsing library (BeautifulSoup4)
        - API keys for search services
        - Rate limiting and caching
        - robots.txt compliance
        """
