from pathlib import Path


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


# Mirror the biometric stale-worker ownership guard on document failure paths.
path = Path('backend/django/apps/identity_documents/tasks.py')
text = path.read_text()
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

# The stricter recovery validator intentionally requires the canonical provider
# contract capability. Make the existing committed-result regression fixture
# represent the same normalized envelope produced by real provider execution.
path = Path('backend/django/apps/verifications/test_processing_job_review_races.py')
text = path.read_text()
old = '''            normalized_result={\n                "passed": True,\n                "score": 0.99,\n'''
new = '''            normalized_result={\n                "capability": ProviderCheckType.LIVENESS,\n                "passed": True,\n                "score": 0.99,\n'''
if text.count(old) != 1:
    raise RuntimeError(f'canonical recovery fixture: expected one match, found {text.count(old)}')
path.write_text(text.replace(old, new, 1))

print('document failure guards and canonical recovery fixture applied')
