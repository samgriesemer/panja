# instantiate a TaskWarrior object from tasklib
# self.tasks variable is a QuerySet
# you can filter a query set
# get the filter params using the process_filterstring util from taskwiki
# tw.tasks.filter using those args, get the tasks that should be in the filter
# have raw access and strip dates

# OR
# just us tw.tasks.filter(uuid=<x>) for the tasks
# already filtered on page

from tasklib import TaskWarrior
from datetime import datetime
import textwrap

DEFAULT_DATA = '~/.task/'
DEFAULT_RC   = '~/.taskrc'

DEFAULT_KWARGS = dict(
   data_location=DEFAULT_DATA,
   taskrc_location=DEFAULT_RC,
)

DEFAULT_VIEWPORT_VIRTUAL_TAGS = ("-DELETED", "-PARENT")
DEFAULT_SORT_ORDER = "status+,end+,due+,priority-,project+"

COMPLETION_DATE = """
    now
    yesterday today tomorrow
    later someday

    monday tuesday wednesday thursday friday saturday sunday

    january february march april may june july
    august september october november december

    sopd sod sond eopd eod eond
    sopw sow sonw eopw eow eonw
    sopww soww sonww eopww eoww eonww
    sopm som sonm eopm eom eonm
    sopq soq sonq eopq eoq eonq
    sopy soy sony eopy eoy eony

    goodfriday easter eastermonday ascension pentecost
    midsommar midsommarafton juhannus
""".split()

COMPLETION_RECUR = """
    daily day weekdays weekly biweekly fortnight monthly
    quarterly semiannual annual yearly biannual biyearly
""".split()


# TaskWiki utility conversions
def filterstring_to_tasks(filterstring, tw=None, use_presets=True):
    """
    This method processes taskfilter in the form or filter string,
    parses it into list of filter args, processing any syntax sugar
    as part of the process.

    Following syntax sugar in filter expressions is currently supported:

    * Expand @name with the definition of 'context.name' TW config
      variable

    * Interpret !+DELETED as forcing the +DELETED token.
    * Interpret !-DELETED as forcing the -DELETED token.
    * Interpret !?DELETED as removing both +DELETED and -DELETED.
    """

    def tw_modstring_to_args(line):
        output = []
        escape_global_chars = ('"', "'")
        line = line.strip()

        current_escape = None
        current_part = ''
        local_escape_pos = None

        for i in range(len(line)):
            char = line[i]
            ignored = False
            process_next_part = False

            # If previous char was \, add to current part no matter what
            if local_escape_pos == i - 1:
                local_escape_pos = None
            # If current char is \, use it as escape mark and ignore it
            elif char == '\\':
                local_escape_pos = i
                ignored = True
            # If current char is ' or ", open or close an escaped seq
            elif char in escape_global_chars:
                # First test if we're finishing an escaped sequence
                if current_escape == char:
                    current_escape = None
                    ignored = True
                # Do we have ' inside "" or " inside ''?
                elif current_escape is not None:
                    pass
                # Opening ' or "
                else:
                    current_escape = char
                    ignored = True
            elif current_escape is not None:
                pass
            elif char == ' ':
                ignored = True
                process_next_part = True

            if not ignored:
                current_part += char

            if process_next_part and current_part:
                output.append(current_part)
                current_part = ''

        if current_part:
            output.append(current_part)

        return output


    # Get the initial version of the taskfilter args
    tw = tw if tw else TaskWarrior(**DEFAULT_KWARGS)
    taskfilter_args = list(DEFAULT_VIEWPORT_VIRTUAL_TAGS)
    #if use_presets:
     #   taskfilter_args += list(preset.PresetHeader.from_line(self.line_number, self.cache).taskfilter)
    taskfilter_args += "("
    taskfilter_args += tw_modstring_to_args(filterstring)
    taskfilter_args += ")"

    # Process syntactic sugar: Context expansion
    detected_contexts = []
    for token in filter(lambda x: x.startswith('@'), taskfilter_args):
        context_variable_name = 'context.{0}'.format(token[1:])
        context_definition = tw.config.get(context_variable_name)

        if context_definition:
            context_args = tw_modstring_to_args(context_definition)
            detected_contexts.append((token, context_args))
        else:
            raise print("Context definition for '{0}' "
                    "could not be found.".format(token[1:]))

    for context_token, context_args in detected_contexts:
        # Find the position of the context token
        token_index = taskfilter_args.index(context_token)

        # Replace the token at token_index by context_args list
        taskfilter_args = (
            taskfilter_args[:token_index] +
            context_args +
            taskfilter_args[(token_index+1):]
        )

    # Process syntactic sugar: Forcing virtual tags
    tokens_to_remove = set()
    tokens_to_add = set()

    is_forced_virtual_tag = lambda x: x.isupper() and (
        x.startswith('!+') or
        x.startswith('!-') or
        x.startswith('!?')
    )

    for token in filter(is_forced_virtual_tag, taskfilter_args):
        # In any case, remove the forced tag and the forcing
        # flag from the taskfilter
        tokens_to_remove.add(token)
        tokens_to_remove.add('+' + token[2:])
        tokens_to_remove.add('-' + token[2:])

        # Add forced tag versions
        if token.startswith('!+'):
            tokens_to_add.add('+' + token[2:])
        elif token.startswith('!-'):
            tokens_to_add.add('-' + token[2:])
        elif token.startswith('!?'):
            pass

    for token in tokens_to_remove:
        if token in taskfilter_args:
            taskfilter_args.remove(token)

    taskfilter_args = list(tokens_to_add) + taskfilter_args

    # Deal with the situation when both +TAG and -TAG appear in the
    # taskfilter_args. If one of them is from the defaults, the explicit
    # version wins.

    def detect_virtual_tag(tag):
        return tag.isupper() and tag[0] in ('+', '-')

    def get_complement_tag(tag):
        return ('+' if tag.startswith('-') else '-') + tag[1:]

    virtual_tags = list(filter(detect_virtual_tag, taskfilter_args))
    tokens_to_remove = set()
    # For each virtual tag, check if its complement is in the
    # taskfilter_args too. If so, remove the tag that came from defaults.
    for token in virtual_tags:
        complement = get_complement_tag(token)
        if complement in virtual_tags:
            # Both tag and its complement are in the taskfilter_args.
            # Remove the one from defaults.
            if token in DEFAULT_VIEWPORT_VIRTUAL_TAGS:
                tokens_to_remove.add(token)
            if complement in DEFAULT_VIEWPORT_VIRTUAL_TAGS:
                tokens_to_remove.add(complement)

    for token in tokens_to_remove:
        if token in taskfilter_args:
            taskfilter_args.remove(token)

    # Process meta tags, remove them from filter
    meta = dict()

    for token in taskfilter_args:
        if token == '-VISIBLE':
            meta['visible'] = False

    #taskfilter_args = [x for x in taskfilter_args
    #                  if x not in self.meta_tokens]

    # If, after all processing, any empty parens appear in the
    # seqeunce of taskfilter_args, remove them
    def deempty_parenthesize(tokens):
        empty_paren_index = None

        # Detect any empty parenthesis pair
        for index, token in enumerate(tokens):
            if token == '(' and tokens[index+1] == ')':
                empty_paren_index = index

        # Delete empty pair, if found
        if empty_paren_index is not None:
            del tokens[empty_paren_index]
            del tokens[empty_paren_index]

            # Attempt to delete next one, if it exists
            deempty_parenthesize(tokens)

    deempty_parenthesize(taskfilter_args)

    # All syntactic processing done, return the resulting filter args
    return tw.tasks.filter(*taskfilter_args)

