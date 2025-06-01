from pathlib import Path
import setuptools

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setuptools.setup(
    name="st-audiorec",
    version="0.1.3",
    author="Stefan Rummer",
    author_email="",
    description="Record audio from the user's microphone in apps that are deployed to the web. (via Browser Media-API) [GitHub ☆ 160+: steamlit-audio-recorder]",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stefanrmmr/streamlit-audio-recorder",
    packages=["st_audiorec"],
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
    install_requires=[
        "streamlit>=0.63",
        "numpy>=1.19.0",
        "streamlit-chat>=0.1.1",
        "python-dotenv>=1.0.0",
        "openai>=1.0.0",
    ],
    package_data={
        "st_audiorec": ["frontend/build/*"],
    },
)