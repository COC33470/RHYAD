from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import Optional, Union
import unicodedata

try:
    import yaml
except ImportError:
    yaml = None

from app.modules.meetings.models import (
    MeetingAnalysisDraft,
    MeetingPostAnalysisResult,
    TranscriptSegment,
    TranscriptionResult,
)


DOCUMENT_PATTERN = re.compile(r"\bCEVA-RHYAD-[A-Z0-9][A-Z0-9_-]*(?:-[A-Z0-9][A-Z0-9_-]*)*\b")
DATE_PATTERN = re.compile(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b")
TRANSCRIPT_LINE_PATTERN = re.compile(
    r"^\[(?P<start>\d{2}:\d{2}:\d{2})\s+-->\s+(?P<end>\d{2}:\d{2}:\d{2})\]\s*(?P<text>.*)$"
)


DEFAULT_GLOSSARY = {
    "corrections": {
        "estricité": "électricité",
        "écronique": "électronique",
        "rabise au lit": "Arabie Saoudite",
        "l'armi solid": "Arabie Saoudite",
        "rabit sa audite": "Arabie Saoudite",
        "sa audite": "Saoudite",
        "master-sins": "master seeds",
        "master-sin": "master seed",
        "souchets": "souches",
        "congestures": "congélateurs",
        "programme fonctionnale": "programme fonctionnel",
        "programmes fonctionnales": "programmes fonctionnels",
        "bureau d'études": "bureau d'études",
        "appel d'offre": "appel d'offres",
        "appel d offres": "appel d'offres",
        "autobax": "autovaccin",
        "autoraxin": "autovaccin",
    },
    "terms": [
        {"canonical": "CEVA", "aliases": ["céva", "ceva", "séva"]},
        {"canonical": "RHYAD", "aliases": ["rhyad", "riad", "riyad"]},
        {"canonical": "Arabie Saoudite", "aliases": ["arabie saoudite", "arabie saoudite", "ksa"]},
        {"canonical": "autovaccin", "aliases": ["autovaccin", "autovaccins", "vaccin autogène", "vaccin autogene"]},
        {"canonical": "vétérinaire", "aliases": ["vétérinaire", "veterinaire", "vétérinaires"]},
        {"canonical": "UPS", "aliases": ["ups", "onduleur", "onduleurs"]},
        {"canonical": "microcoupures", "aliases": ["micro coupures", "micro-coupures", "microcoupure"]},
        {"canonical": "URS", "aliases": ["urs", "user requirement specification"]},
        {"canonical": "BSL2", "aliases": ["bsl2", "bsl 2", "biosafety level 2"]},
        {"canonical": "master seeds", "aliases": ["master seeds", "master seed", "master-seeds"]},
        {"canonical": "congélateurs", "aliases": ["congelateurs", "congélateur", "congelateur"]},
        {"canonical": "souches", "aliases": ["souche", "souches"]},
        {"canonical": "sas", "aliases": ["sas", "airlock", "pal", "mal"]},
        {"canonical": "module", "aliases": ["module", "modules", "modulaire", "modulaires"]},
        {"canonical": "couloir", "aliases": ["couloir", "couloirs"]},
        {"canonical": "stockage", "aliases": ["stockage", "stockages", "magasin"]},
        {"canonical": "déchets", "aliases": ["déchets", "dechets", "effluents"]},
        {"canonical": "flux matières", "aliases": ["flux matières", "flux matieres", "flux matériel", "flux materiel"]},
        {"canonical": "flux personnel", "aliases": ["flux personnel", "flux personnes", "flux des personnes"]},
        {"canonical": "réglementation", "aliases": ["réglementation", "reglementation", "réglementaire", "reglementaire"]},
        {"canonical": "appel d'offres", "aliases": ["appel d'offres", "tender", "rfq"]},
        {"canonical": "autorités", "aliases": ["autorites", "autorités", "sfda"]},
        {"canonical": "terrain", "aliases": ["terrain", "terrains"]},
        {"canonical": "dashboard", "aliases": ["dashboard", "tableau de bord", "r05"]},
        {"canonical": "compte rendu", "aliases": ["compte rendu", "compte-rendu"]},
        {"canonical": "registre des décisions", "aliases": ["registre des décisions", "registre des decisions", "decision log"]},
        {"canonical": "registre des actions", "aliases": ["registre des actions", "action log"]},
        {"canonical": "registre des risques", "aliases": ["registre des risques", "risk register"]},
    ],
    "extraction_topics": {
        "programme_fonctionnel": {
            "title": "Programme fonctionnel",
            "keywords": [
                "programme fonctionnel",
                "fonction",
                "sous-fonction",
                "réception",
                "expédition",
                "stockage",
                "contrôle qualité",
                "maintenance",
                "déchets",
                "effluents",
            ],
            "documents": ["CEVA-RHYAD-002-PF", "CEVA-RHYAD-100-F01..F15", "CEVA-RHYAD-200-F01..F15-DT01"],
        },
        "site_arabie_saoudite": {
            "title": "Contraintes site Arabie Saoudite",
            "keywords": ["Arabie Saoudite", "KSA", "site", "climatique", "terrain", "local"],
            "documents": ["CEVA-RHYAD-002-PF", "DB002 Architecture", "DB003 Bâtiment"],
        },
        "electricite_ups_microcoupures": {
            "title": "Alimentation électrique / UPS / microcoupures",
            "keywords": ["électricité", "UPS", "onduleur", "microcoupures", "coupure", "surtension", "alimentation"],
            "documents": ["CEVA-RHYAD-200-F09-DT01", "DB004 Utilités", "DB010 Sécurité"],
        },
        "froid_souches_master_seeds": {
            "title": "Froid / congélateurs / souches / master seeds",
            "keywords": ["froid", "chambre froide", "congélateurs", "souches", "master seeds", "collection"],
            "documents": ["CEVA-RHYAD-100-F02", "CEVA-RHYAD-200-F02-DT01", "DB006 Production", "DB007 Qualité"],
        },
        "modules_couloirs_sas_bsl2": {
            "title": "Modules / couloirs / sas / BSL2",
            "keywords": ["module", "modulaire", "couloir", "sas", "BSL2", "airlock", "PAL", "MAL"],
            "documents": ["CEVA-RHYAD-002-PF", "DB001 Process", "DB002 Architecture", "DB008 Biosécurité"],
        },
        "flux_matieres_dechets_personnel": {
            "title": "Flux matières / déchets / personnel",
            "keywords": ["flux", "matière", "matériel", "personnel", "déchets", "effluents", "accès"],
            "documents": ["CEVA-RHYAD-100-F06", "CEVA-RHYAD-100-F11", "CEVA-RHYAD-200-F06-DT01"],
        },
        "terrain_calendrier_appel_offres": {
            "title": "Terrain / calendrier / septembre / appel d'offres",
            "keywords": ["terrain", "calendrier", "septembre", "appel d'offres", "tender", "planning", "délai"],
            "documents": ["CEVA-RHYAD-400-R05", "CEVA-RHYAD-004-REGISTRE_DES_RISQUES"],
        },
        "reglementation_autorites_urs": {
            "title": "Réglementation / autorités / URS",
            "keywords": ["réglementation", "autorités", "SFDA", "URS", "GMP", "BPF", "qualité"],
            "documents": ["CEVA-RHYAD-002-PF", "DB007 Qualité", "DB010 Sécurité"],
        },
        "risques_projet": {
            "title": "Risques projet",
            "keywords": ["risque", "risques", "blocage", "bloquant", "retard", "sécuriser", "problème"],
            "documents": ["CEVA-RHYAD-004-REGISTRE_DES_RISQUES", "CEVA-RHYAD-400-R05"],
        },
    },
}

ACTION_KEYWORDS = (
    "action",
    "à faire",
    "a faire",
    "il faut",
    "faut qu",
    "doit",
    "identifier",
    "travailler",
    "envoyer",
    "regarder",
    "valider",
    "préparer",
    "appel d'offres",
    "responsable",
)
DECISION_KEYWORDS = ("décision", "decide", "décidé", "validé", "arbitré", "retenu", "on va")
RISK_KEYWORDS = (
    "risque",
    "blocage",
    "bloquant",
    "retard",
    "problème",
    "coupure",
    "microcoupures",
    "UPS",
    "surtension",
    "froid",
    "congélateurs",
    "souches",
    "master seeds",
    "terrain",
    "réglementation",
)
LOW_VALUE_LINES = {"oui", "ok", "okay", "non", "bon", "ah", "ça", "d'accord"}


@dataclass(frozen=True)
class CleanedTranscriptLine:
    start: str
    end: str
    text: str

    def evidence(self) -> str:
        if self.start and self.end:
            return f"[{self.start} --> {self.end}] {self.text}"
        return self.text


class MeetingAnalysisService:
    def __init__(self, glossary_path: Optional[Path] = None):
        self.glossary_path = Path(glossary_path) if glossary_path else None
        self.glossary = self._load_glossary(self.glossary_path)

    def prepare_draft(self, segments: list[TranscriptSegment]) -> MeetingAnalysisDraft:
        decisions = []
        actions = []
        deadlines = []
        risks = []
        documents = set()

        for segment in segments:
            text = segment.text.strip()
            lowered = text.lower()

            if any(keyword in lowered for keyword in ("décision", "decide", "décidé", "validé", "arbitré")):
                decisions.append(text)
            if any(keyword in lowered for keyword in ("action", "à faire", "a faire", "responsable", "doit", "prendre en charge")):
                actions.append(text)
            if DATE_PATTERN.search(text) or any(keyword in lowered for keyword in ("échéance", "deadline", "avant le", "pour le")):
                deadlines.append(text)
            if any(keyword in lowered for keyword in ("risque", "blocage", "bloquant", "alerte", "retard", "dérive")):
                risks.append(text)

            for match in DOCUMENT_PATTERN.findall(text):
                documents.add(match)

        return MeetingAnalysisDraft(
            decisions=decisions,
            actions=actions,
            deadlines=deadlines,
            risks=risks,
            documents=sorted(documents),
        )

    def analyze_transcript_file(
        self,
        transcript_path: Path,
        transcript_cleaned_path: Path,
        output_dir: Path,
        meeting_id: str,
    ) -> MeetingPostAnalysisResult:
        transcript_text = transcript_path.read_text(encoding="utf-8")
        cleaned_lines = self.post_transcription_cleanup(transcript_text)
        extracted_topics = self.extract_business_topics(cleaned_lines)
        actions = self.extract_candidates(cleaned_lines, ACTION_KEYWORDS)
        decisions = self.extract_candidates(cleaned_lines, DECISION_KEYWORDS)
        risks = self.extract_candidates(cleaned_lines, RISK_KEYWORDS)
        document_impacts = self.extract_document_impacts(extracted_topics)

        output_dir.mkdir(parents=True, exist_ok=True)
        transcript_cleaned_path.parent.mkdir(parents=True, exist_ok=True)

        result = MeetingPostAnalysisResult(
            meeting_id=meeting_id,
            source_transcript_path=transcript_path,
            transcript_cleaned_path=transcript_cleaned_path,
            meeting_minutes_draft_path=output_dir / "meeting_minutes_draft.md",
            action_log_path=output_dir / "action_log.md",
            decision_log_path=output_dir / "decision_log.md",
            risk_register_update_path=output_dir / "risk_register_update.md",
            document_impact_log_path=output_dir / "document_impact_log.md",
            created_at=datetime.now().isoformat(timespec="seconds"),
            extracted_topics=extracted_topics,
            actions=actions,
            decisions=decisions,
            risks=risks,
            document_impacts=document_impacts,
        )

        self._write_post_analysis_outputs(result, cleaned_lines)
        return result

    def clean_transcript_file(
        self,
        transcript_path: Path,
        transcript_cleaned_path: Path,
        meeting_id: str,
    ) -> Path:
        transcript_text = transcript_path.read_text(encoding="utf-8")
        cleaned_lines = self.post_transcription_cleanup(transcript_text)
        extracted_topics = self.extract_business_topics(cleaned_lines)
        transcript_cleaned_path.parent.mkdir(parents=True, exist_ok=True)

        result = MeetingPostAnalysisResult(
            meeting_id=meeting_id,
            source_transcript_path=transcript_path,
            transcript_cleaned_path=transcript_cleaned_path,
            meeting_minutes_draft_path=transcript_cleaned_path.parent / "meeting_minutes_draft.md",
            action_log_path=transcript_cleaned_path.parent / "action_log.md",
            decision_log_path=transcript_cleaned_path.parent / "decision_log.md",
            risk_register_update_path=transcript_cleaned_path.parent / "risk_register_update.md",
            document_impact_log_path=transcript_cleaned_path.parent / "document_impact_log.md",
            created_at=datetime.now().isoformat(timespec="seconds"),
            extracted_topics=extracted_topics,
        )
        transcript_cleaned_path.write_text(
            self._build_cleaned_transcript_markdown(result, cleaned_lines),
            encoding="utf-8",
        )
        return transcript_cleaned_path

    def post_transcription_cleanup(self, transcript_text: str) -> list[CleanedTranscriptLine]:
        cleaned_lines = []

        for raw_line in transcript_text.splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            start = ""
            end = ""
            text = raw_line
            match = TRANSCRIPT_LINE_PATTERN.match(raw_line)
            if match:
                start = match.group("start")
                end = match.group("end")
                text = match.group("text")

            text = self._cleanup_text(text)
            if not text or self._is_low_value_line(text):
                continue

            cleaned_lines.append(CleanedTranscriptLine(start=start, end=end, text=text))

        return cleaned_lines

    def extract_business_topics(self, cleaned_lines: list[CleanedTranscriptLine]) -> dict[str, list[str]]:
        extracted: dict[str, list[str]] = {}
        topics = self.glossary.get("extraction_topics", {})

        for topic_key, topic_config in topics.items():
            keywords = [str(keyword) for keyword in topic_config.get("keywords", [])]
            evidences = []
            for line in cleaned_lines:
                if self._contains_any(line.text, keywords):
                    evidences.append(line.evidence())
            extracted[topic_key] = self._dedupe(evidences)

        return extracted

    def extract_candidates(self, cleaned_lines: list[CleanedTranscriptLine], keywords: tuple[str, ...]) -> list[str]:
        candidates = []
        for line in cleaned_lines:
            if DATE_PATTERN.search(line.text) or self._contains_any(line.text, keywords):
                candidates.append(line.evidence())
        return self._dedupe(candidates)

    def extract_document_impacts(self, extracted_topics: dict[str, list[str]]) -> list[str]:
        impacts = []
        topics = self.glossary.get("extraction_topics", {})

        for topic_key, evidences in extracted_topics.items():
            if not evidences:
                continue
            topic_config = topics.get(topic_key, {})
            title = topic_config.get("title", topic_key)
            documents = topic_config.get("documents", [])
            for document in documents:
                impacts.append(f"{document} | {title} | {len(evidences)} extrait(s) source")

        return self._dedupe(impacts)

    def build_summary_markdown(self, result: TranscriptionResult) -> str:
        draft = result.analysis_draft
        lines = [
            f"# Meeting Summary Draft - {result.meeting_id}",
            "",
            "## Source",
            "",
            f"- Audio: `{result.stored_audio_path}`",
            f"- Langue: `{result.language}`",
            f"- Backend transcription: `{result.backend}`",
            f"- Modèle: `{result.model_name}`",
            "",
            "## Extraction IA à préparer",
            "",
            "### Décisions candidates",
            *self._bullet_lines(draft.decisions),
            "",
            "### Actions candidates",
            *self._bullet_lines(draft.actions),
            "",
            "### Échéances candidates",
            *self._bullet_lines(draft.deadlines),
            "",
            "### Risques candidats",
            *self._bullet_lines(draft.risks),
            "",
            "### Documents évoqués",
            *self._bullet_lines(draft.documents),
            "",
            "## Transcription horodatée",
            "",
        ]

        for segment in result.segments:
            lines.append(f"- [{segment.to_dict()['start_timestamp']} -> {segment.to_dict()['end_timestamp']}] {segment.text}")

        return "\n".join(lines).rstrip() + "\n"

    def _bullet_lines(self, values: list[str]) -> list[str]:
        if not values:
            return ["- À extraire par IA."]
        return [f"- {value}" for value in values]

    def _write_post_analysis_outputs(
        self,
        result: MeetingPostAnalysisResult,
        cleaned_lines: list[CleanedTranscriptLine],
    ) -> None:
        result.transcript_cleaned_path.write_text(
            self._build_cleaned_transcript_markdown(result, cleaned_lines),
            encoding="utf-8",
        )
        result.meeting_minutes_draft_path.write_text(
            self._build_meeting_minutes_markdown(result),
            encoding="utf-8",
        )
        result.action_log_path.write_text(self._build_candidate_log("Action log", result.actions), encoding="utf-8")
        result.decision_log_path.write_text(
            self._build_candidate_log("Decision log", result.decisions),
            encoding="utf-8",
        )
        result.risk_register_update_path.write_text(
            self._build_candidate_log("Risk register update", result.risks),
            encoding="utf-8",
        )
        result.document_impact_log_path.write_text(
            self._build_document_impact_markdown(result),
            encoding="utf-8",
        )

    def _build_cleaned_transcript_markdown(
        self,
        result: MeetingPostAnalysisResult,
        cleaned_lines: list[CleanedTranscriptLine],
    ) -> str:
        lines = [
            f"# Transcription nettoyée - {result.meeting_id}",
            "",
            "## Source",
            "",
            f"- Transcript source: `{result.source_transcript_path}`",
            f"- Dictionnaire métier: `{self.glossary_path or 'configuration par défaut'}`",
            "- Nettoyage: corrections lexicales RHYAD/CEVA et suppression des lignes sans valeur métier.",
            "- Limite: les intervenants ne sont pas inférés.",
            "",
            "## Vue par thèmes",
            "",
        ]

        topics = self.glossary.get("extraction_topics", {})
        for topic_key, topic_config in topics.items():
            evidences = result.extracted_topics.get(topic_key, [])
            if not evidences:
                continue
            title = topic_config.get("title", topic_key)
            lines.extend([f"### {title}", ""])
            lines.extend(self._limited_bullet_lines(evidences, limit=12))
            lines.append("")

        lines.extend(
            [
            "## Transcription nettoyée horodatée",
            "",
            ]
        )
        lines.extend(f"- {self._mark_uncertain_evidence(line.evidence())}" for line in cleaned_lines)
        return "\n".join(lines).rstrip() + "\n"

    def _build_meeting_minutes_markdown(self, result: MeetingPostAnalysisResult) -> str:
        lines = [
            f"# Compte rendu draft - {result.meeting_id}",
            "",
            "## Statut",
            "",
            "- Draft interne RHYAD issu d'une transcription bruitée.",
            "- Priorité donnée aux informations métier exploitables, pas au mot-à-mot.",
            "- Intervenants, responsables et échéances nominatives à confirmer.",
            "",
            "## Synthèse métier priorisée",
            "",
        ]

        topics = self.glossary.get("extraction_topics", {})
        for topic_key, topic_config in topics.items():
            title = topic_config.get("title", topic_key)
            lines.extend([f"### {title}", ""])
            lines.extend(self._limited_bullet_lines(result.extracted_topics.get(topic_key, [])))
            lines.append("")

        lines.extend(
            [
                "## Actions candidates",
                "",
                *self._limited_bullet_lines(result.actions),
                "",
                "## Décisions candidates",
                "",
                *self._limited_bullet_lines(result.decisions),
                "",
                "## Risques candidats",
                "",
                *self._limited_bullet_lines(result.risks),
                "",
                "## Documents impactés candidats",
                "",
                *self._bullet_lines(result.document_impacts),
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    def _build_candidate_log(self, title: str, values: list[str]) -> str:
        lines = [
            f"# {title}",
            "",
            "| ID | Source transcript | Élément candidat | Responsable | Échéance | Statut |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        if not values:
            lines.append("| - | - | À confirmer | À confirmer | À confirmer | À confirmer |")
            return "\n".join(lines).rstrip() + "\n"

        for index, value in enumerate(values, start=1):
            source, text = self._split_evidence(value)
            lines.append(
                f"| {index:03d} | {self._md_cell(source)} | {self._md_cell(text)} | À confirmer | À confirmer | À qualifier |"
            )
        return "\n".join(lines).rstrip() + "\n"

    def _build_document_impact_markdown(self, result: MeetingPostAnalysisResult) -> str:
        lines = [
            "# Document impact log",
            "",
            "| Document RHYAD candidat | Thème extrait | Traçabilité | Statut |",
            "| --- | --- | --- | --- |",
        ]
        if not result.document_impacts:
            lines.append("| À confirmer | À confirmer | À confirmer | À qualifier |")
            return "\n".join(lines).rstrip() + "\n"

        for impact in result.document_impacts:
            document, topic, count = [part.strip() for part in impact.split("|", 2)]
            lines.append(f"| {self._md_cell(document)} | {self._md_cell(topic)} | {self._md_cell(count)} | À qualifier |")
        return "\n".join(lines).rstrip() + "\n"

    def _limited_bullet_lines(self, values: list[str], limit: int = 25) -> list[str]:
        if not values:
            return ["- À confirmer."]
        visible = values[:limit]
        lines = [f"- {self._mark_uncertain_evidence(value)}" for value in visible]
        if len(values) > limit:
            lines.append(f"- ... {len(values) - limit} autre(s) extrait(s) dans le transcript nettoyé.")
        return lines

    def _mark_uncertain_evidence(self, value: str) -> str:
        if "[à vérifier]" in value:
            return value

        text = value.lower()
        uncertain_markers = (
            "...",
            "situite",
            "braille",
            "rouxerche",
            "racclaim",
            "chambrofroid",
            "endulants",
            "pigeonneral",
            "dédeceil",
            "explotation",
            "intifiers",
            "métodologie",
            "l'ilisé",
        )
        if any(marker in text for marker in uncertain_markers):
            return f"{value} [à vérifier]"
        return value

    def _cleanup_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\s+([,.;:!?])", r"\1", text)
        text = self._apply_replacements(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _apply_replacements(self, text: str) -> str:
        replacements = self._replacement_pairs()
        cleaned = text
        for alias, canonical in replacements:
            pattern = re.compile(rf"(?<!\w){re.escape(alias)}(?!\w)", flags=re.IGNORECASE)
            cleaned = pattern.sub(canonical, cleaned)
        return cleaned

    def _replacement_pairs(self) -> list[tuple[str, str]]:
        pairs: list[tuple[str, str]] = []
        corrections = self.glossary.get("corrections", {})
        pairs.extend((str(alias), str(canonical)) for alias, canonical in corrections.items() if alias != canonical)

        for term in self.glossary.get("terms", []):
            canonical = str(term.get("canonical", "")).strip()
            for alias in term.get("aliases", []):
                alias = str(alias).strip()
                if alias and canonical and self._fold(alias) != self._fold(canonical):
                    pairs.append((alias, canonical))

        return sorted(pairs, key=lambda item: len(item[0]), reverse=True)

    def _is_low_value_line(self, text: str) -> bool:
        folded = self._fold(re.sub(r"[.!?]+$", "", text).strip())
        if folded in LOW_VALUE_LINES:
            return True
        tokens = folded.split()
        return len(tokens) <= 2 and folded.replace(" ", "") in LOW_VALUE_LINES

    def _contains_any(self, text: str, keywords: Union[list[str], tuple[str, ...]]) -> bool:
        folded_text = self._fold(text)
        return any(self._fold(keyword) in folded_text for keyword in keywords)

    def _dedupe(self, values: list[str]) -> list[str]:
        seen = set()
        deduped = []
        for value in values:
            key = self._fold(value)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(value)
        return deduped

    def _split_evidence(self, value: str) -> tuple[str, str]:
        match = re.match(r"^(\[\d{2}:\d{2}:\d{2}\s+-->\s+\d{2}:\d{2}:\d{2}\])\s*(.*)$", value)
        if match:
            return match.group(1), match.group(2)
        return "-", value

    def _md_cell(self, value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ").strip()

    def _fold(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(value))
        without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
        return without_accents.casefold()

    def _load_glossary(self, glossary_path: Optional[Path]) -> dict:
        glossary = {
            "corrections": dict(DEFAULT_GLOSSARY["corrections"]),
            "terms": [dict(term) for term in DEFAULT_GLOSSARY["terms"]],
            "extraction_topics": {
                key: {
                    "title": value.get("title", key),
                    "keywords": list(value.get("keywords", [])),
                    "documents": list(value.get("documents", [])),
                }
                for key, value in DEFAULT_GLOSSARY["extraction_topics"].items()
            },
        }

        if not glossary_path or not glossary_path.exists() or yaml is None:
            return glossary

        raw = yaml.safe_load(glossary_path.read_text(encoding="utf-8")) or {}
        glossary["corrections"].update(raw.get("corrections", {}))
        glossary["terms"].extend(raw.get("terms", []))

        for key, value in raw.get("extraction_topics", {}).items():
            existing = glossary["extraction_topics"].setdefault(key, {"title": key, "keywords": [], "documents": []})
            if "title" in value:
                existing["title"] = value["title"]
            existing["keywords"].extend(value.get("keywords", []))
            existing["documents"].extend(value.get("documents", []))

        return glossary
