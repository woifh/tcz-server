"""Version information for the application."""
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess
import os
import re
import logging
from typing import Optional

# Set up logging for version operations
logger = logging.getLogger(__name__)

# Get repository root directory
def get_repo_root():
    """Get the repository root directory."""
    return os.path.dirname(os.path.dirname(__file__))

def get_git_commit_hash():
    """Get the current git commit hash.
    
    Returns:
        Short commit hash string, or "unknown" if unavailable
        
    Requirements: 3.4
    """
    try:
        if not is_git_available():
            logger.debug("Git not available, cannot get commit hash")
            return "unknown"
            
        if not is_git_repository():
            logger.debug("Not in Git repository, cannot get commit hash")
            return "unknown"
            
        result = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL,
            cwd=get_repo_root()
        ).decode('utf-8').strip()
        
        logger.debug(f"Retrieved commit hash: {result}")
        return result
        
    except subprocess.CalledProcessError as e:
        logger.warning(f"Git rev-parse command failed: {e}")
        return "unknown"
    except Exception as e:
        logger.warning(f"Error getting git commit hash: {e}")
        return "unknown"

def get_git_branch():
    """Get the current git branch.
    
    Returns:
        Branch name string, or "unknown" if unavailable
        
    Requirements: 3.2, 3.3
    """
    try:
        if not is_git_available():
            logger.debug("Git not available, cannot get branch")
            return "unknown"
            
        if not is_git_repository():
            logger.debug("Not in Git repository, cannot get branch")
            return "unknown"
            
        result = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stderr=subprocess.DEVNULL,
            cwd=get_repo_root()
        ).decode('utf-8').strip()
        
        logger.debug(f"Retrieved branch: {result}")
        return result
        
    except subprocess.CalledProcessError as e:
        logger.warning(f"Git branch command failed: {e}")
        return "unknown"
    except Exception as e:
        logger.warning(f"Error getting git branch: {e}")
        return "unknown"

def get_last_commit_date():
    """Get the date of the last commit.
    
    Returns:
        Formatted date string, or "unknown" if unavailable
        
    Requirements: 3.2, 3.3
    """
    try:
        if not is_git_available():
            logger.debug("Git not available, cannot get last commit date")
            return "unknown"
            
        if not is_git_repository():
            logger.debug("Not in Git repository, cannot get last commit date")
            return "unknown"
            
        timestamp = subprocess.check_output(
            ['git', 'log', '-1', '--format=%ct'],
            stderr=subprocess.DEVNULL,
            cwd=get_repo_root()
        ).decode('utf-8').strip()
        
        formatted_date = datetime.fromtimestamp(int(timestamp), tz=ZoneInfo('Europe/Berlin')).strftime('%Y-%m-%d %H:%M:%S')
        logger.debug(f"Retrieved last commit date: {formatted_date}")
        return formatted_date
        
    except subprocess.CalledProcessError as e:
        logger.warning(f"Git log command failed: {e}")
        return "unknown"
    except (ValueError, OSError) as e:
        logger.warning(f"Error parsing commit date: {e}")
        return "unknown"
    except Exception as e:
        logger.warning(f"Error getting last commit date: {e}")
        return "unknown"

# Git Operations Layer

def get_latest_version_tag() -> Optional[str]:
    """Get the most recent version tag from Git history.
    
    Returns:
        The latest version tag string, or None if no valid version tags found.
        
    Requirements: 1.1, 1.2, 1.3, 5.4, 3.2, 3.3
    """
    try:
        if not is_git_available():
            logger.warning("Git not available, cannot get version tags")
            return None
            
        if not is_git_repository():
            logger.warning("Not in Git repository, cannot get version tags")
            return None
        
        # Get all tags sorted by version (most recent first)
        result = subprocess.check_output([
            'git', 'tag', '--sort=-version:refname'
        ], stderr=subprocess.DEVNULL, cwd=get_repo_root())
        
        tags = result.decode('utf-8').strip().split('\n')
        
        # Filter out empty strings in case there are no tags
        tags = [tag for tag in tags if tag.strip()]
        
        if not tags:
            logger.info("No Git tags found in repository")
            return None
        
        logger.debug(f"Found {len(tags)} total tags in repository")
        
        # Filter to only valid version tags
        valid_tags = filter_version_tags(tags)
        
        if valid_tags:
            latest_tag = valid_tags[0]  # Already sorted by version (most recent first)
            logger.info(f"Found latest version tag: {latest_tag}")
            return latest_tag
        else:
            logger.info("No valid version tags found among existing tags")
            if len(tags) > 0:
                logger.debug(f"Repository contains {len(tags)} non-version tags that were ignored")
            return None
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git tag command failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting latest version tag: {e}")
        return None

