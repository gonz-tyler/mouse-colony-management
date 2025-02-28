from datetime import datetime

def add_current_year(request):
    """
    Add the current year to the context for use in templates.
    """
    return {'current_year': datetime.now().year}
