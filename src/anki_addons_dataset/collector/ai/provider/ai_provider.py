import logging
from abc import ABC, abstractmethod
from logging import Logger
from typing import NewType, Optional

from anki_addons_dataset.common.data_types import AiModel

log: Logger = logging.getLogger(__name__)

AiPrompt = NewType("AiPrompt", str)
AiResponseText = NewType("AiResponseText", str)
AiInstructions = NewType("AiInstructions", str)


class AiProvider(ABC):
    def __init__(self, model: AiModel):
        self.__model: AiModel = model

    @abstractmethod
    def response(self, prompt: AiPrompt, instructions: Optional[AiInstructions] = None) -> Optional[AiResponseText]:
        ...

    @abstractmethod
    def verify_access(self) -> Optional[str]:
        ...

    def get_model(self) -> AiModel:
        return self.__model
