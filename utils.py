
def parse_time_mmss_to_min(time_str: str) -> float:
    mm, ss = time_str.split(":")
    return int(mm) + int(ss) / 60.0
