from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


GroupMatchMode = Literal["in_person", "chat_only"]
GroupMatchGenerationStrategy = Literal["heuristic", "vector_hybrid"]


class GroupMatchGenerateRequest(BaseModel):
    mode: GroupMatchMode = "in_person"
    strategy: GroupMatchGenerationStrategy = "heuristic"
    max_groups: int = Field(default=5, ge=1, le=100)
    target_group_size: int = Field(default=4, ge=2, le=8)
    same_neighborhood_preferred: bool = True
    dry_run: bool = False


class GroupMatchGenerateScoreSummary(BaseModel):
    avg_pair_hobby_overlap: float
    same_neighborhood_pairs: int


class GroupMatchGeneratedGroupSummary(BaseModel):
    group_match_id: UUID | None = None
    mode: GroupMatchMode
    status: str
    member_ids: list[UUID]
    venue_name: str | None = None
    score_summary: GroupMatchGenerateScoreSummary


class GroupMatchGenerateResponse(BaseModel):
    strategy_used: GroupMatchGenerationStrategy
    dry_run: bool
    created_groups: int
    skipped_users: int
    skip_reasons: dict[str, int]
    groups: list[GroupMatchGeneratedGroupSummary]
