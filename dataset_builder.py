import argparse
import multiprocessing
import subprocess
import gzip
import re
import shutil
import tqdm
import os
import wget
import sys
import functools


def get_args():

    parser = argparse.ArgumentParser(description='Create the Dataset from Ubuntu Software Packages and Ubuntu Debug Symobol Packages.')

    parser.add_argument('--action', type=str, choices=['down', 'unpack', 'associate'], required=True, help='Action')

    parser.add_argument('--deb', type=str, default='https://mirrors.ustc.edu.cn/ubuntu', help='Ubuntu Software Mirror')
    parser.add_argument('--ddeb', type=str, default='http://ddebs.ubuntu.com', help='Ubuntu Debug Symbol Mirror')

    parser.add_argument('--deb_dir', type=str, default='deb', help='Software Package Location')
    parser.add_argument('--ddeb_dir', type=str, default='ddeb', help='Debug Symbol Package Location')

    parser.add_argument('--mapping', type=str, default='package_deb_ddeb.txt', help='Mapping of "Package Name|Software Package Location|Debug Symbol Package Location"')
    parser.add_argument('--deb_unpack_dir', type=str, default='deb_unpack', help='Software Package Unpack Location')
    parser.add_argument('--ddeb_unpack_dir', type=str, default='ddeb_unpack', help='Debug Symbol Package Unpack Location')

    parser.add_argument('--dataset_dir', type=str, default='dataset', help='Software Package Unpack Location')

    parser.add_argument('--ubuntu_version', type=str, default='trusty', choices=['precise', 'trusty', 'xenial', 'bionic', 'focal', 'groovy', 'hirsute', 'impish'], help='Ubuntu Version')
    parser.add_argument('--freedom', type=str, default='main', choices=['main', 'universe', 'restricted', 'multiverse'], help='Freedom of Software')
    parser.add_argument('--arch', type=str, default='i386', choices=['i386', 'amd64'], help='Architecture of Binaries')
    parser.add_argument('--num_cores', type=int, default=multiprocessing.cpu_count(), help='Number of Processings')

    parser.add_argument('--temp', type=str, default='temp', help='TempDir Location')

    args = parser.parse_args()
    return vars(args)


def get_software_package_list(args):

    print('Requesting Software Package Info......')
    url = '{}/dists/{}/{}/binary-{}/Packages.gz'.format(args['deb'], args['ubuntu_version'], args['freedom'], args['arch'])
    save_path = wget.download(url, out=args['temp'], bar=None)
    print('Requesting Software Package Info......Done')

    print('Decompressing......')
    with open(save_path, 'rb') as f:
        uncompress_data = gzip.decompress(f.read())
    raw_package_info = uncompress_data.decode('utf-8')
    print('Decompressing......Done')

    print('Parsing......')
    pattern = re.compile(r'Package: ([^\n]+)((?!\n\n).)*Filename: ([^\n]+\.deb)\n', re.S)
    match_result = pattern.findall(raw_package_info)
    result = [(x[0], '{}/{}'.format(args['deb'], x[-1])) for x in match_result]
    print('Parsing......Done')

    print('Number of Software Packages: ', len(result))

    package_url_map = dict(result)
    assert len(result) == len(package_url_map.keys())
    return package_url_map


def get_debug_symbol_package_list(args):

    if not os.path.exists(args['temp']):
        os.mkdir(args['temp'])

    print('Requesting Debug Symbol Package Info......')
    url = '{}/dists/{}/{}/binary-{}/Packages.gz'.format(args['ddeb'], args['ubuntu_version'], args['freedom'], args['arch'])
    save_path = wget.download(url, out=args['temp'], bar=None)
    print('Requesting Debug Symbol Package Info......Done')

    print('Decompressing......')
    with open(save_path, 'rb') as f:
        uncompress_data = gzip.decompress(f.read())
    raw_package_info = uncompress_data.decode('utf-8')
    print('Decompressing......Done')

    print('Parsing......')
    pattern = re.compile(r'Package: ([^\n]+)((?!\n\n).)*Filename: ([^\n]+\.ddeb)\n', re.S)
    match_result = pattern.findall(raw_package_info)
    result = [(x[0][:-len('-dbgsym')] if x[0].endswith('-dbgsym') else x[0], '{}/{}'.format(args['ddeb'], x[-1])) for x in match_result]
    print('Parsing......Done')

    print('Number of Debug Symbol Packages: ', len(result))

    package_url_map = dict(result)
    assert len(result) == len(package_url_map.keys())
    return package_url_map


def download_packages(args, software_pkgs, debug_pkgs, package_deb_ddeb, lock, pkg):

    deb_file_name = wget.download(software_pkgs[pkg], out=args['deb_dir'])
    ddeb_file_name = wget.download(debug_pkgs[pkg], out=args['ddeb_dir'])

    lock.acquire()
    package_deb_ddeb.append((pkg, deb_file_name, ddeb_file_name))
    lock.release()


