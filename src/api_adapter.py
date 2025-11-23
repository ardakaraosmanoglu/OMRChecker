"""
API Adapter for OMR Checker
Wraps core OMR processing functions to work with in-memory data instead of file system
"""

import os
import cv2
import numpy as np
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Union
from deepmerge import always_merger

from src.template import Template
from src.core import ImageInstanceOps
from src.defaults import CONFIG_DEFAULTS
from src.utils.parsing import get_concatenated_response, open_config_with_defaults
from src.evaluation import EvaluationConfig, evaluate_concatenated_response
from api.utils import numpy_to_base64, bytes_to_numpy, get_default_config


def process_omr_image(
    image_data: bytes,
    template_data: Dict,
    config_data: Optional[Dict] = None,
    marker_data: Optional[bytes] = None,
    file_name: str = "image.jpg",
    include_image: bool = False,
    auto_align: bool = False,
    evaluation_data: Optional[Dict] = None
) -> Dict:
    """
    Process a single OMR image from memory

    Args:
        image_data: Image bytes
        template_data: Template configuration dictionary
        config_data: Optional config dictionary
        marker_data: Optional marker image bytes
        file_name: Name of the file (for reference)
        include_image: Whether to include processed image in response
        auto_align: Enable automatic alignment
        evaluation_data: Optional evaluation config for scoring

    Returns:
        Dictionary with processing results
    """
    try:
        # Convert bytes to numpy array
        image = bytes_to_numpy(image_data)

        if image is None:
            return {
                'status': 'error',
                'file_name': file_name,
                'message': 'Failed to decode image'
            }

        # Prepare configuration
        config = _prepare_config(config_data, auto_align, disable_display=True)

        # Create template from data
        template = _create_template_from_dict(
            template_data,
            config,
            marker_data=marker_data,
            relative_dir=None
        )

        # Create image processor
        image_ops = ImageInstanceOps(config)

        # Apply preprocessors
        # For preprocessors that need file_path, we create a temporary Path object
        temp_path = Path(file_name)
        processed_image = image_ops.apply_preprocessors(temp_path, image, template)

        # Read OMR response
        omr_response, final_marked, multi_marked, multi_roll = image_ops.read_omr_response(
            template,
            processed_image,
            file_name,
            save_dir=None  # No file saving in API mode
        )

        # Get concatenated responses for multi-column fields
        concatenated_response = get_concatenated_response(omr_response, template)

        # Build result
        result = {
            'status': 'success',
            'file_name': file_name,
            'response': concatenated_response,
            'raw_response': omr_response,
            'metadata': {
                'multi_marked': bool(multi_marked),
                'multi_roll': bool(multi_roll),
                'multi_marked_count': int(multi_marked),
                'image_dimensions': list(image.shape[:2])
            }
        }

        # Add evaluation if provided
        if evaluation_data:
            evaluation_config = EvaluationConfig(evaluation_data, template)
            score, evaluation_result = evaluate_concatenated_response(
                concatenated_response,
                evaluation_config
            )
            result['score'] = float(score)
            result['evaluation'] = evaluation_result

        # Add processed image if requested
        if include_image and final_marked is not None:
            result['processed_image'] = numpy_to_base64(final_marked)

        return result

    except Exception as e:
        return {
            'status': 'error',
            'file_name': file_name,
            'message': str(e)
        }


def process_omr_batch(
    images_data: List[bytes],
    file_names: List[str],
    template_data: Dict,
    config_data: Optional[Dict] = None,
    marker_data: Optional[bytes] = None,
    include_images: bool = False,
    auto_align: bool = False,
    evaluation_data: Optional[Dict] = None
) -> Dict:
    """
    Process multiple OMR images from memory

    Args:
        images_data: List of image bytes
        file_names: List of file names
        template_data: Template configuration dictionary
        config_data: Optional config dictionary
        marker_data: Optional marker image bytes
        include_images: Whether to include processed images in response
        auto_align: Enable automatic alignment
        evaluation_data: Optional evaluation config for scoring

    Returns:
        Dictionary with batch processing results
    """
    results = []
    successful = 0
    failed = 0

    for image_data, file_name in zip(images_data, file_names):
        result = process_omr_image(
            image_data=image_data,
            template_data=template_data,
            config_data=config_data,
            marker_data=marker_data,
            file_name=file_name,
            include_image=include_images,
            auto_align=auto_align,
            evaluation_data=evaluation_data
        )

        results.append(result)

        if result['status'] == 'success':
            successful += 1
        else:
            failed += 1

    return {
        'status': 'success',
        'total': len(images_data),
        'successful': successful,
        'failed': failed,
        'results': results
    }


def _prepare_config(config_data: Optional[Dict], auto_align: bool, disable_display: bool = True) -> object:
    """
    Prepare configuration object from dictionary

    Args:
        config_data: Configuration dictionary
        auto_align: Enable automatic alignment
        disable_display: Disable image display (for API mode)

    Returns:
        Configuration object
    """
    # Start with defaults
    config = get_default_config()

    # Merge with provided config
    if config_data:
        config = always_merger.merge(config, config_data)

    # Override for API mode
    if disable_display:
        if 'outputs' not in config:
            config['outputs'] = {}
        config['outputs']['show_image_level'] = 0
        config['outputs']['save_image_level'] = 0

    # Set auto_align
    if 'alignment_params' not in config:
        config['alignment_params'] = {}
    config['alignment_params']['auto_align'] = auto_align

    # Convert to config object
    from dotmap import DotMap
    config_obj = DotMap(config, _dynamic=False)

    # Merge with CONFIG_DEFAULTS to ensure all required fields exist
    final_config = always_merger.merge(CONFIG_DEFAULTS, config_obj)

    return final_config


