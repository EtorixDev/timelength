from dataclasses import dataclass, field


@dataclass
class ParsedTimeLength:
    success: bool = False
    seconds: float = 0
    invalid: list = field(default_factory=list)
    valid: list = field(default_factory=list)

@dataclass
class Scale:
    scale: float = 0
    singular: str = ""
    plural: str = ""
    terms: list = field(default_factory=list)

    def __str__(self):
        return f"Scale(scale={self.scale}, singular={self.singular}, plural={self.plural})"

    def __repr__(self):
        return f"Scale(scale={self.scale}, singular={self.singular}, plural={self.plural})"