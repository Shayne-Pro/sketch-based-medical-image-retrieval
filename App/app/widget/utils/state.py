import itertools
from collections import defaultdict


def is_unique(seq1, seq2):
    seq = seq1 + seq2
    return len(seq) == len(set(seq))


class StateBase(object):

    def __init__(self, **kwargs):
        self.__props = kwargs
        self.__callbacks_for_event = defaultdict(list)

    @property
    def props(self):
        return self.__props

    def connect(self, key, callback):
        if key in self.__props.keys():
            self.__callbacks_for_event[key].append(callback)
        else:
            raise KeyError

    def disconnect(self, key, callback=None):
        if callback is None:
            del self.__callbacks_for_event[key]
        else:
            self.__callbacks_for_event[key].remove(callback)

    def __getitem__(self, key):
        return self.__props[key]

    def __setitem__(self, key, value):
        if key in self.__props.keys():
            self.__props[key] = value
            if key in self.__callbacks_for_event.keys():
                callback = self.__callbacks_for_event[key]
                callback(self, key, value)
        else:
            raise KeyError

    def keys(self):
        return self.__props.keys()

    def update(self, **kwargs):
        for key in kwargs.keys():
            assert key in self.__props.keys()
        self.__props.update(kwargs)

    def __repr__(self):
        text = []
        for key in self.__props.keys():
            text.append('{}: {}'.format(key, str(self.__props[key])))
        return '\n'.join(text)


class StateBundler(object):

    def __init__(self):
        self.__states = set()
        self.__keys = []
        self.__i = 0

    def __len__(self):
        return len(self.__states)

    def __iter__(self):
        return self

    def __next__(self):
        if self.__i == len(self):
            raise StopIteration
        self.__i += 1
        return list(self.__states)[self.__i - 1]

    def add_state(self, state, *states):
        for state in itertools.chain((state,), states):
            assert is_unique(self.__keys, list(state.props.keys()))
            self.__states.add(state)
            self.__keys += list(state.props.keys())

    def discard_state(self, state):
        self.__states.discard(state)
        for key in state.props.keys():
            self.__keys.remove(key)

    def __getitem__(self, key):
        for state in self.__states:
            if key in state.props.keys():
                return state[key]

    def __setitem__(self, key, value):
        for state in self.__states:
            if key in state.props.keys():
                state[key] = value

    def update(self, **kwargs):
        for key in kwargs.keys():
            self[key] = kwargs[key]

    def __repr__(self):
        text = []
        for state in self.__states:
            for key in state.props.keys():
                text.append('{}: {}'.format(key, str(state.props[key])))
        return '\n'.join(text)

    def keys(self):
        return self.__keys
