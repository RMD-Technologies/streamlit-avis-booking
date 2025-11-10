def normalize_to_range(values, new_min=1, new_max=50):
    old_min, old_max = min(values), max(values)
    if old_min == old_max:  # avoid division by zero
        return [new_min] * len(values)
    
    return [
        int(round((v - old_min) / (old_max - old_min) * (new_max - new_min) + new_min))
        for v in values
    ]