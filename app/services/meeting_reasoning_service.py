from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Optional
import unicodedata

from app.modules.meetings.meeting_reasoning import (
    LOW_CONFIDENCE_VALIDATION_NOTE,
    ActionItem,
    DashboardReasoningData,
    Decision,
    DiscussionTopic,
    DocumentImpact,
    MeetingContext,
    MeetingReasoningArtifactPaths,
    MeetingReasoningModel,
    MeetingReasoningResult,
    Milestone,
    OpenPoint,
    Requirement,
    Risk,
)


TRANSCRIPT_BULLET_PATTERN = re.compile(
    r"^[-*]\s+\[(?P<start>\d{2}:\d{2}:\d{2})\s+-->\s+(?P<end>\d{2}:\d{2}:\d{2})\]\s*(?P<text>.*)$"
)

KNOWN_PARTICIPANTS = (
    "Kevin",
    "Coignart",
    "Coignat",
    "Thomas",
    "Bertrand",
    "Jean",
    "Vincent",
    "Tiffany",
    "Christophe",
    "Alain",
    "Emilio",
)


@dataclass(frozen=True)
class TranscriptEvidence:
    start: str
    end: str
    text: str

    def source_ref(self) -> str:
        if self.start and self.end:
            return f"[{self.start} --> {self.end}]"
        return "transcript_cleaned.md"


@dataclass(frozen=True)
class TopicProfile:
    id: str
    subject: str
    keywords: tuple[str, ...]
    context: str
    problem_statement: str
    decisions: tuple[str, ...]
    actions: tuple[str, ...]
    risks: tuple[dict[str, str], ...]
    requirements: tuple[dict[str, str], ...]
    document_impacts: tuple[tuple[str, str, str], ...]
    open_points: tuple[str, ...] = ()
    milestones: tuple[tuple[str, str], ...] = ()
    persons: tuple[str, ...] = ()
    high_confidence_keywords: tuple[str, ...] = ()
    high_priority: bool = False


