"""
Deployment Optimization Script for SDR Dashboard
Optimizes the application for various hosting platforms
"""

import os
import sys
import subprocess
import platform
import psutil
import multiprocessing
from pathlib import Path
import json

class DeploymentOptimizer:
    """Optimizes deployment for different hosting platforms"""
    
    def __init__(self):
        self.platform = self._detect_platform()
        self.cpu_count = multiprocessing.cpu_count()
        self.memory_gb = psutil.virtual_memory().total / (1024**3)
        self.optimization_config = {}
        
    def _detect_platform(self):
        """Detect the hosting platform"""
        # Check for common hosting platform indicators
        if os.environ.get('HEROKU_APP_NAME'):
            return 'heroku'
        elif os.environ.get('STREAMLIT_SERVER_PORT'):
            return 'streamlit_cloud'
        elif os.environ.get('DETA_SPACE_APP'):
            return 'deta_space'
        elif os.environ.get('RAILWAY_PROJECT_ID'):
            return 'railway'
        elif os.environ.get('RENDER_SERVICE_ID'):
            return 'render'
        else:
            return 'local'
    
    def optimize_for_platform(self):
        """Apply platform-specific optimizations"""
        print(f"Detected platform: {self.platform}")
        print(f"CPU cores: {self.cpu_count}")
        print(f"Memory: {self.memory_gb:.1f} GB")
        
        if self.platform == 'heroku':
            self._optimize_heroku()
        elif self.platform == 'streamlit_cloud':
            self._optimize_streamlit_cloud()
        elif self.platform == 'deta_space':
            self._optimize_deta_space()
        elif self.platform == 'railway':
            self._optimize_railway()
        elif self.platform == 'render':
            self._optimize_render()
        else:
            self._optimize_local()
    
    def _optimize_heroku(self):
        """Optimize for Heroku deployment"""
        print("Applying Heroku optimizations...")
        
        # Create optimized Procfile
        procfile_content = """web: streamlit run SDR_Dash.py --server.port $PORT --server.address 0.0.0.0 --server.maxUploadSize 200 --server.maxMessageSize 200
"""
        
        with open('Procfile', 'w') as f:
            f.write(procfile_content)
        
        # Create runtime.txt for Python version
        runtime_content = "python-3.11.0"
        with open('runtime.txt', 'w') as f:
            f.write(runtime_content)
        
        # Create .streamlit/config.toml for performance
        config_dir = Path('.streamlit')
        config_dir.mkdir(exist_ok=True)
        
        config_content = """[server]
maxUploadSize = 200
maxMessageSize = 200
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
base = "light"

[client]
showErrorDetails = false
"""
        
        with open('.streamlit/config.toml', 'w') as f:
            f.write(config_content)
        
        self.optimization_config['heroku'] = {
            'max_workers': min(4, self.cpu_count),
            'memory_limit': min(512, int(self.memory_gb * 1024)),
            'cache_ttl': 1800,  # 30 minutes
            'batch_size': 1000
        }
    
    def _optimize_streamlit_cloud(self):
        """Optimize for Streamlit Cloud deployment"""
        print("Applying Streamlit Cloud optimizations...")
        
        # Create .streamlit/config.toml
        config_dir = Path('.streamlit')
        config_dir.mkdir(exist_ok=True)
        
        config_content = """[server]
maxUploadSize = 200
maxMessageSize = 200
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[theme]
base = "light"

[client]
showErrorDetails = false
"""
        
        with open('.streamlit/config.toml', 'w') as f:
            f.write(config_content)
        
        self.optimization_config['streamlit_cloud'] = {
            'max_workers': 2,  # Streamlit Cloud limitation
            'memory_limit': 512,
            'cache_ttl': 3600,  # 1 hour
            'batch_size': 500
        }
    
    def _optimize_deta_space(self):
        """Optimize for Deta Space deployment"""
        print("Applying Deta Space optimizations...")
        
        # Create Spacefile
        spacefile_content = """v: 0
micros:
  - name: sdr-dashboard
    src: .
    engine: python3.11
    primary: true
    public: true
    vars:
      - name: STREAMLIT_SERVER_PORT
        value: 8080
      - name: STREAMLIT_SERVER_ADDRESS
        value: 0.0.0.0
"""
        
        with open('Spacefile', 'w') as f:
            f.write(spacefile_content)
        
        self.optimization_config['deta_space'] = {
            'max_workers': 1,  # Deta Space limitation
            'memory_limit': 256,
            'cache_ttl': 1800,  # 30 minutes
            'batch_size': 250
        }
    
    def _optimize_railway(self):
        """Optimize for Railway deployment"""
        print("Applying Railway optimizations...")
        
        # Create railway.json
        railway_config = {
            "build": {
                "builder": "nixpacks"
            },
            "deploy": {
                "startCommand": "streamlit run SDR_Dash.py --server.port $PORT --server.address 0.0.0.0",
                "restartPolicyType": "ON_FAILURE",
                "restartPolicyMaxRetries": 3
            }
        }
        
        with open('railway.json', 'w') as f:
            json.dump(railway_config, f, indent=2)
        
        self.optimization_config['railway'] = {
            'max_workers': min(4, self.cpu_count),
            'memory_limit': min(1024, int(self.memory_gb * 1024)),
            'cache_ttl': 3600,  # 1 hour
            'batch_size': 1000
        }
    
    def _optimize_render(self):
        """Optimize for Render deployment"""
        print("Applying Render optimizations...")
        
        # Create render.yaml
        render_config = """services:
  - type: web
    name: sdr-dashboard
    env: python
    buildCommand: pip install -r requirements_optimized.txt
    startCommand: streamlit run SDR_Dash.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: STREAMLIT_SERVER_MAX_UPLOAD_SIZE
        value: 200
      - key: STREAMLIT_SERVER_MAX_MESSAGE_SIZE
        value: 200
"""
        
        with open('render.yaml', 'w') as f:
            f.write(render_config)
        
        self.optimization_config['render'] = {
            'max_workers': min(4, self.cpu_count),
            'memory_limit': min(512, int(self.memory_gb * 1024)),
            'cache_ttl': 3600,  # 1 hour
            'batch_size': 1000
        }
    
    def _optimize_local(self):
        """Optimize for local development"""
        print("Applying local development optimizations...")
        
        self.optimization_config['local'] = {
            'max_workers': self.cpu_count,
            'memory_limit': int(self.memory_gb * 1024),
            'cache_ttl': 7200,  # 2 hours
            'batch_size': 2000
        }
    
    def create_optimized_config(self):
        """Create optimized configuration file"""
        config = {
            'platform': self.platform,
            'system': {
                'cpu_count': self.cpu_count,
                'memory_gb': self.memory_gb,
                'platform': platform.system(),
                'python_version': sys.version
            },
            'optimization': self.optimization_config.get(self.platform, {}),
            'cache': {
                'enabled': True,
                'ttl': self.optimization_config.get(self.platform, {}).get('cache_ttl', 3600),
                'max_entries': 100
            },
            'performance': {
                'vectorization': True,
                'parallel_processing': True,
                'memory_optimization': True,
                'batch_processing': True
            }
        }
        
        with open('deployment_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Created deployment_config.json for {self.platform}")
        return config
    
    def optimize_dependencies(self):
        """Optimize Python dependencies for the platform"""
        print("Optimizing dependencies...")
        
        # Read current requirements
        if os.path.exists('requirements.txt'):
            with open('requirements.txt', 'r') as f:
                current_requirements = f.read()
        
        # Create optimized requirements based on platform
        if self.platform in ['heroku', 'railway', 'render']:
            # Use optimized requirements for cloud platforms
            if os.path.exists('requirements_optimized.txt'):
                optimized_requirements = 'requirements_optimized.txt'
            else:
                optimized_requirements = 'requirements.txt'
        else:
            # Use standard requirements for other platforms
            optimized_requirements = 'requirements.txt'
        
        print(f"Using requirements file: {optimized_requirements}")
        return optimized_requirements
    
    def create_startup_script(self):
        """Create platform-specific startup script"""
        if self.platform == 'heroku':
            # Heroku uses Procfile, no additional script needed
            pass
        elif self.platform in ['streamlit_cloud', 'deta_space']:
            # Create startup script for these platforms
            startup_script = """#!/bin/bash
export STREAMLIT_SERVER_PORT=${PORT:-8501}
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
export STREAMLIT_SERVER_MAX_MESSAGE_SIZE=200

# Set Python optimization flags
export PYTHONOPTIMIZE=2
export PYTHONUNBUFFERED=1

# Start the application
exec streamlit run SDR_Dash.py --server.port $STREAMLIT_SERVER_PORT --server.address $STREAMLIT_SERVER_ADDRESS
"""
            
            with open('start.sh', 'w') as f:
                f.write(startup_script)
            
            # Make executable
            os.chmod('start.sh', 0o755)
        
        print(f"Created startup configuration for {self.platform}")
    
    def optimize_memory_usage(self):
        """Apply memory optimization techniques"""
        print("Applying memory optimizations...")
        
        # Create memory optimization script
        memory_script = """import gc
import psutil
import os

def optimize_memory():
    \"\"\"Optimize memory usage for the application\"\"\"
    
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
"""
        
        with open('memory_optimizer.py', 'w') as f:
            f.write(memory_script)
        
        print("Created memory optimization script")

def main():
    """Main deployment optimization function"""
    print("SDR Dashboard Deployment Optimizer")
    print("=" * 40)
    
    optimizer = DeploymentOptimizer()
    
    # Apply platform-specific optimizations
    optimizer.optimize_for_platform()
    
    # Create optimized configuration
    config = optimizer.create_optimized_config()
    
    # Optimize dependencies
    requirements_file = optimizer.optimize_dependencies()
    
    # Create startup script
    optimizer.create_startup_script()
    
    # Apply memory optimizations
    optimizer.optimize_memory_usage()
    
    print("\nDeployment optimization completed!")
    print(f"Platform: {config['platform']}")
    print(f"CPU cores: {config['system']['cpu_count']}")
    print(f"Memory: {config['system']['memory_gb']:.1f} GB")
    print(f"Requirements file: {requirements_file}")
    
    # Print deployment instructions
    print("\nDeployment Instructions:")
    if config['platform'] == 'heroku':
        print("1. git add .")
        print("2. git commit -m 'Optimized for Heroku'")
        print("3. git push heroku main")
    elif config['platform'] == 'streamlit_cloud':
        print("1. Push to GitHub")
        print("2. Connect repository to Streamlit Cloud")
        print("3. Deploy automatically")
    elif config['platform'] == 'deta_space':
        print("1. deta space push")
    elif config['platform'] == 'railway':
        print("1. Connect GitHub repository to Railway")
        print("2. Deploy automatically")
    elif config['platform'] == 'render':
        print("1. Connect GitHub repository to Render")
        print("2. Deploy automatically")
    else:
        print("1. Run: streamlit run SDR_Dash.py")

if __name__ == "__main__":
    main() 