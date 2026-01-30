"""Parser for conceptual.yml and dbt schema files."""

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
                    display_name=domain_data.get("name", domain_id),
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

            # Build ModelInfo for tag validation
            if layer in ("silver", "gold"):
                tags = model.get("tags", [])
                databricks_tags = model.get("databricks_tags", {})
                realizes_list = meta.get("realizes", [])
                if not isinstance(realizes_list, list):
                    realizes_list = [realizes_list] if realizes_list else []

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
                    realizes=realizes_list,
                    domain_tags=domain_tags,
                    owner_tag=owner_tag,
                    layer=layer,
                    path=model.get("path"),
                )

        # Infer model associations via lineage traversal
        self._infer_lineage(state)

        return state

    def _infer_lineage(self, state: ProjectState) -> None:
        """Infer model associations via lineage traversal.

        For each model with explicit meta.concept:
        - Traverse upstream (refs) through bronze/silver to find related models
        - Traverse downstream (dependents) through gold to find related models
        - Mark inferred models as such (they can't be edited)
        """
        import json

        manifest_path = self.config.project_dir / "target" / "manifest.json"
        if not manifest_path.exists():
            return  # No manifest available, skip lineage inference

        try:
            with open(manifest_path) as f:
                manifest = json.load(f)

            nodes = manifest.get("nodes", {})

            # Build lookup: model_name -> node_id
            model_to_node: dict[str, str] = {}
            for node_id, node_data in nodes.items():
                if node_id.startswith("model."):
                    model_to_node[node_data.get("name", "")] = node_id

            # Build dependency graph: model_name -> [upstream_names]
            upstream_graph: dict[str, list[str]] = {}
            # Build reverse graph: model_name -> [downstream_names]
            downstream_graph: dict[str, list[str]] = {}

            for node_id, node_data in nodes.items():
                if not node_id.startswith("model."):
                    continue

                model_name = node_data.get("name", "")
                if not model_name:
                    continue

                upstream_graph[model_name] = []
                depends_on = node_data.get("depends_on", {})

                for dep_id in depends_on.get("nodes", []):
                    if dep_id.startswith("model."):
                        # Model dependency
                        dep_data = nodes.get(dep_id, {})
                        dep_name = dep_data.get("name", "")
                        if dep_name:
                            upstream_graph[model_name].append(dep_name)
                            # Add to downstream graph
                            if dep_name not in downstream_graph:
                                downstream_graph[dep_name] = []
                            downstream_graph[dep_name].append(model_name)
                    elif dep_id.startswith("source."):
                        # Source dependency - treat as bronze
                        parts = dep_id.split(".")
                        if len(parts) >= 4:
                            source_name = f"{parts[2]}.{parts[3]}"
                            upstream_graph[model_name].append(source_name)

            # Get model path info for layer detection
            def get_layer(model_name: str) -> Optional[str]:
                node_id = model_to_node.get(model_name)
                if not node_id:
                    return None
                node_data = nodes.get(node_id, {})
                original_path = node_data.get("original_file_path", "")
                return self.config.get_layer(original_path)

            # Find all models with explicit meta.concept
            explicit_models: dict[str, str] = {}  # model_name -> concept_id
            for concept_id, concept in state.concepts.items():
                for model_name in concept.silver_models + concept.gold_models:
                    explicit_models[model_name] = concept_id

            # For each explicitly tagged model, traverse lineage
            for anchor_model, concept_id in explicit_models.items():
                concept = state.concepts[concept_id]

                # Traverse upstream (bronze/silver)
                visited: set[str] = set()
                queue = [anchor_model]
                while queue:
                    current = queue.pop(0)
                    if current in visited:
                        continue
                    visited.add(current)

                    for upstream in upstream_graph.get(current, []):
                        if upstream in visited:
                            continue
                        if upstream in explicit_models:
                            # Stop at explicitly tagged models
                            continue

                        layer = get_layer(upstream)
                        # Sources (format: schema.table) are bronze
                        if "." in upstream:
                            layer = "bronze"

                        if layer == "bronze":
                            if upstream not in concept.bronze_models:
                                concept.bronze_models.append(upstream)
                                concept.inferred_models.append(upstream)
                            # Update ModelInfo (append to list for multi-concept)
                            if upstream in state.models:
                                if (
                                    concept_id
                                    not in state.models[upstream].inferred_concepts
                                ):
                                    state.models[upstream].inferred_concepts.append(
                                        concept_id
                                    )
                        elif layer == "silver":
                            if upstream not in concept.silver_models:
                                concept.silver_models.append(upstream)
                                concept.inferred_models.append(upstream)
                            if upstream in state.models:
                                if (
                                    concept_id
                                    not in state.models[upstream].inferred_concepts
                                ):
                                    state.models[upstream].inferred_concepts.append(
                                        concept_id
                                    )
                            # Continue traversing upstream
                            queue.append(upstream)

                # Traverse downstream (gold)
                visited = set()
                queue = [anchor_model]
                while queue:
                    current = queue.pop(0)
                    if current in visited:
                        continue
                    visited.add(current)

                    for downstream in downstream_graph.get(current, []):
                        if downstream in visited:
                            continue
                        if downstream in explicit_models:
                            # Stop if this model has explicit tag
                            # (it belongs to that concept, not inferred)
                            continue

                        layer = get_layer(downstream)
                        if layer == "gold":
                            if downstream not in concept.gold_models:
                                concept.gold_models.append(downstream)
                                concept.inferred_models.append(downstream)
                            if downstream in state.models:
                                if (
                                    concept_id
                                    not in state.models[downstream].inferred_concepts
                                ):
                                    state.models[downstream].inferred_concepts.append(
                                        concept_id
                                    )
                            # Continue traversing downstream gold
                            queue.append(downstream)
                        elif layer == "silver":
                            # Don't infer silver downstream (unusual pattern)
                            pass

        except Exception as e:
            # Don't fail if manifest parsing fails
            import logging

            logging.warning(f"Failed to parse manifest.json for lineage: {e}")

    def validate_and_sync(self, state: ProjectState) -> ValidationState:
        """Run validation checks and create ghost concepts for missing references.

        This method:
        1. Creates ghost concepts for relationships referencing non-existent concepts
        2. Checks for duplicate concept names
        3. Checks for duplicate relationships
        4. Checks for missing models in the project
        5. Generates appropriate messages

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
                        f"Stub created for concept '{rel.from_concept}'",
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
                        f"Stub created for concept '{rel.to_concept}'",
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

        # 4. Check for models referenced but not found in project
        available_models = self._get_available_models()
        for concept_id, concept in state.concepts.items():
            if concept.is_ghost:
                continue
            all_models = concept.silver_models + concept.gold_models
            for model_name in all_models:
                if model_name not in available_models:
                    messages.append(
                        make_msg(
                            "warning",
                            f"Model '{model_name}' not found in project",
                            "concept",
                            concept_id,
                        )
                    )
                    if concept.validation_status == "valid":
                        concept.validation_status = "warning"
                    concept.validation_messages.append(
                        f"Model '{model_name}' not found"
                    )

        # 5. Check for empty domains
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

        # 6. Add sync info message
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

    def _get_available_models(self) -> set[str]:
        """Get set of model names available in the project."""
        models = self.scanner.scan()
        return {m["name"] for m in models}
