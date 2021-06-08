#!/usr/bin/env python3.8

##########################
##    Matus Tvarozny    ##
##       xtvaro00       ##
##     interpret.py     ##
##########################

##  importy  ##
import argparse
import xml.etree.ElementTree as ET
import sys
import getopt
import re
import string

##  globalne premenne  ##
entry_source = None
entry_input = None
output = ''

##  vstupne argumenty  ##
parser = argparse.ArgumentParser(description="Interpret jazyka IPPcode21", usage="python3 interpret.py --source=file --input=file")
parser.add_argument('--source', help="vstupny subor s XML reprezentaciou zdrojoveho kodu")
parser.add_argument('--input', help="subor so vstupmi pre samotnu interpretaciu zadaneho zdrojoveho kodu")
args = vars(parser.parse_args())

if args["source"] != None:
    entry_source = args["source"]

if args["input"] != None:
    entry_input = open(args["input"], "r")

if not (args["source"] or args["input"]):
    parser.error("Potrebny aspon jeden z argumentov --source=file alebo --input=file")


try:
    tree = ET.parse(entry_source)
except:
    sys.exit(31)

try:
    xml = tree.getroot()
except:
    sys.exit(32)

if xml.attrib["language"].upper() != "IPPCODE21":
    sys.exit(32)

if xml.tag != "program":
    sys.exit(32)

try:
    xml = sorted(xml, key = lambda child  :  int(child.get('order')))
except:
    sys.exit(32)


##  navestia a duplicitne 'orders'  ##
labels = {}

def labels_fun():
    global labels
    orders_list = []
    for i in range(0, len(xml)):
        temp = xml[i]
        try:
            order = temp.attrib["order"]
            opcode = temp.attrib["opcode"]
        except:
            sys.exit(32)
        try:
            #duplicitny order
            if order in orders_list:
                sys.exit(32)
            else:
                orders_list.append(order)
            #navestia
            if opcode == "LABEL":
                if len(temp) != 1:
                    sys.exit(32)
                if temp[0].tag != "arg1":
                    sys.exit(32)
                if temp[0].attrib["type"] != "label": 
                    sys.exit(32)
                if temp[0].text in labels.keys():
                    sys.exit(52)
                else:
                    labels[temp[0].text] = i    
        except SystemExit as e:
            if e.code == 52:
                sys.exit(52) #duplicitny label
            else:
                sys.exit(32) #keby chybal opcode
    
labels_fun()


##  funkcia starajuca sa o pracu s premennymi a ramcami  ##
def var_fun(variable, read_write, write=None):
    if write != None and isinstance(write, str):
        all_escapes = []
        for f in re.finditer('\\\[0-9][0-9][0-9]', write):
            all_escapes.append(write[f.start():f.end()])
        for r in all_escapes:
            write = write.replace(str(r), chr(int(r[1:])))

    if read_write == "r":
        if variable[:2] == "GF":
            try:
                return global_frame[variable[3:]]
            except:
                sys.exit(54)
        elif variable[:2] == "TF":
            if "temporary_frame" in globals():
                try: 
                    return temporary_frame[variable[3:]]
                except:
                    sys.exit(54)
            else:
                sys.exit(55)
        elif variable[:2] == "LF":
            if len(local_frames) != 0:
                try:
                    return local_frames[0][variable[3:]]    
                except:
                    sys.exit(54)
            else:
                sys.exit(55)
        else:
            sys.exit(32)

    elif read_write == "w":
        if variable[:2] == "GF":
            try:
                global_frame.update({variable[3:] : write})
            except:
                sys.exit(55)
            else:
                return
        if variable[:2] == "TF":
            try:
                temporary_frame.update({variable[3:] : write})
            except:
                sys.exit(55)
            else:
                return
        if variable[:2] == "LF":
            try:
                local_frames[0].update({variable[3:] : write})
            except:
                sys.exit(55)
            else:
                return
    else:
        sys.exit(99)


