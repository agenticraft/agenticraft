#!/bin/bash
cd /Users/zahere/Desktop/TLV/agenticraft
pytest -xvs tests/fabric/test_decorators.py::TestToolProxy::test_tool_access_by_name
