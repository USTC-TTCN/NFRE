# A Toolkit for Dataset Construction

## Overview

This toolkit is to build the dataset for function name prediction in stripped binaries to facilitate researchers. *Since we are not sure if we have the rights to distribute the packages on the Ubuntu repositories, we write this toolkit to construct the required datasets directly from the original Ubuntu repositories.*

## Requirements

The toolkit uses the following utilities (version numbers are in line with what was used during development, older or newer releases may work as well):

| Tool        | Version   |
|:------------|----------:|
| python      | 3.5.2     |
| file        | 5.25      |
| wget        | 1.17.1    |
| dpkg-deb    | 1.18.4    |
| strip       | 2.26.1    |
| objcopy     | 2.26.1    |

and the following python packages (available through `pip` repositories):

| Package     | Version |
|:------------|--------:|
| tqdm        | 4.30.0  |
| wget        | 3.2     |


## Usage

To build a dataset, there are three steps.

* **Step 1: Download the software packages and the debug symbol packages.**
  ```bash
  python dataset_builder.py --action=down
  ```
  At this step, the toolkit will download the meta files and parse them. The file `package_deb_ddeb.txt` records the information of software projects, corresponding software and debug symbol packages. Then the toolkit will download the software and the debug symbol packages from the Ubuntu repositories. The software packages are saved in the folder `deb`, while the debug symbol packages are saved in the folder `ddeb`. The meta information of packages is saved in the folder `temp`.


* **Step 2: Unpack the packages.**
  ```bash
  python dataset_builder.py --action=unpack
  ```
  At this step, the toolkit will unpack the software and the debug symbol packages. The unpacked software and debug symbol packages are saved in the folder `deb_unpack` and `ddeb_unpack`, respectively.

* **Step 3: Associate the stripped binaries with the debug symbol files.**
  ```bash
  python dataset_builder.py --action=associate
  ```
  At this step, the toolkit will extract the stripped binaries from `deb_unpack` and the debug symbol files from `ddeb_unpack`, associating the stripped binaries with the corresponding debug symbols by `BuildID`. The original debuglink section (`.gnu_debuglink`) will be removed and the new debuglink section will be created. The folder `dataset` is the very dataset.


```
ustcsec@ustcsec:~/Desktop/dataset_builder$ python dataset_builder.py --action=down
Requesting Software Package Info......
Requesting Software Package Info......Done
Decompressing......
Decompressing......Done
Parsing......
Parsing......Done
Number of Software Packages:  8542
Requesting Debug Symbol Package Info......
Requesting Debug Symbol Package Info......Done
Decompressing......
Decompressing......Done
Parsing......
Parsing......Done
Number of Debug Symbol Packages:  434
Number of Final Packages:  434
100% [..............................................................................] 44122 / 44122
ustcsec@ustcsec:~/Desktop/dataset_builder$ python dataset_builder.py --action=unpack
Unpacking: 100%|███████████████████████████████████████████████████████████████████████| 434/434 [00:08<00:00, 51.06it/s]
ustcsec@ustcsec:~/Desktop/dataset_builder$ python dataset_builder.py --action=associate
Associating: 100%|█████████████████████████████████████████████████████████████████████| 434/434 [00:31<00:00, 13.59it/s]
ustcsec@ustcsec:~/Desktop/dataset_builder$ 
```

## Details

The startup Python script provides the following options:

* `--action [ACTION]`

  This option allows to specify an action. The options can be `down`, `unpack` or `associate`.

* `--deb [URL]`

  This option allows to specify the Ubuntu Mirror.

* `--ddeb [URL]`

  This option allows to specify the Ubuntu Debug Symbol.

* `--deb_dir [FOLDER]`

  This option allows to specify a folder for the software packages.

* `--ddeb_dir [FOLDER]`

  This option allows to specify a folder for the debug symbol packages.

* `--mapping [MAPPING_FILE]`

  This option allows to specify a txt file that records the information of software projects, corresponding software and debug symbol packages.

* `--deb_unpack_dir [FOLDER]`

  This option allows to specify a folder for the unpacked software packages.

* `--ddeb_unpack_dir [FOLDER]`

  This option allows to specify a folder for the unpacked debug symbol packages.

* `--dataset_dir [FOLDER]`

  This option allows to specify a folder for the dataset.

* `--ubuntu_version [VERSION]`

  This option allows to specify the Ubuntu version. The toolkit will crawl the software in the current version. The options can be `precise`, `trusty`, `xenial`, `bionic`, `focal`, `groovy`, `hirsute`, `impish`, etc.

* `--freedom [FREEDOM]`

  This option allows to specify the freedom of software. The toolkit will crawl the software of the current freedom. The options can be `main`, `universe`, `restricted` or `multiverse`.

* `--arch [ARCH]`

  This option allows to specify the architecture of software. The options can be `i386` or `amd64`.

* `--num_cores [NUMBER]`

  This option allows to specify the number of workers for downloading the packages.


## Citation
```
@inproceedings{han2021issta,
    author = {Gao, Han and Cheng, Shaoyin and Xue, Yinxing and Zhang, Weiming},
    title = {A Lightweight Framework for Function Name Reassignment Based on Large-Scale Stripped Binaries},
    booktitle = {Proceedings of the 30th ACM SIGSOFT International Symposium on Software Testing and Analysis (ISSTA)},
    year = {2021},
    publisher = {Association for Computing Machinery},
    series = {ISSTA 2021}
}
```