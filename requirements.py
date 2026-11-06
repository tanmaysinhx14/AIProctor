"""Python-accessible dependency list for the AIProctor project.

For your local RTX 3050 setup, ensure you install the CUDA 12.1 build of PyTorch. 
Use this command if installing directly via pip:
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
python -m pip install -r requirements.txt
"""

DEPENDENCIES = (
    # Deep Learning
    "torch",
    "torchvision",
    
    # Backend & Web
    "fastapi",
    "uvicorn[standard]",
    "websockets",
    
    # Computer Vision & ML
    "opencv-contrib-python<5",
    "ultralytics",
    "mediapipe==0.10.9",
    "numpy<2",
    "scipy",
    
    # System Utilities
    "psutil",
)