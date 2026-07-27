from typing import Protocol

from app.models import Interpretacao


class NLUService(Protocol):
    """A tomada entre o texto do usuario e a intencao estruturada.

    Hoje o RuleBasedNLU esta plugado. Quando o modelo treinado existir,
    troca-se a implementacao por uma que respeite o mesmo parse() -> nada
    alem disso deve mudar em quem consome NLUService.
    """

    def parse(self, texto: str) -> Interpretacao: ...
