# Wagon Damage Detection System

A professional Flask web application for railway wagon damage detection, video uploading, and damage analytics.

## Features

- **Secure Authentication System**
  - Username/password login with secure password handling
  - Password visibility toggle
  - Session management with automatic timeout

- **Video Upload**
  - Drag and drop interface
  - File selection with preview
  - Progress tracking with time remaining and data size
  - S3 bucket integration

- **Damage Detection**
  - Date-based video filtering
  - Video selection from repository
  - Processing status with visual feedback
  - Detailed damage reporting

- **Analytics Dashboard**
  - Interactive data visualization with multiple chart types
  - Filterable damage reports
  - CSV and PDF export options
  - Drill-down damage details

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/wagon-damage-detection.git
   cd wagon-damage-detection
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure AWS S3 settings:
   - Edit `app.py` to set your S3 bucket credentials
   - Or use environment variables (recommended for production)

5. Run the application:
   ```
   python app.py
   ```

6. Access the application:
   - Open your browser and navigate to `http://localhost:5000`
   - Login with username: `admin` and password: `123`

## Project Structure

```
flaskapp/
│
├── app.py                  # Main Flask application
├── requirements.txt        # Project dependencies
├── static/                 # Static files
│   ├── css/
│   │   └── style.css       # Main CSS styles
│   ├── js/
│   │   └── main.js         # Main JavaScript functionality
│   └── img/                # Image assets
│
└── templates/              # HTML templates
    ├── base.html           # Base layout template
    ├── index.html          # Home page
    ├── login.html          # Login page
    ├── upload.html         # Video upload page
    ├── damage_detection.html  # Damage detection page
    └── dashboard.html      # Analytics dashboard
```

## Requirements

- Python 3.8+
- Flask 2.3.3
- Werkzeug 2.3.7
- Boto3 1.28.63 (for AWS S3 integration)
- Other dependencies listed in requirements.txt

## Security Considerations

- Production deployments should use environment variables for secrets
- Password hashing is implemented for secure credential storage
- Proper session management and timeouts are configured
- File validation for uploads prevents malicious file uploads

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Bootstrap for UI components
- Chart.js for data visualization
- Font Awesome for icons 