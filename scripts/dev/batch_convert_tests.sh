#!/bin/bash
# Batch convert all test files to use firstname/lastname

echo "Converting test files to use firstname/lastname..."
echo "=================================================="

# Use sed to replace Member(name="Full Name" with Member(firstname="First", lastname="Last"
# This is a simplified approach - review changes before committing!

find tests -name "*.py" -type f | while read file; do
    echo "Processing: $file"
    
    # Backup the file
    cp "$file" "$file.bak"
    
    # Simple replacements for common patterns
    sed -i '' 's/Member(name="Test Member"/Member(firstname="Test", lastname="Member"/g' "$file"
    sed -i '' 's/Member(name="Test User"/Member(firstname="Test", lastname="User"/g' "$file"
    sed -i '' "s/Member(name='Test User'/Member(firstname='Test', lastname='User'/g" "$file"
    sed -i '' 's/Member(name="Test Admin"/Member(firstname="Test", lastname="Admin"/g' "$file"
    sed -i '' 's/Member(name="Admin"/Member(firstname="Admin", lastname="User"/g' "$file"
    sed -i '' 's/Member(name="Member"/Member(firstname="Test", lastname="Member"/g' "$file"
    
    # Alice Smith
    sed -i '' 's/Member(name="Alice Smith"/Member(firstname="Alice", lastname="Smith"/g' "$file"
    sed -i '' "s/Member(name='Alice Smith'/Member(firstname='Alice', lastname='Smith'/g" "$file"
    
    # Bob Johnson
    sed -i '' 's/Member(name="Bob Johnson"/Member(firstname="Bob", lastname="Johnson"/g' "$file"
    sed -i '' "s/Member(name='Bob Johnson'/Member(firstname='Bob', lastname='Johnson'/g" "$file"
    
    # Alice Brown
    sed -i '' 's/Member(name="Alice Brown"/Member(firstname="Alice", lastname="Brown"/g' "$file"
    
    # Charlie Davis
    sed -i '' 's/Member(name="Charlie Davis"/Member(firstname="Charlie", lastname="Davis"/g' "$file"
    
    # Current User
    sed -i '' 's/Member(name="Current User"/Member(firstname="Current", lastname="User"/g' "$file"
    
    # Zoe Wilson
    sed -i '' 's/Member(name="Zoe Wilson"/Member(firstname="Zoe", lastname="Wilson"/g' "$file"
    
    # Bob Smith
    sed -i '' 's/Member(name="Bob Smith"/Member(firstname="Bob", lastname="Smith"/g' "$file"
    
    # Favourite Test
    sed -i '' 's/Member(name="Favourite Test"/Member(firstname="Favourite", lastname="Test"/g' "$file"
    sed -i '' "s/Member(name='Favourite Test'/Member(firstname='Favourite', lastname='Test'/g" "$file"
    
    # TestCase Member
    sed -i '' 's/Member(name="TestCase Member"/Member(firstname="TestCase", lastname="Member"/g' "$file"
    sed -i '' "s/Member(name='TestCase Member'/Member(firstname='TestCase', lastname='Member'/g" "$file"
    
    # Test Member 1
    sed -i '' 's/Member(name="Test Member 1"/Member(firstname="Test", lastname="Member1"/g' "$file"
    
    # Test Member 2
    sed -i '' 's/Member(name="Test Member 2"/Member(firstname="Test", lastname="Member2"/g' "$file"
    
    # Member For
    sed -i '' 's/Member(name="Member For"/Member(firstname="Member", lastname="For"/g' "$file"
    
    # Member By
    sed -i '' 's/Member(name="Member By"/Member(firstname="Member", lastname="By"/g' "$file"
    
    # Generic patterns with variables
    sed -i '' 's/Member(name=\([a-z_]*\)name,/Member(firstname=\1firstname, lastname=\1lastname,/g' "$file"
    sed -i '' 's/Member(name=name,/Member(firstname=firstname, lastname=lastname,/g' "$file"
    
    echo "  ✓ Converted: $file"
done

echo ""
echo "=================================================="
echo "Conversion complete!"
echo ""
echo "IMPORTANT: Review the changes before committing:"
echo "  git diff tests/"
echo ""
echo "To restore backups if needed:"
echo "  find tests -name '*.bak' -exec bash -c 'mv \"\$0\" \"\${0%.bak}\"' {} \;"
echo ""
echo "To remove backups:"
echo "  find tests -name '*.bak' -delete"
