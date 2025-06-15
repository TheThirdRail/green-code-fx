# Green-Code FX Troubleshooting Guide

Quick reference guide for diagnosing and resolving common issues with the Green-Code FX video effects generator.

## Quick Diagnostic Checklist

### 🔍 Initial Assessment (2 minutes)

- [ ] **Container Status**: `docker ps | grep green-code-fx`
- [ ] **Health Check**: `curl http://localhost:8082/api/health`
- [ ] **Resource Usage**: `docker stats --no-stream green-code-fx-generator`
- [ ] **Recent Logs**: `docker logs green-code-fx-generator --since 5m`

### 🚨 Emergency Actions

If service is completely down:
```bash
# Quick restart
docker-compose restart

# If restart fails, force rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Common Issues and Solutions

### 1. Container Won't Start

#### Symptoms
- Container exits immediately
- `docker ps` shows no running container
- Health check fails to connect

#### Diagnostic Commands
```bash
# Check container status and exit code
docker ps -a | grep green-code-fx

# View startup logs
docker logs green-code-fx-generator

# Check system resources
free -h
df -h
```

#### Common Causes and Solutions

**Port Already in Use**
```bash
# Check what's using port 8082
netstat -tulpn | grep 8082
# or
lsof -i :8082

# Solution: Kill the process or change port in docker-compose.yml
```

**Insufficient Memory**
```bash
# Check available memory
free -h

# Solution: Free up memory or reduce container memory limits
```

**Permission Issues**
```bash
# Check file permissions
ls -la docker-compose.yml
ls -la output/ temp/

# Solution: Fix permissions
chmod 644 docker-compose.yml
chmod 755 output/ temp/
```

### 2. Health Check Failures

#### Symptoms
- `/api/health` returns 5xx errors
- Health endpoint times out
- Container running but not responding

#### Diagnostic Commands
```bash
# Test health endpoint with verbose output
curl -v http://localhost:8082/api/health

# Check if Flask is starting
docker logs green-code-fx-generator | grep -i flask

# Check for Python errors
docker logs green-code-fx-generator | grep -i "traceback\|error"
```

#### Solutions

**Application Still Starting**
- Wait 30-60 seconds for complete startup
- Check logs for "Flask app started" message

**Python Import Errors**
```bash
# Rebuild container to fix dependency issues
docker-compose build --no-cache
```

**Resource Exhaustion**
```bash
# Check container resource limits
docker inspect green-code-fx-generator | grep -A 10 "Memory\|Cpu"

