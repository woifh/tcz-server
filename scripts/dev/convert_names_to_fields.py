#!/usr/bin/env python3
"""
Script to help convert name= to firstname= and lastname= in test files.
This is a helper script - review changes before committing!
"""
import re
import sys

def split_name(full_name):
    """Split a full name into firstname and lastname."""
    parts = full_name.strip().split(maxsplit=1)
    if len(parts) == 1:
        return parts[0], parts[0]
    return parts[0], parts[1]

def convert_member_creation(match):
    """Convert Member(name="Full Name") to Member(firstname="First", lastname="Last")."""
    full_match = match.group(0)
    name_value = match.group(1)
    
    # Split the name
    firstname, lastname = split_name(name_value)
    
    # Replace in the original string
    result = full_match.replace(
        f'name="{name_value}"',
        f'firstname="{firstname}", lastname="{lastname}"'
    )
    result = result.replace(
        f"name='{name_value}'",
        f"firstname='{firstname}', lastname='{lastname}'"
    )
    
    return result

def convert_file(filepath):
    """Convert a single file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Pattern to match Member(name="...")
        pattern = r'Member\([^)]*name=["\']([^"\']+)["\'][^)]*\)'
        
        # Find all matches
        matches = list(re.finditer(pattern, content))
        
        if not matches:
            print(f"No matches found in {filepath}")
            return
        
        print(f"\nFound {len(matches)} Member creations in {filepath}")
        print("=" * 60)
        
        # Process each match
        for match in matches:
            print(f"\nOriginal: {match.group(0)}")
            converted = convert_member_creation(match)
            print(f"Converted: {converted}")
            content = content.replace(match.group(0), converted)
        
        # Ask for confirmation
        response = input(f"\nApply changes to {filepath}? (y/n): ")
        if response.lower() == 'y':
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"✓ Updated {filepath}")
        else:
            print("Skipped")
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python convert_names_to_fields.py <file1> [file2] ...")
        print("\nExample:")
        print("  python convert_names_to_fields.py tests/test_member_service.py")
        sys.exit(1)
    
    for filepath in sys.argv[1:]:
        convert_file(filepath)
