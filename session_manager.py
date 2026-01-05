#!/usr/bin/env python3
"""
Session Manager: Production V1.0 - Clean Slate Directory Structure
===================================================================
Implements strict directory management with the following structure:

DIRECTORY STRUCTURE (Enforced):
├── temp_session/      Created on launch, wiped on exit. Stores current upload.
├── taxonomy/          ReadOnly DB. XBRL taxonomy data.
├── output/            Stores final models (DCF, LBO, Comps).
└── logs/              Stores the "Thinking" logs from the iterative engine.

Philosophy:
- NO test files (client_upload.xlsx) - Only user uploads
- Clean slate on every launch
- All thinking/reasoning logged to logs/
- Output directory contains production-ready models
"""

import os
import shutil
import uuid
import glob
import atexit
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass


# Configuration - PRODUCTION V1.0 CLEAN SLATE STRUCTURE
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Core directories (Clean Slate Architecture)
TEMP_SESSION_DIR = os.path.join(BASE_DIR, "temp_session")      # Created on launch, wiped on exit
TAXONOMY_DIR = os.path.join(BASE_DIR, "taxonomy")              # ReadOnly DB
OUTPUT_DIR = os.path.join(BASE_DIR, "output")                  # Final models
LOGS_DIR = os.path.join(BASE_DIR, "logs")                      # Thinking logs

# Legacy (for backwards compatibility during transition)
TEMP_SESSIONS_DIR = os.path.join(BASE_DIR, "temp_sessions")
SESSION_EXPIRY_HOURS = 24  # Auto-cleanup sessions older than this


@dataclass
class SessionInfo:
    """Information about a session."""
    session_id: str
    session_dir: str
    created_at: datetime
    upload_path: Optional[str] = None
    messy_path: Optional[str] = None
    normalized_path: Optional[str] = None
    models_dir: Optional[str] = None


# =============================================================================
# CLEAN SLATE ARCHITECTURE - Production V1.0
# =============================================================================

def initialize_clean_slate() -> Dict[str, str]:
    """
    Initialize the Clean Slate directory structure.
    Called on application launch.

    Creates:
    - temp_session/ - Wiped on launch, stores current upload
    - taxonomy/ - ReadOnly DB (created if missing, never wiped)
    - output/ - Stores final models (wiped on launch)
    - logs/ - Stores thinking logs (wiped on launch)

    Returns:
        Dict with directory paths
    """
    print("[Clean Slate] Initializing Production V1.0 directory structure...")

    # Wipe temp_session/ on launch (clean slate)
    if os.path.exists(TEMP_SESSION_DIR):
        shutil.rmtree(TEMP_SESSION_DIR)
        print(f"  [WIPED] {TEMP_SESSION_DIR}")
    os.makedirs(TEMP_SESSION_DIR, exist_ok=True)
    os.makedirs(os.path.join(TEMP_SESSION_DIR, "uploads"), exist_ok=True)
    print(f"  [CREATED] {TEMP_SESSION_DIR}")

    # Create taxonomy/ (ReadOnly - never wipe, just ensure exists)
    os.makedirs(TAXONOMY_DIR, exist_ok=True)
    print(f"  [READY] {TAXONOMY_DIR} (ReadOnly)")

    # Wipe and recreate output/ for fresh models
    if os.path.exists(OUTPUT_DIR):
        # Preserve taxonomy database if it exists
        taxonomy_db = os.path.join(OUTPUT_DIR, "taxonomy_2025.db")
        taxonomy_backup = None
        if os.path.exists(taxonomy_db):
            taxonomy_backup = os.path.join(BASE_DIR, ".taxonomy_2025.db.bak")
            shutil.copy2(taxonomy_db, taxonomy_backup)

        # Clear output directory
        for item in os.listdir(OUTPUT_DIR):
            item_path = os.path.join(OUTPUT_DIR, item)
            if os.path.isfile(item_path) and item != "taxonomy_2025.db":
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

        # Restore taxonomy database
        if taxonomy_backup and os.path.exists(taxonomy_backup):
            shutil.copy2(taxonomy_backup, taxonomy_db)
            os.remove(taxonomy_backup)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "final_ib_models"), exist_ok=True)
    print(f"  [READY] {OUTPUT_DIR}")

    # Wipe and recreate logs/
    if os.path.exists(LOGS_DIR):
        shutil.rmtree(LOGS_DIR)
    os.makedirs(LOGS_DIR, exist_ok=True)
    print(f"  [CREATED] {LOGS_DIR}")

    # Write session metadata
    with open(os.path.join(TEMP_SESSION_DIR, ".clean_slate_meta"), 'w') as f:
        f.write(f"initialized_at={datetime.now().isoformat()}\n")
        f.write(f"version=1.0\n")

    print("[Clean Slate] Ready for production.")

    return {
        "temp_session": TEMP_SESSION_DIR,
        "taxonomy": TAXONOMY_DIR,
        "output": OUTPUT_DIR,
        "logs": LOGS_DIR
    }