def prepare_task_header(query):
    '''
    Accepts a taskwiki-style viewport query, returns a task list sorted by
    urgency. Second return value is time in milliseconds to the earliest pending
    task in the list.
    '''
    tasklist = sorted(map(lambda x: x._data, filterstring_to_tasks(query)),
        key=lambda x: x.get('urgency',0) if x.get('status') == 'pending' else 0,
        reverse=True
    )
    valid = sorted([
        t['due'].timestamp() for t in tasklist
        if t.get('due') and t.get('status') == 'pending'
    ])
    earliest = valid[0] if valid else 0
    
    return tasklist, earliest


def get_all_tasks(tw=None):
    tw = tw if tw else TaskWarrior(**DEFAULT_KWARGS)
    return tw.tasks

def get_task_by_id(uuid, tw=None):
    tw = tw if tw else TaskWarrior(**DEFAULT_KWARGS)
    task = tw.tasks.filter(uuid=uuid)

    return task[-1] if task else None

def get_tasks_from_ids(uuid_list):
    tw = TaskWarrior(**DEFAULT_KWARGS)

    tasks = []
    for uuid in uuid_list:
        task = get_task_by_id(uuid, tw=tw)
        if task: tasks.append(task)
    return tasks

def taskdict_to_gantt_raw(taskdict, title='Gantt'):
    '''
    taskdict: dictionary of (section name, tasklist) pairs to be
    added to the Gantt chart.
    '''
    if not taskdict: return None

    gantt_txt = '''```{{.mermaid format=svg width=1000 caption="rawmm"}}
    %%{{init:{{'theme':'base','themeVariables':{{'primaryColor':'#646adc9c','backgroundColor':'transparent'}}}}}}%%
    gantt
        title {title}
        dateFormat X

    '''.format(title=title)

    for section, tasklist in taskdict.items():
        section_txt = '''
        section {section}
        '''.format(section=section)

        for task in tasklist:
            # task is pending and started or not, or completed
            # may also have a due date
            taskdata = {**task._data}
            taskdata['entry'] = round(taskdata['entry'].timestamp(),3)

            # end present if completed
            if 'end' not in taskdata:
                if 'due' in taskdata:
                    taskdata['end'] = taskdata['due'].timestamp()
                else:
                    taskdata['end'] = datetime.now().timestamp()
            else:
                taskdata['end'] = taskdata['end'].timestamp()
            taskdata['end'] = round(taskdata['end'],3)
            
            # set status to active if started
            if 'start' in taskdata:
                taskdata['status'] = 'active'
            
            # set status to done if completed
            if taskdata['status'] == 'completed':
                taskdata['status'] = 'done'

            taskdata['description'] = taskdata['description'].replace(';','#59;')
            taskdata['description'] = taskdata['description'].replace(':','#58;')

            # set crit priority if high
            taskdata['crit'] = ''
            if taskdata.get('priority') == 'H':
                taskdata['crit'] = 'crit,'

            section_txt += '''
            {description} :{crit} {status}, {entry}, {end}
            '''.format(**taskdata)

        gantt_txt += section_txt

    gantt_txt += '\n```'

    return textwrap.dedent(gantt_txt)

