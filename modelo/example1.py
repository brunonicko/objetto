from modelo import ObjectModel, attribute, default_attribute, sequence_attribute


class Layer(ObjectModel):
    name = attribute(str, default="master")


class Template(ObjectModel):
    layers = sequence_attribute(Layer)


class Application(ObjectModel):
    template = default_attribute(default_factory=Template)
