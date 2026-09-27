import logging
from abc import ABC, abstractmethod
from logging import Logger
from typing import NewType, Optional

from anki_addons_dataset.common.data_types import AiModel

log: Logger = logging.getLogger(__name__)

AiPrompt = NewType("AiPrompt", str)
AiResponseText = NewType("AiResponseText", str)


class AiProvider(ABC):
    def __init__(self, model: AiModel):
        self.__model: AiModel = model

    @abstractmethod
    def response(self, prompt: AiPrompt) -> Optional[AiResponseText]:
        ...

    def get_model(self) -> AiModel:
        return self.__model


class AiFailure(Exception):
    def __init__(self, message: str, retryable: bool):
        super().__init__(message)
        self.retryable: bool = retryable