def count_commits_since_tag(tag: str) -> int:
    """Count commits since the specified tag.
    
    Args:
        tag: The Git tag to count commits from
        
    Returns:
        Number of commits since the tag, or 0 if counting fails
        
    Requirements: 2.1, 2.2, 3.2, 3.3
    """
    try:
        if not is_git_available():
            logger.warning("Git not available, cannot count commits since tag")
            return 0
            
        if not is_git_repository():
            logger.warning("Not in Git repository, cannot count commits since tag")
            return 0
        
        result = subprocess.check_output([
            'git', 'rev-list', '--count', f'{tag}..HEAD'
        ], stderr=subprocess.DEVNULL, cwd=get_repo_root())
        
        count = int(result.decode('utf-8').strip())
        logger.debug(f"Found {count} commits since tag {tag}")
        return count
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git rev-list command failed for tag {tag}: {e}")
        return 0
    except ValueError as e:
        logger.error(f"Failed to parse commit count for tag {tag}: {e}")
        return 0
    except Exception as e:
        logger.error(f"Error counting commits since tag {tag}: {e}")
        return 0

def count_total_commits() -> int:
    """Count total commits in the repository.
    
    Returns:
        Total number of commits, or 0 if counting fails
        
    Requirements: 3.1, 3.2, 3.3
    """
    try:
        if not is_git_available():
            logger.warning("Git not available, cannot count total commits")
            return 0
            
        if not is_git_repository():
            logger.warning("Not in Git repository, cannot count total commits")
            return 0
        
        result = subprocess.check_output([
            'git', 'rev-list', '--count', 'HEAD'
        ], stderr=subprocess.DEVNULL, cwd=get_repo_root())
        
        count = int(result.decode('utf-8').strip())
        logger.debug(f"Found {count} total commits")
        return count
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git rev-list command failed for total commits: {e}")
        return 0
    except ValueError as e:
        logger.error(f"Failed to parse total commit count: {e}")
        return 0
    except Exception as e:
        logger.error(f"Error counting total commits: {e}")
        return 0

def parse_version_tag(tag: str) -> str:
    """Parse and normalize a version tag (strip 'v' prefix, etc.).
    
    Args:
        tag: The Git tag to parse
        
    Returns:
        Normalized version string
        
    Requirements: 5.1, 5.2, 5.3
    """
    if not tag:
        return "0.0.0"
    
    # Strip 'v' prefix if present
    normalized = tag.lstrip('v')
    
    # If the tag contains additional information after the version (e.g., "1.2.3-beta"),
    # we keep it as per requirement 5.3
    logger.debug(f"Parsed tag '{tag}' to version '{normalized}'")
    return normalized

def is_valid_version_tag(tag: str) -> bool:
    """Check if a tag matches version patterns.
    
    Args:
        tag: The Git tag to validate
        
    Returns:
        True if the tag is a valid version tag, False otherwise
        
    Requirements: 5.4
    """
    if not tag:
        logger.debug("Empty tag provided, marking as invalid")
        return False
    
    # Remove 'v' prefix for pattern matching
    normalized = tag.lstrip('v')
    
    # Skip tags that are clearly not versions (common non-version tag patterns)
    non_version_patterns = [
        r'^release[-_]',  # release-*, release_*
        r'^build[-_]',    # build-*, build_*
        r'^deploy[-_]',   # deploy-*, deploy_*
        r'^test[-_]',     # test-*, test_*
        r'^dev[-_]',      # dev-*, dev_*
        r'^staging[-_]',  # staging-*, staging_*
        r'^prod[-_]',     # prod-*, prod_*
        r'^hotfix[-_]',   # hotfix-*, hotfix_*
        r'^feature[-_]',  # feature-*, feature_*
        r'^bugfix[-_]',   # bugfix-*, bugfix_*
    ]
    
    for pattern in non_version_patterns:
        if re.match(pattern, normalized, re.IGNORECASE):
            logger.debug(f"Tag '{tag}' matches non-version pattern, ignoring")
            return False
    
    # Match semantic version patterns: X.Y.Z with optional additional info
    # Examples: "1.2.3", "1.2.3-beta", "1.2.3-alpha.1", "1.2.3+build.1"
    pattern = r'^\d+\.\d+\.\d+(?:[-+].*)?$'
    
    is_valid = bool(re.match(pattern, normalized))
    
    if is_valid:
        logger.debug(f"Tag '{tag}' is a valid version tag")
    else:
        logger.debug(f"Tag '{tag}' does not match version pattern, ignoring")
    
    return is_valid


def filter_version_tags(tags: list[str]) -> list[str]:
    """Filter a list of tags to only include valid version tags.
    
    Args:
        tags: List of Git tags to filter
        
    Returns:
        List of valid version tags, sorted by version (most recent first)
        
    Requirements: 5.4
    """
    if not tags:
        logger.debug("No tags provided for filtering")
        return []
    
    # Filter out invalid tags
    valid_tags = [tag for tag in tags if is_valid_version_tag(tag)]
    
    logger.debug(f"Filtered {len(tags)} tags down to {len(valid_tags)} valid version tags")
    
    if valid_tags:
        logger.debug(f"Valid version tags found: {valid_tags}")
    else:
        logger.debug("No valid version tags found after filtering")
    
    return valid_tags

# Version Calculator

