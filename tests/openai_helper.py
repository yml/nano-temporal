from temporalio.contrib.openai_agents import TestModel
from agents import ModelResponse, Usage
from agents.items import TResponseOutputItem
from openai.types.responses import (
    ResponseOutputMessage,
    ResponseOutputText,
    ResponseFunctionToolCall,
)


class StaticFakeModel(TestModel):
    __test__ = False
    responses: list[ModelResponse] = []

    def __init__(
        self,
    ) -> None:
        self._responses = iter(self.responses)
        super().__init__(lambda: next(self._responses))


class ResponseBuilders:
    @staticmethod
    def model_response(output: TResponseOutputItem) -> ModelResponse:
        return ModelResponse(
            output=[output],
            usage=Usage(),
            response_id=None,
        )

    @staticmethod
    def response_output_message(text: str) -> ResponseOutputMessage:
        return ResponseOutputMessage(
            id="",
            content=[
                ResponseOutputText(
                    text=text,
                    annotations=[],
                    type="output_text",
                )
            ],
            role="assistant",
            status="completed",
            type="message",
        )

    @staticmethod
    def tool_call(arguments: str, name: str) -> ModelResponse:
        return ResponseBuilders.model_response(
            ResponseFunctionToolCall(
                arguments=arguments,
                call_id="call",
                name=name,
                type="function_call",
                id="id",
                status="completed",
            )
        )

    @staticmethod
    def output_message(text: str) -> ModelResponse:
        return ResponseBuilders.model_response(
            ResponseBuilders.response_output_message(text)
        )
