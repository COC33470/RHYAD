import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from engine.core.figures import check_figures, load_figures_registry, resolve_figure_path
from engine.core.impact_engine import get_impacts
from engine.core.traceability_suggester import suggest_traceability
from engine.utils.pdf import find_libreoffice_executable


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
  rhyad paste <document>
  rhyad validate
  rhyad list
  rhyad doctor
  rhyad impact <object>
  rhyad figures list
  rhyad figures check
  rhyad ui
  rhyad trace suggest
  rhyad trace approve
  rhyad dashboard
  rhyad help

Compatibility:
  python3 scripts/rhyad.py status
  python3 scripts/rhyad.py generate 002
  python3 scripts/rhyad.py import 003
  python3 scripts/rhyad.py paste 003
  python3 scripts/rhyad.py validate
  python3 scripts/rhyad.py list
  python3 scripts/rhyad.py doctor
  python3 scripts/rhyad.py impact D-014
  python3 scripts/rhyad.py figures list
  python3 scripts/rhyad.py figures check
  python3 scripts/rhyad.py ui
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


def _normalize_document_lookup(value):
    code = str(value).strip().upper()

    for prefix in ("DB", "REG", "DT"):
        match = re.fullmatch(rf"{prefix}[-_ ]?(\d{{1,3}})", code)
        if match:
            return f"{prefix}-{int(match.group(1)):03d}"

    return code


def find_registry_entry(root, document):
    requested_code = str(document).strip().upper()
    normalized_code = _normalize_document_lookup(requested_code)
    accepted_codes = {requested_code, normalized_code}

    for entry in load_registry_documents(root / "config" / "document_registry.yaml"):
        entry_code = str(entry.get("code", "")).strip().upper()
        if entry_code in accepted_codes:
            return entry

    return None


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


def _extract_prefixed_value(output, prefix):
    lines = output.splitlines()
    for index, line in enumerate(lines):
        if line.strip() == prefix:
            for following in lines[index + 1 :]:
                if following.strip():
                    return following.strip()
            return ""
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return ""


def summarize_import_output(output, returncode=0):
    docx_path = _extract_prefixed_value(output, "DOCX produit:")
    pdf_path = _extract_prefixed_value(output, "PDF produit:")

    tests = "Non disponible"
    test_match = re.search(r"Ran\s+(\d+)\s+tests?", output)
    if test_match:
        tests = f"{test_match.group(1)} {'OK' if re.search(r'(?m)^OK$', output) else 'FAILED'}"
    elif re.search(r"(?m)^OK$", output):
        tests = "OK"

    commit = "Non créé"
    commit_match = re.search(r"\[[^\]\n]+\s+([0-9a-f]{7,40})\]", output)
    if commit_match:
        commit = commit_match.group(1)
    elif returncode == 0:
        commit_message = _extract_prefixed_value(output, "Commit demandé:")
        if commit_message:
            commit = commit_message

    return {
        "docx": "OK" if docx_path else ("FAILED" if returncode else "Non confirmé"),
        "pdf": "OK" if pdf_path else ("FAILED" if returncode else "Non confirmé"),
        "tests": tests,
        "commit": commit,
    }


def command_paste(document, root=ROOT, stdin=sys.stdin, runner=run_command, stream=sys.stdout):
    registry_entry = find_registry_entry(root, document)
    if not registry_entry:
        print(f"Document inconnu dans config/document_registry.yaml: {document}", file=stream)
        return 1

    document_code = str(registry_entry.get("code", document)).strip().upper()
    official_code = registry_entry.get("official_code", document_code)

    print("-" * 50, file=stream)
    print("RHYAD Import interactif", file=stream)
    print("", file=stream)
    print("Document :", file=stream)
    print(official_code, file=stream)
    print("", file=stream)
    print("Collez maintenant le contenu validé.", file=stream)
    print("", file=stream)
    print("Terminez par :", file=stream)
    print("Ctrl+D (macOS/Linux)", file=stream)
    print("Ctrl+Z puis Entrée (Windows)", file=stream)
    print("-" * 50, file=stream)

    content = stdin.read()
    if not content.strip():
        print("Erreur: contenu vide.", file=stream)
        return 1

    validated_dir = root / "inbox" / "validated"
    validated_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = validated_dir / f"{document_code}.md"
    markdown_path.write_text(content, encoding="utf-8")

    result = runner(["python3", "scripts/import_validated.py", document_code])
    summary = summarize_import_output(result.output, result.returncode)

    print("", file=stream)
    print("Document :", file=stream)
    print(official_code, file=stream)
    print("", file=stream)
    print("Lignes importées :", file=stream)
    print(len(content.splitlines()), file=stream)
    print("", file=stream)
    print("DOCX :", file=stream)
    print(summary["docx"], file=stream)
    print("", file=stream)
    print("PDF :", file=stream)
    print(summary["pdf"], file=stream)
    print("", file=stream)
    print("Tests :", file=stream)
    print(summary["tests"], file=stream)
    print("", file=stream)
    print("Commit :", file=stream)
    print(summary["commit"], file=stream)

    if result.returncode != 0 and result.output:
        print("", file=stream)
        print("Sortie pipeline :", file=stream)
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
        title = document.get("title", "") or titles.get(code.upper(), "")
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


