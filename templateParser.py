import inspect
import re
# TODO MOVE IMPORT TO TEST FILE BELOW
#from processor import Processor
from collections.abc import Iterable

top_level_regex = r'(\$\w+\(?[\w\,\$\(\)]*\)?)'
inner_function_regex = r'\$(\w+)'
#p = Processor()

def snakeCaseToCamelCase(snake_case):
    # saving first and rest using split()
    init, *temp = snake_case.split('_')
    res = ''.join([init.lower(), *map(str.title, temp)])
    return str(res)


def cameltoSnake(str):
    return ''.join(['_' + i.lower() if i.isupper()
                    else i for i in str]).lstrip('_')

def flatten(l):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, dict) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el

def processVariables(variable, state, processor):
    if bool(re.match("\$\w+\(",variable)):
        # find all sub variables in process variable
        split_variables = "(".join(variable.split("(")[1:])
        #inner_variables = list(map(lambda x: x.split(","), re.findall(top_level_regex, split_variables)))[0]
        ## TODO remove above once all test cases pass
        inner_variables = re.findall(top_level_regex, split_variables)
        x = list(map(lambda inner_variable: processVariables(inner_variable, state, processor), inner_variables))
        arguments = flatten(x)
        func = variable.split("(")[0].replace("$", "")
        try:
            return getattr(processor,func)(*arguments)
        except:
            return getattr(processor, func)(*x[0])
    elif "," in variable:
        inner_variables = re.findall(inner_function_regex, variable)
        args = list(map(lambda inner_variable: processVariables(inner_variable, state, processor), inner_variables))
        return args
    elif variable.replace("$","").replace(")","").isnumeric():
        return variable.replace("$","").replace(")","")
    elif variable.replace("$","").replace(")","").isupper():
        return variable.replace("$","").replace(")","")
    else:
        # TODO improve parser not to need this step
        key = variable.replace("$","").replace(")","")
        # check if key is in state
        if key == "state":
            return state
        elif key in state:
            return state[key]
        elif 'persisted' in state and key in state['persisted']:
            return state['persisted'][key]
        # update state
        else:
            func_key = snakeCaseToCamelCase("get_"+key)
            func_args = inspect.getfullargspec(getattr(processor, func_key))[0][1:]
            args = []
            for func_arg in func_args:
                ## TODO consider removing if no usecase is found
                if func_arg == "state":
                    args.append(state)
                else:
                    args.append(processVariables(func_arg, state, processor))
            new_val = getattr(processor,func_key)(*args)
            new_state = {key: new_val}
            state.update(new_state)
            return new_val


def processTemplate(template, state, processor):
    template_vars = re.findall(top_level_regex, template)
    result = map(lambda template_var: processVariables(template_var, state, processor), template_vars)
    for item in list(result):
        template = re.sub(top_level_regex, str(item), template, 1)
    return template

def messageStateProcessor(message_state_proc, state, processor):
    outer_most_func = message_state_proc.split("(")[0].replace("$", "")
    split_func_to_key = cameltoSnake(outer_most_func).split("get_")
    if len(cameltoSnake(outer_most_func).split("get_")) > 1:
        key = cameltoSnake(outer_most_func).split("get_")[1]
    else:
        key = outer_most_func
    result = processVariables(message_state_proc, state, processor)
    state.update({key: result})
    return state

def resultProcessor(message_state_proc, state, processor):
    outer_most_func = message_state_proc.split("(")[0].replace("$", "")
    split_func_to_key = cameltoSnake(outer_most_func).split("get_")
    if len(cameltoSnake(outer_most_func).split("get_")) > 1:
        key = cameltoSnake(outer_most_func).split("get_")[1]
    else:
        key = outer_most_func
    result = processVariables(message_state_proc, state, processor)
    return result

# TODO MOVE TO TEST FILE BELOW
# example call
#processTemplate("$add($a,$add($b,$subtract($a,b))) men $subtract($a,$b) went to $a and then to $b", variables, p)
# TODO MOVE TO TEST FILE ABOVE

