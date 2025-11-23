# OMR Checker Web Interface

Modern, responsive web interface for the OMR Checker API.

## Features

✨ **Modern Design** - Beautiful gradient UI with smooth animations
📤 **File Upload** - Drag and drop OMR sheets, templates, and configs
⚡ **Real-time Processing** - Live results with loading indicators
📊 **Visual Results** - Grid display of all detected answers
🖼️ **Processed Images** - Optional display of marked OMR sheets
📱 **Responsive** - Works on desktop and mobile devices

## Quick Start

### 1. Start the API Server

Make sure the API server is running:

```bash
cd /Users/raxana/Documents/Projects/omr-beyso/OMRChecker
python3 -m api.app
```

The server should start on `http://127.0.0.1:8080`

### 2. Open the Web Interface

Simply open the HTML file in your browser:

```bash
open web/index.html
```

Or double-click `web/index.html` in Finder.

**Alternative - Use a local server:**

```bash
cd web
python3 -m http.server 3000
```

Then open: http://localhost:3000

## Usage

### Required Files

1. **OMR Sheet Image** (.jpg, .png) - **REQUIRED**
   - The scanned or photographed OMR sheet to process
   - This is the ONLY required file!

### Optional Files (Auto-loaded from server if not provided)

All of these files are **OPTIONAL**. If not uploaded, the API will automatically use defaults from the server's `inputs/` folder:

2. **Template File** (template.json) - OPTIONAL
   - Defines the layout of your OMR sheet
   - **Default:** Server uses `inputs/template.json`
   - Only upload if you want to use a different template

3. **Config File** (config.json) - OPTIONAL
   - Processing parameters (thresholds, dimensions, etc.)
   - **Default:** Server uses `inputs/config.json`
   - Only upload if you want custom processing settings

4. **Marker Image** (omr_marker.jpg) - OPTIONAL
   - Used if template has `CropOnMarkers` preprocessor
   - **Default:** Server uses `inputs/omr_marker.jpg`
   - Only upload if you want a different marker image

### Options

- **Include processed image** - Shows the OMR sheet with detected answers highlighted
- **Enable auto-alignment** - Automatically corrects slight misalignments

## Step-by-Step (Simple Mode - Just upload image!)

1. Click **"OMR Sheet Image"** and select your OMR sheet photo
2. Click **"🚀 Process OMR Sheet"**
3. Wait a few seconds for processing
4. View results!

**That's it!** The server will automatically use default template, config, and marker files.

## Step-by-Step (Advanced Mode - Custom settings)

1. Click **"OMR Sheet Image"** and select your OMR sheet photo
2. (Optional) Click **"Template File"** and select your custom template.json
3. (Optional) Click **"Config File"** and select your custom config.json
4. (Optional) Click **"Marker Image"** and select your custom marker image
5. Check options as needed (Include processed image, Auto-align)
6. Click **"🚀 Process OMR Sheet"**
7. Wait a few seconds for processing
8. View results!

## Results Display

### Metadata Section
- File name
- Total questions detected
- Processing time
- Multi-marked status (warnings if multiple answers detected)

### Answers Grid
- All detected answers displayed in a grid
- Empty answers shown with "-" in red
- Hover to highlight individual answers

### Processed Image
- (If enabled) Shows the OMR sheet with detected bubbles marked
- Useful for debugging and verification

## Troubleshooting

### "Error: Failed to fetch" or Network Error

**Cause:** API server is not running or wrong URL

**Solution:**
1. Make sure API server is running: `python3 -m api.app`
2. Check server is on `http://127.0.0.1:8080`
3. Check browser console for CORS errors

### CORS Policy Error

**Cause:** Browser blocking cross-origin requests

**Solution:**
- The API already has CORS enabled (flask-cors)
- If still having issues, try:
  ```bash
  # Open Chrome with CORS disabled (Mac)
  open -na "Google Chrome" --args --disable-web-security --user-data-dir=/tmp/chrome
  ```

### "Template validation failed"

**Cause:** Invalid template.json format

**Solution:**
- Use the validation endpoint first
- Check sample template at `api/defaults/template.json`
- Ensure JSON is properly formatted

### No answers detected

**Cause:** Poor image quality or incorrect template

**Solution:**
- Use higher quality images (good lighting, no blur)
- Verify template coordinates match your physical sheet
- Try enabling "auto-alignment" option
- Check if marker image is needed

## API Endpoint Used

```
POST http://127.0.0.1:8080/api/omr/process
Content-Type: multipart/form-data

Fields:
- image (required): OMR sheet image file
- template (required): template.json file
- config (optional): config.json file
- marker (optional): marker image file
- include_image (optional): "true" or "false"
- auto_align (optional): "true" or "false"
```

## Browser Compatibility

✅ Chrome 90+
✅ Firefox 88+
✅ Safari 14+
✅ Edge 90+

## Screenshots

### Upload Section
Clean interface for uploading files with clear labels for required vs optional files.

### Results Display
Beautiful grid layout showing all detected answers with metadata.

### Processed Image
Visual confirmation of detected bubbles on the original sheet.

## Tips

1. **Image Quality** - Use well-lit, clear images for best results
2. **Template Accuracy** - Ensure template coordinates match your sheet exactly
3. **Marker Files** - Required if using CropOnMarkers preprocessor
4. **Auto-Align** - Enable for photographed sheets with slight rotation
5. **Include Image** - Check this box to see visual confirmation of detection

## Files Structure

```
web/
├── index.html          # Main web interface
└── README.md          # This file
```

## Security Notes

- All processing is done server-side
- Files are not stored permanently
- Use HTTPS in production
- Validate file types and sizes on server

## Future Enhancements

Potential improvements:
- Batch upload (multiple images)
- Progress bar for processing
- Download results as CSV
- Save/load templates
- Print results
- Compare with answer key
- Statistics dashboard

## Support

For issues:
1. Check API server logs
2. Check browser console (F12)
3. Verify all required files are selected
4. Test with sample files from `inputs/` directory

## License

Same as OMRChecker project.
