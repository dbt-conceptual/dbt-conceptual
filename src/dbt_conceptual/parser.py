"""Parser for conceptual.yml and dbt schema files."""

import yaml

from dbt_conceptual.config import Config
from dbt_conceptual.scanner import DbtProjectScanner
from dbt_conceptual.state import (
    ConceptState,
    DomainState,
    OrphanModel,
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
                    color=concept_data.get("color"),
                    replaced_by=concept_data.get("replaced_by"),
                    # Note: status, bronze_models, silver_models, gold_models are now derived
                    # and populated by StateBuilder, not read from YAML
                )

        # Parse relationships
        if "relationships" in data:
            for rel in data["relationships"]:
                verb = rel.get(
                    "verb", rel.get("name", "relates_to")
                )  # Support both new and old format
                from_concept = rel["from"]
                to_concept = rel["to"]

                # Create relationship ID using verb
                rel_id = f"{from_concept}:{verb}:{to_concept}"

                # Parse domains (handle both array and legacy single domain)
                domains_raw = rel.get("domains", rel.get("domain"))
                if isinstance(domains_raw, str):
                    domains = [domains_raw] if domains_raw else []
                elif isinstance(domains_raw, list):
                    domains = domains_raw
                else:
                    domains = []

                state.relationships[rel_id] = RelationshipState(
                    verb=verb,
                    from_concept=from_concept,
                    to_concept=to_concept,
                    cardinality=rel.get("cardinality"),
                    definition=rel.get("definition"),
                    domains=domains,
                    owner=rel.get("owner"),
                    custom_name=rel.get("custom_name"),
                    # Note: status and realized_by are now derived
                    # and populated by StateBuilder, not read from YAML
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
                    if layer == "silver" and model_name not in concept.silver_models:
                        concept.silver_models.append(model_name)
                    elif layer == "gold" and model_name not in concept.gold_models:
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
                        if model_name not in state.relationships[rel_id].realized_by:
                            state.relationships[rel_id].realized_by.append(model_name)
                    # else: validation will catch this

            # Track orphan models (models without concept or realizes)
            if "concept" not in meta and "realizes" not in meta:
                if layer in ("silver", "gold"):  # Only track layered models as orphans
                    orphan = OrphanModel(
                        name=model_name,
                        description=model.get("description"),
                        domain=meta.get("domain"),
                        layer=layer,
                        path=model.get("path"),
                    )
                    state.orphan_models.append(orphan)

        # Parse bronze dependencies from manifest.json if available
        self._parse_bronze_dependencies(state)

        return state

    def _parse_bronze_dependencies(self, state: ProjectState) -> None:
        """Parse bronze layer dependencies from manifest.json.

        Finds source tables that silver models depend on and adds them as bronze_models.
        """
        import json

        manifest_path = self.config.project_dir / "target" / "manifest.json"
        if not manifest_path.exists():
            return  # No manifest available, skip bronze parsing

        try:
            with open(manifest_path) as f:
                manifest = json.load(f)

            # Get all silver models that belong to concepts
            silver_to_concept = {}
            for concept_id, concept in state.concepts.items():
                for silver_model in concept.silver_models:
                    silver_to_concept[silver_model] = concept_id

            # Parse dependencies for each silver model
            nodes = manifest.get("nodes", {})

            for node_id, node_data in nodes.items():
                if not node_id.startswith("model."):
                    continue

                model_name = node_data.get("name")
                if not model_name or model_name not in silver_to_concept:
                    continue

                concept_id = silver_to_concept[model_name]
                concept = state.concepts[concept_id]

                # Get all source dependencies
                depends_on = node_data.get("depends_on", {})
                for source_id in depends_on.get("nodes", []):
                    if source_id.startswith("source."):
                        # Extract source name from ID (e.g., "source.project.schema.table")
                        parts = source_id.split(".")
                        if len(parts) >= 4:
                            source_name = f"{parts[2]}.{parts[3]}"
                            if source_name not in concept.bronze_models:
                                concept.bronze_models.append(source_name)

        except Exception as e:
            # Don't fail if manifest parsing fails
            print(
                f"Warning: Failed to parse manifest.json for bronze dependencies: {e}"
            )
