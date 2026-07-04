import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from engine.core.impact_engine import get_impacts
from engine.core.traceability_suggester import suggest_traceability


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
  rhyad impact <object>
  rhyad trace suggest
  rhyad trace approve
  rhyad dashboard
  rhyad help

Compatibility:
  python3 scripts/rhyad.py status
  python3 scripts/rhyad.py generate 002
  python3 scripts/rhyad.py import 003
  python3 scripts/rhyad.py validate
  python3 scripts/rhyad.py list
  python3 scripts/rhyad.py doctor
  python3 scripts/rhyad.py impact D-014
  python3 scripts/rhyad.py trace suggest
  python3 scripts/rhyad.py trace approve
  python3 scripts/rhyad.py dashboard
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


def count_yaml_list_entries(path, key):
    if not path.exists():
        return 0

    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    count = 0

    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped == f"{key}: []":
            return 0
        if stripped == f"{key}:":
            in_section = True
            continue
        if in_section and raw_line and not raw_line.startswith(" "):
            break
        if in_section and raw_line.startswith("  - "):
            count += 1

    return count


def knowledge_counts(root):
    knowledge_dir = root / "knowledge"
    return {
        "decisions": count_yaml_list_entries(knowledge_dir / "decisions.yaml", "decisions"),
        "risks": count_yaml_list_entries(knowledge_dir / "risks.yaml", "risks"),
        "assumptions": count_yaml_list_entries(knowledge_dir / "assumptions.yaml", "assumptions"),
        "requirements": count_yaml_list_entries(knowledge_dir / "requirements.yaml", "requirements"),
        "interfaces": count_yaml_list_entries(knowledge_dir / "interfaces.yaml", "interfaces"),
    }


def generated_document_count(root, registry):
    generated = 0
    for document in registry:
        official_code = document.get("official_code")
        revision = document.get("revision")
        family = document.get("family")
        if not official_code or not revision or not family:
            continue

        stem = f"{official_code}_{revision}"
        docx_path = root / "output" / "docx" / family / f"{stem}.docx"
        pdf_path = root / "output" / "pdf" / family / f"{stem}.pdf"
        if docx_path.exists() and pdf_path.exists():
            generated += 1

    return generated


def latest_generation(root):
    output_dir = root / "output"
    if not output_dir.exists():
        return "Aucune"

    files = [path for path in output_dir.rglob("*") if path.is_file()]
    if not files:
        return "Aucune"

    latest = max(files, key=lambda path: path.stat().st_mtime)
    timestamp = datetime.fromtimestamp(latest.stat().st_mtime).isoformat(timespec="seconds")
    return f"{timestamp} - {latest.relative_to(root)}"


def test_summary(runner=None):
    if runner is None:
        runner = run_command

    result = runner(["python3", "-m", "unittest", "discover"], timeout=60)
    count = "unknown"
    for line in result.output.splitlines():
        stripped = line.strip()
        if stripped.startswith("Ran ") and " tests" in stripped:
            count = stripped.split()[1]
            break
    return {
        "count": count,
        "result": "OK" if result.returncode == 0 else "FAILED",
    }


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


def command_impact(obj, root=ROOT, stream=sys.stdout):
    result = get_impacts(obj, root / "knowledge", root / "config" / "document_registry.yaml")

    print(f"Objet analysé: {result['source']}", file=stream)
    print("Documents impactés:", file=stream)
    if result["impacts"]:
        for impact in result["impacts"]:
            print(f"- {impact['destination']} ({impact['relation']})", file=stream)
    else:
        print("- Aucun impact identifié", file=stream)
    print(f"Nombre d'impacts: {result['impact_count']}", file=stream)
    print(f"Origine des relations: {result['traceability_path']}", file=stream)
    return 0


def command_trace(args, root=ROOT, stream=sys.stdout):
    if not args:
        print("Usage: rhyad trace suggest|approve", file=stream)
        return 2

    action = args[0]
    if action == "suggest":
        result = suggest_traceability(
            documents_dir=root / "config" / "documents",
            inbox_validated_dir=root / "inbox" / "validated",
            knowledge_dir=root / "knowledge",
            registry_path=root / "config" / "document_registry.yaml",
            suggestions_path=root / "knowledge" / "traceability_suggestions.yaml",
        )
        print("Suggestions de traçabilité", file=stream)
        print(f"Fichier: {result['suggestions_path']}", file=stream)
        print(f"Nombre de propositions: {result['suggestion_count']}", file=stream)
        print("knowledge/traceability.yaml n'a pas été modifié.", file=stream)
        return 0

    if action == "approve":
        print(
            "Validation automatique non activée. Vérifier knowledge/traceability_suggestions.yaml manuellement.",
            file=stream,
        )
        print("knowledge/traceability.yaml n'a pas été modifié.", file=stream)
        return 0

    print("Usage: rhyad trace suggest|approve", file=stream)
    return 2


def command_dashboard(root=ROOT, runner=run_command, stream=sys.stdout):
    project_config = load_project_summary(root / "config" / "project.yaml")
    registry = load_registry_documents(root / "config" / "document_registry.yaml")
    project = project_config.get("project", {})
    generated = generated_document_count(root, registry)
    tests = test_summary(runner=runner)
    counts = knowledge_counts(root)

    print("RHYAD dashboard", file=stream)
    print(f"Projet: {project.get('name', '')}", file=stream)
    print(f"Client: {project.get('client', '')}", file=stream)
    print(f"Branche Git: {_git_output(['rev-parse', '--abbrev-ref', 'HEAD'], runner=runner)}", file=stream)
    print(f"Dernier commit: {_git_output(['log', '-1', '--pretty=%h %s'], runner=runner)}", file=stream)
    print("Documents:", file=stream)
    print(f"- nombre total: {len(registry)}", file=stream)
    print(f"- générés: {generated}", file=stream)
    print(f"- en attente: {max(len(registry) - generated, 0)}", file=stream)
    print("Knowledge Core:", file=stream)
    print(f"- décisions: {counts['decisions']}", file=stream)
    print(f"- risques: {counts['risks']}", file=stream)
    print(f"- hypothèses: {counts['assumptions']}", file=stream)
    print(f"- exigences: {counts['requirements']}", file=stream)
    print(f"- interfaces: {counts['interfaces']}", file=stream)
    print("Tests:", file=stream)
    print(f"- nombre: {tests['count']}", file=stream)
    print(f"- résultat: {tests['result']}", file=stream)
    print(f"Dernière génération: {latest_generation(root)}", file=stream)
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
    if command == "impact":
        if len(argv) != 2:
            print("Usage: rhyad impact <object>")
            return 2
        return command_impact(argv[1])
    if command == "trace":
        return command_trace(argv[1:])
    if command == "dashboard":
        return command_dashboard()

    print(f"Unknown command: {command}")
    print("Run: rhyad help")
    return 2


if __name__ == "__main__":
    sys.exit(main())
