# Green-Code FX Performance Benchmarking Guide

This document provides comprehensive guidance for performance benchmarking of the Green-Code FX video effects generator, specifically focusing on typing effect generation speed analysis.

## Overview

The performance benchmarking system provides detailed analysis of video generation performance to ensure compliance with PRD requirements (≤2x realtime generation speed) and identify optimization opportunities.

## System Components

### 1. Performance Profiler (`src/performance_profiler.py`)

The core profiling system that measures individual pipeline stages:

- **PerformanceProfiler**: Main profiling class with operation timing
- **ProfileResult**: Individual operation timing results
- **Global profiler instance**: Integrated throughout the video generation pipeline

### 2. Performance Tests (`tests/test_performance.py`)

Comprehensive test suite for performance validation:

- **PerformanceBenchmark**: Utility class for test timing and analysis
- **TestTypingEffectPerformance**: Main test class with multiple scenarios
- **Bottleneck Analysis**: Detailed pipeline stage analysis

### 3. Test Runners

Multiple ways to execute performance benchmarks:

- **`scripts/simple_performance_test.py`**: Standalone performance testing
- **`scripts/run_performance_tests.py`**: Pytest-based test execution
- **`scripts/check_performance_integration.py`**: Integration validation

## Performance Requirements

Based on PRODUCT_REQUIREMENTS.md:

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Typing Effect Speed | ≤2.0x realtime | Multiple file sizes (50-500 lines) |
| API Response Time | <500ms | Job submission timing |
| Container Startup | <30 seconds | Health check timing |

## Usage Instructions

### Prerequisites

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure Docker Environment** (if testing in container):
   ```bash
   docker-compose build
   docker-compose up -d
   ```

### Running Performance Tests

#### Option 1: Simple Standalone Test

```bash
python scripts/simple_performance_test.py
```

**Features:**
- Tests small (50 lines), medium (200 lines), and large (500 lines) source files
- Detailed bottleneck analysis with pipeline stage breakdown
- Automatic report generation and file saving
- No external test framework dependencies

#### Option 2: Pytest-based Testing

```bash
python scripts/run_performance_tests.py
```

**Features:**
- Full pytest integration with fixtures and parameterization
- Comprehensive test coverage with statistical analysis
- Detailed error reporting and test isolation
- Integration with CI/CD pipelines

#### Option 3: Manual Integration Testing

```bash
python -m pytest tests/test_performance.py -v -s
```

**Features:**
- Individual test execution
- Verbose output with detailed timing
- Custom test parameterization

### Interpreting Results

#### Performance Metrics

**Generation Ratio**: `generation_time / video_duration`
- **Target**: ≤2.0x realtime
- **Example**: 10s video generated in 15s = 1.5x realtime ✅

**Pipeline Breakdown**: Percentage of total time per operation
- **Main Rendering Loop**: Typically 60-80% of total time
- **Frame Saving**: Usually 10-20% of total time
- **Font Loading**: Should be <5% of total time
- **Video Assembly**: Varies by output format

#### Sample Output

```
PERFORMANCE SUMMARY:
  Total Time: 12.345s
  Ratio: 1.23x realtime
  Requirement: ≤2.0x realtime
  Status: PASS

PIPELINE BREAKDOWN:
  main_rendering_loop: 75.2% (9.284s)
  save_frame: 18.1% (2.234s)
  video_assembly: 4.2% (0.518s)
  load_font: 1.8% (0.222s)
  load_source_file: 0.7% (0.087s)
```

### Generated Reports

The benchmarking system generates several types of reports:

#### 1. Text Reports
- **Location**: `output/typing_effect_performance_report.txt`
- **Content**: Human-readable performance summary
- **Use Case**: Quick performance overview and sharing

#### 2. Detailed Analysis Reports
- **Location**: `output/typing_effect_bottleneck_analysis.txt`
- **Content**: Comprehensive pipeline analysis with recommendations
- **Use Case**: Optimization planning and bottleneck identification

