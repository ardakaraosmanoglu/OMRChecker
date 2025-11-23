#!/usr/bin/env python3
"""
Test script for OMR Checker API
Run this after starting the API server with: python -m api.app
"""

import requests
import json
import os
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8080"

def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()['status'] == 'healthy'
    print("✓ Health check passed")


def test_validate_template():
    """Test template validation endpoint"""
    print("\n=== Testing Template Validation ===")

    template_path = "api/defaults/template.json"

    if not os.path.exists(template_path):
        print(f"✗ Template file not found: {template_path}")
        return

    with open(template_path, 'rb') as f:
        files = {'template': f}
        response = requests.post(f"{BASE_URL}/api/omr/validate-template", files=files)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✓ Template validation passed")


def test_process_with_directory():
    """Test processing with directory path"""
    print("\n=== Testing Directory Path Processing ===")

    input_dir = "inputs"

    if not os.path.exists(input_dir):
        print(f"✗ Input directory not found: {input_dir}")
        return

    # Check if required files exist
    required_files = ['template.json', 'config.json']
    missing_files = [f for f in required_files if not os.path.exists(os.path.join(input_dir, f))]

    if missing_files:
        print(f"✗ Missing required files in {input_dir}: {missing_files}")
        return

    # Get image files
    image_files = list(Path(input_dir).glob("*.jpg")) + list(Path(input_dir).glob("*.png"))
    image_files = [f for f in image_files if 'marker' not in f.name.lower()]

    if not image_files:
        print(f"✗ No image files found in {input_dir}")
        return

    print(f"Found {len(image_files)} image(s) in {input_dir}")

    data = {
        "directory": os.path.abspath(input_dir),
        "include_image": False,
        "auto_align": False
    }

    response = requests.post(
        f"{BASE_URL}/api/omr/process",
        json=data,
        headers={'Content-Type': 'application/json'}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Total Images: {result.get('total', 1)}")
        print(f"Successful: {result.get('successful', 1)}")
        print(f"Failed: {result.get('failed', 0)}")
        print(f"Processing Time: {result.get('processing_time')} seconds")

        # Show first result
        if 'results' in result and result['results']:
            first_result = result['results'][0]
            print(f"\nFirst Result:")
            print(f"  File: {first_result['file_name']}")
            print(f"  Status: {first_result['status']}")
            if first_result['status'] == 'success':
                print(f"  Responses: {list(first_result['response'].items())[:5]}...")
        elif 'response' in result:
            print(f"\nResult:")
            print(f"  File: {result['file_name']}")
            print(f"  Responses: {list(result['response'].items())[:5]}...")

        print("✓ Directory processing passed")
    else:
        print(f"✗ Request failed: {response.text}")


def test_process_with_file_upload():
    """Test processing with file upload"""
    print("\n=== Testing File Upload Processing ===")

    # Find image file
    input_dir = "inputs"
    image_files = list(Path(input_dir).glob("*.jpg")) + list(Path(input_dir).glob("*.png"))
    image_files = [f for f in image_files if 'marker' not in f.name.lower()]

    if not image_files:
        print(f"✗ No image files found in {input_dir}")
        return

    image_file = image_files[0]
    template_file = "api/defaults/template.json"
    config_file = "api/defaults/config.json"
    marker_file = os.path.join(input_dir, "omr_marker.jpg")

    print(f"Using image: {image_file}")

    files = {
        'image': open(image_file, 'rb'),
        'template': open(template_file, 'rb'),
        'config': open(config_file, 'rb')
    }

    # Add marker if exists
    if os.path.exists(marker_file):
        files['marker'] = open(marker_file, 'rb')
        print(f"Using marker: {marker_file}")

    data = {
        'include_image': 'false',
        'auto_align': 'false'
    }

    response = requests.post(
        f"{BASE_URL}/api/omr/process",
        files=files,
        data=data
    )

    # Close files
    for f in files.values():
        f.close()

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"File: {result['file_name']}")
        print(f"Status: {result['status']}")
        print(f"Processing Time: {result.get('processing_time')} seconds")

        if result['status'] == 'success':
            print(f"Multi-marked: {result['metadata']['multi_marked']}")
            print(f"Responses (first 10):")
            for i, (q, ans) in enumerate(list(result['response'].items())[:10]):
                print(f"  {q}: {ans}")
            print("✓ File upload processing passed")
        else:
            print(f"✗ Processing failed: {result.get('message')}")
    else:
        print(f"✗ Request failed: {response.text}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("OMR Checker API Test Suite")
    print("=" * 60)
    print("\nMake sure the API server is running:")
    print("  python -m api.app")
    print("")

    try:
        # Test 1: Health check
        test_health_check()

        # Test 2: Validate template
        test_validate_template()

        # Test 3: Process with directory path
        test_process_with_directory()

        # Test 4: Process with file upload
        test_process_with_file_upload()

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to API server")
        print("Make sure the server is running: python -m api.app")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
