"""Demo mode project generator for dbt-conceptual.

This module provides a self-contained demo project with example concepts,
relationships, and dbt models. The demo data is generated in a temporary
directory that is automatically cleaned up on exit.
"""

import tempfile
from pathlib import Path
from typing import Optional

# Demo project YAML content - embedded for zero external dependencies

DBT_PROJECT_YML = """
name: 'dbt_conceptual_demo'
version: '1.0.0'
config-version: 2

profile: 'demo'

model-paths: ["models"]

vars:
  dbt_conceptual:
    conceptual_path: "."
    silver_paths: ["models/silver"]
    gold_paths: ["models/gold"]
""".strip()

CONCEPTUAL_YML = """
domains:
  core:
    name: Core
    description: Core business domain
    color: "#3498db"
  analytics:
    name: Analytics
    description: Analytics and reporting domain
    color: "#9b59b6"
  sales:
    name: Sales
    description: Sales and commerce domain
    color: "#e74c3c"

concepts:
  customer:
    name: Customer
    definition: |
      A **Customer** represents an individual or organization that has
      purchased or may purchase products/services.

      ## Attributes
      - Customer ID (unique identifier)
      - Name
      - Email
      - Registration date

      ## Business Rules
      - A customer must have a valid email address
      - Customer IDs are immutable once created
    domain: core

  order:
    name: Order
    definition: |
      An **Order** represents a transaction where a customer purchases
      one or more products.

      ## Attributes
      - Order ID
      - Order date
      - Status (pending, confirmed, shipped, delivered, cancelled)
      - Total amount

      ## Business Rules
      - Orders must be associated with a valid customer
      - Order status follows a defined state machine
    domain: sales

  product:
    name: Product
    definition: |
      A **Product** is an item available for purchase.

      ## Attributes
      - Product ID
      - Name
      - Description
      - Price
      - Category

      ## Business Rules
      - Products must have a positive price
      - Product IDs are unique across the catalog
    domain: sales

  revenue:
    name: Revenue
    definition: |
      **Revenue** represents the income generated from orders.

      This is a derived metric calculated from order data.

      ## Calculation
      - Sum of order totals for completed orders
      - Can be grouped by time period, customer, product

      ## Business Rules
      - Only confirmed/delivered orders count toward revenue
      - Cancelled orders do not contribute to revenue
    domain: analytics

relationships:
  - from: customer
    to: order
    verb: places
    cardinality: one-to-many
    definition: A customer can place multiple orders

  - from: order
    to: product
    verb: contains
    cardinality: many-to-many
    definition: An order contains one or more products; products appear in many orders

  - from: order
    to: revenue
    verb: generates
    cardinality: many-to-one
    definition: Orders contribute to revenue calculations

  - from: customer
    to: revenue
    verb: contributes
    cardinality: many-to-one
    definition: Customer purchases contribute to revenue
""".strip()

BRONZE_SCHEMA_YML = """
version: 2

models:
  - name: raw_customers
    description: Raw customer data from source system

  - name: raw_orders
    description: Raw order data from source system

  - name: raw_products
    description: Raw product catalog from source system
""".strip()

SILVER_SCHEMA_YML = """
version: 2

models:
  - name: stg_customers
    description: Staged customer data
    meta:
      concept: customer

  - name: stg_orders
    description: Staged order data
    meta:
      concept: order

  - name: stg_products
    description: Staged product data
    meta:
      concept: product
""".strip()

GOLD_SCHEMA_YML = """
version: 2

models:
  - name: dim_customer
    description: Customer dimension table
    meta:
      realizes: customer

  - name: dim_product
    description: Product dimension table
    meta:
      realizes: product

  - name: fct_orders
    description: Orders fact table
    meta:
      realizes: order

  - name: fct_revenue
    description: Revenue fact/aggregate table
    meta:
      realizes: revenue
""".strip()

LAYOUT_JSON = """
{
  "version": 1,
  "positions": {
    "customer": {"x": 100, "y": 100},
    "order": {"x": 350, "y": 100},
    "product": {"x": 350, "y": 300},
    "revenue": {"x": 600, "y": 200}
  }
}
""".strip()

# Placeholder SQL files (content doesn't matter for conceptual modeling)
PLACEHOLDER_SQL = "-- Placeholder model for demo\nSELECT 1 AS id"


def create_demo_project(base_dir: Optional[Path] = None) -> Path:
    """Create a temporary demo project with example data.

    Args:
        base_dir: Optional base directory. If None, uses system temp dir.

    Returns:
        Path to the created demo project directory.
    """
    if base_dir:
        demo_dir = base_dir / "dbt_conceptual_demo"
        demo_dir.mkdir(parents=True, exist_ok=True)
    else:
        demo_dir = Path(tempfile.mkdtemp(prefix="dbt_conceptual_demo_"))

    # Create directory structure
    models_dir = demo_dir / "models"
    bronze_dir = models_dir / "bronze"
    silver_dir = models_dir / "silver"
    gold_dir = models_dir / "gold"

    for d in [bronze_dir, silver_dir, gold_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Write YAML files
    (demo_dir / "dbt_project.yml").write_text(DBT_PROJECT_YML)
    (demo_dir / "conceptual.yml").write_text(CONCEPTUAL_YML)
    (demo_dir / "conceptual.layout.json").write_text(LAYOUT_JSON)

    # Write schema files
    (bronze_dir / "_schema.yml").write_text(BRONZE_SCHEMA_YML)
    (silver_dir / "_schema.yml").write_text(SILVER_SCHEMA_YML)
    (gold_dir / "_schema.yml").write_text(GOLD_SCHEMA_YML)

    # Write placeholder SQL files
    bronze_models = ["raw_customers", "raw_orders", "raw_products"]
    silver_models = ["stg_customers", "stg_orders", "stg_products"]
    gold_models = ["dim_customer", "dim_product", "fct_orders", "fct_revenue"]

    for model in bronze_models:
        (bronze_dir / f"{model}.sql").write_text(PLACEHOLDER_SQL)
    for model in silver_models:
        (silver_dir / f"{model}.sql").write_text(PLACEHOLDER_SQL)
    for model in gold_models:
        (gold_dir / f"{model}.sql").write_text(PLACEHOLDER_SQL)

    return demo_dir
