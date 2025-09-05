import sqlite3
from pathlib import Path
from typing import List
from platformdirs import user_cache_dir
import json


class EmojiCache:
    def has_cache(self, query: str) -> bool:
        return NotImplemented
    
    def get_cache(self, query: str) -> List[str]:
        return NotImplemented
    
    def write_cache(self, query: str, emojis: List[str]):
        return NotImplemented
    
    def clean_cache(self):
        pass

    def clear_cache(self):
        pass


class EmojiCacheSqlite(EmojiCache):
    def __init__(self, expire_after_days: int = 30):
        self.expire_after_days = expire_after_days
        
        # Create cache directory and database file
        cache_dir = Path(user_cache_dir("emojidb-python", "yemreak"))
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.database_file = cache_dir / "emojis.db"
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.database_file) as conn:
            cursor = conn.cursor()
            
            # Create queries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT UNIQUE NOT NULL,
                    searched_last TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create emojis table with foreign key to queries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS emojis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_id INTEGER NOT NULL,
                    emoji TEXT NOT NULL,
                    FOREIGN KEY (query_id) REFERENCES queries (id) ON DELETE CASCADE,
                    UNIQUE(query_id, emoji)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_query_text ON queries(query_text)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_queries_searched_last ON queries(searched_last)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_emojis_query_id ON emojis(query_id)")
            
            conn.commit()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with foreign keys enabled"""
        conn = sqlite3.connect(self.database_file)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def has_cache(self, query: str) -> bool:
        """Check if a query exists in cache and is not expired"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if query exists and is not expired
                cursor.execute("""
                    SELECT 1 FROM queries 
                    WHERE query_text = ? 
                    AND searched_last >= datetime('now', ?)
                """, (query, f"-{self.expire_after_days} days"))
                
                return cursor.fetchone() is not None
                
        except sqlite3.Error:
            return False
    
    def get_cache(self, query: str) -> List[str]:
        """Get cached emojis for a query"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Update the searched_last timestamp
                cursor.execute("""
                    UPDATE queries 
                    SET searched_last = CURRENT_TIMESTAMP 
                    WHERE query_text = ?
                """, (query,))
                
                # Get the emojis for this query
                cursor.execute("""
                    SELECT e.emoji 
                    FROM emojis e
                    JOIN queries q ON e.query_id = q.id
                    WHERE q.query_text = ?
                    ORDER BY e.id
                """, (query,))
                
                results = cursor.fetchall()
                emojis = [row[0] for row in results]
                
                conn.commit()
                return emojis
                
        except sqlite3.Error:
            return []
    
    def write_cache(self, query: str, emojis: List[str]):
        """Write query and emojis to cache"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert or update the query
                cursor.execute("""
                    INSERT INTO queries (query_text, searched_last)
                    VALUES (?, CURRENT_TIMESTAMP)
                    ON CONFLICT(query_text) 
                    DO UPDATE SET searched_last = CURRENT_TIMESTAMP
                """, (query,))
                
                # Get the query ID
                cursor.execute("SELECT id FROM queries WHERE query_text = ?", (query,))
                query_id = cursor.fetchone()[0]
                
                # Insert emojis (ignore duplicates due to UNIQUE constraint)
                for emoji in emojis:
                    cursor.execute("""
                        INSERT OR IGNORE INTO emojis (query_id, emoji)
                        VALUES (?, ?)
                    """, (query_id, emoji))
                
                conn.commit()
                
        except sqlite3.Error as e:
            # Handle any database errors
            print(f"Error writing to cache: {e}")
    
    def clean_cache(self):
        """Remove expired cache entries"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete queries that are older than expire_after_days
                # This will cascade and delete associated emojis due to FOREIGN KEY
                cursor.execute("""
                    DELETE FROM queries 
                    WHERE searched_last < datetime('now', ?)
                """, (f"-{self.expire_after_days} days",))
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Error cleaning cache: {e}")
    
    def clear_cache(self):
        """Clear all cache data"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Clear both tables
                cursor.execute("DELETE FROM emojis")
                cursor.execute("DELETE FROM queries")
                
                # Reset autoincrement counters (optional)
                cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('queries', 'emojis')")
                
                conn.commit()
                
        except sqlite3.Error as e:
            print(f"Error clearing cache: {e}")
        

class DisableEmojiCache(EmojiCache):
    def __init__(self) -> None:
        pass

    def has_cache(self, query: str) -> bool:
        return False
    
    def get_cache(self, query: str) -> List[str]:
        return []

    def write_cache(self, query: str, emojis: List[str]):
        pass


class LegacyJsonCache(EmojiCache):
    def __init__(self) -> None:
        cache_dir = Path(user_cache_dir("emojidb-python", "yemreak"))
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = cache_dir / "emojis.json"
        
        if not self.cache_file.exists():
            self.cache_file.write_text("{}")

        with self.cache_file.open("r") as f:
            self.data = json.load(f)

    def has_cache(self, query: str) -> bool:
        return query in self.data
    
    def get_cache(self, query: str) -> List[str]:
        return self.data.get("query", [])

    def write_cache(self, query: str, emojis: List[str]):
        self.data[query] = emojis
        with self.cache_file.open("w") as f:
            json.dump(f, self.data)
