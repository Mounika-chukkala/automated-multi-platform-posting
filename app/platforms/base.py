
from abc import ABC, abstractmethod


class BasePlatform(ABC):
    """
    Common interface that every platform integration must implement.
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the platform's name."""
        pass

    @abstractmethod
    async def publish(self, message: str) -> dict:
        """
        Publish a message to the platform.

        Args:
            message: The content to publish.

        Returns:
            A dictionary containing the publishing result.
        """
        pass
