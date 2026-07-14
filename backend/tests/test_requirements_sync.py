"""The root requirements.txt must stay in sync with the backend's.

Vercel installs the Python function's dependencies from the requirements.txt at
the *repository root*, and its parser rejects `-r` includes — so the list has to
be duplicated there. Duplication silently drifts, which would mean the deployed
API runs different package versions than the ones we test against. This test
makes that drift a failing test rather than a production surprise.
"""
from pathlib import Path

BACKEND_REQS = Path(__file__).resolve().parent.parent / "requirements.txt"
ROOT_REQS = BACKEND_REQS.parent.parent / "requirements.txt"


def _pinned_packages(path: Path) -> set[str]:
    """Return the requirement lines, ignoring comments and blank lines."""
    return {
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def test_root_requirements_match_backend() -> None:
    backend = _pinned_packages(BACKEND_REQS)
    root = _pinned_packages(ROOT_REQS)

    assert backend == root, (
        "requirements.txt at the repo root has drifted from backend/requirements.txt.\n"
        f"Only in backend: {sorted(backend - root)}\n"
        f"Only in root:    {sorted(root - backend)}\n"
        "Vercel installs the root file, so they must be identical."
    )
