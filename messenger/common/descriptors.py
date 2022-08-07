class Port:
    def __set__(self, instance, value):
        try:
            value = int(value)
            if not 1023 < value < 65535:
                raise ValueError
        except ValueError:
            raise TypeError('Неверно указан порт, допустимый диапазон от 1024 до 65535!')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
