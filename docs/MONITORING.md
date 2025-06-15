# Green-Code FX Monitoring Guide

This document provides comprehensive information about monitoring capabilities in the Green-Code FX video effects generator.

## Overview

The system provides detailed monitoring through:
- **Prometheus Metrics**: Comprehensive metrics collection for production monitoring
- **Health Endpoints**: Real-time system status and resource information
- **Structured Logging**: JSON-formatted logs for centralized log management

## Prometheus Metrics

### Configuration

Metrics collection is controlled by the `METRICS_ENABLED` environment variable:

```bash
# Enable metrics (default)
METRICS_ENABLED=true

# Disable metrics
METRICS_ENABLED=false
```

### Metrics Endpoint

Access metrics at: `http://localhost:8082/metrics`

The endpoint returns metrics in Prometheus format suitable for scraping.

### Available Metrics

#### Application Information
- `green_code_fx_info` - Application version and environment information

#### Video Generation Metrics
- `green_code_fx_video_generation_total` - Total video generation requests by effect type and status
- `green_code_fx_video_generation_duration_seconds` - Time spent generating videos
- `green_code_fx_video_size_bytes` - Size of generated video files

#### Queue and Job Metrics
- `green_code_fx_queue_size` - Number of jobs in queue
- `green_code_fx_active_jobs` - Number of currently running jobs
- `green_code_fx_queue_wait_time_seconds` - Time jobs spend waiting in queue

#### API Metrics
- `green_code_fx_http_requests_total` - Total HTTP requests by method, endpoint, and status
- `green_code_fx_http_request_duration_seconds` - HTTP request duration
- `green_code_fx_rate_limit_hits_total` - Number of rate limit violations

#### System Resource Metrics
- `green_code_fx_cpu_usage_percent` - CPU usage percentage
- `green_code_fx_memory_usage_percent` - Memory usage percentage
- `green_code_fx_disk_usage_percent` - Disk usage percentage
- `green_code_fx_disk_free_bytes` - Free disk space in bytes

#### Performance Metrics
- `green_code_fx_frame_generation_rate_fps` - Frame generation rate in FPS
- `green_code_fx_performance_ratio` - Generation time vs realtime ratio

### Prometheus Configuration

Example Prometheus scrape configuration:

```yaml
scrape_configs:
  - job_name: 'green-code-fx'
    static_configs:
      - targets: ['localhost:8082']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s
```

## Health Endpoints

### System Health
**Endpoint**: `GET /api/health`

Returns overall system health status:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "active_jobs": 1,
  "queue_length": 0,
  "disk_space": "15.2GB available",
  "timestamp": "2024-06-14T20:30:00Z"
}
```

### Resource Status
**Endpoint**: `GET /api/resources`

Returns detailed resource utilization:

```json
{
  "status": "normal",
  "cpu_percent": 45.2,
  "memory_percent": 62.1,
  "disk_percent": 78.5,
  "disk_free_gb": 15.2,
  "queue_size": 0,
  "active_jobs": 1,
  "max_concurrent_jobs": 2
}
```

### Rate Limit Status
**Endpoint**: `GET /api/rate-limit`

Returns current rate limiting status for the client:

```json
{
  "requests_remaining": 8,
  "reset_time": "2024-06-14T20:31:00Z",
  "limit_per_minute": 10
}
```

## Alerting Recommendations

### Critical Alerts
- **Container Down**: Health endpoint returns 5xx or is unreachable
- **High Error Rate**: Video generation error rate > 10%
- **Resource Exhaustion**: CPU > 90% or Memory > 95% for > 5 minutes
- **Disk Space Low**: Free disk space < 2GB

### Warning Alerts
- **Performance Degradation**: Generation time ratio > 3x realtime
- **Queue Buildup**: Queue size > 5 jobs for > 2 minutes
- **High Resource Usage**: CPU > 80% or Memory > 85% for > 2 minutes

### Example Prometheus Alert Rules

```yaml
groups:
  - name: green-code-fx
    rules:
      - alert: GreenCodeFXDown
        expr: up{job="green-code-fx"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Green-Code FX service is down"

      - alert: HighErrorRate
        expr: rate(green_code_fx_video_generation_total{status="error"}[5m]) / rate(green_code_fx_video_generation_total[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High video generation error rate"

      - alert: HighCPUUsage
        expr: green_code_fx_cpu_usage_percent > 90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High CPU usage detected"

      - alert: LowDiskSpace
        expr: green_code_fx_disk_free_bytes < 2e9
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space"

      - alert: PerformanceDegradation
        expr: histogram_quantile(0.95, rate(green_code_fx_performance_ratio_bucket[5m])) > 3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Video generation performance degraded"
```

## Grafana Dashboard

### Key Panels
1. **System Overview**: Health status, active jobs, queue size
2. **Performance Metrics**: Generation time, performance ratio, frame rate
3. **Resource Utilization**: CPU, memory, disk usage over time
4. **API Metrics**: Request rate, response times, error rates
5. **Video Generation**: Success/failure rates by effect type

### Sample Queries
```promql
# Request rate
rate(green_code_fx_http_requests_total[5m])

# Average generation time
rate(green_code_fx_video_generation_duration_seconds_sum[5m]) / rate(green_code_fx_video_generation_duration_seconds_count[5m])

# Error rate
rate(green_code_fx_video_generation_total{status="error"}[5m])

# Queue size over time
green_code_fx_queue_size
```

## Troubleshooting

### Metrics Not Available
1. Check `METRICS_ENABLED` environment variable
2. Verify prometheus-client is installed
3. Check application logs for metrics initialization errors

### High Resource Usage
1. Check active job count: `green_code_fx_active_jobs`
2. Monitor queue size: `green_code_fx_queue_size`
3. Review generation performance: `green_code_fx_performance_ratio`

### Performance Issues
1. Monitor frame generation rate: `green_code_fx_frame_generation_rate_fps`
2. Check system resources: CPU, memory, disk usage
3. Review video generation duration trends

## Log Analysis

Structured logs are available through Docker:

```bash
# View real-time logs
docker logs -f green-code-fx-generator

# Export logs for analysis
docker logs green-code-fx-generator > app.log
```

Key log events to monitor:
- Video generation start/completion
- Error conditions and exceptions
- Resource pressure warnings
- Rate limiting violations
