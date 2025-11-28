"""
Utility functions for Flask API
"""

import os
import json
import base64
from io import BytesIO, StringIO
from werkzeug.utils import secure_filename
from flask import send_file
import pandas as pd
import cv2
import numpy as np


ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
ALLOWED_JSON_EXTENSIONS = {'json'}


def allowed_file(filename, extensions=None):
    """
    Check if file has allowed extension

    Args:
        filename: Name of the file
        extensions: Set of allowed extensions (default: ALLOWED_IMAGE_EXTENSIONS)

    Returns:
        Boolean indicating if file is allowed
    """
    if extensions is None:
        extensions = ALLOWED_IMAGE_EXTENSIONS

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in extensions


def save_uploaded_file(file, upload_folder):
    """
    Save uploaded file to temporary location

    Args:
        file: FileStorage object from request.files
        upload_folder: Directory to save file

    Returns:
        Path to saved file
    """
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    return filepath


def cleanup_temp_files(temp_files):
    """
    Clean up temporary files

    Args:
        temp_files: List of file paths to delete
    """
    for filepath in temp_files:
        try:
            if isinstance(filepath, str) and os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            # Silent fail for cleanup
            pass


def validate_template_json(template_data, return_details=False):
    """
    Validate template JSON structure

    Args:
        template_data: Dictionary with template configuration
        return_details: If True, return detailed validation results

    Returns:
        Boolean (if return_details=False) or dict with validation results
    """
    from src.utils.validations import validate_template_json as core_validate
    import jsonschema

    errors = []
    warnings = []

    try:
        # Use the built-in validator
        core_validate(template_data, "api_template_validation")
        is_valid = True
    except Exception as e:
        is_valid = False
        errors.append(str(e))

        # Additional checks
        if 'pageDimensions' not in template_data:
            errors.append("Missing 'pageDimensions'")

        if 'bubbleDimensions' not in template_data:
            errors.append("Missing 'bubbleDimensions'")

        if 'fieldBlocks' not in template_data or not template_data['fieldBlocks']:
            errors.append("Missing or empty 'fieldBlocks'")

        # Check field blocks
        if 'fieldBlocks' in template_data:
            for block_name, block_config in template_data['fieldBlocks'].items():
                # Either fieldType OR (bubbleValues + direction) is required
                has_field_type = 'fieldType' in block_config
                has_custom_values = 'bubbleValues' in block_config and 'direction' in block_config
                if not has_field_type and not has_custom_values:
                    errors.append(f"Block '{block_name}' missing 'fieldType' or 'bubbleValues'+'direction'")

                if 'origin' not in block_config:
                    errors.append(f"Block '{block_name}' missing 'origin'")

                if 'fieldLabels' not in block_config:
                    warnings.append(f"Block '{block_name}' missing 'fieldLabels'")

        if return_details:
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }

        return len(errors) == 0

    except Exception as e:
        if return_details:
            return {
                'valid': False,
                'errors': [str(e)],
                'warnings': []
            }
        return False


def validate_config_json(config_data):
    """
    Validate config JSON structure

    Args:
        config_data: Dictionary with config parameters

    Returns:
        Boolean indicating if config is valid
    """
    try:
        # Basic validation - config is optional so just check structure
        if not isinstance(config_data, dict):
            return False

        # Check for known keys (optional)
        known_keys = ['dimensions', 'threshold_params', 'outputs', 'alignment_params']

        return True

    except Exception:
        return False


def numpy_to_base64(image_array):
    """
    Convert numpy array image to base64 string

    Args:
        image_array: Numpy array representing image

    Returns:
        Base64 encoded string
    """
    # Encode image to PNG format
    _, buffer = cv2.imencode('.png', image_array)

    # Convert to base64
    base64_str = base64.b64encode(buffer).decode('utf-8')

    return base64_str


def base64_to_numpy(base64_str):
    """
    Convert base64 string to numpy array image

    Args:
        base64_str: Base64 encoded image string

    Returns:
        Numpy array representing image
    """
    # Decode base64
    image_bytes = base64.b64decode(base64_str)

    # Convert to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)

    # Decode image
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    return image


def bytes_to_numpy(image_bytes):
    """
    Convert bytes to numpy array image

    Args:
        image_bytes: Image data as bytes

    Returns:
        Numpy array representing image (grayscale)
    """
    # Convert to numpy array
    nparr = np.frombuffer(image_bytes, np.uint8)

    # Decode image as GRAYSCALE to match original OMRChecker behavior
    image = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

    return image


def create_csv_response(result_data):
    """
    Create CSV file response from result data

    Args:
        result_data: Dictionary with processing results

    Returns:
        Flask send_file response with CSV
    """
    # Convert results to DataFrame
    if 'results' in result_data:
        # Batch results
        df = pd.DataFrame(result_data['results'])
    else:
        # Single result
        df = pd.DataFrame([{
            'file_name': result_data.get('file_name', 'unknown'),
            'status': result_data.get('status', 'success'),
            **result_data.get('response', {})
        }])

    # Create CSV in memory
    output = StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    # Convert to bytes
    csv_bytes = BytesIO(output.getvalue().encode('utf-8'))

    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name='omr_results.csv'
    )


def get_default_config():
    """
    Get default configuration

    Returns:
        Dictionary with default config values
    """
    return {
        "dimensions": {
            "display_width": 1240,
            "display_height": 1754,
            "processing_height": 1754,
            "processing_width": 1240
        },
        "threshold_params": {
            "MIN_JUMP": 10
        },
        "outputs": {
            "filter_out_multimarked_files": False,
            "show_image_level": 0  # Disable image display for API
        }
    }


def get_default_template():
    """
    Get default template structure (for reference)

    Returns:
        Dictionary with minimal template structure
    """
    return {
        "pageDimensions": [1240, 1754],
        "bubbleDimensions": [18, 18],
        "preProcessors": [],
        "fieldBlocks": {}
    }
