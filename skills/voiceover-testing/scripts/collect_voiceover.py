#!/usr/bin/env python3
"""Sample native VoiceOver last-phrase changes. Never enable, speak or navigate."""
import argparse
import datetime
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

SCRIPT = '''with timeout of 2 seconds
if application id "com.apple.VoiceOver" is not running then error "VoiceOver is not running"
tell application id "com.apple.VoiceOver" to get content of last phrase
end timeout'''


def native_phrase():
    result = subprocess.run(
        ['/usr/bin/osascript', '-e', SCRIPT], capture_output=True,
        text=True, timeout=3, check=False)
    if result.returncode:
        raise RuntimeError(f'osascript exit {result.returncode}: {result.stderr.strip()}')
    return result.stdout.rstrip('\n')


def collect(seconds, state, emit, read=native_phrase, clock=time.monotonic,
            sleep=time.sleep):
    """Return 0 on bounded collection completion; completion is not a test verdict.

    phrase_count in the stop row counts emitted phrases: 1 means only the phrase
    already present at start was seen, so no fresh announcement was captured.
    """
    previous = None
    count = 0
    emit({'kind': 'start', 'state': state, 'seconds': seconds,
          'source': 'voiceover.native.last_phrase',
          'limitations': 'Polling deduplicates consecutive values; not an exhaustive speech stream'})
    start = clock()
    try:
        while clock() - start < seconds:
            phrase = read()
            if phrase != previous:
                emit({'kind': 'phrase', 'state': state,
                      'source': 'voiceover.native.last_phrase', 'phrase': phrase})
                previous = phrase
                count += 1
            sleep(0.1)
    except KeyboardInterrupt:
        emit({'kind': 'stop', 'state': state, 'reason': 'interrupted',
              'phrase_count': count})
        return 130
    except (subprocess.TimeoutExpired, RuntimeError, OSError) as exc:
        emit({'kind': 'error', 'state': state, 'error': str(exc),
              'phrase_count': count})
        return 1
    emit({'kind': 'stop', 'state': state, 'reason': 'duration_elapsed',
          'phrase_count': count})
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=30)
    parser.add_argument('--state', required=True, help='Single observed UI state for this capture')
    parser.add_argument('--output', required=True, type=Path, help='New private JSONL file')
    args = parser.parse_args()
    if not math.isfinite(args.seconds) or not 0 < args.seconds <= 3600:
        parser.error('--seconds must be finite, positive and <= 3600')
    if not args.state.strip():
        parser.error('--state must not be empty')
    if sys.platform != 'darwin':
        parser.error('Native VoiceOver collection requires macOS')
    # Exclusive creation prevents overwriting earlier proof or modifying its permissions.
    try:
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except (FileExistsError, FileNotFoundError):
        parser.error('--output must be a new file in an existing directory')
    with os.fdopen(fd, 'w', encoding='utf-8') as output:
        def emit(row):
            row['timestamp'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            output.write(json.dumps(row, ensure_ascii=False) + '\n')
            output.flush()
        return collect(args.seconds, args.state, emit)


if __name__ == '__main__':
    sys.exit(main())
