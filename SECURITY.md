# Security Policy

## Supported Versions

We provide security updates for the following versions of Green-Code FX:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in Green-Code FX, please report it responsibly.

### How to Report

1. **Do not** create a public GitHub issue for security vulnerabilities
2. Send an email to the project maintainers with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fix (if available)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Initial Assessment**: We will provide an initial assessment within 5 business days
- **Updates**: We will keep you informed of our progress
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days

## Security Measures

### Container Security

- **Non-root User**: Container runs as non-root user (UID 1000)
- **Read-only Filesystem**: Most of the filesystem is read-only
- **Resource Limits**: CPU and memory limits are enforced
- **Minimal Attack Surface**: Only necessary ports are exposed

### Dependency Management

- **Regular Updates**: Dependencies are regularly updated
- **Vulnerability Scanning**: Automated scanning with Trivy
- **Minimal Dependencies**: Only necessary packages are included

### API Security

- **Rate Limiting**: 10 requests per minute per client
- **Input Validation**: All inputs are validated
- **Error Handling**: Errors don't leak sensitive information
- **CORS Configuration**: Properly configured CORS headers

### Data Security

- **No Persistent Data**: No sensitive data is stored permanently
- **Temporary File Cleanup**: Temporary files are automatically cleaned
- **Secure File Handling**: File operations are sandboxed

## Security Best Practices

### Deployment

1. **Use HTTPS**: Always deploy behind HTTPS in production
2. **Network Isolation**: Use proper network segmentation
3. **Regular Updates**: Keep the container image updated
4. **Monitor Logs**: Monitor application and security logs
5. **Resource Monitoring**: Monitor resource usage for anomalies

### Configuration

1. **Environment Variables**: Use environment variables for configuration
2. **Secrets Management**: Use proper secrets management for sensitive data
3. **Least Privilege**: Grant minimal necessary permissions
4. **Regular Backups**: Backup configuration and important data

## Vulnerability Disclosure Timeline

1. **Day 0**: Vulnerability reported
2. **Day 1-2**: Acknowledgment sent
3. **Day 3-7**: Initial assessment and triage
4. **Day 8-30**: Development and testing of fix
5. **Day 30**: Public disclosure (if resolved) or status update

## Security Contacts

For security-related questions or concerns, please contact the project maintainers.

## Acknowledgments

We appreciate the security research community's efforts in making our project more secure. Contributors who responsibly disclose vulnerabilities will be acknowledged (with their permission) in our security advisories.

## Security Checklist for Contributors

Before submitting code:

- [ ] No hardcoded secrets or credentials
- [ ] Input validation for all user inputs
- [ ] Proper error handling without information leakage
- [ ] Dependencies are up to date
- [ ] Security tests are included
- [ ] Documentation is updated for security-relevant changes

## Automated Security Measures

### CI/CD Pipeline

- **Trivy Scanning**: Every build is scanned for vulnerabilities
- **Dependency Checking**: Dependencies are checked for known vulnerabilities
- **Dockerfile Security**: Dockerfile is scanned for security best practices
- **SARIF Upload**: Results are uploaded to GitHub Security tab

### Runtime Security

- **Health Monitoring**: Continuous health and resource monitoring
- **Rate Limiting**: Automatic rate limiting to prevent abuse
- **Graceful Degradation**: System degrades gracefully under pressure
- **Automatic Cleanup**: Temporary files are automatically cleaned

## Security Updates

Security updates will be released as patch versions (e.g., 1.0.1, 1.0.2) and will include:

- Vulnerability fixes
- Dependency updates
- Security configuration improvements
- Documentation updates

Users are strongly encouraged to update to the latest version promptly when security updates are released.
