from collections import defaultdict
from contextvars import ContextVar

# NAME = 'yt-dlp'

postprocessors = ContextVar('postprocessors', default={})
extractors = ContextVar('extractors', default={})
IN_CLI = ContextVar('IN_CLI', default=False)
# `False`=force, `None`=disabled, `True`=enabled
LAZY_EXTRACTORS = ContextVar('LAZY_EXTRACTORS', default=False)

plugin_dirs = ContextVar('plugin_dirs', default=(..., ))
plugin_ies = ContextVar('plugin_ies', default={})
plugin_overrides = ContextVar('plugin_overrides', default=defaultdict(list))
plugin_pps = ContextVar('plugin_pps', default={})
