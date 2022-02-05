def renderOption(option):
    return "<label><input type='checkbox' onclick='handleClick(this)' value='{}'><span>{}</span></label>".format(option, option)

def renderOptions(options):
    return "<p class='chat_options'>" + "".join(map(renderOption, options)) + "</p>"
