"""
Novelist CLI - Command line interface for the novelist project.

Commands:
    init        - Create new project
    write       - Generate scene (2-stage pipeline)
    status      - Show project status
    session     - Manage sessions
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.project import ProjectManager
from parsers.bible_parser import BibleLoader
from parsers.character_loader import CharacterLoader
from pipeline.two_stage import SimplePipeline


def cmd_init(args):
    """Initialize new project."""
    project_path = Path(args.path).resolve()
    
    try:
        ProjectManager.create(project_path, args.name)
        print(f"✓ Created project: {project_path}")
        print(f"  Name: {args.name or project_path.name}")
        print(f"\nNext steps:")
        print(f"  1. Edit {project_path}/bible.md")
        print(f"  2. Add characters to {project_path}/characters/")
        print(f"  3. Run: novelist write --project {project_path} -d 'Scene description'")
    except FileExistsError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


def cmd_write(args):
    """Generate scene using 2-stage pipeline."""
    project_path = Path(args.project).resolve()
    
    # Validate project
    is_valid, issues = ProjectManager.validate(project_path)
    if not is_valid:
        print(f"✗ Invalid project:")
        for issue in issues:
            print(f"  - {issue}")
        sys.exit(1)
    
    print(f"Generating scene...")
    print(f"  Project: {project_path}")
    print(f"  Description: {args.description}")
    print(f"  Words: {args.words}")
    print()
    
    try:
        # Use 2-stage pipeline
        pipeline = SimplePipeline(project_path)
        text = pipeline.write_scene(
            description=args.description,
            chapter=args.chapter or 1,
            word_count=args.words
        )
        
        print(f"\n{'='*60}")
        print(text)
        print(f"{'='*60}")
        print(f"\n✓ Scene generated and saved")
        
    except Exception as e:
        print(f"✗ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_status(args):
    """Show project status."""
    project_path = Path(args.project).resolve()
    
    is_valid, issues = ProjectManager.validate(project_path)
    
    print(f"Project: {project_path}")
    print(f"Status: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    if issues:
        print(f"\nIssues:")
        for issue in issues:
            print(f"  - {issue}")
    
    if is_valid:
        # Show bible info
        try:
            bible = BibleLoader.load(project_path)
            print(f"\nBible loaded")
        except Exception as e:
            print(f"\nBible: Error - {e}")
        
        # Show characters
        chars = CharacterLoader.list_characters(project_path)
        print(f"\nCharacters ({len(chars)}):")
        for char_id in chars:
            print(f"  - {char_id}")
        
        # Show chapters
        from core.project import ChapterManager
        chapters = ChapterManager.list_chapters(project_path)
        print(f"\nChapters ({len(chapters)}):")
        for ch in chapters:
            print(f"  - Chapter {ch}")
        
        # Show sessions
        from session.manager import SessionManager
        sessions = SessionManager.list_sessions(project_path)
        print(f"\nSessions ({len(sessions)}):")
        for s in sessions[:5]:
            print(f"  - {s['session_id']} (Ch.{s['chapter']}, Sc.{s['scene']})")


def cmd_session(args):
    """Manage sessions."""
    project_path = Path(args.project).resolve()
    from session.manager import SessionManager
    
    if args.list:
        sessions = SessionManager.list_sessions(project_path)
        print(f"Sessions ({len(sessions)}):")
        for s in sessions:
            print(f"  {s['session_id']} | Ch.{s['chapter']} Sc.{s['scene']} | {s['created_at'][:10]}")
    
    elif args.delete:
        SessionManager.delete_session(project_path, args.delete)
        print(f"✓ Deleted session {args.delete}")


def main():
    parser = argparse.ArgumentParser(
        prog='novelist',
        description='AI Novel Writing Assistant'
    )
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # init command
    init_parser = subparsers.add_parser('init', help='Create new project')
    init_parser.add_argument('path', help='Project directory path')
    init_parser.add_argument('--name', help='Project name (default: directory name)')
    
    # write command
    write_parser = subparsers.add_parser('write', help='Generate scene (2-stage pipeline)')
    write_parser.add_argument('--project', '-p', default='.', help='Project path')
    write_parser.add_argument('--description', '-d', required=True, help='Scene description')
    write_parser.add_argument('--words', '-w', type=int, default=1000, help='Target word count')
    write_parser.add_argument('--chapter', '-c', type=int, help='Chapter number')
    
    # status command
    status_parser = subparsers.add_parser('status', help='Show project status')
    status_parser.add_argument('--project', '-p', default='.', help='Project path')
    
    # session command
    session_parser = subparsers.add_parser('session', help='Manage sessions')
    session_parser.add_argument('--project', '-p', default='.', help='Project path')
    session_parser.add_argument('--list', '-l', action='store_true', help='List sessions')
    session_parser.add_argument('--delete', '-d', help='Delete session ID')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        cmd_init(args)
    elif args.command == 'write':
        cmd_write(args)
    elif args.command == 'status':
        cmd_status(args)
    elif args.command == 'session':
        cmd_session(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
