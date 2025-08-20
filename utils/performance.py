"""
Performance utilities for the Notion backup system.
"""

import asyncio
import time
from typing import Callable, Any, List, TypeVar
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, TaskID

T = TypeVar('T')


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, max_calls: int = 3, period: float = 1.0):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum calls per period
            period: Time period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    def wait_if_needed(self) -> None:
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove old calls outside the period
        self.calls = [call_time for call_time in self.calls if now - call_time < self.period]
        
        # If we're at the limit, wait
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.calls = self.calls[1:]  # Remove the oldest call
        
        self.calls.append(now)


def batch_process(items: List[T], func: Callable[[T], Any], batch_size: int = 5, max_workers: int = 3) -> List[Any]:
    """
    Process items in parallel batches.
    
    Args:
        items: Items to process
        func: Function to apply to each item
        batch_size: Size of each batch
        max_workers: Maximum number of worker threads
        
    Returns:
        List of results
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            futures = [executor.submit(func, item) for item in batch]
            
            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"Error processing item: {e}")
                    results.append(None)
    
    return results


def with_progress(items: List[T], description: str = "Processing") -> Progress:
    """
    Create a progress bar for iterating over items.
    
    Args:
        items: Items to process
        description: Description for the progress bar
        
    Returns:
        Progress context manager
    """
    progress = Progress()
    task = progress.add_task(description, total=len(items))
    return progress, task


class MemoryOptimizedProcessor:
    """Process large datasets without loading everything into memory."""
    
    def __init__(self, chunk_size: int = 100):
        self.chunk_size = chunk_size
    
    def process_chunks(self, items: List[T], processor: Callable[[List[T]], Any]) -> None:
        """
        Process items in chunks to manage memory usage.
        
        Args:
            items: Items to process
            processor: Function to process each chunk
        """
        for i in range(0, len(items), self.chunk_size):
            chunk = items[i:i + self.chunk_size]
            processor(chunk)
            
            # Optional: force garbage collection after each chunk
            # import gc
            # gc.collect()
