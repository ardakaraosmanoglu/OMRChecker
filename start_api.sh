#!/bin/bash

# Start OMR Checker API Server

echo "Starting OMR Checker API..."
echo "API will be available at: http://localhost:8080"
echo ""
echo "Endpoints:"
echo "  GET  /api/health - Health check"
echo "  POST /api/omr/process - Process OMR images"
echo "  POST /api/omr/batch - Batch process"
echo "  POST /api/omr/validate-template - Validate template"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$(dirname "$0")"
python3 -m api.app