def command_figures(args, root=ROOT, stream=sys.stdout):
    if not args or args[0] not in {"list", "check"}:
        print("Usage: rhyad figures list|check", file=stream)
        return 2

    registry_path = root / "config" / "figures_registry.yaml"
    if args[0] == "list":
        registry = load_figures_registry(registry_path)
        print("Figures RHYAD", file=stream)
        for figure in registry.get("figures", []):
            used_in = ", ".join(figure.get("used_in", [])) or "-"
            print(
                f"{figure['id']} | {figure['title']} | {figure['file']} | {figure['status']} | {used_in}",
                file=stream,
            )
        return 0

    result = check_figures(root, registry_path)
    print("Figures RHYAD check", file=stream)
    print(f"Figures déclarées: {result['declared']}", file=stream)
    print(f"Fichiers existants: {len(result['existing'])}", file=stream)
    print(f"Figures manquantes: {len(result['missing'])}", file=stream)
    for figure in result["missing"]:
        print(f"- {figure['id']}: {resolve_figure_path(root, figure)}", file=stream)
    print(f"Formats non supportés: {len(result['unsupported'])}", file=stream)
    for figure in result["unsupported"]:
        print(f"- {figure['id']}: {figure['file']}", file=stream)
    print(f"Figures non utilisées: {len(result['unused'])}", file=stream)
    for figure in result["unused"]:
        print(f"- {figure['id']}", file=stream)

    return 1 if result["missing"] or result["unsupported"] else 0


def _read_ui_input(input_func, stream, prompt="Choix : "):
    print(prompt, end="", file=stream)
    try:
        return input_func().strip()
    except EOFError:
        return "0"


def _ui_wait(input_func, stream):
    print("", file=stream)
    print("Entrée pour continuer...", end="", file=stream)
    try:
        input_func()
    except EOFError:
        pass


def _load_document_summary(root, document):
    path = _document_source_path(root, document)
    summary = {
        "reference": document.get("official_code", ""),
        "title": document.get("title", ""),
        "revision": document.get("revision", ""),
        "status": document.get("status", ""),
    }
    if not path.exists():
        return summary

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if raw_line.startswith("chapters:"):
            break
        stripped = raw_line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, value = _parse_scalar(stripped)
        if key in summary:
            summary[key] = value

    return summary


def _document_source_path(root, document):
    source = document.get("source", "")
    path = Path(source)
    if source and not path.is_absolute():
        path = root / path
    return path


def _documents_for_ui(root):
    registry = load_registry_documents(root / "config" / "document_registry.yaml")
    repository_titles = load_repository_titles(root / "config" / "rhyad_repository.yaml")
    documents = []
    for document in registry:
        summary = _load_document_summary(root, document)
        code = document.get("code", "")
        title = summary.get("title") or repository_titles.get(code.upper(), "")
        source_path = _document_source_path(root, document)
        documents.append(
            {
                "code": code,
                "official_code": document.get("official_code", ""),
                "family": document.get("family", ""),
                "title": title,
                "revision": summary.get("revision") or document.get("revision", ""),
                "status": summary.get("status", ""),
                "source": document.get("source", ""),
                "source_exists": source_path.exists(),
                "source_path": source_path,
            }
        )
    return documents


