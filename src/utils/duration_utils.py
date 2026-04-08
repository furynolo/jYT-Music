def parse_duration_to_seconds(dur_str):
    """
    Parses duration strings like "4:20", "15:00", or "1:05:30" into total seconds.
    """
    if not dur_str or ":" not in dur_str:
        return 0
    
    parts = dur_str.split(':')
    try:
        if len(parts) == 3: # H:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2: # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, IndexError):
        return 0
    return 0

def format_seconds_to_human(total_seconds):
    """
    Formats seconds into a human-readable string like "2 hours 15 minutes" or "45 minutes".
    """
    if total_seconds <= 0:
        return ""
        
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    
    if hours > 0:
        h_str = f"{hours} hour" + ("s" if hours > 1 else "")
        m_str = f"{minutes} minute" + ("s" if minutes > 1 else "")
        if minutes == 0:
            return h_str
        return f"{h_str} {m_str}"
    
    m_str = f"{minutes} minute" + ("s" if minutes > 1 else "")
    if minutes == 0:
        return f"{total_seconds} seconds"
    return m_str
