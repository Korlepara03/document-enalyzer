# document-enalyzer

Upload documents, extract their text, summarize them, and compare them with a job description.

## Run the web app

```bash
python -m pip install -e .
python -m document_agent.server 
```
  
Do not run `pip install document-server`: `document-server` is a command provided by this local project, not a package on PyPI. After installation, `document-server` also works if Python's Scripts directory is on your `PATH`.

Open http://127.0.0.1:8000 and upload a `.txt`, `.md`, `.pdf`, or `.docx` file. You can also upload a job description to receive an explainable 0-100 confidence score with matched skills, missing skills, and evidence lines. PDF and DOCX support is optional:

```bash
python -m pip install -e ".[pdf,docx]"
```

The extractor recognizes lines formatted like `Invoice number: INV-42` or `Total = 125.00`. The JSON API is available at `POST /api/extract` using a multipart field named `document` and an optional `job_description` file field. Responses include `summary`, `key_values`, `statistics`, and, when a job description is supplied, `job_match`.
