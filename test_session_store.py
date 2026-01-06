from connectors.base.session_store_factory import get_session_store
from connectors.base.types import SessionBlob

store = get_session_store()

blob = SessionBlob(
    platform="JIOMART",
    user_key="local-dev",
    data={"token": "xyz"},
)

store.save(blob, ttl_seconds=60)

loaded = store.load("JIOMART", "local-dev")
print("Loaded session:", loaded)
