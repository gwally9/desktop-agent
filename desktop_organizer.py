#!/usr/bin/env python3
"""
Desktop Organizer AI Agent (macOS)
----------------------------------
Scans the desktop, classifies files by type, organizes them into folders,
and uses Claude's vision API to intelligently rename screenshots based on content.

Requirements:
    pip install anthropic

Usage:
    python desktop_organizer.py [--dry-run] [--desktop-path /path/to/desktop]
"""

import os
import sys
import re
import shutil
import logging
import argparse
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

try:
    import anthropic
except ImportError:
    print("Please install the anthropic package: pip install anthropic")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('desktop_organizer.log')
    ]
)
logger = logging.getLogger(__name__)


# File type classifications
FILE_CATEGORIES: Dict[str, List[str]] = {
    "Documents": [
        ".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx",
        ".ppt", ".pptx", ".csv", ".md", ".tex", ".epub", ".pages", ".numbers",
        ".keynote"
    ],
    "Images": [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico",
        ".tiff", ".tif", ".heic", ".heif", ".raw", ".psd", ".ai"
    ],
    "Videos": [
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v",
        ".mpeg", ".mpg", ".3gp"
    ],
    "Audio": [
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".aiff"
    ],
    "Archives": [
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".dmg"
    ],
    "Code": [
        ".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".c", ".h",
        ".cs", ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
        ".sh", ".bash", ".ps1", ".sql", ".json", ".xml", ".yaml", ".yml",
        ".toml", ".ini", ".cfg", ".tf", ".hcl"
    ],
    "Executables": [
        ".exe", ".msi", ".app", ".dmg", ".deb", ".rpm", ".appimage"
    ],
    "Shortcuts": [
        ".lnk", ".url", ".desktop", ".webloc"
    ],
    "Fonts": [
        ".ttf", ".otf", ".woff", ".woff2", ".eot"
    ],
    "Data": [
        ".db", ".sqlite", ".sqlite3", ".mdb", ".accdb"
    ]
}

# Screenshot filename pattern: "Screenshot YYYY-MM-DD at HH.MM.SS AM/PM"
SCREENSHOT_PATTERN = re.compile(
    r'^Screenshot\s+(\d{4}-\d{2}-\d{2})\s+at\s+(\d{1,2}\.\d{2}\.\d{2})\s*(AM|PM)?',
    re.IGNORECASE
)


