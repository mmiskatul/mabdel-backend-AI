from pathlib import Path
from uuid import uuid4


class LocalObjectStorage:
    def __init__(self, base_dir: str = "storage"):
        self.base = Path(base_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    async def put_pdf(self, content: bytes, prefix: str = "documents") -> str:
        target_dir = self.base / prefix
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / f"{uuid4().hex}.pdf"
        file_path.write_bytes(content)
        return str(file_path).replace("\\", "/")

