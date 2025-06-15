# Green-Code FX Operations Runbook

This document provides comprehensive operational procedures for deploying, maintaining, and troubleshooting the Green-Code FX video effects generator in production environments.

## Table of Contents

1. [Deployment Procedures](#deployment-procedures)
2. [Monitoring and Health Checks](#monitoring-and-health-checks)
3. [Troubleshooting Guide](#troubleshooting-guide)
4. [Maintenance Tasks](#maintenance-tasks)
5. [Incident Response](#incident-response)
6. [Performance Optimization](#performance-optimization)
7. [Backup and Recovery](#backup-and-recovery)

## Deployment Procedures

### Initial Deployment

#### Prerequisites
- Docker Engine 20.10+ and Docker Compose 2.0+
- 4GB+ available RAM
- 10GB+ free disk space
- Network access for container registry

#### Step-by-Step Deployment

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd green-code-fx
   ```

2. **Configure Environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit configuration
   nano .env
   ```

3. **Build and Deploy**
   ```bash
   # Build container
   ./scripts/build.sh
   
   # Start services
   ./scripts/run.sh
   
   # Verify deployment
   ./scripts/health-check.sh
   ```

4. **Verify Installation**
   ```bash
   # Test health endpoint
   curl http://localhost:8082/api/health
   
   # Test metrics endpoint
   curl http://localhost:8082/metrics
   
   # Generate test video
   curl -X POST http://localhost:8082/api/generate/typing \
     -H "Content-Type: application/json" \
     -d '{"duration": 10, "source_file": "snake_code.txt"}'
   ```

### Production Deployment

#### Environment Configuration
```bash
# Production environment variables
FLASK_ENV=production
METRICS_ENABLED=true
LOG_LEVEL=INFO
MAX_CONCURRENT_JOBS=2
VIDEO_CRF=18
```

#### Resource Limits
```yaml
# docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

#### Security Configuration
- Run container as non-root user
- Use read-only filesystem where possible
- Configure proper network isolation
- Enable security scanning in CI/CD

### Rolling Updates

1. **Prepare New Version**
   ```bash
   # Pull latest changes
   git pull origin main
   
   # Build new image
   docker-compose build --no-cache
   ```

2. **Health Check Current System**
   ```bash
   # Verify current system is healthy
   curl -f http://localhost:8082/api/health
   ```

3. **Deploy with Zero Downtime**
   ```bash
   # Scale up new instance
   docker-compose up -d --scale video-fx-generator=2
   
   # Wait for new instance to be healthy
   sleep 30
   
   # Remove old instance
   docker-compose up -d --scale video-fx-generator=1
   ```

## Monitoring and Health Checks

### Health Endpoints

#### System Health
```bash
# Basic health check
curl http://localhost:8082/api/health

# Expected response
{
  "status": "healthy",
  "version": "1.0.0",
  "active_jobs": 0,
  "queue_length": 0,
  "disk_space": "15.2GB available"
}
```

#### Resource Status
```bash
# Detailed resource information
curl http://localhost:8082/api/resources

# Expected response
{
  "status": "normal",
  "cpu_percent": 25.5,
  "memory_percent": 45.2,
  "disk_percent": 60.1,
  "queue_size": 0,
  "active_jobs": 0
}
```

### Monitoring Metrics

#### Key Performance Indicators
- **Availability**: Health endpoint response time < 1s
- **Performance**: Video generation time ≤ 2x realtime
- **Resource Usage**: CPU < 80%, Memory < 85%
- **Error Rate**: < 5% of video generation requests

#### Prometheus Queries
```promql
# Service availability
up{job="green-code-fx"}

# Request rate
rate(green_code_fx_http_requests_total[5m])

# Error rate
rate(green_code_fx_video_generation_total{status="error"}[5m]) / rate(green_code_fx_video_generation_total[5m])

# Average generation time
rate(green_code_fx_video_generation_duration_seconds_sum[5m]) / rate(green_code_fx_video_generation_duration_seconds_count[5m])
```

### Log Monitoring

#### Important Log Events
- Video generation start/completion
- Error conditions and stack traces
- Resource pressure warnings
- Rate limiting violations
- Container startup/shutdown

#### Log Analysis Commands
```bash
# View real-time logs
docker logs -f green-code-fx-generator

# Search for errors
docker logs green-code-fx-generator 2>&1 | grep -i error

# Export logs for analysis
docker logs green-code-fx-generator > /var/log/green-code-fx.log
```

## Troubleshooting Guide

### Common Issues

#### Container Won't Start

**Symptoms**: Container exits immediately or fails to start

**Diagnosis**:
```bash
# Check container status
docker ps -a

# View container logs
docker logs green-code-fx-generator

# Check resource availability
docker system df
free -h
```

**Solutions**:
1. **Insufficient Resources**: Increase available RAM/disk space
2. **Port Conflicts**: Change port mapping in docker-compose.yml
3. **Permission Issues**: Ensure proper file permissions
4. **Missing Dependencies**: Rebuild container with `--no-cache`

#### Health Check Failures

**Symptoms**: Health endpoint returns 5xx or times out

**Diagnosis**:
```bash
# Test health endpoint
curl -v http://localhost:8082/api/health

# Check container logs
docker logs green-code-fx-generator | tail -50

# Verify container is running
docker ps | grep green-code-fx
```

**Solutions**:
1. **Container Not Ready**: Wait 30-60 seconds for startup
2. **Resource Exhaustion**: Check CPU/memory usage
3. **Application Error**: Review logs for exceptions
4. **Network Issues**: Verify port mapping and firewall

#### Video Generation Failures

**Symptoms**: Video generation requests return errors

**Diagnosis**:
```bash
# Test video generation
curl -X POST http://localhost:8082/api/generate/typing \
  -H "Content-Type: application/json" \
  -d '{"duration": 10, "source_file": "snake_code.txt"}'

# Check job status
curl http://localhost:8082/api/jobs/{job_id}

# Review generation logs
docker logs green-code-fx-generator | grep "video generation"
```

**Solutions**:
1. **Missing Assets**: Ensure font files are present
2. **Disk Space**: Check available disk space
3. **Resource Limits**: Verify CPU/memory availability
4. **FFmpeg Issues**: Check FFmpeg installation in container

#### Performance Issues

**Symptoms**: Slow video generation or high resource usage

**Diagnosis**:
```bash
# Check system resources
docker stats green-code-fx-generator

# Monitor performance metrics
curl http://localhost:8082/metrics | grep performance_ratio

# Check queue status
curl http://localhost:8082/api/resources
```

**Solutions**:
1. **Reduce Concurrent Jobs**: Lower MAX_CONCURRENT_JOBS
2. **Optimize Video Settings**: Adjust CRF/preset values
3. **Scale Resources**: Increase CPU/memory allocation
4. **Clean Temporary Files**: Remove old temp files

### Error Code Reference

| Error Code | Description | Solution |
|------------|-------------|----------|
| 400 | Invalid request parameters | Check request format and parameters |
| 429 | Rate limit exceeded | Wait or increase rate limits |
| 500 | Internal server error | Check logs for exceptions |
| 503 | Service unavailable | Check resource availability |

## Maintenance Tasks

### Daily Tasks

#### Health Verification
```bash
# Automated health check script
#!/bin/bash
HEALTH_URL="http://localhost:8082/api/health"
if curl -f "$HEALTH_URL" > /dev/null 2>&1; then
    echo "✅ Service is healthy"
else
    echo "❌ Service health check failed"
    # Send alert
fi
```

#### Resource Monitoring
```bash
# Check disk space
df -h /var/lib/docker

# Check container resource usage
docker stats --no-stream green-code-fx-generator

# Check log file sizes
du -sh /var/log/docker/
```

### Weekly Tasks

#### Log Rotation
```bash
# Rotate Docker logs
docker logs green-code-fx-generator > /backup/logs/green-code-fx-$(date +%Y%m%d).log
docker-compose restart
```

#### Performance Review
```bash
# Generate performance report
curl http://localhost:8082/metrics | grep -E "(generation_duration|performance_ratio)" > performance-$(date +%Y%m%d).txt
```

#### Security Updates
```bash
# Check for base image updates
docker pull python:3.12-slim-bullseye

# Rebuild if updates available
docker-compose build --pull
```

### Monthly Tasks

#### Capacity Planning
- Review resource usage trends
- Analyze video generation patterns
- Plan for scaling requirements

#### Security Review
- Review security scan results
- Update dependencies
- Review access logs

#### Backup Verification
- Test backup restoration procedures
- Verify backup integrity
- Update backup retention policies

## Incident Response

### Severity Levels

#### Critical (P1)
- Service completely unavailable
- Data loss or corruption
- Security breach

**Response Time**: 15 minutes
**Resolution Time**: 2 hours

#### High (P2)
- Significant performance degradation
- Partial service unavailability
- High error rates

**Response Time**: 1 hour
**Resolution Time**: 8 hours

#### Medium (P3)
- Minor performance issues
- Non-critical feature failures

**Response Time**: 4 hours
**Resolution Time**: 24 hours

### Incident Response Procedures

#### Initial Response
1. **Acknowledge**: Confirm incident receipt
2. **Assess**: Determine severity level
3. **Communicate**: Notify stakeholders
4. **Investigate**: Gather diagnostic information

#### Investigation Steps
```bash
# Collect system information
docker ps -a
docker logs green-code-fx-generator --since 1h
curl http://localhost:8082/api/health
curl http://localhost:8082/api/resources
docker stats --no-stream
```

#### Recovery Actions
1. **Immediate**: Restart container if needed
2. **Short-term**: Apply hotfixes or workarounds
3. **Long-term**: Implement permanent solutions

#### Post-Incident
1. **Document**: Record incident details and resolution
2. **Review**: Conduct post-mortem analysis
3. **Improve**: Update procedures and monitoring

## Performance Optimization

### Video Generation Optimization

#### Encoding Settings
```bash
# High quality, smaller files
VIDEO_CRF=18
VIDEO_PRESET=medium
VIDEO_TUNE=film

# Faster encoding, larger files
VIDEO_CRF=23
VIDEO_PRESET=fast
VIDEO_TUNE=zerolatency
```

#### Resource Allocation
```yaml
# Optimize for video generation
deploy:
  resources:
    limits:
      memory: 6G
      cpus: '4.0'
```

### System Optimization

#### Container Optimization
- Use multi-stage builds
- Minimize layer count
- Optimize base image selection
- Enable BuildKit caching

#### Storage Optimization
- Regular cleanup of temporary files
- Compress old video files
- Use efficient storage drivers
- Monitor disk I/O patterns

## Backup and Recovery

### Backup Strategy

#### What to Backup
- Configuration files
- Generated videos (if required)
- Application logs
- Monitoring data

#### Backup Schedule
- **Configuration**: Daily
- **Videos**: As needed
- **Logs**: Weekly
- **Monitoring**: Monthly

#### Backup Commands
```bash
# Backup configuration
tar -czf config-backup-$(date +%Y%m%d).tar.gz docker-compose.yml .env

# Backup generated videos
tar -czf videos-backup-$(date +%Y%m%d).tar.gz output/

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz /var/log/docker/
```

### Recovery Procedures

#### Configuration Recovery
```bash
# Restore configuration
tar -xzf config-backup-YYYYMMDD.tar.gz
docker-compose up -d
```

#### Service Recovery
```bash
# Complete service restoration
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### Disaster Recovery
1. **Assess Damage**: Determine extent of failure
2. **Restore Infrastructure**: Rebuild servers if needed
3. **Restore Application**: Deploy from backup
4. **Verify Functionality**: Test all critical functions
5. **Resume Operations**: Return to normal service

---

## Quick Reference

### Emergency Contacts
- **Technical Lead**: [Contact Information]
- **DevOps Team**: [Contact Information]
- **Security Team**: [Contact Information]

### Critical Commands
```bash
# Emergency restart
docker-compose restart

# View recent errors
docker logs green-code-fx-generator --since 10m | grep -i error

# Check resource usage
docker stats --no-stream green-code-fx-generator

# Emergency stop
docker-compose down

# Force rebuild and restart
docker-compose down && docker-compose build --no-cache && docker-compose up -d
```

### Status Page URLs
- Health Check: http://localhost:8082/api/health
- Metrics: http://localhost:8082/metrics
- Resource Status: http://localhost:8082/api/resources

---

*This runbook should be reviewed and updated quarterly to ensure accuracy and completeness.*
