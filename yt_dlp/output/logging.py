import logging
import os
import shutil
import subprocess
import sys
import traceback
from enum import Enum

from .hoodoo import Color, TermCode, format_text
from .logging_output import logger as _logging_logger
from ..compat import functools
from ..utils import (
    deprecation_warning,
    supports_terminal_sequences,
    variadic,
    write_string,
)


class LogLevel(Enum):
    SCREEN = 0
    PROGRESS = 1
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40


class Verbosity(Enum):
    QUIET = 0
    NORMAL = 1
    VERBOSE = 2


class _OutputBase:
    allow_bidi = False
    use_color = False

    def format(self, text, *text_formats):
        if not self.use_color:
            return text

        return format_text(text, *text_formats)

    def log(self, message):
        pass


class StreamOutput(_OutputBase):
    allow_bidi = True

    def __init__(self, stream, use_color, encoding):
        self._stream = stream
        self._encoding = encoding
        self.use_color = use_color and supports_terminal_sequences(stream)

    def log(self, message):
        write_string(message, self._stream, self._encoding)


class ClassOutput(_OutputBase):
    def __init__(self, func):
        self._logging_function = func

    def log(self, message):
        self._logging_function(message.rstrip())


class LoggingOutput(_OutputBase):
    def __init__(self, level):
        self.level = level

    def log(self, message):
        message = message.rstrip()
        removable_prefixes = ['[debug] ', 'ERROR: ', 'WARNING: ']
        for prefix in removable_prefixes:
            if message.startswith(prefix):
                message = message[len(prefix):]
        if message.startswith('['):
            message = message.partition(']')[2].lstrip()
        _logging_logger.log(self.level, message)


class NullOutput(_OutputBase):
    def __bool__(self):
        return False


NULL_OUTPUT = NullOutput()


class _LoggerProxy:
    def __init__(self, obj, **kwargs):
        for name, wrapper in kwargs.items():
            original = getattr(obj, name)
            # XXX(output): Wrapper needs no reference to obj
            override = wrapper(original)
            functools.update_wrapper(override, original)
            setattr(self, name, override)

        self.__obj = obj

    def __getattr__(self, name):
        return getattr(self.__obj, name)


class Style:
    HEADER = TermCode.make(Color.YELLOW)
    EMPHASIS = TermCode.make(Color.LIGHT | Color.BLUE)
    FILENAME = TermCode.make(Color.GREEN)
    ID = TermCode.make(Color.GREEN)
    DELIM = TermCode.make(Color.BLUE)
    ERROR = TermCode.make(Color.RED)
    WARNING = TermCode.make(Color.YELLOW)
    SUPPRESS = TermCode.make(Color.LIGHT | Color.BLACK)


