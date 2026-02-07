#!/bin/bash
# Integration Example: codeindex parse command
# Epic 12: Single File Parse Command
#
# This script demonstrates how to use the parse command
# for loose coupling with downstream tools like LoomGraph

set -e

echo "=== codeindex parse Integration Example ==="
echo ""

# Example 1: Parse a Python file
echo "1. Parse Python file:"
codeindex parse tests/fixtures/cli_parse/simple.py | jq .

echo ""
echo "2. Parse PHP file:"
codeindex parse tests/fixtures/cli_parse/simple.php | jq .

echo ""
echo "3. Parse Java file:"
codeindex parse tests/fixtures/cli_parse/Simple.java | jq .

echo ""
echo "4. Extract specific fields (symbols only):"
codeindex parse tests/fixtures/cli_parse/simple.py | jq '.symbols[] | {name, kind, signature}'

echo ""
echo "5. Check file language:"
codeindex parse tests/fixtures/cli_parse/simple.py | jq -r '.language'

echo ""
echo "6. Integration with LoomGraph (conceptual):"
echo "   codeindex parse myfile.py | loomgraph import --format codeindex"
echo "   # LoomGraph reads JSON from stdin and builds knowledge graph"

echo ""
echo "=== Integration Example Complete ==="
