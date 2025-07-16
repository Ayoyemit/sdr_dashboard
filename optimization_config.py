"""
Optimization Configuration for SDR Dashboard
Centralized settings for performance optimization
"""

import streamlit as st
from functools import lru_cache
import hashlib
import pickle
import os

# Cache configuration
CACHE_TTL = 3600  # 1 hour cache TTL
CACHE_DIR = ".cache"
MAX_CACHE_SIZE = 100  # Maximum number of cached results

# Performance settings
USE_VECTORIZATION = True
USE_NUMBA = False  # Can be enabled if numba is available
BATCH_SIZE = 1000  # For processing large datasets
PARALLEL_PROCESSING = True

# Memory optimization
CHUNK_SIZE = 5000  # Process data in chunks
CLEANUP_INTERVAL = 100  # Cleanup cache every N operations

class OptimizationConfig:
    """Centralized optimization configuration"""
    
    def __init__(self):
        self.cache_enabled = True
        self.vectorization_enabled = True
        self.parallel_enabled = True
        self.memory_optimized = True
        self.debug_mode = False  # Debug mode for performance monitoring
        self.USE_NUMBA = False  # Added attribute for numba usage
        self.CHUNK_SIZE = 5000  # Process data in chunks for memory efficiency
        
    @staticmethod
    def get_cache_key(*args, **kwargs):
        """Generate a unique cache key for function arguments"""
        # Create a hash of the arguments
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @staticmethod
    def setup_cache_directory():
        """Ensure cache directory exists"""
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
    
    @staticmethod
    def clear_old_cache():
        """Clear old cache files"""
        if os.path.exists(CACHE_DIR):
            import time
            current_time = time.time()
            for filename in os.listdir(CACHE_DIR):
                filepath = os.path.join(CACHE_DIR, filename)
                if os.path.isfile(filepath):
                    if current_time - os.path.getmtime(filepath) > CACHE_TTL:
                        os.remove(filepath)

# Global optimization config
opt_config = OptimizationConfig()

def enable_debug_mode():
    """Enable debug mode for performance monitoring"""
    opt_config.debug_mode = True

def disable_debug_mode():
    """Disable debug mode"""
    opt_config.debug_mode = False

def cache_result(func):
    """Decorator for caching function results"""
    if not opt_config.cache_enabled:
        return func
    
    def wrapper(*args, **kwargs):
        cache_key = OptimizationConfig.get_cache_key(func.__name__, *args, **kwargs)
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.pkl")
        
        # Check if cached result exists and is fresh
        if os.path.exists(cache_file):
            import time
            if time.time() - os.path.getmtime(cache_file) < CACHE_TTL:
                try:
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
                except:
                    pass
        
        # Compute result and cache it
        result = func(*args, **kwargs)
        try:
            OptimizationConfig.setup_cache_directory()
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
        except:
            pass
        
        return result
    
    return wrapper

def streamlit_cache(func):
    """Streamlit-specific caching decorator"""
    if not opt_config.cache_enabled:
        return func
    
    @st.cache_data(ttl=CACHE_TTL, max_entries=MAX_CACHE_SIZE)
    def cached_func(*args, **kwargs):
        return func(*args, **kwargs)
    
    return cached_func 