# Green-Code FX API Documentation

This document provides comprehensive documentation for the Green-Code FX video effects generator API, including all endpoints, parameters, and usage examples.

## Base URL

```
http://localhost:8082
```

## Authentication

Currently, no authentication is required. The API uses rate limiting to prevent abuse.

## Rate Limiting

- **Limit**: 100 requests per hour per IP address
- **Headers**: Rate limit information is included in response headers
- **Endpoint**: `/api/rate-limit` to check current status

## Content Types

The API supports both JSON and multipart form data:
- **JSON**: `application/json` for simple requests
- **Multipart**: `multipart/form-data` for file uploads

---

## Endpoints

### 1. Health Check

Check the health and status of the service.

**Endpoint**: `GET /api/health`

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "active_jobs": 1,
  "queue_length": 0,
  "disk_space": "15.2GB available",
  "timestamp": "2024-06-15T10:30:00Z"
}
```

**Status Codes**:
- `200 OK`: Service is healthy
- `500 Internal Server Error`: Service is unhealthy

---

### 2. Generate Typing Effect

Create a typing code effect video with customizable parameters.

**Endpoint**: `POST /api/generate/typing`

#### Request Parameters

| Parameter | Type | Required | Description | Default | Validation |
|-----------|------|----------|-------------|---------|------------|
| `duration` | integer | Yes | Video duration in seconds | - | 10-600 |
| `font_family` | string | No | Font family identifier | "jetbrains" | Available fonts |
| `font_size` | integer | No | Font size in pixels | 32 | 12-72 |
| `text_color` | string | No | Text color in hex format | "#00FF00" | Valid hex color |
| `custom_text` | string | No | Custom text content | null | Max 50,000 chars |
| `text_file` | file | No | Text file upload (.txt only) | null | Max 10MB, .txt only |
| `output_format` | string | No | Output video format | "mp4" | "mp4" |

#### Usage Examples

**Basic Request (JSON)**:
```bash
curl -X POST http://localhost:8082/api/generate/typing \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 90,
    "output_format": "mp4"
  }'
```

**Enhanced Request with Custom Text (JSON)**:
```bash
curl -X POST http://localhost:8082/api/generate/typing \
  -H "Content-Type: application/json" \
  -d '{
    "duration": 60,
    "font_family": "jetbrains",
    "font_size": 28,
    "text_color": "#FF0000",
    "custom_text": "def hello_world():\n    print(\"Hello, World!\")\n    return True",
    "output_format": "mp4"
  }'
```

**File Upload Request (Multipart)**:
```bash
curl -X POST http://localhost:8082/api/generate/typing \
  -F "duration=45" \
  -F "font_family=jetbrains" \
  -F "font_size=32" \
  -F "text_color=#00FF00" \
  -F "text_file=@my_code.txt" \
  -F "output_format=mp4"
