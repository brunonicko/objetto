

from pytest import main

from objetto.utils.namespace import _WRAPPED, Namespace


def test_namespace():
    wrapped = {"update": "foo"}
    ns = Namespace(wrapped)
    assert hasattr(ns, _WRAPPED)
    assert getattr(ns, _WRAPPED) is wrapped
    assert dict(ns) == {"update": "foo"}

    assert hasattr(ns, "update")
    assert ns.update == "foo"

    ns.update = "bar"
    assert hasattr(ns, "update")
    assert ns.update == "bar"

    del ns.update
    assert not hasattr(ns, "update")

    ns["update"] = "foo"
    assert hasattr(ns, "update")
    assert ns.update == "foo"

    ns["update"] = "bar"
    assert hasattr(ns, "update")
    assert ns.update == "bar"

    del ns["update"]
    assert not hasattr(ns, "update")


if __name__ == "__main__":
    main()
