import re
import sys
import subprocess
import csv
import os
import json

#class File stores each file from json
class File:

    def __init__(self, filename, counter_arr):
        self.filename = filename
        self.counter_arr = counter_arr


#class to store each counter
class Counter:

    def __init__(self, name, component_to_track, increment, weight):
        self.name = name
        self.component_to_track = component_to_track
        self.increment = increment
        self.weight = weight
        self.count = 0


def generate_assemble(new_program):
    #use run input program on or1k
    subprocess.run(['or1k-elf-gcc', new_program, '-o', 'output'], cwd=directory, text=True)

    #dump to output file
    objdump_command = ['or1k-elf-objdump', '-d', 'output']
    output_file_path = os.path.join(directory, 'new_output.txt')

    with open(output_file_path, 'w') as output_file:
        subprocess.run(objdump_command, cwd=directory, check=True, text=True, stdout=output_file)

    return output_file_path


def generate_counter_dict(output_file_path):
    #create counter dict for all commands
    counter_dict = {}
    with open(output_file_path, 'r') as file:

        record = False
        stop = False
        for line in file:
            
            words = line.split()
            
            for word in words:
                if word == '<main>:':
                    record = True
                elif (word.startswith('l.') or word.startswith('lf.') or word.startswith('lv.')) and record:
                    if word in counter_dict:
                        counter_dict[word] += 1
                    else:
                        counter_dict[word] = 1
                elif word == '<atexit>:':
                    stop = True
                    break
            if stop:
                break
    return counter_dict


def update_counts(counter_dict):

    for key, value in counter_dict.items():
        for i in range(value):
            #regular arithmetic or logical command
            if commands_dict[key] == 1:
                component_dict["instruction_fetch"] += 1
                component_dict["instruction_decode"] += 1
                component_dict["ALU"] += 1
            
            #branch command
            elif commands_dict[key] == 2:
                component_dict["program_counter"] += 1
                component_dict["instruction_fetch"] += 1
                component_dict["instruction_decode"] += 1
                component_dict["ALU"] += 1

            #jump command
            elif commands_dict[key] == 3:
                component_dict["program_counter"] += 1
                component_dict["instruction_fetch"] += 1
                component_dict["instruction_decode"] += 1

            #load and store commands
            elif commands_dict[key] == 4:
                component_dict["program_counter"] += 1
                component_dict["instruction_fetch"] += 1
                component_dict["instruction_decode"] += 1
                component_dict["memory_management_unit"] += 1


commands_dict = {
    "l.add": 1, "l.addi": 1, "l.addc": 1,"l.addic": 1,"l.adrp": 1, "l.sub": 1, "l.cmov": 0,"l.muli": 1, "l.mul": 1,"l.mulu": 1,"l.muld": 1,"l.muldu": 1, "l.div": 1, "l.divu": 1, "rem": 0, "remu": 0,
    "l.and": 1, "l.andi": 1, "l.or": 1, "l.ori": 1, "l.xor": 1, "l.xori": 1, "l.sll": 0, "l.slli": 0, "l.srl": 0, "l.srli": 0, "l.sra": 0, "l.srai": 0,
    "l.lb": 4, "l.lbu": 4, "l.lh": 4, "l.lhz": 4, "l.lhu": 4, "l.lhs": 4, "l.lw": 4,"l.lwa": 4,"l.lws": 4,"l.lwz": 4, "l.ld": 4, "l.lf": 4, 
    "l.sb": 4, "l.sh": 4, "l.sw": 4,"l.swa": 4, "l.sd": 4, "l.movhi": 0,"l.msb": 0,"l.msbu": 0, "l.ror": 0,"l.rori": 0,
    "l.extbs": 0,"l.extbz": 0,"l.exths": 0,"l.exthz": 0,"l.extws": 0,"l.extwz": 0,"l.ff1": 0,"l.fl1": 0,
    "l.j": 3, "l.jal": 3, "l.jr": 3, "l.jalr": 3,"l.bnf": 2, "l.bf": 2, "l.bne": 2, "l.nop": 0, "l.mtspr": 0,"l.rfe": 0, "l.sys": 0, "l.trap": 0, "l.msync": 0,"l.csync": 0, "l.psync": 0,
    "l.cust1": 0,"l.cust2": 0,"l.cust3": 0,"l.cust4": 0,"l.cust5": 0,"l.cust6": 0,"l.cust7": 0,"l.cust8": 0,"l.sflts": 0,"l.sfltsi": 0,"l.sfltu": 0,"l.sfltui": 0,
    "lf.add.s": 0, "lf.sub.s": 0, "lf.mul.s": 0, "lf.div.s": 0, "lf.sqrt.s": 0, "lf.madd.s": 0, "lf.cmp.s": 0,"l.sfles": 0,"l.sflesi": 0,"l.sfleu": 0,"l.sfleui": 0,
    "l.mac": 0,"l.maci": 0,"l.macrc": 0,"l.macu": 0,"l.mfspr": 0,"l.sfges": 0, "l.sfgesi": 0,"l.sfgeu": 0,"l.sfgeui": 0,"l.sfgts": 0,"l.sfgtsi": 0,"l.sfgtu": 0,"l.sfgtui": 0,
    "lf.itof.s": 0, "lf.ftoi.s": 0, "lf.mov.s": 0, "l.lbz": 0, "l.sfne": 0,"l.sfnei": 0, "l.sfeq": 0,"l.sfeqi": 0, "lwz": 0,"l.lbs": 0
}


