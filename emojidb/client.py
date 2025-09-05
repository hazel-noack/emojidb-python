import unicodedata
from typing import Any, List, Optional
from urllib.parse import quote, urlencode
import time

from aiohttp import ClientSession
from easy_requests import Connection
from bs4 import BeautifulSoup

from .cache import EmojiCache, EmojiCacheSqlite




def escape_query(query: str) -> str:
    query = query.replace("-", "--")
    query = query.replace(" ", "-")
    return quote(query, safe="")


class EmojiDBClient:
    """A client for the EmojiDB website."""

    # the kwargs have to be there for backwards compatibility
    def __init__(self, cache: Optional[EmojiCache] = None, **kwargs) -> None:
        self.async_client = None

        self.cache = EmojiCacheSqlite(expire_after_days=2) if cache is None else cache
        self.connection = Connection()
        self.connection.generate_headers()

    # the synchronous context manager doesn't do anything, 
    # however it exists so that you can use this synchronous similar to how you'd use async 
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass

    async def __aenter__(self):
        self.async_client = AsyncEmojiDBClient(cache=self.cache)
        return self.async_client

    async def __aexit__(self, *args: Any):
        assert self.async_client is not None, "EmojiDBClient.__aexit__ has to be called from a context manager"
        await self.async_client.close()

    def _search_no_cache(self, query: str):
        response = self.connection.get(f"https://emojidb.org/{query}-emojis")
        soup = BeautifulSoup(response.text, "html.parser")
        results =  [r.text for r in soup.find_all("div", class_="emoji")]

        self.cache.write_cache(query=query, emojis=results)
        return results

    def search(self, query: str) -> List[str]:
        query = escape_query(query)

        if self.cache.has_cache(query):
            return self.cache.get_cache(query)
        
        return self._search_no_cache(query=query)

    def _get_send_copy_url(self, emoji: str, query: str, is_negative: bool) -> str:
        base = "https://emojidb.org/api/copyEmoji?"

        query_params = {
            "emoji": emoji,
            "query": query,
            "time": int(time.time() * 1000),
            "key": "",
            "anti": is_negative,
        }

        encoded_params = urlencode(query_params)
        return base + encoded_params

    def like(self, emoji: str, query: str):
        url = self._get_send_copy_url(emoji=emoji, query=query, is_negative=False)
        self.connection.get(url)

    def dislike(self, emoji: str, query: str):
        url = self._get_send_copy_url(emoji=emoji, query=query, is_negative=True)
        self.connection.get(url)

    def _get_add_emoji_url(self, emoji: str, query: str) -> str:
        base = "https://emojidb.org/api/copyEmoji?"

        query_params = {
            "emoji": emoji,
            "query": query,
            "time": int(time.time() * 1000),
            "manuallySubmitted": 1,
            "referrer": "",
            "embedMode": "no",
            "key": "",
        }

        encoded_params = urlencode(query_params)
        return base + encoded_params
    
    def add_emoji(self, emoji: str, query: str):
        url = self._get_add_emoji_url(emoji=emoji, query=query)
        self.connection.get(url)

class AsyncEmojiDBClient(EmojiDBClient):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.session = ClientSession()

    async def close(self):
        await self.session.close()
    
    async def _search_no_cache(self, query: str) -> List[str]:
        async with self.session.get(
            f"https://emojidb.org/{query}-emojis"
        ) as response:
            soup = BeautifulSoup(await response.content.read(), "html.parser")
            results =  [r.text for r in soup.find_all("div", class_="emoji")]
            self.cache.write_cache(query=query, emojis=results)
            return results
        
    async def search(self, query: str) -> List[str]:
        query = escape_query(query)

        if self.cache.has_cache(query):
            return self.cache.get_cache(query)
        
        return await self._search_no_cache(query)
    
    async def search_for_emojis(self, query: str) -> list[tuple[str, str]]:
        """
        Only exists for backwards compatibility.
        Use search instead
        """
        return [(e, unicodedata.name(e, "").capitalize() if len(e) == 1 else "") for e in await self.search(query=query)]
    
    async def like(self, emoji: str, query: str):
        url = self._get_send_copy_url(emoji=emoji, query=query, is_negative=False)
        async with self.session.get(url) as response:
            pass

    async def dislike(self, emoji: str, query: str):
        url = self._get_send_copy_url(emoji=emoji, query=query, is_negative=True)
        async with self.session.get(url) as response:
            pass
    
    async def add_emoji(self, emoji: str, query: str):
        url = self._get_add_emoji_url(emoji=emoji, query=query)
        async with self.session.get(url) as response:
            pass