def cleanup_on_exit():
    """
    Cleanup function registered with atexit.
    Wipes temp_session/ on application exit.
    """
    if os.path.exists(TEMP_SESSION_DIR):
        try:
            shutil.rmtree(TEMP_SESSION_DIR)
            print("[Clean Slate] Wiped temp_session/ on exit.")
        except Exception as e:
            print(f"[Clean Slate] Warning: Could not wipe temp_session/: {e}")


def get_clean_slate_paths() -> Dict[str, str]:
    """
    Get the current Clean Slate directory paths.

    Returns:
        Dict with directory paths
    """
    return {
        "temp_session": TEMP_SESSION_DIR,
        "taxonomy": TAXONOMY_DIR,
        "output": OUTPUT_DIR,
        "logs": LOGS_DIR,
        "upload": os.path.join(TEMP_SESSION_DIR, "uploads"),
        "models": os.path.join(OUTPUT_DIR, "final_ib_models")
    }


def get_current_upload_path() -> Optional[str]:
    """
    Get the path to the current uploaded file (if any).

    Returns:
        Path to uploaded file or None
    """
    uploads_dir = os.path.join(TEMP_SESSION_DIR, "uploads")
    if not os.path.exists(uploads_dir):
        return None

    xlsx_files = glob.glob(os.path.join(uploads_dir, "*.xlsx"))
    return xlsx_files[0] if xlsx_files else None