TOPIC_PROFILES = (
    TopicProfile(
        id="programme_fonctionnel",
        subject="Structuration du programme fonctionnel RHYAD",
        keywords=(
            "programme fonctionnel",
            "fonction",
            "sous-function",
            "réception",
            "expédition",
            "stockage",
            "maintenance",
            "déchets",
            "effluents",
        ),
        context=(
            "La réunion confirme que le programme fonctionnel doit organiser les besoins par fonctions métier, "
            "puis alimenter les contraintes de conception et les DT."
        ),
        problem_statement=(
            "Le référentiel doit éviter les informations dispersées entre fonctions, DT et documents de réunion."
        ),
        decisions=(
            "Le programme fonctionnel doit rester la structure de référence pour organiser les besoins métier F01 à F15.",
        ),
        actions=(
            "Consolider le programme fonctionnel par fonctions F01 à F15 afin de relier chaque besoin aux DT correspondantes.",
            "Identifier les informations manquantes par fonction avant de les transmettre aux bureaux d'études.",
        ),
        risks=(
            {
                "risk": "Les besoins fonctionnels peuvent rester incomplets ou dispersés entre plusieurs documents.",
                "cause": "Les fonctions métier et les DT ne sont pas encore totalement alimentées par des données confirmées.",
                "impact": "Risque d'incohérence de programmation et de reprise documentaire en phase études.",
                "probability": "Moyenne",
                "gravity": "Moyenne",
                "criticality": "Modérée",
                "owner": "AMO RHYAD",
                "action_plan": "Mettre à jour les fonctions et DT uniquement avec les informations source validées.",
            },
        ),
        requirements=(
            {
                "requirement": "Chaque fonction du programme doit disposer de ses contraintes, interfaces et données d'entrée traçables.",
                "discipline": "Programmation fonctionnelle",
                "constraint": "Une information = une seule source.",
                "impact": "Base de préparation des DT et des Design Basis.",
            },
        ),
        document_impacts=(
            ("CEVA-RHYAD-002-PF", "Compléter les rubriques fonctionnelles avec les besoins confirmés.", "Haute"),
            ("CEVA-RHYAD-100-F01..F15", "Compléter les fonctions impactées sans dupliquer les DT.", "Haute"),
            ("CEVA-RHYAD-200-F01..F15-DT01", "Préremplir les données techniques disponibles et marquer le reste À confirmer.", "Haute"),
        ),
        open_points=("Confirmer les données manquantes par fonction avant intégration définitive dans les DT.",),
        high_confidence_keywords=("programme fonctionnel", "fonction"),
    ),
    TopicProfile(
        id="site_ksa",
        subject="Contraintes du site en Arabie Saoudite",
        keywords=("arabie saoudite", "ksa", "site", "climatique", "terrain", "local", "construction local"),
        context=(
            "La réunion aborde l'adaptation du projet au contexte local saoudien, incluant climat, réseau électrique, "
            "terrain et construction locale."
        ),
        problem_statement=(
            "Les contraintes site ne sont pas entièrement stabilisées et conditionnent architecture, bâtiment, utilités et planning."
        ),
        decisions=(
            "Les contraintes de site en Arabie Saoudite doivent être consolidées avant le gel des choix d'implantation.",
        ),
        actions=(
            "Consolider l'analyse de contexte Arabie Saoudite afin d'identifier les contraintes climatiques, réglementaires et d'accès au site.",
            "Vérifier les contraintes locales de raccordement, d'autorisation et de construction avant l'appel d'offres constructeur.",
        ),
        risks=(
            {
                "risk": "Les contraintes locales du site peuvent remettre en cause les hypothèses de conception.",
                "cause": "Terrain et conditions locales encore à confirmer.",
                "impact": "Risque de reprise des choix bâtiment, architecture et utilités.",
                "probability": "Moyenne",
                "gravity": "Élevée",
                "criticality": "Élevée",
                "owner": "AMO RHYAD / CEVA",
                "action_plan": "Formaliser les contraintes site dans le programme et les futures Design Basis.",
            },
        ),
        requirements=(
            {
                "requirement": "La conception doit intégrer les contraintes climatiques et réglementaires de l'Arabie Saoudite.",
                "discipline": "Site / Bâtiment",
                "constraint": "Contexte local non entièrement confirmé.",
                "impact": "Conditionne implantation, enveloppe bâtiment, utilités et planning.",
            },
        ),
        document_impacts=(
            ("CEVA-RHYAD-002-PF", "Ajouter les contraintes de site confirmées.", "Haute"),
            ("DB002 Architecture", "Tracer les impacts architecture.", "Moyenne"),
            ("DB003 Bâtiment", "Tracer les impacts bâtiment et site.", "Haute"),
        ),
        open_points=("Confirmer les contraintes définitives du terrain et du contexte local.",),
        high_confidence_keywords=("arabie saoudite", "terrain"),
        high_priority=True,
    ),
    TopicProfile(
        id="electricite_ups",
        subject="Continuité électrique et protection UPS",
        keywords=("électricité", "electricite", "ups", "onduleur", "microcoupures", "coupure", "alimentation"),
        context=(
            "La réunion évoque la stabilité du réseau électrique, les microcoupures et la protection des équipements critiques."
        ),
        problem_statement=(
            "La stratégie de continuité électrique doit être clarifiée pour éviter un impact sur contrôle, froid et process."
        ),
        decisions=(
            "La stratégie UPS et continuité électrique doit être arbitrée avant le gel des DT utilités et des principes de sûreté de fonctionnement.",
        ),
        actions=(
            "Identifier le fournisseur d'électricité local afin de confirmer les contraintes d'alimentation électrique du site.",
            "Qualifier le besoin UPS pour les fonctions critiques, notamment contrôle, congélateurs, automatisme et équipements process.",
            "Définir les scénarios de microcoupures et les durées admissibles par famille d'équipements.",
        ),
        risks=(
            {
                "risk": "Les microcoupures peuvent perturber les équipements critiques et les systèmes de contrôle.",
                "cause": "Qualité d'alimentation électrique locale à confirmer.",
                "impact": "Risque de perte de continuité process, défaut qualité ou arrêt d'équipements critiques.",
                "probability": "Moyenne",
                "gravity": "Élevée",
                "criticality": "Élevée",
                "owner": "Électricité / Utilités",
                "action_plan": "Réaliser une analyse de continuité électrique et dimensionner les protections UPS nécessaires.",
            },
        ),
        requirements=(
            {
                "requirement": "Les équipements critiques doivent être protégés contre les microcoupures selon leur criticité process et qualité.",
                "discipline": "Électricité / Utilités",
                "constraint": "Qualité d'alimentation locale à confirmer.",
                "impact": "Alimente les DT F09, DB004 Utilités et DB010 Sécurité.",
            },
        ),
        document_impacts=(
            ("CEVA-RHYAD-200-F09-DT01", "Compléter les exigences d'alimentation électrique et UPS.", "Haute"),
            ("DB004 Utilités", "Tracer l'impact utilités.", "Haute"),
            ("DB010 Sécurité", "Tracer l'impact continuité / sûreté de fonctionnement.", "Haute"),
            ("CEVA-RHYAD-400-R05", "Suivre l'arbitrage UPS dans le dashboard.", "Haute"),
        ),
        open_points=("Confirmer la qualité du réseau et les exigences UPS par équipement critique.",),
        high_confidence_keywords=("ups", "microcoupures", "coupure"),
        high_priority=True,
    ),
    TopicProfile(
        id="froid_souches",
        subject="Conservation des souches et master seeds",
        keywords=("froid", "chambre froide", "congélateur", "congelateur", "souches", "master seeds", "collection"),
        context=(
            "La réunion aborde les souches, les master seeds et les besoins de conservation sous froid."
        ),
        problem_statement=(
            "La conservation des souches doit être sécurisée avant de dimensionner stockage, froid et continuité électrique."
        ),
        decisions=(
            "Le choix des master seeds devra être validé avant le lancement des études détaillées.",
        ),
        actions=(
            "Définir la stratégie de conservation des souches et master seeds, incluant température, redondance et surveillance.",
            "Identifier les volumes et familles de souches à stocker afin de dimensionner congélateurs et stockage froid.",
        ),
        risks=(
            {
                "risk": "Une perte de froid peut compromettre la conservation des souches et master seeds.",
                "cause": "Besoins de conservation et autonomie froid encore à confirmer.",
                "impact": "Risque qualité majeur et risque de perte de matière biologique critique.",
                "probability": "Moyenne",
                "gravity": "Élevée",
                "criticality": "Élevée",
                "owner": "Qualité / Production",
                "action_plan": "Définir les exigences froid, alarme, redondance et secours électrique pour les stockages critiques.",
            },
        ),
        requirements=(
            {
                "requirement": "Les souches et master seeds doivent disposer d'une conservation maîtrisée, surveillée et secourue.",
                "discipline": "Froid / Qualité / Production",
                "constraint": "Paramètres de stockage et volumes à confirmer.",
                "impact": "Dimensionnement stockage froid, utilités, qualité et continuité électrique.",
            },
        ),
        document_impacts=(
            ("CEVA-RHYAD-100-F02", "Compléter les besoins de stockage froid.", "Haute"),
            ("CEVA-RHYAD-200-F02-DT01", "Préremplir les données techniques de stockage froid.", "Haute"),
            ("DB006 Production", "Tracer l'impact production.", "Moyenne"),
            ("DB007 Qualité", "Tracer l'impact qualité / conservation des souches.", "Haute"),
        ),
        open_points=("Confirmer température, volumes, redondance et règles qualité applicables aux souches.",),
        high_confidence_keywords=("souches", "master seeds", "congélateur"),
        high_priority=True,
    ),
    TopicProfile(
        id="modules_flux_bsl2",
        subject="Architecture modulaire, sas et flux BSL2",
        keywords=("module", "modulaire", "couloir", "sas", "bsl2", "airlock", "flux", "personnel", "déchets"),
        context=(
            "La réunion traite l'intégration des modules, des sas, des couloirs et des flux matières, déchets et personnel."
        ),
        problem_statement=(
            "L'organisation modulaire doit démontrer la séparation des flux et la maîtrise des interfaces process, architecture et biosécurité."
        ),
        decisions=(
            "L'organisation des sas, couloirs et flux doit être validée comme donnée d'entrée du programme et des Design Basis.",
        ),
        actions=(
            "Cartographier les flux matières, personnel, déchets et équipements pour vérifier les croisements et interfaces entre modules.",
            "Clarifier si les sas et couloirs critiques sont intégrés dans les modules ou traités comme ouvrages séparés.",
        ),
        risks=(
            {
                "risk": "Une mauvaise organisation des flux peut créer des croisements incompatibles avec les exigences biosécurité et GMP.",
                "cause": "Interfaces modules, sas et couloirs encore à clarifier.",
                "impact": "Risque de reprise layout, surface et principes de confinement.",
                "probability": "Moyenne",
                "gravity": "Élevée",
                "criticality": "Élevée",
                "owner": "Process / Architecture / Biosécurité",
                "action_plan": "Produire une cartographie des flux et une matrice d'interfaces module par module.",
            },
        ),
        requirements=(
            {
                "requirement": "Les flux matières, personnel et déchets doivent être séparés et compatibles avec les exigences BSL2/GMP.",
                "discipline": "Process / Architecture / Biosécurité",
                "constraint": "Interfaces modules et sas à confirmer.",
                "impact": "Conditionne layout, surfaces, portes, sas et circulations.",
            },
        ),
        document_impacts=(
            ("CEVA-RHYAD-002-PF", "Intégrer les contraintes modules, couloirs et sas.", "Haute"),
            ("CEVA-RHYAD-100-F06", "Compléter la fonction gestion des flux.", "Haute"),
            ("CEVA-RHYAD-100-F11", "Compléter la fonction déchets / effluents.", "Moyenne"),
            ("DB001 Process", "Tracer l'impact process.", "Haute"),
            ("DB002 Architecture", "Tracer l'impact architecture.", "Haute"),
            ("DB008 Biosécurité", "Tracer l'impact biosécurité.", "Haute"),
        ),
        open_points=("Arbitrer l'intégration des sas et couloirs dans les modules ou dans la construction locale.",),
        high_confidence_keywords=("module", "flux", "sas"),
        high_priority=True,
    ),
    TopicProfile(
        id="terrain_planning_tender",
        subject="Terrain, planning et appel d'offres",
        keywords=("terrain", "calendrier", "septembre", "appel d'offres", "tender", "planning", "permis"),
        context=(
            "La réunion indique que le terrain et le calendrier conditionnent la préparation de l'appel d'offres."
        ),
        problem_statement=(
            "Le terrain n'est pas totalement sécurisé, ce qui peut retarder le dossier technique et l'appel d'offres constructeur."
        ),
        decisions=(
            "Le choix du terrain doit être stabilisé avant de figer les données techniques transmises pour l'appel d'offres constructeur.",
        ),
        actions=(
            "Obtenir la confirmation du terrain cible afin de sécuriser les hypothèses de surface, accès, raccordements et permis.",
            "Préparer le dossier technique d'appel d'offres en distinguant les données confirmées et les hypothèses dépendantes du terrain.",
        ),
        risks=(
            {
                "risk": "L'absence de terrain confirmé peut bloquer le planning et retarder l'appel d'offres.",
                "cause": "Choix du terrain et données locales encore à confirmer.",
                "impact": "Risque de décalage du calendrier études, consultation et construction.",
                "probability": "Élevée",
                "gravity": "Élevée",
                "criticality": "Critique",
                "owner": "CEVA / AMO RHYAD",
                "action_plan": "Mettre le terrain en point bloquant du dashboard et suivre une échéance de confirmation.",
            },
        ),
        requirements=(
            {
                "requirement": "Les données terrain doivent être confirmées avant le gel des hypothèses de conception locale.",
                "discipline": "Planning / Bâtiment",
                "constraint": "Terrain et permis à confirmer.",
                "impact": "Conditionne appel d'offres, surfaces, raccordements et planning.",
            },
        ),
        document_impacts=(
            ("CEVA-RHYAD-400-R05", "Mettre à jour les jalons terrain et appel d'offres.", "Haute"),
            ("CEVA-RHYAD-004-REGISTRE_DES_RISQUES", "Mettre à jour les risques planning / terrain.", "Haute"),
            ("DB003 Bâtiment", "Tracer les hypothèses dépendantes du terrain.", "Haute"),
        ),
        open_points=("Confirmer le terrain, son calendrier de disponibilité et les impacts permis.",),
        milestones=(
            ("Confirmer le terrain cible et les contraintes associées.", "Septembre - à confirmer"),
            ("Préparer le dossier technique d'appel d'offres constructeur.", "Après confirmation terrain"),
        ),
        high_confidence_keywords=("terrain", "septembre", "appel d'offres"),
        high_priority=True,
    ),
    TopicProfile(
        id="reglementation_urs",
        subject="Réglementation, autorités et URS",
        keywords=("réglementation", "reglementation", "autorités", "sfda", "urs", "gmp", "bpf", "qualité"),
        context=(
            "La réunion fait apparaître un besoin de clarification réglementaire et de cohérence avec l'URS."
        ),
        problem_statement=(
            "Les exigences réglementaires applicables aux autovaccins doivent être clarifiées avant la consolidation des livrables techniques."
        ),
        decisions=(
            "La position réglementaire et les exigences URS doivent être confirmées avant d'engager les choix détaillés qualité et biosécurité.",
        ),
        actions=(
            "Organiser une clarification réglementaire avec les autorités ou référents CEVA afin de confirmer les exigences applicables aux autovaccins.",
            "Aligner l'URS, le programme fonctionnel et les DT sur le niveau GMP réellement applicable.",
        ),
        risks=(
            {
                "risk": "Une interprétation réglementaire incomplète peut imposer une reprise du programme ou du layout.",
                "cause": "Niveau GMP et attentes autorités encore à confirmer.",
                "impact": "Risque de non-conformité, reprise URS et décalage planning.",
                "probability": "Moyenne",
                "gravity": "Élevée",
                "criticality": "Élevée",
                "owner": "Qualité / Réglementaire",
                "action_plan": "Tracer les points réglementaires ouverts et obtenir validation CEVA avant gel documentaire.",
            },
        ),
        requirements=(
            {
                "requirement": "Le programme et les DT doivent intégrer uniquement des exigences réglementaires confirmées.",
                "discipline": "Qualité / Réglementaire",
                "constraint": "Validation autorités / CEVA à obtenir.",
                "impact": "Conditionne qualité, biosécurité, process et documents d'appel d'offres.",
            },
        ),
        document_impacts=(
            ("CEVA-RHYAD-002-PF", "Compléter les contraintes réglementaires et URS confirmées.", "Haute"),
            ("DB007 Qualité", "Tracer l'impact qualité.", "Haute"),
            ("DB008 Biosécurité", "Tracer l'impact biosécurité.", "Haute"),
            ("CEVA-RHYAD-004-REGISTRE_DES_RISQUES", "Suivre le risque de clarification réglementaire.", "Haute"),
        ),
        open_points=("Confirmer les exigences autorités, SFDA le cas échéant, et le niveau GMP applicable.",),
        high_confidence_keywords=("réglementation", "urs", "gmp"),
        high_priority=True,
    ),
)


