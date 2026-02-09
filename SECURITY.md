# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:
1. Do NOT open a public issue
2. Email: [your-email] with details
3. We will respond within 48 hours

## API Key Safety

EchoScribe takes API key security seriously:
- API keys are stored in Windows Credential Manager (encrypted by OS)
- Keys are NEVER stored in config files, logs, or source code
- All log output automatically masks API key patterns
- Pre-commit hooks scan for accidental key commits
- CI/CD includes secret scanning via TruffleHog

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |
