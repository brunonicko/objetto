# -*- coding: utf-8 -*-
import pytest

from objetto.utils.subject_observer import Observer, ObserverToken, Subject


def test_send_payload():
    class MyObserver(Observer):
        def __init__(self):
            self.payload = ()

        def __observe__(self, *_payload):
            self.payload = payload

    subject = Subject()

    observer_a = MyObserver()
    observer_a.start_observing(subject)

    observer_b = MyObserver()
    observer_b.start_observing(subject)

    payload = 1, 2, 3
    errors = subject.send(*payload)

    assert not errors
    assert observer_a.payload == payload
    assert observer_b.payload == payload

    observer_a.stop_observing(subject)
    observer_b.stop_observing(subject)

    other_payload = 4, 5, 6
    errors = subject.send(*other_payload)

    assert not errors
    assert observer_a.payload == payload
    assert observer_b.payload == payload


def test_tokens():
    class MyObserver(Observer):
        def __init__(self, index):
            self.payload = ()
            self.index = index

        def __observe__(self, *_payload):
            called.append(self.index)
            if self.index < 99:
                wait_for = self.index + 1
                tokens[wait_for].wait()
            observed.append(self.index)

    subject = Subject()

    observers = []
    tokens = []
    for i in range(100):
        observer = MyObserver(i)
        tokens.append(observer.start_observing(subject))
        observers.append(observer)

    called = []
    observed = []
    payload = 1, 2, 3
    errors = subject.send(payload)

    assert sorted(called) == list(range(100))
    assert len(called) == 100
    assert not errors
    assert observed == list(reversed(range(100)))


def test_token_cycle_errors():
    class MyObserver(Observer):
        def __init__(self, index):
            self.payload = ()
            self.index = index

        def __observe__(self, *_payload):
            called.append(self.index)
            tokens[99 - self.index].wait()
            observed.append(self.index)

    subject = Subject()

    observers = []
    tokens = []
    for i in range(100):
        observer = MyObserver(i)
        tokens.append(observer.start_observing(subject))
        observers.append(observer)

    called = []
    observed = []
    payload = 1, 2, 3
    errors = subject.send(payload)

    assert sorted(called) == list(range(100))
    assert len(called) == 100
    assert len(errors) == 100
    assert not observed


def test_prevent_token_instantiation():
    with pytest.raises(RuntimeError):
        subject, observer = Subject(), Observer()
        ObserverToken(subject, observer)


if __name__ == "__main__":
    pytest.main()
