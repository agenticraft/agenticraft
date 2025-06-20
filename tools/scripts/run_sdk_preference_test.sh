#!/bin/bash
cd /Users/zahere/Desktop/TLV/agenticraft
echo "Running the specific SDK preference parsing test..."
pytest -xvs tests/fabric/test_sdk_integration.py::TestSDKIntegration::test_sdk_preference_parsing
