#!/bin/bash
cd /Users/zahere/Desktop/TLV/agenticraft
pytest -xvs tests/fabric/test_sdk_integration.py::TestSDKIntegration::test_sdk_preference_parsing