def parse_semantic_version(version_str: str) -> tuple[int, int, int, str]:
    """Parse a semantic version string into components.
    
    Args:
        version_str: Version string like "1.2.3" or "1.2.3-beta"
        
    Returns:
        Tuple of (major, minor, patch, suffix) where suffix includes any additional info
        
    Requirements: 2.1, 2.2
    """
    if not version_str:
        return (0, 0, 0, "")
    
    # Split on '-' or '+' to separate version from suffix
    parts = re.split(r'[-+]', version_str, 1)
    version_part = parts[0]
    suffix = f"-{parts[1]}" if len(parts) > 1 and parts[1] else ""
    
    try:
        # Parse the main version numbers
        version_numbers = version_part.split('.')
        
        # Ensure we have at least 3 parts (major.minor.patch)
        while len(version_numbers) < 3:
            version_numbers.append('0')
        
        major = int(version_numbers[0])
        minor = int(version_numbers[1])
        patch = int(version_numbers[2])
        
        logger.debug(f"Parsed version '{version_str}' to ({major}, {minor}, {patch}, '{suffix}')")
        return (major, minor, patch, suffix)
        
    except (ValueError, IndexError) as e:
        logger.error(f"Failed to parse semantic version '{version_str}': {e}")
        return (0, 0, 0, "")

def increment_minor_version(base_version: str, increment: int) -> str:
    """Increment the minor version by the specified amount.
    
    Args:
        base_version: Base version string like "1.2.3"
        increment: Number to add to the minor version
        
    Returns:
        New version string with incremented minor version
        
    Requirements: 2.1, 2.2
    """
    if increment <= 0:
        return base_version
    
    major, minor, patch, suffix = parse_semantic_version(base_version)
    
    # Increment the minor version
    new_minor = minor + increment
    
    # Build the new version string (without suffix for clean versioning)
    new_version = f"{major}.{new_minor}.{patch}"
    
    logger.debug(f"Incremented version '{base_version}' by {increment} to '{new_version}'")
    return new_version

def is_git_available() -> bool:
    """Check if Git is available on the system.
    
    Returns:
        True if Git is available, False otherwise
        
    Requirements: 3.3
    """
    try:
        subprocess.check_output(['git', '--version'], stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return False

def is_git_repository() -> bool:
    """Check if we're in a Git repository.
    
    Returns:
        True if in a Git repository, False otherwise
        
    Requirements: 3.2
    """
    try:
        subprocess.check_output(
            ['git', 'rev-parse', '--git-dir'],
            stderr=subprocess.DEVNULL,
            cwd=get_repo_root()
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return False

def get_fallback_version_with_hash() -> str:
    """Get fallback version with commit hash if available.
    
    Returns:
        Fallback version string with commit hash when possible
        
    Requirements: 3.4
    """
    commit_hash = get_git_commit_hash()
    if commit_hash != "unknown":
        fallback_version = f"0.0.0-{commit_hash}"
        logger.info(f"Using fallback version with commit hash: {fallback_version}")
        return fallback_version
    else:
        logger.info("Using basic fallback version: 0.0.0-dev")
        return "0.0.0-dev"

def calculate_version_from_git() -> str:
    """Calculate version using Git tags and commit count.
    
    Returns:
        Calculated version string based on Git history
        
    Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 3.4
    """
    # Check if Git is available on the system
    if not is_git_available():
        logger.warning("Git is not available on the system, using fallback version")
        return get_fallback_version_with_hash()
    
    # Check if we're in a Git repository
    if not is_git_repository():
        logger.warning("Not in a Git repository, using fallback version")
        return get_fallback_version_with_hash()
    
    try:
        # Get base version from latest tag
        latest_tag = get_latest_version_tag()
        
        if latest_tag:
            base_version = parse_version_tag(latest_tag)
            commit_count = count_commits_since_tag(latest_tag)
            
            if commit_count > 0:
                # Increment minor version by commit count
                calculated_version = increment_minor_version(base_version, commit_count)
                logger.info(f"Calculated version: {calculated_version} (base: {base_version}, commits: {commit_count})")
                return calculated_version
            else:
                # No commits since tag, return tag version unchanged
                logger.info(f"Using tag version unchanged: {base_version}")
                return base_version
        else:
            # No tags found - count all commits from initial commit
            total_commits = count_total_commits()
            if total_commits > 0:
                fallback_version = f"0.{total_commits}.0"
                logger.info(f"No tags found, using fallback version with commit count: {fallback_version}")
                return fallback_version
            else:
                # No commits found either, use basic fallback
                logger.warning("No tags or commits found, using basic fallback version")
                return get_fallback_version_with_hash()
            
    except Exception as e:
        logger.error(f"Error calculating version from Git: {e}")
        logger.info("Falling back to version with commit hash")
        return get_fallback_version_with_hash()

def get_version_info():
    """Get complete version information."""
    return {
        'version': calculate_version_from_git(),
        'commit_hash': get_git_commit_hash(),
        'branch': get_git_branch(),
        'last_commit_date': get_last_commit_date(),
        'deployment_time': datetime.now(ZoneInfo('Europe/Berlin')).strftime('%Y-%m-%d %H:%M:%S')
    }