```

#### Response

**Success Response** (`202 Accepted`):
```json
{
  "job_id": "typing_20240615_143022",
  "status": "queued",
  "estimated_duration": "45s",
  "message": "Video generation job queued successfully"
}
```

**Error Responses**:

`400 Bad Request` - Invalid parameters:
```json
{
  "error": "Invalid duration: must be between 10 and 600 seconds",
  "code": "INVALID_PARAMETER"
}
```

`400 Bad Request` - Conflicting parameters:
```json
{
  "error": "Cannot specify both custom_text and text_file",
  "code": "CONFLICTING_PARAMETERS"
}
```

`413 Payload Too Large` - File too large:
```json
{
  "error": "File size exceeds maximum limit of 10MB",
  "code": "FILE_TOO_LARGE"
}
```

`415 Unsupported Media Type` - Invalid file type:
```json
{
  "error": "Only .txt files are allowed",
  "code": "INVALID_FILE_TYPE"
}
```

`429 Too Many Requests` - Rate limit exceeded:
```json
{
  "error": "Rate limit exceeded. Try again later.",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 3600
}
```

---

### 3. List Available Fonts

Get a list of available fonts for the typing effect.

**Endpoint**: `GET /api/fonts`

**Response**:
```json
{
  "fonts": [
    {
      "id": "jetbrains",
      "name": "JetBrains Mono",
      "type": "bundled"
    }
  ],
  "default": "jetbrains"
}
```

**Status Codes**:
- `200 OK`: Fonts retrieved successfully
- `500 Internal Server Error`: Failed to retrieve fonts

---

### 4. Check Job Status

Get the current status and progress of a video generation job.

**Endpoint**: `GET /api/jobs/{job_id}`

**Path Parameters**:
- `job_id`: The unique identifier returned when creating a job

**Response**:

**In Progress** (`200 OK`):
```json
{
  "job_id": "typing_20240615_143022",
  "status": "running",
  "progress": 45,
  "estimated_remaining": "30s",
  "created_at": "2024-06-15T14:30:22Z",
  "started_at": "2024-06-15T14:30:25Z"
}
```

**Completed** (`200 OK`):
```json
{
  "job_id": "typing_20240615_143022",
  "status": "completed",
  "progress": 100,
  "output_file": "/api/download/typing_20240615_143022.mp4",
  "file_size": "245MB",
  "duration": "90s",
  "created_at": "2024-06-15T14:30:22Z",
  "started_at": "2024-06-15T14:30:25Z",
  "completed_at": "2024-06-15T14:32:10Z"
}
```

**Failed** (`200 OK`):
```json
{
  "job_id": "typing_20240615_143022",
  "status": "failed",
  "progress": 0,
  "error": "Font file not found",
  "created_at": "2024-06-15T14:30:22Z",
  "started_at": "2024-06-15T14:30:25Z",
  "failed_at": "2024-06-15T14:30:30Z"
}
```

**Status Codes**:
- `200 OK`: Job status retrieved successfully
- `404 Not Found`: Job not found

---

### 5. Download Generated Video

Download a completed video file.

**Endpoint**: `GET /api/download/{filename}`

**Path Parameters**:
- `filename`: The filename returned in the job completion response

**Response**:
- **Success**: Binary video file with appropriate headers
- **Headers**:
  - `Content-Type`: `video/mp4`
  - `Content-Disposition`: `attachment; filename="video.mp4"`
  - `Content-Length`: File size in bytes

**Status Codes**:
- `200 OK`: File downloaded successfully
- `404 Not Found`: File not found
- `410 Gone`: File has been cleaned up

---

### 6. Rate Limit Status

Check current rate limit status for the requesting client.

**Endpoint**: `GET /api/rate-limit`

**Response**:
```json
{
  "requests_remaining": 95,
  "requests_limit": 100,
  "reset_time": "2024-06-15T15:30:00Z",
  "retry_after": null
}
```

**Status Codes**:
- `200 OK`: Rate limit status retrieved successfully

---

### 7. System Resources

Get current system resource status and queue information.

**Endpoint**: `GET /api/resources`

**Response**:
```json
{
  "cpu_usage": 45.2,
  "memory_usage": 67.8,
  "disk_usage": 23.1,
  "active_jobs": 1,
  "queue_length": 2,
  "max_concurrent_jobs": 2,
  "uptime": "2d 14h 32m"
}
```

**Status Codes**:
- `200 OK`: Resource status retrieved successfully
- `500 Internal Server Error`: Failed to retrieve resource status

---

## Error Handling

### Error Response Format

All error responses follow this format:
```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `INVALID_PARAMETER` | One or more parameters are invalid |
| `MISSING_PARAMETER` | Required parameter is missing |
| `CONFLICTING_PARAMETERS` | Mutually exclusive parameters provided |
| `FILE_TOO_LARGE` | Uploaded file exceeds size limit |
| `INVALID_FILE_TYPE` | Uploaded file type not allowed |
| `RATE_LIMIT_EXCEEDED` | Too many requests from client |
| `INTERNAL_ERROR` | Server-side error occurred |
| `JOB_NOT_FOUND` | Requested job does not exist |
| `FILE_NOT_FOUND` | Requested file does not exist |

---

## Best Practices

### 1. Polling Job Status

When checking job status, use exponential backoff:
```bash
# Initial check after 5 seconds
sleep 5
curl http://localhost:8082/api/jobs/{job_id}

# Then check every 10 seconds
while [ "$status" != "completed" ] && [ "$status" != "failed" ]; do
  sleep 10
  response=$(curl -s http://localhost:8082/api/jobs/{job_id})
  status=$(echo $response | jq -r '.status')
done
```

### 2. File Upload Validation

Always validate files before uploading:
- Check file extension is `.txt`
- Verify file size is under 10MB
- Ensure file contains valid text content

### 3. Error Handling

Implement proper error handling for all API calls:
```bash
response=$(curl -s -w "%{http_code}" http://localhost:8082/api/generate/typing ...)
http_code="${response: -3}"
body="${response%???}"

if [ "$http_code" -eq 202 ]; then
  echo "Job created successfully"
elif [ "$http_code" -eq 400 ]; then
  echo "Bad request: $body"
elif [ "$http_code" -eq 429 ]; then
  echo "Rate limited. Retry after: $(echo $body | jq -r '.retry_after')"
fi
```

### 4. Rate Limiting

Respect rate limits and implement backoff:
- Check rate limit headers in responses
- Use `/api/rate-limit` endpoint to check status
- Implement exponential backoff when rate limited

---

## SDK Examples

### Python Example

```python
import requests
import time
import json

class GreenCodeFXClient:
    def __init__(self, base_url="http://localhost:8082"):
        self.base_url = base_url
    
    def generate_typing_video(self, duration, custom_text=None, **kwargs):
        """Generate a typing effect video."""
        data = {"duration": duration, **kwargs}
        if custom_text:
            data["custom_text"] = custom_text
        
        response = requests.post(
            f"{self.base_url}/api/generate/typing",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def check_job_status(self, job_id):
        """Check the status of a job."""
        response = requests.get(f"{self.base_url}/api/jobs/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, job_id, timeout=3600):
        """Wait for a job to complete."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.check_job_status(job_id)
            if status["status"] == "completed":
                return status
            elif status["status"] == "failed":
                raise Exception(f"Job failed: {status.get('error')}")
            time.sleep(10)
        raise TimeoutError("Job did not complete within timeout")

# Usage
client = GreenCodeFXClient()
job = client.generate_typing_video(
    duration=60,
    custom_text="print('Hello, World!')",
    font_size=32,
    text_color="#00FF00"
)
result = client.wait_for_completion(job["job_id"])
print(f"Video ready: {result['output_file']}")
```

---

For more information, see the [User Guide](USER_GUIDE.md) and [Troubleshooting Guide](TROUBLESHOOTING.md).
