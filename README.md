LibvirtApi
==========

#### 1、安装

```
yum install -y libvirt-devel gcc-c++

pip install libvirt-python

cd libvirtapi/

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

python setup.py install
```

#### 2、运行

```
start-libvirtapi

cd libvirtapi/

./start-noVNC.sh
```
