"""Domain models for transcript analysis."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TranscriptAnalysis:
    """Represents an analyzed transcript with summary and action items."""

    summary: str
    action_items: list[str]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))