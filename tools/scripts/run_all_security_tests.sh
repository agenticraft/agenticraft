#!/bin/bash
cd /Users/zahere/Desktop/TLV/agenticraft
echo "Running all security sandbox tests..."
echo "======================================"
pytest -xvs tests/security/test_sandbox.py
