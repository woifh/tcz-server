"""Helper functions for tests."""


def split_name(full_name):
    """Split a full name into firstname and lastname.
    
    Args:
        full_name: Full name string (e.g., "John Doe")
        
    Returns:
        tuple: (firstname, lastname)
    """
    parts = full_name.strip().split(maxsplit=1)
    if len(parts) == 1:
        return parts[0], parts[0]  # Use same name for both if only one part
    return parts[0], parts[1]
