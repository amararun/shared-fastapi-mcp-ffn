# Documentation System

This directory contains the converted HTML documentation for the SPR (Security Performance Review) application.

## Files

- `SPR_QS_METHODOLOGY.html` - Main documentation file converted from markdown
- `assets/docs.css` - Custom CSS styling for the documentation
- `README.md` - This file

## Access URLs

### Local Development
```
http://localhost:8000/static/docs/SPR_QS_METHODOLOGY.html
```

### Production (Render/Remote)
```
https://your-app-domain.com/static/docs/SPR_QS_METHODOLOGY.html
```

## Regenerating Documentation

Whenever you update `docs/SPR_QS_METHODOLOY.md`, regenerate the HTML using:

### Option 1: Simple wrapper (recommended)
```bash
python convert_docs.py
```

### Option 2: Direct script
```bash
python scripts/doc_converter.py
```

## Frontend Integration Examples

### Direct Link
```html
<a href="https://your-app.com/static/docs/SPR_QS_METHODOLOGY.html" target="_blank">
    View Documentation
</a>
```

### Embedded iframe
```html
<iframe 
    src="https://your-app.com/static/docs/SPR_QS_METHODOLOGY.html"
    width="100%" 
    height="600px"
    frameBorder="0">
</iframe>
```

### Fetch and inject (JavaScript)
```javascript
const fetchDocs = async () => {
    const response = await fetch('https://your-app.com/static/docs/SPR_QS_METHODOLOGY.html');
    const html = await response.text();
    document.getElementById('docs-container').innerHTML = html;
};
```

### React/Next.js Component
```javascript
import { useState, useEffect } from 'react';

const DocsViewer = () => {
    const [docsUrl] = useState('https://your-app.com/static/docs/SPR_QS_METHODOLOGY.html');
    
    return (
        <div style={{ width: '100%', height: '80vh' }}>
            <iframe 
                src={docsUrl}
                width="100%" 
                height="100%"
                frameBorder="0"
                title="SPR Methodology Documentation"
            />
        </div>
    );
};
```

## Benefits of This Approach

1. **Single Source of Truth**: Edit only the MD file, HTML auto-generated
2. **Universal Compatibility**: Works in any frontend framework
3. **Fast Loading**: No client-side markdown parsing needed
4. **Consistent Styling**: Same appearance across all frontends
5. **SEO Friendly**: Search engines can index the HTML content
6. **Mobile Responsive**: CSS includes responsive design

## Maintenance

- Source file: `docs/SPR_QS_METHODOLOY.md` 
- Regenerate HTML after any changes to the source
- CSS can be customized in `scripts/doc_converter.py`
- HTML template can be modified in the same script 