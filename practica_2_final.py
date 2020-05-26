#
#   Pràctica 2 Sistemes Distribuits - Mutual Exclusion
#
#   autor: Oriol Villanova Llorens
#   email: oriol.villanova@estudiants.urv.cat
#
#

# coding=utf-8
#Importem les llibreries necessaries
import pywren_ibm_cloud as pywren
import numpy as np
import pickle
import ibm_boto3
import time
import datetime
import filecmp
import os
import ibm_botocore


#Es defineixen els valors constants que s'utilitzaran

N_SLAVES = 5 # Mai pot ser major que 100
BUCKET_NAME = 'prac2'
SEGONS = 10
RESULTAT = 'result.txt'

def master(id, x, ibm_cos):
    write_permission_list = []
    # 1. monitor COS bucket each X seconds
    n =  ibm_cos.list_objects_v2(Bucket=BUCKET_NAME, Prefix='p_write')['KeyCount']
    fitxers = ibm_cos.list_objects( Bucket=BUCKET_NAME,Prefix='p_write_')
    while n > 0 :
        time.sleep(1)
        # 2. List all "p_write_{id}" files
        fitxers = ibm_cos.list_objects(Bucket=BUCKET_NAME,Prefix='p_write_')
        queue_ = []
        for dic in fitxers['Contents']:
            queue_.append([dic['Key'], dic['LastModified']])
        # 3. Order objects by time of creation
        queue_.sort(key=lambda x: x[1])
        # 4. Pop first object of the list "p_write_{id}" 
        slave = queue_.pop(0)
        last_modified_ = ibm_cos.list_objects_v2(Bucket=BUCKET_NAME, Prefix=RESULTAT)['Contents'][0]['LastModified']
        # 5. Write empty "write_{id}" object into COS
        permis = 'write_'+str(slave[0][8:])
        ibm_cos.put_object(Bucket=BUCKET_NAME, Key=permis)
        # 6. Delete from COS "p_write_{id}", save {id} in write_permission_list
        write_permission_list.append(int(slave[0][8:]))
        ibm_cos.delete_object(Bucket=BUCKET_NAME,Key=slave[0])
        # 7. Monitor "result.txt" object each X seconds until it is updated
        modified_date = ibm_cos.list_objects_v2(Bucket=BUCKET_NAME, Prefix='result.txt')['Contents'][0]['LastModified']
        while modified_date  <= last_modified_:
            time.sleep(2)
            modified_date = ibm_cos.list_objects_v2(Bucket=BUCKET_NAME, Prefix='result.txt')['Contents'][0]['LastModified']
        # 8. Delete from COS “write_{id}”
        ibm_cos.delete_object(Bucket=BUCKET_NAME,Key=permis)
        # 9. Back to step 1 until no "p_write_{id}" objects in the bucket
        n = ibm_cos.list_objects_v2(Bucket=BUCKET_NAME, Prefix='p_write')['KeyCount']
        fitxers = ibm_cos.list_objects(Bucket=BUCKET_NAME,Prefix='p_write_')   
    return write_permission_list



def slave(id, x, ibm_cos):
    # 1. Write empty "p_write_{id}" object into COS
    ibm_cos.put_object(Bucket=BUCKET_NAME, Key='p_write_'+str(id))
    # 2. Monitor COS bucket each X seconds until it finds a file called "write_{id}"
    while ibm_cos.list_objects_v2(Bucket=BUCKET_NAME, Prefix = 'write_'+str(id))['KeyCount'] == 0:
       indent = 0

    time.sleep(1)
    # 3. If write_{id} is in COS: get result.txt, append {id}, and put back to COS result.txt
    esc = ibm_cos.get_object(Bucket = BUCKET_NAME, Key = RESULTAT) ['Body'].read()
    escriure = pickle.loads(esc)
    escriure.append(id)
    escrit = pickle.dumps(escriure)
    ibm_cos.put_object(Bucket=BUCKET_NAME, Key=RESULTAT, Body=escrit) 
    indent = indent + 1
    # 4. Finish 
    # No need to return anything
    


if __name__ == '__main__':

    #Es crea el fitxer result
    pw = pywren.ibm_cf_executor()
    ibm_cos = pw.internal_storage.get_client()
    s = pickle.dumps([])
    ibm_cos.put_object(Bucket = BUCKET_NAME, Key = RESULTAT, Body=s )
    pw = pywren.ibm_cf_executor() 
    pw.map(slave, range(N_SLAVES)) 
    pw.call_async(master, 0)
    write_permission_list = pw.get_result()
    res = ibm_cos.get_object(Bucket = BUCKET_NAME, Key = RESULTAT) ['Body'].read()
    results = pickle.loads(res) 

    # Get result.txt
    print('                                                     ')
    print('--------------write_permision_list-------------------')
    print (write_permission_list)
    print('--------------write_permision_list-------------------')
    print('                                                     ')
    # check if content of result.txt == write_permission_list
    print('------------------result.txt-------------------------')
    print (results)
    print('------------------result.txt-------------------------')
    print('                                                     ')

    if (write_permission_list == results):
        print ('Son iguals')
    else:
        print ('No son iguals')


    ibm_cos.delete_object(Bucket=BUCKET_NAME,Key=RESULTAT)