def _existing_documents_for_ui(root):
    return [document for document in _documents_for_ui(root) if document["source_exists"]]


def _missing_source_documents_for_ui(root):
    return [document for document in _documents_for_ui(root) if not document["source_exists"]]


def _document_state(status):
    value = str(status).strip().lower()
    if not value:
        return None
    if "published" in value or "publié" in value:
        return "Published"
    if "validated" in value or "validé" in value or "valide" in value:
        return "Validated"
    if "review" in value or "revue" in value:
        return "Review"
    if "draft" in value or "brouillon" in value or "working" in value:
        return "Draft"
    return None


def _document_state_counts(root):
    counts = {"Draft": 0, "Review": 0, "Validated": 0, "Published": 0}
    for document in _documents_for_ui(root):
        state = _document_state(document.get("status", ""))
        if state in counts:
            counts[state] += 1
    return counts


def _open_items_count(path, key):
    if not path.exists():
        return 0

    closed_statuses = {
        "closed",
        "clôturé",
        "cloture",
        "done",
        "terminé",
        "termine",
        "validated",
        "validé",
        "valide",
        "published",
        "obsolete",
    }
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    entries = []
    current_status = None

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
            if current_status is not None:
                entries.append(current_status)
            current_status = ""
            if "status:" in stripped:
                _, current_status = _parse_scalar(stripped[2:])
            continue
        if in_section and current_status is not None and stripped.startswith("status:"):
            _, current_status = _parse_scalar(stripped)

    if current_status is not None:
        entries.append(current_status)

    return sum(1 for status in entries if str(status).strip().lower() not in closed_statuses)


def _impacted_documents_count(root):
    path = root / "knowledge" / "traceability.yaml"
    if not path.exists():
        return 0
    destinations = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("destination:"):
            _, value = _parse_scalar(stripped)
            if value:
                destinations.add(value)
    return len(destinations)


def _next_meeting(root):
    path = root / "knowledge" / "meetings.yaml"
    if not path.exists():
        return "À planifier"
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("date:"):
            _, value = _parse_scalar(stripped)
            if value and value not in {"À compléter", "A compléter"}:
                return value
    return "À planifier"


def _git_summary(runner):
    branch = _git_output(["rev-parse", "--abbrev-ref", "HEAD"], runner=runner)
    status = _git_output(["status", "--short"], runner=runner)
    state = "clean" if not status else "modifié"
    return f"{branch} / {state}"


def _print_ui_home(root, runner, stream):
    project_config = load_project_summary(root / "config" / "project.yaml")
    project = project_config.get("project", {})
    project_name = project.get("name", "")

    print("====================================================", file=stream)
    print("RHYAD", file=stream)
    print("Assistant AMO / Maîtrise d'Œuvre Industrielle", file=stream)
    print("====================================================", file=stream)
    print("", file=stream)
    print("Projet actif :", file=stream)
    print(project_name, file=stream)
    print("", file=stream)
    print("----------------------------------------------------", file=stream)
    print("", file=stream)
    print("1. Tableau de bord", file=stream)
    print("", file=stream)
    print("2. Documents", file=stream)
    print("", file=stream)
    print("3. Réunions", file=stream)
    print("", file=stream)
    print("4. Décisions", file=stream)
    print("", file=stream)
    print("5. Actions", file=stream)
    print("", file=stream)
    print("6. Risques", file=stream)
    print("", file=stream)
    print("7. Design Basis", file=stream)
    print("", file=stream)
    print("8. Données Techniques", file=stream)
    print("", file=stream)
    print("9. Générer les livrables", file=stream)
    print("", file=stream)
    print("10. Synchroniser le projet", file=stream)
    print("", file=stream)
    print("11. Administration", file=stream)
    print("", file=stream)
    print("0. Quitter", file=stream)
    print("", file=stream)
    print("----------------------------------------------------", file=stream)


