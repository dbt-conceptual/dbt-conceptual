"""Parser for conceptual.yml and dbt schema files.

v1.0: Simplified parser with flat model lists and no lineage inference.
"""

from typing import Optional

import yaml

from dbt_conceptual.config import Config
from dbt_conceptual.scanner import DbtProjectScanner
from dbt_conceptual.state import (
    ConceptState,
    DomainState,
    Message,
    ModelInfo,
    OrphanModel,
    ProjectState,
    RelationshipState,
    ValidationState,
)


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
                state.concepts[concept_id] = ConceptState(
                    name=concept_data.get("name", concept_id),
                    domain=concept_data.get("domain"),
                    owner=concept_data.get("owner"),
                    definition=concept_data.get("definition"),
                    color=concept_data.get("color"),
                    # models list populated by StateBuilder, not from YAML
                )

        # Parse relationships
        if "relationships" in data:
            for rel in data["relationships"]:
                verb = rel.get("verb", "relates_to")
                from_concept = rel["from"]
                to_concept = rel["to"]

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

    def validate_and_sync(self, state: ProjectState) -> ValidationState:
        """Run validation checks and create ghost concepts for missing references.

        This method:
        1. Creates ghost concepts for relationships referencing non-existent concepts
        2. Checks for duplicate concept names
        3. Checks for duplicate relationships
        4. Generates appropriate messages

        Args:
            state: The current project state (will be modified in place)

        Returns:
            ValidationState with all messages and counts
        """
        messages: list[Message] = []
        msg_counter = 0

        def make_msg(
            severity: str,
            text: str,
            element_type: Optional[str] = None,
            element_id: Optional[str] = None,
        ) -> Message:
            nonlocal msg_counter
            msg_counter += 1
            return Message(
                id=f"msg-{msg_counter}",
                severity=severity,  # type: ignore[arg-type]
                text=text,
                element_type=element_type,  # type: ignore[arg-type]
                element_id=element_id,
            )

        # 1. Check relationships for missing concepts and create ghosts
        for rel_id, rel in state.relationships.items():
            from_missing = rel.from_concept not in state.concepts
            to_missing = rel.to_concept not in state.concepts

            if from_missing:
                # Create ghost concept
                ghost = ConceptState(
                    name=rel.from_concept,
                    domain=None,
                    is_ghost=True,
                    validation_status="error",
                    validation_messages=["Referenced but not defined"],
                )
                state.concepts[rel.from_concept] = ghost
                messages.append(
                    make_msg(
                        "error",
                        f"Relationship '{rel_id}' references non-existent "
                        f"concept '{rel.from_concept}'",
                        "relationship",
                        rel_id,
                    )
                )
                messages.append(
                    make_msg(
                        "warning",
                        f"Ghost created for concept '{rel.from_concept}'",
                        "concept",
                        rel.from_concept,
                    )
                )
                rel.validation_status = "error"
                rel.validation_messages.append(
                    f"Source concept '{rel.from_concept}' not defined"
                )

            if to_missing:
                # Create ghost concept
                ghost = ConceptState(
                    name=rel.to_concept,
                    domain=None,
                    is_ghost=True,
                    validation_status="error",
                    validation_messages=["Referenced but not defined"],
                )
                state.concepts[rel.to_concept] = ghost
                messages.append(
                    make_msg(
                        "error",
                        f"Relationship '{rel_id}' references non-existent "
                        f"concept '{rel.to_concept}'",
                        "relationship",
                        rel_id,
                    )
                )
                messages.append(
                    make_msg(
                        "warning",
                        f"Ghost created for concept '{rel.to_concept}'",
                        "concept",
                        rel.to_concept,
                    )
                )
                rel.validation_status = "error"
                rel.validation_messages.append(
                    f"Target concept '{rel.to_concept}' not defined"
                )

        # 2. Check for duplicate concept names
        names_seen: dict[str, str] = {}  # name -> first concept_id
        for concept_id, concept in state.concepts.items():
            if concept.is_ghost:
                continue  # Skip ghosts for duplicate check
            if concept.name in names_seen:
                first_id = names_seen[concept.name]
                messages.append(
                    make_msg(
                        "error",
                        f"Duplicate concept name '{concept.name}'",
                        "concept",
                        concept_id,
                    )
                )
                concept.validation_status = "error"
                concept.validation_messages.append(f"Duplicate name: {concept.name}")
                # Also mark the first one
                if first_id in state.concepts:
                    state.concepts[first_id].validation_status = "error"
                    state.concepts[first_id].validation_messages.append(
                        f"Duplicate name: {concept.name}"
                    )
            else:
                names_seen[concept.name] = concept_id

        # 3. Check for duplicate relationships
        rel_keys_seen: dict[str, str] = {}  # key -> first rel_id
        for rel_id, rel in state.relationships.items():
            key = f"{rel.from_concept}:{rel.verb}:{rel.to_concept}"
            if key in rel_keys_seen and rel_keys_seen[key] != rel_id:
                messages.append(
                    make_msg(
                        "error",
                        f"Duplicate relationship '{rel_id}'",
                        "relationship",
                        rel_id,
                    )
                )
                rel.validation_status = "error"
                rel.validation_messages.append("Duplicate relationship")
            else:
                rel_keys_seen[key] = rel_id

        # 4. Check for empty domains
        domain_concept_counts: dict[str, int] = dict.fromkeys(state.domains, 0)
        for concept in state.concepts.values():
            if concept.domain and not concept.is_ghost:
                if concept.domain in domain_concept_counts:
                    domain_concept_counts[concept.domain] += 1
        for domain_id, count in domain_concept_counts.items():
            if count == 0:
                messages.append(
                    make_msg(
                        "warning",
                        f"Domain '{domain_id}' has no concepts",
                        "domain",
                        domain_id,
                    )
                )

        # 5. Add sync info message
        real_concepts = [c for c in state.concepts.values() if not c.is_ghost]
        messages.append(
            make_msg(
                "info",
                f"Synced {len(real_concepts)} concepts from conceptual.yml",
            )
        )

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
