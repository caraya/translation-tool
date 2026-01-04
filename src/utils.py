import datetime


def format_timestamp(seconds: float) -> str:
    """
    Formats a timestamp in seconds to SRT format (HH:MM:SS,mmm).
    """
    td = datetime.timedelta(seconds=seconds)
    # SRT format: 00:00:00,000
    # timedelta str is usually H:MM:SS.micros or [D day[s], ]H:MM:SS[.micros]

    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int(td.microseconds / 1000)

    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def write_srt(subtitles, output_path):
    """
    Writes subtitles to an SRT file.
    subtitles: list of dicts with 'start', 'end', 'text'
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for i, sub in enumerate(subtitles, start=1):
            start = format_timestamp(sub['start'])
            end = format_timestamp(sub['end'])
            text = sub['text'].strip()
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
