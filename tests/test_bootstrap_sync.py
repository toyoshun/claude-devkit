import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(cwd), *args],
        env=ENV,
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


class Setup:
    def __init__(self, tmp_path: Path) -> None:
        self.home = tmp_path / "home"
        self.home.mkdir()
        self.remote = tmp_path / "remote.git"
        seed = tmp_path / "seed"
        shutil.copytree(ROOT / "scripts", seed / "scripts")
        shutil.copytree(ROOT / "rules", seed / "rules")
        subprocess.run(["git", "init", "-q", "-b", "main", str(seed)], check=True)
        git(seed, "add", "-A")
        git(seed, "commit", "-qm", "seed")
        subprocess.run(
            ["git", "clone", "-q", "--bare", str(seed), str(self.remote)], check=True
        )
        self.devkit = tmp_path / "devkit"
        subprocess.run(
            ["git", "clone", "-q", str(self.remote), str(self.devkit)], check=True
        )
        self.upstream = seed
        git(seed, "remote", "add", "origin", str(self.remote))

    def publish(self) -> str:
        (self.upstream / "rules" / "pstack-principles.md").write_text(
            "# updated\n", encoding="utf-8"
        )
        git(self.upstream, "commit", "-qam", "update")
        git(self.upstream, "push", "-q", "origin", "main")
        return git(self.upstream, "rev-parse", "HEAD")

    def bootstrap(self) -> None:
        env = {**ENV, "HOME": str(self.home)}
        script = self.devkit / "scripts" / "bootstrap.sh"
        subprocess.run(["bash", str(script)], env=env, check=True)

    def head(self) -> str:
        return git(self.devkit, "rev-parse", "HEAD")


@pytest.fixture
def setup(tmp_path: Path) -> Setup:
    return Setup(tmp_path)


def test_session_start_pulls_new_commits_and_installs_new_rules(setup: Setup) -> None:
    new = setup.publish()
    setup.bootstrap()
    assert setup.head() == new
    rule = setup.home / ".claude" / "rules" / "pstack-principles.md"
    assert rule.read_text(encoding="utf-8") == "# updated\n"


def test_second_start_within_interval_does_not_pull(setup: Setup) -> None:
    setup.bootstrap()
    old = setup.head()
    setup.publish()
    setup.bootstrap()
    assert setup.head() == old


def test_feature_branch_is_left_alone(setup: Setup) -> None:
    git(setup.devkit, "checkout", "-qb", "work")
    old = setup.head()
    setup.publish()
    setup.bootstrap()
    assert setup.head() == old


def test_uncommitted_changes_are_left_alone(setup: Setup) -> None:
    (setup.devkit / "rules" / "pstack-models.md").write_text("mine\n", encoding="utf-8")
    old = setup.head()
    setup.publish()
    setup.bootstrap()
    assert setup.head() == old


def test_unreachable_remote_does_not_fail_the_session(setup: Setup) -> None:
    shutil.rmtree(setup.remote)
    setup.bootstrap()
