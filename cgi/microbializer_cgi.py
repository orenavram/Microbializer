#!/data/shared/python/anaconda3-5.1.0/bin/python3.6

import os
import shutil
import sys
import cgi
import cgitb
import subprocess
from time import time, ctime
from random import randint

import WEBSERVER_CONSTANTS as CONSTS
if os.path.exists('/bioseq/microbializer'): # remote run
    sys.path.append('/bioseq/microbializer/auxiliaries/')
    sys.path.append('/bioseq/bioSequence_scripts_and_constants/')
else:
    # local run
    sys.path.append('../auxiliaries/')

from directory_creator import create_dir # from /bioseq/microbializer/auxiliaries/
from email_sender import send_email # from /bioseq/bioSequence_scripts_and_constants/

def print_hello_world(output_path = '', run_number = 'NO_RUN_NUMBER'):

    hello_world_html = """
<html>
    <body>
        <h2>Hello World! """ + run_number + """</h2>
    </body>
</html>
    """
    if not output_path:
        print(hello_world_html)
    else:
        with open(output_path, 'w') as f:
            f.write(hello_world_html)


def write_to_debug_file(cgi_debug_path_f, content):
    cgi_debug_path_f.write(f'{ctime()}: {content}\n')


def write_html_prefix(output_path_f, run_number):
    output_path_f.write(f'''<html><head>

    <meta http-equiv="cache-control" content="no-cache, must-revalidate, post-check=0, pre-check=0" />
    <meta http-equiv="cache-control" content="max-age=0" />
    <meta http-equiv="expires" content="0" />
    <meta http-equiv="expires" content="Tue, 01 Jan 1980 1:00:00 GMT" />
    <meta http-equiv="pragma" content="no-cache" />
    {CONSTS.RELOAD_TAGS}

    <title>{CONSTS.WEBSERVER_NAME} Job #{run_number}</title>
    <link rel="shortcut icon" type="image/x-icon" href="{CONSTS.WEBSERVER_URL}/pics/logo.gif" />

    <meta charset="utf-8">
    <!--<meta name="viewport" content="width=device-width, initial-scale=1">-->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>
    <link rel="stylesheet" href="https://gitcdn.github.io/bootstrap-toggle/2.2.2/css/bootstrap-toggle.min.css">

    <link rel="stylesheet" href="{CONSTS.WEBSERVER_URL}/css/general.css">
    <link rel="stylesheet" href="../webpage/css/general.css">

    </head><body>
    <nav role="navigation" class="navbar navbar-inverse navbar-fixed-top">
        <div class="jumbotron" id="jumbo">
            <div class="container">            
                <div class="row" id="title-row" align="center">
                    <div class="col-md-1">
                    </div>
                    <div class="col-md-10">
                        <span id="server-title">{CONSTS.WEBSERVER_NAME}</span>
                        <img src="{CONSTS.WEBSERVER_URL}/pics/logo.gif" id="nav_bar_image" class="img-rounded">
                        <br><span id="sub-title">{CONSTS.WEBSERVER_TITLE}</span>
                    </div>
                </div>
            </div>       
        </div>
    </nav>
    <div id="behind-nav-bar-results">
    </div>
    <br><br><div class="container" style="font-size: 17px; {CONSTS.CONTAINER_STYLE}"  align="justify"> 
    <H1 align=center>Job Status: <FONT color='red'>RUNNING</FONT></h1>
    <br>{CONSTS.WEBSERVER_NAME} is now processing your request. This page will be automatically updated every {CONSTS.RELOAD_INTERVAL} seconds (until the job is done). You can also reload it manually. Once the job has finished, the output will appear below. A link to this page was sent to your email in case you wish to view these results at a later time without recalculating them. Please note that the results will be kept in the server for 3 months.
    <br><br></div>''')
    output_path_f.flush()


def write_running_parameters_to_html(output_path_f, job_title, file_name=''):
    output_path_f.write(f'<div class="container" style="{CONSTS.CONTAINER_STYLE}">')

    # regular params rows
    output_path_f.write('<div class="row" style="font-size: 20px;"><div class="col-md-6">')
    output_path_f.write(f'<b>Folder name: </b>{file_name}')
    output_path_f.write('</div></div>')

    # optional params rows
    if job_title != '':
        output_path_f.write('<div class="row" style="font-size: 20px;"><div class="col-md-6">')
        output_path_f.write(f'<b>Job title: </b>{job_title}')
        output_path_f.write('</div></div>')

    output_path_f.write('</div><br>')


