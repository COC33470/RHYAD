import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class CommandResult:
    returncode: int
    output: str


HELP_TEXT = """RHYAD CLI

Usage:
  rhyad status
  rhyad generate <document>
  rhyad import <document>
  rhyad validate
  rhyad list
  rhyad doctor
  rhyad help

Compatibility:
  python3 scripts/rhyad.py status
  python3 scripts/rhyad.py generate 002
  python3 scripts/rhyad.py import 003
  python3 scripts/rhyad.py validate
  python3 scripts/rhyad.py list
  python3 scripts/rhyad.py doctor
"""


def _strip_quotes(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_scalar(line):
    key, value = line.split(":", 1)
    return key.strip(), _strip_quotes(value.strip())


def load_project_summary(path):
    summary = {"project": {}, "document": {}}
    current_section = None

    if not path.exists():
        return summary

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        if not raw_line.startswith(" ") and raw_line.rstrip().endswith(":"):
            current_section = raw_line.strip()[:-1]
            summary.setdefault(current_section, {})
            continue

        if current_section and raw_line.startswith("  ") and ":" in raw_line:
            key, value = _parse_scalar(raw_line.strip())
            summary[current_section][key] = value

    return summary


def load_registry_documents(path):
    documents = []
    current = None

    if not path.exists():
        return documents

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or stripped == "documents:":
            continue

        if stripped.startswith("- "):
            if current:
                documents.append(current)
            current = {}
            remainder = stripped[2:]
            if ":" in remainder:
                key, value = _parse_scalar(remainder)
                current[key] = value
            continue

        if current is not None and ":" in stripped:
            key, value = _parse_scalar(stripped)
            current[key] = value

    if current:
        documents.append(current)

    return documents


def load_repository_titles(path):
    titles = {}
    current_doc_code = None

    if not path.exists():
        return titles

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        indent = len(raw_line) - len(raw_line.lstrip(" "))

        if indent == 8 and stripped.startswith("- code:"):
            _, value = _parse_scalar(stripped[2:])
            current_doc_code = value
            continue

        if indent == 10 and current_doc_code and stripped.startswith("title:"):
            _, value = _parse_scalar(stripped)
            titles[current_doc_code.upper()] = value
            current_doc_code = None

    return titles


def knowledge_file_count(root):
    knowledge_dir = root / "knowledge"
    if not knowledge_dir.exists():
        return 0
    return sum(1 for path in knowledge_dir.iterdir() if path.is_file())


def run_command(command, timeout=None):
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
        return CommandResult(result.returncode, result.stdout.strip())
    except subprocess.TimeoutExpired:
        return CommandResult(124, f"Command timed out: {' '.join(command)}")


def _git_output(args, runner=run_command):
    result = runner(["git", *args], timeout=10)
    return result.output if result.returncode == 0 else "Unavailable"


def _test_status(runner=run_command):
    result = runner(["python3", "-m", "unittest", "discover"], timeout=60)
    return "OK" if result.returncode == 0 else "FAILED"


def _print_process_result(result, stream):
    if result.output:
        print(result.output, file=stream)
    return result.returncode


def command_status(root=ROOT, runner=run_command, stream=sys.stdout):
    project_config = load_project_summary(root / "config" / "project.yaml")
    registry = load_registry_documents(root / "config" / "document_registry.yaml")
    project = project_config.get("project", {})

    git_status = _git_output(["status", "--short"], runner=runner)
    git_state = "clean" if not git_status else f"modified ({len(git_status.splitlines())} entries)"

    print("RHYAD status", file=stream)
    print(f"Client: {project.get('client', '')}", file=stream)
    print(f"Projet: {project.get('name', '')}", file=stream)
    print(f"Branche Git: {_git_output(['rev-parse', '--abbrev-ref', 'HEAD'], runner=runner)}", file=stream)
    print(f"Etat Git: {git_state}", file=stream)
    print(f"Documents dans le registre: {len(registry)}", file=stream)
    print(f"Fichiers Knowledge Core: {knowledge_file_count(root)}", file=stream)
    print(f"Dernier commit: {_git_output(['log', '-1', '--pretty=%h %s'], runner=runner)}", file=stream)
    print(f"Tests rapides: {_test_status(runner=runner)}", file=stream)
    return 0


def command_generate(document, runner=run_command, stream=sys.stdout):
    return _print_process_result(runner(["python3", "scripts/main.py", document]), stream)


def command_import(document, runner=run_command, stream=sys.stdout):
    return _print_process_result(runner(["python3", "scripts/import_validated.py", document]), stream)


def command_validate(runner=run_command, stream=sys.stdout):
    return _print_process_result(runner(["python3", "-m", "unittest", "discover"]), stream)


def command_list(root=ROOT, stream=sys.stdout):
    registry = load_registry_documents(root / "config" / "document_registry.yaml")
    titles = load_repository_titles(root / "config" / "rhyad_repository.yaml")

    print("Documents RHYAD", file=stream)
    for document in registry:
        code = document.get("code", "")
        official_code = document.get("official_code", "")
        family = document.get("family", "")
        title = titles.get(code.upper(), "")
        print(f"{official_code} | {title} | famille {family}", file=stream)

    return 0


def _check_path(label, path):
    return label, path.exists(), str(path)


def command_doctor(root=ROOT, runner=run_command, stream=sys.stdout):
    checks = []
    checks.append(("Python", bool(sys.executable), sys.executable))
    libreoffice = shutil.which("soffice") or shutil.which("libreoffice")
    checks.append(("LibreOffice / soffice", bool(libreoffice), libreoffice or "not found"))
    checks.append(_check_path("config/project.yaml", root / "config" / "project.yaml"))
    checks.append(_check_path("config/document_registry.yaml", root / "config" / "document_registry.yaml"))
    checks.append(_check_path("knowledge/", root / "knowledge"))
    checks.append(_check_path("inbox/", root / "inbox"))
    checks.append(_check_path("output/", root / "output"))

    test_result = runner(["python3", "-m", "unittest", "discover"], timeout=60)
    checks.append(("tests", test_result.returncode == 0, "OK" if test_result.returncode == 0 else test_result.output))

    print("RHYAD doctor", file=stream)
    for label, ok, detail in checks:
        status = "OK" if ok else "FAIL"
        print(f"{status} {label}: {detail}", file=stream)

    return 0 if all(ok for _, ok, _ in checks) else 1


def command_help(stream=sys.stdout):
    print(HELP_TEXT, file=stream)
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv or argv[0] in {"help", "-h", "--help"}:
        return command_help()

    command = argv[0]
    if command == "status":
        return command_status()
    if command == "generate":
        if len(argv) != 2:
            print("Usage: rhyad generate <document>")
            return 2
        return command_generate(argv[1])
    if command == "import":
        if len(argv) != 2:
            print("Usage: rhyad import <document>")
            return 2
        return command_import(argv[1])
    if command == "validate":
        return command_validate()
    if command == "list":
        return command_list()
    if command == "doctor":
        return command_doctor()

    print(f"Unknown command: {command}")
    print("Run: rhyad help")
    return 2


if __name__ == "__main__":
    sys.exit(main())
