# Technical Debt Report

## Summary

- **Files Analyzed:** 37
- **Total Issues:** 16
- **Quality Score:** 96.5/100

### Issues by Severity

- **CRITICAL:** 0
- **HIGH:** 5
- **MEDIUM:** 11
- **LOW:** 0

## Issues by Severity

### HIGH (5)

| File | Category | Description | Suggestion |
| --- | --- | --- | --- |
| topology.py | long_method | 'TopologyAnalyzer.analyze_from_data' has 159 lines (threshold: 150) | Extract helper methods to reduce complexity |
| lightrag_client.py | long_method | 'LightRAGClient.batch_create_graph' has 187 lines (threshold: 150) | Extract helper methods to reduce complexity |
| _indexing.py | long_method | '_async_index_pipeline' has 183 lines (threshold: 150) | Extract helper methods to reduce complexity |
| _indexing.py | long_method | 'update' has 161 lines (threshold: 150) | Extract helper methods to reduce complexity |
| _indexing.py | long_method | '_async_warm_update' has 186 lines (threshold: 150) | Extract helper methods to reduce complexity |

### MEDIUM (11)

| File | Category | Description | Suggestion |
| --- | --- | --- | --- |
| deps.py | long_method | 'DepsAnalyzer.analyze' has 82 lines (threshold: 80) | Consider breaking into smaller functions |
| injector.py | long_method | 'inject_parse_result' has 125 lines (threshold: 80) | Consider breaking into smaller functions |
| injector.py | high_coupling | File has 9 internal imports (threshold: 8) | Reduce coupling by introducing facades or reorganizing modules |
| overview.py | long_method | 'OverviewAnalyzer.analyze' has 101 lines (threshold: 80) | Consider breaking into smaller functions |
| indexer.py | long_method | 'index_repository' has 94 lines (threshold: 80) | Consider breaking into smaller functions |
| topology.py | long_method | 'TopologyAnalyzer._analyze_server_side' has 94 lines (threshold: 80) | Consider breaking into smaller functions |
| lightrag_client.py | medium_file | File has 831 lines (threshold: 800) | Consider refactoring to reduce file size |
| compare.py | long_method | 'CompareAnalyzer.analyze' has 82 lines (threshold: 80) | Consider breaking into smaller functions |
| _search.py | long_method | '_async_find' has 83 lines (threshold: 80) | Consider breaking into smaller functions |
| _indexing.py | medium_file | File has 821 lines (threshold: 800) | Consider refactoring to reduce file size |
| _indexing.py | long_method | 'index' has 83 lines (threshold: 80) | Consider breaking into smaller functions |
