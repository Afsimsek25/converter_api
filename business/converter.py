import json
import re
import os
from business import excel_operations as xl
wb = None
ws = None
events = []
element = []
anchored_events = []
step = None
event = None
classifier = None
text = None
order = None
anchor = None
anchor_sign = '>'
classifier_in_anchor = None
text_in_anchor = None
order_in_anchor = None


def get_text_between_quotes(line):
    return re.findall(r'(?<=")(.*?)(?=")', line)
def get_text_in_line(items):
    text = ""
    for item in items:
        if str(item).startswith('>'):
            break
        else:
            text += (item + " ")
    return text

def find_indices(list_to_check, item_to_find):
    indices = []
    for idx, value in enumerate(list_to_check):
        if value == item_to_find:
            indices.append(idx)
    return indices
def get_ordered_item_and_order(items):
    for i, item in enumerate(items):
        if str(item).__contains__('['):
            order_index = str(item).index('[')
            only_item = str(item)[0:order_index]
            order = str(item).__getitem__(order_index + 1)
            return i, only_item, order
def line_have_order(line):
    have = False
    for element in line.split(" "):
        if str(element).__contains__('[') and str(element).__contains__(']'):
            have = True
    return have
def listToString(s):
    str1 = " "
    str = (str1.join(s))
    strc = str.strip()
    return strc
def get_items_between_anchors(items):
    items_between_anchors = []
    for it in listToString(items[1:len(items)]).split(anchor_sign):
        items_between_anchors.append(it.strip())
    return items_between_anchors
def anchored_element_switcher(list):
    global classifier_in_anchor
    global text_in_anchor
    global order_in_anchor
    global element
    element = []

    for item in list:
        classifier_in_anchor = None
        text_in_anchor = None
        order_in_anchor = None

        item_list = item.split(' ')
        have_order = line_have_order(item)
        if len(item_list) > 1:
            classifier_in_anchor = item_list[0]
            text_in_anchor = listToString(item_list[1:])
            if have_order:
                ordered_item = get_ordered_item_and_order(item_list)
                order_in_anchor = ordered_item[1]
            element.append({
                'classifier': classifier_in_anchor,
                'order': order_in_anchor,
                'text': text_in_anchor
            })
        else:
            if have_order:
                ordered_item = get_ordered_item_and_order(item_list)
                classifier_in_anchor = ordered_item[1]
                order_in_anchor = ordered_item[2]
            else:
                classifier_in_anchor = item_list[0]
            element.append({
                'classifier': classifier_in_anchor,
                'order': order_in_anchor,
                'text': text_in_anchor
            })
    return element
def line_have_anchor(line):
    have = False
    for element in line.split(" "):
        if str(element).__contains__('>'):
            have = True
    return have
def txt_to_list(path):
    with open(path, encoding="utf-8") as f:
        return f.readlines()
def xl_to_list(path):
    list = []
    xl.connect(path)
    xl.navigate_sheet()
    step_no = xl.search_spesific_value('Step No')
    last_row = xl.get_max_row()
    for x in range(int(step_no.row) + 1, int(last_row)):
        line = str(xl.get_data(x, 1).value) + " " + str(xl.get_data(x, 2).value)
        list.append(line)
    return list
def switch_item(line):
    global step
    global event
    global classifier
    global order
    global text
    global element

    element = None
    step = None
    event = None
    classifier = None
    order = None
    text = None

    have_order = line_have_order(line)
    items = line.split(" ")
    step = re.findall(r'\d+', str(items[0]))[0]
    event = items[1]
    classifier = items[2]
    if have_order:
        ordered_item = get_ordered_item_and_order(items)
        order = ordered_item[2]
        classifier = ordered_item[1]
    if (classifier == 'Text' or
        classifier == 'Button' or
        classifier == 'InputLabel' or
        classifier == 'ProductBox' or
        classifier == 'Image'):
        if items[3:len(items)]:
            text = get_text_in_line(items[3:len(items)]).rstrip(' ')

    element = [{
        'classifier': classifier,
        'order': order,
        'text': text
    }]
    return step, event, element
def anchored_line_switch(line):
    anchor_index = line.index('>')
    first_part = line[0:anchor_index]
    second_part = line[anchor_index:]
    first = switch_item(first_part)
    anchored_part = anchored_element_switcher(get_items_between_anchors(second_part.split(' ')))
    return first[0], first[1], first[2], anchored_part
def line_parser(line):
    if line_have_anchor(line):
        line_content = anchored_line_switch(line)
        return line_content, 'Anc'
    elif not line_have_anchor(line):
        line_content = switch_item(line)
        return line_content, 'NotAnc'