i = 0

##  ramce  ##
global_frame = {}
local_frames = []
call_list = []
stack = []


##  interpret  ##
while i < len(xml):
    
    instruction = xml[i]

    ##  element instrukcie musi byt 'instruction'  ##
    if instruction.tag != "instruction":
        sys.exit(32)
    
    args_count = len(instruction)

    if args_count > 3:
        sys.exit(32)

    opcode = instruction.attrib["opcode"].upper()
    order = instruction.attrib["order"]

    ##  negativny order  ##
    if int(order) <= 0:
        sys.exit(32)

    ##  kontrola typu argumentu a jeho hodnoty  ##
    for argument in range(0,args_count):
        arg_type = instruction[argument].attrib["type"]
        arg_text = instruction[argument].text
        if arg_type == "int":
            try: 
                int(arg_text)
            except ValueError:
                sys.exit(32)
        elif arg_type == "nil":
            if arg_text != "nil":
                sys.exit(32)

    arg1_bool = False
    arg2_bool = False
    arg3_bool = False

    ##  kontrola spravnych tagov argumentov a ich ulozenie do premennych  ##
    for arg_number in range(0, args_count):
        if instruction[arg_number].tag == "arg1":
            arg1 = instruction[arg_number]
            arg1_type = arg1.attrib["type"]

            if arg1_type == "string" and arg1.text == None:
                arg1_text = ""
            else:
                arg1_text = arg1.text

            if arg1_type == "string":
                all_escapes = []
                for f in re.finditer('\\\[0-9][0-9][0-9]', arg1_text):
                    all_escapes.append(arg1_text[f.start():f.end()])
                for r in all_escapes:
                    arg1_text = arg1_text.replace(str(r), chr(int(r[1:])))

            arg1_bool = True
        elif instruction[arg_number].tag == "arg2":
            arg2 = instruction[arg_number]
            arg2_type = arg2.attrib["type"]

            if arg2_type == "string" and arg2.text == None:
                arg2_text = ""
            else:
                arg2_text = arg2.text

            if arg2_type == "string":
                all_escapes = []
                for f in re.finditer('\\\[0-9][0-9][0-9]', arg2_text):
                    all_escapes.append(arg2_text[f.start():f.end()])
                for r in all_escapes:
                    arg2_text = arg2_text.replace(str(r), chr(int(r[1:])))

            arg2_bool = True
        elif instruction[arg_number].tag == "arg3":
            arg3 = instruction[arg_number]
            arg3_type = arg3.attrib["type"]

            if arg3_type == "string" and arg3.text == None:
                arg3_text = ""
            else:
                arg3_text = arg3.text

            if arg3_type == "string":
                all_escapes = []
                for f in re.finditer('\\\[0-9][0-9][0-9]', arg3_text):
                    all_escapes.append(arg3_text[f.start():f.end()])
                for r in all_escapes:
                    arg3_text = arg3_text.replace(str(r), chr(int(r[1:])))

            arg3_bool = True
        else:
            sys.exit(32)

    if args_count == 1 and arg1_bool != True:
        sys.exit(32)
    if args_count == 2 and arg1_bool != True and arg2_bool != True:
        sys.exit(32)
    if args_count == 3 and arg1_bool != True and arg2_bool != True and arg3_bool != True:
        sys.exit(32)
    

    if opcode == "MOVE":
        if args_count != 2: 
            sys.exit(32)

        #arg1
        if arg1_type != "var": 
            sys.exit(32)
        var_fun(arg1_text, "r")

        #arg2
        if arg2_type == "var":
            temp = var_fun(arg2_text, "r")
            if temp == None:
                sys.exit(56)
            var_fun(arg1_text, "w", temp)
        elif arg2_type == "int":
            if arg2_text == None:
                var_fun(arg1_text, "w", 0)
            else:
                var_fun(arg1_text, "w", int(arg2_text))
        elif arg2_type == "string":
            if arg2_text == None:
                var_fun(arg1_text, "w", "")
            else:
                var_fun(arg1_text, "w", str(arg2_text))
        elif arg2_type == "bool":
            if arg2_text == None:
                var_fun(arg1_text, "w", bool)
            else:
                if arg2_text == "true":
                    var_fun(arg1_text, "w", True)
                elif arg2_text == "false":
                    var_fun(arg1_text, "w", False)
                else:
                    sys.exit(32)
        elif arg2_type == "nil":
            var_fun(arg1_text, "w", "") 
        else:
            sys.exit(32)


    elif opcode == "CREATEFRAME":
        if args_count != 0: 
            sys.exit(32)
        
        #createframe
        temporary_frame = {}


    elif opcode == "PUSHFRAME":
        if args_count != 0: 
            sys.exit(32)
        
        #pushframe
        try:
            local_frames.insert(0, temporary_frame)
        except:
            sys.exit(55)
        else:
            del temporary_frame


    elif opcode == "POPFRAME":
        if args_count != 0: 
            sys.exit(32)

        #popframe
        if len(local_frames) != 0:
            temporary_frame = local_frames.pop(0)
        else:
            sys.exit(55)


    elif opcode == "DEFVAR":
        if args_count != 1:
            sys.exit(32)

        #arg1
        if arg1_type != "var": 
            sys.exit(32)


        #defvar
        if arg1_text[:2] == "GF":
            if arg1_text[3:] in global_frame.keys():
                sys.exit(52)
        if arg1_text[:2] == "LF":
            try:
                local_frames[0]
            except:
                sys.exit(55)
            if arg1_text[3:] in local_frames[0]:
                sys.exit(52)
        if arg1_text[:2] == "TF":
            try:
                temporary_frame.keys()
            except:
                sys.exit(55)
            if arg1_text[3:] in temporary_frame.keys():
                sys.exit(52)
        var_fun(arg1_text, "w", None)   


    elif opcode == "CALL":
        if args_count != 1: 
            sys.exit(32)

        #arg1
        if arg1_type != "label": 
            sys.exit(32)
        if arg1_text not in labels.keys():
            sys.exit(52)

        #call
        call_list.insert(0, i)
        i = int(labels[arg1_text])

        
    elif opcode == "RETURN":
        if args_count != 0: 
            sys.exit(32)

        #return
        if len(call_list) != 0:
            i = call_list.pop(0)
        else:
            sys.exit(56)

        
    elif opcode == "PUSHS":
        if args_count != 1: 
            sys.exit(32)

        #arg1/pushs
        if arg1_type == "var":
            temp = var_fun(arg1_text, "r")
            if temp is None:
                sys.exit(56)
            stack.insert(0, temp)
        elif arg1_type == "int":
            stack.insert(0, int(arg1_text))
        elif arg1_type == "string":
            stack.insert(0, arg1_text)
        elif arg1_type == "bool":
            if arg1_text == "true":
                stack.insert(0, True)
            elif arg1_text == "false":
                stack.insert(0, False)
            else:
                sys.exit(32)
        elif arg1_type == "nil":
            stack.insert(0, "nil")
        else:
            sys.exit(32)


    elif opcode == "POPS":
        if args_count != 1: 
            sys.exit(32)

        #arg1
        if arg1_type != "var": 
            sys.exit(32)
        var_fun(arg1_text, "r")

        #pops
        if len(stack) != 0:
            temp = stack.pop(0)
            var_fun(arg1_text, "w", temp)
        else:
            sys.exit(56)


    elif opcode == "ADD" or opcode == "SUB" or opcode == "MUL" or opcode == "IDIV":
        if args_count != 3: 
            sys.exit(32)
        
        #arg1
        if arg1_type != "var": 
            sys.exit(32)
        var_fun(arg1_text, "r")

        #arg2
        if arg2_type == "var": 
            int1 = var_fun(arg2_text, "r")
            if not isinstance(int1, int):
                if int1 is None:
                    sys.exit(56)
                else:
                    sys.exit(32)
        elif arg2_type == "int":
            int1 = int(arg2_text)
        else:
            sys.exit(53)

        #arg3
        if arg3_type == "var": 
            int2 = var_fun(arg3_text, "r")
            if not isinstance(int2, int):
                if int2 is None:
                    sys.exit(56)
                else:
                    sys.exit(32)
        elif arg3_type == "int":
            int2 = int(arg3_text)
        else:
            sys.exit(53)

        #add/sub/mul/idiv
        if opcode == "ADD":
            temp = int1 + int2
            var_fun(arg1_text, "w", temp)
        elif opcode == "SUB":
            temp = int1 - int2
            var_fun(arg1_text, "w", temp)
        elif opcode == "MUL":
            temp = int1 * int2
            var_fun(arg1_text, "w", temp)
        elif opcode == "IDIV":
            if int2 == 0:
                sys.exit(57)
            temp = int1 // int2
            var_fun(arg1_text, "w", temp)


    elif opcode == "LT" or opcode == "GT":
        if args_count != 3: 
            sys.exit(32)

        #arg1
        if arg1_type != "var": 
            sys.exit(32)
        var_fun(arg1_text, "r")

        #arg2/arg3
        if arg2_type == "var":
            check_set = var_fun(arg2_text, "r")
            if check_set is None:
                sys.exit(56)
        if arg3_type == "var":
            check_set = var_fun(arg3_text, "r")
            if check_set is None:
                sys.exit(56)

        if arg2_type != arg3_type:
            sys.exit(53)
        if arg2_type == "nil":
            sys.exit(53)

        #lt/gt
        if arg2_type == "int":
            arg2_text = int(arg2_text)
            arg3_text = int(arg3_text)

        if arg2_type == "int" or arg2_type == "string":
            if opcode == "LT":
                if arg2_text < arg3_text:
                    var_fun(arg1_text, "w", True)
                else:
                    var_fun(arg1_text, "w", False)

            if opcode == "GT":
                if arg2_text > arg3_text:
                    var_fun(arg1_text, "w", True)
                else:
                    var_fun(arg1_text, "w", False)
        elif arg2_type == "bool":
            if opcode == "LT":
                if arg2_text == "false" and arg3_text == "true":
                    var_fun(arg1_text, "w", True)
                else:
                    var_fun(arg1_text, "w", False)

            if opcode == "GT":
                if arg2_text == "true" and arg3_text == "false":
                    var_fun(arg1_text, "w", True)
                else:
                    var_fun(arg1_text, "w", False)
        else:
            sys.exit(53)


    elif opcode == "EQ":
        if args_count != 3: 
            sys.exit(32)

        #arg1
        if arg1_type != "var": 
            sys.exit(32)
        var_fun(arg1_text, "r")
        
        #arg2/arg3
        if arg2_type == "var":
            temp1 = var_fun(arg2_text, "r")
            if temp1 is None:
                sys.exit(56)
        if arg3_type == "var":
            temp2 = var_fun(arg3_text, "r")
            if temp2 is None:
                sys.exit(56)

        if arg2_type != arg3_type:
            if arg2_type != "nil" and arg3_type != "nil":
                if arg2_type != "var" and arg3_type != "var":   
                    sys.exit(53)

        #arg2
        if arg2_type == "int":
            temp1 = int(arg2_text)
        elif arg2_type == "bool":
            if arg2_text == "true":
                temp1 = True
            elif arg2_text == "false":
                temp1 = False
            else:
                exit(32)
        elif arg2_type == "nil":
            temp1 = ""
        elif arg2_type == "string":
            temp1 = arg2_text

        #arg3
        if arg3_type == "int":
            temp2 = int(arg3_text)
        elif arg3_type == "bool":
            if arg3_text == "true":
                temp2 = True
            elif arg3_text == "false":
                temp2 = False
            else:
                exit(32)
        elif arg3_type == "nil":
            temp2 = ""
        elif arg3_type == "string":
            temp2 = arg3_text

        #eq
        if temp1 == temp2: 
            var_fun(arg1_text, "w", True)
        else:
            var_fun(arg1_text, "w", False)
    

    elif opcode == "AND" or opcode == "OR":
        if args_count != 3: 
            sys.exit(32)
        
        #arg1
        if arg1_type != "var": 
            sys.exit(32)
        var_fun(arg1_text, "r")

        #arg2
        if arg2_type == "var": 
            bool1 = var_fun(arg2_text, "r")
            if not isinstance(bool1, bool):
                if bool1 is None:
                    sys.exit(56)
                else:
                    sys.exit(53)
        elif arg2_type == "bool":
            if arg2_text == "true":
                bool1 = True
            elif arg2_text == "false":
                bool1 = False
            else:
                sys.exit(53)
        else:
            sys.exit(53)
        
        #arg3
        if arg3_type == "var": 
            bool2 = var_fun(arg3_text, "r")
            if not isinstance(bool2, bool):
                if bool2 is None:
                    sys.exit(56)
                else:
                    sys.exit(53)
        elif arg3_type == "bool":
            if arg3_text == "true":
                bool2 = True
            elif arg3_text == "false":
                bool2 = False
            else:
                sys.exit(53)
        else:
            sys.exit(53)

        #and/or
        if opcode == "AND":
            temp = bool1 and bool2
            var_fun(arg1_text, "w", temp)
        if opcode == "OR":
            temp = bool1 or bool2
            var_fun(arg1_text, "w", temp)


    elif opcode == "NOT":
        if args_count != 2: 
            sys.exit(32)
        
        #arg1
        if arg1_type != "var": 
            sys.exit(32)
        var_fun(arg1_text, "r")

        #arg2
        if arg2_type == "var":
            bool1 = var_fun(arg2_text, "r")
            if not isinstance(bool1, bool):
                if bool1 is None:
                    sys.exit(56)
                else:
                    sys.exit(53)
        elif arg2_type == "bool":
            if arg2_text == "true":
                bool1 = True
            elif arg2_text == "false":
                bool1 = False
            else:
                sys.exit(53)
        else:
            sys.exit(53)

        #not
        temp = not bool1
        var_fun(arg1_text, "w", temp)


    elif opcode == "INT2CHAR":
        if args_count != 2: 
            sys.exit(32)

        #arg1
        if arg1_type != "var": 
            sys.exit(32)
        var_fun(arg1_text, "r")
        
        #arg2
        if arg2_type == "var":
            temp = var_fun(arg2_text, "r")
            if temp is None:
                sys.exit(56)
            if isinstance(temp, bool):
                sys.exit(53)
            elif isinstance(temp, int):
                
                try:
                    var_fun(arg1_text, "w", chr(int(temp)))
                except:
                    sys.exit(58)
            else:
                sys.exit(53)
        elif arg2_type == "int":
            try:
                var_fun(arg1_text, "w", chr(int(arg2_text)))
            except:
                sys.exit(58)
        else:
            sys.exit(53)


    elif opcode == "STRI2INT":
        if args_count != 3: 
            sys.exit(32)

        #arg1
        if arg1_type != "var": 
            sys.exit(32)
        var_fun(arg1_text, "r")

        #arg2
        temp1 = ""
        if arg2_type == "var":
            temp1 = var_fun(arg2_text, "r")
            if temp1 is None:
                sys.exit(56)
            if not isinstance(temp1, str):
                sys.exit(53)
        elif arg2_type == "string":
            temp1 = arg2_text
        else:
            sys.exit(53)

        #arg3
        temp2 = 0
        if arg3_type == "var":
            temp2 = var_fun(arg3_text, "r")
            if temp2 is None:
                sys.exit(56)
            if not isinstance(temp2, int):
                sys.exit(53)
        elif arg3_type == "int":
            temp2 =  int(arg3_text)
        else:
            sys.exit(53)

        #stri2int
        if 0 <= temp2 < len(temp1):
            var_fun(arg1_text, "w", ord(temp1[temp2]))
        else:
            sys.exit(58)


    elif opcode == "READ":
        if args_count != 2: 
            sys.exit(32)

        #arg1
        if arg1_type != "var": 
            sys.exit(32)
        var_fun(arg1_text, "r")

        #arg2
        if arg2_type != "type":
            sys.exit(32)

        #read
        if entry_input != None:
            temp = entry_input.readline()
        else:
            try:
                temp = input()
            except:
                temp = ""

        if arg2_text == "int":
            try:
                temp = int(temp)
            except:
                temp = ""
        if arg2_text == "bool":
            if temp.lower() == "true":
                temp = True
            elif temp == "":
                temp = ""
            else:
                temp = False
        if arg2_text == "string":
            temp = str(temp)
            temp = temp.strip()
        
        #v pripade chybajuceho vstupe sa ulozi nil
        var_fun(arg1_text, "w", temp)


    elif opcode == "WRITE":
        if args_count != 1: 
            sys.exit(32)

        #arg1/write
        if arg1_type == "var":
            temp = var_fun(arg1_text, "r")
            if temp is None:
                sys.exit(56)
            if isinstance(temp, bool):
                if temp == True:
                    output += "true"
                    #print("true", end='')
                else:
                    output += "false"
                    #print("false", end= '')
            elif temp == "nil":
                output += ""
                #print("", end='')
            elif temp == int:
                output += "int"
            elif temp == str:
                if temp == "":
                    output += "nil"
                else:
                    output += "string"
            elif temp == bool:
                output += "bool"
            elif temp == type(None):
                output += "nil"
            else:
                output += str(temp)
                #print(temp, end='')
        elif arg1_type == "nil":
            output += ""
            #print("", end='')
        else:
            all_escapes = []
            for f in re.finditer('\\\[0-9][0-9][0-9]', arg1_text):
                all_escapes.append(write[f.start():f.end()])
            for r in all_escapes:
                arg1_text = arg1_text.replace(str(r), chr(int(r[1:])))
            output += str(arg1_text)
            #print(arg1_text, end ='')


    elif opcode == "CONCAT":
        if args_count != 3: 
            sys.exit(32)
        
        #arg1
        if arg1_type != "var": 
            sys.exit(32)
        var_fun(arg1_text, "r")

        #arg2
        if arg2_type == "var": 
            string1 = var_fun(arg2_text, "r")
            if not isinstance(string1, str):
                if string1 is None:
                    sys.exit(56)
                else:
                    sys.exit(32)
        elif arg2_type == "string":
            if arg2_text is None:
                arg2_text = ""
            string1 = arg2_text
        else:
            sys.exit(53)

        #arg3
        if arg3_type == "var": 
            string2 = var_fun(arg3_text, "r")
            if not isinstance(string2, str):
                if string2 is None:
                    sys.exit(56)
                else:
                    sys.exit(32)
        elif arg3_type == "string":
            if arg3_text is None:
                arg3_text = ""
            string2 = arg3_text
        else:
            sys.exit(53)

        #concat
        temp = string1 + string2
        var_fun(arg1_text, "w", temp)


    elif opcode == "STRLEN":
        if args_count != 2: 
            sys.exit(32)
        
        #arg1
        if arg1_type != "var": 
            sys.exit(32)
        var_fun(arg1_text, "r")
    
        #arg2
        if arg2_type == "var":
            temp = var_fun(arg2_text, "r")
            if temp is None:
                sys.exit(56)
            if isinstance(temp, str):
                if temp == "":
                    sys.exit(53)
                var_fun(arg1_text, "w", len(temp))
            else:
                sys.exit(53)
        elif arg2_type == "string":
            if arg2_text == None:
                var_fun(arg1_text, "w", 0)
            else:
                var_fun(arg1_text, "w", len(arg2_text))
        else:
            sys.exit(53)


    elif opcode == "GETCHAR":
        if args_count != 3: 
            sys.exit(32)

        #arg1
        if arg1_type != "var": 
            sys.exit(32)
        var_fun(arg1_text, "r")

        #arg2
        temp1 = ""
        if arg2_type == "var":
            temp1 = var_fun(arg2_text, "r")
            if not isinstance(temp1, str):
                if temp1 is None:
                    sys.exit(56)
                else:
                    sys.exit(58)
        elif arg2_type == "string":
            temp1 = arg2_text
        else:
            sys.exit(53)

        #arg3
        temp2 = 0
        if arg3_type == "var":
            temp2 = var_fun(arg3_text, "r")
            if not isinstance(temp2, int):
                if temp2 is None:
                    sys.exit(56)
                else:
                    sys.exit(58)
        elif arg3_type == "int":
            temp2 = int(arg3_text)
        else:
            sys.exit(53)

        #getchar
        if 0 <= temp2 < len(temp1):
            var_fun(arg1_text, "w", temp1[temp2])
        else:
            sys.exit(58)


    elif opcode == "SETCHAR":
        if args_count != 3: 
            sys.exit(32)

        #arg1
        if arg1_type != "var":
            sys.exit(32)
        temp1 = var_fun(arg1_text, "r")
        if temp1 is None:
                sys.exit(56)

        if arg2_type == "var":
            temp2 = var_fun(arg2_text, "r")
            if temp2 is None:
                sys.exit(56)
        if arg3_type == "var":
            temp3 = var_fun(arg3_text, "r")
            if temp3 is None:
                sys.exit(56) 

        #kontrola ci tam je string
        if not isinstance(temp1, str):
            sys.exit(53)
        if len(temp1) == 0:
            sys.exit(53)

        #arg2
        if arg2_type == "int":
            temp2 = int(arg2_text)
        elif arg2_type == "var":
            temp2 = var_fun(arg2_text, "r")
            if not isinstance(temp2, int):
                sys.exit(53)
            temp2 = int(temp2)
        else:
            sys.exit(53)

        #arg3
        if arg3_type == "string":
            if len(arg3_text) == 0:
                sys.exit(58)
            temp3 = arg3_text[0]
        elif arg3_type == "var":
            temp3 = var_fun(arg3_text, "r")
            temp3 = temp3[0]
        else:
            sys.exit(53)

        if int(temp2) < 0 or int(temp2) >= len(temp1):
            sys.exit(58)

        #setchar
        temp4 = temp1[:temp2] + temp3 + temp1[temp2+1:]
        var_fun(arg1_text, "w", temp4)


    elif opcode == "TYPE":
        if args_count != 2: 
            sys.exit(32)

        #arg1
        if arg1_type != "var":
            sys.exit(32)
        var_fun(arg1_text, "r")

        #arg2/type
        if arg2_type == "var":
            temp = var_fun(arg2_text, "r")
            if temp == "":
                var_fun(arg1_text, "w", type(None))
            elif temp is None:
                var_fun(arg1_text, "w", "")
            elif temp == bool or temp == str or temp == int or temp == type:
                var_fun(arg1_text, "w", "string")
            else:
                var_fun(arg1_text, "w", type(temp))
        elif arg2_type == "bool":
            var_fun(arg1_text, "w", bool)
        elif arg2_type == "int":
            var_fun(arg1_text, "w", int)
        elif arg2_type == "string":
            var_fun(arg1_text, "w", str)
        elif arg2_type == "nil":
            var_fun(arg1_text, "w", type(None))
        else:
            sys.exit(53)


    elif opcode == "LABEL":
        if args_count != 1: 
            sys.exit(32)


    elif opcode == "JUMP":
        if args_count != 1: 
            sys.exit(32)
            
        #jump
        if arg1_type == "label":
            if arg1_text in labels:
                i = int(labels[arg1_text]-1)
            else:
                sys.exit(52)
        else:   
            sys.exit(52)


    elif opcode == "JUMPIFEQ" or opcode == "JUMPIFNEQ":
        if args_count != 3: 
            sys.exit(32)
        
        #arg1
        if arg1_type != "label":
            sys.exit(52)
        if arg1_text not in labels:
            sys.exit(52)

        if arg2_type == "var":
            check_set = var_fun(arg2_text, "r")
            if check_set is None:
                sys.exit(56)
        if arg3_type == "var":
            check_set = var_fun(arg3_text, "r")
            if check_set is None:
                sys.exit(56)

        if arg2_type != arg3_type:
            if arg2_type != "nil" and arg3_type != "nil":
                if arg2_type != "var" and arg3_type != "var":
                    sys.exit(53)

        #arg2
        if arg2_type == "var":
            temp1 = var_fun(arg2_text, "r")
        elif arg2_type == "nil":
            temp1 = ""
        elif arg2_type == "int":
            temp1 = int(arg2_text)
        elif arg2_type == "string":
            temp1 = arg2_text
        elif arg2_type == "bool":
            if arg2_text == "true":
                temp1 = True
            elif arg2_text == "false":
                temp1 = False
        else:
            sys.exit(55)

        #arg3
        if arg3_type == "var":
            temp2 = var_fun(arg3_text, "r")
        elif arg3_type == "nil":
            temp2 = ""
        elif arg3_type == "int":
            temp2 = int(arg3_text)
        elif arg3_type == "string":
            temp2 = arg3_text
        elif arg3_type == "bool":
            if arg3_text == "true":
                temp2 = True
            elif arg3_text == "false":
                temp2 = False
        else:
            sys.exit(55)

        #jumpifeq/jumpifneq
        if opcode == "JUMPIFEQ":
            if temp1 == temp2:
                i = int(labels[arg1_text]-1)
        if opcode == "JUMPIFNEQ":
            if temp1 != temp2:
                i = int(labels[arg1_text]-1)
    
    
    elif opcode == "EXIT":
        if args_count != 1: 
            sys.exit(32)

        #exit
        if arg1_type == "var":
            temp = var_fun(arg1_text, "r")
            if temp is None:
                exit(56)
            if not isinstance(temp, int):
                sys.exit(53)
            if isinstance(temp, bool):
                sys.exit(53)
            if 0 <= temp <= 49:
                if len(output) != 0:
                    print(output, end='')
                sys.exit(temp)
            else:
                sys.exit(57)
        elif arg1_type == "int":
            try:   
                int(arg1_text)
            except:
                sys.exit(53)
            temp = int(arg1_text)
            if 0 <= temp <= 49:
                if len(output) != 0:
                    print(output, end='')
                sys.exit(temp)
            else:
                sys.exit(57)
        else:
            sys.exit(53)


    elif opcode == "DPRINT":
        if args_count != 1: 
            sys.exit(32)

        #dprint
        if arg1_type == "var":
            temp = var_fun(arg1_text, "r")
            if isinstance(temp, bool):
                if temp == True:
                    sys.stderr.write("true")
                else:                  
                    sys.stderr.write("false")                  
            elif temp == "nil":               
                sys.stderr.write("")                
            else:                
                sys.stderr.write(temp)                
        elif arg1_type == "nil":            
            sys.stderr.write("")            
        else:            
            sys.stderr.write(arg1_text)


    elif opcode == "BREAK":
        if args_count != 0: 
            sys.exit(32)
    
    else:
        sys.exit(32)

    i += 1

print(output, end='')
sys.exit(0)