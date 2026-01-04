"""Anonymous data filtering service for protecting member privacy."""


class AnonymousDataFilter:
    """Service for filtering sensitive data for anonymous users."""
    
    @staticmethod
    def filter_availability_data(grid_data, is_authenticated):
        """
        Filter court availability data based on user authentication status.
        
        For anonymous users, removes all member information from reservations
        while preserving block information and availability status.
        
        Args:
            grid_data: List of court availability data with slots
            is_authenticated: Boolean indicating if user is authenticated
            
        Returns:
            list: Filtered grid data appropriate for user's authentication status
        """
        if is_authenticated:
            # Return original data for authenticated users
            return grid_data
        
        # Create a deep copy to avoid modifying original data
        filtered_grid = []
        
        for court in grid_data:
            filtered_court = {
                'court_id': court['court_id'],
                'court_number': court['court_number'],
                'slots': []
            }
            
            for slot in court['slots']:
                filtered_slot = {
                    'time': slot['time'],
                    'status': slot['status'],
                    'details': slot['details']
                }
                
                # Filter reservation details for anonymous users
                if slot['status'] in ['reserved', 'short_notice']:
                    # Normalize short_notice to reserved for anonymous users
                    filtered_slot['status'] = 'reserved'
                    # Remove all member information
                    filtered_slot['details'] = None
                
                # Block information remains unchanged for anonymous users
                # This preserves block reasons and details as specified in requirements 3.1, 3.2
                
                filtered_court['slots'].append(filtered_slot)
            
            filtered_grid.append(filtered_court)
        
        return filtered_grid