import json;

def default_jsonable(obj):
    d = obj.__dict__;
    d["__class"] = type(obj).__name__;
    return d;

class Jsonable(object):
    @classmethod
    def from_json(cls, json_string):
        attributes = json.loads(json_string);
        if not isinstance(attributes, dict) or attributes.pop('__class') != cls.__name__:
            raise ValueError;
        return cls(**attributes);

    def to_json(self):
        return json.dumps(self, indent=4, default=default_jsonable);

class Person(Jsonable):
    def __init__(self, name, age):
        print("__init__!!");
        self.name = name
        self.age = age

    def GetName(self):
        return self.name;

    def SetName(self, new_name):
        self.name = new_name;

a = Person("John", 12);

a_string = a.to_json();

print(a_string);

b = Person.from_json(a_string);

print(b.GetName());

b.SetName("Billy");

print(b.GetName());