class DesktopOrganizer:
    """AI-powered desktop organization agent."""
    
    def __init__(self, desktop_path: Optional[str] = None, dry_run: bool = False):
        """
        Initialize the desktop organizer.
        
        Args:
            desktop_path: Custom path to desktop. If None, auto-detects.
            dry_run: If True, only logs actions without making changes.
        """
        self.desktop_path = Path(desktop_path) if desktop_path else self._get_desktop_path()
        self.dry_run = dry_run
        self.client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var
        
        # Statistics
        self.stats = {
            "files_processed": 0,
            "files_moved": 0,
            "screenshots_renamed": 0,
            "folders_created": 0,
            "errors": 0
        }
        
        logger.info(f"Desktop path: {self.desktop_path}")
        logger.info(f"Dry run mode: {self.dry_run}")
    
    def _get_desktop_path(self) -> Path:
        """Get the macOS desktop path."""
        desktop = Path.home() / "Desktop"
        
        if desktop.exists() and desktop.is_dir():
            return desktop
        
        raise ValueError(f"Desktop not found at {desktop}")
    
    def _get_category(self, file_path: Path) -> Optional[str]:
        """Determine the category for a file based on its extension."""
        ext = file_path.suffix.lower()
        
        for category, extensions in FILE_CATEGORIES.items():
            if ext in extensions:
                return category
        
        return "Other"
    
    def _is_screenshot(self, file_path: Path) -> bool:
        """Check if a file matches the screenshot naming convention."""
        return bool(SCREENSHOT_PATTERN.match(file_path.name))
    
    def _encode_image(self, file_path: Path) -> Tuple[str, str]:
        """
        Encode an image file to base64 for API submission.
        
        Returns:
            Tuple of (base64_data, media_type)
        """
        ext = file_path.suffix.lower()
        media_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        
        media_type = media_types.get(ext, "image/png")
        
        with open(file_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
        
        return image_data, media_type
    
    def _analyze_screenshot(self, file_path: Path) -> Optional[str]:
        """
        Use Claude's vision API to analyze screenshot content and generate a name.
        
        Args:
            file_path: Path to the screenshot file.
            
        Returns:
            Suggested filename (without extension) or None if analysis fails.
        """
        try:
            image_data, media_type = self._encode_image(file_path)
            
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=150,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": """Analyze this screenshot and provide a short, descriptive filename.

Rules:
1. Use 2-5 words maximum
2. Use hyphens between words (e.g., "Code-Snippet-Python")
3. Be specific but concise
4. Use Title-Case
5. Only output the filename, nothing else

Examples of good names:
- Code-Snippet-Python
- Website-Login-Page
- Error-Message-404
- Email-Inbox-Gmail
- Terminal-Command-Output
- Chart-Sales-Data
- Photo-Mountain-Sunset
- Document-Contract-Page1
- App-Settings-Menu
- Social-Media-Post

Respond with ONLY the filename, no explanation."""
                            }
                        ]
                    }
                ]
            )
            
            suggested_name = response.content[0].text.strip()
            
            # Clean up the name
            suggested_name = re.sub(r'[^\w\-]', '-', suggested_name)
            suggested_name = re.sub(r'-+', '-', suggested_name)
            suggested_name = suggested_name.strip('-')
            
            # Validate length
            if len(suggested_name) < 3 or len(suggested_name) > 50:
                logger.warning(f"Invalid name length: {suggested_name}")
                return None
            
            return suggested_name
            
        except Exception as e:
            logger.error(f"Error analyzing screenshot {file_path.name}: {e}")
            return None
    
    def _create_folder(self, folder_name: str) -> Path:
        """Create a folder on the desktop if it doesn't exist."""
        folder_path = self.desktop_path / folder_name
        
        if not folder_path.exists():
            if not self.dry_run:
                folder_path.mkdir(parents=True)
                self.stats["folders_created"] += 1
            logger.info(f"{'[DRY RUN] Would create' if self.dry_run else 'Created'} folder: {folder_name}")
        
        return folder_path
    
    def _get_unique_path(self, destination: Path) -> Path:
        """
        Get a unique file path by appending a number if file already exists.
        """
        if not destination.exists():
            return destination
        
        base = destination.stem
        ext = destination.suffix
        parent = destination.parent
        counter = 1
        
        while True:
            new_name = f"{base}-{counter}{ext}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
    
    def _move_file(self, source: Path, destination: Path) -> bool:
        """
        Move a file to a new location.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            destination = self._get_unique_path(destination)
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would move: {source.name} -> {destination}")
            else:
                shutil.move(str(source), str(destination))
                logger.info(f"Moved: {source.name} -> {destination}")
                self.stats["files_moved"] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error moving {source.name}: {e}")
            self.stats["errors"] += 1
            return False
    
    def _rename_file(self, source: Path, new_name: str) -> Optional[Path]:
        """
        Rename a file while keeping it in the same directory.
        
        Returns:
            New path if successful, None otherwise.
        """
        try:
            new_path = source.parent / f"{new_name}{source.suffix}"
            new_path = self._get_unique_path(new_path)
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would rename: {source.name} -> {new_path.name}")
            else:
                source.rename(new_path)
                logger.info(f"Renamed: {source.name} -> {new_path.name}")
                self.stats["screenshots_renamed"] += 1
            
            return new_path
            
        except Exception as e:
            logger.error(f"Error renaming {source.name}: {e}")
            self.stats["errors"] += 1
            return None
    
    def organize(self) -> Dict:
        """
        Main method to organize the desktop.
        
        Returns:
            Statistics dictionary.
        """
        logger.info("=" * 60)
        logger.info("Starting desktop organization...")
        logger.info("=" * 60)
        
        if not self.desktop_path.exists():
            raise ValueError(f"Desktop path does not exist: {self.desktop_path}")
        
        # Get all files on desktop (not directories)
        files = [
            f for f in self.desktop_path.iterdir()
            if f.is_file() and not f.name.startswith('.')
        ]
        
        logger.info(f"Found {len(files)} files on desktop")
        
        # Process screenshots first (rename them)
        screenshots = [f for f in files if self._is_screenshot(f)]
        other_files = [f for f in files if not self._is_screenshot(f)]
        
        # Rename screenshots based on content
        renamed_screenshots = []
        if screenshots:
            logger.info(f"\nProcessing {len(screenshots)} screenshots...")
            for screenshot in screenshots:
                self.stats["files_processed"] += 1
                logger.info(f"Analyzing: {screenshot.name}")
                
                new_name = self._analyze_screenshot(screenshot)
                if new_name:
                    new_path = self._rename_file(screenshot, new_name)
                    if new_path:
                        renamed_screenshots.append(new_path)
                    else:
                        renamed_screenshots.append(screenshot)
                else:
                    logger.warning(f"Could not generate name for: {screenshot.name}")
                    renamed_screenshots.append(screenshot)
        
        # Combine renamed screenshots with other files
        all_files = renamed_screenshots + other_files
        
        # Organize files into folders
        logger.info(f"\nOrganizing files into folders...")
        for file_path in all_files:
            if file_path not in renamed_screenshots:
                self.stats["files_processed"] += 1
            
            category = self._get_category(file_path)
            if category:
                folder = self._create_folder(category)
                destination = folder / file_path.name
                self._move_file(file_path, destination)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("Organization complete!")
        logger.info("=" * 60)
        logger.info(f"Files processed: {self.stats['files_processed']}")
        logger.info(f"Files moved: {self.stats['files_moved']}")
        logger.info(f"Screenshots renamed: {self.stats['screenshots_renamed']}")
        logger.info(f"Folders created: {self.stats['folders_created']}")
        logger.info(f"Errors: {self.stats['errors']}")
        
        return self.stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AI-powered desktop organizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with auto-detected desktop (dry run first!)
    python desktop_organizer.py --dry-run
    
    # Run for real
    python3 desktop_organizer.py
    
    # Specify custom desktop path
    python3 desktop_organizer.py --desktop-path /home/user/Desktop
    
Environment Variables:
    ANTHROPIC_API_KEY - Your Anthropic API key for screenshot analysis
        """
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview changes without making them"
    )
    
    parser.add_argument(
        "--desktop-path", "-p",
        type=str,
        help="Path to desktop folder (auto-detected if not specified)"
    )
    
    args = parser.parse_args()
    
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.error(
            "ANTHROPIC_API_KEY environment variable not set.\n"
            "Set it with: export ANTHROPIC_API_KEY='your-key-here'"
        )
        sys.exit(1)
    
    try:
        organizer = DesktopOrganizer(
            desktop_path=args.desktop_path,
            dry_run=args.dry_run
        )
        organizer.organize()
        
    except KeyboardInterrupt:
        logger.info("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