def _create_template_from_dict(
    template_data: Dict,
    config: object,
    marker_data: Optional[bytes] = None,
    relative_dir: Optional[str] = None
) -> Template:
    """
    Create Template object from dictionary

    Args:
        template_data: Template configuration dictionary
        config: Configuration object
        marker_data: Optional marker image bytes
        relative_dir: Optional directory for relative paths (for file-based markers)

    Returns:
        Template object
    """
    import cv2
    import os

    # If marker data is provided and template uses CropOnMarkers,
    # we need to save it temporarily
    temp_marker_path = None

    if marker_data and 'preProcessors' in template_data:
        for processor in template_data['preProcessors']:
            if processor.get('name') == 'CropOnMarkers':
                # Save marker temporarily
                temp_marker_path = '/tmp/omr_marker_temp.jpg'
                marker_image = bytes_to_numpy(marker_data)
                cv2.imwrite(temp_marker_path, marker_image)

                # Update absolute path in template
                if 'options' in processor:
                    processor['options']['relativePath'] = temp_marker_path

    # If relative_dir is provided and no marker_data, convert relative paths to absolute
    elif relative_dir and 'preProcessors' in template_data:
        for processor in template_data['preProcessors']:
            if processor.get('name') == 'CropOnMarkers':
                if 'options' in processor and 'relativePath' in processor['options']:
                    rel_path = processor['options']['relativePath']
                    # Convert to absolute path
                    abs_path = os.path.join(relative_dir, rel_path)
                    processor['options']['relativePath'] = abs_path

    # Create template from dictionary
    template = Template.from_dict(template_data, config, relative_dir=relative_dir)

    return template


def process_dir_for_api(
    input_dir: str,
    include_images: bool = False,
    auto_align: bool = False
) -> Dict:
    """
    Process a directory of OMR images (for directory path mode)

    Args:
        input_dir: Path to input directory
        include_images: Whether to include processed images
        auto_align: Enable automatic alignment

    Returns:
        Dictionary with processing results
    """
    from src.entry import process_dir
    from src.constants.common import TEMPLATE_FILENAME, CONFIG_FILENAME

    input_path = Path(input_dir)

    if not input_path.exists():
        return {
            'status': 'error',
            'message': f'Directory not found: {input_dir}'
        }

    # Check for template and config
    template_path = input_path / TEMPLATE_FILENAME
    config_path = input_path / CONFIG_FILENAME

    if not template_path.exists():
        return {
            'status': 'error',
            'message': f'Template file not found in directory: {TEMPLATE_FILENAME}'
        }

    # Load template and config
    with open(template_path, 'r') as f:
        import json
        template_data = json.load(f)

    config_data = None
    if config_path.exists():
        config_data = open_config_with_defaults(config_path)

    # Get all image files
    image_extensions = {'.png', '.jpg', '.jpeg'}
    image_files = [
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]

    # Filter out marker files
    image_files = [
        f for f in image_files
        if 'marker' not in f.name.lower()
    ]

    if not image_files:
        return {
            'status': 'error',
            'message': 'No image files found in directory'
        }

    # Load marker if exists
    marker_data = None
    marker_path = input_path / 'omr_marker.jpg'
    if marker_path.exists():
        with open(marker_path, 'rb') as f:
            marker_data = f.read()

    # Process all images
    images_data = []
    file_names = []

    for img_file in image_files:
        with open(img_file, 'rb') as f:
            images_data.append(f.read())
        file_names.append(img_file.name)

    # Process batch with relative directory for marker files
    results = []
    successful = 0
    failed = 0

    # Prepare config
    config = _prepare_config(config_data, auto_align, disable_display=True)

    # Create template with relative directory
    template = _create_template_from_dict(
        template_data,
        config,
        marker_data=marker_data,
        relative_dir=str(input_path)
    )

    # Process each image
    from src.core import ImageInstanceOps
    from src.utils.parsing import get_concatenated_response

    image_ops = ImageInstanceOps(config)

    for image_data, file_name in zip(images_data, file_names):
        try:
            # Convert bytes to numpy
            image = bytes_to_numpy(image_data)

            if image is None:
                results.append({
                    'status': 'error',
                    'file_name': file_name,
                    'message': 'Failed to decode image'
                })
                failed += 1
                continue

            # Apply preprocessors
            temp_path = Path(file_name)
            processed_image = image_ops.apply_preprocessors(temp_path, image, template)

            # Read OMR response
            omr_response, final_marked, multi_marked, multi_roll = image_ops.read_omr_response(
                template,
                processed_image,
                file_name,
                save_dir=None
            )

            # Get concatenated responses
            concatenated_response = get_concatenated_response(omr_response, template)

            # Build result
            result = {
                'status': 'success',
                'file_name': file_name,
                'response': concatenated_response,
                'raw_response': omr_response,
                'metadata': {
                    'multi_marked': bool(multi_marked),
                    'multi_roll': bool(multi_roll),
                    'multi_marked_count': int(multi_marked),
                    'image_dimensions': list(image.shape[:2])
                }
            }

            # Add processed image if requested
            if include_images and final_marked is not None:
                result['processed_image'] = numpy_to_base64(final_marked)

            results.append(result)
            successful += 1

        except Exception as e:
            results.append({
                'status': 'error',
                'file_name': file_name,
                'message': str(e)
            })
            failed += 1

    return {
        'status': 'success',
        'total': len(images_data),
        'successful': successful,
        'failed': failed,
        'results': results
    }