def save_current_upload(file_content: bytes, filename: str) -> str:
    """
    Save uploaded file to temp_session/uploads/.

    Args:
        file_content: Raw bytes of the uploaded file
        filename: Original filename

    Returns:
        Path to the saved file
    """
    uploads_dir = os.path.join(TEMP_SESSION_DIR, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    # Clear any existing uploads (single session model)
    for existing in glob.glob(os.path.join(uploads_dir, "*.xlsx")):
        os.remove(existing)

    # Sanitize filename
    safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
    if not safe_filename.endswith(".xlsx"):
        safe_filename += ".xlsx"

    upload_path = os.path.join(uploads_dir, safe_filename)

    with open(upload_path, 'wb') as f:
        f.write(file_content)

    return upload_path


def write_thinking_log(log_content: str, log_name: str = "thinking") -> str:
    """
    Write a thinking/reasoning log to logs/.

    Args:
        log_content: The log content to write
        log_name: Base name for the log file

    Returns:
        Path to the log file
    """
    os.makedirs(LOGS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(LOGS_DIR, f"{log_name}_{timestamp}.log")

    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"=== FinanceX Thinking Log ===\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"{'='*50}\n\n")
        f.write(log_content)

    return log_path


def append_thinking_log(log_line: str, log_path: str = None) -> str:
    """
    Append a line to the current thinking log.

    Args:
        log_line: Line to append
        log_path: Optional specific log path

    Returns:
        Path to the log file
    """
    if log_path is None:
        os.makedirs(LOGS_DIR, exist_ok=True)
        log_path = os.path.join(LOGS_DIR, "current_thinking.log")

    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {log_line}\n")

    return log_path


# Register cleanup on exit
atexit.register(cleanup_on_exit)


class SessionManager:
    """
    Manages temp sessions for file isolation.

    Usage:
        sm = SessionManager()
        session = sm.create_session()
        upload_path = sm.save_upload(session.session_id, uploaded_file)
        # ... run pipeline with session paths ...
        sm.cleanup_session(session.session_id)  # Or let auto-cleanup handle it
    """

    def __init__(self):
        """Initialize session manager and ensure temp directory exists."""
        self._ensure_temp_dir()

    def _ensure_temp_dir(self):
        """Create temp_sessions directory if it doesn't exist."""
        os.makedirs(TEMP_SESSIONS_DIR, exist_ok=True)

        # Create .gitkeep to ensure directory is tracked (but empty)
        gitkeep_path = os.path.join(TEMP_SESSIONS_DIR, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, 'w') as f:
                f.write("# This file ensures temp_sessions/ exists but contents are ignored\n")

    def create_session(self) -> SessionInfo:
        """
        Create a new isolated session directory.

        Returns:
            SessionInfo with paths for this session
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        session_dir = os.path.join(TEMP_SESSIONS_DIR, session_id)

        # Create session directory structure
        os.makedirs(session_dir, exist_ok=True)
        os.makedirs(os.path.join(session_dir, "uploads"), exist_ok=True)
        os.makedirs(os.path.join(session_dir, "output"), exist_ok=True)
        os.makedirs(os.path.join(session_dir, "final_ib_models"), exist_ok=True)

        # Write session metadata
        meta_path = os.path.join(session_dir, ".session_meta")
        with open(meta_path, 'w') as f:
            f.write(f"created_at={datetime.now().isoformat()}\n")
            f.write(f"session_id={session_id}\n")

        return SessionInfo(
            session_id=session_id,
            session_dir=session_dir,
            created_at=datetime.now(),
            models_dir=os.path.join(session_dir, "final_ib_models")
        )

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        Get information about an existing session.

        Args:
            session_id: The session identifier

        Returns:
            SessionInfo or None if session doesn't exist
        """
        session_dir = os.path.join(TEMP_SESSIONS_DIR, session_id)
        if not os.path.exists(session_dir):
            return None

        # Read metadata
        meta_path = os.path.join(session_dir, ".session_meta")
        created_at = datetime.now()  # Default if meta missing
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                for line in f:
                    if line.startswith("created_at="):
                        try:
                            created_at = datetime.fromisoformat(line.split("=", 1)[1].strip())
                        except (ValueError, IndexError):
                            pass

        # Find files
        upload_files = glob.glob(os.path.join(session_dir, "uploads", "*.xlsx"))
        upload_path = upload_files[0] if upload_files else None

        messy_path = os.path.join(session_dir, "output", "messy_input.csv")
        messy_path = messy_path if os.path.exists(messy_path) else None

        normalized_path = os.path.join(session_dir, "output", "normalized_financials.csv")
        normalized_path = normalized_path if os.path.exists(normalized_path) else None

        return SessionInfo(
            session_id=session_id,
            session_dir=session_dir,
            created_at=created_at,
            upload_path=upload_path,
            messy_path=messy_path,
            normalized_path=normalized_path,
            models_dir=os.path.join(session_dir, "final_ib_models")
        )

    def save_upload(self, session_id: str, file_content: bytes, filename: str) -> str:
        """
        Save an uploaded file to the session's upload directory.

        Args:
            session_id: The session identifier
            file_content: Raw bytes of the uploaded file
            filename: Original filename

        Returns:
            Path to the saved file
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Sanitize filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        if not safe_filename.endswith(".xlsx"):
            safe_filename += ".xlsx"

        upload_path = os.path.join(session.session_dir, "uploads", safe_filename)

        with open(upload_path, 'wb') as f:
            f.write(file_content)

        return upload_path

    def get_output_dir(self, session_id: str) -> str:
        """Get the output directory for a session."""
        return os.path.join(TEMP_SESSIONS_DIR, session_id, "output")

    def get_models_dir(self, session_id: str) -> str:
        """Get the final_ib_models directory for a session."""
        return os.path.join(TEMP_SESSIONS_DIR, session_id, "final_ib_models")

    def cleanup_session(self, session_id: str) -> bool:
        """
        Delete a session and all its files.

        Args:
            session_id: The session identifier

        Returns:
            True if cleanup succeeded
        """
        session_dir = os.path.join(TEMP_SESSIONS_DIR, session_id)
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir)
                return True
            except OSError as e:
                print(f"Warning: Could not cleanup session {session_id}: {e}")
                return False
        return True  # Already cleaned up

    def cleanup_expired_sessions(self) -> List[str]:
        """
        Remove all sessions older than SESSION_EXPIRY_HOURS.

        Returns:
            List of session IDs that were cleaned up
        """
        cleaned = []
        expiry_time = datetime.now() - timedelta(hours=SESSION_EXPIRY_HOURS)

        if not os.path.exists(TEMP_SESSIONS_DIR):
            return cleaned

        for session_name in os.listdir(TEMP_SESSIONS_DIR):
            if session_name.startswith("."):
                continue

            session_dir = os.path.join(TEMP_SESSIONS_DIR, session_name)
            if not os.path.isdir(session_dir):
                continue

            # Check session age
            meta_path = os.path.join(session_dir, ".session_meta")
            created_at = None

            if os.path.exists(meta_path):
                with open(meta_path, 'r') as f:
                    for line in f:
                        if line.startswith("created_at="):
                            try:
                                created_at = datetime.fromisoformat(line.split("=", 1)[1].strip())
                            except (ValueError, IndexError):
                                pass
                            break

            # Fall back to directory mtime if no metadata
            if created_at is None:
                mtime = os.path.getmtime(session_dir)
                created_at = datetime.fromtimestamp(mtime)

            # Cleanup if expired
            if created_at < expiry_time:
                if self.cleanup_session(session_name):
                    cleaned.append(session_name)

        return cleaned

    def cleanup_all_sessions(self) -> int:
        """
        Remove ALL sessions (aggressive cleanup).

        Returns:
            Number of sessions cleaned up
        """
        count = 0
        if not os.path.exists(TEMP_SESSIONS_DIR):
            return count

        for session_name in os.listdir(TEMP_SESSIONS_DIR):
            if session_name.startswith("."):
                continue

            session_dir = os.path.join(TEMP_SESSIONS_DIR, session_name)
            if os.path.isdir(session_dir):
                if self.cleanup_session(session_name):
                    count += 1

        return count

    def list_sessions(self) -> List[SessionInfo]:
        """
        List all active sessions.

        Returns:
            List of SessionInfo for all sessions
        """
        sessions = []
        if not os.path.exists(TEMP_SESSIONS_DIR):
            return sessions

        for session_name in os.listdir(TEMP_SESSIONS_DIR):
            if session_name.startswith("."):
                continue

            session_dir = os.path.join(TEMP_SESSIONS_DIR, session_name)
            if os.path.isdir(session_dir):
                session = self.get_session(session_name)
                if session:
                    sessions.append(session)

        return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    def get_session_files(self, session_id: str) -> Dict[str, Optional[str]]:
        """
        Get all output file paths for a session.

        Returns:
            Dict with file type -> path mappings
        """
        session = self.get_session(session_id)
        if not session:
            return {}

        output_dir = os.path.join(session.session_dir, "output")
        models_dir = os.path.join(session.session_dir, "final_ib_models")

        def check_path(path):
            return path if os.path.exists(path) else None

        return {
            "upload": session.upload_path,
            "messy_input": check_path(os.path.join(output_dir, "messy_input.csv")),
            "normalized": check_path(os.path.join(output_dir, "normalized_financials.csv")),
            "dcf": check_path(os.path.join(models_dir, "DCF_Historical_Setup.csv")),
            "lbo": check_path(os.path.join(models_dir, "LBO_Credit_Stats.csv")),
            "comps": check_path(os.path.join(models_dir, "Comps_Trading_Metrics.csv")),
            "validation": check_path(os.path.join(models_dir, "Validation_Report.csv")),
            "unmapped": check_path(os.path.join(models_dir, "Unmapped_Data_Report.csv")),
            "hierarchy": check_path(os.path.join(models_dir, "Hierarchy_Resolution_Report.csv")),
        }


# Convenience functions for direct use
_manager = None


def get_session_manager() -> SessionManager:
    """Get or create the global session manager."""
    global _manager
    if _manager is None:
        _manager = SessionManager()
    return _manager


def create_session() -> SessionInfo:
    """Create a new session (convenience function)."""
    return get_session_manager().create_session()


def cleanup_on_startup():
    """Cleanup expired sessions - call this on app startup."""
    manager = get_session_manager()
    cleaned = manager.cleanup_expired_sessions()
    if cleaned:
        print(f"[SessionManager] Cleaned up {len(cleaned)} expired sessions")
    return cleaned


if __name__ == "__main__":
    # Test the session manager
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "cleanup":
            manager = SessionManager()
            count = manager.cleanup_all_sessions()
            print(f"Cleaned up {count} sessions")

        elif cmd == "list":
            manager = SessionManager()
            sessions = manager.list_sessions()
            if not sessions:
                print("No active sessions")
            else:
                for s in sessions:
                    print(f"  {s.session_id} (created: {s.created_at})")

        elif cmd == "test":
            manager = SessionManager()
            print("Creating test session...")
            session = manager.create_session()
            print(f"  Session ID: {session.session_id}")
            print(f"  Session Dir: {session.session_dir}")
            print(f"  Models Dir: {session.models_dir}")

            print("\nSession files:")
            files = manager.get_session_files(session.session_id)
            for k, v in files.items():
                print(f"  {k}: {v or '(not created yet)'}")

            print("\nCleaning up test session...")
            manager.cleanup_session(session.session_id)
            print("Done!")
    else:
        print("Usage: python session_manager.py [cleanup|list|test]")
