"""Two same-named methods — exercises both AMBIGUOUS and UNRESOLVED resolution.

``kickoff`` calls a BARE ``run()``: last-segment matches both ``Builder.run``
and ``Packer.run`` (step-2 full-suffix) → genuine AMBIGUOUS.

``dispatch`` calls a DOTTED ``obj.run()``: the receiver ``obj`` is a runtime
parameter whose type is statically unknowable, so this is dynamic dispatch →
UNRESOLVED, not ambiguous (GH #127).
"""


class Builder:
    def run(self) -> None:
        pass


class Packer:
    def run(self) -> None:
        pass


def kickoff() -> None:
    run()  # noqa: F821 — parser fixture: bare callee exercising cross-file AMBIGUOUS resolution (Builder.run / Packer.run)


def dispatch(obj) -> None:
    obj.run()  # dotted callee -> UNRESOLVED (GH #127)
