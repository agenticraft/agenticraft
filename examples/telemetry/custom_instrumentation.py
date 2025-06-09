#!/usr/bin/env python3
"""Custom instrumentation example.

This example shows how to add custom telemetry to your own code.
"""

import asyncio
import random
import time
from typing import Any

from agenticraft import Agent
from agenticraft.telemetry import (
    LatencyTimer,
    create_span,
    get_meter,
    get_tracer,
    record_error,
    record_exception,
    set_span_attributes,
)
from agenticraft.telemetry.integration import TelemetryConfig


# Custom business logic with telemetry
class DocumentProcessor:
    """Example document processor with custom telemetry."""

    def __init__(self, agent: Agent):
        self.agent = agent
        self.tracer = get_tracer()
        self.meter = get_meter()

        # Create custom metrics
        self.doc_counter = self.meter.create_counter(
            "document_processor.documents_total",
            unit="documents",
            description="Total documents processed",
        )

        self.doc_size_histogram = self.meter.create_histogram(
            "document_processor.size_bytes",
            unit="bytes",
            description="Document size distribution",
        )

    async def process_document(self, doc_id: str, content: str) -> dict[str, Any]:
        """Process a document with full telemetry."""

        # Create a span for the entire operation
        with create_span("document.process", attributes={"doc_id": doc_id}) as span:
            try:
                # Record document size
                doc_size = len(content.encode("utf-8"))
                self.doc_size_histogram.record(doc_size, {"doc_type": "text"})

                # Step 1: Validate document
                with create_span("document.validate") as validate_span:
                    validation_result = await self._validate_document(content)
                    set_span_attributes(
                        {
                            "validation.passed": validation_result["valid"],
                            "validation.issues": len(
                                validation_result.get("issues", [])
                            ),
                        }
                    )

                if not validation_result["valid"]:
                    raise ValueError(
                        f"Document validation failed: {validation_result['issues']}"
                    )

                # Step 2: Extract information
                with LatencyTimer("document.extract"):
                    extraction_result = await self._extract_information(content)

                # Step 3: Analyze with agent
                with create_span("document.analyze") as analyze_span:
                    analysis = await self.agent.arun(
                        f"Analyze this document summary: {extraction_result['summary']}"
                    )

                    # Add custom attributes
                    span_attrs = {
                        "analysis.sentiment": self._detect_sentiment(analysis.content),
                        "analysis.word_count": len(analysis.content.split()),
                    }

                    # Get model name from agent config
                    if hasattr(self.agent, "config") and hasattr(
                        self.agent.config, "model"
                    ):
                        span_attrs["analysis.model"] = self.agent.config.model
                    else:
                        # Default to the model we know was used
                        span_attrs["analysis.model"] = "gpt-4o-mini"

                    set_span_attributes(span_attrs)

                # Record success metric
                self.doc_counter.add(1, {"status": "success", "doc_type": "text"})

                return {
                    "doc_id": doc_id,
                    "validation": validation_result,
                    "extraction": extraction_result,
                    "analysis": analysis.content,
                    "metrics": {
                        "size_bytes": doc_size,
                        "processing_time_ms": (
                            span.end_time - span.start_time if span.end_time else 0
                        ),
                    },
                }

            except Exception as e:
                # Record exception in span
                record_exception(e, escaped=True)

                # Record error metric
                self.doc_counter.add(
                    1, {"status": "error", "error_type": type(e).__name__}
                )

                record_error(type(e).__name__, "document.process")
                raise

    async def _validate_document(self, content: str) -> dict[str, Any]:
        """Validate document content."""
        await asyncio.sleep(0.1)  # Simulate work

        issues = []
        if len(content) < 10:
            issues.append("Document too short")
        if len(content) > 10000:
            issues.append("Document too long")

        return {"valid": len(issues) == 0, "issues": issues}

    async def _extract_information(self, content: str) -> dict[str, Any]:
        """Extract key information from document."""
        await asyncio.sleep(0.2)  # Simulate work

        # Simple extraction
        words = content.split()
        return {
            "summary": " ".join(words[:20]) + "...",
            "word_count": len(words),
            "entities": ["Entity1", "Entity2"],  # Simulated
        }

    def _detect_sentiment(self, text: str) -> str:
        """Simple sentiment detection."""
        positive_words = ["good", "great", "excellent", "positive", "beneficial"]
        negative_words = ["bad", "poor", "negative", "harmful", "problematic"]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"


