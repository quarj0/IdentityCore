from pathlib import Path

path = Path('backend/django/apps/identity_documents/tasks.py')
text = path.read_text()


def guard_block(text, header, end_marker, label):
    start = text.find(header)
    if start < 0:
        raise RuntimeError(f'{label}: header not found')
    body_start = start + len(header)
    end = text.find(end_marker, body_start) if end_marker else len(text)
    if end < 0:
        raise RuntimeError(f'{label}: end marker not found')
    body = text[body_start:end]
    indented = ''.join(('    ' + line) if line.strip() else line for line in body.splitlines(True))
    guard = (
        '        with transaction.atomic():\n'
        '            lock_processing_job_for_finalization(processing_job)\n'
    )
    return text[:body_start] + guard + indented + text[end:]


text = guard_block(
    text,
    '    except ProviderRouteExhausted as exc:\n',
    '    except AIServiceUnavailable:\n',
    'route exhaustion failure writes',
)
text = guard_block(
    text,
    '    except Exception as exc:\n',
    None,
    'generic document failure writes',
)
path.write_text(text)
print('document failure ownership guards applied')
