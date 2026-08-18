"""ImageBatch Pro 安装脚本。"""
from setuptools import setup, find_packages

setup(
    name="imagebatch-pro",
    version="1.0.0",
    description="一键批量压缩、改尺寸、加水印、转格式。纯本地运行，隐私零泄露。",
    author="ImageBatch Pro",
    license="MIT",
    python_requires=">=3.9",
    packages=find_packages(exclude=["tests", "tests.*", "build", "dist"]),
    install_requires=[
        "Pillow>=10.2.0,<11.0.0",
    ],
    extras_require={
        "pro": [
            "PyQt5>=5.15.10",
            "pystray>=0.19.5",
            "watchdog>=4.0.0",
            "exifread>=3.0.0",
            "piexif>=1.1.3",
        ],
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.1.0",
            "black>=24.0.0",
            "flake8>=7.0.0",
            "pyinstaller>=6.0.0",
        ],
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "imagebatch-pro=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Graphics",
    ],
)
