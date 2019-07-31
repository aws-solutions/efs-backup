######################################################################################################################
#  Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.                                           #
#                                                                                                                    #
#  Licensed under the Amazon Software License (the "License"). You may not use this file except in compliance        #
#  with the License. A copy of the License is located at                                                             #
#                                                                                                                    #
#      http://aws.amazon.com/asl/                                                                                    #
#                                                                                                                    #
#  or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES #
#  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions    #
#  and limitations under the License.                                                                                #
######################################################################################################################

#!/usr/bin/env python
import os
import zipfile

def zip_function(zip_file_name, function_path, output_path, exclude_list):
    orig_path = os.getcwd()
    os.chdir(output_path)
    function_path = os.path.normpath(function_path)
    zip_name = zip_file_name + '.zip'
    if os.path.exists(zip_name):
        try:
            os.remove(zip_name)
        except OSError:
            pass
    zip_file = zipfile.ZipFile(zip_name, mode='a')
    os.chdir(function_path)
    print('\n Following files will be zipped in {} and saved in the deployment/dist folder. \n--------------' \
          '------------------------------------------------------------------------'.format(zip_name))
    for folder, subs, files in os.walk('.'):
        for filename in files:
            fpath = os.path.join(folder, filename)
            if fpath.endswith('.py') or fpath.endswith('.sh') or '.so' in fpath:
                if not any(x in fpath for x in exclude_list):
                    print(fpath)
                    zip_file.write(fpath)
    zip_file.close()
    os.chdir(orig_path)
    return

def make_dir(directory):
    # if exist skip else create dir
    try:
        os.stat(directory)
        print("\n Directory {} already exist... skipping".format(directory))
    except:
        print("\n Directory {} not found, creating now...".format(directory))
        os.makedirs(directory)

if __name__ == "__main__":
    # if condition changes the path this script runs from command line 'solution-root$ python source/scripts/lambda_build.py'
    if 'scripts' not in os.getcwd():
        os.chdir('./source/scripts')

    #Create Lambda Zip
    function_path = '../../source'
    zip_file_name = 'efs_to_efs_backup'
    output_path = '../../deployment/dist'
    make_dir(output_path)
    lambda_exclude = ['tests', 'scripts', 'egg', 'requirement', 'setup', 'scratch']
    zip_function(zip_file_name, function_path, output_path, lambda_exclude)




