from magicgui import magicgui

from entry_1 import widget_entry1
from entry_2 import widget_entry2


@magicgui(
    auto_call=True,
    layout="vertical",
    title={"widget_type": "Label", "label": "Seg2Link:"},
    round1={"widget_type": "PushButton", "label": "The first round"},
    round2={"widget_type": "PushButton", "label": "The second round"},
)
def widget_entry(title="Please select a round",round1=True, round2=True):
    return None


@widget_entry.round1.changed.connect
def r1_changed():
    widget_entry1.show(run=True)


@widget_entry.round2.changed.connect
def r2_changed():
    widget_entry2.show(run=True)


if __name__ == "__main__":
    widget_entry.show(run=True)