class Logger:
    """
    A YoutubeDL output/logging facility

    After instancing, one of the following functions MUST be called:
    - `setup_stream_logger`
    - `setup_class_logger`
    - `setup_logging_logger`
    You are free to call any of the setup functions more than once.

    To enable the bidirectional workaround, call `init_bidi_workaround()`.
    You SHOULD NOT call `init_bidi_workaround` more than once.

    The logger for LogLevel.SCREEN will always be a `StreamLogger`.
    """

    def __init__(self, screen, verbosity=Verbosity.NORMAL,
                 *, encoding=None, allow_color=False):
        self._bidi_initalized = False
        self._message_cache = set()
        self._pref_encoding = encoding
        self._allow_color = allow_color
        self._verbosity = verbosity

        screen_output = NULL_OUTPUT if screen is None else StreamOutput(screen, allow_color, encoding)
        # TODO(output): remove type hint
        self.mapping: dict[LogLevel, _OutputBase] = {LogLevel.SCREEN: screen_output}

    def make_derived(self, screen=None, debug=None, info=None, warning=None, error=None, handle_error=None) -> 'Logger':
        kwargs = {
            'screen': screen,
            'debug': debug,
            'info': info,
            'warning': warning,
            'error': error,
            'handle_error': handle_error,
        }

        return _LoggerProxy(self, **{key: value for key, value in kwargs.items() if value})

    def setup_stream_logger(self, stdout, stderr, *, no_warnings=False):
        stdout_output = NULL_OUTPUT if stdout is None else StreamOutput(stdout, self._allow_color, self._pref_encoding)
        stderr_output = NULL_OUTPUT if stderr is None else StreamOutput(stderr, self._allow_color, self._pref_encoding)

        self.mapping.update({
            LogLevel.DEBUG: (
                stderr_output if self._verbosity is Verbosity.VERBOSE
                else NULL_OUTPUT),
            LogLevel.INFO: stdout_output,
            LogLevel.WARNING: NULL_OUTPUT if no_warnings else stderr_output,
            LogLevel.ERROR: stderr_output,
        })
        return self

    def setup_class_logger(self, logger):
        debug_logger = ClassOutput(logger.debug)
        error_logger = ClassOutput(logger.error)
        warning_logger = ClassOutput(logger.warning)

        self.mapping.update({
            LogLevel.DEBUG: debug_logger,
            LogLevel.INFO: debug_logger,
            LogLevel.WARNING: warning_logger,
            LogLevel.ERROR: error_logger,
        })
        return self

    def setup_logging_logger(self):
        self.mapping.update({
            LogLevel.DEBUG: LoggingOutput(logging.DEBUG),
            LogLevel.INFO: LoggingOutput(logging.INFO),
            LogLevel.WARNING: LoggingOutput(logging.WARNING),
            LogLevel.ERROR: LoggingOutput(logging.ERROR),
        })
        return self

    def log(self, level, message, *, newline=True, once=False, suppress=False, trace=None, prefix=None):
        logger = self.mapping.get(level)
        if not logger or suppress:
            return

        assert isinstance(message, str)

        if once:
            if message in self._message_cache:
                return
            self._message_cache.add(message)

        if logger.allow_bidi and self._bidi_initalized:
            message = self._apply_bidi_workaround(message)

        if prefix:
            message = ' '.join((*map(str, variadic(prefix)), message))

        # XXX: Might have to call twice instead of append for compat
        if level is LogLevel.ERROR and self._verbosity is Verbosity.VERBOSE:
            message += '\n'
            if trace is not None:
                message += str(trace)

            elif sys.exc_info()[0]:  # called from an except block
                if hasattr(sys.exc_info()[1], 'exc_info') and sys.exc_info()[1].exc_info[0]:
                    message += ''.join(traceback.format_exception(*sys.exc_info()[1].exc_info))
                message += traceback.format_exc()

            else:
                message += ''.join(traceback.format_list(traceback.extract_stack()))

        if newline:
            message += '\n'

        logger.log(message)

    def format(self, level, text, *text_formats):
        logger = self.mapping.get(level)
        if not logger:
            return text

        return logger.format(str(text), *text_formats)

    def try_encoding(self, level, text, fallback_text, pref_encoding=None):
        logger = self.mapping.get(level)
        if not isinstance(logger, StreamOutput):
            return text

        # stream.encoding can be None. See https://github.com/yt-dlp/yt-dlp/issues/2711
        encoding = pref_encoding or getattr(logger._stream, 'encoding', None) or 'ascii'
        round_trip = text.encode(encoding, 'ignore').decode(encoding)

        return text if round_trip == text else fallback_text

    def screen(self, message, newline=True):
        """Print message to screen"""
        self.log(LogLevel.SCREEN, message, newline=newline)

    def debug(self, message, once=False):
        """Print debug message to stderr"""
        self.log(LogLevel.DEBUG, message, once=once)

    def info(self, message, newline=True, quiet=None, once=False):
        """Print message to stdout"""
        suppress = (
            False if self._verbosity is Verbosity.VERBOSE
            else quiet if quiet is not None
            else self._verbosity is Verbosity.QUIET)

        self.log(LogLevel.INFO, message, suppress=suppress, newline=newline, once=once)

    def warning(self, message, once=False):
        """
        Print a message to stderr, prefixed with 'WARNING:'
        If stderr is a tty file the prefix will be colored
        """
        self.log(LogLevel.WARNING, message, once=once,
                 prefix=self.format(LogLevel.WARNING, "WARNING:", Style.WARNING))

    def deprecation_warning(self, message, *, stacklevel=0):
        deprecation_warning(
            message, stacklevel=stacklevel + 1, printer=self.handle_error,
            is_error=False, prefix=True)

    def deprecated_feature(self, message):
        self.log(LogLevel.WARNING, message, once=True,
                 prefix=self.format(LogLevel.WARNING, "Deprecated Feature:", Style.ERROR))

    def error(self, message, once=False):
        """Print message to stderr"""
        self.log(LogLevel.ERROR, message, once=once)

    def handle_error(self, message, trace=None, is_error=True, prefix=True):
        """
        Determine action to take when a download problem appears.
        Optionally prefix the message with 'ERROR:'.
        If stderr is a tty the prefix will be colored.

        @param trace       If given, is additional traceback information
        @param is_error    Useful only in a derived logger
        """
        if prefix:
            prefix = self.format(LogLevel.ERROR, "ERROR:", Style.ERROR)

        self.log(LogLevel.ERROR, message, trace=trace, prefix=prefix)

    def init_bidi_workaround(self):
        import pty

        master, slave = pty.openpty()
        width = shutil.get_terminal_size().columns
        width_args = [] if width is None else ['-w', str(width)]
        sp_kwargs = {'stdin': subprocess.PIPE, 'stdout': slave, 'stderr': sys.stderr}
        try:
            _output_process = subprocess.Popen(['bidiv'] + width_args, **sp_kwargs)
        except OSError:
            _output_process = subprocess.Popen(['fribidi', '-c', 'UTF-8'] + width_args, **sp_kwargs)

        assert _output_process.stdin is not None
        self._bidi_writer = _output_process.stdin
        self._bidi_reader = os.fdopen(master, 'rb')
        self._bidi_initalized = True

    def _apply_bidi_workaround(self, message):
        # `init_bidi_workaround()` MUST have been called prior.
        line_count = message.count('\n') + 1

        self._bidi_writer.write(f'{message}\n')
        self._bidi_writer.flush()
        result = b''.join(self._bidi_reader.readlines(line_count)).decode()
        return result[:-1]


default_logger = Logger(None, Verbosity.QUIET)
default_logger.setup_stream_logger(None, sys.stderr)