def _print_ui_dashboard(root, runner, stream):
    project_config = load_project_summary(root / "config" / "project.yaml")
    project = project_config.get("project", {})
    states = _document_state_counts(root)

    print("Tableau de bord", file=stream)
    print("", file=stream)
    print(f"Projet : {project.get('name', '')}", file=stream)
    print(f"Git : {_git_summary(runner)}", file=stream)
    print(f"Dernière génération : {latest_generation(root)}", file=stream)
    print(f"Documents Draft : {states['Draft']}", file=stream)
    print(f"Documents Review : {states['Review']}", file=stream)
    print(f"Documents Validated : {states['Validated']}", file=stream)
    print(f"Documents Published : {states['Published']}", file=stream)
    print(f"Décisions ouvertes : {_open_items_count(root / 'knowledge' / 'decisions.yaml', 'decisions')}", file=stream)
    print(f"Actions ouvertes : {_open_items_count(root / 'knowledge' / 'actions.yaml', 'actions')}", file=stream)
    print(f"Risques ouverts : {_open_items_count(root / 'knowledge' / 'risks.yaml', 'risks')}", file=stream)
    print(f"Documents impactés : {_impacted_documents_count(root)}", file=stream)
    print(f"Prochaine réunion : {_next_meeting(root)}", file=stream)


def _print_documents(documents, stream):
    print("Documents", file=stream)
    for document in documents:
        status = document.get("status") or "À définir"
        print(
            f"{document['official_code']} | {document['title']} | famille {document['family']} | {status}",
            file=stream,
        )


def _print_numbered_documents(documents, stream):
    if not documents:
        print("Aucun document.", file=stream)
        return

    for index, document in enumerate(documents, start=1):
        status = document.get("status") or "À définir"
        print(
            f"{index}. {document['official_code']} | {document['title']} | famille {document['family']} | {status}",
            file=stream,
        )


def _select_document(documents, stream, input_func):
    _print_numbered_documents(documents, stream)
    if not documents:
        return None

    choice = _read_ui_input(input_func, stream, "Sélection : ")
    try:
        index = int(choice)
    except ValueError:
        print("Sélection invalide.", file=stream)
        return None

    if index < 1 or index > len(documents):
        print("Sélection invalide.", file=stream)
        return None

    return documents[index - 1]


