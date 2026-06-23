from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

URGENCY_COLORS = {
    "normal": "green",
    "monitor": "yellow",
    "vet_soon": "orange3",
    "emergency": "red"
}

def print_report(assessment):
    urgency = assessment.get("urgency", "unknown")
    color = URGENCY_COLORS.get(urgency, "white")

    console.print(Panel(
        "[bold]PoopSense Visual Screening[/bold]",
        style=f"bold {color}"
    ))

    table = Table(show_header=False, box=None, padding=(0,1))
    table.add_column("Field", style="dim")
    table.add_column("Value", style="bold")

    table.add_row("Color", assessment.get("color", "—"))
    table.add_row("Consistency", assessment.get("consistency", "—"))
    table.add_row("Blood present", "Yes" if assessment.get("blood_present") else "No")
    table.add_row("Mucus present", "Yes" if assessment.get("mucus_present") else "No")
    table.add_row("Foreign objects", "Yes" if assessment.get("foreign_objects") else "No")
    table.add_row(f"[{color}]Urgency[/{color}]", f"[{color}]{urgency.upper()}[/{color}]")

    console.print(table)
    console.print(f"\n[bold]Recommendation:[/bold] {assessment.get('recommendation','')}")
    console.print("\n[dim]Informational AI screening only. Not a veterinary diagnosis.[/dim]")
