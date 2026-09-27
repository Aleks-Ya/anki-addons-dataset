from dataclasses import dataclass


@dataclass(frozen=True)
class AiCacheStats:
    hit_count: int = 0
    miss_count: int = 0

    def __add__(self, other: "AiCacheStats") -> "AiCacheStats":
        return AiCacheStats(self.hit_count + other.hit_count, self.miss_count + other.miss_count)
