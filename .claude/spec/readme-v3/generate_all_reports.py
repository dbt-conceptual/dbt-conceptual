#!/usr/bin/env python3
"""Generate PNG assets from all-reports.html using Playwright."""

import asyncio
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed")
    print("Run: pip install playwright && playwright install chromium")
    exit(1)


async def generate_reports():
    """Generate PNG assets from all-reports.html."""
    script_dir = Path(__file__).parent
    html_file = script_dir / "all-reports.html"
    assets_dir = script_dir.parent.parent.parent / "assets"

    # Ensure assets directory exists
    assets_dir.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Load the HTML file
        await page.goto(f"file://{html_file.absolute()}")

        # Wait for fonts to load
        await page.wait_for_timeout(1000)

        # Get all report sections
        report_sections = await page.query_selector_all(".report-section")

        # Report 1: Coverage Dashboard
        print("Generating coverage-dashboard.png...")
        coverage_frame = await report_sections[0].query_selector(".coverage-dashboard")
        await coverage_frame.screenshot(
            path=str(assets_dir / "coverage-dashboard.png"),
            omit_background=False
        )

        # Report 2: Bus Matrix
        print("Generating bus-matrix.png...")
        bus_matrix_frame = await report_sections[1].query_selector(".bus-matrix")
        await bus_matrix_frame.screenshot(
            path=str(assets_dir / "bus-matrix.png"),
            omit_background=False
        )

        # Report 3: Diff Report (UI version)
        print("Generating diff-report.png...")
        diff_frame = await report_sections[2].query_selector(".diff-report")
        await diff_frame.screenshot(
            path=str(assets_dir / "diff-report.png"),
            omit_background=False
        )

        # Report 3b: Diff CLI Output
        print("Generating diff-cli.png...")
        diff_cli = await report_sections[3].query_selector(".cli-output")
        await diff_cli.screenshot(
            path=str(assets_dir / "diff-cli.png"),
            omit_background=False
        )

        # Report 4: Validation (with errors)
        print("Generating validation-errors.png...")
        validation_errors = await report_sections[4].query_selector(".validation-report")
        await validation_errors.screenshot(
            path=str(assets_dir / "validation-errors.png"),
            omit_background=False
        )

        # Report 4b: Validation (success)
        print("Generating validation-success.png...")
        validation_success = await report_sections[5].query_selector(".validation-report")
        await validation_success.screenshot(
            path=str(assets_dir / "validation-success.png"),
            omit_background=False
        )

        await browser.close()

    print(f"\nAll report assets generated in: {assets_dir}")
    print("- coverage-dashboard.png")
    print("- bus-matrix.png")
    print("- diff-report.png")
    print("- diff-cli.png")
    print("- validation-errors.png")
    print("- validation-success.png")


if __name__ == "__main__":
    asyncio.run(generate_reports())