# Increase limits in docker-compose.yml if needed
```

### 3. Video Generation Failures

#### Symptoms
- POST requests to `/api/generate/*` return errors
- Jobs stuck in "queued" status
- Generated videos are corrupted

#### Diagnostic Commands
```bash
# Test video generation
curl -X POST http://localhost:8082/api/generate/typing \
  -H "Content-Type: application/json" \
  -d '{"duration": 10, "source_file": "snake_code.txt"}'

# Check job status
curl http://localhost:8082/api/jobs/{job_id}

# Check for FFmpeg errors
docker logs green-code-fx-generator | grep -i ffmpeg
```

#### Common Causes and Solutions

**Missing Font Files**
```bash
# Check font directory
docker exec green-code-fx-generator ls -la /app/assets/fonts/

# Solution: Add required font files to assets/fonts/
```

**Disk Space Full**
```bash
# Check disk space
df -h

# Clean up old files
docker exec green-code-fx-generator find /app/temp -type f -mtime +1 -delete
```

**FFmpeg Issues**
```bash
# Test FFmpeg in container
docker exec green-code-fx-generator ffmpeg -version

# Check for codec issues in logs
docker logs green-code-fx-generator | grep -i "codec\|encode"
```

### 4. Performance Issues

#### Symptoms
- Slow video generation (>5x realtime)
- High CPU/memory usage
- Request timeouts

#### Diagnostic Commands
```bash
# Monitor real-time resource usage
docker stats green-code-fx-generator

# Check performance metrics
curl http://localhost:8082/metrics | grep performance_ratio

# Check queue status
curl http://localhost:8082/api/resources
```

#### Solutions

**High CPU Usage**
```bash
# Reduce concurrent jobs
# Edit docker-compose.yml: MAX_CONCURRENT_JOBS=1

# Optimize video encoding
# Edit docker-compose.yml: VIDEO_PRESET=ultrafast
```

**Memory Issues**
```bash
# Increase memory limit
# Edit docker-compose.yml memory limit to 6G or 8G

# Check for memory leaks
docker logs green-code-fx-generator | grep -i "memory\|oom"
```

**Slow Disk I/O**
```bash
# Check disk I/O
iostat -x 1 5

# Move temp directory to faster storage
# Mount SSD volume for /app/temp
```

### 5. Network and API Issues

#### Symptoms
- Connection refused errors
- Timeouts on API calls
- CORS errors in browser

#### Diagnostic Commands
```bash
# Test network connectivity
curl -I http://localhost:8082/api/health

# Check port binding
netstat -tulpn | grep 8082

# Test from inside container
docker exec green-code-fx-generator curl localhost:8082/api/health
```

#### Solutions

**Port Binding Issues**
```bash
# Check docker-compose.yml port mapping
# Ensure: "8082:8082"

# Restart with correct ports
docker-compose down && docker-compose up -d
```

**Firewall Issues**
```bash
# Check firewall rules (Linux)
iptables -L | grep 8082

# Allow port through firewall
ufw allow 8082
```

**CORS Issues**
```bash
# Check CORS configuration in logs
docker logs green-code-fx-generator | grep -i cors

# Update CORS_ORIGINS in config if needed
```

## Advanced Troubleshooting

### Debug Mode

Enable debug logging:
```bash
# Set debug environment
docker-compose down
echo "LOG_LEVEL=DEBUG" >> .env
docker-compose up -d

# View debug logs
docker logs -f green-code-fx-generator
```

### Container Shell Access

Access container for debugging:
```bash
# Get shell access
docker exec -it green-code-fx-generator bash

# Check Python environment
python -c "import pygame; print('Pygame OK')"
python -c "import prometheus_client; print('Prometheus OK')"

# Check file system
ls -la /app/
ls -la /app/assets/fonts/
```

### Performance Profiling

```bash
# Generate performance test
docker exec green-code-fx-generator python scripts/simple_matrix_performance_test.py

# Check metrics
curl http://localhost:8082/metrics | grep -E "(duration|ratio|fps)"
```

## Error Code Reference

| HTTP Code | Meaning | Common Causes | Solutions |
|-----------|---------|---------------|-----------|
| 400 | Bad Request | Invalid JSON, missing parameters | Check request format |
| 429 | Too Many Requests | Rate limit exceeded | Wait or increase limits |
| 500 | Internal Server Error | Application crash, missing files | Check logs, restart |
| 503 | Service Unavailable | Resource exhaustion | Check resources, scale |

## Log Analysis

### Important Log Patterns

**Successful Operations**
```
[info] Video generation started
[info] Video generation completed
[info] Prometheus metrics collector initialized
```

**Warning Signs**
```
[warning] High CPU usage detected
[warning] Queue size growing
[warning] Disk space low
```

**Critical Errors**
```
[error] Video generation failed
[error] FFmpeg process failed
[error] Out of memory
```

### Log Analysis Commands

```bash
# Count errors by type
docker logs green-code-fx-generator 2>&1 | grep -i error | sort | uniq -c

# Find performance issues
docker logs green-code-fx-generator 2>&1 | grep -E "(slow|timeout|performance)"

# Monitor real-time logs
docker logs -f green-code-fx-generator | grep -E "(error|warning|failed)"
```

## Recovery Procedures

### Quick Recovery
```bash
# Standard restart
docker-compose restart

# Clean restart
docker-compose down && docker-compose up -d
```

### Full Recovery
```bash
# Complete rebuild
docker-compose down
docker system prune -f
docker-compose build --no-cache
docker-compose up -d
```

### Emergency Recovery
```bash
# Nuclear option - complete reset
docker-compose down
docker system prune -a -f
git pull origin main
docker-compose build --no-cache
docker-compose up -d
```

## Prevention

### Monitoring Setup
- Set up Prometheus alerts for key metrics
- Monitor disk space and resource usage
- Set up log aggregation and analysis

### Maintenance Schedule
- **Daily**: Health checks and resource monitoring
- **Weekly**: Log rotation and performance review
- **Monthly**: Security updates and capacity planning

### Best Practices
- Always check logs before and after changes
- Test changes in staging environment first
- Keep monitoring data for trend analysis
- Document all configuration changes

---

**Emergency Contact**: [Your contact information]
**Last Updated**: [Current date]
