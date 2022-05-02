import pandas as pd
import sys
import openpyxl as oxl
sys.path.append(r"C:\Users\Usuario\Documents\Trabajo\TU Berlin\E-mobility flexiblity potential\mob4anci")
from m4a_classes.inputclass import inputInfo



def readInput(path):

    data = pd.read_excel(path, 'input')
    
    dayoption = ['week', 'sat', 'hol'] #workweek, saturday, holiday/sunday

    aktInput = inputInfo()
    items = list(aktInput.__dict__.keys())

    for element in items:

        if element =='connectivity':

            cols = [aktInput.id + '_' + day for day in dayoption]
            connectivity = pd.read_excel(path, 'connectivity', index_col=0).loc[:,cols]

        else:

            setattr(aktInput, element, data.loc[0, element])

    aktInput.connectivity = connectivity



    return aktInput

def readAnService(path, servicetype):

    data = pd.read_excel(path, servicetype)

    return data

def writeOutput(path, id, servicetype, checks):
    ''' get the path and opern the workbook. Then, we get the checks that we have stored in the checks list obtaine from comaperValues.
    '''
    wb = oxl.load_workbook(path)
    wsname = wb.sheetnames[0]
    ws = wb[wsname]
    rowindex = ws.max_row + 1 

    for colindex in range(1,ws.max_column+1):

        #first column is always id

        if colindex == 1:

            ws.cell(row=rowindex, column=colindex).value = id

        #second column is always service type

        elif colindex == 2:

            ws.cell(row=rowindex,column=colindex).value = servicetype

        #add the booleans values of the checks

        else:
            # if any of the columns does not have a check boolean, just write '-'
            if checks[colindex-3] ==  None:

                ws.cell(row=rowindex,column=colindex).value = '-'

            else:

                ws.cell(row=rowindex,column=colindex).value = str(checks[colindex-3])
        
    wb.save(path)
            

    print()




