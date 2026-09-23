"""API client for Artificial Analysis."""

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

import httpx


class APIError(Exception):
    """API request failed."""
    pass


class AuthError(APIError):
    """Authentication failed."""
    pass


class ArtificialAnalysisClient:
    """Client for Artificial Analysis Free Data API."""
    
    BASE_URL = "https://artificialanalysis.ai/api/v2"
    DEFAULT_CACHE_TTL = 6 * 3600  # 6 hours
    
    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[Path] = None):
        """Initialize client with API key and cache directory.
        
        Args:
            api_key: API key, or None to auto-discover
            cache_dir: Cache directory, defaults to ~/.cache/aanalysis
        """
        self.api_key = api_key or self._discover_api_key()
        self.cache_dir = cache_dir or Path.home() / ".cache" / "aanalysis"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _discover_api_key(self) -> Optional[str]:
        """Discover API key from environment or config files."""
        # 1. Environment variable
        if key := os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY"):
            return key.strip()
        
        # 2. ~/.config/artificial-analysis/api_key
        aa_config = Path.home() / ".config" / "artificial-analysis" / "api_key"
        if aa_config.exists():
            return aa_config.read_text().strip()
        
        # 3. ~/.config/aanalysis/api_key
        aanalysis_config = Path.home() / ".config" / "aanalysis" / "api_key"
        if aanalysis_config.exists():
            return aanalysis_config.read_text().strip()
        
        return None
    
    def _get_cache_path(self, endpoint: str, params: dict[str, Any]) -> Path:
        """Get cache file path for an endpoint."""
        # Create a stable cache key from endpoint + params
        # Strip leading slash from endpoint to avoid absolute path issues
        endpoint_key = endpoint.lstrip("/").replace("/", "_")
        param_str = json.dumps(params, sort_keys=True)
        cache_key = f"{endpoint_key}_{hash(param_str)}"
        return self.cache_dir / f"{cache_key}.json"
    
    def _read_cache(self, cache_path: Path, ttl: int) -> Optional[dict]:
        """Read from cache if fresh."""
        if not cache_path.exists():
            return None
        
        stat = cache_path.stat()
        age = time.time() - stat.st_mtime
        if age > ttl:
            return None
        
        return json.loads(cache_path.read_text())
    
    def _write_cache(self, cache_path: Path, data: dict):
        """Write to cache."""
        cache_path.write_text(json.dumps(data, indent=2))
    
    def _request(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        use_cache: bool = True,
        cache_ttl: int = DEFAULT_CACHE_TTL
    ) -> dict:
        """Make API request with caching.
        
        Args:
            endpoint: API endpoint (e.g. "/language/models/free")
            params: Query parameters
            use_cache: Whether to use cache
            cache_ttl: Cache TTL in seconds
            
        Returns:
            Response data
            
        Raises:
            AuthError: Authentication failed
            APIError: Request failed
        """
        if not self.api_key:
            raise AuthError("No API key configured")
        
        params = params or {}
        
        # Check cache
        cache_path = self._get_cache_path(endpoint, params)
        if use_cache:
            if cached := self._read_cache(cache_path, cache_ttl):
                return cached
        
        # Make request
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"x-api-key": self.api_key}
        
        try:
            response = httpx.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthError("Invalid API key")
            raise APIError(f"HTTP {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {e}")
        
        data = response.json()
        
        # Write cache
        if use_cache:
            self._write_cache(cache_path, data)
        
        return data
    
    def list_models(
        self,
        page: int = 1,
        refresh: bool = False
    ) -> dict:
        """List LLM models from free tier API.
        
        Args:
            page: Page number (1-indexed)
            refresh: Bust cache
            
        Returns:
            Response with meta and data keys
        """
        return self._request(
            "/language/models/free",
            params={"page": page},
            use_cache=not refresh
        )
    
    def fetch_all_models(self, refresh: bool = False) -> list[dict]:
        """Fetch all models across all pages.
        
        Args:
            refresh: Bust cache
            
        Returns:
            List of all models
        """
        models = []
        page = 1
        
        while True:
            response = self.list_models(page=page, refresh=refresh)
            
            # API returns data at top level
            page_models = response.get("data", [])
            
            if not page_models:
                break
            
            models.extend(page_models)
            
            # Check pagination (top-level or nested in meta)
            pagination = response.get("pagination") or (response.get("meta") or {}).get("pagination") or {}
            # Tolerate both has_more and has_next
            has_more = pagination.get("has_more", False) or pagination.get("has_next", False)
            if not has_more:
                break
            
            page += 1
        
        return models
