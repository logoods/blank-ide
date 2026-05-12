from pydantic import BaseModel
from typing import Any, Optional
import time


class Field(BaseModel):
    """
    世界状态的原子单元 / Atomic unit of world state.
    每个 Field 代表一条有版本、有时间戳的键值记录。
    Each Field represents a versioned, timestamped key-value record.
    """

    name: str                        # 字段名 / Field name
    value: Any                       # 字段值 / Field value
    type: str = "generic"           # 类型标签 / Type label
    version: int = 1                 # 版本号 / Version number
    timestamp: float = time.time()  # 写入时间戳 / Write timestamp
