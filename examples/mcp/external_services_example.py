#!/usr/bin/env python3
"""MCP integration with external services example.

This example demonstrates how to expose external services
(APIs, databases, etc.) through MCP protocol.
"""

import asyncio
from datetime import datetime
from typing import Any

from agenticraft import Agent
from agenticraft.protocols.mcp import MCPClient, MCPServer, mcp_tool

# Mock external services (in real app, these would be actual API calls)


class WeatherService:
    """Mock weather service."""

    @staticmethod
    async def get_weather(city: str) -> dict[str, Any]:
        """Get weather for a city."""
        # Simulate API delay
        await asyncio.sleep(0.2)

        # Mock data
        weather_data = {
            "New York": {"temp": 72, "condition": "Partly Cloudy", "humidity": 65},
            "London": {"temp": 59, "condition": "Rainy", "humidity": 80},
            "Tokyo": {"temp": 77, "condition": "Clear", "humidity": 70},
            "Sydney": {"temp": 68, "condition": "Sunny", "humidity": 55},
        }

        default = {"temp": 70, "condition": "Unknown", "humidity": 50}
        return weather_data.get(city, default)


class DatabaseService:
    """Mock database service."""

    def __init__(self):
        self.users = [
            {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin"},
            {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user"},
            {
                "id": 3,
                "name": "Charlie",
                "email": "charlie@example.com",
                "role": "user",
            },
        ]
        self.tasks = [
            {"id": 1, "user_id": 1, "title": "Review PR", "status": "pending"},
            {"id": 2, "user_id": 2, "title": "Write docs", "status": "completed"},
            {"id": 3, "user_id": 1, "title": "Fix bug", "status": "in_progress"},
        ]

    async def query_users(
        self, filter_by: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Query users with optional filters."""
        await asyncio.sleep(0.1)  # Simulate DB delay

        if not filter_by:
            return self.users

        results = []
        for user in self.users:
            match = all(user.get(k) == v for k, v in filter_by.items())
            if match:
                results.append(user)
        return results

    async def query_tasks(
        self, user_id: int | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        """Query tasks with filters."""
        await asyncio.sleep(0.1)

        results = []
        for task in self.tasks:
            if user_id and task["user_id"] != user_id:
                continue
            if status and task["status"] != status:
                continue
            results.append(task)
        return results


class EmailService:
    """Mock email service."""

    @staticmethod
    async def send_email(
        to: str, subject: str, body: str, cc: list[str] | None = None
    ) -> dict[str, Any]:
        """Send an email."""
        await asyncio.sleep(0.3)  # Simulate sending delay

        return {
            "message_id": f"msg_{datetime.now().timestamp()}",
            "status": "sent",
            "timestamp": datetime.now().isoformat(),
            "recipients": {"to": [to], "cc": cc or []},
        }


# Create service instances
weather_service = WeatherService()
db_service = DatabaseService()
email_service = EmailService()


# Define MCP tools that wrap external services


@mcp_tool(
    returns={
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "temperature": {"type": "number"},
            "condition": {"type": "string"},
            "humidity": {"type": "number"},
            "unit": {"type": "string"},
        },
    },
    examples=[
        {
            "input": {"city": "New York"},
            "output": {
                "city": "New York",
                "temperature": 72,
                "condition": "Partly Cloudy",
                "humidity": 65,
                "unit": "fahrenheit",
            },
        }
    ],
)
async def get_weather(city: str) -> dict[str, Any]:
    """Get current weather for a city.

    Args:
        city: City name

    Returns:
        Weather information
    """
    data = await weather_service.get_weather(city)
    return {
        "city": city,
        "temperature": data["temp"],
        "condition": data["condition"],
        "humidity": data["humidity"],
        "unit": "fahrenheit",
    }


@mcp_tool(
    returns={
        "type": "object",
        "properties": {
            "users": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "role": {"type": "string"},
                    },
                },
            },
            "count": {"type": "integer"},
        },
    }
)
async def query_users(
    role: str | None = None, name: str | None = None
) -> dict[str, Any]:
    """Query users from database.

    Args:
        role: Filter by role (optional)
        name: Filter by name (optional)

    Returns:
        List of users and count
    """
    filters = {}
    if role:
        filters["role"] = role
    if name:
        filters["name"] = name

    users = await db_service.query_users(filters)
    return {"users": users, "count": len(users)}


@mcp_tool(
    returns={
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "user_id": {"type": "integer"},
                        "title": {"type": "string"},
                        "status": {"type": "string"},
                    },
                },
            },
            "count": {"type": "integer"},
            "breakdown": {
                "type": "object",
                "properties": {
                    "pending": {"type": "integer"},
                    "in_progress": {"type": "integer"},
                    "completed": {"type": "integer"},
                },
            },
        },
    }
)
async def get_user_tasks(
    user_id: int, include_completed: bool = True
) -> dict[str, Any]:
    """Get tasks for a specific user.

    Args:
        user_id: User ID
        include_completed: Include completed tasks

    Returns:
        User's tasks with statistics
    """
    # Get all tasks for user
    all_tasks = await db_service.query_tasks(user_id=user_id)

    # Filter if needed
    if not include_completed:
        tasks = [t for t in all_tasks if t["status"] != "completed"]
    else:
        tasks = all_tasks

    # Calculate breakdown
    breakdown = {
        "pending": sum(1 for t in all_tasks if t["status"] == "pending"),
        "in_progress": sum(1 for t in all_tasks if t["status"] == "in_progress"),
        "completed": sum(1 for t in all_tasks if t["status"] == "completed"),
    }

    return {"tasks": tasks, "count": len(tasks), "breakdown": breakdown}


@mcp_tool(
    returns={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message_id": {"type": "string"},
            "details": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "timestamp": {"type": "string"},
                },
            },
        },
    }
)
async def send_task_reminder(user_id: int, task_id: int) -> dict[str, Any]:
    """Send email reminder about a task.

    Args:
        user_id: User ID
        task_id: Task ID

    Returns:
        Email sending result
    """
    # Get user info
    users = await db_service.query_users({"id": user_id})
    if not users:
        return {"success": False, "error": "User not found"}

    user = users[0]

    # Get task info
    tasks = await db_service.query_tasks()
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        return {"success": False, "error": "Task not found"}

    # Compose and send email
    subject = f"Reminder: {task['title']}"
    body = f"""
Hi {user['name']},

This is a reminder about your task:
- Title: {task['title']}
- Status: {task['status']}
- ID: {task['id']}

Please complete this task as soon as possible.

Best regards,
Task Management System
"""

    result = await email_service.send_email(
        to=user["email"], subject=subject, body=body
    )

    return {
        "success": True,
        "message_id": result["message_id"],
        "details": {
            "to": user["email"],
            "subject": subject,
            "timestamp": result["timestamp"],
        },
    }


@mcp_tool
async def get_system_status() -> dict[str, Any]:
    """Get status of all integrated services.

    Returns:
        Status of each service
    """
    statuses = {}

    # Check weather service
    try:
        await weather_service.get_weather("Test")
        statuses["weather_api"] = "operational"
    except:
        statuses["weather_api"] = "error"

    # Check database
    try:
        await db_service.query_users()
        statuses["database"] = "operational"
    except:
        statuses["database"] = "error"

    # Check email (don't actually send)
    statuses["email_service"] = "operational"  # Mock

    return {
        "timestamp": datetime.now().isoformat(),
        "services": statuses,
        "overall": (
            "operational"
            if all(s == "operational" for s in statuses.values())
            else "degraded"
        ),
    }


async def demonstrate_external_services():
    """Demonstrate MCP with external services."""
    print("\n🌐 MCP External Services Integration Demo")
    print("=" * 60)

    # Create and start server
    server = MCPServer(
        name="External Services Gateway",
        version="1.0.0",
        description="MCP gateway to external services and APIs",
    )

    # Register all service tools
    tools = [
        get_weather,
        query_users,
        get_user_tasks,
        send_task_reminder,
        get_system_status,
    ]
    server.register_tools(tools)

    print(f"📦 Registered {len(tools)} service tools")

    # Start server
    server_task = asyncio.create_task(server.start_websocket_server("localhost", 3005))
    await asyncio.sleep(0.5)

    try:
        # Connect with client
        async with MCPClient("ws://localhost:3005") as client:
            print(f"✅ Connected to {client.server_info.name}")

            # Create an agent
            agent = Agent(
                name="ServiceCoordinator",
                instructions="""You are a service coordinator with access to:
                - Weather API (get_weather)
                - User database (query_users)
                - Task management (get_user_tasks)
                - Email service (send_task_reminder)
                - System monitoring (get_system_status)
                
                Help users by coordinating these services effectively.""",
                tools=client.get_tools(),
                model="gpt-4o-mini",
            )

            # Example scenarios
            scenarios = [
                {
                    "name": "Weather Check",
                    "query": "What's the weather in New York and London?",
                },
                {
                    "name": "User Management",
                    "query": "Show me all admin users and their current tasks",
                },
                {
                    "name": "Task Reminder",
                    "query": "Send a reminder to user ID 1 about task ID 3",
                },
                {
                    "name": "System Health",
                    "query": "Check if all services are operational",
                },
            ]

            for scenario in scenarios:
                print(f"\n📋 Scenario: {scenario['name']}")
                print(f"👤 User: {scenario['query']}")

                response = await agent.arun(scenario["query"])
                print(f"🤖 Agent: {response.content}")

                if response.tool_calls:
                    print("   🔧 Services used:")
                    for call in response.tool_calls:
                        print(f"      - {call.function.name}")

            # Direct service composition example
            print("\n🔗 Direct Service Composition Example:")
            print(
                "   Finding users with pending tasks and checking weather for demo..."
            )

            # Get users
            users_result = await client.call_tool("query_users", {})
            print(f"   Found {users_result['count']} users")

            # Check tasks for each user
            users_with_pending = []
            for user in users_result["users"]:
                tasks_result = await client.call_tool(
                    "get_user_tasks",
                    {"user_id": user["id"], "include_completed": False},
                )
                if tasks_result["breakdown"]["pending"] > 0:
                    users_with_pending.append(
                        {
                            "user": user,
                            "pending_tasks": tasks_result["breakdown"]["pending"],
                        }
                    )

            print(f"   Users with pending tasks: {len(users_with_pending)}")
            for item in users_with_pending:
                print(
                    f"      - {item['user']['name']}: {item['pending_tasks']} pending"
                )

            # Get weather for demo
            weather = await client.call_tool("get_weather", {"city": "New York"})
            print(
                f"   Weather in NYC: {weather['temperature']}°F, {weather['condition']}"
            )

    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    print("\n✅ External services demo complete!")


async def main():
    """Run the external services integration demo."""
    try:
        await demonstrate_external_services()
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
