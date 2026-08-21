import argparse
import json
import re
from pathlib import Path
from typing import Any, Optional


class DocumentAgent:
    """Extract text, key/value fields, and basic statistics from documents."""

    supported_extensions = {".txt", ".md", ".markdown", ".pdf", ".docx"}
    skill_aliases = {
        "Python": ("python",),
        "SQL": ("sql",),
        "Machine Learning": ("machine learning", "scikit-learn", "sklearn"),
        "Deep Learning": ("deep learning", "pytorch", "tensorflow"),
        "NLP": ("nlp", "natural language processing"),
        "Computer Vision": ("computer vision", "opencv"),
        "Generative AI": ("generative ai", "genai", "generative artificial intelligence"),
        "LLMs": ("llm", "llms", "large language model", "large language models"),
        "Hugging Face": ("hugging face", "huggingface"),
        "RAG": ("rag", "retrieval-augmented generation", "retrieval augmented generation"),
        "AI Agents": ("ai agents", "ai agent", "agentic ai"),
        "REST APIs": ("rest api", "rest apis", "restful api"),
        "FastAPI": ("fastapi",),
        "Flask": ("flask",),
        "Django": ("django",),
        "NumPy": ("numpy",),
        "Pandas": ("pandas",),
        "Databases": ("mysql", "postgresql", "mongodb", "sqlite", "database"),
        "Vector Databases": ("vector database", "vector databases", "faiss", "chromadb", "pinecone"),
        "Docker": ("docker", "containerize", "containerized"),
        "Cloud": ("aws", "azure", "gcp", "cloud platforms", "cloud-based"),
        "Git": ("git", "github", "gitlab"),
        "Testing": ("automated testing", "api testing", "test cases", "testing"),
        "MLOps": ("mlops", "model lifecycle management", "monitoring"),
    }

    def extract(
        self, filename: str, content: bytes, job_description: Optional[str] = None
    ) -> dict[str, Any]:
        extension = Path(filename).suffix.lower()
        if extension not in self.supported_extensions:
            supported = ", ".join(sorted(self.supported_extensions))
            raise ValueError(f"Unsupported file type. Use: {supported}")

        text = self._extract_text(extension, content)
        result = {
            "filename": Path(filename).name,
            "text": text,
            "summary": self.summarize(text),
            "key_values": self.extract_key_values(text),
            "statistics": self.analyze(text),
        }
        if job_description and job_description.strip():
            result["job_match"] = self.match_job_description(text, job_description)
        return result

    @staticmethod
    def summarize(text: str, max_lines: int = 3) -> str:
        """Create a short grounded summary from the first meaningful lines."""
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return "No readable text was extracted from this document."
        summary = " ".join(lines[:max_lines])
        return summary if len(summary) <= 500 else summary[:497].rstrip() + "..."

    def match_job_description(self, document_text: str, job_description: str) -> dict[str, Any]:
        """Return an explainable skill-overlap score for a document and job description."""
        job_lower = job_description.lower()
        document_lower = document_text.lower()
        required_skills = [
            skill
            for skill, aliases in self.skill_aliases.items()
            if any(self._contains_term(job_lower, alias) for alias in aliases)
        ]
        matched_skills = [
            skill
            for skill in required_skills
            if any(self._contains_term(document_lower, alias) for alias in self.skill_aliases[skill])
        ]
        missing_skills = [skill for skill in required_skills if skill not in matched_skills]
        score = round((len(matched_skills) / len(required_skills)) * 100) if required_skills else 0
        evidence = {
            skill: self._evidence_line(document_text, self.skill_aliases[skill])
            for skill in matched_skills
        }
        return {
            "confidence_score": score,
            "match_level": self._match_level(score),
            "required_skill_count": len(required_skills),
            "matched_skill_count": len(matched_skills),
            "required_skills": required_skills,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "evidence": evidence,
        }

    @staticmethod
    def _contains_term(text: str, term: str) -> bool:
        return re.search(r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])", text) is not None

    @staticmethod
    def _evidence_line(text: str, aliases: tuple[str, ...]) -> str:
        for line in text.splitlines():
            if any(DocumentAgent._contains_term(line.lower(), alias) for alias in aliases):
                return line.strip()
        return ""

    @staticmethod
    def _match_level(score: int) -> str:
        if score >= 80:
            return "Strong match"
        if score >= 60:
            return "Good match"
        if score >= 40:
            return "Partial match"
        return "Low match"

    def extract_key_values(self, text: str) -> dict[str, str]:
        """Find labeled values such as ``Name: Ada`` or ``Total = 42``."""
        values: dict[str, str] = {}
        pattern = re.compile(r"^\s*([^:\n=]{2,80}?)\s*[:=]\s*(.+?)\s*$")
        for line in text.splitlines():
            match = pattern.match(line)
            if match:
                key, value = match.groups()
                values[key.strip()] = value.strip()
        return values

    def _extract_text(self, extension: str, content: bytes) -> str:
        if extension in {".txt", ".md", ".markdown"}:
            return content.decode("utf-8", errors="replace")
        if extension == ".pdf":
            return self._extract_pdf_text(content)
        return self._extract_docx_text(content)

    @staticmethod
    def _extract_pdf_text(content: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise ValueError("PDF extraction requires the optional 'pypdf' package") from error
        import io

        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(content)).pages)

    @staticmethod
    def _extract_docx_text(content: bytes) -> str:
        try:
            from docx import Document
        except ImportError as error:
            raise ValueError("DOCX extraction requires the optional 'python-docx' package") from error
        import io

        return "\n".join(paragraph.text for paragraph in Document(io.BytesIO(content)).paragraphs)

    def analyze(self, text: str) -> dict[str, int]:
        words = text.split()
        return {
            "characters": len(text),
            "words": len(words),
            "lines": len(text.splitlines()),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a text document.")
    parser.add_argument("document", type=Path, help="Path to a UTF-8 text file")
    args = parser.parse_args()

    result = DocumentAgent().extract(args.document.name, args.document.read_bytes())
    print(json.dumps(result, indent=2))