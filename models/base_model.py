import pydantic


def to_camel_case(string: str):
    split = string.split("_")
    return split[0] + "".join(s.capitalize() for s in split[1:])


class BaseModel(pydantic.BaseModel):
    class Config:
        alias_generator = to_camel_case
        allow_population_by_field_name = True
