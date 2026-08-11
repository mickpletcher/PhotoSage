import tempfile
from pathlib import Path

import pytest

pytest.importorskip("hypothesis")

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from photosage.manifest.manifest_reader import load_manifest
from photosage.manifest.manifest_writer import create_manifest, write_manifest
from photosage.manifest.review import apply_review_decisions
from photosage.rename.sanitizer import sanitize_filename


@given(st.text(max_size=500))
def test_sanitized_filenames_never_escape_a_directory(value):
    filename = sanitize_filename(value or "photo.jpg")
    assert Path(filename).name == filename
    assert len(filename) <= 180
    assert not {"/", "\\", "\0"}.intersection(filename)


@settings(max_examples=20, stateful_step_count=8)
class ReviewManifestStateMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.temporary = tempfile.TemporaryDirectory(prefix="photosage-state-")
        self.root = Path(self.temporary.name)
        self.source = self.root / "photo.jpg"
        self.source.write_bytes(b"photo")
        manifest = create_manifest(
            self.root,
            True,
            None,
            70,
            [
                {
                    "original_path": str(self.source),
                    "new_path": str(self.root / "planned.jpg"),
                    "original_filename": self.source.name,
                    "new_filename": "planned.jpg",
                    "status": "needs-review",
                    "approval_status": "required",
                }
            ],
        )
        self.manifest_path = write_manifest(manifest, self.root)

    @rule()
    def approve(self):
        manifest = load_manifest(self.manifest_path)
        if manifest["files"][0]["status"] in {"planned", "needs-review"}:
            apply_review_decisions(self.manifest_path, [{"selector": "photo.jpg", "action": "approve"}])

    @rule(name=st.sampled_from(["first.jpg", "second.jpg", "third.jpg"]))
    def edit(self, name):
        apply_review_decisions(
            self.manifest_path,
            [{"selector": "photo.jpg", "action": "edit", "new_filename": name}],
        )

    @rule()
    def reject(self):
        apply_review_decisions(self.manifest_path, [{"selector": "photo.jpg", "action": "reject"}])

    @invariant()
    def checksum_and_state_remain_valid(self):
        manifest = load_manifest(self.manifest_path)
        item = manifest["files"][0]
        assert item["status"] in {"planned", "rejected", "needs-review"}
        assert item["approval_status"] in {"required", "approved", "rejected"}

    def teardown(self):
        self.temporary.cleanup()


TestReviewManifestStateMachine = ReviewManifestStateMachine.TestCase