# Custom span decorator
def trace_operation(operation_name: str):
    """Decorator to trace any function."""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            with create_span(operation_name) as span:
                # Add function arguments as attributes
                set_span_attributes(
                    {
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                    }
                )

                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("result.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("result.success", False)
                    record_exception(e, escaped=True)
                    raise

        def sync_wrapper(*args, **kwargs):
            with create_span(operation_name) as span:
                # Add function arguments as attributes
                set_span_attributes(
                    {
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                    }
                )

                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("result.success", True)
                    return result
                except Exception as e:
                    span.set_attribute("result.success", False)
                    record_exception(e, escaped=True)
                    raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# Example traced function
@trace_operation("business.calculate_risk")
def calculate_risk_score(value: float, category: str) -> float:
    """Calculate risk score with tracing."""

    # Add custom span inside
    with create_span("risk.calculation") as span:
        span.set_attribute("input.value", value)
        span.set_attribute("input.category", category)

        # Simulate calculation
        base_score = value * 0.1

        if category == "high":
            multiplier = 2.0
        elif category == "medium":
            multiplier = 1.5
        else:
            multiplier = 1.0

        risk_score = base_score * multiplier

        span.set_attribute("risk.score", risk_score)
        span.set_attribute("risk.multiplier", multiplier)

        # Record custom metric
        with LatencyTimer("risk.calculation", category=category):
            time.sleep(0.1)  # Simulate complex calculation

        return risk_score


async def main():
    """Run custom instrumentation example."""
    print("🔧 AgentiCraft Custom Instrumentation Example")
    print("=" * 50)

    # Initialize telemetry
    telemetry = TelemetryConfig(
        enabled=True,
        traces_enabled=True,
        metrics_enabled=True,
        exporter_type="console",
        service_name="custom_instrumentation",
        auto_instrument=True,
    )
    telemetry.initialize()

    print("\n✅ Telemetry initialized")

    # Create agent and processor
    agent = Agent(
        name="DocumentAgent",
        instructions="You analyze document content for insights.",
        model="gpt-4o-mini",
    )

    processor = DocumentProcessor(agent)

    print("\n📄 Processing documents with custom telemetry...\n")

    # Process multiple documents
    documents = [
        ("doc1", "This is a great example of excellent telemetry implementation."),
        ("doc2", "Short doc"),  # Will fail validation
        (
            "doc3",
            "The problematic aspects of poor monitoring lead to bad outcomes and negative results.",
        ),
        ("doc4", "Neutral document about observability and monitoring systems."),
    ]

    for doc_id, content in documents:
        print(f"\n📄 Processing {doc_id}...")
        try:
            result = await processor.process_document(doc_id, content)
            print(
                f"✅ Success: Sentiment={processor._detect_sentiment(result['analysis'])}"
            )
        except Exception as e:
            print(f"❌ Failed: {e}")

    # Use custom traced function
    print("\n💰 Calculating risk scores...")
    categories = ["low", "medium", "high"]
    for i in range(5):
        value = random.uniform(100, 1000)
        category = random.choice(categories)

        score = calculate_risk_score(value, category)
        print(f"  Risk score for ${value:.2f} ({category}): {score:.2f}")

    # Show manual span creation
    print("\n🔍 Manual span example...")
    tracer = get_tracer()

    with tracer.start_as_current_span("manual.operation") as span:
        span.set_attribute("custom.attribute", "custom_value")
        span.add_event("Processing started")

        # Simulate work
        await asyncio.sleep(0.5)

        span.add_event("Processing completed", {"items_processed": 42, "success": True})

    print("✅ Manual span created")

    # Summary
    print("\n" + "=" * 50)
    print("📊 Custom Instrumentation Summary")
    print("=" * 50)
    print("\n🔍 What we demonstrated:")
    print("1. Custom spans with meaningful names")
    print("2. Setting span attributes for context")
    print("3. Recording exceptions with telemetry")
    print("4. Creating custom metrics")
    print("5. Using the @trace_operation decorator")
    print("6. Manual span creation")
    print("7. Measuring latency with LatencyTimer")

    print("\n💡 Best Practices:")
    print("- Use descriptive span names (noun.verb)")
    print("- Add relevant attributes for debugging")
    print("- Record both successes and failures")
    print("- Create custom metrics for business KPIs")
    print("- Use consistent attribute naming")

    # Shutdown
    from agenticraft.telemetry.metrics import shutdown_metrics
    from agenticraft.telemetry.tracer import shutdown_tracer

    print("\n🔚 Shutting down telemetry...")
    shutdown_tracer()
    shutdown_metrics()

    print("✅ Custom instrumentation example complete!")


if __name__ == "__main__":
    asyncio.run(main())
