# Green-Code FX User Guide

Welcome to Green-Code FX! This guide will help you create professional typing code effect videos using our user-friendly web interface.

## Getting Started

### Accessing the Web Interface

1. **Start the Service**: Ensure Green-Code FX is running (see [README.md](../README.md) for setup instructions)
2. **Open Your Browser**: Navigate to `http://localhost:8082`
3. **Verify Connection**: You should see the Green-Code FX interface with a dark theme and green accents

### System Requirements

**Supported Browsers**:
- Chrome 90+ (recommended)
- Firefox 88+
- Safari 14+
- Edge 90+

**Device Compatibility**:
- Desktop computers (Windows, macOS, Linux)
- Tablets (iPad, Android tablets)
- Mobile phones (iOS, Android)

---

## Creating Your First Video

### Step 1: Choose Your Text Input Method

The interface offers three ways to provide text for your typing effect:

#### Option A: Custom Text
1. **Select "Custom Text"** (default option)
2. **Type or paste your code** in the text area
3. **Character counter** shows usage (max 50,000 characters)
4. **Real-time validation** ensures text length is appropriate

**Best for**: Short code snippets, custom messages, or specific text content

#### Option B: File Upload
1. **Select "Upload File"**
2. **Drag and drop** a .txt file onto the upload area, or **click to browse**
3. **File validation** ensures only .txt files under 10MB are accepted
4. **Upload progress** shows file processing status

**Best for**: Long code files, existing projects, or pre-written content

#### Option C: Default Code
1. **Select "Default Code"**
2. **No additional input required** - uses built-in Snake game code
3. **Perfect for testing** or demonstration purposes

**Best for**: Quick tests, demonstrations, or when you need example content

### Step 2: Customize the Appearance

#### Font Settings
- **Font Family**: Choose from available fonts (JetBrains Mono recommended for code)
- **Font Size**: Adjust from 12px to 72px using the slider
- **Real-time preview** shows size changes immediately

