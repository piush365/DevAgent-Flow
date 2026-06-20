"""
DevFlow Agent — BaseAgent Abstract Class
All agents inherit from this class, which provides a shared LLMClient
instance and enforces the generator-based streaming contract.
"""

import logging
from abc import ABC, abstractmethod
from typing import Generator

from app.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base for all DevFlow agents.

    Subclasses must implement:
        run(*args, **kwargs)   — public entrypoint, yields text chunks
        _build_prompt(...)     — constructs the LLM prompt string
        _system_prompt()       — returns the system role instruction

    The shared ``self.llm`` instance handles provider fallback automatically.
    """

    def __init__(self) -> None:
        self.llm = LLMClient()

    @abstractmethod
    def run(self, *args, **kwargs) -> Generator[str, None, None]:
        """
        Execute the agent and yield streamed text chunks.
        Every chunk yielded here is sent directly to the HTTP response.
        """
        raise NotImplementedError

    @abstractmethod
    def _build_prompt(self, *args, **kwargs) -> str:
        """Construct the user-facing LLM prompt from structured inputs."""
        raise NotImplementedError

    @abstractmethod
    def _system_prompt(self) -> str:
        """Return the system instruction for the LLM."""
        raise NotImplementedError

    def _stream_llm(self, prompt: str) -> Generator[str, None, None]:
        """
        Stream from the LLM with uniform error handling.
        Wraps self.llm.stream() so subclasses don't repeat try/except.
        """
        try:
            yield from self.llm.stream(prompt, system=self._system_prompt())
        except Exception as exc:
            logger.exception("%s encountered an LLM error", self.__class__.__name__)
            yield f"\n⚠️ LLM error: {exc}"
