"""Parse Solio optimization results HTML to extract transfer recommendations."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup


@dataclass
class Transfer:
    """A single transfer recommendation."""

    out_player: str
    in_player: str


@dataclass
class GameweekPlan:
    """Optimization plan for a single gameweek."""

    gameweek: str  # e.g., "GW17"
    grade: str  # e.g., "A-", "B+"
    points_range: str  # e.g., "60-73 pts"
    transfers_used: str  # e.g., "1 / 3"
    bank: str  # e.g., "1.5"
    transfers: list[Transfer] = field(default_factory=list)


@dataclass
class SolveResults:
    """Complete results from an optimization solve."""

    total_points: float
    total_transfers: int
    final_bank: float
    gameweek_plans: list[GameweekPlan] = field(default_factory=list)


def parse_results_html(html_content: str) -> SolveResults:
    """Parse the Solio results HTML and extract transfer recommendations.

    Args:
        html_content: Raw HTML content from the results page.

    Returns:
        SolveResults object containing all parsed data.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Parse total points and summary from evaluation node
    total_points = 0.0
    total_transfers = 0
    final_bank = 0.0

    eval_node = soup.find("div", class_=lambda x: bool(x and "evaluationNode" in x))
    if eval_node:
        # Look for total points (e.g., "639.6 pts")
        pts_span = eval_node.find("span", {"class": "text-2xl"})
        if pts_span:
            pts_text = pts_span.get_text(strip=True)
            try:
                total_points = float(pts_text)
            except ValueError:
                pass

        # Look for transfer count and bank in the summary
        summary_ps = eval_node.find_all("p", {"class": "flex"})
        for p in summary_ps:
            text = p.get_text(strip=True)
            # Bank value (e.g., "0.1")
            if "pound-sterling" in str(p):
                match = re.search(r"[\d.]+", text)
                if match:
                    try:
                        final_bank = float(match.group())
                    except ValueError:
                        pass
            # Transfer count (e.g., "10")
            elif "arrow-left-right" in str(p):
                match = re.search(r"\d+", text)
                if match:
                    try:
                        total_transfers = int(match.group())
                    except ValueError:
                        pass

    # Parse individual gameweek plans
    gameweek_plans = []
    plan_nodes = soup.find_all("div", class_=lambda x: bool(x and "planNode" in x))

    for node in plan_nodes:
        # Extract gameweek (e.g., "GW17")
        gw_elem = node.find(
            "p", class_=lambda x: bool(x and "text-lg" in x and "font-light" in x)
        )
        if not gw_elem:
            continue
        gameweek = gw_elem.get_text(strip=True)

        # Extract grade (e.g., "A-", "B+")
        grade = ""
        grade_elem = node.find(
            "span",
            class_=lambda x: bool(x and "text-2xl" in x and "font-semibold" in x),
        )
        if grade_elem:
            grade = grade_elem.get_text(strip=True)

        # Extract points range
        points_range = ""
        points_container = grade_elem.find_parent("span") if grade_elem else None
        if points_container:
            # Get text after the grade span (e.g., "60-73 pts")
            full_text = points_container.get_text(strip=True)
            # Remove the grade prefix
            points_range = full_text.replace(grade, "").strip()

        # Extract transfers used and bank
        transfers_used = ""
        bank = ""
        info_ps = node.find_all("p", {"class": "flex"})
        for p in info_ps:
            parent_div = p.find_parent(
                "div", class_=lambda x: bool(x and "flex" in x and "gap-2" in x)
            )
            if not parent_div:
                continue
            text = p.get_text(strip=True)
            svg = p.find("svg")
            if svg:
                aria_label = svg.get("aria-label", "")
                if aria_label == "Transfers":
                    transfers_used = text
                elif aria_label == "Bank":
                    bank = text

        # Extract transfer recommendations (OUT -> IN)
        transfers = []
        transfer_div = node.find("div", class_=lambda x: bool(x and "max-w-22" in x))
        if transfer_div:
            # Find OUT players (opacity-50 section)
            out_div = transfer_div.find(
                "div", class_=lambda x: bool(x and "opacity-50" in x)
            )
            out_players = []
            if out_div:
                for p in out_div.find_all("p"):
                    out_players.append(p.get_text(strip=True))

            # Find IN players (after the arrow, text-base section)
            in_div = None
            arrow = transfer_div.find(
                "svg", class_=lambda x: bool(x and "arrow-down" in x)
            )
            if arrow:
                in_div = arrow.find_next_sibling("div")
            if in_div:
                in_players = []
                for p in in_div.find_all("p"):
                    in_players.append(p.get_text(strip=True))

                # Match OUT and IN players
                for out_p, in_p in zip(out_players, in_players):
                    transfers.append(Transfer(out_player=out_p, in_player=in_p))

        plan = GameweekPlan(
            gameweek=gameweek,
            grade=grade,
            points_range=points_range,
            transfers_used=transfers_used,
            bank=bank,
            transfers=transfers,
        )
        gameweek_plans.append(plan)

    # Sort by gameweek number
    def gw_sort_key(plan: GameweekPlan) -> int:
        match = re.search(r"\d+", plan.gameweek)
        return int(match.group()) if match else 0

    gameweek_plans.sort(key=gw_sort_key)

    return SolveResults(
        total_points=total_points,
        total_transfers=total_transfers,
        final_bank=final_bank,
        gameweek_plans=gameweek_plans,
    )


def parse_results_file(file_path: Path) -> SolveResults:
    """Parse a saved results HTML file.

    Args:
        file_path: Path to the HTML file.

    Returns:
        SolveResults object containing all parsed data.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return parse_results_html(html_content)


def format_results_text(results: SolveResults) -> str:
    """Format results as human-readable text for email/display.

    Args:
        results: Parsed solve results.

    Returns:
        Formatted text string.
    """
    lines = []
    lines.append("=" * 50)
    lines.append("SOLIO OPTIMIZATION RESULTS")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"Total Projected Points: {results.total_points}")
    lines.append(f"Total Transfers: {results.total_transfers}")
    lines.append(f"Final Bank: {results.final_bank}m")
    lines.append("")

    for plan in results.gameweek_plans:
        lines.append("-" * 40)
        lines.append(f"{plan.gameweek}: {plan.grade} ({plan.points_range})")
        lines.append(f"  Transfers: {plan.transfers_used} | Bank: {plan.bank}m")

        if plan.transfers:
            lines.append("  Recommended moves:")
            for t in plan.transfers:
                lines.append(f"    - {t.out_player} -> {t.in_player}")
        else:
            lines.append("  No transfers this week")
        lines.append("")

    lines.append("=" * 50)
    return "\n".join(lines)


def main():
    """Parse the most recent results file and print summary."""
    from .config import OUTPUT_DIR

    # Find most recent results file
    result_files = list(OUTPUT_DIR.glob("results_*.html"))
    if not result_files:
        print("No results files found in output directory.")
        return

    latest_file = max(result_files, key=lambda f: f.stat().st_mtime)
    print(f"Parsing: {latest_file}")
    print()

    results = parse_results_file(latest_file)
    print(format_results_text(results))


if __name__ == "__main__":
    main()
