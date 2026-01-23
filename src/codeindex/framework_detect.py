"""Framework detection and pattern extraction for PHP projects."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .parser import ParseResult, Symbol


FrameworkType = Literal["thinkphp", "laravel", "unknown"]


@dataclass
class RouteInfo:
    """Information about a route."""
    url: str
    controller: str
    action: str
    method_signature: str = ""


@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    table: str  # Inferred table name
    file_path: Path | None = None


@dataclass
class FrameworkInfo:
    """Detected framework information."""
    framework: FrameworkType
    version: str = ""
    modules: list[str] = field(default_factory=list)
    routes: list[RouteInfo] = field(default_factory=list)
    models: list[ModelInfo] = field(default_factory=list)


def detect_framework(root: Path) -> FrameworkType:
    """
    Detect which PHP framework is used in the project.

    Detection rules:
    - ThinkPHP: Has Application/ directory with Controller subdirs
    - Laravel: Has app/Http/Controllers and artisan file
    - Unknown: No recognized pattern
    """
    # Check for ThinkPHP
    app_dir = root / "Application"
    if app_dir.exists():
        # Look for Controller directories inside modules
        for module_dir in app_dir.iterdir():
            if module_dir.is_dir():
                controller_dir = module_dir / "Controller"
                if controller_dir.exists():
                    return "thinkphp"

    # Check for Laravel
    if (root / "artisan").exists() and (root / "app" / "Http" / "Controllers").exists():
        return "laravel"

    # Check composer.json for framework hints
    composer_file = root / "composer.json"
    if composer_file.exists():
        try:
            import json
            with open(composer_file) as f:
                data = json.load(f)
                require = data.get("require", {})
                if "topthink/framework" in require or "topthink/think" in require:
                    return "thinkphp"
                if "laravel/framework" in require:
                    return "laravel"
        except Exception:
            pass

    return "unknown"


def extract_thinkphp_routes(
    parse_results: list[ParseResult],
    module_name: str,
) -> list[RouteInfo]:
    """
    Extract routes from ThinkPHP controllers.

    ThinkPHP routing convention:
    - URL: /module/controller/action
    - Example: /admin/index/home -> Admin\\Controller\\IndexController::home()
    """
    routes = []

    for result in parse_results:
        if result.error:
            continue

        # Find controller class
        controller_class = None
        for symbol in result.symbols:
            if symbol.kind == "class" and symbol.name.endswith("Controller"):
                controller_class = symbol.name
                break

        if not controller_class:
            continue

        # Extract controller name (remove "Controller" suffix)
        controller_name = controller_class.replace("Controller", "").lower()

        # Find public methods (actions)
        for symbol in result.symbols:
            if symbol.kind != "method":
                continue

            # Only public methods are routes
            if "public" not in symbol.signature.lower():
                continue

            # Skip magic methods and internal methods
            method_name = symbol.name.split("::")[-1]
            if method_name.startswith("_") or method_name.startswith("__"):
                continue

            # Build route URL
            url = f"/{module_name.lower()}/{controller_name}/{method_name}"

            routes.append(RouteInfo(
                url=url,
                controller=controller_class,
                action=method_name,
                method_signature=symbol.signature,
            ))

    return routes


def extract_thinkphp_models(
    parse_results: list[ParseResult],
) -> list[ModelInfo]:
    """
    Extract model information from ThinkPHP models.

    ThinkPHP model convention:
    - Model name: UserModel -> table: tp_user (with prefix)
    - Or uses $tableName property
    """
    models = []

    for result in parse_results:
        if result.error:
            continue

        for symbol in result.symbols:
            if symbol.kind != "class":
                continue

            # Check if it's a model class
            if not symbol.name.endswith("Model"):
                # Also check if extends Model
                if "extends Model" not in symbol.signature and "extends BaseModel" not in symbol.signature:
                    continue

            # Extract model name
            model_name = symbol.name.replace("Model", "")

            # Infer table name (ThinkPHP convention: lowercase + underscore)
            # e.g., UserOrder -> user_order
            table_name = ""
            for i, char in enumerate(model_name):
                if char.isupper() and i > 0:
                    table_name += "_"
                table_name += char.lower()

            models.append(ModelInfo(
                name=symbol.name,
                table=table_name,
                file_path=result.path,
            ))

    return models


def analyze_thinkphp_project(
    root: Path,
    parse_results_by_dir: dict[Path, list[ParseResult]],
) -> FrameworkInfo:
    """
    Analyze a ThinkPHP project and extract framework-specific information.

    Args:
        root: Project root directory
        parse_results_by_dir: Parse results grouped by directory

    Returns:
        FrameworkInfo with routes, models, and module information
    """
    info = FrameworkInfo(framework="thinkphp")

    app_dir = root / "Application"
    if not app_dir.exists():
        return info

    # Find modules
    for module_dir in sorted(app_dir.iterdir()):
        if not module_dir.is_dir():
            continue
        if module_dir.name.startswith("."):
            continue

        info.modules.append(module_dir.name)

        # Extract routes from Controller directory
        controller_dir = module_dir / "Controller"
        if controller_dir in parse_results_by_dir:
            routes = extract_thinkphp_routes(
                parse_results_by_dir[controller_dir],
                module_dir.name,
            )
            info.routes.extend(routes)

        # Extract models from Model directory
        model_dir = module_dir / "Model"
        if model_dir in parse_results_by_dir:
            models = extract_thinkphp_models(parse_results_by_dir[model_dir])
            info.models.extend(models)

    return info


def format_framework_info(info: FrameworkInfo, max_routes: int = 20) -> str:
    """
    Format framework information for README output.

    Args:
        info: Framework information
        max_routes: Maximum routes to display per module

    Returns:
        Markdown formatted string
    """
    if info.framework == "unknown":
        return ""

    lines = [
        f"## Framework: {info.framework.title()}",
        "",
    ]

    if info.modules:
        lines.append(f"**Modules**: {', '.join(info.modules)}")
        lines.append("")

    # Routes table (grouped by module)
    if info.routes:
        lines.append("### Routes")
        lines.append("")
        lines.append("| URL | Controller | Action |")
        lines.append("|-----|------------|--------|")

        # Group by module (first part of URL)
        from collections import defaultdict
        by_module = defaultdict(list)
        for route in info.routes:
            module = route.url.split("/")[1] if "/" in route.url else "default"
            by_module[module].append(route)

        shown = 0
        for module, routes in sorted(by_module.items()):
            for route in routes[:max_routes]:
                lines.append(f"| `{route.url}` | {route.controller} | {route.action} |")
                shown += 1
                if shown >= max_routes * 3:  # Limit total
                    break
            if shown >= max_routes * 3:
                break

        total = len(info.routes)
        if shown < total:
            lines.append(f"| ... | _{total - shown} more routes_ | |")

        lines.append("")

    # Models table
    if info.models:
        lines.append("### Models")
        lines.append("")
        lines.append("| Model | Table |")
        lines.append("|-------|-------|")

        for model in sorted(info.models, key=lambda m: m.name)[:30]:
            lines.append(f"| {model.name} | `{model.table}` |")

        if len(info.models) > 30:
            lines.append(f"| ... | _{len(info.models) - 30} more models_ |")

        lines.append("")

    return "\n".join(lines)
