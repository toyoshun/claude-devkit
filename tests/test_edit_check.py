import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "edit_check.py"
LINT = (
    "import sys\n"
    "text = open(sys.argv[1], encoding='utf-8').read()\n"
    "if 'TODO' in text:\n"
    "    print(sys.argv[1] + ':1: error: TODO')\n"
)
CLEAN = "# 届け\n\n届けは転出届から始めます。\n"
DIRTY = "# 届け\n\nTODO 出典を足す。\n"
ARTICLE = "content/articles/A1/article.md"
CONFIG = {
    "edit_checks": [
        {"glob": "content/articles/*/article.md", "run": ["python3", "lint.py"]}
    ]
}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)
    write(root / "lint.py", LINT)
    write(root / ".claude" / "devkit.json", json.dumps(CONFIG))
    return root


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def hook(stdin: str, path_env: str | None = None) -> subprocess.CompletedProcess[str]:
    env = {"PATH": path_env} if path_env is not None else None
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env=env,
    )


def edited(path: Path) -> str:
    return json.dumps({"tool_input": {"file_path": str(path)}})


def assert_silent_pass(result: subprocess.CompletedProcess[str]) -> None:
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


def link_ruff(repo: Path) -> None:
    ruff = Path(sys.executable).parent / "ruff"
    if not ruff.exists():
        pytest.skip("ruff is not installed next to the test interpreter")
    (repo / ".venv" / "bin").mkdir(parents=True)
    (repo / ".venv" / "bin" / "ruff").symlink_to(ruff)


def test_devkit_json_check_exits_2_and_names_the_file(repo: Path) -> None:
    result = hook(edited(write(repo / ARTICLE, DIRTY)))
    assert result.returncode == 2
    assert f"{ARTICLE}:1: error:" in result.stderr


def test_clean_file_is_silent(repo: Path) -> None:
    assert_silent_pass(hook(edited(write(repo / ARTICLE, CLEAN))))


def test_repo_python_in_venv_is_preferred_for_python_commands(repo: Path) -> None:
    fake = repo / ".venv" / "bin" / "python"
    write(fake, "#!/bin/sh\necho used-venv-python $@\n")
    fake.chmod(0o755)
    result = hook(edited(write(repo / ARTICLE, CLEAN)))
    assert result.returncode == 2
    assert f"used-venv-python lint.py {ARTICLE}" in result.stderr


def test_repo_without_devkit_json_runs_only_builtin_checks(repo: Path) -> None:
    (repo / ".claude" / "devkit.json").unlink()
    assert_silent_pass(hook(edited(write(repo / ARTICLE, DIRTY))))


@pytest.mark.parametrize("config", ["not json", "[]", '{"edit_checks": 1}', "{}"])
def test_bad_devkit_json_is_ignored(repo: Path, config: str) -> None:
    write(repo / ".claude" / "devkit.json", config)
    assert_silent_pass(hook(edited(write(repo / ARTICLE, DIRTY))))


def test_missing_command_fails_open(repo: Path) -> None:
    config = {"edit_checks": [{"glob": "*.md", "run": ["no-such-command-xyz"]}]}
    write(repo / ".claude" / "devkit.json", json.dumps(config))
    assert_silent_pass(hook(edited(write(repo / "a.md", DIRTY))))


def test_path_outside_any_repo_is_ignored(tmp_path: Path) -> None:
    outside = write(tmp_path / "plain" / ARTICLE, DIRTY)
    assert_silent_pass(hook(edited(outside)))


def test_symlink_pointing_outside_repo_is_ignored(repo: Path) -> None:
    real = write(repo.parent / "elsewhere.md", DIRTY)
    link = repo / ARTICLE
    link.parent.mkdir(parents=True)
    link.symlink_to(real)
    assert_silent_pass(hook(edited(link)))


@pytest.mark.parametrize(
    "rel",
    ["notes.md", "content/articles/A1/brief.md", "content/articles/article.md"],
)
def test_non_matching_file_is_ignored(repo: Path, rel: str) -> None:
    assert_silent_pass(hook(edited(write(repo / rel, DIRTY))))


@pytest.mark.parametrize(
    "stdin",
    [
        "not json",
        "",
        "[]",
        "{}",
        '{"tool_input": {}}',
        '{"tool_input": {"file_path": 1}}',
    ],
)
def test_bad_input_is_ignored(stdin: str) -> None:
    assert_silent_pass(hook(stdin))


def test_missing_file_is_ignored(repo: Path) -> None:
    assert_silent_pass(hook(edited(repo / ARTICLE)))


def test_python_file_is_formatted_and_fixed_with_repo_ruff(repo: Path) -> None:
    link_ruff(repo)
    source = write(repo / "pkg" / "x.py", "import os\nx = {'a':1}\nprint(missing)\n")
    result = hook(edited(source))
    assert result.returncode == 2
    assert "pkg/x.py:2:" in result.stderr and "F821" in result.stderr
    assert source.read_text(encoding="utf-8") == 'x = {"a": 1}\nprint(missing)\n'
    assert_silent_pass(hook(edited(write(repo / "pkg" / "y.py", "x = 1\n"))))


def test_python_file_without_any_ruff_is_skipped(repo: Path) -> None:
    source = write(repo / "pkg" / "x.py", "import os\n")
    assert_silent_pass(hook(edited(source), path_env=str(repo / "empty-bin")))
    assert source.read_text(encoding="utf-8") == "import os\n"


def test_ruff_on_path_is_used_when_the_repo_has_none(repo: Path) -> None:
    ruff = Path(sys.executable).parent / "ruff"
    if not ruff.exists():
        pytest.skip("ruff is not installed next to the test interpreter")
    bin_dir = repo.parent / "bin"
    bin_dir.mkdir()
    shutil.copy(ruff, bin_dir / "ruff")
    source = write(repo / "pkg" / "x.py", "x = {'a':1}\n")
    assert_silent_pass(hook(edited(source), path_env=str(bin_dir)))
    assert source.read_text(encoding="utf-8") == 'x = {"a": 1}\n'


def test_files_under_venv_are_ignored(repo: Path) -> None:
    link_ruff(repo)
    source = write(repo / ".venv" / "lib" / "x.py", "import os\n")
    assert_silent_pass(hook(edited(source)))
