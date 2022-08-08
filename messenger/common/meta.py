import dis


def get_cls_methods(cls_dict, bases=None):
    if bases:
        cls_methods, global_methods, attributes = get_cls_methods(bases[0].__dict__, bases[1:])
    else:
        cls_methods = set()
        global_methods = set()
        attributes = set()
    for key in cls_dict:
        try:
            instructions = dis.get_instructions(cls_dict[key])
        except TypeError:
            pass
        else:
            cls_methods.add(key)
            for instr in instructions:
                # print(f'{key} + {instr}')
                if instr.opname == 'LOAD_GLOBAL':
                    global_methods.add(instr.argval)
                if instr.opname == 'LOAD_ATTR':
                    attributes.add(instr.argval)
    return cls_methods, global_methods, attributes


class ClientVerifier(type):
    def __init__(cls, cls_name, bases, cls_dict):
        cls_methods, methods, attributes = get_cls_methods(cls_dict, list(bases))
        for func in ('accept', 'listen'):
            if func in methods:
                raise TypeError(f'Недопустимый метод {func}')
        for func in ('get_message', 'send_message'):
            if func not in cls_methods:
                raise TypeError(f'Отсутствует обязательный метод {func}')
        super().__init__(cls_name, bases, cls_dict)


class ServerVerifier(type):
    def __init__(cls, cls_name, bases, cls_dict):
        cls_methods, methods, attributes = get_cls_methods(cls_dict, bases)
        for func in ('SOCK_STREAM', 'AF_INET'):
            if func not in attributes:
                raise TypeError(f'Отсутствует параметр сокета {func}')
        for func in ('get_message', 'send_message'):
            if func not in cls_methods:
                raise TypeError(f'Отсутствует обязательный метод {func}')
        super().__init__(cls_name, bases, cls_dict)
