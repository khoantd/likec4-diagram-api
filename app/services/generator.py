"""Generate LikeC4 diagrams in D2, Mermaid, or PlantUML from a processed view."""

from app.core.schemas import ProcessedView, ViewEdge, ViewNode

DiagramFormat = str  # "d2" | "mermaid" | "puml"


def _fqn_name(node_id: str) -> str:
    """Convert node id (e.g. 'cloud.backend.api') to D2-style name (e.g. 'Cloud.Backend.Api')."""
    return "".join(part[:1].upper() + part[1:] for part in node_id.split("."))


def _node_name(node: ViewNode) -> str:
    """Display name for a node (segment only, not full path)."""
    if node.parent is None:
        return _fqn_name(node.id)
    segment = node.id[len(node.parent) + 1 :]
    return _fqn_name(segment)


def _d2_direction(direction: str) -> str:
    match direction:
        case "TB":
            return "down"
        case "BT":
            return "up"
        case "LR":
            return "right"
        case "RL":
            return "left"
        case _:
            return "down"


def _d2_shape(shape: str) -> str:
    if shape in ("queue", "cylinder", "rectangle", "document"):
        return shape
    if shape == "person":
        return "c4-person"
    if shape == "storage":
        return "stored_data"
    return "rectangle"


def _generate_d2(view: ProcessedView) -> str:
    """Generate D2 diagram text from a processed view (mirrors @likec4/generators D2)."""
    nodes = view.nodes
    edges = view.edges
    names: dict[str, str] = {}

    def print_node(node: ViewNode, parent_name: str | None = None) -> str:
        name = _node_name(node)
        fqn = f"{parent_name}.{name}" if parent_name else name
        names[node.id] = fqn
        label = _escape_d2_label(node.title)
        shape = _d2_shape(node.shape)
        child_nodes = [n for n in nodes if n.parent == node.id]
        lines = [f"  label: {label}"]
        if shape != "rectangle":
            lines.append(f"  shape: {shape}")
        for child in child_nodes:
            lines.append("")
            lines.append(print_node(child, fqn))
        body = "\n".join(lines)
        return f"{name}: {{\n{body}\n}}\n"

    root_nodes = [n for n in nodes if n.parent is None]
    direction = _d2_direction(view.auto_layout.direction)
    out_lines = [f"direction: {direction}", ""]
    for node in root_nodes:
        out_lines.append(print_node(node))
    if edges:
        out_lines.append("")
        for e in edges:
            src = names.get(e.source, e.source)
            tgt = names.get(e.target, e.target)
            if e.label:
                out_lines.append(f'{src} -> {tgt}: {_escape_d2_label(e.label)}')
            else:
                out_lines.append(f"{src} -> {tgt}")
    return "\n".join(out_lines).strip() + "\n"


def _escape_d2_label(s: str) -> str:
    """Escape and quote label for D2 (JSON-style string)."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def _generate_mermaid(view: ProcessedView) -> str:
    """Generate Mermaid diagram from a processed view (mirrors @likec4/generators Mermaid)."""
    nodes = view.nodes
    edges = view.edges
    names: dict[str, str] = {}

    def mermaid_label(s: str) -> str:
        return s.replace('"', "#quot;").replace("\n", "<br/>")

    def node_name_segment(node: ViewNode) -> str:
        if node.parent is None:
            return _fqn_name(node.id)
        segment = node.id[len(node.parent) + 1 :]
        return _fqn_name(segment)

    def print_node(node: ViewNode, parent_name: str | None = None) -> str:
        name = node_name_segment(node)
        fqn = f"{parent_name}.{name}" if parent_name else name
        names[node.id] = fqn
        label = mermaid_label(node.title)
        child_nodes = [n for n in nodes if n.parent == node.id]
        if child_nodes:
            parts = [f'subgraph {fqn}["{label}"]']
            for child in child_nodes:
                parts.append("  " + print_node(child, fqn).replace("\n", "\n  "))
            parts.append("end")
            return "\n".join(parts)
        return f'{fqn}["{label}"]'

    root_nodes = [n for n in nodes if n.parent is None]
    out_lines = ["flowchart TB"]
    for node in root_nodes:
        out_lines.append(print_node(node))
    for e in edges:
        src = names.get(e.source, e.source)
        tgt = names.get(e.target, e.target)
        if e.label:
            out_lines.append(f'{src} -->|{mermaid_label(e.label)}| {tgt}')
        else:
            out_lines.append(f"{src} --> {tgt}")
    return "\n".join(out_lines)


def _generate_puml(view: ProcessedView) -> str:
    """Generate PlantUML diagram from a processed view (mirrors @likec4/generators PlantUML)."""
    nodes = view.nodes
    edges = view.edges
    names: dict[str, str] = {}

    def segment_name(node: ViewNode) -> str:
        if node.parent is None:
            return _fqn_name(node.id)
        return _fqn_name(node.id[len(node.parent) + 1 :])

    def resolve_fqn(node: ViewNode) -> str:
        if node.parent is None:
            return segment_name(node)
        parent_fqn = names.get(node.parent)
        if parent_fqn is None:
            pn = next((n for n in nodes if n.id == node.parent), None)
            if pn:
                names[node.parent] = resolve_fqn(pn)
            parent_fqn = names.get(node.parent, node.parent)
        return f"{parent_fqn}.{segment_name(node)}"

    for node in nodes:
        names[node.id] = resolve_fqn(node)

    out = ["@startuml", "!pragma layout smetana", ""]
    for node in nodes:
        out.append(f'rectangle "{node.title}" as {names[node.id]}')
    out.append("")
    for e in edges:
        src = names.get(e.source, e.source)
        tgt = names.get(e.target, e.target)
        if e.label:
            out.append(f'{src} --> {tgt} : {e.label}')
        else:
            out.append(f"{src} --> {tgt}")
    out.append("@enduml")
    return "\n".join(out)


def generate_diagram(view: ProcessedView, format: DiagramFormat) -> str:
    """
    Generate diagram in the requested format from a LikeC4 processed view.

    Supported formats: d2, mermaid, puml.
    """
    fmt = format.lower().strip()
    if fmt == "d2":
        return _generate_d2(view)
    if fmt == "mermaid" or fmt == "mmd":
        return _generate_mermaid(view)
    if fmt == "puml" or fmt == "plantuml":
        return _generate_puml(view)
    raise ValueError(f"Unsupported diagram format: {format}. Use one of: d2, mermaid, puml")
