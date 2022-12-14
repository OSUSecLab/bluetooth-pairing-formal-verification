import subprocess, resource
from prettytable import PrettyTable
import os, re, pwd, platform, uuid
from pathlib import Path, PurePath
from threading import Timer
from time import strftime, gmtime
from datetime import datetime
import platform

import shutil
import smtplib, ssl
import argparse
from email.mime.text import MIMEText

parser = argparse.ArgumentParser()

parser.add_argument('--tam_code_file', dest='tamCodeFile', help='Tamarin code file')

parser.add_argument( '--timeout_min', dest='timeout_min' ,type=float, default=20, help='timeout in minutes')
parser.add_argument( '--folder_resume', dest='folder_resume', type=str, default=None, help='last resume folder name')
parser.add_argument('--trace_algos', action='store', dest='trace_algos', type=str, nargs='*', default=['SEQDFS', 'DFS', 'BFS'],   help="list of trace_algos e.g. --trace_algos DFS BFS")

parser.add_argument('--prove_src_lemmas', dest='prove_src_lemmas', default=False, action='store_true' , help='if mentioned as command line argument will prove source lemmas in additional to other non-source lemmas (default is to skip proving source lemma)')
parser.add_argument('--prove_reuse_lemmas', dest='prove_reuse_lemmas', default=False, action='store_true' , help='if mentioned as command line argument will prove reuse lemmas in additional to other non-reuse lemmas default is to skip proving reuse lemma')
parser.add_argument('--save_only_last_lines_of_proof', dest='save_only_last_lines_of_proof', default=False, action='store_true' , help='save disk space by storing only last lines of proof output')


parser.add_argument('--auto-sources', dest='auto_sources', default=False, action='store_true' , help='add --auto-sources flag in the command ')
parser.add_argument('--prove-only-auto-typing', dest='prove_only_auto_typing', default=False, action='store_true' , help='This will prove only the autogenerated source lemma with --auto-source flag')
parser.add_argument('--oracle_file_path', dest='oracle_file_path', type=str, default=None, help='path to the oracle file')

parser.add_argument( '--summary_copy_folder', dest='summary_copy_folder', type=str, default='', help='Additional Path to copy summary file')

parser.add_argument('--exclude_lemmas', action='store', dest='exclude_lemmas', type=str, nargs='*', default=[],   help="list of lemmas to exclude  e.g. --exclude_lemmas lemmaA lemmaB")



cmd_args = parser.parse_args()

trace_search_algos = cmd_args.trace_algos


timeout_sec = 60*cmd_args.timeout_min  # sec


filetext = None
with open(cmd_args.tamCodeFile, 'r') as file:
    filetext = file.read()

include_lemmas =[g1 for g1,g2 in re.findall('^[ ]*lemma (?P<lemma_name>[^;]*?)( |:)', filetext, re.MULTILINE)]



list_exclude_lemmas = []
    
# soruce lemma will remain with all other lemmas
for lemma_name in include_lemmas:
    
    # by default we will not prove source lemmas
    if not cmd_args.prove_src_lemmas:
        if lemma_name.endswith('_src'):
            list_exclude_lemmas.append(lemma_name)

    # by default we will not prove reuse lemmas
    if not cmd_args.prove_reuse_lemmas:
        if lemma_name.endswith('_reuse'):
            list_exclude_lemmas.append(lemma_name)


list_exclude_lemmas += cmd_args.exclude_lemmas

# remove exclude list items
for lemma_name in list_exclude_lemmas:
    include_lemmas.remove(lemma_name)



cmdstr_lemmas = []


for il in include_lemmas:
    temp_str= ''
    for l in il.split(','):
        temp_str += ' --prove='+l
    cmdstr_lemmas.append((il,temp_str))


p = PurePath(cmd_args.tamCodeFile)
folder_parent =  p.parent.as_posix() + '/'
basename= p.stem

if not cmd_args.folder_resume:
    save_folder_basename = basename + datetime.now().strftime("_%Y_%b_%d_%a_%I_%M_%S_%p")
    # save_folder_basename = cmd_args.run_tag
    save_dir = folder_parent+ save_folder_basename
    file_copy = save_dir +'/'+ basename + '.spthy'
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    shutil.copy(folder_parent + basename + '.spthy', file_copy)    
else:
    # if resuming a user will provide the existing folder in cmd_args.folder_resume
    save_folder_basename = cmd_args.folder_resume
    save_dir = folder_parent+ cmd_args.folder_resume    
    file_copy = save_dir +'/'+ basename + '.spthy'
    # make a copy of existing summary file
    shutil.copy(save_dir + '/summary.txt', save_dir+'/summary_'+datetime.now().strftime("_%Y_%b_%d_%a_%I_%M_%S_%p")+'.txt')

    if cmd_args.summary_copy_folder != '':
        shutil.copy(save_dir + '/summary.txt', cmd_args.summary_copy_folder+'/summary_'+datetime.now().strftime("_%Y_%b_%d_%a_%I_%M_%S_%p")+'.txt')
        


