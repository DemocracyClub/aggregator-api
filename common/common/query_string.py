from dataclasses import fields, replace

TRUTHY_VALUES = {"1", "true"}


def clean_query_params(request, config_cls):
    cfg = config_cls()

    if "query_string" not in request.scope:
        return cfg

    updates = {}

    for f in fields(cfg):
        if f.type is bool:
            raw = request.query_params.get(f.name, "")
            updates[f.name] = raw.lower() in TRUTHY_VALUES
        else:
            # TODO: implement other types if we need them
            raise NotImplementedError()

    return replace(cfg, **updates)
