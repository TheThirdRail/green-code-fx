#!/usr/bin/env python3
"""
Container security scanning script for Green-Code FX.

This script performs security scans on the Docker container using Trivy
and other security tools to identify vulnerabilities.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, timeout=300):
    """Run a shell command with timeout."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout} seconds"


def install_trivy():
    """Install Trivy security scanner if not present."""
    print("🔍 Checking for Trivy installation...")
    
    success, stdout, stderr = run_command("trivy --version")
    if success:
        print(f"✅ Trivy already installed: {stdout.strip()}")
        return True
    
    print("📦 Installing Trivy...")
    
    # Try different installation methods based on OS
    install_commands = [
        # Linux (apt)
        "sudo apt-get update && sudo apt-get install -y wget apt-transport-https gnupg lsb-release && wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add - && echo 'deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main' | sudo tee -a /etc/apt/sources.list.d/trivy.list && sudo apt-get update && sudo apt-get install -y trivy",
        
        # macOS (brew)
        "brew install trivy",
        
        # Generic (download binary)
        "curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin"
    ]
    
    for cmd in install_commands:
        print(f"Trying: {cmd[:50]}...")
        success, stdout, stderr = run_command(cmd, timeout=600)
        if success:
            print("✅ Trivy installed successfully")
            return True
    
    print("❌ Failed to install Trivy automatically")
    print("Please install Trivy manually: https://aquasecurity.github.io/trivy/latest/getting-started/installation/")
    return False


def scan_container_image():
    """Scan the container image for vulnerabilities."""
    print("🔍 Scanning container image for vulnerabilities...")
    
    image_name = "green-code-fx-generator:latest"
    
    # Build the image first
    print("🔨 Building container image...")
    success, stdout, stderr = run_command("docker-compose build", timeout=600)
    if not success:
        print(f"❌ Failed to build image: {stderr}")
        return False
    
    # Run Trivy scan
    scan_cmd = f"trivy image --format json --output trivy-report.json {image_name}"
    print(f"Running: {scan_cmd}")
    
    success, stdout, stderr = run_command(scan_cmd, timeout=600)
    if not success:
        print(f"❌ Trivy scan failed: {stderr}")
        return False
    
    # Parse results
    try:
        with open("trivy-report.json", 'r') as f:
            scan_results = json.load(f)
        
        return analyze_trivy_results(scan_results)
        
    except Exception as e:
        print(f"❌ Failed to parse scan results: {e}")
        return False


def analyze_trivy_results(results):
    """Analyze Trivy scan results."""
    print("\n" + "="*60)
    print("CONTAINER SECURITY SCAN RESULTS")
    print("="*60)
    
    total_vulnerabilities = 0
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    
    if "Results" in results:
        for result in results["Results"]:
            if "Vulnerabilities" in result:
                for vuln in result["Vulnerabilities"]:
                    total_vulnerabilities += 1
                    severity = vuln.get("Severity", "UNKNOWN")
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    print(f"Total Vulnerabilities: {total_vulnerabilities}")
    print(f"  Critical: {severity_counts['CRITICAL']}")
    print(f"  High: {severity_counts['HIGH']}")
    print(f"  Medium: {severity_counts['MEDIUM']}")
    print(f"  Low: {severity_counts['LOW']}")
    print(f"  Unknown: {severity_counts['UNKNOWN']}")
    
    # Detailed critical and high vulnerabilities
    if severity_counts['CRITICAL'] > 0 or severity_counts['HIGH'] > 0:
        print(f"\n🚨 CRITICAL AND HIGH SEVERITY VULNERABILITIES:")
        
        for result in results.get("Results", []):
            for vuln in result.get("Vulnerabilities", []):
                if vuln.get("Severity") in ["CRITICAL", "HIGH"]:
                    print(f"  {vuln.get('Severity')}: {vuln.get('VulnerabilityID')} in {vuln.get('PkgName')}")
                    print(f"    Description: {vuln.get('Description', 'N/A')[:100]}...")
                    if vuln.get('FixedVersion'):
                        print(f"    Fixed in: {vuln.get('FixedVersion')}")
                    print()
    
    # Security recommendations
    print(f"\n🔧 SECURITY RECOMMENDATIONS:")
    if severity_counts['CRITICAL'] > 0:
        print(f"  - URGENT: Fix {severity_counts['CRITICAL']} critical vulnerabilities")
    if severity_counts['HIGH'] > 0:
        print(f"  - HIGH PRIORITY: Fix {severity_counts['HIGH']} high severity vulnerabilities")
    
    print(f"  - Update base image to latest security patches")
    print(f"  - Review and update all dependencies")
    print(f"  - Consider using distroless or minimal base images")
    print(f"  - Implement regular security scanning in CI/CD")
    
    # Determine pass/fail
    critical_threshold = 0  # No critical vulnerabilities allowed
    high_threshold = 5      # Max 5 high severity vulnerabilities
    
    if severity_counts['CRITICAL'] <= critical_threshold and severity_counts['HIGH'] <= high_threshold:
        print(f"\n✅ SECURITY SCAN: PASS")
        print(f"   Critical: {severity_counts['CRITICAL']}/{critical_threshold}")
        print(f"   High: {severity_counts['HIGH']}/{high_threshold}")
        return True
    else:
        print(f"\n❌ SECURITY SCAN: FAIL")
        print(f"   Critical: {severity_counts['CRITICAL']}/{critical_threshold}")
        print(f"   High: {severity_counts['HIGH']}/{high_threshold}")
        return False


