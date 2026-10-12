"""Run tests and write a compact report for GitHub Actions artifacts."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
result = unittest.TextTestRunner(verbosity=2).run(suite)
report = {'tests': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
          'successful': result.wasSuccessful(),
          'details': [{'test': str(test), 'traceback': trace} for test, trace in result.failures + result.errors]}
(ROOT / 'reports').mkdir(exist_ok=True)
(ROOT / 'reports' / 'tests.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
sys.exit(0 if result.wasSuccessful() else 1)
