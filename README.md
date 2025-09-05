# 📦 EmojiDB

Simple python wrapper for [emojidb.com](https://emojidb.org/).

## ⭐️ Usage

```bash
pip install emojidb-python
```

The library can be asynchronously and synchronously.

```python
from asyncio import run
from emojidb import EmojiDBClient


async def main():
    async with EmojiDBClient() as client:
        emojis = await client.search("love")
        print(*emojis, sep=", ")

        client.like(emojis[0], query)

run(main())
```

```python
from emojidb import EmojiDBClient

client = EmojiDBClient()
emojis = client.search("love")
print(*emojis, sep=", ")
```

You can also do more than just fetch emojis. All of those functions work both async and synchronously. Here are all functionalities.

```python
from emojidb import EmojiDBClient

client = EmojiDBClient()

# fetch emojis
emojis = client.search("love")
print(*emojis, sep=", ")
# if you want to fetch similar emojis,
# you can just use the search function an pass in the emoji
emojis = client.search("🥺")
print(*emojis, sep=", ")

# like an emoji
client.like("🥺", "pleading face")

# dislike an emoji
client.dislike("🥺", "pleading face")

# suggest a new emoji
client.add_emoji("🥺", "pleading face")
```

If you want to change the caching behavior you can easily do so by just passing a custom cache class in the client.

```python
from emojidb import EmojiDBClient, EmojiCache, DisableEmojiCache, EmojiCacheSqlite

# use sqlite as cache (DEFAULT with expires in 30 days)
client = EmojiDBClient(EmojiCacheSqlite(expire_after_days=1))

# disable the cache
client = EmojiDBClient(DisableEmojiCache())

# custom cache
class MemoryCache(EmojiCache):
    """
    This cache only caches everything in memory.
    When initializing a new client the cache wouldn't persist
    """
    def __init__(self):
        self.data = {}

    def has_cache(self, query: str) -> bool:
        return query in self.data
    
    def get_cache(self, query: str) -> List[str]:
        return self.data.get(query, [])
    
    def write_cache(self, query: str, emojis: List[str]):
        return self.data[query] = emojis
    
    def clear_cache(self):
        self.data = {}

client = EmojiDBClient(MemoryCache())
```

The functions `EmojiCache.clean_cache()` and `EmojiCache.clear_cache()` are never called by the client, but it is recommended to still implement them.

Programms that use this library can use these functions by doing this:

```python
from emojidb import EmojiDBClient

client = EmojiDBClient(DisableEmojiCache())
client.cache.clean_cache()
client.cache.clear_cache()
```

## Features

- use an asynchronous client or a synchronous one
- cache the results using sqlite
- search for emojis
- like and dislike emojis (please do not abuse that)

## 🪪 License

```
Copyright 2023 Yunus Emre Ak ~ YEmreAk.com

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