def write_cmds_file(cmds_file, parameters, run_number):
    # the queue does not like very long commands so I use a dummy delimiter (!@#) to break the commands for q_submitter
    new_line_delimiter = '!@#'
    # the code contains features that are exclusive to Python3.6 (or higher)!
    required_modules = ' '.join(
        ['python/anaconda_python-3.6.4'])
    with open(cmds_file, 'w') as f:
        f.write(f'module load {required_modules};')
        f.write(new_line_delimiter)
        f.write(f'{" ".join(["python", CONSTS.MAIN_SCRIPT, parameters])}\tM1CRO{run_number}') # mic stands for M1CROB1AL1Z3R

def run_cgi():

    # prints detailed error report on BROWSER when backend crashes
    # This line MUST appear (as is) BEFORE any error occurs to get a report about the exception!! otherwise you'll get a non-informatvie message like "internal server error"
    cgitb.enable()

    # print_hello_world() # for debugging
    form = cgi.FieldStorage()  # extract POSTed object

    # random_chars = "".join(choice(string.ascii_letters + string.digits) for x in range(20))
    run_number = str(round(time())) + str(randint(10 ** 19, 10 ** 20 - 1))  # adding 20 random digits to prevent users see data that are not their's
    if False:
        run_number = 'debug'  # str(round(time())) + str(randint(1000,9999)) # adding 4 random figures to prevent users see data that are not their's

    results_url = os.path.join(CONSTS.WEBSERVER_RESULTS_URL, run_number)
    output_url = os.path.join(results_url, 'output.html')

    wd = os.path.join(CONSTS.WEBSERVER_RESULTS_DIR, run_number)
    create_dir(wd)
    output_path = os.path.join(wd, 'output.html')
    output_path_f = open(output_path, 'w')
    cgi_debug_path = os.path.join(wd, 'cgi_debug.txt')
    #print('Content-Type: text/html\n')  # For more details see https://www.w3.org/International/articles/http-charset/index#scripting
    # print_hello_world(output_html_path, run_number) # comment out for debugging

    write_html_prefix(output_path_f, run_number)  # html's prefix must be written BEFORE redirecting...

    print(f'Location: {output_url}')  # Redirects to the results url. MUST appear before any other print.
    print('Content-Type: text/html\n')  # For more details see https://www.w3.org/International/articles/http-charset/index#scripting
    sys.stdout.flush()  # must be flushed immediately!!!

    # Send me a notification email every time there's a new request
    send_email(smtp_server=CONSTS.SMTP_SERVER,
               sender=CONSTS.ADMIN_EMAIL,
               receiver=f'{CONSTS.OWNER_EMAIL}',
               subject=f'{CONSTS.WEBSERVER_NAME} - A new job has been submitted: {run_number}',
               content=f"{os.path.join(CONSTS.WEBSERVER_URL, 'results', run_number, 'cgi_debug.txt')}\n"
                        f"{os.path.join(CONSTS.WEBSERVER_URL, 'results', run_number, 'output.html')}")

    try:
        cgi_debug_path_f = open(cgi_debug_path,'w')

        if 'email' in form and form['email'].value != '':
            write_to_debug_file(cgi_debug_path_f, f"{form['email'].value.strip()}\n\n")

        # for debugging
        write_to_debug_file(cgi_debug_path_f, f'{"#"*100}\n{ctime()}: A new CGI request has been recieved!\n')
        sorted_form_keys = sorted(form.keys())
        write_to_debug_file(cgi_debug_path_f, f'These are the keys that the CGI received:\n{"; ".join(sorted_form_keys)}\n\n')
        write_to_debug_file(cgi_debug_path_f, 'Form values are:\n')
        for key in sorted_form_keys:
            if 'data' not in key:
                write_to_debug_file(cgi_debug_path_f, f'{key} = {form[key]}\n')
        for key in sorted_form_keys:
            if 'data' in key:
                write_to_debug_file(cgi_debug_path_f, f'100 first characters of {key} = {form[key].value[:100]}\n')

        # extract form's values:
        user_email = form['email'].value.strip()

        job_title = ''
        if form['job_title'].value != '':
            job_title = form['job_title'].value.strip()

        # This is hidden field that only spammer bots might fill in...
        confirm_email_add = form['confirm_email'].value  # if it is contain a value it is a spammer.

        if form['example_page'] == 'no':
            write_to_debug_file(cgi_debug_path_f, f'\n{"#"*80}\nuploading data\n')

            file_name = form['data'].filename
            write_to_debug_file(cgi_debug_path_f, f'file name is:\n{file_name}')

            data = form['data'].value
            write_to_debug_file(cgi_debug_path_f, f'{file_name} first 100 chars are: {data[:100]}\n')

            data_path = os.path.join(wd, file_name)
            with open(data_path, 'wb') as data_f:
                data_f.write(data)
            write_to_debug_file(cgi_debug_path_f, f'Uploaded data was saved to disk successfully\n')
        else:  # example data
            file_name = 'example_data.tar.gz'
            data_path = os.path.join(wd, file_name)
            write_to_debug_file(cgi_debug_path_f, f'Copying example data FROM {CONSTS.EXAMPLE_DATA} TO {data_path}\n')
            try:
                shutil.copy(CONSTS.EXAMPLE_DATA, data_path)
                write_to_debug_file(cgi_debug_path_f, f'File was copied successfully to {data_path}\n\n')
            except IOError as e:
                write_to_debug_file(cgi_debug_path_f, f'{"#" * 50}\nFailed to copy for example data due to the following reason:\n{e.args[0]}\n{"#" * 50}\n')
                raise e

        write_to_debug_file(cgi_debug_path_f, f'ls of {wd} yields:\n{os.listdir(wd)}\n')

        write_to_debug_file(cgi_debug_path_f, f'{ctime()}: write_running_parameters_to_html...\n')
        write_running_parameters_to_html(output_path_f, job_title, file_name)
        write_to_debug_file(cgi_debug_path_f, f'{ctime()}: Running parameters were written to html successfully.\n')

        parameters = f'{data_path} {os.path.join(wd, "outputs")} {CONSTS.OWNER_EMAIL} -q bioseq'

        cmds_file = os.path.join(wd, 'qsub.cmds')
        write_cmds_file(cmds_file, parameters, run_number)

        log_file = cmds_file.replace('cmds', 'log')
        # complex command with more than one operation (module load + python q_submitter.py)
        # submission_cmd = 'ssh bioseq@lecs2login "module load python/anaconda_python-3.6.4; python /bioseq/bioSequence_scripts_and_constants/q_submitter.py {} {} -q {} --verbose > {}"'.format(cmds_file, wd, queue_name, log_file)

        # simple command when using shebang header
        submission_cmd = f'ssh bioseq@lecs2login /bioseq/bioSequence_scripts_and_constants/q_submitter.py {cmds_file} {wd} -q bioseq --verbose > {log_file}'

        write_to_debug_file(cgi_debug_path_f, f'\nSSHing and SUBMITting the JOB to the QUEUE:\n{submission_cmd}\n')

        subprocess.call(submission_cmd, shell=True)

        if user_email != '':
            with open(os.path.join(wd, 'user_email.txt'), 'w') as email_f:
                email_f.write(f'{user_email}\n')

        write_to_debug_file(cgi_debug_path_f, f'\n\n{"#"*50}\nCGI finished running!\n{"#"*50}\n')

        cgi_debug_path_f.close()
        output_path_f.close()

    except Exception as e:
        msg = 'CGI crashed before the job was submitted :('
        with open(output_path) as f:
            html_content = f.read()
        html_content = html_content.replace('RUNNING', 'FAILED')
        html_content += f'<br><br><br><center><h2><font color="red">{msg}</font><br><br>Please try to re-run your job or <a href="mailto:{CONSTS.ADMIN_EMAIL}?subject={CONSTS.WEBSERVER_NAME}%20Run%20Number%20{run_number}">contact us</a> for further information</h2></center><br><br>\n</body>\n</html>\n'
        with open(output_path, 'w') as f:
            f.write(html_content)

        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        with open(cgi_debug_path, 'w') as cgi_debug_path_f:
            write_to_debug_file(cgi_debug_path_f, f'\n{"$"*100}\n\n{msg}\n\n{fname}: {exc_type}, at line: {exc_tb.tb_lineno}\n\ne.args[0]: {e.args[0]}\n\n{"$"*100}')

        # Send me a notification email every time there's a failure
        try:
            email = form['email'].value.strip() if form['email'].value.strip() else 'NO_EMAIL'
        except:
            email = 'NO_EMAIL'
        send_email(smtp_server=CONSTS.SMTP_SERVER,
                   sender=CONSTS.ADMIN_EMAIL,
                   receiver=f'{CONSTS.OWNER_EMAIL}',
                   subject=f'{CONSTS.WEBSERVER_NAME} job {run_number} by {email} has been failed!',
                   content=f"{email}\n\n{os.path.join(CONSTS.WEBSERVER_URL, 'results', run_number, 'output.html')}\n"
                            f"\n{os.path.join(CONSTS.WEBSERVER_URL, 'results', run_number, 'cgi_debug.txt')}")

        # logger.info(f'Waiting {2*CONSTS.RELOAD_INTERVAL} seconds to remove html refreshing headers...')
        # Must be after flushing all previous data. Otherwise it might refresh during the writing.. :(
        from time import sleep

        sleep(2 * CONSTS.RELOAD_INTERVAL)
        with open(output_path) as f:
            html_content = f.read()
        html_content = html_content.replace(CONSTS.RELOAD_TAGS, '')
        with open(output_path, 'w') as f:
            f.write(html_content)

if __name__ == '__main__':
    run_cgi()