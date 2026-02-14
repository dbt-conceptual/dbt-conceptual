"""Parser for conceptual.yml and dbt schema files.

v1.0: Simplified parser with flat model lists and no lineage inference.
"""

from pathlib import Path
from typing import Literal, Optional

import yaml

from dbt_conceptual.config import Config
from dbt_conceptual.scanner import DbtProjectScanner
from dbt_conceptual.state import (
    ConceptState,
    DomainState,
    Guidance,
    GuidanceRule,
    Message,
    MessageSeverity,
    ModelInfo,
    OrphanModel,
    ProjectState,
    RelationshipState,
    ValidationState,
    ValidationStatus,
)

# Element types that can appear in validation messages
ElementType = Literal["concept", "relationship", "domain"]


class ConceptualModelParser:
    """Parses conceptual.yml file."""

    def __init__(self, config: Config):
        """Initialize the parser.

        Args:
            config: Configuration object
        """
        self.config = config

    def parse(self) -> ProjectState:
        """Parse the conceptual model file and build initial state.

        Returns:
            ProjectState with concepts, relationships, and domains

        Raises:
            ValueError: If relationships section is malformed (not a list,
                entries missing required 'from'/'to' keys, or entries are
                not mappings).
        """
        state = ProjectState()

        conceptual_file = self.config.conceptual_file
        if not conceptual_file.exists():
            return state

        with open(conceptual_file) as f:
            data = yaml.safe_load(f)

        if not data:
            return state

        # Parse metadata
        if "metadata" in data:
            state.metadata = data["metadata"]

        # Parse domains
        if "domains" in data:
            for domain_id, domain_data in data["domains"].items():
                state.domains[domain_id] = DomainState(
                    name=domain_id,
                    display_name=domain_data.get(
                        "display_name", domain_data.get("name", domain_id)
                    ),
                    color=domain_data.get("color"),
                    owner=domain_data.get("owner"),
                )

        # Parse concepts
        if "concepts" in data:
            for concept_id, concept_data in data["concepts"].items():
                # Parse guidance block if present
                guidance = None
                if "guidance" in concept_data:
                    guidance_data = concept_data["guidance"]
                    rules = []
                    if "rules" in guidance_data:
                        for rule_data in guidance_data["rules"]:
                            rules.append(
                                GuidanceRule(
                                    name=rule_data["name"],
                                    description=rule_data["description"],
                                )
                            )
                    guidance = Guidance(
                        context=guidance_data.get("context"),
                        rules=rules,
                    )

                state.concepts[concept_id] = ConceptState(
                    name=concept_data.get("name", concept_id),
                    domain=concept_data.get("domain"),
                    owner=concept_data.get("owner"),
                    definition=concept_data.get("definition"),
                    color=concept_data.get("color"),
                    guidance=guidance,
                    # models list populated by StateBuilder, not from YAML
                )

        # Parse relationships
        if "relationships" in data:
            relationships = data["relationships"]
            if not isinstance(relationships, list):
                raise ValueError(
                    "Invalid conceptual.yml: 'relationships' must be a list, "
                    f"got {type(relationships).__name__}. "
                    "Expected format: relationships:\\n  - from: x\\n    to: y"
                )
            for i, rel in enumerate(relationships):
                if not isinstance(rel, dict):
                    raise ValueError(
                        f"Invalid conceptual.yml: relationship at index {i} "
                        f"must be a mapping, got {type(rel).__name__}"
                    )
                from_concept = rel.get("from")
                to_concept = rel.get("to")
                if not from_concept:
                    raise ValueError(
                        f"Invalid conceptual.yml: relationship at index {i} "
                        "is missing required key 'from'. "
                        "Each relationship must have 'from' and 'to' keys."
                    )
                if not to_concept:
                    raise ValueError(
                        f"Invalid conceptual.yml: relationship at index {i} "
                        "is missing required key 'to'. "
                        "Each relationship must have 'from' and 'to' keys."
                    )

                verb = rel.get("verb", "relates_to")

                # Create relationship ID using verb
                rel_id = f"{from_concept}:{verb}:{to_concept}"

                # Default cardinality to 1:N if not specified
                cardinality = rel.get("cardinality", "1:N")
                # Validate cardinality - only 1:1 and 1:N allowed
                if cardinality not in ("1:1", "1:N"):
                    cardinality = "1:N"

                state.relationships[rel_id] = RelationshipState(
                    verb=verb,
                    from_concept=from_concept,
                    to_concept=to_concept,
                    cardinality=cardinality,
                    definition=rel.get("definition"),
                    owner=rel.get("owner"),
                )

        return state

    def _parse_conceptual_yml(self, conceptual_file: Path) -> ProjectState:
        """Parse a conceptual.yml file and return basic state (for git.py).

        This is a simplified version of parse() that only loads the YAML structure
        without scanning dbt models.

        Args:
            conceptual_file: Path to conceptual.yml file

        Returns:
            ProjectState with domains, concepts, and relationships
        """
        # Temporarily swap config file path
        try:
            # Override conceptual_file path
            self.config._conceptual_file_override = conceptual_file  # type: ignore[attr-defined]
            return self.parse()
        finally:
            # Restore original path
            if hasattr(self.config, "_conceptual_file_override"):
                delattr(self.config, "_conceptual_file_override")


