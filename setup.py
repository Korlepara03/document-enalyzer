from setuptools import find_packages, setup


setup(
    name="document-enalyzer",
    version="0.1.0",
    description="A small Python agent for analyzing documents.",
    packages=find_packages(),
    package_data={"document_agent": ["web/index.html"]},
    extras_require={
        "pdf": ["pypdf>=4.0"],
        "docx": ["python-docx>=1.1"],
    },
    entry_points={
        "console_scripts": [
            "document-agent=document_agent.agent:main",
            "document-server=document_agent.server:main",
        ],
    },
    python_requires=">=3.9",
)