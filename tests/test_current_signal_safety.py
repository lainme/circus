"""
Test to demonstrate current signal handler safety issues.
"""
import signal
import threading
import time
from unittest import TestCase, skipIf
from unittest.mock import patch, MagicMock

from circus.sighandler import SysHandler
from circus.util import IS_WINDOWS


class TestCurrentSignalSafety(TestCase):
    """Test to show current signal handler has safety issues."""
    
    @skipIf(IS_WINDOWS, "Signal handling different on Windows")
    def test_current_signal_handler_unsafe_operations(self):
        """
        Demonstrate that current signal handler performs unsafe operations.
        """
        # Create a mock controller
        mock_controller = MagicMock()
        mock_loop = MagicMock()
        mock_controller.loop = mock_loop
        
        # Patch logger to track calls
        with patch('circus.sighandler.logger') as mock_logger:
            handler = SysHandler(mock_controller)
            
            # Trigger signal handler
            handler.signal(signal.SIGTERM)
            
            # Check that logger was called IN the signal handler
            # This is UNSAFE!
            mock_logger.info.assert_called_with('Got signal SIG_TERM')
            
            # The quit method was called, which then uses add_callback_from_signal
            # But the logging happened BEFORE we got to the safe part!
            mock_loop.add_callback_from_signal.assert_called()
            
    def test_signal_handler_performs_dictionary_lookups(self):
        """
        Show that signal handler does dictionary lookups (unsafe).
        """
        mock_controller = MagicMock()
        handler = SysHandler(mock_controller)
        
        # The signal method does:
        # 1. self.SIG_NAMES.get(sig) - Dictionary lookup (UNSAFE)
        # 2. getattr(self, "handle_%s" % signame) - Object attribute access (UNSAFE)
        # 3. String formatting with % - Memory allocation (UNSAFE)
        
        # All of these can cause problems in signal context
        
    def test_deadlock_scenario(self):
        """
        Demonstrate potential deadlock scenario.
        """
        # This is harder to demonstrate but the issue is:
        # 1. Main thread acquires logging lock
        # 2. Signal arrives, interrupting main thread
        # 3. Signal handler tries to log, needs same lock
        # 4. DEADLOCK - signal handler waits for lock held by interrupted thread
        print("\nDeadlock scenario:")
        print("1. Main thread: logger.info() acquires internal lock")
        print("2. SIGTERM arrives, interrupting main thread") 
        print("3. Signal handler: logger.info() tries to acquire same lock")
        print("4. DEADLOCK - handler waits for lock held by interrupted thread")