def get_build_id(file_path):
    cmd_result = subprocess.check_output(['file', file_path]).decode('utf-8')
    pattern = re.compile(r'BuildID\[sha1\]=([^,\n]*)')
    match_result = pattern.findall(cmd_result)
    if len(match_result) > 0:
        return match_result[0]
    else:
        return None


def get_dir_files(dir_path):
    l = []
    for main_dir, _, file_name_list in os.walk(dir_path):

        for f in file_name_list:
            file_path = os.path.join(main_dir, f)
            l.append(file_path)
    return l


if __name__ == '__main__':

    args = get_args()

    if args['action'] == 'down':

        '''
        Download software packages(.deb) and debug symbol packages(.ddeb)
        '''

        if not os.path.exists(args['temp']):
            os.mkdir(args['temp'])
        if not os.path.exists(args['deb_dir']):
            os.mkdir(args['deb_dir'])
        if not os.path.exists(args['ddeb_dir']):
            os.mkdir(args['ddeb_dir'])
    
        software_pkg_list = get_software_package_list(args)
        debug_symbol_pkg_list = get_debug_symbol_package_list(args)

        all_packages = list(software_pkg_list.keys() & debug_symbol_pkg_list.keys())
        print('Number of Final Packages: ', len(all_packages))

        
        def yielder():
            for pkg in all_packages:
                yield pkg
        

        package_deb_ddeb = multiprocessing.Manager().list()
        lock = multiprocessing.Manager().Lock()

        download_packages_ = functools.partial(download_packages, args, software_pkg_list, debug_symbol_pkg_list, package_deb_ddeb, lock)

        pool = multiprocessing.Pool(processes=args['num_cores'])
        pool.map_async(download_packages_, yielder())
        pool.close()
        pool.join()
        
        with open('package_deb_ddeb.txt', 'w') as f:
            f.write('\n'.join(['|'.join(x) for x in package_deb_ddeb]))
    

    elif args['action'] == 'unpack':

        '''
        Unpacking software packages(.deb) and debug symbol packages(.ddeb)
        '''

        if os.path.exists(args['deb_unpack_dir']):
            shutil.rmtree(args['deb_unpack_dir'])
        os.mkdir(args['deb_unpack_dir'])

        if os.path.exists(args['ddeb_unpack_dir']):
            shutil.rmtree(args['ddeb_unpack_dir'])
        os.mkdir(args['ddeb_unpack_dir'])
        
        if not os.path.exists(args['mapping']):
            print('Mapping File Not Exist!')
            sys.exit(0)
        
        with open(args['mapping'], 'r') as f:
            mapping_content = f.read().split('\n')
        
        for mapping_item in tqdm.tqdm(mapping_content, desc='Unpacking'):
            package_name, deb_path, ddeb_path = mapping_item.split('|')
            subprocess.check_output(['dpkg-deb', '-x', deb_path, '{}/{}'.format(args['deb_unpack_dir'], package_name)])
            subprocess.check_output(['dpkg-deb', '-x', ddeb_path, '{}/{}'.format(args['ddeb_unpack_dir'], package_name)])
    
    elif args['action'] == 'associate':

        '''
        Associate stripped binaries with their debug symbols by BuildID
        '''

        if os.path.exists(args['dataset_dir']):
            shutil.rmtree(args['dataset_dir'])
        
        os.mkdir(args['dataset_dir'])

        packages = os.listdir(args['deb_unpack_dir'])

        for package in tqdm.tqdm(packages, desc='Associating'):
            files_in_deb = get_dir_files('{}/{}'.format(args['deb_unpack_dir'], package))
            files_in_ddeb = get_dir_files('{}/{}'.format(args['ddeb_unpack_dir'], package))
        
            path_id_binaries = dict()
            path_id_debugs = dict()
            id_path_binaries = dict()
            id_path_debugs = dict()

            for f in files_in_deb:
                build_id = get_build_id(f)
                if build_id != None:
                    path_id_binaries[f] = build_id
                    id_path_binaries[build_id] = f
            for f in files_in_ddeb:
                build_id = get_build_id(f)
                if build_id != None:
                    path_id_debugs[f] = build_id
                    id_path_debugs[build_id] = f
            
            build_ids = id_path_binaries.keys() & id_path_debugs.keys()

            if len(build_ids) > 0:
                os.mkdir('{}/{}'.format(args['dataset_dir'], package))
            
            for id in build_ids:

                target_binary_path = '{}/{}/{}'.format(args['dataset_dir'], package, id)
                target_debug_path = '{}/{}/{}.debug'.format(args['dataset_dir'], package, id)

                shutil.copy(id_path_binaries[id], target_binary_path)
                shutil.copy(id_path_debugs[id], target_debug_path)
                
                # Reconstruct debug link
                subprocess.check_output(['strip', '--remove-section=.gnu_debuglink', target_binary_path])
                subprocess.check_output(['objcopy', '--add-gnu-debuglink={}'.format(target_debug_path), target_binary_path])
