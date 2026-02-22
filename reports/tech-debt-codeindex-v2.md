# Technical Debt Report

## Summary

- **Files Analyzed:** 37
- **Total Issues:** 18
- **Quality Score:** 97.0/100

### Issues by Severity

- **CRITICAL:** 0
- **HIGH:** 2
- **MEDIUM:** 16
- **LOW:** 0

## Issues by Severity

### HIGH (2)

| File | Category | Description | Suggestion |
| --- | --- | --- | --- |
| cli_scan.py | long_method | 'scan' has 256 lines (threshold: 150) | Extract helper methods to reduce complexity |
| cli_scan.py | long_method | 'scan_all' has 207 lines (threshold: 150) | Extract helper methods to reduce complexity |

### MEDIUM (16)

| File | Category | Description | Suggestion |
| --- | --- | --- | --- |
| tech_debt.py | long_method | 'TechDebtDetector.analyze_symbol_overload' has 86 lines (threshold: 80) | Consider breaking into smaller functions |
| cli_tech_debt.py | high_coupling | File has 10 internal imports (threshold: 8) | Reduce coupling by introducing facades or reorganizing modules |
| directory_tree.py | long_method | 'DirectoryTree._build_tree' has 105 lines (threshold: 80) | Consider breaking into smaller functions |
| cli_symbols.py | long_method | 'extract_module_purpose' has 93 lines (threshold: 80) | Consider breaking into smaller functions |
| cli_symbols.py | high_coupling | File has 10 internal imports (threshold: 8) | Reduce coupling by introducing facades or reorganizing modules |
| cli_scan.py | high_coupling | File has 16 internal imports (threshold: 8) | Reduce coupling by introducing facades or reorganizing modules |
| cli_config.py | long_method | 'init' has 129 lines (threshold: 80) | Consider breaking into smaller functions |
| cli_parse.py | long_method | 'parse' has 89 lines (threshold: 80) | Consider breaking into smaller functions |
| hierarchical.py | long_method | 'scan_directories_hierarchical' has 81 lines (threshold: 80) | Consider breaking into smaller functions |
| hierarchical.py | long_method | 'generate_enhanced_fallback_readme' has 130 lines (threshold: 80) | Consider breaking into smaller functions |
| cli_hooks.py | medium_file | File has 819 lines (threshold: 800) | Consider refactoring to reduce file size |
| cli_hooks.py | long_method | '_generate_pre_commit_script' has 142 lines (threshold: 80) | Consider breaking into smaller functions |
| cli_hooks.py | long_method | '_generate_post_commit_script' has 137 lines (threshold: 80) | Consider breaking into smaller functions |
| cli.py | high_coupling | File has 14 internal imports (threshold: 8) | Reduce coupling by introducing facades or reorganizing modules |
| init_wizard.py | long_method | 'run_interactive_wizard' has 88 lines (threshold: 80) | Consider breaking into smaller functions |
| init_wizard.py | long_method | 'create_codeindex_md' has 106 lines (threshold: 80) | Consider breaking into smaller functions |
