class Stack(object):
    """
        数据结构栈的实现
    """

    def __init__(self, contents):
        self.contents = contents

    # 压入栈
    def push(self, character):
        return Stack([character] + self.contents)

    # 出栈
    @property
    def pop(self):
        return Stack(self.contents[1:])

    # 栈顶元素
    @property
    def top(self):
        return self.contents[0]

    # 重写字符串方法
    def __str__(self):
        top = self.contents[0]
        other = ''.join(self.contents[1:])
        return '#<Stack ({top}){other}>'.format(**locals())

    __repr__ = __str__



class PDAConfiguration(object):
    """
        存储PDA的配置容器
    """
    STUCK_STATE = object()

    def __init__(self, state, stack):
        self.state = state
        self.stack = stack

    @property
    def stuck(self):
        return PDAConfiguration(self.__class__.STUCK_STATE, self.stack)

    @property
    def if_stuck(self):
        return self.state == self.__class__.STUCK_STATE

    def __str__(self):
        state = self.state
        stack = repr(self.stack)
        return '#<struct PDAConfiguration state={state}, stack={stack}>'.format(**locals())

    __repr__ = __str__


class PDARule(object):
    """
        表示PDA的规则
    """

    def __init__(self, state, character, next_state, pop_character, push_characters):
        self.state = state
        self.character = character
        self.next_state = next_state
        self.pop_character = pop_character
        self.push_characters = push_characters

    def applies_to(self, configuration, character):
        return self.state == configuration.state and \
               self.pop_character == configuration.stack.top and \
               self.character == character

    def follow(self, configuration):
        return PDAConfiguration(self.next_state, self.next_stack(configuration))

    def next_stack(self, configuration):
        popped_stack = configuration.stack.pop
        for item in self.push_characters[::-1]:
            popped_stack = popped_stack.push(item)
        return popped_stack

    def __str__(self):
        s = repr(self.state)
        char = repr(self.character)
        nexts = repr(self.next_state)
        pop_char = repr(self.pop_character)
        push_chars = repr(self.push_characters)

        return '#<struct PDARule\n\
        state={s},\n\
        character={char},\n\
        next_state={nexts},\n\
        pop_character={pop_char},\n\
        push_characters={push_chars}'.format(**locals())

    __repr__ = __str__


class NPDARulebook(object):
    """
        NPDA规则集合的容器
    """

    def __init__(self, rules):
        self.rules = rules

    def next_configurations(self, configurations, character):
        nexts = []
        for config in configurations:
            nexts += self.follow_rules_for(config, character)

        return set(nexts)

    def follow_rules_for(self, configuration, character):
        return [rule.follow(configuration) for rule in self.rules_for(configuration, character)]

    def rules_for(self, configuration, character):
        return [rule for rule in self.rules if rule.applies_to(configuration, character)]

    def follow_free_moves(self, configurations):
        more_configurations = self.next_configurations(configurations, None)

        # 必须将configuration转为字符串后，才能比较互相是否相同
        not_in_configs = []
        for more in more_configurations:
            flag = False
            for config in configurations:
                if str(more) == str(config):
                    flag = True
            if not flag:
                not_in_configs += [more]

        if not not_in_configs:
            return configurations
        else:
            return self.follow_free_moves(configurations.union(set(not_in_configs)))


class NPDA(object):
    """
        NPDA的实现
    """

    def __init__(self, current_configurations, accept_states, rulebook):
        self._current_configurations = current_configurations
        self.accept_states = accept_states
        self.rulebook = rulebook

    @property
    def current_configurations(self):
        return self.rulebook.follow_free_moves(self._current_configurations)

    @property
    def accepting(self):
        if [config for config in self.current_configurations if config.state in self.accept_states]:
            return True
        else:
            return False

    def read_character(self, character):
        self._current_configurations = self.rulebook.next_configurations(self.current_configurations, character)

    def read_string(self, string):
        for character in string:
            self.read_character(character)


class NPDADesign(object):
    """
        将NPDA封装到NPDADesign里面
    """

    def __init__(self, start_state, bottom_character, accept_states, rulebook):
        self.start_state = start_state
        self.bottom_character = bottom_character
        self.accept_states = accept_states
        self.rulebook = rulebook

    def accepts(self, string):
        npda = self.to_npda
        npda.read_string(string)
        return npda.accepting

    @property
    def to_npda(self):
        start_stack = Stack([self.bottom_character])
        start_configuration = PDAConfiguration(self.start_state, start_stack)
        return NPDA(set([start_configuration]), self.accept_states, self.rulebook)