class StateBuilder:
    """Builds complete ProjectState by combining conceptual model and dbt models."""

    def __init__(self, config: Config):
        """Initialize the state builder.

        Args:
            config: Configuration object
        """
        self.config = config
        self.parser = ConceptualModelParser(config)
        self.scanner = DbtProjectScanner(config)
        self._msg_counter = 0

    def build(self) -> ProjectState:
        """Build complete project state from conceptual model and dbt models.

        Returns:
            Complete ProjectState with all linkages
        """
        # Start with conceptual model
        state = self.parser.parse()

        # Scan dbt models (gold layer only)
        models = self.scanner.scan()

        # Process each model
        for model in models:
            meta = model.get("meta", {})
            model_name = model["name"]

            # Handle concept linkage via meta.concept
            if "concept" in meta:
                concept_id = meta["concept"]
                if concept_id in state.concepts:
                    concept = state.concepts[concept_id]
                    if model_name not in concept.models:
                        concept.models.append(model_name)
                # else: validation will catch unknown concept references

            # Track orphan models (models without concept tag)
            if "concept" not in meta:
                orphan = OrphanModel(
                    name=model_name,
                    description=model.get("description"),
                    domain=meta.get("domain"),
                    path=model.get("path"),
                )
                state.orphan_models.append(orphan)

            # Build ModelInfo for validation
            tags = model.get("tags", [])
            databricks_tags = model.get("databricks_tags", {})

            # Extract domain and owner tags
            domain_tags = []
            owner_tag = None

            # Standard format: tags like "domain:party", "owner:team"
            for tag in tags:
                if isinstance(tag, str):
                    if tag.startswith("domain:"):
                        domain_tags.append(tag[7:])  # Strip "domain:" prefix
                    elif tag.startswith("owner:"):
                        owner_tag = tag[6:]  # Strip "owner:" prefix

            # Databricks format: databricks_tags dict
            if databricks_tags:
                if "domain" in databricks_tags:
                    domain_val = databricks_tags["domain"]
                    if isinstance(domain_val, list):
                        domain_tags.extend(domain_val)
                    elif domain_val:
                        domain_tags.append(str(domain_val))
                if "owner" in databricks_tags:
                    owner_tag = str(databricks_tags["owner"])

            state.models[model_name] = ModelInfo(
                name=model_name,
                concept=meta.get("concept"),
                domain_tags=domain_tags,
                owner_tag=owner_tag,
                path=model.get("path"),
            )

        return state

    def _parse_conceptual_yml(self, conceptual_file: Path) -> ProjectState:
        """Parse a conceptual.yml file and return basic state (for git.py).

        This delegates to ConceptualModelParser's method.

        Args:
            conceptual_file: Path to conceptual.yml file

        Returns:
            ProjectState with domains, concepts, and relationships
        """
        return self.parser._parse_conceptual_yml(conceptual_file)

    def _make_msg(
        self,
        severity: MessageSeverity,
        text: str,
        element_type: Optional[ElementType] = None,
        element_id: Optional[str] = None,
    ) -> Message:
        """Create a validation message with auto-incrementing ID.

        Args:
            severity: Message severity level (error, warning, info)
            text: Human-readable message text
            element_type: Type of element this message relates to
            element_id: ID of the element this message relates to

        Returns:
            A new Message instance
        """
        self._msg_counter += 1
        return Message(
            id=f"msg-{self._msg_counter}",
            severity=severity,
            text=text,
            element_type=element_type,
            element_id=element_id,
        )

    def _check_ghost_concepts(self, state: ProjectState) -> list[Message]:
        """Check relationships for missing concepts and create ghosts.

        For each relationship, if the 'from' or 'to' concept does not exist
        in state.concepts, a ghost ConceptState is created and error/warning
        messages are generated.

        Args:
            state: The current project state (modified in place)

        Returns:
            List of validation messages generated
        """
        messages: list[Message] = []

        for rel_id, rel in state.relationships.items():
            from_missing = rel.from_concept not in state.concepts
            to_missing = rel.to_concept not in state.concepts

            if from_missing:
                ghost = ConceptState(
                    name=rel.from_concept,
                    domain=None,
                    is_ghost=True,
                    validation_status=ValidationStatus.ERROR,
                    validation_messages=["Referenced but not defined"],
                )
                state.concepts[rel.from_concept] = ghost
                messages.append(
                    self._make_msg(
                        "error",
                        f"Relationship '{rel_id}' references non-existent "
                        f"concept '{rel.from_concept}'",
                        "relationship",
                        rel_id,
                    )
                )
                messages.append(
                    self._make_msg(
                        "warning",
                        f"Ghost created for concept '{rel.from_concept}'",
                        "concept",
                        rel.from_concept,
                    )
                )
                rel.validation_status = ValidationStatus.ERROR
                rel.validation_messages.append(
                    f"Source concept '{rel.from_concept}' not defined"
                )

            if to_missing:
                ghost = ConceptState(
                    name=rel.to_concept,
                    domain=None,
                    is_ghost=True,
                    validation_status=ValidationStatus.ERROR,
                    validation_messages=["Referenced but not defined"],
                )
                state.concepts[rel.to_concept] = ghost
                messages.append(
                    self._make_msg(
                        "error",
                        f"Relationship '{rel_id}' references non-existent "
                        f"concept '{rel.to_concept}'",
                        "relationship",
                        rel_id,
                    )
                )
                messages.append(
                    self._make_msg(
                        "warning",
                        f"Ghost created for concept '{rel.to_concept}'",
                        "concept",
                        rel.to_concept,
                    )
                )
                rel.validation_status = ValidationStatus.ERROR
                rel.validation_messages.append(
                    f"Target concept '{rel.to_concept}' not defined"
                )

        return messages

    def _check_duplicate_concepts(self, state: ProjectState) -> list[Message]:
        """Check for duplicate concept names.

        Scans all non-ghost concepts and flags any that share the same
        display name.

        Args:
            state: The current project state (modified in place)

        Returns:
            List of validation messages generated
        """
        messages: list[Message] = []
        names_seen: dict[str, str] = {}  # name -> first concept_id

        for concept_id, concept in state.concepts.items():
            if concept.is_ghost:
                continue  # Skip ghosts for duplicate check
            if concept.name in names_seen:
                first_id = names_seen[concept.name]
                messages.append(
                    self._make_msg(
                        "error",
                        f"Duplicate concept name '{concept.name}'",
                        "concept",
                        concept_id,
                    )
                )
                concept.validation_status = ValidationStatus.ERROR
                concept.validation_messages.append(f"Duplicate name: {concept.name}")
                # Also mark the first one
                if first_id in state.concepts:
                    state.concepts[first_id].validation_status = ValidationStatus.ERROR
                    state.concepts[first_id].validation_messages.append(
                        f"Duplicate name: {concept.name}"
                    )
            else:
                names_seen[concept.name] = concept_id

        return messages

    def _check_duplicate_relationships(self, state: ProjectState) -> list[Message]:
        """Check for duplicate relationships.

        Two relationships are considered duplicates if they have the same
        from_concept, verb, and to_concept.

        Args:
            state: The current project state (modified in place)

        Returns:
            List of validation messages generated
        """
        messages: list[Message] = []
        rel_keys_seen: dict[str, str] = {}  # key -> first rel_id

        for rel_id, rel in state.relationships.items():
            key = f"{rel.from_concept}:{rel.verb}:{rel.to_concept}"
            if key in rel_keys_seen and rel_keys_seen[key] != rel_id:
                messages.append(
                    self._make_msg(
                        "error",
                        f"Duplicate relationship '{rel_id}'",
                        "relationship",
                        rel_id,
                    )
                )
                rel.validation_status = ValidationStatus.ERROR
                rel.validation_messages.append("Duplicate relationship")
            else:
                rel_keys_seen[key] = rel_id

        return messages

    def _check_empty_domains(self, state: ProjectState) -> list[Message]:
        """Check for domains with no concepts assigned.

        Args:
            state: The current project state (read only)

        Returns:
            List of validation messages generated
        """
        messages: list[Message] = []
        domain_concept_counts: dict[str, int] = dict.fromkeys(state.domains, 0)

        for concept in state.concepts.values():
            if concept.domain and not concept.is_ghost:
                if concept.domain in domain_concept_counts:
                    domain_concept_counts[concept.domain] += 1

        for domain_id, count in domain_concept_counts.items():
            if count == 0:
                messages.append(
                    self._make_msg(
                        "warning",
                        f"Domain '{domain_id}' has no concepts",
                        "domain",
                        domain_id,
                    )
                )

        return messages

    def _make_sync_summary(self, state: ProjectState) -> list[Message]:
        """Generate sync summary info message.

        Args:
            state: The current project state (read only)

        Returns:
            List containing the sync info message
        """
        real_concepts = [c for c in state.concepts.values() if not c.is_ghost]
        return [
            self._make_msg(
                "info",
                f"Synced {len(real_concepts)} concepts from conceptual.yml",
            )
        ]

    def validate_and_sync(self, state: ProjectState) -> ValidationState:
        """Run validation checks and create ghost concepts for missing references.

        This method:
        1. Creates ghost concepts for relationships referencing non-existent concepts
        2. Checks for duplicate concept names
        3. Checks for duplicate relationships
        4. Checks for empty domains
        5. Generates sync summary

        Args:
            state: The current project state (will be modified in place)

        Returns:
            ValidationState with all messages and counts
        """
        self._msg_counter = 0
        messages: list[Message] = []

        # 1. Check relationships for missing concepts and create ghosts
        messages.extend(self._check_ghost_concepts(state))

        # 2. Check for duplicate concept names
        messages.extend(self._check_duplicate_concepts(state))

        # 3. Check for duplicate relationships
        messages.extend(self._check_duplicate_relationships(state))

        # 4. Check for empty domains
        messages.extend(self._check_empty_domains(state))

        # 5. Add sync info message
        messages.extend(self._make_sync_summary(state))

        # Count by severity
        error_count = sum(1 for m in messages if m.severity == "error")
        warning_count = sum(1 for m in messages if m.severity == "warning")
        info_count = sum(1 for m in messages if m.severity == "info")

        return ValidationState(
            messages=messages,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
        )
