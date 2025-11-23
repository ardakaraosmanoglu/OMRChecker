# OMR Checker Flask API

A RESTful API for processing OMR (Optical Mark Recognition) sheets.

## Quick Start

### 1. Install Dependencies

```bash
cd OMRChecker
pip install -r requirements.txt
```

Required packages:
- Flask >= 3.0.0
- flask-cors >= 4.0.0
- opencv-python >= 4.8.0
- numpy >= 1.25.0
- pandas >= 2.0.2
- And other dependencies from requirements.txt

### 2. Start the API Server

**Option A: Using the startup script**
```bash
./start_api.sh
```

**Option B: Using Python directly**
```bash
python -m api.app
```

The API will start on `http://localhost:8080`

### 3. Test the API

**Health Check:**
```bash
curl http://localhost:8080/api/health
```

**Run Test Suite:**
```bash
python test_api.py
```

## API Endpoints

### Health Check
```
GET /api/health
```

### Process OMR Images
```
POST /api/omr/process
```

**Two input methods supported:**

1. **File Upload (multipart/form-data)**
   - Upload images and configs directly
   - See examples in `API_USAGE.md`

2. **Directory Path (JSON)**
   - Process images from a directory on the server
   - Directory must contain `template.json` and image files

### Validate Template
```
POST /api/omr/validate-template
```

Validate template.json structure before processing.

## Directory Structure

```
OMRChecker/
├── api/
│   ├── app.py              # Flask application
│   ├── routes.py           # API endpoints
│   ├── utils.py            # Helper functions
│   ├── defaults/           # Default configs
│   │   ├── template.json
│   │   └── config.json
│   └── temp_uploads/       # Temporary upload directory
├── src/
│   ├── api_adapter.py      # Adapter for API mode
│   └── ...                 # Other OMRChecker modules
├── inputs/                 # Example input directory
│   ├── template.json
│   ├── config.json
│   ├── omr_marker.jpg
│   └── *.jpg               # OMR sheet images
├── API_USAGE.md           # Detailed API usage guide
├── API_README.md          # This file
├── test_api.py            # API test script
└── start_api.sh           # Startup script
```

## Usage Examples

### Python Example

```python
import requests

url = "http://localhost:8080/api/omr/process"

# Method 1: File upload
files = {
    'image': open('omr_sheet.jpg', 'rb'),
    'template': open('api/defaults/template.json', 'rb')
}
response = requests.post(url, files=files)
result = response.json()
print(result['response'])

# Method 2: Directory path
data = {"directory": "/path/to/inputs"}
response = requests.post(url, json=data)
result = response.json()
print(result['results'])
```

### cURL Example

```bash
# File upload
curl -X POST http://localhost:8080/api/omr/process \
  -F "image=@omr_sheet.jpg" \
  -F "template=@api/defaults/template.json"

# Directory path
curl -X POST http://localhost:8080/api/omr/process \
  -H "Content-Type: application/json" \
  -d '{"directory": "/path/to/inputs"}'
```

## Configuration

### Template Configuration

Define your OMR sheet layout in `template.json`:

```json
{
  "pageDimensions": [1240, 1754],
  "bubbleDimensions": [18, 18],
  "fieldBlocks": {
    "MCQBlock1": {
      "fieldType": "QTYPE_MCQ5",
      "origin": [100, 465],
      "fieldLabels": ["q1..40"],
      "bubblesGap": 47,
      "labelsGap": 31.1
    }
  }
}
```

### Processing Configuration

Adjust processing parameters in `config.json`:

```json
{
  "dimensions": {
    "processing_width": 1240,
    "processing_height": 1754
  },
  "threshold_params": {
    "MIN_JUMP": 10
  }
}
```

## Features

- ✅ File upload support (multipart/form-data)
- ✅ Directory path processing
- ✅ Single and batch image processing
- ✅ Template validation
- ✅ JSON and CSV output formats
- ✅ Processed image output (base64)
- ✅ Auto-alignment support
- ✅ CORS enabled
- ✅ Error handling with proper HTTP status codes

## API Response Format

### Success Response
```json
{
  "status": "success",
  "file_name": "omr_sheet.jpg",
  "response": {
    "q1": "A",
    "q2": "B",
    "...": "..."
  },
  "metadata": {
    "multi_marked": false,
    "multi_marked_count": 0,
    "image_dimensions": [1754, 1240]
  },
  "processing_time": 2.34
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description",
  "processing_time": 0.12
}
```

## Advanced Options

### Include Processed Image

Add `include_image=true` to get the processed image in response:

```bash
curl -X POST http://localhost:8080/api/omr/process \
  -F "image=@omr_sheet.jpg" \
  -F "template=@api/defaults/template.json" \
  -F "include_image=true"
```

Response will include:
```json
{
  "processed_image": "base64_encoded_image_string"
}
```

### Download as CSV

Add `?format=csv` to download results as CSV:

```bash
curl -X POST "http://localhost:5000/api/omr/process?format=csv" \
  -F "image=@sheet1.jpg" \
  -F "template=@api/defaults/template.json" \
  -o results.csv
```

### Enable Auto-Alignment

For scanned or photographed images with slight misalignment:

```bash
curl -X POST http://localhost:8080/api/omr/process \
  -F "image=@omr_sheet.jpg" \
  -F "template=@api/defaults/template.json" \
  -F "auto_align=true"
```

## Troubleshooting

### ImportError: No module named 'flask'

Install dependencies:
```bash
pip install -r requirements.txt
```

### Connection Refused

Make sure the API server is running:
```bash
python -m api.app
```

### Template Validation Errors

Use the validation endpoint to check your template:
```bash
curl -X POST http://localhost:5000/api/omr/validate-template \
  -F "template=@your_template.json"
```

### Multi-marked Responses

Check the `metadata.multi_marked` field in the response. Adjust threshold parameters in config.json if needed.

## Documentation

- **API_USAGE.md** - Detailed API usage examples
- **Main OMRChecker Docs** - https://github.com/Udayraj123/OMRChecker

## Support

For issues with the API, please check:
1. Server logs for detailed error messages
2. Template validation using the validation endpoint
3. Test script output: `python test_api.py`

For OMRChecker core functionality issues, refer to the main repository.
