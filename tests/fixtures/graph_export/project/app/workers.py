"""Two same-named methods — forces an AMBIGUOUS CALLS resolution."""


class Builder:
    def run(self) -> None:
        pass


class Packer:
    def run(self) -> None:
        pass


def kickoff(obj) -> None:
    obj.run()  # bare `.run` -> ambiguous (Builder.run / Packer.run)
