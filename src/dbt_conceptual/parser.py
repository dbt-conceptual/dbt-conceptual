"""Parser for conceptual.yml and dbt schema files."""

import yaml

from dbt_conceptual.config import Config
from dbt_conceptual.scanner import DbtProjectScanner
from dbt_conceptual.state import (
    ConceptState,
    DomainState,
    ProjectState,
    RelationshipState,
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
                    display_name=domain_data.get("name", domain_id),
                    color=domain_data.get("color"),
                )

        # Parse concepts
        if "concepts" in data:
            for concept_id, concept_data in data["concepts"].items():
                state.concepts[concept_id] = ConceptState(
                    name=concept_data.get("name", concept_id),
                    domain=concept_data.get("domain"),
                    owner=concept_data.get("owner"),
                    definition=concept_data.get("definition"),
                    status=concept_data.get("status", "stub"),
                    replaced_by=concept_data.get("replaced_by"),
                    discovered_from=concept_data.get("discovered_from"),
                )

        # Parse relationships
        if "relationships" in data:
            for rel in data["relationships"]:
                rel_name = rel["name"]
                from_concept = rel["from"]
                to_concept = rel["to"]

                # Create relationship ID
                rel_id = f"{from_concept}:{rel_name}:{to_concept}"

                state.relationships[rel_id] = RelationshipState(
                    name=rel_name,
                    from_concept=from_concept,
                    to_concept=to_concept,
                    cardinality=rel.get("cardinality"),
                    status=rel.get("status", "complete"),
                )

        # Parse relationship groups
        if "relationship_groups" in data:
            for group_name, rel_list in data["relationship_groups"].items():
                state.groups[group_name] = rel_list

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

    def _expand_realizes(self, realizes: list[str], state: ProjectState) -> list[str]:
        """Expand realizes list handling groups and exclusions.

        Args:
            realizes: List of relationship IDs, group names, or exclusions
            state: Current project state

        Returns:
            Expanded list of relationship IDs
        """
        expanded = []
        exclusions = set()

        for item in realizes:
            # Handle exclusions (minus prefix)
            if item.startswith("-"):
                exclusions.add(item[1:])
                continue

            # Check if it's a group reference
            if item in state.groups:
                expanded.extend(state.groups[item])
            else:
                expanded.append(item)

        # Remove exclusions
        return [rel for rel in expanded if rel not in exclusions]

    def build(self) -> ProjectState:
        """Build complete project state from conceptual model and dbt models.

        Returns:
            Complete ProjectState with all linkages
        """
        # Start with conceptual model
        state = self.parser.parse()

        # Scan dbt models
        models = self.scanner.scan()

        # Process each model
        for model in models:
            meta = model.get("meta", {})
            model_name = model["name"]
            layer = model["layer"]

            # Handle concept linkage
            if "concept" in meta:
                concept_id = meta["concept"]
                if concept_id in state.concepts:
                    concept = state.concepts[concept_id]
                    if layer == "silver":
                        concept.silver_models.append(model_name)
                    elif layer == "gold":
                        concept.gold_models.append(model_name)
                # else: validation will catch this

            # Handle relationship realization
            if "realizes" in meta:
                realizes_list = meta["realizes"]
                if not isinstance(realizes_list, list):
                    realizes_list = [realizes_list]

                # Expand groups and exclusions
                expanded = self._expand_realizes(realizes_list, state)

                # Add to realized_by for each relationship
                for rel_id in expanded:
                    if rel_id in state.relationships:
                        state.relationships[rel_id].realized_by.append(model_name)
                    # else: validation will catch this

            # Track orphan models (models without concept or realizes)
            if "concept" not in meta and "realizes" not in meta:
                if layer in ("silver", "gold"):  # Only track layered models as orphans
                    state.orphan_models.append(model_name)

        return state
