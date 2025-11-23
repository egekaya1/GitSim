"""Commit graph rendering for git-sim CLI."""

from typing import Optional, Dict, List, Set, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from git_sim.core.models import CommitGraph, CommitInfo


class CommitGraphRenderer:
    """
    Renders commit DAGs in ASCII art similar to git log --graph.

    Uses a column-based algorithm where each active branch occupies
    a column, with edges connecting commits to their parents.
    """

    # Graph glyphs
    GLYPHS: Dict[str, str] = {
        "commit": "*",
        "vertical": "|",
        "horizontal": "-",
        "merge_down_right": "\\",
        "merge_down_left": "/",
        "branch_right": "\\",
        "branch_left": "/",
    }

    # Colors for branches (cycles through these)
    BRANCH_COLORS: List[str] = [
        "bright_green",
        "bright_yellow",
        "bright_blue",
        "bright_magenta",
        "bright_cyan",
        "bright_red",
    ]

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the graph renderer.

        Args:
            console: Rich Console instance. If None, creates a new one.
        """
        self.console = console or Console()

    def render(
        self,
        graph: CommitGraph,
        highlight_shas: Optional[Set[str]] = None,
        max_commits: int = 30,
        title: Optional[str] = None,
    ) -> None:
        """
        Render the commit graph to the console.

        Args:
            graph: CommitGraph to render.
            highlight_shas: Set of SHAs to highlight (e.g., rebased commits).
            max_commits: Maximum number of commits to show.
            title: Optional title for the graph panel.
        """
        highlight_shas = highlight_shas or set()

        # Get topologically sorted commits
        sorted_shas: List[str] = self._topological_sort(graph)[:max_commits]

        if not sorted_shas:
            self.console.print("[dim]No commits to display[/dim]")
            return

        # Build the graph lines
        lines: List[Text] = self._build_graph_lines(graph, sorted_shas, highlight_shas)

        # Create output text
        output = Text()
        for line in lines:
            output.append(line)
            output.append("\n")

        # Wrap in panel if title provided
        if title:
            self.console.print(Panel(output, title=title, border_style="dim"))
        else:
            self.console.print(output)

    def render_comparison(
        self,
        before: CommitGraph,
        after: CommitGraph,
        highlight_before: Optional[Set[str]] = None,
        highlight_after: Optional[Set[str]] = None,
        max_commits: int = 20,
    ) -> None:
        """
        Render before and after graphs side by side.

        Args:
            before: Graph before the operation.
            after: Graph after the operation.
            highlight_before: SHAs to highlight in before graph.
            highlight_after: SHAs to highlight in after graph.
            max_commits: Maximum commits per graph.
        """
        self.console.print()
        self.render(
            before,
            highlight_shas=highlight_before,
            max_commits=max_commits,
            title="[bold]Before[/bold]",
        )
        self.console.print()
        self.render(
            after,
            highlight_shas=highlight_after,
            max_commits=max_commits,
            title="[bold]After (Simulated)[/bold]",
        )

    def _topological_sort(self, graph: CommitGraph) -> List[str]:
        """
        Sort commits so that tips appear first and ancestors later.

        Implements a modified Kahn's algorithm on edges (child -> parent):
        - indegree[node] = number of children referencing it
        - start queue with tips (indegree == 0)
        - process by newest timestamp first for stability
        """
        # Initialize indegree counts and adjacency (child -> parents list)
        indegree: Dict[str, int] = {sha: 0 for sha in graph.commits}
        adjacency: Dict[str, List[str]] = {sha: [] for sha in graph.commits}

        for child_sha, parent_sha in graph.edges:
            if parent_sha in indegree:
                indegree[parent_sha] += 1
            if child_sha in adjacency:
                adjacency[child_sha].append(parent_sha)

        # Queue of tips (no children referencing them)
        tips: List[str] = [sha for sha, deg in indegree.items() if deg == 0]
        # Sort newest first
        tips.sort(key=lambda sha: graph.commits[sha].timestamp, reverse=True)

        result: List[str] = []
        import heapq

        # Use heap with negative timestamp for max-heap behavior
        heap: List[Tuple[int, str]] = [(-graph.commits[sha].timestamp, sha) for sha in tips]
        heapq.heapify(heap)

        while heap:
            _, sha = heapq.heappop(heap)
            result.append(sha)
            for parent in adjacency.get(sha, []):
                indegree[parent] -= 1
                if indegree[parent] == 0:
                    heapq.heappush(heap, (-graph.commits[parent].timestamp, parent))

        # Fallback: include any commits not reached (shouldn't happen in proper DAG)
        if len(result) < len(graph.commits):
            remaining: List[str] = [sha for sha in graph.commits if sha not in result]
            # Append remaining sorted by timestamp desc
            remaining.sort(key=lambda sha: graph.commits[sha].timestamp, reverse=True)
            result.extend(remaining)

        return result

    def _build_graph_lines(
        self,
        graph: CommitGraph,
        sorted_shas: List[str],
        highlight_shas: Set[str],
    ) -> List[Text]:
        """
        Build the graph lines for rendering.

        Returns list of Rich Text objects, one per commit.
        """
        lines: List[Text] = []

        # Track which column each "thread" is in
        # A thread is a branch of commits we're currently drawing
        columns: List[Optional[str]] = []  # column -> sha being tracked

        # Assign colors to branches
        branch_colors: Dict[str, str] = {}
        for i, (branch, sha) in enumerate(graph.branch_tips.items()):
            branch_colors[branch] = self.BRANCH_COLORS[i % len(self.BRANCH_COLORS)]

        for sha in sorted_shas:
            commit = graph.commits[sha]
            line = self._build_commit_line(
                commit,
                columns,
                graph,
                highlight_shas,
                branch_colors,
            )
            lines.append(line)

            # Update columns for next iteration
            self._update_columns(sha, commit, columns)

        return lines

    def _build_commit_line(
        self,
        commit: CommitInfo,
        columns: List[Optional[str]],
        graph: CommitGraph,
        highlight_shas: Set[str],
        branch_colors: Dict[str, str],
    ) -> Text:
        """Build a single line for a commit."""
        line = Text()
        sha = commit.sha

        # Find or create column for this commit
        col = self._find_column(sha, columns, commit)

        # Build the graph prefix
        for i in range(len(columns) + 1):
            if i == col:
                # This is where the commit goes
                if sha in highlight_shas:
                    line.append(self.GLYPHS["commit"], style="bold yellow")
                else:
                    line.append(self.GLYPHS["commit"], style="bold green")
            elif i < len(columns) and columns[i] is not None:
                line.append(self.GLYPHS["vertical"], style="dim")
            else:
                line.append(" ")
            line.append(" ")

        # Add commit info
        short_sha = commit.short_sha
        message = commit.first_line[:50]
        if len(commit.first_line) > 50:
            message += "..."

        # Find branch labels for this commit
        labels: List[str] = []
        for branch, tip_sha in graph.branch_tips.items():
            if tip_sha == sha:
                color = branch_colors.get(branch, "cyan")
                if sha == graph.head_sha:
                    labels.append(f"[bold {color}]HEAD -> {branch}[/bold {color}]")
                else:
                    labels.append(f"[{color}]{branch}[/{color}]")

        # Build the info portion
        if sha in highlight_shas:
            line.append(f"[bold yellow]{short_sha}[/bold yellow] ")
        else:
            line.append(f"[yellow]{short_sha}[/yellow] ")

        if labels:
            line.append("(")
            line.append(Text.from_markup(", ".join(labels)))
            line.append(") ")

        line.append(message, style="white")

        return line

    def _find_column(
        self,
        sha: str,
        columns: List[Optional[str]],
        commit: CommitInfo,
    ) -> int:
        """Find or create a column for a commit."""
        # Check if we're already tracking this SHA
        for i, tracked in enumerate(columns):
            if tracked == sha:
                return i

        # Check if any parent is being tracked (continue that column)
        for parent_sha in commit.parent_shas:
            for i, tracked in enumerate(columns):
                if tracked == parent_sha:
                    columns[i] = sha
                    return i

        # Need a new column - find first empty or append
        for i, tracked in enumerate(columns):
            if tracked is None:
                columns[i] = sha
                return i

        columns.append(sha)
        return len(columns) - 1

    def _update_columns(
        self,
        sha: str,
        commit: CommitInfo,
        columns: List[Optional[str]],
    ) -> None:
        """Update column tracking after processing a commit."""
        # Find the column for this commit
        col = -1
        for i, tracked in enumerate(columns):
            if tracked == sha:
                col = i
                break

        if col == -1:
            return

        # Replace with first parent, or clear if no parents
        if commit.parent_shas:
            columns[col] = commit.parent_shas[0]
        else:
            columns[col] = None

        # Clean up trailing None columns
        while columns and columns[-1] is None:
            columns.pop()


def render_simple_graph(
    commits: List[CommitInfo],
    highlight_shas: Optional[Set[str]] = None,
    console: Optional[Console] = None,
) -> None:
    """
    Render a simple linear commit graph.

    For cases where we just want a simple list of commits without
    full DAG visualization.
    """
    console = console or Console()
    highlight_shas = highlight_shas or set()

    for commit in commits:
        sha_style = "bold yellow" if commit.sha in highlight_shas else "yellow"
        message = commit.first_line[:60]
        if len(commit.first_line) > 60:
            message += "..."

        console.print(f"  * [{sha_style}]{commit.short_sha}[/{sha_style}] {message}")
