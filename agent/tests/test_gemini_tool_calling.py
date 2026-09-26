import asyncio
from types import SimpleNamespace
from typing import ClassVar

from agent.ai.gemini_config import GeminiLiveConfig
from agent.ai.live_session import GeminiLiveService, MAX_TOOL_CALLS_PER_USER_TURN
from agent.tests.test_gemini_live import (
    FakeClient,
    FakeLiveConnection,
    FakeLiveSession,
    turn_complete_response,
    wait_until,
)
from agent.tools.base import DesktopTool, ToolArguments
from agent.tools.registry import ToolRegistry
from agent.tools.result import ToolResult


class CallArguments(ToolArguments):
    value: str


class RecordingTool(DesktopTool):
    name = "record_action"
    description = "Record an action for tests."
    arguments_type = CallArguments
    parameters: ClassVar[dict[str, object]] = {
        "type": "object",
        "properties": {"value": {"type": "string"}},
        "required": ["value"],
    }

    def __init__(self, succeed: bool = True) -> None:
        self.succeed = succeed
        self.values: list[str] = []

    def execution_label(self, arguments: ToolArguments) -> str:
        return "Performing safe action..."

    def execute(self, arguments: ToolArguments) -> ToolResult:
        assert isinstance(arguments, CallArguments)
        self.values.append(arguments.value)
        if self.succeed:
            return ToolResult.ok("Safe action completed.", recorded=arguments.value)
        return ToolResult.fail("TEST_FAILURE", "Safe action failed.")


def tool_call_response(call_id: str, value: str = "one") -> SimpleNamespace:
    return SimpleNamespace(
        tool_call=SimpleNamespace(
            function_calls=[SimpleNamespace(id=call_id, name="record_action", args={"value": value})]
        ),
        server_content=None,
        data=None,
    )


def test_function_call_routes_through_registry_preserves_id_and_keeps_session_open() -> None:
    events: list[dict[str, object]] = []

    async def run() -> None:
        async def emit(event: dict[str, object]) -> None:
            events.append(event)

        tool = RecordingTool()
        registry = ToolRegistry((tool,))
        session = FakeLiveSession()
        connection = FakeLiveConnection(session)
        client = FakeClient(connection)
        service = GeminiLiveService(
            GeminiLiveConfig(api_key="test"),
            emit,
            client_factory=lambda _: client,
            tool_registry=registry,
        )
        assert await service.start()
        config = client.aio.live.last_connect_options["config"]
        assert config.tools[0].function_declarations[0].name == "record_action"

        await session.responses.put([tool_call_response("call-one")])
        await wait_until(lambda: len(session.tool_responses) == 1)
        first = session.tool_responses[0][0]
        assert first.id == "call-one"
        assert first.response == {
            "success": True,
            "message": "Safe action completed.",
            "recorded": "one",
        }
        assert [event["type"] for event in events if str(event["type"]).startswith("tool.")] == [
            "tool.started",
            "tool.completed",
        ]

        await session.responses.put([turn_complete_response()])
        await session.responses.put([tool_call_response("call-two", "two")])
        await wait_until(lambda: len(session.tool_responses) == 2)
        assert session.tool_responses[1][0].id == "call-two"
        assert tool.values == ["one", "two"]
        assert client.aio.live.connect_calls == 1
        assert connection.exit_count == 0
        await service.close()

    asyncio.run(run())


def test_failed_result_returns_to_gemini_without_closing_session() -> None:
    events: list[dict[str, object]] = []

    async def run() -> None:
        async def emit(event: dict[str, object]) -> None:
            events.append(event)

        session = FakeLiveSession()
        connection = FakeLiveConnection(session)
        client = FakeClient(connection)
        service = GeminiLiveService(
            GeminiLiveConfig(api_key="test"),
            emit,
            client_factory=lambda _: client,
            tool_registry=ToolRegistry((RecordingTool(succeed=False),)),
        )
        assert await service.start()
        await session.responses.put([tool_call_response("failed-call")])
        await wait_until(lambda: len(session.tool_responses) == 1)
        response = session.tool_responses[0][0]
        assert response.id == "failed-call"
        assert response.response["success"] is False
        assert response.response["error"] == "TEST_FAILURE"
        assert any(event["type"] == "tool.failed" for event in events)
        assert connection.exit_count == 0
        await service.close()

    asyncio.run(run())


def test_tool_call_limit_blocks_excess_calls() -> None:
    async def run() -> None:
        async def emit(_: dict[str, object]) -> None:
            pass

        tool = RecordingTool()
        session = FakeLiveSession()
        connection = FakeLiveConnection(session)
        service = GeminiLiveService(
            GeminiLiveConfig(api_key="test"),
            emit,
            client_factory=lambda _: FakeClient(connection),
            tool_registry=ToolRegistry((tool,)),
        )
        assert await service.start()
        calls = [
            SimpleNamespace(id=f"call-{index}", name="record_action", args={"value": str(index)})
            for index in range(MAX_TOOL_CALLS_PER_USER_TURN + 1)
        ]
        await session.responses.put(
            [SimpleNamespace(tool_call=SimpleNamespace(function_calls=calls), server_content=None, data=None)]
        )
        await wait_until(lambda: len(session.tool_responses) == 1)
        responses = session.tool_responses[0]
        assert len(tool.values) == MAX_TOOL_CALLS_PER_USER_TURN
        assert responses[-1].id == f"call-{MAX_TOOL_CALLS_PER_USER_TURN}"
        assert responses[-1].response["error"] == "TOOL_LIMIT_EXCEEDED"
        await service.close()

    asyncio.run(run())
