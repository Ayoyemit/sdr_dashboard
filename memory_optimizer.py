import gc
import psutil
import os

def optimize_memory():
    """Optimize memory usage for the application"""
    
    # Force garbage collection
    gc.collect()
    
    # Set memory limit based on available memory
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    if memory_gb < 1:
        # Low memory environment
        os.environ['STREAMLIT_SERVER_MAX_UPLOAD_SIZE'] = '50'
        os.environ['STREAMLIT_SERVER_MAX_MESSAGE_SIZE'] = '50'
        return {
            'batch_size': 100,
            'cache_ttl': 900,  # 15 minutes
            'max_workers': 1
        }
    elif memory_gb < 2:
        # Medium memory environment
        os.environ['STREAMLIT_SERVER_MAX_UPLOAD_SIZE'] = '100'
        os.environ['STREAMLIT_SERVER_MAX_MESSAGE_SIZE'] = '100'
        return {
            'batch_size': 500,
            'cache_ttl': 1800,  # 30 minutes
            'max_workers': 2
        }
    else:
        # High memory environment
        os.environ['STREAMLIT_SERVER_MAX_UPLOAD_SIZE'] = '200'
        os.environ['STREAMLIT_SERVER_MAX_MESSAGE_SIZE'] = '200'
        return {
            'batch_size': 1000,
            'cache_ttl': 3600,  # 1 hour
            'max_workers': 4
        }

if __name__ == "__main__":
    optimize_memory()