class MeetingReasoningService:
    def reason(
        self,
        transcript_cleaned_path: Path,
        output_dir: Path,
        meeting_id: str,
        meeting_summary_path: Optional[Path] = None,
    ) -> MeetingReasoningResult:
        transcript_cleaned_path = Path(transcript_cleaned_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        evidence = self._read_transcript(transcript_cleaned_path)
        summary_text = self._read_optional_text(meeting_summary_path)
        model = self._build_model(meeting_id, evidence, summary_text)
        paths = MeetingReasoningArtifactPaths(
            meeting_minutes_prefill_path=output_dir / "meeting_minutes_prefill.md",
            dashboard_prefill_path=output_dir / "dashboard_prefill.md",
            action_log_path=output_dir / "action_log.md",
            decision_log_path=output_dir / "decision_log.md",
            risk_register_update_path=output_dir / "risk_register_update.md",
            document_impact_log_path=output_dir / "document_impact_log.md",
            meeting_knowledge_graph_path=output_dir / "meeting_knowledge_graph.json",
        )
        result = MeetingReasoningResult(
            meeting_id=meeting_id,
            source_transcript_path=transcript_cleaned_path,
            source_summary_path=Path(meeting_summary_path) if meeting_summary_path else None,
            output_dir=output_dir,
            data=model,
            paths=paths,
        )
        self._write_outputs(result)
        return result

    def _build_model(
        self,
        meeting_id: str,
        evidence: list[TranscriptEvidence],
        summary_text: str,
    ) -> MeetingReasoningModel:
        topics = []
        counters = {
            "decision": 1,
            "action": 1,
            "risk": 1,
            "requirement": 1,
            "document": 1,
            "open_point": 1,
            "milestone": 1,
        }
        for profile in TOPIC_PROFILES:
            matched = self._matching_evidence(profile, evidence, summary_text)
            if not matched:
                continue
            confidence = self._confidence(profile, matched, summary_text)
            validation_note = self._validation_note(confidence)
            topic = self._build_topic(profile, matched, confidence, validation_note, counters)
            topics.append(topic)

        context = self._build_context(meeting_id, evidence, summary_text, topics)
        decisions = [item for topic in topics for item in topic.decisions]
        actions = [item for topic in topics for item in topic.actions]
        risks = [item for topic in topics for item in topic.risks]
        requirements = [item for topic in topics for item in topic.requirements]
        document_impacts = [item for topic in topics for item in topic.document_impacts]
        open_points = [item for topic in topics for item in topic.open_points]
        milestones = [item for topic in topics for item in topic.milestones]
        dashboard = self._build_dashboard(topics, decisions, actions, risks, document_impacts, milestones)

        return MeetingReasoningModel(
            context=context,
            topics=topics,
            decisions=decisions,
            actions=actions,
            risks=risks,
            requirements=requirements,
            document_impacts=document_impacts,
            open_points=open_points,
            milestones=milestones,
            dashboard=dashboard,
        )

    def _build_topic(
        self,
        profile: TopicProfile,
        matched: list[TranscriptEvidence],
        confidence: str,
        validation_note: str,
        counters: dict[str, int],
    ) -> DiscussionTopic:
        decisions = [
            Decision(
                id=self._next_id("D", counters, "decision"),
                decision=text,
                context=profile.subject,
                document_impact=[doc for doc, _, _ in profile.document_impacts],
                confidence=confidence,
                validation_note=validation_note,
            )
            for text in profile.decisions
        ]
        actions = [
            ActionItem(
                id=self._next_id("A", counters, "action"),
                action=text,
                priority="Haute" if profile.high_priority else "Moyenne",
                source_topic=profile.subject,
                confidence=confidence,
                validation_note=validation_note,
            )
            for text in profile.actions
        ]
        risks = [
            Risk(
                id=self._next_id("R", counters, "risk"),
                risk=item["risk"],
                cause=item["cause"],
                impact=item["impact"],
                probability=item["probability"],
                gravity=item["gravity"],
                criticality=item["criticality"],
                owner=item["owner"],
                action_plan=item["action_plan"],
                source_topic=profile.subject,
                confidence=confidence,
                validation_note=validation_note,
            )
            for item in profile.risks
        ]
        requirements = [
            Requirement(
                id=self._next_id("REQ", counters, "requirement"),
                requirement=item["requirement"],
                discipline=item["discipline"],
                constraint=item["constraint"],
                project_impact=item["impact"],
                source_topic=profile.subject,
                confidence=confidence,
                validation_note=validation_note,
            )
            for item in profile.requirements
        ]
        document_impacts = [
            DocumentImpact(
                id=self._next_id("I", counters, "document"),
                document=document,
                required_change=required_change,
                source_topic=profile.subject,
                priority=priority,
                confidence=confidence,
                validation_note=validation_note,
            )
            for document, required_change, priority in profile.document_impacts
        ]
        open_points = [
            OpenPoint(
                id=self._next_id("OP", counters, "open_point"),
                open_point=text,
                expected_arbitration="Arbitrage ou confirmation CEVA requis.",
                source_topic=profile.subject,
                confidence=confidence,
                validation_note=validation_note,
            )
            for text in profile.open_points
        ]
        milestones = [
            Milestone(
                id=self._next_id("M", counters, "milestone"),
                milestone=text,
                target_date=target,
                source_topic=profile.subject,
                confidence=confidence,
                validation_note=validation_note,
            )
            for text, target in profile.milestones
        ]
        return DiscussionTopic(
            id=profile.id,
            subject=profile.subject,
            context=profile.context,
            problem_statement=profile.problem_statement,
            decisions=decisions,
            actions=actions,
            risks=risks,
            requirements=requirements,
            document_impacts=document_impacts,
            open_points=open_points,
            milestones=milestones,
            persons=list(profile.persons),
            evidence_refs=[item.source_ref() for item in matched[:5]],
            confidence=confidence,
            validation_note=validation_note,
        )

    def _build_context(
        self,
        meeting_id: str,
        evidence: list[TranscriptEvidence],
        summary_text: str,
        topics: list[DiscussionTopic],
    ) -> MeetingContext:
        participants = self._identified_participants(evidence, summary_text)
        if any(topic.id == "terrain_planning_tender" for topic in topics):
            subject = "Réunion de cadrage terrain, programme, modules et appel d'offres"
        elif topics:
            subject = "Réunion de cadrage programme et données techniques"
        else:
            subject = "Réunion RHYAD à qualifier"
        confidence = "medium" if topics else "low"
        return MeetingContext(
            meeting_date=self._meeting_date(meeting_id),
            subject=subject,
            participants=participants or ["À confirmer"],
            confidence=confidence,
            validation_note=self._validation_note(confidence),
        )

    def _build_dashboard(
        self,
        topics: list[DiscussionTopic],
        decisions: list[Decision],
        actions: list[ActionItem],
        risks: list[Risk],
        document_impacts: list[DocumentImpact],
        milestones: list[Milestone],
    ) -> DashboardReasoningData:
        blocking = [
            risk.risk
            for risk in risks
            if risk.criticality in {"Élevée", "Critique"}
            and any(word in self._normalize(risk.risk) for word in ("terrain", "microcoupure", "réglementaire", "froid"))
        ]
        critical_actions = [action.action for action in actions if action.priority == "Haute"]
        critical_risks = [f"{risk.risk} ({risk.criticality})" for risk in risks if risk.criticality in {"Élevée", "Critique"}]
        documents_to_update = self._dedupe([item.document for item in document_impacts])
        documents_to_produce = self._documents_to_produce(topics)
        planning = [item.milestone for item in milestones]
        next_deadlines = [
            f"{item.milestone} - {item.target_date}"
            for item in milestones
        ]
        return DashboardReasoningData(
            overall_status=(
                "Projet exploitable pour préremplissage RHYAD, avec arbitrages critiques à sécuriser sur terrain, "
                "continuité électrique, froid critique, modules/flux et réglementation."
                if topics
                else "Réunion à qualifier par le chef de projet."
            ),
            blocking_points=blocking or ["Aucun point bloquant confirmé automatiquement ; validation chef de projet requise."],
            major_decisions=[item.decision for item in decisions[:8]] or ["À confirmer"],
            critical_actions=critical_actions[:10] or [item.action for item in actions[:5]] or ["À confirmer"],
            critical_risks=critical_risks[:10] or ["À confirmer"],
            planning=planning or ["À confirmer"],
            next_deadlines=next_deadlines or ["À confirmer"],
            documents_to_produce=documents_to_produce,
            documents_to_update=documents_to_update or ["À confirmer"],
        )

    def _write_outputs(self, result: MeetingReasoningResult) -> None:
        result.paths.meeting_minutes_prefill_path.write_text(self._build_minutes(result), encoding="utf-8")
        result.paths.dashboard_prefill_path.write_text(self._build_dashboard_markdown(result), encoding="utf-8")
        result.paths.action_log_path.write_text(self._build_action_log(result.data.actions), encoding="utf-8")
        result.paths.decision_log_path.write_text(self._build_decision_log(result.data.decisions), encoding="utf-8")
        result.paths.risk_register_update_path.write_text(self._build_risk_log(result.data.risks), encoding="utf-8")
        result.paths.document_impact_log_path.write_text(self._build_document_impact_log(result.data.document_impacts), encoding="utf-8")
        result.paths.meeting_knowledge_graph_path.write_text(
            json.dumps(self._build_knowledge_graph(result.data), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _build_minutes(self, result: MeetingReasoningResult) -> str:
        data = result.data
        lines = [
            f"# Compte rendu CEVA-RHYAD prérempli - {result.meeting_id}",
            "",
            "## Statut de génération",
            "",
            "- Préremplissage automatique Meeting Manager Alpha 0.4.",
            "- Méthode : raisonnement métier AMO / ingénierie à partir de la transcription nettoyée et du résumé disponible.",
            "- Les formulations sont reformulées pour usage projet ; les données faibles sont marquées pour validation chef de projet.",
            "",
            "## 1. Informations réunion",
            "",
            "| Champ CEVA-RHYAD | Valeur préremplie | Confiance |",
            "| --- | --- | --- |",
            f"| Projet | {self._md(data.context.project)} | {data.context.confidence} |",
            f"| Date réunion | {self._md(data.context.meeting_date)} | {data.context.confidence} |",
            f"| Objet | {self._md(data.context.subject)} | {data.context.confidence} |",
            f"| Participants identifiés | {self._md(', '.join(data.context.participants))} | {data.context.confidence} |",
            "",
            "## 2. Synthèse exécutive",
            "",
            data.dashboard.overall_status,
            "",
            "## 3. Sujets traités",
            "",
            self._topic_table(data.topics),
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
            "## 9. Exigences techniques",
            "",
            self._requirement_table(data.requirements),
            "",
            "## 10. Prochaines étapes",
            "",
            *self._bullet(data.dashboard.critical_actions[:8]),
        ]
        return "\n".join(lines).rstrip() + "\n"

    def _build_dashboard_markdown(self, result: MeetingReasoningResult) -> str:
        dashboard = result.data.dashboard
        lines = [
            "# Dashboard projet prérempli - CEVA-RHYAD-400-R05",
            "",
            "Compatible avec la première slide de contenu après page de titre.",
            "",
            "## Etat général",
            "",
            dashboard.overall_status,
            "",
            "## Points bloquants",
            "",
            *self._bullet(dashboard.blocking_points),
            "",
            "## Décisions majeures",
            "",
            *self._bullet(dashboard.major_decisions),
            "",
            "## Actions critiques",
            "",
            *self._bullet(dashboard.critical_actions),
            "",
            "## Risques critiques",
            "",
            *self._bullet(dashboard.critical_risks),
            "",
            "## Planning",
            "",
            *self._bullet(dashboard.planning),
            "",
            "## Prochaines échéances",
            "",
            *self._bullet(dashboard.next_deadlines),
            "",
            "## Documents à produire",
            "",
            *self._bullet(dashboard.documents_to_produce),
            "",
            "## Documents à mettre à jour",
            "",
            *self._bullet(dashboard.documents_to_update),
        ]
        return "\n".join(lines).rstrip() + "\n"

    def _build_action_log(self, actions: list[ActionItem]) -> str:
        return "\n".join(["# Action Log", "", self._action_table(actions)]).rstrip() + "\n"

    def _build_decision_log(self, decisions: list[Decision]) -> str:
        return "\n".join(["# Decision Log", "", self._decision_table(decisions)]).rstrip() + "\n"

    def _build_risk_log(self, risks: list[Risk]) -> str:
        return "\n".join(["# Risk Register Update", "", self._risk_table(risks)]).rstrip() + "\n"

    def _build_document_impact_log(self, impacts: list[DocumentImpact]) -> str:
        return "\n".join(["# Document Impact Log", "", self._document_impact_table(impacts)]).rstrip() + "\n"

    def _topic_table(self, topics: list[DiscussionTopic]) -> str:
        lines = [
            "| ID | Sujet | Contexte | Problématique | Confiance | Validation |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for topic in topics:
            lines.append(
                f"| {topic.id} | {self._md(topic.subject)} | {self._md(topic.context)} | "
                f"{self._md(topic.problem_statement)} | {topic.confidence} | {self._md(topic.validation_note)} |"
            )
        return "\n".join(lines)

    def _action_table(self, actions: list[ActionItem]) -> str:
        lines = [
            "| ID | Action | Responsable | Échéance | Priorité | Statut | Sujet source | Confiance | Validation |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for item in actions:
            lines.append(
                f"| {item.id} | {self._md(item.action)} | {self._md(item.owner)} | {self._md(item.due_date)} | "
                f"{self._md(item.priority)} | {self._md(item.status)} | {self._md(item.source_topic)} | "
                f"{item.confidence} | {self._md(item.validation_note)} |"
            )
        return "\n".join(lines)

    def _decision_table(self, decisions: list[Decision]) -> str:
        lines = [
            "| ID | Décision | Contexte | Valideur | Date | Impact documentaire | Confiance | Validation |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for item in decisions:
            lines.append(
                f"| {item.id} | {self._md(item.decision)} | {self._md(item.context)} | "
                f"{self._md(item.owner_or_validator)} | {self._md(item.date)} | "
                f"{self._md(', '.join(item.document_impact) or 'À confirmer')} | {item.confidence} | "
                f"{self._md(item.validation_note)} |"
            )
        return "\n".join(lines)

    def _risk_table(self, risks: list[Risk]) -> str:
        lines = [
            "| ID | Risque | Cause | Impact | Probabilité | Gravité | Criticité | Responsable | Plan d'action | Confiance | Statut |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for item in risks:
            status = item.validation_note or "À qualifier"
            lines.append(
                f"| {item.id} | {self._md(item.risk)} | {self._md(item.cause)} | {self._md(item.impact)} | "
                f"{self._md(item.probability)} | {self._md(item.gravity)} | {self._md(item.criticality)} | "
                f"{self._md(item.owner)} | {self._md(item.action_plan)} | {item.confidence} | {self._md(status)} |"
            )
        return "\n".join(lines)

    def _document_impact_table(self, impacts: list[DocumentImpact]) -> str:
        lines = [
            "| ID | Document concerné | Modification à faire | Source métier | Priorité | Confiance | Statut |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for item in impacts:
            status = item.validation_note or "À qualifier"
            lines.append(
                f"| {item.id} | {self._md(item.document)} | {self._md(item.required_change)} | "
                f"{self._md(item.source_topic)} | {self._md(item.priority)} | {item.confidence} | {self._md(status)} |"
            )
        return "\n".join(lines)

    def _open_point_table(self, points: list[OpenPoint]) -> str:
        lines = [
            "| ID | Point ouvert | Arbitrage attendu | Responsable | Échéance cible | Confiance | Validation |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for item in points:
            lines.append(
                f"| {item.id} | {self._md(item.open_point)} | {self._md(item.expected_arbitration)} | "
                f"{self._md(item.owner)} | {self._md(item.target_due_date)} | {item.confidence} | "
                f"{self._md(item.validation_note)} |"
            )
        return "\n".join(lines)

    def _requirement_table(self, requirements: list[Requirement]) -> str:
        lines = [
            "| ID | Exigence | Discipline concernée | Contrainte associée | Impact projet | Confiance | Validation |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for item in requirements:
            lines.append(
                f"| {item.id} | {self._md(item.requirement)} | {self._md(item.discipline)} | "
                f"{self._md(item.constraint)} | {self._md(item.project_impact)} | {item.confidence} | "
                f"{self._md(item.validation_note)} |"
            )
        return "\n".join(lines)

    def _build_knowledge_graph(self, model: MeetingReasoningModel) -> dict:
        nodes = []
        edges = []

        def add_node(node_id: str, node_type: str, label: str, confidence: str = "medium") -> None:
            nodes.append({"id": node_id, "type": node_type, "label": label, "confidence": confidence})

        def add_edge(source: str, target: str, relation: str) -> None:
            edges.append({"source": source, "target": target, "relation": relation})

        add_node("meeting:current", "MeetingContext", model.context.subject, model.context.confidence)
        for topic in model.topics:
            topic_node = f"topic:{topic.id}"
            add_node(topic_node, "Sujet", topic.subject, topic.confidence)
            add_edge("meeting:current", topic_node, "covers")
            for decision in topic.decisions:
                node_id = f"decision:{decision.id}"
                add_node(node_id, "Decision", decision.decision, decision.confidence)
                add_edge(topic_node, node_id, "decision")
            for action in topic.actions:
                node_id = f"action:{action.id}"
                add_node(node_id, "Action", action.action, action.confidence)
                add_edge(topic_node, node_id, "action")
            for risk in topic.risks:
                node_id = f"risk:{risk.id}"
                add_node(node_id, "Risk", risk.risk, risk.confidence)
                add_edge(topic_node, node_id, "risk")
            for requirement in topic.requirements:
                node_id = f"requirement:{requirement.id}"
                add_node(node_id, "Requirement", requirement.requirement, requirement.confidence)
                add_edge(topic_node, node_id, "requirement")
            for impact in topic.document_impacts:
                node_id = f"document:{impact.document}"
                add_node(node_id, "Document", impact.document, impact.confidence)
                add_edge(topic_node, node_id, "document")
            for person in topic.persons:
                node_id = f"person:{person}"
                add_node(node_id, "Person", person, topic.confidence)
                add_edge(topic_node, node_id, "person")

        return {
            "meeting": model.context.to_dict() if hasattr(model.context, "to_dict") else model.context.__dict__,
            "topics": [
                {
                    "id": topic.id,
                    "subject": topic.subject,
                    "decisions": [item.id for item in topic.decisions],
                    "actions": [item.id for item in topic.actions],
                    "risks": [item.id for item in topic.risks],
                    "documents": [item.document for item in topic.document_impacts],
                    "requirements": [item.id for item in topic.requirements],
                    "persons": topic.persons,
                    "confidence": topic.confidence,
                }
                for topic in model.topics
            ],
            "nodes": self._unique_nodes(nodes),
            "edges": edges,
        }

    def _matching_evidence(
        self,
        profile: TopicProfile,
        evidence: list[TranscriptEvidence],
        summary_text: str,
    ) -> list[TranscriptEvidence]:
        matched = [item for item in evidence if self._contains_any(item.text, profile.keywords)]
        if matched:
            return matched[:30]
        if self._contains_any(summary_text, profile.keywords):
            return [TranscriptEvidence("", "", profile.context)]
        return []

    def _confidence(
        self,
        profile: TopicProfile,
        evidence: list[TranscriptEvidence],
        summary_text: str,
    ) -> str:
        high_signal = sum(1 for item in evidence if self._contains_any(item.text, profile.high_confidence_keywords))
        uncertain = sum(1 for item in evidence if "[à vérifier]" in item.text.lower())
        if len(evidence) >= 4 and high_signal >= 2 and uncertain <= len(evidence) / 2:
            return "high"
        if len(evidence) >= 2 or self._contains_any(summary_text, profile.keywords):
            return "medium"
        return "low"

    def _validation_note(self, confidence: str) -> str:
        return LOW_CONFIDENCE_VALIDATION_NOTE if confidence == "low" else ""

    def _read_transcript(self, path: Path) -> list[TranscriptEvidence]:
        evidence = []
        raw_lines = path.read_text(encoding="utf-8").splitlines()
        has_transcript_section = any("Transcription nettoyée horodatée" in line for line in raw_lines)
        in_transcript_section = not has_transcript_section
        for raw_line in raw_lines:
            stripped = raw_line.strip()
            if "Transcription nettoyée horodatée" in stripped:
                in_transcript_section = True
                continue
            if not in_transcript_section or not stripped or stripped.startswith("#") or stripped.startswith("|"):
                continue
            match = TRANSCRIPT_BULLET_PATTERN.match(stripped)
            if match:
                text = match.group("text").strip()
                if text:
                    evidence.append(TranscriptEvidence(match.group("start"), match.group("end"), text))
                continue
            if stripped.startswith(("- ", "* ")):
                text = stripped[2:].strip()
                if text and not text.startswith(("Transcript source:", "Dictionnaire métier:", "Nettoyage:", "Limite:")):
                    evidence.append(TranscriptEvidence("", "", text))
        return evidence

    def _read_optional_text(self, path: Optional[Path]) -> str:
        if not path:
            return ""
        path = Path(path)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def _identified_participants(self, evidence: list[TranscriptEvidence], summary_text: str) -> list[str]:
        haystack = " ".join([summary_text, *(item.text for item in evidence)])
        found = []
        for participant in KNOWN_PARTICIPANTS:
            if re.search(rf"\b{re.escape(participant)}\b", haystack, flags=re.IGNORECASE):
                found.append(participant)
        return self._dedupe(found)

    def _meeting_date(self, meeting_id: str) -> str:
        match = re.search(r"(20\d{2})(\d{2})(\d{2})", meeting_id)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        return "À confirmer"

    def _documents_to_produce(self, topics: list[DiscussionTopic]) -> list[str]:
        docs = []
        if any(topic.id in {"site_ksa", "terrain_planning_tender"} for topic in topics):
            docs.append("Note de synthèse terrain / contraintes site pour arbitrage CEVA.")
        if any(topic.id == "electricite_ups" for topic in topics):
            docs.append("Analyse de continuité électrique et stratégie UPS.")
        if any(topic.id == "modules_flux_bsl2" for topic in topics):
            docs.append("Matrice des flux et interfaces modules / sas / couloirs.")
        if any(topic.id == "reglementation_urs" for topic in topics):
            docs.append("Registre des points réglementaires à confirmer.")
        return docs or ["À confirmer"]

    def _next_id(self, prefix: str, counters: dict[str, int], key: str) -> str:
        value = counters[key]
        counters[key] += 1
        return f"{prefix}-{value:03d}"

    def _bullet(self, items: list[str]) -> list[str]:
        return [f"- {item}" for item in items] if items else ["- À confirmer"]

    def _md(self, value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ").strip()

    def _contains_any(self, value: str, needles: tuple[str, ...]) -> bool:
        normalized = self._normalize(value)
        return any(self._normalize(needle) in normalized for needle in needles)

    def _normalize(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(value))
        without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
        return without_accents.casefold()

    def _dedupe(self, items: list[str]) -> list[str]:
        seen = set()
        result = []
        for item in items:
            key = self._normalize(item)
            if key and key not in seen:
                result.append(item)
                seen.add(key)
        return result

    def _unique_nodes(self, nodes: list[dict]) -> list[dict]:
        seen = set()
        unique = []
        for node in nodes:
            if node["id"] in seen:
                continue
            seen.add(node["id"])
            unique.append(node)
        return unique
