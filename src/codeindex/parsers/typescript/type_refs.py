"""Type-reference extraction for TypeScript/JavaScript parser (GH #128).

Extracts type identifiers used in type position — `: Foo` annotations, generic
arguments ``Array<Foo>``, ``as Foo`` assertions — so graph-export can emit
symbol-level reference edges to the referenced type entity (interface /
type_alias / class). Without these edges, declared types that are never *called*
or *inherited* are zero-edge and get falsely flagged orphan by downstream
topology (#128: 88/92 interfaces + 25/25 type_aliases orphan on fabricOS before
type-ref; drops to 0/0 after).
"""

from tree_sitter import Node, Tree

from ...parser import TypeRef
from ..utils import get_node_text

# Node types that name a user-defined type reference. `predefined_type`
# (string/number/…) is deliberately excluded — builtins never resolve to a
# scan-tree entity, so collecting them would only add noise.
_TYPE_NAME_NODES = ("type_identifier", "nested_type_identifier")

# Parent nodes whose `type_identifier` child is the declaration *name*, not a
# reference (e.g. the `Props` in `interface Props {}`). Collecting those would
# manufacture a spurious self-reference edge for every declared type.
_DECL_NAME_PARENTS = {
    "interface_declaration",
    "type_alias_declaration",
    "class_declaration",
    "abstract_class_declaration",
    "enum_declaration",
}


def extract_type_refs(tree: Tree, source_bytes: bytes) -> list:
    """Extract type references from type-position identifiers.

    Walks the whole tree collecting ``type_identifier`` and
    ``nested_type_identifier`` nodes, skipping the declaration-name node of an
    interface/type/class/enum (that is a definition, not a reference).
    Qualified names (``Mod.Inner``) are reduced to the last segment to match
    the entity last-segment used by ``last_index`` resolution in graph-export.

    Args:
        tree: The tree-sitter parse tree.
        source_bytes: Source code as bytes.

    Returns:
        List of :class:`TypeRef` (one per type-name occurrence; graph-export
        dedups when emitting edges).
    """
    refs: list[TypeRef] = []

    def walk(node: Node) -> None:
        if node.type in _TYPE_NAME_NODES:
            parent_type = node.parent.type if node.parent else None
            if parent_type not in _DECL_NAME_PARENTS:
                text = get_node_text(node, source_bytes)
                name = text.rsplit(".", 1)[-1]
                if name:
                    refs.append(TypeRef(name=name, line=node.start_point[0] + 1))
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return refs