def scan_dockerfile_best_practices():
    """Scan Dockerfile for security best practices."""
    print("\n🔍 Scanning Dockerfile for security best practices...")
    
    dockerfile_path = project_root / "Dockerfile"
    if not dockerfile_path.exists():
        print("❌ Dockerfile not found")
        return False
    
    with open(dockerfile_path, 'r') as f:
        dockerfile_content = f.read()
    
    issues = []
    recommendations = []
    
    # Check for security best practices
    if "USER root" in dockerfile_content or "USER 0" in dockerfile_content:
        issues.append("Running as root user")
    elif "USER " not in dockerfile_content:
        issues.append("No USER directive specified (defaults to root)")
    
    if "COPY . ." in dockerfile_content or "ADD . ." in dockerfile_content:
        issues.append("Copying entire context (use .dockerignore)")
    
    if "--no-cache-dir" not in dockerfile_content and "pip install" in dockerfile_content:
        recommendations.append("Use --no-cache-dir with pip install")
    
    if "apt-get update" in dockerfile_content and "apt-get clean" not in dockerfile_content:
        recommendations.append("Clean apt cache after package installation")
    
    if "EXPOSE" not in dockerfile_content:
        recommendations.append("Explicitly EXPOSE required ports")
    
    # Report results
    if issues:
        print("🚨 SECURITY ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    
    if recommendations:
        print("💡 RECOMMENDATIONS:")
        for rec in recommendations:
            print(f"  - {rec}")
    
    if not issues and not recommendations:
        print("✅ No obvious security issues found in Dockerfile")
        return True
    
    return len(issues) == 0  # Pass if no critical issues


def main():
    """Main security scanning workflow."""
    print("Green-Code FX Container Security Scanner")
    print("=" * 60)
    
    try:
        # Install Trivy if needed
        if not install_trivy():
            return 1
        
        # Scan Dockerfile
        dockerfile_ok = scan_dockerfile_best_practices()
        
        # Scan container image
        container_ok = scan_container_image()
        
        # Generate summary
        print("\n" + "="*60)
        print("SECURITY SCAN SUMMARY")
        print("="*60)
        
        if dockerfile_ok and container_ok:
            print("✅ All security scans PASSED")
            print("   Container meets security requirements")
            return 0
        else:
            print("❌ Security scans FAILED")
            if not dockerfile_ok:
                print("   Dockerfile has security issues")
            if not container_ok:
                print("   Container has critical vulnerabilities")
            print("   Review and fix issues before production deployment")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Security scan interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Security scan failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
