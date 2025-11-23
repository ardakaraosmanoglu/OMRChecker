"""
API Routes for OMR Checker
Defines all REST API endpoints
"""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json
import time
from io import BytesIO
import base64

from api.utils import (
    allowed_file,
    save_uploaded_file,
    validate_template_json,
    validate_config_json,
    cleanup_temp_files,
    create_csv_response
)
from src.api_adapter import process_omr_image, process_omr_batch, process_dir_for_api


api_blueprint = Blueprint('api', __name__)


@api_blueprint.route('/omr/process', methods=['POST'])
def process_omr():
    """
    Process single or multiple OMR images

    Accepts:
        - File uploads (multipart/form-data):
            - image: OMR image file(s)
            - template: template.json file or JSON in form field
            - config: config.json file or JSON in form field (optional)
            - marker: marker image file (optional)
        - Directory path (JSON):
            - directory: path to directory containing images and configs

    Returns:
        - JSON response with detected answers
        - Optional: processed images as base64
        - Optional: CSV download
    """
    start_time = time.time()
    temp_files = []

    try:
        # Check if request is file upload or directory path
        if request.content_type and 'multipart/form-data' in request.content_type:
            # File upload mode
            result = _process_file_upload(request, temp_files)
        elif request.is_json:
            # Directory path mode
            result = _process_directory_path(request)
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid request format. Use multipart/form-data for file uploads or JSON for directory path.'
            }), 400

        # Add processing time
        result['processing_time'] = round(time.time() - start_time, 2)

        # Handle CSV download if requested
        if request.args.get('format') == 'csv' or request.form.get('format') == 'csv':
            return create_csv_response(result)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'processing_time': round(time.time() - start_time, 2)
        }), 500

    finally:
        # Cleanup temporary files
        cleanup_temp_files(temp_files)


def _process_file_upload(request, temp_files):
    """Handle file upload processing"""
    # Validate required files
    if 'image' not in request.files:
        raise ValueError('No image file provided')

    # Get uploaded files
    image_files = request.files.getlist('image')
    template_file = request.files.get('template')
    config_file = request.files.get('config')
    marker_file = request.files.get('marker')

    # Validate image files
    for img in image_files:
        if not allowed_file(img.filename, ['png', 'jpg', 'jpeg']):
            raise ValueError(f'Invalid image file: {img.filename}')

    # Get template from file or form field, or use default
    if template_file:
        template_data = json.load(template_file)
    elif 'template' in request.form:
        template_data = json.loads(request.form['template'])
    else:
        # Use default template from inputs folder
        default_template_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'inputs',
            'template.json'
        )
        if os.path.exists(default_template_path):
            with open(default_template_path, 'r') as f:
                template_data = json.load(f)
        else:
            raise ValueError('No template provided and default template not found')

    # Validate template
    validate_template_json(template_data)

    # Get config from file or form field, or use default
    config_data = None
    if config_file:
        config_data = json.load(config_file)
    elif 'config' in request.form:
        config_data = json.loads(request.form['config'])
    else:
        # Use default config from inputs folder
        default_config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'inputs',
            'config.json'
        )
        if os.path.exists(default_config_path):
            from src.utils.parsing import open_config_with_defaults
            config_data = open_config_with_defaults(default_config_path)

    if config_data:
        validate_config_json(config_data)

    # Get marker image data if provided, or use default
    marker_data = None
    if marker_file:
        marker_data = marker_file.read()
        temp_files.append(marker_data)
    else:
        # Use default marker from inputs folder if template uses CropOnMarkers
        if 'preProcessors' in template_data:
            for processor in template_data['preProcessors']:
                if processor.get('name') == 'CropOnMarkers':
                    default_marker_path = os.path.join(
                        os.path.dirname(os.path.dirname(__file__)),
                        'inputs',
                        'omr_marker.jpg'
                    )
                    if os.path.exists(default_marker_path):
                        with open(default_marker_path, 'rb') as f:
                            marker_data = f.read()
                    break

    # Get options
    include_image = request.form.get('include_image', 'false').lower() == 'true'
    auto_align = request.form.get('auto_align', 'false').lower() == 'true'

    # Process single or multiple images
    if len(image_files) == 1:
        # Single image processing
        image_data = image_files[0].read()
        temp_files.append(image_data)

        result = process_omr_image(
            image_data=image_data,
            template_data=template_data,
            config_data=config_data,
            marker_data=marker_data,
            file_name=image_files[0].filename,
            include_image=include_image,
            auto_align=auto_align
        )
    else:
        # Multiple images processing
        images_data = []
        file_names = []
        for img_file in image_files:
            img_data = img_file.read()
            images_data.append(img_data)
            file_names.append(img_file.filename)
            temp_files.append(img_data)

        result = process_omr_batch(
            images_data=images_data,
            file_names=file_names,
            template_data=template_data,
            config_data=config_data,
            marker_data=marker_data,
            include_images=include_image,
            auto_align=auto_align
        )

    return result


def _process_directory_path(request):
    """Handle directory path processing"""
    data = request.get_json()

    if 'directory' not in data:
        raise ValueError('No directory path provided')

    directory = data['directory']

    # Validate directory exists
    if not os.path.isdir(directory):
        raise ValueError(f'Directory not found: {directory}')

    # Get options
    include_image = data.get('include_image', False)
    auto_align = data.get('auto_align', False)

    # Process directory
    result = process_dir_for_api(
        input_dir=directory,
        include_images=include_image,
        auto_align=auto_align
    )

    return result


@api_blueprint.route('/omr/batch', methods=['POST'])
def batch_process():
    """
    Batch process multiple OMR images with aggregated results

    Similar to /omr/process but optimized for batch operations
    Returns aggregated CSV by default
    """
    # For now, redirect to process endpoint
    # Can be optimized later for true batch processing
    return process_omr()


@api_blueprint.route('/omr/validate-template', methods=['POST'])
def validate_template():
    """
    Validate template.json structure

    Accepts:
        - JSON body with template structure
        - File upload with template.json

    Returns:
        - Validation result with errors/warnings
    """
    try:
        # Get template from request
        if request.is_json:
            template_data = request.get_json()
        elif 'template' in request.files:
            template_file = request.files['template']
            template_data = json.load(template_file)
        else:
            return jsonify({
                'status': 'error',
                'message': 'No template provided'
            }), 400

        # Validate template
        validation_result = validate_template_json(template_data, return_details=True)

        return jsonify({
            'status': 'success',
            'valid': validation_result['valid'],
            'errors': validation_result.get('errors', []),
            'warnings': validation_result.get('warnings', [])
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@api_blueprint.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error"""
    return jsonify({
        'status': 'error',
        'message': 'File too large. Maximum size is 50MB.'
    }), 413


@api_blueprint.errorhandler(400)
def bad_request(error):
    """Handle bad request error"""
    return jsonify({
        'status': 'error',
        'message': 'Bad request'
    }), 400