#### 3. JSON Data Files
- **Location**: `output/typing_effect_bottleneck_data.json`
- **Content**: Raw timing data and structured analysis
- **Use Case**: Further analysis, visualization, and automation

## Performance Optimization Guide

### Common Bottlenecks

1. **Main Rendering Loop (>80% of time)**
   - **Cause**: Excessive pygame operations per frame
   - **Solutions**: 
     - Cache text surfaces for repeated characters
     - Optimize drawing operations
     - Reduce unnecessary screen updates

2. **Frame Saving (>25% of time)**
   - **Cause**: PNG compression overhead
   - **Solutions**:
     - Use faster image formats for intermediate frames
     - Implement parallel frame saving
     - Optimize disk I/O operations

3. **Font Loading (>10% of time)**
   - **Cause**: Repeated font initialization
   - **Solutions**:
     - Implement font caching
     - Preload fonts during initialization
     - Use system fonts when possible

### Optimization Strategies

#### 1. Rendering Optimizations
```python
# Cache text surfaces to avoid repeated rendering
text_cache = {}
def get_cached_text(text, font, color):
    key = (text, id(font), color)
    if key not in text_cache:
        text_cache[key] = font.render(text, True, color)
    return text_cache[key]
```

#### 2. I/O Optimizations
```python
# Use threading for frame saving
import threading
from queue import Queue

def async_frame_saver(frame_queue):
    while True:
        frame_data = frame_queue.get()
        if frame_data is None:
            break
        pygame.image.save(frame_data['surface'], frame_data['path'])
        frame_queue.task_done()
```

#### 3. Memory Optimizations
```python
# Limit memory usage for large videos
MAX_CACHED_SURFACES = 100
if len(text_cache) > MAX_CACHED_SURFACES:
    text_cache.clear()  # Simple cache eviction
```

## Continuous Performance Monitoring

### CI/CD Integration

Add performance tests to your CI/CD pipeline:

```yaml
# .github/workflows/performance.yml
name: Performance Tests
on: [push, pull_request]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run performance tests
        run: python scripts/simple_performance_test.py
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: performance-reports
          path: output/*.txt
```

### Performance Regression Detection

Monitor performance trends over time:

```bash
# Compare current performance with baseline
python scripts/compare_performance.py \
  --baseline output/baseline_performance.json \
  --current output/current_performance.json \
  --threshold 0.1  # 10% regression threshold
```

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'pygame'"**
   - **Solution**: Install dependencies with `pip install -r requirements.txt`

2. **"SDL_VIDEODRIVER not set"**
   - **Solution**: Ensure headless mode with `export SDL_VIDEODRIVER=dummy`

3. **Performance tests timeout**
   - **Solution**: Increase timeout values or reduce test duration

4. **Inconsistent performance results**
   - **Solution**: Run multiple iterations and use statistical analysis

### Debug Mode

Enable detailed profiling output:

```python
from src.performance_profiler import profiler

# Enable verbose profiling
profiler.enabled = True
profiler.reset()

# Your video generation code here

# Generate detailed report
report = profiler.generate_report(include_raw_data=True)
print(report)
```

## Best Practices

1. **Consistent Test Environment**: Always test in the same environment (container vs native)
2. **Multiple Iterations**: Run tests multiple times and average results
3. **Baseline Establishment**: Create performance baselines for regression detection
4. **Regular Monitoring**: Include performance tests in regular development workflow
5. **Documentation**: Document performance changes and optimization decisions

## Future Enhancements

Planned improvements to the benchmarking system:

- **GPU Performance Monitoring**: Track GPU utilization during rendering
- **Memory Profiling**: Detailed memory usage analysis
- **Network Performance**: API response time monitoring
- **Comparative Analysis**: Performance comparison across different configurations
- **Automated Optimization**: AI-driven performance optimization suggestions

---

For questions or issues with performance benchmarking, refer to the troubleshooting section or check the generated reports for detailed analysis.
