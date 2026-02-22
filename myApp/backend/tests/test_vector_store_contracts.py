from datetime import datetime, timezone

from app.schemas.vector_store import (
    UserProfileEmbeddingRecord,
    UserProfileVectorMetadata,
    UserProfileVectorQuery,
)
from app.services.vector_store import user_profile_embedding_record_id


def test_user_profile_embedding_record_id_format():
    record_id = user_profile_embedding_record_id(
        "42efd9cb-e81b-4569-843b-1d2b71fdc6fe", "user_profile_embed_v1"
    )
    assert (
        record_id
        == "user_profile:42efd9cb-e81b-4569-843b-1d2b71fdc6fe:user_profile_embed_v1"
    )


def test_user_profile_embedding_record_contract():
    metadata = UserProfileVectorMetadata(
        discoverable=True,
        open_to_meetups=True,
        neighborhood="Midtown",
        geohash=None,
        budget_min=10,
        budget_max=50,
        hobbies=["coffee", "hiking"],
        diet_tags=["vegetarian"],
        vibe_tags=["casual"],
    )

    record = UserProfileEmbeddingRecord(
        id="user_profile:abc:user_profile_embed_v1",
        user_id="abc",
        vector=[0.1, 0.2, 0.3],
        embedding_version="user_profile_embed_v1",
        embedding_model="gemini-text-embedding-004",
        preference_profile_version="preference_profile_v1",
        source_content_hash="sha256:123",
        metadata=metadata,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert record.entity_type == "user_profile"
    assert record.metadata.open_to_meetups is True


def test_user_profile_vector_query_contract():
    query = UserProfileVectorQuery(
        query_vector=[0.1, 0.2, 0.3],
        top_k=20,
        embedding_version="user_profile_embed_v1",
        exclude_user_ids=["u1", "u2"],
    )

    assert query.top_k == 20
    assert query.filters.hobbies_any == []
    assert query.include_metadata is True