#### Color Customization
- **Color Picker**: Click the color preview to open the advanced color picker
- **Hex Input**: Enter hex color codes directly (e.g., #00FF00 for green)
- **Preset Colors**: Choose from common programming colors
- **Validation**: Invalid colors are automatically corrected

#### Duration Settings
- **Video Length**: Set duration from 10 to 600 seconds (10 minutes)
- **Automatic Calculation**: System estimates typing speed based on text length
- **Recommended**: 60-90 seconds for most code snippets

### Step 3: Preview Your Settings

1. **Click "Preview"** to see how your text will appear
2. **Preview panel** shows:
   - Font family and size
   - Text color
   - Sample text with blinking cursor
3. **Make adjustments** as needed before generating

### Step 4: Generate Your Video

1. **Click "Generate Video"** to start the process
2. **Monitor progress** in the status panel:
   - Queue position (if applicable)
   - Generation progress (0-100%)
   - Estimated time remaining
3. **Wait for completion** - generation typically takes 1-3 minutes

### Step 5: Download Your Video

1. **Download button** appears when generation is complete
2. **File information** shows:
   - File size
   - Video duration
   - Download link
3. **Click "Download Video"** to save the MP4 file

---

## Advanced Features

### Mobile and Tablet Usage

#### Mobile Optimization
- **Responsive design** adapts to small screens
- **Touch-friendly controls** with appropriate sizing
- **Swipe gestures** for navigation
- **Portrait and landscape** orientation support

#### Tablet Features
- **Optimized layout** for medium screens
- **Enhanced touch targets** for precise control
- **Split-screen compatibility** for multitasking

### File Upload Features

#### Drag and Drop
1. **Drag files** from your file manager
2. **Drop onto the upload area** (highlighted when dragging)
3. **Automatic validation** and processing
4. **Visual feedback** for successful uploads

#### File Validation
- **Type checking**: Only .txt files accepted
- **Size limits**: Maximum 10MB per file
- **Content validation**: Ensures readable text content
- **Security scanning**: Protects against malicious files

### Real-time Features

#### Live Preview
- **Instant updates** when changing settings
- **Color preview** shows exact appearance
- **Font preview** demonstrates text rendering
- **Character counting** with usage indicators

#### Progress Monitoring
- **Real-time status** updates every 2 seconds
- **Progress bar** shows completion percentage
- **Queue position** when multiple jobs are running
- **Estimated time** based on current system load

---

## Tips and Best Practices

### Text Content Tips

**For Code Files**:
- Use proper indentation (spaces or tabs)
- Include comments for better visual appeal
- Keep lines under 120 characters for best display
- Consider syntax highlighting-friendly content

**For Custom Text**:
- Break long lines for better readability
- Use consistent formatting
- Include meaningful variable names
- Add comments to explain complex logic

### Visual Design Tips

**Font Selection**:
- **JetBrains Mono**: Best for code (monospace, clear)
- **System fonts**: Good for general text
- **Size recommendations**: 24-32px for 4K output

**Color Choices**:
- **Classic green (#00FF00)**: Traditional terminal look
- **Bright colors**: Better visibility on dark backgrounds
- **Avoid dark colors**: May not show well on black background
- **Test contrast**: Ensure readability

**Duration Guidelines**:
- **Short snippets (< 50 lines)**: 30-60 seconds
- **Medium files (50-200 lines)**: 60-120 seconds
- **Large files (200+ lines)**: 120+ seconds
- **Consider audience**: Adjust speed for viewing comfort

### Performance Tips

**For Best Results**:
- Use stable internet connection
- Close unnecessary browser tabs
- Allow pop-ups for download notifications
- Keep browser updated

**File Upload Optimization**:
- Use UTF-8 encoded text files
- Remove unnecessary whitespace
- Compress large files if possible
- Test with small files first

---

## Troubleshooting

### Common Issues

#### "Video Generation Failed"
**Possible Causes**:
- Invalid text content
- Server overload
- Network connectivity issues

**Solutions**:
1. Check text content for special characters
2. Try again in a few minutes
3. Refresh the page and retry
4. Contact support if issue persists

#### "File Upload Failed"
**Possible Causes**:
- File too large (> 10MB)
- Invalid file type (not .txt)
- Network interruption

**Solutions**:
1. Check file size and type
2. Try uploading a smaller file
3. Ensure stable internet connection
4. Use a different browser if needed

#### "Preview Not Working"
**Possible Causes**:
- JavaScript disabled
- Browser compatibility issues
- Ad blockers interfering

**Solutions**:
1. Enable JavaScript in browser
2. Try a different browser
3. Disable ad blockers temporarily
4. Clear browser cache

### Browser-Specific Issues

#### Chrome
- Enable hardware acceleration for better performance
- Allow pop-ups for download notifications
- Clear cache if interface appears broken

#### Firefox
- Enable WebGL for better rendering
- Check privacy settings for file uploads
- Update to latest version

#### Safari
- Enable JavaScript and cookies
- Allow file downloads
- Check security settings

#### Mobile Browsers
- Use landscape mode for better experience
- Ensure sufficient storage space
- Close other apps to free memory

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Enter` | Generate video |
| `Ctrl + P` | Preview settings |
| `Ctrl + R` | Refresh page |
| `Escape` | Close dialogs |
| `Tab` | Navigate between fields |

---

## Getting Help

### Support Resources
- **Documentation**: Check [API.md](API.md) for technical details
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- **Operations**: Review [OPERATIONS.md](OPERATIONS.md) for system administration

### Contact Information
- **Technical Issues**: Check container logs for error details
- **Feature Requests**: Submit through project repository
- **Bug Reports**: Include browser version and error messages

---

## Video Usage Tips

### Video Editing Integration

**Recommended Workflow**:
1. Generate your typing effect video
2. Import into your video editor
3. Use "Screen" or "Add" blend mode
4. Overlay on your background content
5. Adjust timing and positioning as needed

**Chroma Key Settings**:
- **Key Color**: Pure black (#000000)
- **Blend Mode**: Screen or Add (recommended)
- **Alternative**: Luma key for black removal
- **Avoid**: Green screen keying (removes text)

**Quality Settings**:
- **Resolution**: 4K (3840×2160) for maximum quality
- **Frame Rate**: 60 FPS for smooth motion
- **Format**: H.264 MP4 for broad compatibility
- **Compression**: Minimal loss for professional results

---

Enjoy creating professional typing code effects with Green-Code FX!
