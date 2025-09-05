# 📦 EmojiDB

- Simple python wrapper for emojidb.com

## ⭐️ Usage

```bash
pip install emojidb-python
```

```python
from asyncio import run
from emojidb import EmojiDBClient

from urllib.parse import quote


async def _main_async():
    query = "love"
    
    async with EmojiDBClient() as client:
        emojis = await client.search(query)
        print(*emojis, sep=", ")

        client.like(emojis[0], query)

def main_async():
    run(_main_async())


def main():
    query = "love"

    with EmojiDBClient() as client:
        emojis = client.search(query)
        print(*emojis, sep=", ")

        client.like(emojis[0], query)


if __name__ == "__main__":
    main()
    main_async()
```

## ToDo

- [x] cache with actual sqlite database
- [x] implement synchronous option
- [x] built query properly
- [x] liking and disliking emojis

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
