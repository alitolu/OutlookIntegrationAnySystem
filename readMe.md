Reference Search Application
A Python application for detecting and analyzing Reference Numbers information in emails and documents.
Project Overview
This application provides automated detection of  tracking numbers from emails (primarily Outlook), with AI-assisted analysis capabilities. It helps logistics professionals and shipping coordinators efficiently track shipments by scanning communications for relevant tracking information.
Architecture
The application follows an MVC architecture:
•	Views: User interface components including the main window and utility dialogs
•	Controllers & Models: Core business logic and data structures
•	Utilities: Specialized components for detection, analysis, and integration
Key Features
•	Email scanning through Outlook integration
•	Configurable  pattern detection
•	AI-powered content analysis
•	Excel import/export capabilities
•	Attachment processing
•	Search result caching
Components
UI Layer
•	main_window.py: Main application interface
•	data_source_editor.py: Configure email sources
•	pattern_manager.py: Manage  detection patterns
•	widgets.py: Reusable UI components
•	progress.py: Detailed progress reporting
Core
•	search_controller.py: Coordinates search operations
•	mail_model.py: Mail data representation
Utilities
•	_detector.py:  pattern recognition
•	cache_manager.py: Search result caching
•	config_manager.py: Application settings
•	excel_helper.py: Excel file operations
•	mail_analyzer.py: Email content analysis
•	outlook_helper.py: Microsoft Outlook integration
•	ai_analyzer.py: AI-assisted content analysis
•	attachment_processor.py: Email attachment handling
Configuration
The application uses JSON files for configuration:
•	settings.json: Application settings
•	_patterns.json: Configurable  detection patterns