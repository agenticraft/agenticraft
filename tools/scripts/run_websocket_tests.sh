#!/bin/bash
cd /Users/zahere/Desktop/TLV/agenticraft
pytest -xvs tests/examples/test_websocket_transport.py::test_performance
