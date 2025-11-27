# Système de Présence Géolocalisé

## Overview
This is a Flask-based attendance tracking system that uses geolocation to verify student presence. Students scan a QR code with their mobile device, which records their location and validates whether they are within the acceptable distance from the classroom.

## Current State
- ✅ Fully functional Flask application
- ✅ QR code generation for attendance scanning
- ✅ Geolocation-based validation
- ✅ SQLite database for tracking attendance
- ✅ Admin interface to view attendance history
- ✅ Configured for Replit deployment

## Recent Changes (November 27, 2025)
- Completed the Flask application with all routes and API endpoints
- Added database operations for students and presence tracking
- Implemented geolocation distance calculation using Haversine formula
- Configured for Replit environment with proper host settings (0.0.0.0:5000)
- Set up workflow for development server
- Added Gunicorn for production deployment
- Configured autoscale deployment settings

## Project Architecture

### Backend (Flask - Python)
- **app.py**: Main Flask application with routes and business logic
  - `/` - Home page displaying QR code
  - `/scan` - Student presence recording page
  - `/admin` - Admin interface for viewing attendance
  - `/api/presence` - REST API endpoint for recording attendance
  
### Database (SQLite)
- **students** table: Stores student information
- **presences** table: Records attendance with location data

### Templates
- `admin.html` - Admin dashboard showing attendance history
- `scan.html` - Student-facing page with geolocation capture

### Key Configuration
- Reference coordinates: REF_LAT=48.8566, REF_LON=2.3522 (Paris - to be updated)
- Maximum distance: 50 meters
- QR code path: static/qr_math1.png

## Environment Variables
- `REPLIT_URL`: The public URL of the deployed application (set automatically)

## Dependencies
- Flask 2.3.2
- Flask-Cors 3.0.10
- qrcode 7.4.2
- Pillow 10.0.0
- gunicorn 21.2.0

## Development
Run locally: `python app.py`
The application will start on http://0.0.0.0:5000

## Deployment
Configured for autoscale deployment using Gunicorn WSGI server.
Deploy using Replit's publish feature.

## Notes
- The reference coordinates (REF_LAT, REF_LON) should be updated to match the actual classroom location
- The maximum distance threshold can be adjusted in app.py
- The application uses UTC timestamps for attendance records
