from .meta import MetaMessage


class MidiTrack(list):
    @property
    def name(self):
        for message in self:
            if message.type == 'track_name':
                return message.name
        else:
            return ''

    @name.setter
    def name(self, name):
        # Find the first track_name message and modify it.
        for message in self:
            if message.type == 'track_name':
                message.name = name
                return
        else:
            # No track name found, add one.
            self.insert(0, MetaMessage('track_name', name=name, time=0))

    def copy(self):
        return self.__class__(self)

    def __getitem__(self, index_or_slice):
        # Retrieve item from the MidiTrack
        lst = list.__getitem__(self, index_or_slice)
        if isinstance(index_or_slice, int):
            # If an index was provided, return the list element
            return lst
        else:
            # Otherwise, construct a MidiTrack to return.
            # TODO: this make a copy of the list. Is there a better way?
            return self.__class__(lst)

    def __add__(self, other):
        return self.__class__(list.__add__(self, other))

    def __mul__(self, other):
        return self.__class__(list.__mul__(self, other))

    def __repr__(self):
        return '<midi track {!r} {} messages>'.format(self.name, len(self))


def _to_abstime(messages):
    """Convert messages to absolute time."""
    now = 0
    for msg in messages:
        now += msg.time
        yield msg.copy(time=now)


def _to_reltime(messages):
    """Convert messages to relative time."""
    now = 0
    for msg in messages:
        delta = msg.time - now
        yield msg.copy(time=delta)
        now = msg.time


def fix_end_of_track(messages):
    # Accumulated delta time from removed end of track messages.
    # This is added to the next message.
    accum = 0

    for msg in messages:
        if msg.type == 'end_of_track':
            accum += msg.time
        else:
            if accum:
                delta = accum + msg.time
                yield msg.copy(time=delta)
                accum = 0
            else:
                yield msg

    yield MetaMessage('end_of_track', time=accum)


def merge_tracks(tracks):
    messages = []
    for track in tracks:
        messages.extend(_to_abstime(track))

    messages.sort(key=lambda msg: msg.time)

    return MidiTrack(fix_end_of_track(_to_reltime(messages)))
