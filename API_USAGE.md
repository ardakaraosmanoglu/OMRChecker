# OMR Checker API Usage Guide

This guide explains how to use the OMR Checker Flask API to process OMR (Optical Mark Recognition) sheets.

## Table of Contents
- [Installation](#installation)
- [Starting the API Server](#starting-the-api-server)
- [API Endpoints](#api-endpoints)
- [Examples](#examples)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have the following Python packages installed:
   - Flask
   - flask-cors
   - opencv-python
   - numpy
   - pandas

## Starting the API Server

Run the Flask API server:

```bash
cd OMRChecker
python -m api.app
```

The API will start on `http://localhost:8080`

## API Endpoints

### 1. Health Check
**GET** `/api/health`

Check if the API is running.

```bash
curl http://localhost:8080/api/health
```

Response:
```json
{
  "status": "healthy",
  "service": "OMR Checker API"
}
```

### 2. Process OMR Images
**POST** `/api/omr/process`

Process single or multiple OMR images.

#### Method 1: File Upload (multipart/form-data)

Upload images and configuration files directly.

**Parameters:**
- `image` (required): OMR image file(s) - PNG/JPG/JPEG
- `template` (required): Template JSON file or JSON string in form field
- `config` (optional): Config JSON file or JSON string in form field
- `marker` (optional): Marker image file for CropOnMarkers preprocessor
- `include_image` (optional): "true" to include processed image in response
- `auto_align` (optional): "true" to enable automatic alignment
- `format` (optional): "csv" to download results as CSV

**Example: Single Image Upload**
```bash
curl -X POST http://localhost:8080/api/omr/process \
  -F "image=@/path/to/omr_sheet.jpg" \
  -F "template=@api/defaults/template.json" \
  -F "config=@api/defaults/config.json" \
  -F "marker=@inputs/omr_marker.jpg" \
  -F "include_image=true"
```

**Example: Multiple Images Upload**
```bash
curl -X POST http://localhost:8080/api/omr/process \
  -F "image=@sheet1.jpg" \
  -F "image=@sheet2.jpg" \
  -F "image=@sheet3.jpg" \
  -F "template=@api/defaults/template.json"
```

**Example: Using JSON String Instead of File**
```bash
curl -X POST http://localhost:8080/api/omr/process \
  -F "image=@omr_sheet.jpg" \
  -F 'template={"pageDimensions":[1240,1754],"bubbleDimensions":[18,18],"fieldBlocks":{...}}'
```

#### Method 2: Directory Path (JSON)

Process images from a directory on the server.

**JSON Body:**
```json
{
  "directory": "/path/to/input/directory",
  "include_image": false,
  "auto_align": false
}
```

**Example:**
```bash
curl -X POST http://localhost:8080/api/omr/process \
  -H "Content-Type: application/json" \
  -d '{
    "directory": "/Users/raxana/Documents/Projects/omr-beyso/OMRChecker/inputs",
    "include_image": true
  }'
```

**Response (Single Image):**
```json
{
  "status": "success",
  "file_name": "omr_sheet.jpg",
  "response": {
    "q1": "A",
    "q2": "B",
    "q3": "C",
    "q4": "D",
    "...": "..."
  },
  "raw_response": {
    "q1": ["A"],
    "q2": ["B"],
    "...": "..."
  },
  "metadata": {
    "multi_marked": false,
    "multi_roll": false,
    "multi_marked_count": 0,
    "image_dimensions": [1754, 1240]
  },
  "processed_image": "base64_encoded_image_string",
  "processing_time": 2.34
}
```

**Response (Multiple Images):**
```json
{
  "status": "success",
  "total": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "status": "success",
      "file_name": "sheet1.jpg",
      "response": {...}
    },
    {
      "status": "success",
      "file_name": "sheet2.jpg",
      "response": {...}
    }
  ],
  "processing_time": 5.67
}
```

### 3. Batch Process
**POST** `/api/omr/batch`

Same as `/api/omr/process` but optimized for batch operations.

### 4. Validate Template
**POST** `/api/omr/validate-template`

Validate a template.json structure before processing.

**Example (JSON Body):**
```bash
curl -X POST http://localhost:5000/api/omr/validate-template \
  -H "Content-Type: application/json" \
  -d @api/defaults/template.json
```

**Example (File Upload):**
```bash
curl -X POST http://localhost:5000/api/omr/validate-template \
  -F "template=@api/defaults/template.json"
```

**Response:**
```json
{
  "status": "success",
  "valid": true,
  "errors": [],
  "warnings": []
}
```

## Examples

### Python Example

```python
import requests
import json

# API endpoint
url = "http://localhost:8080/api/omr/process"

# Prepare files
files = {
    'image': open('omr_sheet.jpg', 'rb'),
    'template': open('api/defaults/template.json', 'rb'),
    'marker': open('inputs/omr_marker.jpg', 'rb')
}

# Prepare form data
data = {
    'include_image': 'true',
    'auto_align': 'false'
}

# Make request
response = requests.post(url, files=files, data=data)

# Parse response
result = response.json()
print(f"Status: {result['status']}")
print(f"Responses: {result['response']}")
```

### JavaScript Example

```javascript
const formData = new FormData();
formData.append('image', fileInput.files[0]);
formData.append('template', templateFile);
formData.append('include_image', 'true');

fetch('http://localhost:8080/api/omr/process', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('Responses:', data.response);
  if (data.processed_image) {
    // Display processed image
    const img = document.createElement('img');
    img.src = 'data:image/png;base64,' + data.processed_image;
    document.body.appendChild(img);
  }
})
.catch(error => console.error('Error:', error));
```

### Download Results as CSV

Add `?format=csv` to the URL or include `format=csv` in form data:

```bash
curl -X POST "http://localhost:5000/api/omr/process?format=csv" \
  -F "image=@sheet1.jpg" \
  -F "image=@sheet2.jpg" \
  -F "template=@api/defaults/template.json" \
  -o results.csv
```

## Template Configuration

The template.json file defines the layout of your OMR sheet. Here's the structure:

```json
{
  "pageDimensions": [1240, 1754],
  "bubbleDimensions": [18, 18],
  "preProcessors": [
    {
      "name": "CropOnMarkers",
      "options": {
        "relativePath": "omr_marker.jpg",
        "sheetToMarkerWidthRatio": 17
      }
    }
  ],
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

**Key Fields:**
- `pageDimensions`: [width, height] of the OMR sheet
- `bubbleDimensions`: [width, height] of each bubble
- `preProcessors`: Image preprocessing steps
- `fieldBlocks`: Define question blocks with positions and types

**Field Types:**
- `QTYPE_MCQ4`: Multiple choice with 4 options (A, B, C, D)
- `QTYPE_MCQ5`: Multiple choice with 5 options (A, B, C, D, E)
- `QTYPE_INT`: Integer field (for roll numbers, etc.)

## Config Configuration

The config.json file contains processing parameters:

```json
{
  "dimensions": {
    "processing_width": 1240,
    "processing_height": 1754
  },
  "threshold_params": {
    "MIN_JUMP": 10
  },
  "outputs": {
    "show_image_level": 0
  }
}
```

## Error Handling

All endpoints return proper HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid input)
- `413`: File Too Large (>50MB)
- `500`: Server Error

Error response format:
```json
{
  "status": "error",
  "message": "Error description",
  "processing_time": 0.12
}
```

## Tips

1. **Marker Image**: If using `CropOnMarkers` preprocessor, always include the marker image
2. **Image Quality**: Higher quality images yield better results
3. **Template Accuracy**: Ensure template coordinates match your physical OMR sheet
4. **Auto Align**: Enable auto_align for photographed/scanned images with slight misalignment
5. **Batch Processing**: For multiple images, use batch endpoint for better performance

## Troubleshooting

**Issue: "Failed to decode image"**
- Ensure image is valid PNG/JPG/JPEG format
- Check file is not corrupted

**Issue: "Template validation failed"**
- Use `/api/omr/validate-template` endpoint to check template structure
- Ensure all required fields are present

**Issue: "Multi-marked responses"**
- Check bubble detection parameters in config
- Verify image quality and clarity
- Review threshold_params values

## Support

For issues and questions, refer to the main OMRChecker documentation:
https://github.com/Udayraj123/OMRChecker
