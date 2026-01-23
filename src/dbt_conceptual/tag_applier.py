"""Tag applier for propagating domain/owner tags to dbt model files."""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from dbt_conceptual.config import Config
from dbt_conceptual.state import ProjectState

logger = logging.getLogger(__name__)

# Pattern to detect YAML anchors (&name) and aliases (*name)
_YAML_ANCHOR_PATTERN = re.compile(r"[&*]\w+")


@dataclass
class TagChange:
    """Represents a change to be made to a model's tags."""

    model_name: str
    file_path: Path
    action: str  # "add", "modify", "none"
    current_tags: list[str]
    expected_tags: list[str]
    domain_tags_to_add: list[str] = field(default_factory=list)
    domain_tags_to_remove: list[str] = field(default_factory=list)
    owner_tag_to_add: Optional[str] = None
    owner_tag_to_remove: Optional[str] = None


@dataclass
class ApplyResult:
    """Result of applying tag changes."""

    changes: list[TagChange]
    modified_files: list[Path]
    errors: list[str]


class TagApplier:
    """Applies domain and owner tags to dbt model YAML files."""

    def __init__(self, config: Config, state: ProjectState):
        """Initialize the tag applier.

        Args:
            config: Configuration object
            state: Project state with concepts and models
        """
        self.config = config
        self.state = state
        self.tag_config = config.validation.tag_validation

    def compute_changes(
        self, model_names: Optional[list[str]] = None
    ) -> list[TagChange]:
        """Compute what tag changes need to be made.

        Args:
            model_names: Optional list of model names to scope changes to.
                        If None, applies to all models.

        Returns:
            List of TagChange objects describing changes needed.
        """
        changes: list[TagChange] = []

        for model_name, model_info in self.state.models.items():
            # Skip if not in scope
            if model_names and model_name not in model_names:
                continue

            # Skip models without concept linkage
            if not model_info.concept:
                continue

            concept = self.state.concepts.get(model_info.concept)
            if not concept or concept.is_ghost:
                continue

            # Get expected domain
            expected_domain = concept.domain
            if not expected_domain:
                continue  # Can't apply tags without domain

            # Get expected owner (from concept or domain)
            expected_owner = concept.owner
            if not expected_owner:
                domain_state = self.state.domains.get(expected_domain)
                if domain_state:
                    expected_owner = domain_state.owner

            # Compute domain tag changes
            current_domain_tags = set(model_info.domain_tags)
            expected_domain_tags = {expected_domain}

            domain_tags_to_add = list(expected_domain_tags - current_domain_tags)
            domain_tags_to_remove = (
                list(current_domain_tags - expected_domain_tags)
                if not self.tag_config.domains_allow_multiple
                else []
            )

            # Compute owner tag changes
            owner_tag_to_add = None
            owner_tag_to_remove = None

            if expected_owner and model_info.owner_tag != expected_owner:
                owner_tag_to_add = expected_owner
                if model_info.owner_tag:
                    owner_tag_to_remove = model_info.owner_tag

            # Determine action
            has_changes = bool(
                domain_tags_to_add
                or domain_tags_to_remove
                or owner_tag_to_add
                or owner_tag_to_remove
            )

            if not has_changes:
                continue  # No changes needed

            action = "add" if not model_info.domain_tags else "modify"

            # Build expected tags list
            expected_tags = []
            for tag in domain_tags_to_add:
                if self.tag_config.domains_format == "standard":
                    expected_tags.append(f"domain:{tag}")
            for tag in sorted(current_domain_tags - set(domain_tags_to_remove)):
                if tag not in expected_domain_tags:
                    if self.tag_config.domains_format == "standard":
                        expected_tags.append(f"domain:{tag}")

            if owner_tag_to_add:
                if self.tag_config.domains_format == "standard":
                    expected_tags.append(f"owner:{owner_tag_to_add}")

            # Find the file path for this model
            file_path = self._find_model_file(model_name)
            if not file_path:
                continue  # Can't find file

            changes.append(
                TagChange(
                    model_name=model_name,
                    file_path=file_path,
                    action=action,
                    current_tags=list(model_info.domain_tags)
                    + ([model_info.owner_tag] if model_info.owner_tag else []),
                    expected_tags=expected_tags,
                    domain_tags_to_add=domain_tags_to_add,
                    domain_tags_to_remove=domain_tags_to_remove,
                    owner_tag_to_add=owner_tag_to_add,
                    owner_tag_to_remove=owner_tag_to_remove,
                )
            )

        return changes

    def _find_model_file(self, model_name: str) -> Optional[Path]:
        """Find the YAML file containing a model definition.

        Args:
            model_name: Name of the model to find

        Returns:
            Path to the YAML file, or None if not found
        """
        # Search in silver and gold paths
        search_paths = self.config.silver_paths + self.config.gold_paths

        for search_path in search_paths:
            full_path = self.config.project_dir / search_path
            if not full_path.exists():
                continue

            # Search for YAML files containing this model
            for yaml_file in full_path.rglob("*.yml"):
                try:
                    with open(yaml_file) as f:
                        content = yaml.safe_load(f)
                    if not content or "models" not in content:
                        continue
                    for model in content.get("models", []):
                        if model.get("name") == model_name:
                            return yaml_file
                except Exception:
                    continue

            for yaml_file in full_path.rglob("*.yaml"):
                try:
                    with open(yaml_file) as f:
                        content = yaml.safe_load(f)
                    if not content or "models" not in content:
                        continue
                    for model in content.get("models", []):
                        if model.get("name") == model_name:
                            return yaml_file
                except Exception:
                    continue

        return None

    def apply(
        self,
        changes: list[TagChange],
        dry_run: bool = False,
    ) -> ApplyResult:
        """Apply tag changes to YAML files.

        Args:
            changes: List of changes to apply
            dry_run: If True, don't actually write files

        Returns:
            ApplyResult with modified files and any errors
        """
        modified_files: list[Path] = []
        errors: list[str] = []

        # Group changes by file
        changes_by_file: dict[Path, list[TagChange]] = {}
        for change in changes:
            if change.file_path not in changes_by_file:
                changes_by_file[change.file_path] = []
            changes_by_file[change.file_path].append(change)

        # Process each file
        for file_path, file_changes in changes_by_file.items():
            try:
                self._apply_to_file(file_path, file_changes, dry_run)
                modified_files.append(file_path)
            except Exception as e:
                errors.append(f"Error processing {file_path}: {e}")

        return ApplyResult(
            changes=changes,
            modified_files=modified_files,
            errors=errors,
        )

    def _apply_to_file(
        self,
        file_path: Path,
        changes: list[TagChange],
        dry_run: bool,
    ) -> None:
        """Apply tag changes to a single YAML file.

        Args:
            file_path: Path to the YAML file
            changes: List of changes for models in this file
            dry_run: If True, don't write the file
        """
        # Read the file
        with open(file_path) as f:
            raw_content = f.read()

        # Warn if YAML anchors/aliases are detected
        if _YAML_ANCHOR_PATTERN.search(raw_content):
            logger.warning(
                "File %s contains YAML anchors/aliases which will not be preserved. "
                "Consider using --dry-run first to review changes.",
                file_path,
            )

        content = yaml.safe_load(raw_content)

        if not content or "models" not in content:
            return

        # Build lookup of changes by model name
        changes_by_model = {c.model_name: c for c in changes}

        # Update models
        for model in content.get("models", []):
            model_name = model.get("name")
            if model_name not in changes_by_model:
                continue

            change = changes_by_model[model_name]

            # Get or create config section
            if "config" not in model:
                model["config"] = {}

            config = model["config"]

            # Get or create tags list
            if "tags" not in config:
                config["tags"] = []

            tags = config["tags"]
            if not isinstance(tags, list):
                tags = [tags] if tags else []
                config["tags"] = tags

            # Apply changes based on format
            if self.tag_config.domains_format == "standard":
                # Remove old domain/owner tags
                tags = [
                    t
                    for t in tags
                    if not (t.startswith("domain:") or t.startswith("owner:"))
                ]

                # Add domain tags
                for domain in change.domain_tags_to_add:
                    tags.append(f"domain:{domain}")

                # Keep existing domain tags that aren't being removed
                for domain in sorted(
                    set(change.current_tags) - set(change.domain_tags_to_remove)
                ):
                    if (
                        domain
                        and not domain.startswith("domain:")
                        and not domain.startswith("owner:")
                    ):
                        # This was a bare domain from domain_tags list
                        if domain not in change.domain_tags_to_add:
                            if self.tag_config.domains_allow_multiple:
                                tags.append(f"domain:{domain}")

                # Add owner tag
                if change.owner_tag_to_add:
                    tags.append(f"owner:{change.owner_tag_to_add}")

                config["tags"] = tags

            elif self.tag_config.domains_format == "databricks":
                # Use databricks_tags dict
                if "databricks_tags" not in config:
                    config["databricks_tags"] = {}

                db_tags = config["databricks_tags"]

                # Set domain
                if change.domain_tags_to_add:
                    if self.tag_config.domains_allow_multiple:
                        db_tags["domain"] = change.domain_tags_to_add
                    else:
                        db_tags["domain"] = change.domain_tags_to_add[0]

                # Set owner
                if change.owner_tag_to_add:
                    db_tags["owner"] = change.owner_tag_to_add

        # Write back if not dry run
        if not dry_run:
            with open(file_path, "w") as f:
                yaml.dump(content, f, default_flow_style=False, sort_keys=False)
