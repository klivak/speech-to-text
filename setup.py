from setuptools import find_packages, setup

setup(
    name="voicetype",
    version="1.0.0",
    description="Voice-to-text input for Windows powered by OpenAI Whisper",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "openai-whisper>=20231117",
        "openai>=1.0.0",
        "sounddevice>=0.4.6",
        "numpy>=1.24.0",
        "keyboard>=0.13.5",
        "pyperclip>=1.8.2",
        "pyautogui>=0.9.54",
        "PyQt6>=6.5.0",
        "Pillow>=10.0.0",
        "python-dotenv>=1.0.0",
        "keyring>=24.0.0",
    ],
    entry_points={
        "console_scripts": [
            "voicetype=src.main:main",
        ],
    },
)