pt = PrettyTable()
pt.field_names = ['lemmas', 'trace_algo', 'wall_time', 'user_time', 'sys_time'  ]



for trace_search_algo in trace_search_algos:
    for (lemma_names, cmdstr_lemma) in cmdstr_lemmas: 
        
        proof_case = lemma_names.replace(',', '_')+'.spthyproof'


        if not Path(save_dir+'/'+ proof_case).exists():
            
            
            # 
            cmd =  'exec tamarin-prover '+ (' --auto-sources' if (cmd_args.prove_only_auto_typing or cmd_args.auto_sources) else '') +(' --oraclename='+ cmd_args.oracle_file_path if cmd_args.oracle_file_path else ' --stop-on-trace='+trace_search_algo) +' '+cmdstr_lemma+ ' '+ file_copy
            
            

            print('start -- '+proof_case + '\ncmd: '+cmd)
            # print('start -- '+proof_case )
            
            wall_t_start = datetime.now()
            usage_start = resource.getrusage(resource.RUSAGE_CHILDREN)

            process= subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

            timer = Timer(timeout_sec, process.kill) # timeout
            try:
                timer.start()
                process_output = process.communicate()[0].decode('utf-8',errors='replace')
                # https://python-reference.readthedocs.io/en/latest/docs/str/decode.html   
                # 'strict' --    Raise ValueError (or a subclass); this is the default.
                # 'ignore' --  Ignore the character and continue with the next.
                # 'replace' --  Replace with a suitable replacement character       
            finally:
                timer.cancel()                     
                process.terminate()


            usage_end = resource.getrusage(resource.RUSAGE_CHILDREN)
            wall_t_end = datetime.now()

            user_time = usage_end.ru_utime - usage_start.ru_utime
            system_time = usage_end.ru_stime - usage_start.ru_stime
            wall_time_diff = wall_t_end - wall_t_start

            # detect if timeout occured based on output_string
            proof_completed = False
            timeout_suffix = ''
            if 'summary of summaries:' not in process_output:
                timeout_suffix = '**TO'
            else:
                proof_completed = True



            
            pt.add_row([lemma_names + timeout_suffix, trace_search_algo, strftime("%H:%M:%S", gmtime(wall_time_diff.seconds)) , strftime("%H:%M:%S", gmtime(user_time)), strftime("%H:%M:%S", gmtime(system_time))])


            # to save disk space record only last lines of proof 
            if cmd_args.save_only_last_lines_of_proof:
                process_output = process_output[-3000:]
            

            # Wall clock time is the actual amount of time taken to perform a job. This is equivalent to timing your job with a stopwatch and the measured time to complete your task can be affected by anything else that the system happens to be doing at the time.

            # User time measures the amount of time the CPU spent running your code. This does not count anything else that might be running, and also does not count CPU time spent in the kernel (such as for file I/O).

            # CPU time measures the total amount of time the CPU spent running your code or anything requested by your code. This includes kernel time.

            # The "User time" measurement is probably the most appropriate for measuring the performance of different jobs, since it will be least affected by other things happening on the system.

            with open(save_dir+'/'+ proof_case, 'wt', encoding='utf-8') as f:
                f.write(process_output + '\n '+timeout_suffix + '\n wall_time '+ strftime("%H:%M:%S", gmtime(wall_time_diff.seconds)) + '\n usertime '+strftime("%H:%M:%S", gmtime(user_time)) + '\n systime '+ strftime("%H:%M:%S", gmtime(system_time)))
            

            print(' -- done')

            pt.sortby = 'wall_time'
            # print(pt)
            summary_text ='\n --------------\n'+ basename +'\n'+ str(include_lemmas) +'\n'+ str(pt)
            with open(save_dir+ '/summary.txt', 'wt', encoding='utf-8') as f:            
                f.write(summary_text)

            if cmd_args.summary_copy_folder != '':
                with open(cmd_args.summary_copy_folder+ '/'+ save_folder_basename+ '_summary.txt', 'wt', encoding='utf-8') as f:            
                    f.write(summary_text)                   

        else:
            # if the case file already exists
            print('skip existing -- '+ proof_case)

