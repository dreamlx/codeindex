# Security Policy

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.12.x  | :white_check_mark: |
| 0.11.x  | :white_check_mark: |
| < 0.11  | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report security issues by:

1. **Email**: Send details to the project maintainers (check repository for contact)
2. **GitHub Security Advisory**: Use the "Security" tab → "Report a vulnerability"

### What to Include

- Description of the vulnerability
- Steps to reproduce the issue
- Affected versions
- Potential impact
- Suggested fix (if you have one)

### Response Timeline

- **Initial response**: Within 48 hours
- **Status update**: Within 7 days
- **Fix timeline**: Depends on severity (Critical: <7 days, High: <30 days)

## Security Best Practices for Users

When using codeindex:

1. **Protect Credentials**
   - Never commit `.env` files or API keys
   - Review generated README_AI.md for accidentally exposed secrets
   - Use environment variables for sensitive data

2. **AI Command Security**
   - Be careful with `ai_command` in `.codeindex.yaml`
   - Use `--fallback` mode if AI CLI contains sensitive data
   - Validate AI-generated content before committing

3. **Keep Updated**
   ```bash
   pip install --upgrade ai-codeindex
   ```

4. **Validate Inputs**
   - Don't scan untrusted code without reviewing it first
   - Be cautious with external configuration files

## Known Security Considerations

- **AI-generated content**: Always review AI-generated documentation before publishing
- **File system access**: codeindex reads files in specified directories only
- **External commands**: The `ai_command` configuration executes external programs

## Security Features

- ✅ No network access (except AI CLI if configured)
- ✅ Respects `.gitignore` patterns
- ✅ Sandboxed file access (only scans specified directories)
- ✅ No code execution from scanned files

Thank you for helping keep codeindex and its users safe!
