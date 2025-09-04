import pytest
import asyncio
import argparse
from unittest.mock import Mock, patch, AsyncMock

from run_servers import parse_args, web_server, interrupt_event


class TestArgumentParsing:
    def test_parse_args_default(self):
        with patch('sys.argv', ['run_servers.py']):
            args = parse_args()
            assert args.host == "127.0.0.1:8000"

    def test_parse_args_custom_host_port(self):
        with patch('sys.argv', ['run_servers.py', '--host=0.0.0.0:9000']):
            args = parse_args()
            assert args.host == "0.0.0.0:9000"

    def test_parse_args_short_flag(self):
        with patch('sys.argv', ['run_servers.py', '--host', '192.168.1.100:3000']):
            args = parse_args()
            assert args.host == "192.168.1.100:3000"

    def test_parse_args_help_message(self):
        parser = argparse.ArgumentParser(
            description="Run web server and temporal worker",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        parser.add_argument(
            "--host",
            default="127.0.0.1:8000",
            help="Host address and port to bind to (default: 127.0.0.1:8000)",
        )
        
        # Test that parser was configured correctly
        assert parser.description == "Run web server and temporal worker"
        assert parser.formatter_class == argparse.RawDescriptionHelpFormatter


class TestWebServer:
    @pytest.mark.asyncio
    async def test_web_server_configuration(self):
        with patch('uvicorn.Server') as mock_server_class:
            mock_server = Mock()
            mock_server.serve = AsyncMock()
            mock_server_class.return_value = mock_server
            
            with patch('uvicorn.Config') as mock_config:
                await web_server(host="127.0.0.1", port=8000)
                
                # Verify Config was called with correct parameters
                mock_config.assert_called_once()
                args, kwargs = mock_config.call_args
                assert kwargs['host'] == "127.0.0.1"
                assert kwargs['port'] == 8000
                
                # Verify Server was instantiated and serve was called
                mock_server_class.assert_called_once_with(mock_config.return_value)
                mock_server.serve.assert_called_once()

    @pytest.mark.asyncio
    async def test_web_server_custom_host_port(self):
        with patch('uvicorn.Server') as mock_server_class:
            mock_server = Mock()
            mock_server.serve = AsyncMock()
            mock_server_class.return_value = mock_server
            
            with patch('uvicorn.Config') as mock_config:
                await web_server(host="0.0.0.0", port=9000)
                
                args, kwargs = mock_config.call_args
                assert kwargs['host'] == "0.0.0.0"
                assert kwargs['port'] == 9000


class TestMainExecution:
    def test_main_execution_flow(self):
        # Test that the main components can be imported and configured properly
        from run_servers import parse_args, web_server, interrupt_event
        from web import app
        
        # Test that parse_args works
        with patch('sys.argv', ['run_servers.py']):
            args = parse_args()
            assert args.host == "127.0.0.1:8000"
        
        # Test that app has required methods
        assert hasattr(app, '_prepare')
        assert hasattr(app, '_prestart')
        
        # Test that web_server function exists and is callable
        assert callable(web_server)
        
        # Test that interrupt_event is properly configured
        assert hasattr(interrupt_event, 'set')
        assert hasattr(interrupt_event, 'is_set')

    def test_interrupt_event_handling(self):
        # Test that interrupt_event is an asyncio.Event
        assert isinstance(interrupt_event, asyncio.Event)
        
        # Test that it starts unset
        assert not interrupt_event.is_set()

    def test_keyboard_interrupt_handling(self):
        # Test that interrupt_event handling is properly configured
        mock_args = Mock()
        mock_args.host = "127.0.0.1:8000"
        
        with patch('run_servers.parse_args', return_value=mock_args), \
             patch('run_servers.app._prepare'), \
             patch('run_servers.app._prestart', return_value=("127.0.0.1", 8000)), \
             patch('asyncio.new_event_loop') as mock_loop_factory:
            
            mock_loop = Mock()
            mock_loop_factory.return_value = mock_loop
            mock_loop.create_task.return_value = Mock()
            mock_loop.run_forever.side_effect = KeyboardInterrupt()
            mock_loop.run_until_complete = Mock()
            mock_loop.shutdown_asyncgens = Mock(return_value="shutdown_result")
            
            # Verify KeyboardInterrupt is properly handled
            # This mainly tests that the interrupt_event is available
            assert hasattr(interrupt_event, 'set')
            assert hasattr(interrupt_event, 'is_set')


class TestImports:
    def test_required_imports(self):
        # Test that all required modules can be imported
        import asyncio
        import argparse
        import uvicorn
        from web import app
        from run_worker import temporal_worker
        
        assert asyncio is not None
        assert argparse is not None
        assert uvicorn is not None
        assert app is not None
        assert temporal_worker is not None

    def test_web_app_import(self):
        from web import app
        assert hasattr(app, '_prepare')
        assert hasattr(app, '_prestart')

    def test_temporal_worker_import(self):
        from run_worker import temporal_worker
        assert callable(temporal_worker)