def create_document_skeleton(document):
    document["source_path"].parent.mkdir(parents=True, exist_ok=True)
    document["source_path"].write_text(
        "\n".join(
            [
                f"reference: \"{document['official_code']}\"",
                f"title: \"{document['title']}\"",
                f"revision: \"{document.get('revision') or 'Rev0.1'}\"",
                "status: \"Draft\"",
                "",
                "chapters:",
                "  - title: \"1. Contenu\"",
                "    text: \"À compléter.\"",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return document["source_path"]


def _ui_documents(root, runner, stream, input_func, paste_func=command_paste):
    while True:
        print("Menu Documents", file=stream)
        print("1. Afficher tous les documents", file=stream)
        print("2. Filtrer par famille", file=stream)
        print("3. Afficher le statut", file=stream)
        print("4. Ouvrir un document", file=stream)
        print("5. Mettre à jour un document", file=stream)
        print("6. Générer un document", file=stream)
        print("7. Nouveau document", file=stream)
        print("0. Retour", file=stream)
        choice = _read_ui_input(input_func, stream)

        if choice == "0":
            return

        documents = _documents_for_ui(root)
        if choice == "1":
            _print_documents(documents, stream)
            _ui_wait(input_func, stream)
            continue
        if choice == "2":
            family = _read_ui_input(input_func, stream, "Famille : ")
            _print_documents([doc for doc in documents if doc["family"] == family], stream)
            _ui_wait(input_func, stream)
            continue
        if choice == "3":
            _print_documents(documents, stream)
            _ui_wait(input_func, stream)
            continue
        if choice == "4":
            code = _read_ui_input(input_func, stream, "Document : ")
            document = next((doc for doc in documents if doc["code"].upper() == code.upper()), None)
            if document:
                _print_documents([document], stream)
            else:
                print("Document non trouvé.", file=stream)
            _ui_wait(input_func, stream)
            continue
        if choice == "5":
            code = _read_ui_input(input_func, stream, "Document : ")
            paste_func(code, root=root, runner=runner, stream=stream)
            _ui_wait(input_func, stream)
            continue
        if choice == "6":
            existing_documents = _existing_documents_for_ui(root)
            print("Documents existants", file=stream)
            document = _select_document(existing_documents, stream, input_func)
            if document:
                command_generate(document["code"], runner=runner, stream=stream)
            _ui_wait(input_func, stream)
            continue
        if choice == "7":
            missing_documents = _missing_source_documents_for_ui(root)
            print("Nouveaux documents disponibles", file=stream)
            document = _select_document(missing_documents, stream, input_func)
            if document:
                create_document_skeleton(document)
                print(f"Document préparé : {document['official_code']}", file=stream)
                paste_func(document["code"], root=root, runner=runner, stream=stream)
            _ui_wait(input_func, stream)
            continue

        print("Choix non reconnu.", file=stream)


def _ui_simple_menu(title, actions, stream, input_func):
    print(title, file=stream)
    for action in actions:
        print(f"- {action}", file=stream)
    print("", file=stream)
    print("0. Retour", file=stream)
    _read_ui_input(input_func, stream)


def _ui_generate_deliverables(root, runner, stream, input_func):
    print("Générer les livrables", file=stream)
    document = _select_document(_existing_documents_for_ui(root), stream, input_func)
    if document:
        command_generate(document["code"], runner=runner, stream=stream)
    _ui_wait(input_func, stream)


def _ui_sync_project(runner, stream, input_func):
    print("Synchroniser le projet", file=stream)
    print(f"État du projet : {_git_summary(runner)}", file=stream)
    print("Aucune synchronisation distante n'est lancée automatiquement.", file=stream)
    _ui_wait(input_func, stream)


def command_ui(root=ROOT, runner=run_command, stream=sys.stdout, input_func=input, paste_func=command_paste):
    while True:
        _print_ui_home(root, runner, stream)
        choice = _read_ui_input(input_func, stream)

        if choice == "0":
            print("Fermeture de l'interface RHYAD.", file=stream)
            return 0
        if choice == "1":
            _print_ui_dashboard(root, runner, stream)
            _ui_wait(input_func, stream)
            continue
        if choice == "2":
            _ui_documents(root, runner, stream, input_func, paste_func=paste_func)
            continue
        if choice == "3":
            _ui_simple_menu(
                "Menu Réunions",
                (
                    "Créer une réunion",
                    "Coller un compte rendu",
                    "Analyser les décisions, actions, risques et documents impactés",
                    "Proposer les mises à jour",
                ),
                stream,
                input_func,
            )
            continue
        if choice == "4":
            _ui_simple_menu(
                "Menu Décisions",
                (
                    "Consulter les décisions",
                    "Créer une décision",
                    "Voir les impacts documentaires",
                    "Lancer la propagation",
                ),
                stream,
                input_func,
            )
            continue
        if choice == "5":
            _ui_simple_menu("Menu Actions", ("Consulter les actions", "Créer une action", "Modifier le statut"), stream, input_func)
            continue
        if choice == "6":
            _ui_simple_menu(
                "Menu Risques",
                (
                    "Consulter les risques",
                    "Créer un risque",
                    "Modifier son statut",
                    "Voir les documents associés",
                ),
                stream,
                input_func,
            )
            continue
        if choice == "7":
            _ui_simple_menu("Design Basis", ("Consulter les Design Basis", "Voir les documents à produire"), stream, input_func)
            continue
        if choice == "8":
            _ui_simple_menu("Données Techniques", ("Consulter les données techniques", "Voir les hypothèses associées"), stream, input_func)
            continue
        if choice == "9":
            _ui_generate_deliverables(root, runner, stream, input_func)
            continue
        if choice == "10":
            _ui_sync_project(runner, stream, input_func)
            continue
        if choice == "11":
            _ui_simple_menu("Administration", ("Afficher l'état du projet", "Contrôler l'environnement"), stream, input_func)
            continue

        print("Choix non reconnu.", file=stream)


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
    libreoffice = find_libreoffice_executable()
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
    if command == "paste":
        if len(argv) != 2:
            print("Usage: rhyad paste <document>")
            return 2
        return command_paste(argv[1])
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
    if command == "figures":
        return command_figures(argv[1:])
    if command == "ui":
        return command_ui()
    if command == "trace":
        return command_trace(argv[1:])
    if command == "dashboard":
        return command_dashboard()

    print(f"Unknown command: {command}")
    print("Run: rhyad help")
    return 2


if __name__ == "__main__":
    sys.exit(main())
