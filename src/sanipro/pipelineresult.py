from dataclasses import dataclass

from sanipro.abc import IPipelineResult, MutablePrompt
from sanipro.diff import PromptDifferenceDetector


@dataclass(frozen=True)
class PipelineResult(IPipelineResult):
    input: MutablePrompt
    output: MutablePrompt

    def get_summary(self) -> list[str]:
        return PromptDifferenceDetector(self.input, self.input).get_summary()
