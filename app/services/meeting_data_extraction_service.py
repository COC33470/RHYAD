from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Optional, Union
import unicodedata

from app.modules.meetings.extracted_meeting_data import (
    ActionItem,
    DashboardData,
    DecisionItem,
    DocumentImpactItem,
    ExecutiveSummary,
    ExtractedMeetingData,
    MeetingExtractionArtifactPaths,
    MeetingExtractionResult,
    MeetingInfo,
    OpenPointItem,
    RiskItem,
    TechnicalRequirementItem,
)


TRANSCRIPT_BULLET_PATTERN = re.compile(
    r"^[-*]\s+\[(?P<start>\d{2}:\d{2}:\d{2})\s+-->\s+(?P<end>\d{2}:\d{2}:\d{2})\]\s*(?P<text>.*)$"
)
DATE_PATTERN = re.compile(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b")

TOPICS = {
    "programme_fonctionnel": {
        "label": "Programme fonctionnel",
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
        "documents": [
            ("CEVA-RHYAD-002-PF", "Compléter les rubriques du programme fonctionnel avec les besoins exprimés."),
            ("CEVA-RHYAD-100-F01..F15", "Compléter les fonctions impactées."),
            ("CEVA-RHYAD-200-F01..F15-DT01", "Préremplir les DT concernées."),
        ],
        "discipline": "Programme fonctionnel",
    },
    "site_arabie_saoudite": {
        "label": "Contraintes site Arabie Saoudite",
        "keywords": ["arabie saoudite", "ksa", "site", "climatique", "terrain", "local"],
        "documents": [
            ("CEVA-RHYAD-002-PF", "Ajouter les contraintes de site confirmées."),
            ("DB002 Architecture", "Tracer les impacts architecture."),
            ("DB003 Bâtiment", "Tracer les impacts bâtiment et site."),
        ],
        "discipline": "Site / Bâtiment",
    },
    "electricite_ups_microcoupures": {
        "label": "Alimentation électrique / UPS / microcoupures",
        "keywords": ["électricité", "ups", "onduleur", "microcoupures", "coupure", "surtension", "alimentation"],
        "documents": [
            ("CEVA-RHYAD-200-F09-DT01", "Compléter les exigences d'alimentation électrique et UPS."),
            ("DB004 Utilités", "Tracer l'impact utilités."),
            ("DB010 Sécurité", "Tracer l'impact continuité / sûreté de fonctionnement."),
        ],
        "discipline": "Électricité / Utilités",
    },
    "froid_souches_master_seeds": {
        "label": "Froid / congélateurs / souches / master seeds",
        "keywords": ["froid", "chambre froide", "congélateur", "congelateur", "souches", "master seeds", "collection"],
        "documents": [
            ("CEVA-RHYAD-100-F02", "Compléter les besoins de stockage froid."),
            ("CEVA-RHYAD-200-F02-DT01", "Préremplir les données techniques de stockage."),
            ("DB006 Production", "Tracer l'impact production."),
            ("DB007 Qualité", "Tracer l'impact qualité / conservation des souches."),
        ],
        "discipline": "Froid / Qualité / Production",
    },
    "modules_couloirs_sas_bsl2": {
        "label": "Modules / couloirs / sas / BSL2",
        "keywords": ["module", "modulaire", "couloir", "sas", "bsl2", "airlock", "pal", "mal"],
        "documents": [
            ("CEVA-RHYAD-002-PF", "Intégrer les contraintes modules / couloirs / sas."),
            ("DB001 Process", "Tracer l'impact process."),
            ("DB002 Architecture", "Tracer l'impact architecture."),
            ("DB008 Biosécurité", "Tracer l'impact biosécurité."),
        ],
        "discipline": "Process / Architecture / Biosécurité",
    },
    "flux_matieres_dechets_personnel": {
        "label": "Flux matières / déchets / personnel",
        "keywords": ["flux", "matière", "matériel", "personnel", "déchets", "effluents", "accès"],
        "documents": [
            ("CEVA-RHYAD-100-F06", "Compléter la fonction flux."),
            ("CEVA-RHYAD-100-F11", "Compléter la fonction déchets / effluents."),
            ("CEVA-RHYAD-200-F06-DT01", "Préremplir les DT flux."),
        ],
        "discipline": "Flux / Logistique / HSE",
    },
    "terrain_calendrier_appel_offres": {
        "label": "Terrain / calendrier / septembre / appel d'offres",
        "keywords": ["terrain", "calendrier", "septembre", "appel d'offres", "tender", "planning", "délai"],
        "documents": [
            ("CEVA-RHYAD-400-R05", "Mettre à jour jalons et prochaines étapes du dashboard."),
            ("CEVA-RHYAD-004-REGISTRE_DES_RISQUES", "Mettre à jour les risques planning / terrain."),
        ],
        "discipline": "Planning / Projet",
    },
    "reglementation_autorites_urs": {
        "label": "Réglementation / autorités / URS",
        "keywords": ["réglementation", "autorités", "sfda", "urs", "gmp", "bpf", "qualité"],
        "documents": [
            ("CEVA-RHYAD-002-PF", "Compléter les contraintes réglementaires et URS."),
            ("DB007 Qualité", "Tracer l'impact qualité."),
            ("DB010 Sécurité", "Tracer l'impact sécurité / conformité."),
        ],
        "discipline": "Réglementaire / Qualité",
    },
    "risques_projet": {
        "label": "Risques projet",
        "keywords": ["risque", "risques", "blocage", "bloquant", "retard", "sécuriser", "problème"],
        "documents": [
            ("CEVA-RHYAD-004-REGISTRE_DES_RISQUES", "Mettre à jour le registre des risques."),
            ("CEVA-RHYAD-400-R05", "Refléter les risques majeurs au dashboard."),
        ],
        "discipline": "Management projet",
    },
}

ACTION_KEYWORDS = (
    "il faut",
    "faut qu",
    "doit",
    "à faire",
    "a faire",
    "préparer",
    "identifier",
    "vérifier",
    "valider",
    "envoyer",
    "compléter",
    "mettre à jour",
    "appel d'offres",
)
DECISION_KEYWORDS = ("décision", "décidé", "validé", "retenu", "arbitré", "choix")
RISK_KEYWORDS = (
    "risque",
    "problème",
    "blocage",
    "bloquant",
    "retard",
    "coupure",
    "microcoupures",
    "surtension",
    "congélateur",
    "souches",
    "master seeds",
    "terrain",
    "réglementation",
)
OPEN_POINT_KEYWORDS = ("à confirmer", "à voir", "est-ce que", "?", "arbitrer", "dépend", "identifier")
CRITICAL_KEYWORDS = (
    "terrain",
    "septembre",
    "appel d'offres",
    "coupure",
    "microcoupures",
    "ups",
    "souches",
    "master seeds",
    "réglementation",
    "sfda",
    "risque",
)
KNOWN_PARTICIPANTS = (
    "Kevin",
    "Coignart",
    "Coignat",
    "Jamet",
    "Thomas",
    "Bertrand",
    "Emilio",
    "Jean",
    "Vincent",
    "Tiffany",
    "Christophe",
    "Alain",
)


@dataclass(frozen=True)
class EvidenceLine:
    start: str
    end: str
    text: str

    def source(self) -> str:
        if self.start and self.end:
            return f"[{self.start} --> {self.end}] {self.text}"
        return self.text


class MeetingDataExtractionService:
    def extract(
        self,
        transcript_cleaned_path: Path,
        output_dir: Path,
        meeting_id: str,
        meeting_summary_path: Optional[Path] = None,
        transcript_json_path: Optional[Path] = None,
    ) -> MeetingExtractionResult:
        transcript_cleaned_path = Path(transcript_cleaned_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        lines = self._read_transcript_lines(transcript_cleaned_path)
        summary_text = self._read_optional_text(meeting_summary_path)
        transcript_json = self._read_optional_json(transcript_json_path)
        topic_lines = self._extract_topic_lines(lines)

        data = self._build_extracted_data(
            meeting_id=meeting_id,
            lines=lines,
            topic_lines=topic_lines,
            summary_text=summary_text,
            transcript_json=transcript_json,
        )
        paths = MeetingExtractionArtifactPaths(
            meeting_minutes_prefill_path=output_dir / "meeting_minutes_prefill.md",
            dashboard_prefill_path=output_dir / "dashboard_prefill.md",
            action_log_path=output_dir / "action_log.md",
            decision_log_path=output_dir / "decision_log.md",
            risk_register_update_path=output_dir / "risk_register_update.md",
            document_impact_log_path=output_dir / "document_impact_log.md",
        )
        result = MeetingExtractionResult(
            meeting_id=meeting_id,
            source_transcript_path=transcript_cleaned_path,
            output_dir=output_dir,
            data=data,
            paths=paths,
        )
        self._write_outputs(result)
        return result

    def _build_extracted_data(
        self,
        meeting_id: str,
        lines: list[EvidenceLine],
        topic_lines: dict[str, list[EvidenceLine]],
        summary_text: str,
        transcript_json: dict,
    ) -> ExtractedMeetingData:
        meeting_info = self._build_meeting_info(meeting_id, lines, summary_text, transcript_json)
        decisions = self._build_decisions(lines)
        actions = self._build_actions(lines)
        risks = self._build_risks(lines)
        open_points = self._build_open_points(lines)
        document_impacts = self._build_document_impacts(topic_lines)
        technical_requirements = self._build_technical_requirements(topic_lines)
        executive_summary = self._build_executive_summary(topic_lines, risks)
        dashboard_data = self._build_dashboard_data(topic_lines, decisions, actions, risks)

        return ExtractedMeetingData(
            meeting_info=meeting_info,
            executive_summary=executive_summary,
            dashboard_data=dashboard_data,
            decisions=decisions,
            actions=actions,
            risks=risks,
            open_points=open_points,
            document_impacts=document_impacts,
            technical_requirements=technical_requirements,
        )

    def _build_meeting_info(
        self,
        meeting_id: str,
        lines: list[EvidenceLine],
        summary_text: str,
        transcript_json: dict,
    ) -> MeetingInfo:
        meeting_date = self._meeting_date(meeting_id, transcript_json)
        participants = self._identified_participants(lines, summary_text)
        project = "CEVA Riyadh Campus Project" if self._contains_any_text(lines, ["riyadh", "arabie saoudite", "ceva"]) else "CEVA-RHYAD"
        subject = self._first_available(
            [
                self._first_topic_sentence(lines, ["programme fonctionnel", "appel d'offres", "terrain", "modules"]),
                "Préremplissage compte rendu CEVA-RHYAD depuis transcription stabilisée",
            ]
        )
        context = self._first_available(
            [
                self._first_topic_sentence(lines, ["programme fonctionnel", "contraintes", "site", "arabie saoudite"]),
                "Réunion exploitée par Meeting Manager Alpha 0.3.",
            ]
        )

        return MeetingInfo(
            project=project,
            meeting_date=meeting_date,
            subject=subject,
            identified_participants=participants or ["À confirmer"],
            context=context,
        )

    def _build_executive_summary(
        self,
        topic_lines: dict[str, list[EvidenceLine]],
        risks: list[RiskItem],
    ) -> ExecutiveSummary:
        active_topics = [TOPICS[key]["label"] for key, values in topic_lines.items() if values]
        short_summary = (
            "La réunion alimente le compte rendu CEVA-RHYAD sur "
            + ", ".join(active_topics[:5])
            + "."
            if active_topics
            else "À confirmer"
        )
        major_points = []
        for key, values in topic_lines.items():
            if values:
                major_points.append(f"{TOPICS[key]['label']}: {values[0].source()}")

        alerts = [risk.risk for risk in risks if risk.criticality == "Haute"][:8]
        if not alerts and risks:
            alerts = [risks[0].risk]

        return ExecutiveSummary(
            short_summary=short_summary,
            major_points=major_points[:12],
            alerts=alerts or ["À confirmer"],
        )

    def _build_dashboard_data(
        self,
        topic_lines: dict[str, list[EvidenceLine]],
        decisions: list[DecisionItem],
        actions: list[ActionItem],
        risks: list[RiskItem],
    ) -> DashboardData:
        active_topics = [TOPICS[key]["label"] for key, values in topic_lines.items() if values]
        document_progress = []
        if topic_lines.get("programme_fonctionnel"):
            document_progress.append("Programme fonctionnel à compléter avec les fonctions et DT identifiées.")
        if topic_lines.get("reglementation_autorites_urs"):
            document_progress.append("URS / contraintes réglementaires à consolider.")
        if topic_lines.get("terrain_calendrier_appel_offres"):
            document_progress.append("Dashboard et registre risques à mettre à jour avec terrain / calendrier / appel d'offres.")

        return DashboardData(
            overall_status=(
                "Transcription exploitable pour préremplissage RHYAD; données à qualifier avant livrable client."
                if active_topics
                else "À confirmer"
            ),
            document_progress=document_progress or ["À confirmer"],
            recent_decisions=[decision.decision for decision in decisions[:5]] or ["À confirmer"],
            critical_actions=[action.action for action in actions if action.priority == "Haute"][:6] or ["À confirmer"],
            main_risks=[risk.risk for risk in risks[:6]] or ["À confirmer"],
            next_milestones=self._milestone_lines(topic_lines.get("terrain_calendrier_appel_offres", [])),
        )

    def _build_decisions(self, lines: list[EvidenceLine]) -> list[DecisionItem]:
        decisions = []
        for line in self._candidate_lines(lines, DECISION_KEYWORDS, limit=30):
            decisions.append(
                DecisionItem(
                    decision=self._clean_item_text(line.text),
                    context=line.source(),
                    owner_or_validator=self._extract_owner(line.text),
                    date=self._extract_date(line.text),
                    document_impact=self._document_impact_for_text(line.text),
                )
            )
        return decisions

    def _build_actions(self, lines: list[EvidenceLine]) -> list[ActionItem]:
        actions = []
        for line in self._candidate_lines(lines, ACTION_KEYWORDS, limit=80):
            actions.append(
                ActionItem(
                    action=self._clean_item_text(line.text),
                    owner=self._extract_owner(line.text),
                    due_date=self._extract_date(line.text),
                    priority=self._priority(line.text),
                    status="À qualifier",
                    transcription_source=line.source(),
                )
            )
        return actions

    def _build_risks(self, lines: list[EvidenceLine]) -> list[RiskItem]:
        risks = []
        for line in self._candidate_lines(lines, RISK_KEYWORDS, limit=70):
            risks.append(
                RiskItem(
                    risk=self._clean_item_text(line.text),
                    cause=self._risk_cause(line.text),
                    impact=self._risk_impact(line.text),
                    proposed_measure=self._risk_measure(line.text),
                    criticality=self._criticality(line.text),
                )
            )
        return risks

    def _build_open_points(self, lines: list[EvidenceLine]) -> list[OpenPointItem]:
        points = []
        for line in self._candidate_lines(lines, OPEN_POINT_KEYWORDS, limit=50):
            points.append(
                OpenPointItem(
                    open_point=self._clean_item_text(line.text),
                    expected_arbitration=self._expected_arbitration(line.text),
                    owner=self._extract_owner(line.text),
                    target_due_date=self._extract_date(line.text),
                )
            )
        return points

    def _build_document_impacts(self, topic_lines: dict[str, list[EvidenceLine]]) -> list[DocumentImpactItem]:
        impacts = []
        for topic_key, values in topic_lines.items():
            if not values:
                continue
            topic = TOPICS[topic_key]
            priority = "Haute" if topic_key in {"electricite_ups_microcoupures", "terrain_calendrier_appel_offres", "risques_projet"} else "Moyenne"
            source = values[0].source()
            for document, required_change in topic["documents"]:
                impacts.append(
                    DocumentImpactItem(
                        document=document,
                        required_change=required_change,
                        decision_source=source,
                        priority=priority,
                    )
                )
        return impacts

    def _build_technical_requirements(self, topic_lines: dict[str, list[EvidenceLine]]) -> list[TechnicalRequirementItem]:
        requirements = []
        for topic_key, values in topic_lines.items():
            if not values:
                continue
            topic = TOPICS[topic_key]
            for line in values[:6]:
                requirements.append(
                    TechnicalRequirementItem(
                        requirement=self._clean_item_text(line.text),
                        discipline=topic["discipline"],
                        related_constraint=topic["label"],
                        project_impact=self._document_impact_for_text(line.text),
                    )
                )
        return requirements

    def _extract_topic_lines(self, lines: list[EvidenceLine]) -> dict[str, list[EvidenceLine]]:
        topics = {}
        for topic_key, topic in TOPICS.items():
            topics[topic_key] = [
                line for line in lines if self._contains_any(line.text, topic["keywords"])
            ][:120]
        return topics

    def _candidate_lines(
        self,
        lines: list[EvidenceLine],
        keywords: tuple[str, ...],
        limit: int,
    ) -> list[EvidenceLine]:
        candidates = [line for line in lines if self._contains_any(line.text, keywords)]
        return self._dedupe_lines(candidates)[:limit]

    def _read_transcript_lines(self, path: Path) -> list[EvidenceLine]:
        lines = []
        raw_lines = path.read_text(encoding="utf-8").splitlines()
        has_transcript_section = any("Transcription nettoyée horodatée" in line for line in raw_lines)
        in_transcript_section = not has_transcript_section

        for raw_line in raw_lines:
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("|"):
                if "Transcription nettoyée horodatée" in stripped:
                    in_transcript_section = True
                continue
            if not in_transcript_section:
                continue
            match = TRANSCRIPT_BULLET_PATTERN.match(stripped)
            if match:
                text = match.group("text").strip()
                if text:
                    lines.append(EvidenceLine(match.group("start"), match.group("end"), text))
                continue
            if stripped.startswith(("- ", "* ")):
                text = stripped[2:].strip()
                if text and not self._is_metadata_line(text):
                    lines.append(EvidenceLine("", "", text))
        return lines

    def _write_outputs(self, result: MeetingExtractionResult) -> None:
        result.paths.meeting_minutes_prefill_path.write_text(self._build_minutes_prefill(result), encoding="utf-8")
        result.paths.dashboard_prefill_path.write_text(self._build_dashboard_prefill(result), encoding="utf-8")
        result.paths.action_log_path.write_text(self._build_action_log(result.data.actions), encoding="utf-8")
        result.paths.decision_log_path.write_text(self._build_decision_log(result.data.decisions), encoding="utf-8")
        result.paths.risk_register_update_path.write_text(self._build_risk_log(result.data.risks), encoding="utf-8")
        result.paths.document_impact_log_path.write_text(
            self._build_document_impact_log(result.data.document_impacts),
            encoding="utf-8",
        )

    def _build_minutes_prefill(self, result: MeetingExtractionResult) -> str:
        data = result.data
        lines = [
            f"# Compte rendu CEVA-RHYAD prérempli - {result.meeting_id}",
            "",
            "## Statut de génération",
            "",
            "- Préremplissage automatique Meeting Manager Alpha 0.3.",
            "- Source primaire: transcription nettoyée.",
            "- Les champs non établis restent à confirmer.",
            "",
            "## 1. Informations réunion",
            "",
            "| Champ CEVA-RHYAD | Valeur préremplie |",
            "| --- | --- |",
            f"| Projet | {self._md(data.meeting_info.project)} |",
            f"| Date réunion | {self._md(data.meeting_info.meeting_date)} |",
            f"| Objet | {self._md(data.meeting_info.subject)} |",
            f"| Participants identifiés | {self._md(', '.join(data.meeting_info.identified_participants) or 'À confirmer')} |",
            f"| Contexte | {self._md(data.meeting_info.context)} |",
            "",
            "## 2. Synthèse exécutive",
            "",
            f"- Synthèse courte: {data.executive_summary.short_summary}",
            "",
            "### Points majeurs",
            *self._bullet(data.executive_summary.major_points),
            "",
            "### Alertes",
            *self._bullet(data.executive_summary.alerts),
            "",
            "## 3. Sujets traités",
            "",
            *self._bullet(data.executive_summary.major_points),
            "",
            "## 4. Décisions",
            "",
            self._decision_table(data.decisions),
            "",
            "## 5. Actions",
            "",
            self._action_table(data.actions),
            "",
            "## 6. Risques",
            "",
            self._risk_table(data.risks),
            "",
            "## 7. Points ouverts",
            "",
            self._open_point_table(data.open_points),
            "",
            "## 8. Impacts documentaires",
            "",
            self._document_impact_table(data.document_impacts),
            "",
            "## 9. Exigences techniques candidates",
            "",
            self._technical_requirement_table(data.technical_requirements),
            "",
            "## 10. Prochaine étape",
            "",
            *self._bullet(data.dashboard_data.next_milestones[:3]),
        ]
        return "\n".join(lines).rstrip() + "\n"

    def _build_dashboard_prefill(self, result: MeetingExtractionResult) -> str:
        dashboard = result.data.dashboard_data
        lines = [
            "# Dashboard projet prérempli - CEVA-RHYAD-400-R05",
            "",
            "Compatible avec la première slide de contenu des présentations projet.",
            "",
            "## 1. État du projet",
            "",
            "| Indicateur | Valeur | Source |",
            "| --- | --- | --- |",
            f"| Statut général | {self._md(dashboard.overall_status)} | {self._md(str(result.source_transcript_path))} |",
            f"| Projet | {self._md(result.data.meeting_info.project)} | {self._md(str(result.source_transcript_path))} |",
            f"| Objet réunion | {self._md(result.data.meeting_info.subject)} | {self._md(result.data.meeting_info.context)} |",
            "",
            "## 2. Planning",
            "",
            "| Jalon | État | Source |",
            "| --- | --- | --- |",
            *[f"| {self._md(item)} | À qualifier | {self._md(str(result.source_transcript_path))} |" for item in dashboard.next_milestones],
            "",
            "## 3. Documents reçus / impactés",
            "",
            "| Document | Modification à faire | Priorité |",
            "| --- | --- | --- |",
            *[
                f"| {self._md(item.document)} | {self._md(item.required_change)} | {self._md(item.priority)} |"
                for item in result.data.document_impacts[:20]
            ],
            "",
            "## 4. Décisions et orientations",
            "",
            "| Décision | Impact documentaire | Responsable / valideur |",
            "| --- | --- | --- |",
            *[
                f"| {self._md(item.decision)} | {self._md(item.document_impact)} | {self._md(item.owner_or_validator)} |"
                for item in result.data.decisions[:12]
            ],
            "",
            "## 5. Risques principaux",
            "",
            "| Risque | Impact | Criticité |",
            "| --- | --- | --- |",
            *[
                f"| {self._md(item.risk)} | {self._md(item.impact)} | {self._md(item.criticality)} |"
                for item in result.data.risks[:12]
            ],
            "",
            "## 6. Prochaines étapes",
            "",
            "| Action critique | Priorité | Statut |",
            "| --- | --- | --- |",
            *[
                f"| {self._md(item.action)} | {self._md(item.priority)} | {self._md(item.status)} |"
                for item in result.data.actions[:15]
            ],
            "",
            "## 7. Alertes",
            "",
            "| Alerte | Source |",
            "| --- | --- |",
            *[
                f"| {self._md(alert)} | {self._md(str(result.source_transcript_path))} |"
                for alert in result.data.executive_summary.alerts[:12]
            ],
        ]
        return "\n".join(lines).rstrip() + "\n"

    def _build_action_log(self, actions: list[ActionItem]) -> str:
        lines = ["# Action Log", "", self._action_table(actions)]
        return "\n".join(lines).rstrip() + "\n"

    def _build_decision_log(self, decisions: list[DecisionItem]) -> str:
        lines = ["# Decision Log", "", self._decision_table(decisions)]
        return "\n".join(lines).rstrip() + "\n"

    def _build_risk_log(self, risks: list[RiskItem]) -> str:
        lines = ["# Risk Register Update", "", self._risk_table(risks)]
        return "\n".join(lines).rstrip() + "\n"

    def _build_document_impact_log(self, impacts: list[DocumentImpactItem]) -> str:
        lines = ["# Document Impact Log", "", self._document_impact_table(impacts)]
        return "\n".join(lines).rstrip() + "\n"

    def _action_table(self, actions: list[ActionItem]) -> str:
        lines = [
            "| ID | Action | Responsable | Échéance | Priorité | Statut | Source |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        if not actions:
            lines.append("| - | À confirmer | À confirmer | À confirmer | À confirmer | À confirmer | À confirmer |")
            return "\n".join(lines)
        for index, item in enumerate(actions, start=1):
            lines.append(
                f"| A-{index:03d} | {self._md(item.action)} | {self._md(item.owner)} | {self._md(item.due_date)} | "
                f"{self._md(item.priority)} | {self._md(item.status)} | {self._md(item.transcription_source)} |"
            )
        return "\n".join(lines)

    def _decision_table(self, decisions: list[DecisionItem]) -> str:
        lines = [
            "| ID | Décision | Contexte | Valideur | Date | Impact documentaire |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        if not decisions:
            lines.append("| - | À confirmer | À confirmer | À confirmer | À confirmer | À confirmer |")
            return "\n".join(lines)
        for index, item in enumerate(decisions, start=1):
            lines.append(
                f"| D-{index:03d} | {self._md(item.decision)} | {self._md(item.context)} | {self._md(item.owner_or_validator)} | "
                f"{self._md(item.date)} | {self._md(item.document_impact)} |"
            )
        return "\n".join(lines)

    def _risk_table(self, risks: list[RiskItem]) -> str:
        lines = [
            "| ID | Risque | Cause | Impact | Mesure proposée | Criticité | Statut |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        if not risks:
            lines.append("| - | À confirmer | À confirmer | À confirmer | À définir | À qualifier | À qualifier |")
            return "\n".join(lines)
        for index, item in enumerate(risks, start=1):
            lines.append(
                f"| R-{index:03d} | {self._md(item.risk)} | {self._md(item.cause)} | {self._md(item.impact)} | "
                f"{self._md(item.proposed_measure)} | {self._md(item.criticality)} | À qualifier |"
            )
        return "\n".join(lines)

    def _open_point_table(self, points: list[OpenPointItem]) -> str:
        lines = [
            "| Point ouvert | Arbitrage attendu | Responsable | Échéance cible |",
            "| --- | --- | --- | --- |",
        ]
        if not points:
            lines.append("| À confirmer | À confirmer | À confirmer | À confirmer |")
            return "\n".join(lines)
        for item in points:
            lines.append(
                f"| {self._md(item.open_point)} | {self._md(item.expected_arbitration)} | "
                f"{self._md(item.owner)} | {self._md(item.target_due_date)} |"
            )
        return "\n".join(lines)

    def _document_impact_table(self, impacts: list[DocumentImpactItem]) -> str:
        lines = [
            "| ID | Document concerné | Modification à faire | Source | Priorité | Statut |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        if not impacts:
            lines.append("| - | À confirmer | À confirmer | À confirmer | À qualifier | À qualifier |")
            return "\n".join(lines)
        for index, item in enumerate(impacts, start=1):
            lines.append(
                f"| I-{index:03d} | {self._md(item.document)} | {self._md(item.required_change)} | "
                f"{self._md(item.decision_source)} | {self._md(item.priority)} | À qualifier |"
            )
        return "\n".join(lines)

    def _technical_requirement_table(self, requirements: list[TechnicalRequirementItem]) -> str:
        lines = [
            "| Exigence | Discipline concernée | Contrainte associée | Impact projet |",
            "| --- | --- | --- | --- |",
        ]
        if not requirements:
            lines.append("| À confirmer | À confirmer | À confirmer | À qualifier |")
            return "\n".join(lines)
        for item in requirements:
            lines.append(
                f"| {self._md(item.requirement)} | {self._md(item.discipline)} | "
                f"{self._md(item.related_constraint)} | {self._md(item.project_impact)} |"
            )
        return "\n".join(lines)

    def _milestone_lines(self, lines: list[EvidenceLine]) -> list[str]:
        milestones = [
            self._clean_item_text(line.text)
            for line in lines
            if self._contains_any(line.text, ["septembre", "calendrier", "appel d'offres", "terrain"])
        ]
        return self._dedupe_text(milestones)[:8] or ["À confirmer"]

    def _identified_participants(self, lines: list[EvidenceLine], summary_text: str) -> list[str]:
        text = "\n".join([line.text for line in lines]) + "\n" + summary_text
        participants = [name for name in KNOWN_PARTICIPANTS if re.search(rf"\b{re.escape(name)}\b", text)]
        return participants

    def _meeting_date(self, meeting_id: str, transcript_json: dict) -> str:
        match = re.match(r"^(\d{4})(\d{2})(\d{2})", meeting_id)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

        created_at = str(transcript_json.get("created_at", ""))
        if re.match(r"^\d{4}-\d{2}-\d{2}", created_at):
            return created_at[:10]
        return "À confirmer"

    def _extract_owner(self, text: str) -> str:
        for name in KNOWN_PARTICIPANTS:
            if re.search(rf"\b{re.escape(name)}\b", text):
                return name
        if "responsable" in self._fold(text):
            return "Responsable à identifier"
        return "À confirmer"

    def _extract_date(self, text: str) -> str:
        if self._contains_any(text, ["septembre"]):
            return "Septembre - à confirmer"
        match = DATE_PATTERN.search(text)
        return match.group(0) if match else "À confirmer"

    def _document_impact_for_text(self, text: str) -> str:
        for topic_key, topic in TOPICS.items():
            if self._contains_any(text, topic["keywords"]):
                return ", ".join(document for document, _change in topic["documents"])
        return "À confirmer"

    def _priority(self, text: str) -> str:
        return "Haute" if self._contains_any(text, CRITICAL_KEYWORDS) else "Moyenne"

    def _criticality(self, text: str) -> str:
        if self._contains_any(text, ["coupure", "microcoupures", "souches", "master seeds", "terrain", "réglementation", "sfda"]):
            return "Haute"
        if self._contains_any(text, ["risque", "retard", "problème"]):
            return "Moyenne"
        return "À qualifier"

    def _risk_cause(self, text: str) -> str:
        if self._contains_any(text, ["coupure", "microcoupures", "surtension"]):
            return "Qualité ou continuité de l'alimentation électrique."
        if self._contains_any(text, ["souches", "master seeds", "congélateur"]):
            return "Conservation des souches / master seeds dépendante du froid."
        if self._contains_any(text, ["terrain"]):
            return "Terrain non stabilisé ou dépendant d'un arbitrage local."
        if self._contains_any(text, ["réglementation", "sfda"]):
            return "Cadre réglementaire à clarifier."
        return "À confirmer"

    def _risk_impact(self, text: str) -> str:
        if self._contains_any(text, ["coupure", "microcoupures", "surtension"]):
            return "Risque sur continuité process, contrôle et équipements critiques."
        if self._contains_any(text, ["souches", "master seeds", "congélateur"]):
            return "Risque qualité sur conservation des souches critiques."
        if self._contains_any(text, ["terrain"]):
            return "Risque planning et appel d'offres."
        if self._contains_any(text, ["réglementation", "sfda"]):
            return "Risque de reprise URS / conformité."
        return "À qualifier"

    def _risk_measure(self, text: str) -> str:
        if self._contains_any(text, ["ups", "onduleur", "microcoupures"]):
            return "Qualifier le besoin UPS / continuité électrique."
        if self._contains_any(text, ["congélateur", "froid", "souches", "master seeds"]):
            return "Définir sécurisation froid et stratégie de conservation."
        if self._contains_any(text, ["terrain", "septembre"]):
            return "Sécuriser terrain et jalons associés."
        if self._contains_any(text, ["réglementation", "sfda", "urs"]):
            return "Confirmer exigences réglementaires et URS."
        return "À définir"

    def _expected_arbitration(self, text: str) -> str:
        if self._contains_any(text, ["terrain"]):
            return "Choix / disponibilité du terrain."
        if self._contains_any(text, ["ups", "coupure", "électricité"]):
            return "Niveau de sécurisation électrique requis."
        if self._contains_any(text, ["souches", "froid", "congélateur"]):
            return "Niveau de sécurisation froid requis."
        if self._contains_any(text, ["réglementation", "sfda", "urs"]):
            return "Position réglementaire / URS."
        return "À confirmer"

    def _first_topic_sentence(self, lines: list[EvidenceLine], keywords: list[str]) -> str:
        for line in lines:
            if self._contains_any(line.text, keywords):
                return line.source()
        return ""

    def _first_available(self, values: list[str]) -> str:
        for value in values:
            if value:
                return value
        return "À confirmer"

    def _clean_item_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 240:
            return text[:237].rstrip() + "..."
        return text or "À confirmer"

    def _contains_any_text(self, lines: list[EvidenceLine], keywords: list[str]) -> bool:
        return any(self._contains_any(line.text, keywords) for line in lines)

    def _contains_any(self, text: str, keywords: Union[list[str], tuple[str, ...]]) -> bool:
        folded = self._fold(text)
        return any(self._fold(keyword) in folded for keyword in keywords)

    def _dedupe_lines(self, lines: list[EvidenceLine]) -> list[EvidenceLine]:
        seen = set()
        result = []
        for line in lines:
            key = self._fold(line.text)
            if key in seen:
                continue
            seen.add(key)
            result.append(line)
        return result

    def _dedupe_text(self, values: list[str]) -> list[str]:
        seen = set()
        result = []
        for value in values:
            key = self._fold(value)
            if key in seen:
                continue
            seen.add(key)
            result.append(value)
        return result

    def _read_optional_text(self, path: Optional[Path]) -> str:
        if not path or not Path(path).exists():
            return ""
        return Path(path).read_text(encoding="utf-8")

    def _read_optional_json(self, path: Optional[Path]) -> dict:
        if not path or not Path(path).exists():
            return {}
        try:
            return json.loads(Path(path).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _is_metadata_line(self, text: str) -> bool:
        return self._fold(text).startswith(
            (
                "transcript source:",
                "dictionnaire metier:",
                "nettoyage:",
                "limite:",
            )
        )

    def _bullet(self, values: list[str]) -> list[str]:
        if not values:
            return ["- À confirmer"]
        return [f"- {value}" for value in values]

    def _md(self, value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ").strip()

    def _fold(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(value))
        without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
        return without_accents.casefold()
