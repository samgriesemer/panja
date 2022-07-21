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