def event_parser(list):
    for line in list:
        line = line.strip('\n')
        if str(line).__contains__("Click"):
            content = line_parser(line)
            if content[1] == 'Anc':
                save_event(step=content[0][0], event=content[0][1], element=content[0][2][0],
                           anchored_element=content[0][3])
            elif content[1] == 'NotAnc':
                save_event(step=content[0][0], event=content[0][1], element=content[0][2])
        elif str(line).__contains__("Write"):
            data = get_text_between_quotes(line)[0]
            line = line.replace(' "' + data + '"', '')
            content = line_parser(line)
            if content[1] == 'Anc':
                save_event(step=content[0][0], event=content[0][1], element=content[0][2][0],
                           anchored_element=content[0][3], data=data)
            elif content[1] == 'NotAnc':
                save_event(step=content[0][0], event=content[0][1], element=content[0][2], data=data)
        elif str(line).__contains__("MoveMouseTo"):
            content = line_parser(line)
            if content[1] == 'Anc':
                save_event(step=content[0][0], event=content[0][1], element=content[0][2][0],
                           anchored_element=content[0][3])
            elif content[1] == 'NotAnc':
                save_event(step=content[0][0], event=content[0][1], element=content[0][2])
        elif str(line).__contains__("Hover"):
            content = line_parser(line)
            if content[1] == 'Anc':
                save_event(step=content[0][0], event=content[0][1], element=content[0][2][0],
                           anchored_element=content[0][3])
            elif content[1] == 'NotAnc':
                save_event(step=content[0][0], event=content[0][1], element=content[0][2])
        elif str(line).__contains__("Hover_And_Click"):
            content = line_parser(line)
            if content[1] == 'Anc':
                save_event(step=content[0][0], event=content[0][1], element=content[0][2][0],
                           anchored_element=content[0][3])
            elif content[1] == 'NotAnc':
                save_event(step=content[0][0], event=content[0][1], element=content[0][2])
        elif str(line).__contains__("Get_Text"):
            content = line_parser(line)
            if content[1] == 'Anc':
                save_event(step=content[0][0], event=content[0][1], element=content[0][2][0],
                           anchored_element=content[0][3])
            elif content[1] == 'NotAnc':
                save_event(step=content[0][0], event=content[0][1], element=content[0][2])
        elif str(line).__contains__("IsVisible"):
            content = line_parser(line)
            if content[1] == 'Anc':
                save_event(step=content[0][0], event=content[0][1], element=content[0][2][0],
                           anchored_element=content[0][3])
            elif content[1] == 'NotAnc':
                save_event(step=content[0][0], event=content[0][1], element=content[0][2])
        elif str(line).__contains__("Scroll"):
            content = line.split(" ")
            save_event(step=content[0], event=content[1], px=content[2])
        elif str(line).__contains__("Delay"):
            content = line.split(" ")
            save_event(step=content[0], event=content[1], milis=content[2])
def returner(element=None, anchored_element=None):
    event = []
    event.append(element)
    for x in range(len(anchored_element)):
        event.append(anchored_element[x])
    return event
def save_json():
    with open('events.json', 'w', encoding='utf8') as event:
        json.dump(events, event, indent=4, ensure_ascii=False)
    return
def save_event(step, event, element=None, anchored_element=None, data=None, px=None, milis = None):
    if event == 'Write':
        if anchored_element:
            anchored_part = returner(element, anchored_element)
            info = {
                'step': step,
                'event': event,
                'data': data,
                'elements': anchored_part
            }
            events.append(info)
        else:
            info = {
                'step': step,
                'event': event,
                'data': data,
                'elements': element
            }
            events.append(info)
    elif event == 'Scroll':
        info = {
            'step': step,
            'event': event,
            'px': px
        }
        events.append(info)
    elif event == 'Delay':
        info = {
            'step': step,
            'event': event,
            'milisecond': milis
        }
        events.append(info)

    else:
        if anchored_element:
            anchored_part = returner(element, anchored_element)
            info = {
                'step': step,
                'event': event,
                'elements': anchored_part
            }
            events.append(info)
        else:
            info = {
                'step': step,
                'event': event,
                'elements': element
            }
            events.append(info)
    return
def path_router(path):
    file_extension = os.path.splitext(path)[1]
    if str(file_extension) == '.txt':
        event_list = txt_to_list(path)
    elif str(file_extension) == '.xlsx':
        event_list = xl_to_list(path)
    else:
        raise Exception('We only support .txt and .xlsx formats')
    event_parser(event_list)
def run(path):
    path_router(path)
    save_json()