#read in json file
json_file = sys.argv[1]

with open(json_file, 'r') as j_file:
    json_data = json.load(j_file)

input_programs = json_data["input_programs"]
directory = json_data["or1k_directory"]
counter_number = json_data["counter_number"]

#create file to store file objects
file_arr = []

#iterate through all programs 
for i in input_programs:

    #create counters for specific file
    counter_arr = []
    for j in range(1, counter_number+1):
        key = f'counter_{j}'
        counter = json_data[key]
        counter_arr.append(Counter(counter["name"], counter["component_to_track"], counter["increment_value"], counter["weight"]))

    component_dict = {"instruction_fetch": 0, "instruction_decode": 0, "ALU": 0, "program_counter": 0, "memory_management_unit": 0}
    output_file = generate_assemble(i)
    counter_dict = generate_counter_dict(output_file)
    update_counts(counter_dict)

    for j in range(len(counter_arr)):
        counter_arr[j].count = component_dict[counter_arr[j].component_to_track]

    file_arr.append(File(i, counter_arr))


    
for i in file_arr:
    print(i.filename)
    for j in i.counter_arr:
        print(j.name, ":", j.count)

''''
csv_file = 'new_assemble_out.csv'

file_exists = os.path.isfile(csv_file)

# Open the CSV file in append mode if it exists, otherwise in write mode
with open(csv_file, mode='a' if file_exists else 'w', newline='') as file:
    #fieldnames = list(basic_dict.keys()) + list(commands_dict.keys())
    fieldnames = []
    for i in basic_dict.keys():
        fieldnames.append(i)

    for i in commands_dict.keys():
        fieldnames.append(i)

    writer = csv.DictWriter(file, fieldnames=fieldnames)
    
    # Write the header only if the file was newly created
    if not file_exists:
        writer.writeheader()

    # Combine both dictionaries into a single row and write it
    combined_dict = {**basic_dict, **commands_dict}
    writer.writerow(combined_dict)


for key in commands_dict:
    pattern = re.compile(rf'\b{key}\b')
    matches = pattern.findall(assemble_output.stdout)
    count = len(matches)
    commands_dict[key] = count
    
    print(f'{key} : {count}')

    with open(csv_file, mode='r', newline='') as file:
        reader = csv.reader(file)
        rows = list(reader)

# Iterate over rows and find the row with the specific name
    for row in rows:
        if row[0] == input_program:  # Assuming name is in the first column
            row.append(str(count))   # Append the new data to the row
            break
# Write the updated data back to the CSV file
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

'''
