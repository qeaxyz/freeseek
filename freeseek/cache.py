from functools import lru_cache

class Cache:
    @lru_cache(maxsize=100)
    def get_cached_data(self, key: str) -> Any:
        # Simulate cache retrieval logic.
        return f"cached-data-{key}"